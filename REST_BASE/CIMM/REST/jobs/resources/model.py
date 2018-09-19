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
from flask import Response
from flask_apispec import MethodResource, marshal_with, use_kwargs
from flask_login import current_user
from functools import wraps
from pony.orm import flush
from time import sleep
from werkzeug.exceptions import HTTPException
from .common import JobMixin
from ..marshal import DataBaseModelSchema, DeployModelSchema, PreparingDocumentSchema
from ...utils import abort
from ....constants import ModelType, TaskStatus, TaskType, StructureStatus, StructureType


def admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.is_admin:
            return f(*args, **kwargs)

        return Response('access deny', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    return wrapper


class AvailableModels(JobMixin, MethodResource):
    @marshal_with(DataBaseModelSchema(many=True), 200, 'models list')
    @marshal_with(None, 401, 'user not authenticated')
    def get(self):
        """
        get available models list
        """
        return list(self.models.select(lambda x: x._type in (ModelType.MOLECULE_MODELING.value,
                                                             ModelType.REACTION_MODELING.value))), 200

    @admin
    @use_kwargs(DeployModelSchema(many=True))
    @marshal_with(DataBaseModelSchema(many=True), 201, 'accepted models list')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 500, 'dispatcher/modeling server error')
    def post(self, *data):
        preparer = self.models.select(lambda x: x._type == ModelType.PREPARER.value).first()
        if preparer is None:
            abort(500, 'dispatcher server error')

        report, structures = [], []
        for n, m in enumerate(data, start=1):
            model = self.models.get(name=m['name'])
            if model:
                d = m['destination']
                if not self.destinations.exists(model=model, host=d['host'], port=d['port'], name=d['name']):
                    self.destinations(model=model, **d)
                    report.append(model)
            else:
                s = m['example']
                s['structure'] = n
                structures.append(s)

        if structures:
            try:
                job_id, task_id = self.enqueue(preparer, structures)
            except ConnectionError:
                abort(500, 'modeling server error')

            self.save(task_id, TaskType.MODELING, TaskStatus.PREPARING, [job_id])

            while True:
                sleep(3)
                try:
                    task = self.fetch(task_id, TaskStatus.PREPARED)
                except HTTPException:
                    pass
                else:
                    break

            for s in task['structures']:
                if s['status'] == StructureStatus.CLEAR:
                    m = data[s['structure'] - 1]
                    if m['type'] == ModelType.PREPARER or StructureType[m['type'].name.split('_')[0]] == s['type']:
                        s['structure'] = 1
                        s.pop('models')
                        s = PreparingDocumentSchema().dump(s)
                        model = self.models(type=m['type'], name=m['name'], description=m['description'], example=s)
                        self.destinations(model=model, **m['destination'])
                        report.append(model)
            flush()
        return report
