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
from ..constants import ModelType
from ..REST.jobs import database


def cmd(subparsers):
    parser = subparsers.add_parser('init_rest_db', help='init models db',
                                   formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--user', '-u', default='postgres', help='database login')
    parser.add_argument('--password', '-p', required=True, help='database pass')
    parser.add_argument('--host', '-H', default='localhost', help='database host name')
    parser.add_argument('--port', '-P', type=int, default=5432, help='database port')
    parser.add_argument('--base', '-b', default='postgres', help='database name')
    parser.add_argument('--name', '-n', required=True, help='access schema name')

    parser.add_argument('--worker', '-w', required=True, help='worker name')
    parser.add_argument('--redis_host', '-rh', default='localhost')
    parser.add_argument('--redis_pass', '-rp')
    parser.add_argument('--redis_port', '-rr', type=int, default=6379)

    parser.set_defaults(func=run)


def run(args):
    db = getattr(database, args.name)
    db.bind('postgres', user=args.user, password=args.password, host=args.host, database=args.base, port=args.port)
    db.generate_mapping(create_tables=True)

    with db_session:
        p = db.Model(name='Structure Preparer', description='Structure Preparer', type=ModelType.PREPARER,
                     object='Preparer', example={})
        db.Destination(model=p, name=args.worker, host=args.redis_host, port=args.redis_port, password=args.redis_pass)
