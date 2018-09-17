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
from flask_apispec import MethodResource, marshal_with, use_kwargs
from flask_login import current_user, login_required, login_user
from MWUI.logins import UserLogin
from .marshal import UserSchema
from ..utils import abort


class LogIn(MethodResource):
    @login_required
    @marshal_with(UserSchema(exclude=('email', 'password')), code=200)
    @marshal_with(None, 401, 'user not authenticated')
    def get(self):
        """
        get user data
        """
        return current_user

    @use_kwargs(UserSchema)
    @marshal_with(UserSchema, 201, 'authentication done')
    @marshal_with(None, 403, 'bad credentials')
    @marshal_with(None, 422, 'invalid data')
    def post(self, email, password):
        """
        get auth token

        token returned in headers as remember_token.
        for use task api send in requests headers Cookie: 'remember_token=_token_' or 'session=_session_'
        """
        user = UserLogin.get(email, password)
        if not user:
            abort(403, 'bad credentials')
        login_user(user, remember=True)
        return user, 201


__all__ = [LogIn.__name__]
