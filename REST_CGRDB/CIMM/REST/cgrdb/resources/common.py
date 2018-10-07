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
from flask_login import login_required, current_user
from pony.orm import db_session, ObjectNotFound
from werkzeug.routing import BaseConverter, ValidationError
from .. import database
from ...utils import abort


class DBFetch:
    decorators = (login_required, db_session)

    def database(self, name, table):
        if self.__table is None:
            db = getattr(database, current_app.config['CGRDB_DB_SCHEMA'])
            try:
                user = db.User[current_user.id]
            except ObjectNotFound:
                abort(404, 'user not found')

            base = db.DataBase.get(name=name)
            if not base:
                abort(404, 'database not found')

            access = db.UserBase.get(user=user, database=base)
            if not access:
                abort(403, 'user access to database denied')

            self.__table = getattr(current_app.config['CGRDB_LOADER'][name], table), access.is_admin

        return self.__table

    __table = None


class DBTableConverter(BaseConverter):
    def to_python(self, value):
        if value in ('Molecule', 'MOLECULE', 'molecule', 'mol', 'm', 'M'):
            return 'MoleculeProperties', 'MOLECULE'
        if value in ('Reaction', 'REACTION', 'reaction', 'r', 'R'):
            return 'ReactionConditions', 'REACTION'
        raise ValidationError()
