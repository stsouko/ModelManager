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
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Blueprint
from flask_apispec import FlaskApiSpec
from .models import get_schema
from .resourses import CreateTask
from .resourses.create import TaskTypeConverter


blueprint = Blueprint('jobs', __name__)
blueprint.record_once(lambda state: state.app.url_map.converters.update(TaskType=TaskTypeConverter))
blueprint.record_once(lambda state:
                      state.app.config.update(APISPEC_SPEC=APISpec(title='Jobs API', version='1.0.0',
                                                                   openapi_version='2.0',
                                                                   plugins=(MarshmallowPlugin(),))))

blueprint.add_url_rule('/create/<TaskType:_type>', endpoint='create', view_func=CreateTask.as_view('create'))


docs = FlaskApiSpec()
docs.register(CreateTask, endpoint='create', blueprint='jobs')
