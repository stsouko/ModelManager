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
from argparse import ArgumentDefaultsHelpFormatter, FileType
from collections import defaultdict
from configparser import ConfigParser
from pickle import loads, dumps
from pony.orm import db_session
from redis import Redis, ConnectionError
from requests import post
from rq import Queue
from time import sleep
from traceback import format_exc
from warnings import warn
from ..REST.jobs import database
from ..REST.jobs.utils import update_chunks


def cmd(subparsers):
    parser = subparsers.add_parser('monitor', help='register new models in db',
                                   formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--name', '-n', required=True, help='models schema name')
    parser.add_argument('--config', '-c', type=FileType(), help='configuration file')

    parser.add_argument('--postgres_user', '-u', default='postgres', help='database login')
    parser.add_argument('--postgres_pass', '-p', help='database pass')
    parser.add_argument('--postgres_host', '-H', default='localhost', help='database host name')
    parser.add_argument('--postgres_port', '-P', type=int, default=5432, help='database port')
    parser.add_argument('--postgres_base', '-b', default='postgres', help='database name')

    parser.add_argument('--redis_host', '-rh', default='localhost')
    parser.add_argument('--redis_pass', '-rp')
    parser.add_argument('--redis_port', '-rr', type=int, default=6379)

    parser.add_argument('--chunk_size', '-s', type=int, default=50)
    parser.add_argument('--task_ttl', '-t', type=int, default=86400)
    parser.add_argument('--publish_url', '-pu', help='nchan publish url')

    parser.set_defaults(func=run)


def run(args):
    if args.config is None:
        redis_host = args.redis_host
        redis_pass = args.redis_pass
        redis_port = args.redis_port

        postgres_user = args.postgres_user
        postgres_host = args.postgres_host
        postgres_pass = args.postgres_pass
        postgres_port = args.postgres_port
        postgres_base = args.postgres_base

        chunk_size = args.chunk_size
        task_ttl = args.task_ttl
        publish_url = args.publish_url
    else:
        config = ConfigParser()
        config.read_file(args.config)
        try:
            redis_host = config[args.name].get('redis_host', 'localhost')
            redis_pass = config[args.name].get('redis_pass', None)
            redis_port = config[args.name].get('redis_port', 6379)

            postgres_user = config[args.name].get('postgres_user', 'postgres')
            postgres_host = config[args.name].get('postgres_host', 'localhost')
            postgres_pass = config[args.name]['postgres_pass']
            postgres_port = config[args.name].get('postgres_port', 5432)
            postgres_base = config[args.name].get('postgres_base', 'postgres')

            chunk_size = config[args.name].get('chunk_size', 50)
            task_ttl = config[args.name].get('task_ttl', 86400)
            publish_url = config[args.name]['publish_url']
        except KeyError:
            raise KeyError('monitor config not found')

    redis = Redis(host=redis_host, port=redis_port, password=redis_pass)

    db = getattr(database, args.name)
    db.bind('postgres', user=postgres_user, password=postgres_pass, host=postgres_host, database=postgres_base,
            port=postgres_port)
    db.generate_mapping(create_tables=False)
    with db_session:
        dests = list(db.Destination.select())

    connections, channels = {}, {}
    for hpp in set((x.host, x.port, x.password) for x in dests):
        r = Redis(host=hpp[0], port=hpp[1], password=hpp[2])
        p = r.pubsub()
        p.subscribe('done_jobs')
        connections[hpp] = r
        channels[hpp] = p

    queues = defaultdict(dict)
    for x in dests:
        hpp = (x.host, x.port, x.password)
        queues[hpp][x.name] = Queue(connection=connections[hpp], name=x.name)

    while True:
        for hpp, p in channels.items():
            try:
                message = p.get_message()
                if not message or message['type'] != 'message':
                    continue

                name, _id = loads(message['data'])
                job = queues[hpp][name].fetch_job(_id)
                if not job:
                    warn(f"invalid job id '{_id}' for worker '{name}' on host '{hpp}'")
                    continue

                task_id = job.meta['task']
                task = redis.get(task_id)
                if not task:
                    warn(f"job has invalid task id '{task_id}'")
                    continue

                task = loads(task)
                task['jobs'] = [x for x in task['jobs'] if x[2] != _id]
                if job.is_finished:
                    update_chunks(task['chunks'], job, redis, chunk_size, task_ttl)
                    if job.ended_at > task['date']:
                        task['date'] = job.ended_at

                job.delete()
                redis.set(task_id, dumps(task), ex=task_ttl)

                if not task['jobs']:
                    post(publish_url + str(task['user']), data=task_id)

            except ConnectionError:
                warn(f'redis connection error:\n{format_exc()}')
        sleep(2)
