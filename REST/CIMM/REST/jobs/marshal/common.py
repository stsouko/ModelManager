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
from marshmallow import Schema, pre_load
from marshmallow.fields import Integer
from marshmallow.validate import ValidationError


class CountSchema(Schema):
    total = Integer(description='amount of available data')
    pages = Integer(description='amount of pages of data')
    size = Integer(description='size of page')


class EmptyCheck:
    @pre_load(pass_many=True)
    def check_empty_data(self, data, many):
        if many:
            if not isinstance(data, (list, tuple)):
                raise ValidationError('invalid data')
            if not data:
                raise ValidationError('empty data')
        return data
