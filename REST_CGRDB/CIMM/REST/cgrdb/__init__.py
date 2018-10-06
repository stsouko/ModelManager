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
from flask import Blueprint
from .resources import *
from .resources.common import DBTableConverter
from ..utils import Documentation


def setup_documentation(state):
    bp = state.blueprint.name
    Documentation.register(RecordsList, endpoint='list', blueprint=bp)
    Documentation.register(RecordsFullList, endpoint='list_full', blueprint=bp)
    Documentation.register(RecordsCount, endpoint='list_count', blueprint=bp)


blueprint = Blueprint('CIMM_CGRDB_API', __name__)
blueprint.record_once(setup_documentation)
blueprint.record_once(lambda state: state.app.url_map.converters.update(DBTable=DBTableConverter))

record_list_view = RecordsList.as_view('list')
blueprint.add_url_rule('/<string:database>/<DBTable:table>', view_func=record_list_view)
blueprint.add_url_rule('/<string:database>/<DBTable:table>/pages/<int(min=1):page>',
                       view_func=record_list_view, methods=['GET'])
blueprint.add_url_rule('/<string:database>/<DBTable:table>/users/<int(min=1):user>',
                       view_func=record_list_view, methods=['GET'])
blueprint.add_url_rule('/<string:database>/<DBTable:table>/users/<int(min=1):user>/pages/<int(min=1):page>',
                       view_func=record_list_view, methods=['GET'])
