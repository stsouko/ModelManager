#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Copyright 2016, 2017 Ramil Nugmanov <stsouko@live.ru>
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
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from ModelManager import ModelSet
from ModelManager.utils import server_post
from ModelManager.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD


class DefaultList(list):
    @staticmethod
    def __copy__(*_):
        return []


def main(workers, admin_user=None, admin_pass=None):
    destinations = []
    redis_host = dict(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    for x in workers:
        tmp = redis_host.copy()
        tmp['name'] = x
        destinations.append(tmp)

    models = ModelSet().get_models()

    report = []
    for m in models:
        print('found: ', m['name'])
        report.append(dict(type=m['type'].value, name=m['name'], example=m['example'], description=m['description'],
                           destinations=destinations))

    for m in server_post(report, admin_user, admin_pass):
        print(m)


if __name__ == "__main__":
    rawopts = ArgumentParser(description="Model Register", formatter_class=ArgumentDefaultsHelpFormatter,
                             epilog="Copyright 2016, 2017 Ramil Nugmanov <stsouko@live.ru>")

    rawopts.add_argument("--name", "-n", dest='workers', action='append', type=str, default=DefaultList(['worker']),
                         help="available workers names. -n worker1 [-n worker2]")
    rawopts.add_argument("--admin_user", "-aus", type=str, default=None, help="Admin username")
    rawopts.add_argument("--admin_pass", "-apw", type=str, default=None, help="Admin password")

    main(**vars(rawopts.parse_args()))
