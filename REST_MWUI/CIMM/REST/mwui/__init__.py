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
from ..utils import Documentation


def setup_documentation(state):
    bp = state.blueprint.name
    Documentation.register(LogIn, endpoint='login', blueprint=bp)


blueprint = Blueprint('CIMM_MWUI_API', __name__)
blueprint.record_once(setup_documentation)

blueprint.add_url_rule('/login', view_func=LogIn.as_view('login'))
blueprint.add_url_rule('/example/<int(min=1):_id>', view_func=ExampleView.as_view('example'))
