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
from ..REST.cgrdb import database


def cmd(subparsers):
    parser = subparsers.add_parser('init_access_db', help='init cgrdb user access db',
                                   formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--user', '-u', help='admin login')
    parser.add_argument('--password', '-p', help='admin pass')
    parser.add_argument('--host', '-H', help='host name')
    parser.add_argument('--port', '-P', help='database port')
    parser.add_argument('--base', '-b', help='database name')
    parser.add_argument('--name', '-n', help='schema name', required=True)

    parser.set_defaults(func=run)


def run(args):
    db = getattr(database, args.name)
    db.bind('postgres', user=args.user, password=args.password, host=args.host, database=args.base, port=args.port)
    db.generate_mapping(create_tables=True)
