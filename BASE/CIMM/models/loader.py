# -*- coding: utf-8 -*-
#
#  Copyright 2015-2018 Ramil Nugmanov <stsouko@live.ru>
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
from traceback import format_exc
from warnings import warn


class Models:
    def __init__(self, workpath='.'):
        self.__models = self.__scan_models()
        self.__workpath = workpath

    def __getitem__(self, name):
        if name not in self.__models:
            raise KeyError('model not found')
        return self.__models[name][0](name, workpath=self.__workpath)

    def __iter__(self):
        return list(self.__models)

    def keys(self):
        return list(self.__models)

    def values(self):
        return [x for _, x in self.__models.values()]

    @staticmethod
    def __scan_models():
        loaders = {}
        for module_info in iter_modules(import_module(__package__).__path__):
            if module_info.ispkg:
                module = import_module('{}.{}'.format(__package__, module_info.name))
                if hasattr(module, 'ModelLoader'):
                    loaders[module_info.name] = module.ModelLoader

        available = {}
        for modname, loader in loaders.items():
            try:
                models = loader.get_models()
            except:
                warn('ModelLoader %s consist errors:\n %s' % (modname, format_exc()), ImportWarning)
            else:
                for model in models:
                    available[model['name']] = loader, model
        return available
