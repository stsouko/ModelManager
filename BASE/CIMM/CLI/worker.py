# -*- coding: utf-8 -*-
#
#  Copyright 2016-2018 Ramil Nugmanov <stsouko@live.ru>
#  This file is part of CIMM (ChemoInformatics Models Manager).
#
#  CIMM is free software; you can redistribute it and/or modify
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
from redis import Redis
from rq import Connection, Worker
from ..version import version


parser = ArgumentParser(description='CIMM worker', epilog='(c) Dr. Ramil Nugmanov',
                        formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('--version', '-v', action='version', version=version(), default=False)
parser.add_argument('--name', '-n', help='worker name', required=True, type=str)
parser.add_argument('--config', '-c', default=None, type=FileType(), help='workers configuration file')
parser.add_argument('--redis_host', '-rh', default='localhost', type=str)
parser.add_argument('--redis_pass', '-rp', default=None, type=str)
parser.add_argument('--redis_port', '-rr', default=6379, type=int)


class EventWorker(Worker):
    def execute_job(self, job, queue):
        super().execute_job(job, queue)
        self.connection.publish('done_jobs', job.id)


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

    with Connection(Redis(host=redis_host, port=redis_port, password=redis_pass)):
        EventWorker([args.name]).work()
