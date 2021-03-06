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
from collections import defaultdict
from flask_apispec import use_kwargs, marshal_with, doc
from uuid import uuid4
from .common import dynamic_docstring, JobMixin
from ..marshal import ProcessingDocumentSchema, MetadataSchema, ProcessedSchema, ExtendedMetadataSchema
from ...utils import abort
from ....constants import TaskStatus, StructureStatus, TaskType


@doc(params={'task': {'description': 'task id', 'type': 'string'}})
@marshal_with(None, 403, 'user access deny')
@marshal_with(None, 500, 'modeling/dispatcher server error')
@marshal_with(None, 512, 'task not ready')
class ProcessMetadata(JobMixin):
    @marshal_with(ExtendedMetadataSchema, 200, 'processed task')
    @marshal_with(None, 404, 'invalid task id/status')
    def get(self, task):
        """
        get task metadata
        """
        return self.fetch_meta(task, TaskStatus.PROCESSED), 200


class Process(ProcessMetadata):
    @doc(params={'page': {'description': 'page number', 'type': 'integer'}})
    @marshal_with(ProcessedSchema, 200, 'processed task')
    @marshal_with(None, 404, 'invalid task id/status or page not found')
    def get(self, task, page=None):
        """
        Task with results of structures processing

        all structures include models with results lists.
        failed models contain empty results lists.
        """
        return self.fetch(task, TaskStatus.PROCESSED, page), 200

    @use_kwargs(ProcessingDocumentSchema(many=True), locations=('json',))
    @marshal_with(MetadataSchema, 201, 'processing task created')
    @marshal_with(None, 404, 'task is/status is invalid. only validation stage searching/modeling tasks acceptable')
    @marshal_with(None, 422, 'invalid structure data')
    @dynamic_docstring(StructureStatus.HAS_ERROR)
    def post(self, *data, task):
        """
        create processing task

        send only changed data and structure id's. e.g. if user changed only temperature in structure 4 json should be
        {{"temperature": new_value, "structure": 4}} or in  list [{{"temperature": new_value, "structure": 4}}]

        structures with status {0.value} [{0.name}] will be removed from task.
        """
        task = self.fetch(task, TaskStatus.PREPARED)
        if task['type'] == TaskType.POPULATING:
            abort(406, 'invalid task type')

        prepared = {s['structure']: s for s in task['structures']}
        update = {x['structure']: x for x in data}

        ready_modeling = defaultdict(list)
        for n, ps in prepared.items():
            if ps['status'] != StructureStatus.CLEAN:
                continue

            d = update[n]
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
                    if m.type.compatible(ps['type'], task['type']):
                        ready_modeling[m].append(ps)

        if not ready_modeling:
            abort(422, 'invalid data')

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
