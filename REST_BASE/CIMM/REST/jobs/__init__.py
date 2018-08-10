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
from flask import Blueprint
from flask_restplus import Api
from .create import api as create
from .marshal import structure_document, description, amounted_additives, post_response


blueprint = Blueprint('jobs', __name__)
api = Api(blueprint,
          title='CIMM Jobs',
          version='1.0',
          description='CIMM Jobs REST API',
          validate=True
          )

api.models[structure_document.name] = structure_document
api.models[description.name] = description
api.models[amounted_additives.name] = amounted_additives
api.models[post_response.name] = post_response


api.add_namespace(create, path='/create')
