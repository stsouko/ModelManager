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
from datetime import datetime
from flask import current_app
from flask_login import current_user
from pickle import dumps, loads
from redis import Redis, ConnectionError
from uuid import uuid4
from ..models import get_schema
from ...utils import abort
from ....constants import TaskStatus


class JobMixin:
    @staticmethod
    def enqueue(model, data, task_id=None, runner='run'):
        if task_id is None:
            task_id = str(uuid4())

        job_id = model.create_job(data, task_id,
                                  current_app.config.get('REDIS_JOB_TIMEOUT', 3600),
                                  current_app.config.get('REDIS_TTL', 86400),
                                  'CIMM.rq.' + runner)
        return job_id, task_id

    def save(self, task_id, _type, status, jobs, data=None):
        redis = self.redis
        chunks = current_app.config.get('REDIS_CHUNK', 86400)
        ex = current_app.config.get('REDIS_TTL', 86400)
        tmp = {}
        if data is not None:
            for x in range(0, len(data), chunks):  # store structures in chunks.
                _id = str(uuid4())
                chunk = {s['structure']: s for s in data[x: x + chunks]}
                redis.set(_id, dumps(chunk), ex=ex)
                for s in chunk:
                    tmp[s] = _id

        redis.set(task_id, dumps({'chunks': tmp, 'jobs': jobs, 'user': current_user.get_id(),
                                  'type': _type,
                                  'status': TaskStatus.PREPARED if status == TaskStatus.PREPARING else
                                            TaskStatus.PROCESSED}), ex=ex)

        return {'task': task_id, 'status': status, 'type': _type, 'date': datetime.utcnow(), 'user': current_user}

    @property
    def redis(self):
        redis = Redis(host=current_app.config.get('REDIS_HOST', 'localhost'),
                      port=current_app.config.get('REDIS_PORT', 6379),
                      password=current_app.config.get('REDIS_PASSWORD'))
        try:
            redis.ping()
        except ConnectionError:
            abort(500, 'dispatcher server error')
        return redis

    @property
    def models(self):
        return get_schema(current_app.config['JOBS_DB_SCHEMA']).Model

    def fetch(self, task, status, page=None):
        job = self.redis.get(task)

        if job is None:
            abort(404, message='invalid task id. perhaps this task has already been removed')

        result = loads(job)

        if result['jobs']:
            abort(512, message='PROCESSING.Task not ready')

        if result['status'] != status:
            abort(406, message='task status is invalid. task status is [%s]' % result['status'].name)

        if result['user'] != current_user.get_id():
            abort(403, message='user access deny. you do not have permission to this task')

        return result


def dynamic_docstring(*sub):
    def decorator(f):
        f.__doc__ = f.__doc__.format(*sub)
        return f

    return decorator
