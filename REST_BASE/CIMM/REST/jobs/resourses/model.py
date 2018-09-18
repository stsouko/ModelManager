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
from flask import current_app, Response
from flask_apispec import MethodResource, marshal_with, use_kwargs
from flask_login import login_required, current_user
from functools import wraps
from pony.orm import db_session
from ..marshal import DataBaseModelSchema, DeployModelSchema
from ..database import get_schema
from ....constants import ModelType


def admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.is_admin:
            return f(*args, **kwargs)

        return Response('access deny', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    return wrapper


class AvailableModels(MethodResource):
    decorators = (login_required, db_session)

    @marshal_with(DataBaseModelSchema(many=True), 200, 'models list')
    @marshal_with(None, 401, 'user not authenticated')
    def get(self):
        """
        get available models list
        """
        return list(self.models.select(lambda x: x._type in (ModelType.MOLECULE_MODELING.value,
                                                             ModelType.REACTION_MODELING.value))), 200

    @admin
    @use_kwargs(DeployModelSchema)
    @marshal_with(DataBaseModelSchema, 201, 'models list')
    @marshal_with(None, 401, 'user not authenticated')
    def post(self):
        pass

    @property
    def models(self):
        return get_schema(current_app.config['JOBS_DB_SCHEMA']).Model
