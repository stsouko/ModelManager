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
from flask_apispec import MethodResource, use_kwargs, marshal_with, doc
from flask_login import current_user, login_required
from pickle import dumps
from pony.orm import db_session
from redis import ConnectionError
from uuid import uuid4
from werkzeug.routing import BaseConverter, ValidationError
from ..decorators import pass_db_redis
from ..marshal import DocumentSchema, PostResponseSchema
from ...utils import abort
from ....constants import TaskType, TaskStatus, StructureStatus, StructureType, ModelType


class TaskTypeConverter(BaseConverter):
    def to_python(self, value):
        try:
            return TaskType(int(value))
        except ValueError as e:
            raise ValidationError(e)


@doc(params={'_type': {'description': 'Task type ID: ' + ', '.join('{0.value} - {0.name}'.format(x) for x in TaskType),
                       'type': 'integer'}})
class CreateTask(MethodResource):
    @db_session
    @login_required
    @use_kwargs(DocumentSchema(many=True), locations=('json',))
    @marshal_with(PostResponseSchema, 201, 'validation task created')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 422, 'invalid structure data')
    @marshal_with(None, 500, 'modeling/dispatcher server error')
    @pass_db_redis
    def post(self, *data, _type, db, redis):
        """
        create new task
        """
        try:
            preparer = db.Model.get_by_type(ModelType.PREPARER)[0]
        except IndexError:
            abort(500, 'dispatcher server error')

        if _type == TaskType.SEARCHING:
            data = data[:1]

        for s, d in enumerate(data, start=1):
            d['structure'] = s

        task_id = str(uuid4())
        try:
            job_id = preparer.create_job(data, task_id, current_app.config.get('REDIS_JOB_TIMEOUT', 3600),
                                         current_app.config.get('REDIS_TTL', 86400))
        except (ConnectionError, ValueError):
            abort(500, 'modeling server error')

        redis.set(task_id, dumps({'chunks': {}, 'jobs': [(preparer.id, *job_id)], 'user': current_user.get_id(),
                                  'type': _type, 'status': TaskStatus.PREPARED}),
                  ex=current_app.config.get('REDIS_TTL', 86400))

        return dict(task=task_id, status=TaskStatus.PREPARING, type=_type, date=datetime.utcnow(),
                    user=current_user), 201
