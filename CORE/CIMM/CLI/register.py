# -*- coding: utf-8 -*-
#
#  Copyright 2016-2018 Ramil Nugmanov <stsouko@live.ru>
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
from requests import Session
from shutil import rmtree
from tempfile import mkdtemp
from traceback import format_exc
from warnings import warn
from ..models import loader


def cmd(subparsers):
    parser = subparsers.add_parser('register', help='register new models in db',
                                   formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--name', '-n', required=True, help='worker name')
    parser.add_argument('--redis_host', '-rh', default='localhost')
    parser.add_argument('--redis_pass', '-rp')
    parser.add_argument('--redis_port', '-rr', type=int, default=6379)
    parser.add_argument('--url', '-u', required=True, help='dispatcher url')
    parser.add_argument('--auth_url', '-au', help='dispatcher auth url')
    parser.add_argument('--admin_user', '-aus', help='admin username')
    parser.add_argument('--admin_pass', '-apw', help='admin password')

    parser.set_defaults(func=run)


def run(args):
    destination = dict(name=args.name, host=args.redis_host, port=args.redis_port)
    if args.redis_pass:
        destination['password'] = args.redis_pass

    models = []
    for m in dir(loader):
        print('found: ', m)
        workpath = mkdtemp()
        try:
            m = getattr(loader, m)(workpath)
        except:
            warn(f'Model not found or not loadable.\n{format_exc()}', ImportWarning)
        else:
            models.append(dict(name=m.name, description=m.description, type=m.type.value, example=m.example,
                               object=m.object, destination=destination))
            del m
        finally:
            rmtree(workpath)

    if models:
        s = Session()
        q = s.post(args.url, json=models)
        if q.status_code == 201:
            print(q.json())
        elif not args.auth_url:
            print('need auth url')
        else:
            q = s.post(args.auth_url, json={'password': args.admin_pass, 'email': args.admin_user})
            if q.status_code != 201:
                print('bad credentials')
            else:
                q = s.post(args.url, json=models)
                if q.status_code == 201:
                    print(q.json())
