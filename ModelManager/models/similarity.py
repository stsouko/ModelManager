# -*- coding: utf-8 -*-
#
#  Copyright 2016, 2017 Ramil Nugmanov <stsouko@live.ru>
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
from CGRdb import Loader
from CGRtools.files.RDFrw import RDFread
from io import StringIO
from MWUI.constants import ModelType, ResultType
from os.path import basename, dirname, join
from ..utils import chemax_post


model_name = 'Reaction Similarity'


class Model(object):
    def __init__(self):
        with open(join(dirname(__file__), basename(__file__), 'db.cfg')) as f:
            self.__db_list = f.read().split()

    @staticmethod
    def get_example():
        return None

    @staticmethod
    def get_description():
        return 'Reaction similarity wrapper'

    @staticmethod
    def get_name():
        return model_name

    @staticmethod
    def get_type():
        return ModelType.REACTION_SEARCHING

    def set_work_path(self, _):
        pass

    def get_results(self, structures):
        if len(structures) != 1:
            return False

        chemaxed = chemax_post('calculate/molExport',
                               dict(structure=structures[0]['data'], parameters='rdf'))
        if not chemaxed:
            return False

        with StringIO(chemaxed['structure']) as f:
            data = RDFread(f).read()


class ModelLoader(object):
    def __init__(self, **kwargs):
        pass

    @staticmethod
    def load_model(name):
        if name == model_name:
            return Model()

    @staticmethod
    def get_models():
        model = Model()
        return [dict(example=model.get_example(), description=model.get_description(),
                     type=model.get_type(), name=model_name)]
