# -*- coding: utf-8 -*-
#
#  Copyright 2018 Ramil Nugmanov <stsouko@live.ru>
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
from marshmallow import ValidationError
from json import loads
from pkg_resources import resource_string
from .constants import AdditiveType


class Additive:
    def __init__(self, name, amount):
        try:
            limit = self.limits[name]
        except KeyError:
            raise ValidationError('invalid name of additive')

        if amount > limit:
            raise ValidationError('invalid amount. expected in range [0:%d]' % self.limits[name])

        self.name = name
        self.amount = amount
        self.structure = self.structures[name]
        self.additive = self.ids[name]
        self.type = self.types[name]

    structures, limits, types, ids = {}, {}, {}, {}
    with resource_string(__package__, 'additives.json') as s:
        for n, a in enumerate(loads(s), start=1):
            structures[a['name']] = a['structure']
            limits[a['name']] = a['limit']
            types[a['name']] = AdditiveType(a['type'])
            ids[a['name']] = n
