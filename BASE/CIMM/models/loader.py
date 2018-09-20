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


def __getattr__(name):
    models = _scan_models()
    if name in models:
        module = import_module(f'{__package__}.{models[name]}')
        return getattr(module, name)
    raise AttributeError(f"model '{name}' not found")


def __dir__():
    return list(_scan_models())


def _scan_models():
    models = {}
    for module_info in iter_modules(import_module(__package__).__path__):
        if module_info.ispkg:
            module = import_module(f'{__package__}.{module_info.name}')
            if hasattr(module, 'ModelLoader'):
                try:
                    module = dir(module)
                except:
                    warn(f'{module_info.name}.ModelLoader consist errors:\n {format_exc()}', ImportWarning)

                for model_name in module:
                    if model_name in models:
                        warn(f"{module_info.name}.ModelLoader has conflict model name '{model_name}' with "
                             f"{models[model_name]}.ModelLoader", ImportWarning)
                    else:
                        models[model_name] = module_info.name
    return models
