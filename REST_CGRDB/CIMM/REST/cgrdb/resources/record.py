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
from flask_apispec import MethodResource, use_kwargs, marshal_with, doc
from flask_login import current_user
from marshmallow.fields import String
from pony.orm import ObjectNotFound
from .common import DBFetch
from ..marshal import RecordMetadataSchema, RecordSchema
from ...jobs.marshal.documents import DocumentSchema
from ...jobs.resources.common import JobMixin
from ...utils import abort
from ....constants import TaskStatus, TaskType, StructureStatus, StructureType


@doc(params={'database': {'description': 'database name', 'type': 'string'},
             'table': {'description': 'table name', 'type': 'string'},
             'record': {'description': 'record id', 'type': 'int'}})
@marshal_with(None, 401, 'user not authenticated')
@marshal_with(None, 403, 'user access deny')
@marshal_with(None, 404, 'user/database/table/record not found')
class Record(DBFetch, JobMixin, MethodResource):
    @marshal_with(RecordSchema, 200, 'metadata record')
    def get(self, database, table, record):
        """
        record with requested metadata id
        """
        return self.get_record(database, table[0], record), 200

    @use_kwargs({'task': String(required=True, description='task id')}, locations=('json',))
    @marshal_with(RecordSchema, 201, 'record updated')
    @marshal_with(None, 400, 'task structure has errors or invalid type')
    @marshal_with(None, 404, 'database/table/record/task not found. perhaps this task has already been removed')
    @marshal_with(None, 406, 'task status/type is invalid. only validated populating tasks acceptable')
    @marshal_with(None, 500, 'modeling/dispatcher server error')
    @marshal_with(None, 512, 'task not ready')
    def post(self, database, table, record, task):
        """
        update record from task.
        """
        task = self.fetch(task, TaskStatus.PREPARED)
        if task['type'] != TaskType.POPULATING:
            abort(406, message='invalid task type')

        record = self.get_record(database, table[0], record)
        data = task['structures'][0]
        if data['status'] != StructureStatus.CLEAN or data['type'] != StructureType[table[1]]:
            abort(400, message='task structure has errors or invalid type')

        structure = data['data']
        entity = self.database(database, table[0])
        in_db = entity.find_structure(structure)

        if in_db != record.structure:
            old = record.structure
            if in_db:
                record.structure = in_db
            else:
                record.structure = entity(structure, current_user)

            if not old.metadata.count():  # delete old structure without metadata
                old.delete()

        record.data = DocumentSchema(exclude=('structure', 'status', 'type')).dump(data)
        if record.user_id != current_user.id:
            record.user_id = current_user.id
        return record, 201

    @marshal_with(RecordMetadataSchema, 202, 'record deleted')
    def delete(self, database, table, record):
        """
        Delete record from db

        if table is REACTION and reaction consist only this metadata record, then reaction also will be deleted.
        """
        data = self.get_record(database, table[0], record)

        if data.structure.metadata.count() == 1 and table[1] == 'REACTION':
            data.structure.delete()
        else:
            data.delete()
        return data, 202

    def get_record(self, database, table, record):
        entity, access = self.database(database, table)
        try:
            data = entity[record]
        except ObjectNotFound:
            abort(404, message='invalid record id')

        if data.user_id != current_user.id and not access:
            abort(403, message="user access deny. you do not have permission to see another user's data")
        return data
