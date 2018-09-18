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
from marshmallow import Schema
from marshmallow.fields import String, Integer, Email
from marshmallow.validate import Length
from MWUI.constants import UserRole
from ..jobs.marshal.fields import IntEnumField


class UserSchema(Schema):
    user = Integer(dump_only=True, attribute='id', description='user id')
    name = String(dump_only=True, attribute='full_name', description='user name')
    role = IntEnumField(UserRole, dump_only=True, description='user access role')
    email = Email(load_only=True, required=True, description='user email')
    password = String(load_only=True, validate=Length(5), required=True, description='user password')
