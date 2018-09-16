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
from .resourses import *
from .resourses.create import TaskTypeConverter


docs = FlaskApiSpec()
docs.register(CreateTask, endpoint='create', blueprint='CIMM_JobsAPI')
docs.register(UploadTask, endpoint='upload', blueprint='CIMM_JobsAPI')

docs.register(Prepare, endpoint='prepare', blueprint='CIMM_JobsAPI')
docs.register(PrepareMetadata, endpoint='prepare_meta', blueprint='CIMM_JobsAPI')

docs.register(Process, endpoint='process', blueprint='CIMM_JobsAPI')
docs.register(ProcessMetadata, endpoint='process_meta', blueprint='CIMM_JobsAPI')

docs.register(Saved, endpoint='save', blueprint='CIMM_JobsAPI')
docs.register(SavedMetadata, endpoint='save_meta', blueprint='CIMM_JobsAPI')
docs.register(SavedList, endpoint='saves', blueprint='CIMM_JobsAPI')
docs.register(SavedCount, endpoint='saves_count', blueprint='CIMM_JobsAPI')


blueprint = Blueprint('CIMM_JobsAPI', __name__)
blueprint.record_once(lambda state: state.app.url_map.converters.update(TaskType=TaskTypeConverter))
blueprint.record_once(lambda state: state.app.config.update(APISPEC_SPEC=APISpec(title='Jobs API', version='1.0.0',
                                                                                 openapi_version='2.0',
                                                                                 plugins=(MarshmallowPlugin(),))))

blueprint.add_url_rule('/create/<TaskType:_type>', view_func=CreateTask.as_view('create'))
blueprint.add_url_rule('/upload', view_func=UploadTask.as_view('upload'))
blueprint.add_url_rule('/batch/<string:file>', view_func=BatchDownload.as_view('batch'))

prepare_view = Prepare.as_view('prepare')
blueprint.add_url_rule('/prepare/<string:task>', view_func=prepare_view)
blueprint.add_url_rule('/prepare/<string:task>/pages/<int(min=1):page>', view_func=prepare_view, methods=['GET'])
blueprint.add_url_rule('/prepare/<string:task>/meta', view_func=PrepareMetadata.as_view('prepare_meta'))

process_view = Process.as_view('process')
blueprint.add_url_rule('/process/<string:task>', view_func=process_view)
blueprint.add_url_rule('/process/<string:task>/pages/<int(min=1):page>', view_func=process_view, methods=['GET'])
blueprint.add_url_rule('/process/<string:task>/meta', view_func=ProcessMetadata.as_view('process_meta'))

saved_view = Saved.as_view('save')
saved_list_view = SavedList.as_view('saves')
blueprint.add_url_rule('/saves/<string:task>', view_func=saved_view)
blueprint.add_url_rule('/saves/<string:task>/pages/<int(min=1):page>', view_func=saved_view, methods=['GET'])
blueprint.add_url_rule('/saves/<string:task>/meta', view_func=SavedMetadata.as_view('save_meta'))
blueprint.add_url_rule('/saves', view_func=saved_list_view, methods=['POST'])
blueprint.add_url_rule('/saves/pages/<int(min=1):page>', view_func=saved_list_view, methods=['GET'])
blueprint.add_url_rule('/saves/pages', view_func=SavedCount.as_view('saves_count'))

# DON'T MOVE. docs.init_app should be after all routes definition
blueprint.record_once(lambda state: docs.init_app(state.app))
