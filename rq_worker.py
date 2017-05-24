#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Copyright 2017 Ramil Nugmanov <stsouko@live.ru>
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
from ModelManager.config import CGR_DB, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
from importlib.util import find_spec
from redis import Redis
from rq import Connection, Worker
from sys import argv

if CGR_DB and find_spec('CGRdb'):
    """ preload DB for speedup.
    """
    from CGRdb import Loader
    print("CGRdb preloaded")
    Loader.load_schemas()

with Connection(Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)):
    Worker(argv[1:2] or ['default']).work()
