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
from flask import current_app
from flask_apispec import MethodResource, marshal_with
from flask_login import login_required
from pony.orm import db_session
from ..marshal import ModelSchema
from ..database import get_schema
from ....constants import ModelType


class AvailableModels(MethodResource):
    decorators = (login_required, db_session)

    @marshal_with(ModelSchema(many=True,
                              exclude=('results',
                                       'example.additives.type',
                                       'example.additives.structure',
                                       'example.additives.name')), 200, 'models list')
    @marshal_with(None, 401, 'user not authenticated')
    def get(self):
        """
        get available models list
        """
        model = get_schema(current_app.config['JOBS_DB_SCHEMA']).Model
        return list(model.select(lambda x: x._type in (ModelType.MOLECULE_MODELING.value,
                                                       ModelType.REACTION_MODELING.value))), 200
