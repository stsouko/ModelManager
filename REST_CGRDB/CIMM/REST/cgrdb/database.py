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
from pony.orm import PrimaryKey, Required, Set, Database


__schemas = {}


def __dir__():
    return list(__schemas)


def __getattr__(schema):
    if schema in __schemas:
        return __schemas[schema]

    db = Database()

    class User(db.Entity):
        _table_ = (schema, 'user')
        id = PrimaryKey(int, auto=True)
        name = Required(str)
        databases = Set('UserBase')

    class DataBase(db.Entity):
        _table_ = (schema, 'database')
        id = PrimaryKey(int, auto=True)
        name = Required(str)
        users = Set('UserBase')

    class UserBase(db.Entity):
        _table_ = (schema, 'user_database')
        id = PrimaryKey(int, auto=True)
        user = Required('User')
        database = Required('DataBase')
        is_admin = Required(bool, default=False)

    return __schemas.setdefault(schema, db)
