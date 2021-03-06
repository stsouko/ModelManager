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
from pony.orm import PrimaryKey, Required, Optional, Set, Json, Database
from redis import Redis, ConnectionError
from rq import Queue
from ...constants import ModelType


__schemas = {}


def __dir__():
    return list(__schemas)


def __getattr__(schema):
    if schema in __schemas:
        return __schemas[schema]

    db = Database()

    class Model(db.Entity):
        _table_ = (schema, 'model')
        id = PrimaryKey(int, auto=True)
        name = Required(str, unique=True)
        description = Required(str)
        object = Required(str, unique=True)
        example = Required(Json, lazy=True)
        destinations = Set('Destination')
        _type = Required(int, column='type')

        def __init__(self, **kwargs):
            _type = kwargs.pop('type').value
            super().__init__(_type=_type, **kwargs)

        @property
        def type(self):
            return ModelType(self._type)

        def create_job(self, structures, task_id, runner, job_timeout=3600, result_ttl=86400):
            qs = []
            for d in self.destinations:
                try:
                    q = d.get_queue(job_timeout)
                    qs.append((d, q))
                except ConnectionError:
                    pass
            try:
                d, q = min(qs, key=lambda x: len(x[1]))
            except ValueError:
                raise ConnectionError

            return self.id, d.id, q.enqueue_call(runner, kwargs={'structures': structures, 'model': self.object},
                                                 result_ttl=result_ttl,
                                                 meta={'task': task_id, 'model': self.id, 'destination': d.id}).id

        @classmethod
        def fetch_job(cls, job_id):
            m_id, d_id, q_id = job_id
            model = cls.get(id=m_id)
            if model is None:
                raise KeyError('invalid model')
            dest = Destination.get(id=d_id)
            if dest is None:
                raise KeyError('invalid destination')

            queue = dest.get_queue()
            job = queue.fetch_job(q_id)
            if job is None:
                raise KeyError('invalid job')
            return job

    class Destination(db.Entity):
        _table_ = (schema, 'destination')
        id = PrimaryKey(int, auto=True)
        host = Required(str)
        model = Required('Model')
        name = Required(str)
        password = Optional(str)
        port = Required(int, default=6379)

        def __init__(self, **kwargs):
            super().__init__(**{x: y for x, y in kwargs.items() if y})

        def get_queue(self, job_timeout=3600):
            r = Redis(host=self.host, port=self.port, password=self.password)
            r.ping()
            return Queue(connection=r, name=self.name, default_timeout=job_timeout)

    class Task(db.Entity):
        _table_ = (schema, 'task')
        id = PrimaryKey(int, auto=True)
        task = Required(str, unique=True, sql_type='CHARACTER(36)')
        date = Required(datetime)
        size = Required(int)
        user = Required(int)
        data = Required(Json, lazy=True)

        def __init__(self, data, **kwargs):
            super().__init__(data=data, size=len(data), **kwargs)

    return __schemas.setdefault(schema, db)
