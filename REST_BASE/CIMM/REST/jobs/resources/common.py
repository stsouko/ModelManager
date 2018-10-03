# -*- coding: utf-8 -*-
#
#  Copyright 2018 Ramil Nugmanov <stsouko@live.ru>
#  This file is part of CIMM (ChemoInformatics Models Manager).
#
#  CIMM is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
from collections import Counter
from datetime import datetime
from flask import current_app
from flask_login import current_user, login_required
from pickle import dumps, loads
from pony.orm import db_session
from redis import Redis, ConnectionError
from uuid import uuid4
from .. import database
from ...utils import abort
from ....constants import TaskStatus


class JobMixin:
    decorators = (login_required, db_session)

    @staticmethod
    def enqueue(model, data, task_id=None, runner='run'):
        if task_id is None:
            task_id = str(uuid4())

        job_id = model.create_job(data, task_id, 'CIMM.models.rq.' + runner,
                                  current_app.config.get('REDIS_JOB_TIMEOUT', 3600),
                                  current_app.config.get('REDIS_TTL', 86400))
        return job_id, task_id

    def save(self, task_id, _type, status, jobs, data=None):
        chunks = current_app.config.get('REDIS_CHUNK', 50)
        ex = current_app.config.get('REDIS_TTL', 86400)
        tmp = {}
        if data:
            for x in range(0, len(data), chunks):  # store structures in chunks.
                _id = str(uuid4())
                chunk = {s['structure']: s for s in data[x: x + chunks]}
                self.redis.set(_id, dumps(chunk), ex=ex)
                for s in chunk:
                    tmp[s] = _id

        self.redis.set(task_id, dumps({'chunks': tmp, 'jobs': jobs, 'user': current_user.get_id(),
                                       'type': _type, 'task': task_id,
                                       'status': TaskStatus.PREPARED if status == TaskStatus.PREPARING else
                                                 TaskStatus.PROCESSED}), ex=ex)

        return {'task': task_id, 'status': status, 'type': _type, 'date': datetime.utcnow(),
                'user': current_user.get_id()}

    @property
    def redis(self):
        if self.__redis_cache is None:
            redis = Redis(host=current_app.config.get('REDIS_HOST', 'localhost'),
                          port=current_app.config.get('REDIS_PORT', 6379),
                          password=current_app.config.get('REDIS_PASSWORD'))
            try:
                redis.ping()
            except ConnectionError:
                abort(500, 'dispatcher server error')
            self.__redis_cache = redis

        return self.__redis_cache

    @property
    def models(self):
        if self.__models_cache is None:
            self.__models_cache = getattr(database, current_app.config['JOBS_DB_SCHEMA']).Model
        return self.__models_cache

    @property
    def destinations(self):
        if self.__destinations_cache is None:
            self.__destinations_cache = getattr(database, current_app.config['JOBS_DB_SCHEMA']).Destination
        return self.__destinations_cache

    def fetch_meta(self, task, status):
        result = self.__fetch(task, status)
        chunks = result['chunks']
        return {'structures': {'total': len(chunks), 'pages': len(set(chunks.values()))}, **result}

    def fetch(self, task, status, page=None):
        result = self.__fetch(task, status)

        loaded_chunks = {}
        chunks = result['chunks']
        if page is None:
            tmp = []
            for s_id in sorted(chunks):
                ch_id = chunks[s_id]
                ch = loaded_chunks.get(ch_id) or loaded_chunks.setdefault(ch_id, loads(self.redis.get(ch_id)))
                tmp.append(ch[s_id])
        else:
            chunks = sorted(set(chunks.values()))
            if page > len(chunks):
                abort(404, message='page not found')

            ch = loads(self.redis.get(chunks[page - 1]))
            tmp = [ch[s_id] for s_id in sorted(ch)]

        return {'structures': tmp, **result}

    def __fetch(self, task_id, status):
        task = self.redis.get(task_id)

        if task is None:
            abort(404, message='invalid task id. perhaps this task has already been removed')

        task = loads(task)

        if task['status'] != status:
            abort(406, message='task status is invalid. task status is [%s]' % task['status'].name)

        if task['user'] != current_user.get_id():
            abort(403, message='user access deny. you do not have permission to this task')

        if task['jobs']:
            jobs = [self.models.fetch_job(x) for x in task['jobs']]
            if any(x.is_queued or x.is_started for x in jobs):
                abort(512, message='PROCESSING.Task not ready')

            ended_at = None
            flag = True
            for job in jobs:
                if ended_at is None:
                    ended_at = job.ended_at
                elif job.ended_at > ended_at:
                    ended_at = job.ended_at

                if job.is_finished:
                    self.__update_task(task['chunks'], job)
                else:
                    flag = False
                job.delete()

            task['jobs'] = []
            task['date'] = ended_at
            if flag:
                self.redis.set(task_id, dumps(task), ex=current_app.config.get('REDIS_TTL', 86400))
        return task

    def __update_task(self, chunks, job):
        chunk_size = current_app.config.get('REDIS_CHUNK', 50)
        partial_chunk = next((c_id for c_id, fill in Counter(chunks.values()).items() if fill < chunk_size), None)
        model = job.meta['model']

        loaded_chunks = {}
        for s in job.result:
            results = dict(results=s.pop('results', []), model=model)
            s_id = s['structure']
            if s_id in chunks:
                c_id = chunks[s_id]
                ch = loaded_chunks.get(c_id) or loaded_chunks.setdefault(c_id, loads(self.redis.get(c_id)))
                ch[s_id]['models'].append(results)
            else:
                if partial_chunk:
                    ch = loaded_chunks.get(partial_chunk) or \
                         loaded_chunks.setdefault(partial_chunk, loads(self.redis.get(partial_chunk)))
                else:
                    partial_chunk = str(uuid4())
                    ch = loaded_chunks[partial_chunk] = {}

                s['models'] = [results]
                ch[s_id] = s
                chunks[s_id] = partial_chunk

                if len(ch) == chunk_size:
                    partial_chunk = None

        for c_id, chunk in loaded_chunks.items():
            self.redis.set(c_id, dumps(chunk), ex=current_app.config.get('REDIS_TTL', 86400))

    __redis_cache = __models_cache = __destinations_cache = None


def dynamic_docstring(*sub):
    def decorator(f):
        f.__doc__ = f.__doc__.format(*sub)
        return f

    return decorator
