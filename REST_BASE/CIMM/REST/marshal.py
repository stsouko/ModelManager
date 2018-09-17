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
from enum import Enum
from marshmallow.fields import Integer


class IntEnumField(Integer):
    def __init__(self, enum, **kwargs):
        self.enum = enum
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj):
        if isinstance(value, Enum):
            return super()._serialize(value.value, attr, obj)
        self.fail('not_enum')

    def _deserialize(self, value, attr, data):
        try:
            return self.enum(super()._deserialize(value, attr, data))
        except ValueError:
            self.fail('unknown_enum')

    default_error_messages = {'invalid': 'not a valid integer',
                              'not_enum': 'not a Enum', 'unknown_enum': 'not a valid Enum key'}
