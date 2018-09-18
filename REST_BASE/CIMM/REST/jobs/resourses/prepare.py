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
from flask_apispec import MethodResource, use_kwargs, marshal_with, doc
from .common import dynamic_docstring, JobMixin
from ..marshal import PreparingDocumentSchema, MetadataSchema, PreparedSchema, ExtendedMetadataSchema
from ...utils import abort
from ....constants import ModelType, TaskStatus, StructureStatus, StructureType, ResultType


@doc(params={'task': {'description': 'task id', 'type': 'string'}})
class Prepare(JobMixin, MethodResource):
    @doc(params={'page': {'description': 'page number', 'type': 'integer'}})
    @marshal_with(PreparedSchema, 200, 'validated task')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 403, 'user access deny. you do not have permission to this task')
    @marshal_with(None, 404, 'invalid task id or page not found')
    @marshal_with(None, 406, 'task status is invalid. only validation tasks acceptable')
    @marshal_with(None, 422, 'page must be a positive integer or None')
    @marshal_with(None, 500, 'modeling/dispatcher server error')
    @marshal_with(None, 512, 'task not ready')
    @dynamic_docstring(ModelType.PREPARER, StructureStatus.CLEAN, StructureStatus.RAW, StructureStatus.HAS_ERROR,
                       ResultType.TEXT, StructureType.REACTION, StructureType.MOLECULE)
    def get(self, task, page=None):
        """
        task with validated structures and conditions data

        all structures has check status = {1.value} [{1.name}] - all checks passed. {3.value} [{3.name}] - structure \
        has errors. {2.value} [{2.name}] - validation failed.
        structure type also autoassigned: {5.value} [{5.name}] or {6.value} [{6.name}].

        all newly validated structures include model with type = {0.value} [{0.name}] with results containing \
        errors or warning information.
        if task not newly created by upload file or create task api it can contain models with types different from \
        {0.value} [{0.name}] which previously selected on revalidaton for structures with status = {1.value} [{1.name}].
        this models contain empty results list.

        if preparer model failed [due to server lag etc] returned structures with status = {2.value} [{2.name}] and\
        {0.name} model with results list containing error message.
        in this case possible to resend this task to revalidation as is.
        for upload task failed validation return empty structure list and resend impossible.

        model results response structure:
        key: string - header
        type: data type = {4.value} [{4.name}] - plain text information
        value: string - body
        """
        task = self.fetch(task, TaskStatus.PREPARED, page)
        self.reset_models(task['structures'])
        return task, 200

    @use_kwargs(PreparingDocumentSchema(many=True), locations=('json',))
    @marshal_with(MetadataSchema, 201, 'revalidation task created')
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
        revalidate task structures and conditions

        send only changed data and structure id's. e.g. if user changed only temperature in structure 4 json should be
        {{"temperature": new_value, "structure": 4}} or in  list [{{"temperature": new_value, "structure": 4}}]

        unchanged data server kept as is. except structures with status {0.value} [{0.name}].
        this structures if not modified will be removed from task.
        todelete field marks structure for delete.

        example json: [{{"structure": 5, "todetele": true}}]
            structure with id 5 in task will be removed from list.
        """
        task = self.fetch(task, TaskStatus.PREPARED)
        prepared = {s['structure']: s for s in task['structures']}
        update = {x['structure']: x for x in data}

        preparer = self.models.select(lambda x: x._type == ModelType.PREPARER.value).first()
        if preparer is None:
            abort(500, 'dispatcher server error')

        need_preparing = []
        ready_modeling = []
        for s, ps in prepared.items():
            if s not in update:
                if ps['status'] == StructureStatus.RAW:  # renew preparer model.
                    del ps['models']
                    need_preparing.append(ps)
                elif ps['status'] == StructureStatus.CLEAN:
                    ready_modeling.append(ps)
            else:
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

                if 'data' in d:
                    del ps['models']
                    ps['data'], ps['status'] = d['data'], StructureStatus.RAW
                    need_preparing.append(ps)
                elif ps['status'] == StructureStatus.RAW:  # renew preparer model.
                    del ps['models']
                    need_preparing.append(ps)

                elif ps['status'] == StructureStatus.CLEAN:
                    ready_modeling.append(ps)
                else:
                    continue

        if not need_preparing:
            abort(422, message='invalid structure data')

        try:
            job_id, task_id = self.enqueue(preparer, need_preparing)
        except ConnectionError:
            abort(500, 'modeling server error')

        return self.save(task_id, task['type'], TaskStatus.PREPARING, [job_id], ready_modeling), 201


class PrepareMetadata(JobMixin, MethodResource):
    @doc(params={'task': {'description': 'task id', 'type': 'string'}})
    @marshal_with(ExtendedMetadataSchema, 200, 'saved data')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 403, 'user access deny. you do not have permission to this task')
    @marshal_with(None, 404, 'invalid task id')
    @marshal_with(None, 406, 'task status is invalid. only validation tasks acceptable')
    @marshal_with(None, 500, 'modeling/dispatcher server error')
    @marshal_with(None, 512, 'task not ready')
    def get(self, task):
        """
        get task metadata
        """
        return self.fetch_meta(task, TaskStatus.PREPARED), 200
