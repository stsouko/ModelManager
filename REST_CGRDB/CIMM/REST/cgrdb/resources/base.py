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
from flask import current_app
from flask_apispec import MethodResource, marshal_with, doc
from flask_login import current_user, login_required
from pony.orm import db_session, ObjectNotFound, select
from .. import database
from ..marshal import DatabaseSchema
from ...utils import abort


@doc(params={'user': {'description': 'user id', 'type': 'int'}})
class DataBases(MethodResource):
    decorators = (login_required, db_session)

    @marshal_with(DatabaseSchema, 200, 'list of databases')
    @marshal_with(None, 401, 'user not authenticated')
    def get(self, user=None):
        """
        available models list
        """
        if user is None:
            user = current_user.id
        elif user != current_user.id and not current_user.is_admin:
            abort(403, "user access deny. you do not have permission to see another user's databases")

        db = getattr(database, current_app.config['CGRDB_DB_SCHEMA'])
        try:
            user = db.User[user]
        except ObjectNotFound:
            abort(404, 'user not found')

        return list(select(x.database for x in db.UserBase if x.user == user)), 200
