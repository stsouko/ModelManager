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
from flask_apispec import marshal_with, doc, use_kwargs
from flask_login import current_user
from pony.orm import ObjectNotFound, flush
from .common import DataBaseMixin
from ..marshal import DatabaseSchema
from ...utils import abort, admin


@doc(params={'user': {'description': 'user id', 'type': 'int'}})
@marshal_with(None, 401, 'user not authenticated')
@marshal_with(None, 403, 'access denied')
@marshal_with(None, 404, 'user/database not found')
class DataBases(DataBaseMixin):
    @marshal_with(DatabaseSchema(many=True), 200, 'list of databases')
    def get(self, user=None):
        """
        available for user database list
        """
        if user is None:
            if current_user.is_admin:
                return [{'database': x, 'is_admin': True} for x in self.database.DataBase.select()]
            user = current_user.id
        elif user != current_user.id and not current_user.is_admin:
            abort(403, "user access deny. you do not have permission to see another user's databases")

        try:
            user = self.database.User[user]
        except ObjectNotFound:
            abort(404, 'user not found')

        return list(self.database.UserBase.select(lambda x: x.user == user).prefetch(self.database.DataBase)), 200

    @admin
    @use_kwargs(DatabaseSchema)
    @marshal_with(DatabaseSchema, 201, 'database added to user')
    @marshal_with(DatabaseSchema, 202, 'database access rights updated')
    @marshal_with(None, 409, 'user already has this db')
    def post(self, user, name, is_admin):
        try:
            user = self.database.User[user]
        except ObjectNotFound:
            abort(404, 'user not found')

        base = self.database.DataBase.get(name=name)
        if not base:
            abort(404, 'database not found')

        exists = self.database.UserBase.get(user=user, database=base)
        if exists:
            if exists.is_admin == is_admin:
                abort(409, 'user already has this db')
            exists.is_admin = is_admin
            return exists, 202
        new = self.database.UserBase(user=user, database=base)
        flush()
        return new, 201
