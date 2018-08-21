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
from flask_restplus import Resource, Namespace
from .marshal import login, login_response
from ..restplus import authenticate


api = Namespace('login', description='authorization API')


class LogIn(Resource):
    @api.response(401, 'user not authenticated')
    @api.marshal_with(login_response, code=200)
    @authenticate
    def get(self):
        """
        get user data
        """
        return current_user

    @api.expect(login)
    @api.response(400, 'invalid data')
    @api.response(403, 'bad credentials')
    @api.marshal_with(login_response, code=200)
    def post(self):
        """
        get auth token

        token returned in headers as remember_token.
        for use task api send in requests headers Cookie: 'remember_token=_token_' or 'session=_session_'
        """
        data = api.payload
        user = UserLogin.get(username, password)
        if user:
            login_user(user, remember=True)
            return marshal(user, LogInResponseFields.resource_fields)
        return dict(message='bad credentials'), 403
