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
from importlib import import_module
from pkgutil import iter_modules


class API:
    def __init__(self):
        self.__apis = self.__scan_api()

    def __getitem__(self, name):
        if name not in self.__apis:
            raise KeyError('api not found')
        return self.__apis[name]

    def __iter__(self):
        return list(self.__apis)

    def keys(self):
        return list(self.__apis)

    def values(self):
        return list(self.__apis.values())

    @staticmethod
    def __scan_api():
        apis = {}
        for module_info in iter_modules(import_module(__package__).__path__):
            if module_info.ispkg:
                module = import_module('{}.{}'.format(__package__, module_info.name))
                if hasattr(module, 'api') and hasattr(module, 'blueprint'):
                    apis[module_info.name] = module.blueprint

        return apis
