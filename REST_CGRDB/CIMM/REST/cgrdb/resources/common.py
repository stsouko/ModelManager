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
from CGRdb import Loader
from flask import current_app
from flask_login import login_required
from pony.orm import db_session
from werkzeug.routing import BaseConverter, ValidationError
from ...utils import abort


class DBFetch:
    decorators = (login_required, db_session)

    @staticmethod
    def database(name, table):
        if name not in current_app.config['CGRDB_DB_SCHEMAS']:
            abort(404, 'database not found')

        return getattr(Loader(**current_app.config['CGRDB_DB_CONFIG'])[name], table)


class DBTableConverter(BaseConverter):
    def to_python(self, value):
        if value in ('Molecule', 'MOLECULE', 'molecule', 'mol', 'm', 'M'):
            return 'MoleculeProperties', 'MOLECULE'
        if value in ('Reaction', 'REACTION', 'reaction', 'r', 'R'):
            return 'ReactionConditions', 'REACTION'
        raise ValidationError()
