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
from flask import redirect, url_for
from flask.views import MethodView
from flask_apispec import MethodResource, marshal_with, use_kwargs
from flask_login import current_user, login_required, login_user
from MWUI.logins import UserLogin
from pony.orm import db_session
from uuid import uuid4
from .marshal import UserSchema
from ..jobs.resources.common import JobMixin
from ..utils import abort
from ...constants import ModelType, TaskType, TaskStatus


class LogIn(MethodResource):
    decorators = (db_session,)

    @login_required
    @marshal_with(UserSchema(exclude=('email', 'password')), code=200)
    @marshal_with(None, 401, 'user not authenticated')
    def get(self):
        """
        get user data
        """
        return current_user

    @use_kwargs(UserSchema)
    @marshal_with(UserSchema(exclude=('email', 'password')), 201, 'authentication done')
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


class ExampleView(JobMixin, MethodView):
    @db_session
    @login_required
    def get(self, _id):
        """
        get example task
        """
        model = self.models.get(id=_id)
        if model is None or model.type not in (ModelType.MOLECULE_MODELING, ModelType.REACTION_MODELING):
            abort(404)

        preparer = self.models.select(lambda x: x._type == ModelType.PREPARER.value).first()
        if preparer is None:
            abort(500, 'dispatcher server error')

        task_id = str(uuid4())

        try:
            jobs = [self.enqueue(preparer, [model.example])[0]]
        except ConnectionError:
            abort(500, 'modeling server error')

        self.save(task_id, TaskType.MODELING, TaskStatus.PROCESSING, jobs)
        return redirect(url_for('view.predictor') + f'#/prepare/?task={task_id}')


__all__ = [LogIn.__name__, ExampleView.__name__]
