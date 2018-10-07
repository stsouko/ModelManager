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
from CGRdb import Loader
from flask import Blueprint
from . import database
from .resources import *
from .resources.common import DBTableConverter
from ..utils import Documentation


def setup_database(state):
    config = state.app.config
    db = getattr(database, config['CGRDB_DB_SCHEMA'])
    if db.provider is None:
        db.bind('postgres', **config['CGRDB_DB_CONFIG'])
        db.generate_mapping(create_tables=False)
    config['CGRDB_LOADER'] = Loader(**config['CGRDB_LOADER_CONFIG'])


def setup_documentation(state):
    bp = state.blueprint.name
    Documentation.register(RecordsList, endpoint='list', blueprint=bp)
    Documentation.register(RecordsFullList, endpoint='list_full', blueprint=bp)
    Documentation.register(RecordsCount, endpoint='list_count', blueprint=bp)
    Documentation.register(Record, endpoint='record', blueprint=bp)
    Documentation.register(DataBases, endpoint='bases', blueprint=bp)


blueprint = Blueprint('CIMM_CGRDB_API', __name__)
blueprint.record_once(setup_documentation)
blueprint.record_once(setup_database)
blueprint.record_once(lambda state: state.app.url_map.converters.update(DBTable=DBTableConverter))

databases_view = DataBases.as_view('bases')
blueprint.add_url_rule('/', view_func=databases_view, methods=['GET'])
blueprint.add_url_rule('/users/<int(min=1):user>/', view_func=databases_view)

blueprint.add_url_rule('/<string:database>/<DBTable:table>/<int(min=1):record>', view_func=Record.as_view('record'))

records_list_view = RecordsList.as_view('list')
blueprint.add_url_rule('/<string:database>/<DBTable:table>', view_func=records_list_view)
blueprint.add_url_rule('/<string:database>/<DBTable:table>/pages/<int(min=1):page>',
                       view_func=records_list_view, methods=['GET'])
blueprint.add_url_rule('/users/<int(min=1):user>/<string:database>/<DBTable:table>',
                       view_func=records_list_view, methods=['GET'])
blueprint.add_url_rule('/users/<int(min=1):user>/<string:database>/<DBTable:table>/pages/<int(min=1):page>',
                       view_func=records_list_view, methods=['GET'])

records_list_full_view = RecordsFullList.as_view('list_full')
blueprint.add_url_rule('/<string:database>/<DBTable:table>/full', view_func=records_list_full_view)
blueprint.add_url_rule('/<string:database>/<DBTable:table>/pages/<int(min=1):page>/full',
                       view_func=records_list_full_view)
blueprint.add_url_rule('/users/<int(min=1):user>/<string:database>/<DBTable:table>/full',
                       view_func=records_list_full_view)
blueprint.add_url_rule('/users/<int(min=1):user>/<string:database>/<DBTable:table>/pages/<int(min=1):page>/full',
                       view_func=records_list_full_view)

record_list_count_view = RecordsCount.as_view('list_count')
blueprint.add_url_rule('/<string:database>/<DBTable:table>/pages', view_func=record_list_count_view)
blueprint.add_url_rule('/users/<int(min=1):user>/<string:database>/<DBTable:table>/pages',
                       view_func=record_list_count_view)
