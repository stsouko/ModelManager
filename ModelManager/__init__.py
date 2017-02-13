# -*- coding: utf-8 -*-
#
#  Copyright 2015-2017 Ramil Nugmanov <stsouko@live.ru>
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
from sys import stderr
from traceback import format_exc
from os import listdir
from os.path import dirname, join


class ModelSet(object):
    def __init__(self):
        self.__models = self.__scan_models()

    @staticmethod
    def __loader(module):
        return getattr(__import__('%s.models.%s' % (__name__, module), globals(), locals()).models,
                       module).ModelLoader()

    def __scan_models(self):
        models = {}
        for module in listdir(join(dirname(__file__), 'models')):
            if module.endswith('.py') and module != '__init__.py':
                try:
                    model_loader = self.__loader(module[:-3])
                    for x in model_loader.get_models():
                        models[x['name']] = (module[:-3], x)
                except Exception:
                    print('module %s consist errors: %s' % (module, format_exc()), file=stderr)
        return models

    def load_model(self, name, workpath='.'):
        if name in self.__models:
            model = self.__loader(self.__models[name][0]).load_model(name)
            model.set_work_path(workpath)
            return model

    def get_models(self):
        return [x for _, x in self.__models.values()]
