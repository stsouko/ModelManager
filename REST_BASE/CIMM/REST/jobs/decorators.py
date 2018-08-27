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
from functools import wraps
from pickle import dumps
from redis import Redis, ConnectionError
from uuid import uuid4
from .models import get_schema
from ..utils import abort
from ...constants import TaskStatus


def pass_db(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        db = get_schema(current_app.config['JOBS_DB_SCHEMA'])
        return f(self, *args, db=db, **kwargs)
    return wrapper


def pass_redis(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        redis = Redis(host=current_app.config.get('REDIS_HOST', 'localhost'),
                      port=current_app.config.get('REDIS_PORT', 6379),
                      password=current_app.config.get('REDIS_PASSWORD'))
        try:
            redis.ping()
        except ConnectionError:
            abort(500, 'dispatcher server error')
        return f(self, *args, redis=redis, **kwargs)

    return wrapper


def create_job(f):
    @wraps(f)
    def wrapper(self, *args, redis, **kwargs):
        data, _type, model, code, *func = f(self, *args, **kwargs)
        func = func[0] if func else 'run'
        ac = current_app.config
        task_id = str(uuid4())
        try:
            job_id = model.create_job(data, task_id, ac.get('REDIS_JOB_TIMEOUT', 3600), ac.get('REDIS_TTL', 86400),
                                      'CIMM.rq.' + func)
        except (ConnectionError, ValueError):
            abort(500, 'modeling server error')

        redis.set(task_id, dumps({'chunks': {}, 'jobs': [(model.id, *job_id)], 'user': current_user.get_id(),
                                  'type': _type, 'status': TaskStatus.PREPARED}), ex=ac.get('REDIS_TTL', 86400))

        return dict(task=task_id, status=TaskStatus.PREPARING, type=_type, date=datetime.utcnow(),
                    user=current_user), code
    return wrapper
