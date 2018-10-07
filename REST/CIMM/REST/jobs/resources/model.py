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
from flask_apispec import marshal_with, use_kwargs
from pony.orm import flush
from time import sleep
from werkzeug.exceptions import HTTPException
from .common import JobMixin
from ..marshal import DataBaseModelSchema, DeployModelSchema, PreparingDocumentSchema
from ...utils import abort, admin
from ....constants import ModelType, TaskStatus, TaskType, StructureStatus, StructureType


class AvailableModels(JobMixin):
    @marshal_with(DataBaseModelSchema(many=True), 200, 'models list')
    def get(self):
        """
        get available models list
        """
        return list(self.models.select(lambda x: x._type != ModelType.PREPARER.value)), 200

    @admin
    @use_kwargs(DeployModelSchema(many=True), locations=('json',))
    @marshal_with(DataBaseModelSchema(many=True), 201, 'accepted models list')
    @marshal_with(None, 403, 'access denied')
    @marshal_with(None, 422, 'invalid data')
    @marshal_with(None, 500, 'modeling/dispatcher server error')
    def post(self, *data):
        preparer = self.models.select(lambda x: x._type == ModelType.PREPARER.value).first()
        if preparer is None:
            abort(500, 'dispatcher server error')

        report, structures = [], []
        for n, m in enumerate(data, start=1):
            model = self.models.get(object=m['object'])
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
                if s['status'] == StructureStatus.CLEAN:
                    m = data[s['structure'] - 1]
                    if m['type'] == ModelType.PREPARER or StructureType[m['type'].name.split('_')[0]] == s['type']:
                        s['structure'] = 1
                        s = PreparingDocumentSchema(exclude=('models',)).dump(s)
                        model = self.models(type=m['type'], name=m['name'], description=m['description'],
                                            object=m['object'], example=s)
                        self.destinations(model=model, **m['destination'])
                        report.append(model)
            flush()
        return report, 201
