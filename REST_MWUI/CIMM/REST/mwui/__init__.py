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
from .resources import *
from ..utils import Documentation as docs


blueprint = Blueprint('CIMM_MWUI_API', __name__)
blueprint.add_url_rule('/login', view_func=LogIn.as_view('login'))
blueprint.add_url_rule('/example/<int(min=1):_id>', view_func=LogIn.as_view('example'))

docs.register(LogIn, endpoint='login', blueprint='CIMM_MWUI_API')
docs.register(ExampleView, endpoint='example', blueprint='CIMM_MWUI_API')