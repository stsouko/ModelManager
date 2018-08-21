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


def __dir__():
    return list(_scan_models())


def _scan_models():
    loaders = {}
    for module_info in iter_modules(import_module(__package__).__path__):
        if module_info.ispkg:
            module = import_module(f'{__package__}.{module_info.name}')
            if hasattr(module, 'ModelLoader'):
                loaders[module_info.name] = module.ModelLoader

    available = {}
    for module_name, loader in loaders.items():
        try:
            models = loader._get_models()
        except:
            warn(f"{module_name}.ModelLoader consist errors:\n {format_exc()}", ImportWarning)
        else:
            for model_name in models:
                if model_name in available:
                    warn(f"{module_name}.ModelLoader has conflict model_name name: {model_name}", ImportWarning)
                else:
                    available[model_name] = module_name
    return available
