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
from CGRtools.files.MRVrw import MRVwrite
from CGRtools.files.RDFrw import RDFread
from io import StringIO
from MWUI.constants import ModelType, ResultType
from os import mkdir
from os.path import basename, dirname, join, exists, splitext, isdir
from ..utils import chemax_post


config_dir = join(dirname(__file__), splitext(basename(__file__))[0])
config_file = join(config_dir, 'config.ini')

if not exists(config_dir):
    mkdir(config_dir, 750)
elif not isdir(config_dir):
    raise Exception('path to config dir occupied by file', config_dir)

if not exists(config_file):
    raise Exception('not configured', config_file)


class Model(object):
    def __init__(self, name):
        self.__type = self.__types[name][0]
        self.__func = self.__types[name][2]
        self.__name = name

        with open(config_file) as f:
            db_list = f.read().split()

        self.__dbs = {x: Loader.get_database(x)[self.__types[name][1]] for x in db_list}

    __types = {'Reaction Similarity': (ModelType.REACTION_SEARCHING, 1, 'find_similar'),
               'Molecule Similarity': (ModelType.MOLECULE_SEARCHING, 0, 'find_similar'),
               'Reaction Substructure': (ModelType.REACTION_SEARCHING, 1, 'find_substructures'),
               'Molecule Substructure': (ModelType.MOLECULE_SEARCHING, 0, 'find_substructures'),
               'Reaction Structure': (ModelType.REACTION_SEARCHING, 1, 'find_structure'),
               'Molecule Structure': (ModelType.MOLECULE_SEARCHING, 0, 'find_structure')}

    @staticmethod
    def get_example():
        return None

    def get_description(self):
        return '%s model. frontend for CGRdb lib.' % self.__name

    def get_name(self):
        return self.__name

    def get_type(self):
        return self.__type

    def set_work_path(self, _):
        pass

    def get_results(self, structures):
        if len(structures) != 1:
            return False

        chemaxed = chemax_post('calculate/molExport', dict(structure=structures[0]['data'], parameters='rdf'))
        if not chemaxed:
            return False

        with StringIO(chemaxed['structure']) as f:
            data = RDFread(f).read()

        if len(data) != 1:
            return False

        res = []
        for k, entity in self.__dbs.items():
            tmp = getattr(entity, self.__func)(data[0])
            for x in tmp if isinstance(tmp, list) else [tmp]:
                with StringIO() as f:
                    mrv = MRVwrite(f)
                    mrv.write(x.structure)
                    mrv.finalize()
                    dict(key='structure', value=f.getvalue(), type=ResultType.STRUCTURE)



class ModelLoader(object):
    __model_names = ('Reaction Similarity', 'Molecule Similarity',
                     'Reaction Substructure', 'Molecule Substructure',
                     'Reaction Structure', 'Molecule Structure')

    @classmethod
    def load_model(cls, name):
        if name in cls.__model_names:
            return Model(name)

    @classmethod
    def get_models(cls):
        return [dict(example=x.get_example(), description=x.get_description(),
                     type=x.get_type(), name=x.get_name()) for x in (Model(x) for x in cls.__model_names)]
