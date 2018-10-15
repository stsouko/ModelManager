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
from CIMtools.preprocessing.common import iter2array
from functools import partial
from json import loads
from pickle import load
from pkg_resources import resource_string, resource_stream
from sklearn.pipeline import FeatureUnion, Pipeline
from ...constants import ModelType, ResultType


def set_work_path(steps, workpath):
    for _, step in steps:
        if isinstance(step, FeatureUnion):
            set_work_path(step.transformer_list, workpath)
        elif isinstance(step, Pipeline):
            set_work_path(step.steps, workpath)
        elif hasattr(step, 'set_work_path'):
            step.set_work_path(workpath)


class ModelLoader:
    def __init__(self, name, workpath='.'):
        self.__object = self.__models[name]
        self.__model = load(resource_stream(__package__, name))
        self.__workpath = workpath
        set_work_path(self.__model.steps, workpath)

    def __new__(cls, name, *args, **kwargs):
        if name not in cls.__models:
            raise NameError(f"model '{name}' not found")
        return super().__new__(cls)

    def __call__(self, structures):
        for s, r in zip(structures, iter2array(self.__model.predict([s['data'] for s in structures]))):
            s['results'] = [dict(result=self.__object['units'], data=f'{r:.4f}', type=ResultType.TEXT)]

        return structures

    @classmethod
    def _get_models(cls):
        return list(cls.__models)

    @property
    def name(self):
        return self.__object['name']

    @property
    def object(self):
        return self.__object['object']

    @property
    def description(self):
        return self.__object['description']

    @property
    def type(self):
        return ModelType(self.__object['type'])

    @property
    def example(self):
        return self.__object['example']

    __models = {x['object']: x for x in loads(resource_string(__package__, 'models.json').decode())}


def __getattr__(name):
    if name not in ModelLoader._get_models():
        raise AttributeError(f"model '{name}' not found")
    return partial(ModelLoader, name)


def __dir__():
    return ModelLoader._get_models()
