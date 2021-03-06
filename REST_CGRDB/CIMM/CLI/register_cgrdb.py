# -*- coding: utf-8 -*-
#
#  Copyright 2018 Ramil Nugmanov <stsouko@live.ru>
#  This file is part of CIMM (ChemoInformatics Models Manager).
#
#  CIMM is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, see <https://www.gnu.org/licenses/>.
#
from argparse import ArgumentDefaultsHelpFormatter
from pony.orm import db_session
from ..REST.cgrdb import database


def cmd(subparsers):
    parser = subparsers.add_parser('register_cgrdb', help='register new structures db in cgrdb user access db',
                                   formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--user', '-u', default='postgres', help='database login')
    parser.add_argument('--password', '-p', required=True, help='database pass')
    parser.add_argument('--host', '-H', default='localhost', help='database host name')
    parser.add_argument('--port', '-P', type=int, default=5432, help='database port')
    parser.add_argument('--base', '-b', default='postgres', help='database name')
    parser.add_argument('--name', '-n', required=True, help='access schema name')
    parser.add_argument('--cgrdb', '-c', required=True, help='cgrdb schema name')

    parser.set_defaults(func=run)


def run(args):
    db = getattr(database, args.name)
    db.bind('postgres', user=args.user, password=args.password, host=args.host, database=args.base, port=args.port)
    db.generate_mapping(create_tables=False)
    with db_session:
        db.DataBase(name=args.cgrdb)
