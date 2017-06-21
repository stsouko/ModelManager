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
from pathlib import Path
from os.path import expanduser  # python 3.4 ad-hoc
from sys import stderr
from traceback import format_exc


SERVER_ROOT = 'https://cimm.kpfu.ru'
ADDITIVES = "%s/api/resources/additives" % SERVER_ROOT
CHEMAXON = "%s/webservices" % SERVER_ROOT
PREDICTOR = "%s/api/admin/models" % SERVER_ROOT

# redis server for task queue.
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = None

CGR_DB = False
WORKPATH = '/tmp'

config_list = ('CHEMAXON', 'ADDITIVES', 'PREDICTOR', 'REDIS_HOST', 'REDIS_PORT', 'REDIS_PASSWORD', 'WORKPATH', 'CGR_DB')

config_dirs = [x / '.ModelManager.ini' for x in (Path(__file__).parent, Path(expanduser('~')), Path('/etc'))]

if not any(x.exists() for x in config_dirs):
    with config_dirs[1].open('w') as f:
        f.write('\n'.join('%s = %s' % (x, y or '') for x, y in globals().items() if x in config_list))

with next(x for x in config_dirs if x.exists()).open() as f:
    for n, line in enumerate(f, start=1):
        try:
            line = line.strip()
            if line and not line.startswith('#'):
                k, v = line.split('=')
                k = k.rstrip()
                v = v.lstrip()
                if k in config_list:
                    globals()[k] = int(v) if v.isdigit() else v == 'True' if v in ('True', 'False', '') else v
        except ValueError:
            print('line %d\n\n%s\n consist errors: %s' % (n, line, format_exc()), file=stderr)
