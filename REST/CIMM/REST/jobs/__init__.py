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
from flask_login import LoginManager, UserMixin
from . import database
from .resources import *
from .resources.create import TaskTypeConverter
from ..utils import Documentation


class User(UserMixin):
    @property
    def id(self):
        return 1

    @property
    def is_admin(self):
        return False

    @property
    def is_authenticated(self):
        return False

    @property
    def is_anonymous(self):
        return True


def setup_database(state):
    config = state.app.config
    db = getattr(database, config['JOBS_DB_SCHEMA'])
    if db.provider is None:
        db.bind('postgres', **config['JOBS_DB_CONFIG'])
        db.generate_mapping(create_tables=False)


def setup_login(state):
    app = state.app
    if not hasattr(app, 'login_manager'):  # set login manager ad-hoc
        app.config['LOGIN_DISABLED'] = True
        LoginManager(app).anonymous_user = User


def setup_documentation(state):
    bp = state.blueprint.name
    Documentation.register(CreateTask, endpoint='create', blueprint=bp)
    Documentation.register(UploadTask, endpoint='upload', blueprint=bp)

    Documentation.register(Prepare, endpoint='prepare', blueprint=bp)
    Documentation.register(PrepareMetadata, endpoint='prepare_meta', blueprint=bp)

    Documentation.register(Process, endpoint='process', blueprint=bp)
    Documentation.register(ProcessMetadata, endpoint='process_meta', blueprint=bp)

    Documentation.register(Saved, endpoint='save', blueprint=bp)
    Documentation.register(SavedMetadata, endpoint='save_meta', blueprint=bp)
    Documentation.register(SavedList, endpoint='saves', blueprint=bp)
    Documentation.register(SavedCount, endpoint='saves_count', blueprint=bp)

    Documentation.register(AvailableModels, endpoint='models', blueprint=bp)
    Documentation.register(AvailableAdditives, endpoint='additives', blueprint=bp)
    Documentation.register(MagicNumbers, endpoint='magic', blueprint=bp)


blueprint = Blueprint('CIMM_JobsAPI', __name__)
blueprint.record_once(setup_documentation)
blueprint.record_once(setup_database)
blueprint.record_once(setup_login)
blueprint.record_once(lambda state: state.app.url_map.converters.update(TaskType=TaskTypeConverter))

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
blueprint.add_url_rule('/saves/', view_func=saved_list_view)
blueprint.add_url_rule('/saves/pages/<int(min=1):page>', view_func=saved_list_view, methods=['GET'])
blueprint.add_url_rule('/saves/pages', view_func=SavedCount.as_view('saves_count'))

blueprint.add_url_rule('/models/', view_func=AvailableModels.as_view('models'))
blueprint.add_url_rule('/additives/', view_func=AvailableAdditives.as_view('additives'))
blueprint.add_url_rule('/magic', view_func=MagicNumbers.as_view('magic'))

blueprint.add_url_rule('/subscribe', view_func=SubscribeAuth.as_view('subscribe_auth'))
blueprint.add_url_rule('/subscribe/internal/<int:channel>',
                       view_func=PubSubURL.as_view('subscribe'), methods=['GET'])
blueprint.add_url_rule('/publish/<int:channel>', view_func=PubSubURL.as_view('publish'), methods=['POST'])

_config_ = {'JOBS_DB_SCHEMA': 'postgres schema',
            'JOBS_REDIS_TIMEOUT': 'jobs run timeout',
            'JOBS_REDIS_TTL': 'jobs results save time',
            'JOBS_REDIS_CHUNK': 'amount of structures per page',
            'JOBS_REDIS_CONFIG': 'redis connection config',
            'JOBS_UPLOAD': 'path for upload of batch files',
            'JOBS_DB_CONFIG': 'dict of postgres connection config'}
