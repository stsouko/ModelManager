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
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program; if not, see <https://www.gnu.org/licenses/>.
#
from importlib import import_module
from pkgutil import iter_modules
from .. import REST


def __getattr__(name):
    try:
        return _apis[name]
    except KeyError:
        raise AttributeError(f"api '{name}' not found")


def __dir__():
    return list(_apis)


def _scan_apis():
    apis = {}
    for module_info in iter_modules(REST.__path__):
        if not module_info.ispkg:
            continue
        module = import_module(f'{__package__}.{module_info.name}')
        if hasattr(module, 'blueprint'):
            apis[module.blueprint.name[5:]] = module.blueprint
    return apis


_apis = _scan_apis()
