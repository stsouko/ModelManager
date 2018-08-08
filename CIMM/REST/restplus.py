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
from flask_login import current_user
from flask_restplus import Resource, abort
from flask_restplus.fields import Integer, MarshallingError
from functools import wraps
from pony.orm import db_session


# resourses


def authenticate(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            return f(*args, **kwargs)

        abort(401, 'not authenticated')

    return wrapper


class AuthResource(Resource):
    method_decorators = [authenticate]


class DBAuthResource(AuthResource):
    method_decorators = AuthResource.method_decorators + [db_session]


# fields


class UnEnumField(Integer):
    def format(self, value):
        return value.value


class UserIDField(Integer):
    def format(self, value):
        return value.id


def enum_field_factory(enum):
    class EnumFieldMeta(type):
        def __new__(mcs, *args, **kwargs):
            return super().__new__(mcs, enum.__name__ + 'Field', *args, **kwargs)

    class EnumField(Integer, metaclass=EnumFieldMeta):
        def __init__(self, default=0, **kwargs):
            super().__init__(default=enum(default), **kwargs)

        def format(self, value):
            try:
                mt = enum(value)
            except ValueError as ve:
                raise MarshallingError(ve)
            return mt

    return EnumField
