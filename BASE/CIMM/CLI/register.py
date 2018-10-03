#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Copyright 2016-2018 Ramil Nugmanov <stsouko@live.ru>
#  This file is part of ModelManager.
#
#  ModelManager is free software; you can redistribute it and/or modify
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
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType
from configparser import ConfigParser
from requests import Session
from shutil import rmtree
from tempfile import mkdtemp
from traceback import format_exc
from warnings import warn
from ..models import loader
from ..version import version


parser = ArgumentParser(description='CIMM worker', epilog='(c) Dr. Ramil Nugmanov',
                        formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('--version', '-v', action='version', version=version(), default=False)
parser.add_argument('--name', '-n', help='worker name', required=True, type=str)
parser.add_argument('--config', '-c', type=FileType(), help='workers configuration file')
parser.add_argument('--redis_host', '-rh', default='localhost', type=str)
parser.add_argument('--redis_pass', '-rp', type=str)
parser.add_argument('--redis_port', '-rr', default=6379, type=int)
parser.add_argument('--url', '-u', type=str, help='dispatcher url', required=True)
parser.add_argument('--auth_url', '-au', type=str, help='dispatcher auth url')
parser.add_argument('--admin_user', '-aus', type=str, help='admin username')
parser.add_argument('--admin_pass', '-apw', type=str, help='admin password')


def run():
    args = parser.parse_args()

    if args.config is None:
        redis_host = args.redis_host
        redis_pass = args.redis_pass
        redis_port = args.redis_port
    else:
        config = ConfigParser().read_file(args.config)
        try:
            redis_host = config[args.name].get('redis_host', 'localhost')
            redis_pass = config[args.name].get('redis_pass', None)
            redis_port = config[args.name].get('redis_port', 6379)
        except KeyError:
            raise KeyError(f"worker '{args.name}' config not found")

    destination = dict(name=args.name, host=redis_host, port=redis_port)
    if redis_pass:
        destination['password'] = redis_pass

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
        elif q.status_code == 401:
            if not args.auth_url:
                print('need auth url')
            else:
                q = s.post(args.auth_url, json={'password': args.admin_pass, 'email': args.admin_user})
                if q.status_code != 201:
                    print('bad credentials')
                else:
                    q = s.post(args.url, json=models)
                    if q.status_code == 201:
                        print(q.json())
