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
from flask import current_app
from flask_apispec import MethodResource, use_kwargs, marshal_with, doc
from flask_login import current_user
from marshmallow.fields import String
from math import ceil
from pony.orm import flush
from .common import DBFetch
from ..marshal import RecordMetadataSchema, RecordSchema
from ...jobs.marshal import CountSchema
from ...jobs.marshal.documents import DocumentSchema
from ...jobs.resources.common import JobMixin
from ...utils import abort
from ....constants import TaskStatus, TaskType, StructureStatus, StructureType


@doc(params={'database': {'description': 'database name', 'type': 'string'},
             'table': {'description': 'table name', 'type': 'string'}})
@marshal_with(None, 401, 'user not authenticated')
@marshal_with(None, 403, 'user access deny')
class RecordsCount(DBFetch, MethodResource):
    @doc(params={'user': {'description': 'user id', 'type': 'integer'}})
    @marshal_with(CountSchema, 200, 'records amount')
    @marshal_with(None, 404, 'user/database/table not found')
    def get(self, database, table, user=None):
        """
        user's records count
        """
        q = self.select_by_user(database, table[0], user).count()
        return dict(total=q, pages=ceil(q / current_app.config.get('CGRDB_PAGESIZE', 30))), 200

    def select_by_user(self, database, table, user):
        entity, access = self.database(database, table)
        if user is None:
            user = current_user.id
        elif user != current_user.id and not access:
            abort(403, message="user access deny. you do not have permission to see another user's data")
        return entity.select(lambda x: x.user_id == user)


class RecordsFullList(RecordsCount, MethodResource):
    @doc(params={'page': {'description': 'page number', 'type': 'integer'}})
    @marshal_with(RecordSchema(many=True), 200, 'records data')
    @marshal_with(None, 404, 'page/user/database/table not found')
    def get(self, database, table, page=1, user=None):
        """
        user's records
        """
        # todo: preload structures
        return self.get_page(database, table[0], user, page), 200

    def get_page(self, database, table, user, page):
        return self.select_by_user(database, table, user).order_by(lambda x: x.id). \
            page(page, pagesize=current_app.config.get('CGRDB_PAGESIZE', 30))


class RecordsList(JobMixin, RecordsFullList):
    @marshal_with(RecordMetadataSchema(many=True), 200, 'records metadata')
    def get(self, database, table, page=1, user=None):
        return self.get_page(database, table[0], user, page), 200

    @use_kwargs({'task': String(required=True, description='task id')}, locations=('json',))
    @marshal_with(RecordSchema(many=True), 201, 'record saved')
    @marshal_with(None, 404, 'user/database/table/task not found. perhaps this task has already been removed')
    @marshal_with(None, 406, 'task status/type is invalid. only validated populating tasks acceptable')
    @marshal_with(None, 500, 'modeling/dispatcher server error')
    @marshal_with(None, 512, 'task not ready')
    def post(self, database, table, task):
        """
        add new records from task
        """
        task = self.fetch(task, TaskStatus.PREPARED)
        if task['type'] != TaskType.POPULATING:
            abort(406, message='invalid task type')

        entity = self.database(database, table[0])[0]
        data_dump = DocumentSchema(exclude=('structure', 'status', 'type'))

        res = []
        for s in task['structures']:
            if s['status'] != StructureStatus.CLEAN or s['type'] != StructureType[table[1]]:
                continue
            data = data_dump.dump(s)
            structure = s['data']
            in_db = entity.find_structure(structure)
            if not in_db:
                in_db = entity(structure, current_user)

            res.append(in_db.add_metadata(data, current_user))

        flush()
        return res, 201
