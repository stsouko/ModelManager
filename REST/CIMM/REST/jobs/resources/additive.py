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
from flask_apispec import MethodResource, marshal_with
from flask_login import login_required
from ..marshal import AdditiveSchema
from ....additives import Additive


class AvailableAdditives(MethodResource):
    @login_required
    @marshal_with(AdditiveSchema(many=True, exclude=('amount',)), 200, 'additives list')
    @marshal_with(None, 401, 'user not authenticated')
    def get(self):
        """
        get available additives list
        """
        return Additive.list(), 200
