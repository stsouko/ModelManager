# -*- coding: utf-8 -*-
#
#  Copyright 2018 Ramil Nugmanov <stsouko@live.ru>
#  This file is part of CIMM (ChemoInformatics Models Manager).
#
#  CIMM is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, see <https://www.gnu.org/licenses/>.
#
from json import load
from pathlib import Path
from .constants import AdditiveType


class Additive:
    def __init__(self, amount, name=None, _id=None):
        if _id is not None:
            name = self.names[_id]
        else:
            _id = self.ids[name]

        limit = self.limits[name]

        if amount > limit:
            raise ValueError('invalid amount. expected in range [0:%d]' % self.limits[name])

        self.name = name
        self.amount = amount
        self.id = _id
        self.structure = self.structures[name]
        self.type = self.types[name]

    def __repr__(self):
        return "%s(%.5f, %s)" % (type(self).__name__, self.amount, repr(self.name))

    def __eq__(self, other):
        if isinstance(other, Additive):
            return self.name == other.name and self.amount == other.amount
        return False

    @classmethod
    def list(cls):
        return [cls(y, x) for x, y in cls.limits.items()]

    # pkg_resources.resource_string unusable for namespace packages
    with (Path(__file__).parent / 'additives.json').open() as f:
        additives = load(f)

    structures, limits, types, ids, names = {}, {}, {}, {}, {}
    for n, a in enumerate(additives, start=1):
        names[n] = name = a['name']
        structures[name] = a['structure']
        limits[name] = a['limit']
        types[name] = AdditiveType(a['type'])
        ids[name] = n
    del n, a, f, additives
