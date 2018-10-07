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
from flask_apispec import marshal_with, use_kwargs, doc
from flask_login import current_user
from pony.orm import ObjectNotFound, max, raw_sql, select
from .common import DataBaseMixin
from ..marshal import UserSchema
from ...utils import abort, admin


@doc(params={'user': {'description': 'user id', 'type': 'int'}})
@marshal_with(None, 403, 'access denied')
@marshal_with(None, 404, 'user not found')
class User(DataBaseMixin):
    @marshal_with(UserSchema, 200, 'user data')
    def get(self, user):
        return self.get_user(user), 200

    @use_kwargs(UserSchema)
    @marshal_with(UserSchema, 201, 'user updated')
    @marshal_with(None, 422, 'invalid data')
    def post(self, user, **kwargs):
        user = self.get_user(user)
        user.name = kwargs['name']
        return user, 201

    @admin
    @marshal_with(UserSchema, 202, 'user updated')
    def delete(self, user):
        user = self.get_user(user)
        user.delete()
        return user, 202

    def get_user(self, user):
        if user != current_user.id and not current_user.is_admin:
            abort(403, 'access denied')

        try:
            user = self.database.User[user]
        except ObjectNotFound:
            abort(404, 'user not found')
        return user


class Users(DataBaseMixin):
    @marshal_with(UserSchema(many=True), 200, 'list of users')
    @marshal_with(None, 404, 'user not found')
    def get(self):
        """
        users list
        """
        if current_user.is_admin:
            return list(self.user.select()), 200

        try:
            user = self.user[current_user.id]
        except ObjectNotFound:
            abort(404, 'user not found')
        return [user], 200

    @admin
    @use_kwargs(UserSchema)
    @marshal_with(UserSchema, 201, 'user added')
    @marshal_with(None, 409, 'user already exists in db')
    @marshal_with(None, 422, 'invalid data')
    def post(self, **kwargs):
        if 'id' in kwargs:
            i = kwargs['id']
            if self.user.exists(id=i):
                abort(409, 'user already exists in db')

            if i - max(x.id for x in self.user) > 1:
                select(raw_sql("setval('user_id_seq', $(i - 1))") for x in self.user).first()

        return self.user(**kwargs)

    @property
    def user(self):
        return self.database.User
