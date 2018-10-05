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
from pony.orm import flush
from .common import DBFetch
from ..marshal import RecordMetadataSchema, RecordSchema
from ...jobs.marshal.documents import DocumentSchema
from ...jobs.resources.common import JobMixin
from ...utils import abort
from ....constants import TaskStatus, TaskType, StructureStatus, StructureType


@doc(params={'database': {'description': 'database name', 'type': 'string'},
             'table': {'description': 'table name', 'type': 'string'}})
class RecordsList(DBFetch, JobMixin, MethodResource):
    @doc(params={'page': {'description': 'page number', 'type': 'integer'},
                 'user': {'description': 'user id', 'type': 'integer'}})
    @marshal_with(RecordSchema(many=True), 200, 'saved tasks')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 403, 'user access deny')
    @marshal_with(None, 404, 'page/user/database/table not found')
    def get(self, database, table, page=1, user=None):
        """
        user's records
        """
        if user is None:
            user = current_user.id

        if user == current_user.id:
            if not current_user.is_dataminer:
                abort(403, message='user access deny. you do not have permission to database')
        elif not current_user.is_admin:
            abort(403, message="user access deny. you do not have permission to see another user's data")

        entity = getattr(self.database(database), table[0])
        q = entity.select(lambda x: x.user_id == current_user.id).order_by(lambda x: x.id).\
            page(page, pagesize=current_app.config.get('CGRDB_PAGESIZE', 30))
        # todo: preload structures
        return list(q), 200

    @use_kwargs({'task': String(required=True, description='task id')}, locations=('json',))
    @marshal_with(RecordSchema(many=True), 201, 'record saved')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 403, 'user access deny')
    @marshal_with(None, 404, 'invalid task id. perhaps this task has already been removed')
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

        if not current_user.is_dataminer:
            abort(403, message='user access deny. you do not have permission to database')

        entity = getattr(database, table[0])
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

'''
class RecordsCount(MethodResource):
    request = RequestParser(bundle_errors=True)
    request.add_argument('user', type=positive, help='User number. by default current user return. {error_msg}')

    @swagger.operation(
        nickname='records_count',
        parameters=[dict(name='database', description='DataBase name: [%s]' % ', '.join(DB_DATA_LIST), required=True,
                         allowMultiple=False, dataType='str', paramType='path'),
                    dict(name='table', description='Table name: [molecule, reaction]', required=True,
                         allowMultiple=False, dataType='str', paramType='path'),
                    dict(name='user', description='user ID', required=False,
                         allowMultiple=False, dataType='int', paramType='query')],
        responseClass=RecordsCountFields.__name__,
        responseMessages=[dict(code=200, message="saved data"),
                          dict(code=400, message="user must be a positive integer or None"),
                          dict(code=401, message="user not authenticated"),
                          dict(code=403, message="user access deny")])
    @request_arguments_parser(request)
    def get(self, database, table, user=None):
        """
        Get user's records count
        """
        if user is None:
            user = current_user.id
        if user == current_user.id:
            if not current_user.role_is((UserRole.ADMIN, UserRole.DATA_MANAGER, UserRole.DATA_FILLER)):
                abort(403, message='user access deny. You do not have permission to database')
        elif not current_user.role_is((UserRole.ADMIN, UserRole.DATA_MANAGER)):
            abort(403, message="user access deny. You do not have permission to see another user's data")

        entity = getattr(Loader.get_schema(database),
                         'ReactionConditions' if table == 'REACTION' else 'MoleculeProperties')
        q = entity.select(lambda x: x.user_id == user).count()
        return dict(data=q, pages=ceil(q / RESULTS_PER_PAGE))
'''