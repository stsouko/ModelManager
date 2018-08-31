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
from flask_apispec import MethodResource, use_kwargs, marshal_with, doc
from flask_login import login_required, current_user
from marshmallow.fields import Integer
from marshmallow.validate import Range
from pony.orm import db_session
from uuid import uuid4
from .common import dynamic_docstring, JobMixin
from ..marshal import PreparingDocumentSchema, PostResponseSchema
from ...utils import abort
from ....constants import TaskType, ModelType, TaskStatus, StructureStatus, StructureType, ResultType


@doc(params={'task': {'description': 'Task ID', 'type': 'string'}})
class PrepareTask(MethodResource, JobMixin):
    @use_kwargs({'page': Integer(validate=Range(1), description='results pagination')}, locations=('query',))
    @marshal_with(PostResponseSchema, 200, 'validation task')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 403, 'user access deny. you do not have permission to this task')
    @marshal_with(None, 404, 'invalid task id. perhaps this task has already been removed')
    @marshal_with(None, 406, 'task status is invalid. only validation tasks acceptable')
    @marshal_with(None, 422, 'page must be a positive integer or None')
    @marshal_with(None, 500, 'modeling/dispatcher server error')
    @marshal_with(None, 512, 'task not ready')
    @dynamic_docstring(ModelType.PREPARER, StructureStatus.CLEAR, StructureStatus.RAW, StructureStatus.HAS_ERROR,
                       ResultType.TEXT, StructureType.REACTION, StructureType.MOLECULE)
    def get(self, task, page=None):
        """
        Task with validated structure and conditions data

        all structures has check status = {1.value} [{1.name}] - all checks passed. {3.value} [{3.name}] - structure \
        has errors. {2.value} [{2.name}] - validation failed.
        structure type also autoassigned: {5.value} [{5.name}] or {6.value} [{6.name}].

        all newly validated structures include model with type = {0.value} [{0.name}] with results containing \
        errors or warning information.
        if task not newly created by upload file or create task api it can contain models with types different from \
        {0.value} [{0.name}] which previously selected on revalidaton for structures with status = {1.value} [{1.name}].
        this models contain empty results list.

        if preparer model failed [due to server lag etc] returned structures with status = {2.value} [{2.name}] and\
        {0.name} model with empty results list. In this case possible to resend this task to revalidation as is.
        for upload task failed validation return empty structure list and resend impossible.

        model results response structure:
        key: string - header
        type: data type = {4.value} [{4.name}] - plain text information
        value: string - body
        """
        print(task, page)
        return dict(task=task, date=ended_at, status=job['status'], type=job['type'], user=current_user,
                    structures=job['structures']), 200

    @db_session
    @login_required
    @use_kwargs(PreparingDocumentSchema(many=True), locations=('json',))
    @marshal_with(PostResponseSchema, 201, 'revalidation task created')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 403, 'user access deny. you do not have permission to this task')
    @marshal_with(None, 404, 'invalid task id. perhaps this task has already been removed')
    @marshal_with(None, 406, 'task status is invalid. only validation tasks acceptable')
    @marshal_with(None, 422, 'invalid structure data')
    @marshal_with(None, 500, 'modeling/dispatcher server error')
    @marshal_with(None, 512, 'task not ready')
    @dynamic_docstring(StructureStatus.CLEAR, StructureType.REACTION, ModelType.REACTION_MODELING,
                       StructureType.MOLECULE, ModelType.MOLECULE_MODELING, StructureStatus.HAS_ERROR)
    def post(self, *data, task):
        """
        Revalidate task structures and conditions

        possible to send list of TaskStructureFields.
        send only changed data and structure id's. e.g. if user changed only temperature in structure 4 json should be
        {{"temperature": new_value, "structure": 4}} or in  list [{{"temperature": new_value, "structure": 4}}]

        unchanged data server kept as is. except structures with status {5.value} [{5.name}].
        this structures if not modified will be removed from task.

        todelete field marks structure for delete.
        example json: [{{"structure": 5, "todetele": true}}]
        structure with id 5 in task will be removed from list.

        data field should be a string containing marvin document or cml or smiles/smirks.

        models field usable if structure has status = {0.value} [{0.name}] and don't changed.
        for structure type = {1.value} [{1.name}] acceptable only model types = {2.value} [{2.name}]
        and vice versa for type = {3.value} [{3.name}] only model types = {4.value} [{4.name}].
        only model id field required. e.g. [{{"models": [{{model: 1}}], "structure": 3}}]

        for SEARCH type tasks models field unusable.

        see also task/create doc.
        """
        prepared = {s['structure']: s for s in job['structures']}
        tmp = {x['structure']: x for x in data} if isinstance(data, list) else {data['structure']: data}

        if 0 in tmp:
            abort(400, message='invalid structure data')

        preparer = Model.get_preparer_model()
        additives = Additive.get_additives_dict()
        models = Model.get_models_dict()

        structures = []
        for s, ps in prepared.items():
            if s not in tmp:
                if ps['status'] == StructureStatus.RAW:  # renew preparer model.
                    ps['models'] = [preparer.copy()]
                elif ps['status'] == StructureStatus.HAS_ERROR:
                    continue
            elif tmp[s]['todelete']:
                continue
            else:
                d = tmp[s]

                if d['data']:
                    ps['data'], ps['status'], ps['models'] = d['data'], StructureStatus.RAW, [preparer.copy()]
                elif ps['status'] == StructureStatus.RAW:  # renew preparer model.
                    ps['models'] = [preparer.copy()]
                elif ps['status'] == StructureStatus.CLEAR:
                    if d['models'] is not None:
                        ps['models'] = [models[m['model']].copy() for m in d['models'] if m['model'] in models and
                                        models[m['model']]['type'].compatible(ps['type'], job['type'])]
                    else:  # recheck models for existing
                        ps['models'] = [models[m['model']].copy() for m in ps['models'] if m['model'] in models
                                        if m['type'] != ModelType.PREPARER]
                else:
                    continue

                if d['additives'] is not None:
                    ps['additives'] = additives_check(d['additives'], additives)

                if d['temperature']:
                    ps['temperature'] = d['temperature']

                if d['pressure']:
                    ps['pressure'] = d['pressure']

                if d['description']:
                    ps['description'] = d['description']

            structures.append(ps)

        if not structures:
            abort(400, message='invalid structure data')

        new_job = redis.new_job(structures, job['user'], job['type'], TaskStatus.PREPARING)
        if new_job is None:
            abort(500, message='modeling server error')

        return dict(task=new_job['id'], status=TaskStatus.PREPARING, type=job['type'], date=new_job['created_at'],
                    user=current_user), 201
