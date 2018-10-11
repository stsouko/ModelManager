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
from argparse import ArgumentDefaultsHelpFormatter, FileType
from configparser import ConfigParser
from pickle import dumps
from redis import Redis
from rq import Connection, Worker


def cmd(subparsers):
    parser = subparsers.add_parser('worker', help='start models worker',
                                   formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--name', '-n', required=True, help='worker name')
    parser.add_argument('--config', '-c', type=FileType(), help='workers configuration file')
    parser.add_argument('--redis_host', '-rh', default='localhost')
    parser.add_argument('--redis_pass', '-rp')
    parser.add_argument('--redis_port', '-rr', type=int, default=6379)

    parser.set_defaults(func=run)


def run(args):
    if args.config is None:
        redis_host = args.redis_host
        redis_pass = args.redis_pass
        redis_port = args.redis_port
    else:
        config = ConfigParser()
        config.read_file(args.config)
        try:
            redis_host = config[args.name].get('redis_host', 'localhost')
            redis_pass = config[args.name].get('redis_pass', None)
            redis_port = config[args.name].get('redis_port', 6379)
        except KeyError:
            raise KeyError(f"worker '{args.name}' config not found")

    with Connection(Redis(host=redis_host, port=redis_port, password=redis_pass)):
        EventWorker([args.name]).work()


class EventWorker(Worker):
    def execute_job(self, job, queue):
        super().execute_job(job, queue)
        self.connection.publish('done_jobs', dumps((self.queues[0].name, job.id)))
