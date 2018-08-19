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
from flask import current_app
from functools import wraps
from redis import Redis, ConnectionError
from .models import get_schema
from ..utils import abort


def pass_db_redis(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        db = get_schema(current_app.config['JOBS_DB_SCHEMA'])
        redis = Redis(host=current_app.config['REDIS_HOST'], port=current_app.config['REDIS_PORT'],
                      password=current_app.config['REDIS_PASSWORD'])
        try:
            redis.ping()
        except ConnectionError:
            abort(500, 'dispatcher server error')
        return f(*args, db=db, redis=redis, **kwargs)
    return wrapper
