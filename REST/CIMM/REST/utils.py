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
from flask import jsonify
from flask_apispec import FlaskApiSpec
from flask_apispec.extension import make_apispec
from flask_login import current_user
from functools import wraps
from webargs.flaskparser import FlaskParser
from werkzeug.exceptions import HTTPException


def abort(code, message=None):
    """ copy-paste from flask-restful
    """
    response = jsonify(error=message)
    response.status_code = code
    raise HTTPException(response=response)


class Documentation:
    @classmethod
    def register(cls, *args, **kwargs):
        cls.__doc.register(*args, **kwargs)

    @classmethod
    def init_app(cls, app):
        if 'APISPEC_SPEC' not in app.config:
            app.config['APISPEC_SPEC'] = make_apispec('CIMM API', '2.0')
        if 'APISPEC_WEBARGS_PARSER' not in app.config:
            app.config['APISPEC_WEBARGS_PARSER'] = parser = FlaskParser()
            parser.error_handler(lambda error, *_: abort(error.status_code, error.messages))

        cls.__doc.init_app(app)

    def __init__(self, app):
        self.init_app(app)

    __doc = FlaskApiSpec()


def admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.is_admin:
            return f(*args, **kwargs)
        return abort(403, 'access denied')
    return wrapper
