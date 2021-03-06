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
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program; if not, see <https://www.gnu.org/licenses/>.
#
from datetime import datetime
from flask import current_app
from flask_apispec import MethodResource, marshal_with
from flask_login import current_user, login_required
from pickle import dumps, loads
from pony.orm import db_session
from redis import Redis, ConnectionError
from uuid import uuid4
from .. import database
from ..utils import update_chunks
from ...utils import abort
from ....constants import TaskStatus


@marshal_with(None, 401, 'user not authenticated')
class JobMixin(MethodResource):
    decorators = (login_required, db_session)

    @staticmethod
    def enqueue(model, data, task_id=None, runner='run'):
        if task_id is None:
            task_id = str(uuid4())

        job_id = model.create_job(data, task_id, 'CIMM.models.rq.' + runner,
                                  current_app.config.get('JOBS_REDIS_TIMEOUT', 3600),
                                  current_app.config.get('JOBS_REDIS_TTL', 86400))
        return job_id, task_id

    def save(self, task_id, _type, status, jobs, data=None):
        chunks = current_app.config.get('JOBS_REDIS_CHUNK', 50)
        ex = current_app.config.get('JOBS_REDIS_TTL', 86400)
        tmp = {}
        if data:
            for x in range(0, len(data), chunks):  # store structures in chunks.
                _id = str(uuid4())
                chunk = {s['structure']: s for s in data[x: x + chunks]}
                self.redis.set(_id, dumps(chunk), ex=ex)
                for s in chunk:
                    tmp[s] = _id

        self.redis.set(task_id, dumps({'chunks': tmp, 'jobs': jobs, 'user': current_user.id,
                                       'type': _type, 'task': task_id, 'date': datetime.utcnow(),
                                       'status': TaskStatus.PREPARED if status == TaskStatus.PREPARING else
                                                 TaskStatus.PROCESSED}), ex=ex)

        return {'task': task_id, 'status': status, 'type': _type, 'date': datetime.utcnow(), 'user': current_user.id}

    @property
    def redis(self):
        if self.__redis_cache is None:
            redis = Redis(**current_app.config.get('JOBS_REDIS_CONFIG', {}))
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
        return {'structures': {'total': len(chunks), 'pages': len(set(chunks.values())) or 1,
                               'size': current_app.config.get('JOBS_REDIS_CHUNK', 50)}, **result}

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
                abort(404, 'page not found')

            ch = loads(self.redis.get(chunks[page - 1]))
            tmp = [ch[s_id] for s_id in sorted(ch)]

        return {'structures': tmp, **result}

    def __fetch(self, task_id, status):
        task = self.redis.get(task_id)

        if task is None:
            abort(404, 'invalid task id. perhaps this task has already been removed')

        task = loads(task)

        if task['status'] != status:
            abort(404, 'task with valid status not found')

        if task['user'] != current_user.id:
            abort(403, 'user access deny')

        if task['jobs']:
            jobs = [self.models.fetch_job(x) for x in task['jobs']]
            if any(x.is_queued or x.is_started for x in jobs):
                abort(512, 'PROCESSING.Task not ready')

            ended_at = task['date']
            for job in jobs:
                if job.is_finished:
                    update_chunks(task['chunks'], job, self.redis, current_app.config.get('JOBS_REDIS_CHUNK', 50),
                                  current_app.config.get('JOBS_REDIS_TTL', 86400))
                    if job.ended_at > ended_at:
                        ended_at = job.ended_at
                job.delete()

            task['jobs'] = []
            task['date'] = ended_at
            self.redis.set(task_id, dumps(task), ex=current_app.config.get('JOBS_REDIS_TTL', 86400))
        return task

    __redis_cache = __models_cache = __destinations_cache = None


def dynamic_docstring(*sub):
    def decorator(f):
        f.__doc__ = f.__doc__.format(*sub)
        return f

    return decorator
