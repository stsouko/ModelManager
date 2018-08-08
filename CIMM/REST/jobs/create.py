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
from flask_restplus import Namespace
from .marshal import structure_document, post_response
from ..restplus import AuthResource
from ...constants import TaskType


api = Namespace('create', description='job creation')


@api.route('/<int:_type>')
@api.param('_type', 'Task type ID: ' + ', '.join('{0.value} - {0.name}'.format(x) for x in TaskType), _in='path')
class CreateTask(AuthResource):
    @api.expect(structure_document)
    @api.response(400, 'invalid structure data')
    @api.response(401, 'user not authenticated')
    @api.response(403, 'invalid task type')
    @api.response(500, 'modeling server error')
    @api.marshal_with(post_response, code=201, description='validation task created')
    def post(self, _type):
        """
        Create new task
        """
        print(api.payload)
