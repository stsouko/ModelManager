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
from flask_apispec import MethodResource, marshal_with
from flask_login import current_user, login_required
from pony.orm import ObjectNotFound, db_session
from werkzeug.routing import BaseConverter, ValidationError
from .. import database
from ...utils import abort


@marshal_with(None, 401, 'user not authenticated')
class DataBaseMixin(MethodResource):
    decorators = (login_required, db_session)

    @property
    def database(self):
        if self.__database is None:
            self.__database = getattr(database, current_app.config['CGRDB_DB_SCHEMA'])
        return self.__database

    def cgrdb_table(self, name, table):
        if self.__access is None:
            try:
                user = self.database.User[current_user.id]
            except ObjectNotFound:
                abort(404, 'user not found')

            base = self.database.DataBase.get(name=name)
            if not base:
                abort(404, 'database not found')

            if current_user.is_admin:
                access = current_user
            else:
                access = self.database.UserBase.get(user=user, database=base)
                if not access:
                    abort(403, 'user access to database denied')

            self.__access = access.is_admin

        return getattr(current_app.config['CGRDB_LOADER'][name], table), self.__access

    __access = __database = None


class DBTableConverter(BaseConverter):
    def to_python(self, value):
        if value in ('Molecule', 'MOLECULE', 'molecule', 'mol', 'm', 'M'):
            return 'Molecule', 'MoleculeProperties', 'MOLECULE'
        if value in ('Reaction', 'REACTION', 'reaction', 'r', 'R'):
            return 'Reaction', 'ReactionConditions', 'REACTION'
        raise ValidationError()
