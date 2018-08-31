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
from flask import send_from_directory, current_app, url_for
from flask.views import MethodView
from flask_apispec import MethodResource, use_kwargs, marshal_with, doc
from flask_login import login_required
from marshmallow.fields import String, Url, Field
from pathlib import Path
from pony.orm import db_session
from uuid import uuid4
from werkzeug.routing import BaseConverter, ValidationError
from .common import JobMixin
from ..marshal import DocumentSchema, PostResponseSchema
from ...utils import abort
from ....constants import TaskType, ModelType, TaskStatus


class TaskTypeConverter(BaseConverter):
    def to_python(self, value):
        try:
            return TaskType(int(value))
        except ValueError as e:
            raise ValidationError(e)


@doc(params={'_type': {'description': 'Task type ID: ' + ', '.join('{0.value} - {0.name}'.format(x) for x in TaskType),
                       'type': 'integer'}})
class CreateTask(MethodResource, JobMixin):
    @db_session
    @login_required
    @use_kwargs(DocumentSchema(many=True), locations=('json',))
    @marshal_with(PostResponseSchema, 201, 'validation task created')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 422, 'invalid structure data')
    @marshal_with(None, 500, 'modeling/dispatcher server error')
    def post(self, *data, _type):
        """
        create new task
        """
        try:
            preparer = self.models.get_by_type(ModelType.PREPARER)[0]
        except IndexError:
            abort(500, 'dispatcher server error')

        if _type == TaskType.SEARCHING:
            data = data[:1]

        for s, d in enumerate(data, start=1):
            d['structure'] = s

        try:
            job_id, task_id = self.enqueue(preparer, data)
        except (ConnectionError, ValueError):
            abort(500, 'modeling server error')

        return self.save(task_id, _type, TaskStatus.PREPARING, [job_id]), 201


class UploadTask(MethodResource, JobMixin):
    @db_session
    @login_required
    @use_kwargs({'file_path': String(attribute='file.path'), 'file_url': Url(attribute='file.url'),
                 'structures': Field()}, locations=('files', ))
    @marshal_with(PostResponseSchema, 201, 'validation task created')
    @marshal_with(None, 400, 'structure file required')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 500, 'modeling/dispatcher server error')
    def post(self, structures=None, file_url=None, file_path=None):
        """
        Structures file upload

        Create validation task from uploaded structures file
        Need for batch modeling mode.
        Any chemical structure formats convertable with Chemaxon JChem can be passed.

        conditions in files should be present in next key-value format:
        additive.amount.1 --> string = float [possible delimiters: :, :=, =]
        temperature --> float
        pressure --> float
        additive.2 --> string
        amount.2 --> float
        where .1[.2] is index of additive. possible set multiple additives.

        example [RDF]:
        $DTYPE additive.amount.1
        $DATUM water = .4
        $DTYPE temperature
        $DATUM 298
        $DTYPE pressure
        $DATUM 0.9
        $DTYPE additive.2
        $DATUM DMSO
        $DTYPE amount.2
        $DATUM 0.6

        parsed as:
        temperature = 298
        pressure = 0.9
        additives = [{"name": "water", "amount": 0.4, "type": x, "additive": y1}, \
                     {"name": "DMSO", "amount": 0.6, "type": x, "additive": y2}]
        where "type" and "additive" obtained from DataBase by name

        see task/create doc about acceptable conditions values and additives types and response structure.
        """
        try:
            preparer = self.models.get_by_type(ModelType.PREPARER)[0]
        except IndexError:
            abort(500, 'dispatcher server error')

        if file_url is None:  # smart frontend
            upload_root = Path(current_app.config['JOBS_UPLOAD'])
            if file_path:  # NGINX upload
                file_name = Path(file_path).name
                if (upload_root / file_name).exists():
                    file_url = url_for('.batch', file=file_name, _external=True)
            elif structures:  # flask
                file_name = str(uuid4())
                structures.save((upload_root / file_name).as_posix())
                file_url = url_for('.batch', file=file_name, _external=True)

            if file_url is None:
                abort(400, message='structure file required')
        try:
            job_id, task_id = self.enqueue(preparer, file_url, runner='convert')
        except (ConnectionError, ValueError):
            abort(500, 'modeling server error')

        return self.save(task_id, TaskType.MODELING, TaskStatus.PREPARING, [job_id]), 201


class BatchDownload(MethodView):
    def get(self, file):
        return send_from_directory(directory=current_app.config['JOBS_UPLOAD'], filename=file)
