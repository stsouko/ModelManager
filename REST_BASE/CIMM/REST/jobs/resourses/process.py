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
from collections import defaultdict
from flask_apispec import MethodResource, use_kwargs, marshal_with, doc
from flask_login import login_required
from itertools import chain
from marshmallow.fields import Integer
from marshmallow.validate import Range
from pony.orm import db_session
from uuid import uuid4
from .common import dynamic_docstring, JobMixin
from ..marshal import ModelingDocumentSchema, PostResponseSchema, GetResponseSchema
from ...utils import abort
from ....constants import ModelType, TaskStatus, StructureStatus, ResultType


@doc(params={'task': {'description': 'Task ID', 'type': 'string'}})
class ProcessTask(MethodResource, JobMixin):
    @db_session
    @login_required
    @use_kwargs({'page': Integer(validate=Range(1), description='results pagination')}, locations=('query',))
    @marshal_with(GetResponseSchema, 200, 'processed task')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 403, 'user access deny. you do not have permission to this task')
    @marshal_with(None, 404, 'invalid task id or page not found')
    @marshal_with(None, 406, 'task status is invalid. only processing tasks acceptable')
    @marshal_with(None, 422, 'page must be a positive integer or None')
    @marshal_with(None, 500, 'modeling/dispatcher server error')
    @marshal_with(None, 512, 'task not ready')
    @dynamic_docstring(', '.join('{0.value} - {0.name}'.format(x) for x in ResultType))
    def get(self, task, page=None):
        """
        Task with results of structures processing

        all structures include models with results lists.
        failed models contain empty results lists.

        available model results response types: {0}
        """
        task = self.fetch(task, TaskStatus.PROCESSED, page)
        self.reset_models(task['structures'])
        return task, 200

    @db_session
    @login_required
    @use_kwargs(ModelingDocumentSchema(many=True), locations=('json',))
    @marshal_with(PostResponseSchema, 201, 'processing task created')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 403, 'user access deny. you do not have permission to this task')
    @marshal_with(None, 404, 'invalid task id. perhaps this task has already been removed')
    @marshal_with(None, 406, 'task status is invalid. only validation tasks acceptable')
    @marshal_with(None, 422, 'invalid structure data')
    @marshal_with(None, 500, 'modeling/dispatcher server error')
    @marshal_with(None, 512, 'task not ready')
    @dynamic_docstring(StructureStatus.HAS_ERROR)
    def post(self, *data, task):
        """
        create processing task

        send only changed data and structure id's. e.g. if user changed only temperature in structure 4 json should be
        {{"temperature": new_value, "structure": 4}} or in  list [{{"temperature": new_value, "structure": 4}}]

        structures with status {0.value} [{0.name}] will be removed from task.
        todelete field marks structure for delete.

        example json: [{{"structure": 5, "todetele": true}}]
            structure with id 5 in task will be removed from list.
        """
        if not data:
            abort(422, message='invalid data')

        task = self.fetch(task, TaskStatus.PREPARED)
        prepared = {s['structure']: s for s in task['structures']}
        update = {x['structure']: x for x in data}
        models = {x.id: x for x in chain(self.models.get_by_type(ModelType.MOLECULE_MODELING),
                                         self.models.get_by_type(ModelType.REACTION_MODELING))}

        ready_modeling = defaultdict(list)
        for s, ps in prepared.items():
            if ps['status'] != StructureStatus.CLEAN:
                continue

            d = update[s]
            if d.get('todelete'):
                continue

            if 'additives' in d:
                ps['additives'] = d['additives']

            if 'temperature' in d:
                ps['temperature'] = d['temperature']

            if 'pressure' in d:
                ps['pressure'] = d['pressure']

            if 'description' in d:
                ps['description'] = d['description']

            if d['models']:
                ps.pop('models')
                for m in d['models']:
                    mid = m['model']
                    if mid in models and models[mid].type.compatible(ps['type'], task['type']):
                        ready_modeling[mid].append(ps)

        if not ready_modeling:
            abort(422, message='invalid data')

        task_id = str(uuid4())
        jobs = []
        for m, d in ready_modeling.items():
            try:
                jobs.append(self.enqueue(m, d, task_id=task_id)[0])
            except ConnectionError:
                pass

        if not jobs:
            abort(500, 'modeling server error. all models not accessible')

        return self.save(task_id, task['type'], TaskStatus.PROCESSING, jobs), 201
