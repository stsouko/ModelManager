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
from importlib import import_module
from pkgutil import iter_modules
from traceback import format_exc
from warnings import warn
from .. import models


def __getattr__(name):
    try:
        return getattr(_found_models[name], name)
    except KeyError:
        raise AttributeError(f"model '{name}' not found")


def __dir__():
    return list(_found_models)


def _scan_models():
    found_models = {}
    for module_info in iter_modules(models.__path__):
        if not module_info.ispkg:
            continue

        try:
            module = import_module(f'{__package__}.{module_info.name}')
        except:
            warn(f'{module_info.name} consist errors:\n {format_exc()}', ImportWarning)
            continue

        try:
            module_models = dir(module)
        except:
            warn(f'{module_info.name}.ModelLoader consist errors:\n {format_exc()}', ImportWarning)
            continue

        for model_name in module_models:
            if model_name in found_models:
                warn(f"{module_info.name} has conflict model name '{model_name}' with {models[model_name]}",
                     ImportWarning)
            else:
                found_models[model_name] = module
    return found_models


_found_models = _scan_models()
