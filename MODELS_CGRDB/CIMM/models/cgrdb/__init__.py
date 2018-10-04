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
from CGRdb import Loader
from itertools import count
from functools import partial
from os import getenv
from pathlib import Path
from pony.orm import db_session
from sys import path
from ...constants import ModelType, StructureType, ResultType, StructureStatus


env = getenv('CIMM_CGR_DB')
if env:
    cfg = Path(env)
    if cfg.is_dir() and (cfg / 'config.py').is_file() and str(cfg) not in path:
        path.append(str(cfg))

try:
    from config import DB_LIST, DB_PASS, DB_HOST, DB_USER, DB_NAME, DB_PORT
except ImportError:
    raise Exception('install config.py correctly')


class ModelLoader:
    def __init__(self, name, workpath='.'):
        self.__object = name
        self.__workpath = workpath

    def __new__(cls, name, *args, **kwargs):
        if name not in cls._get_models():
            raise NameError(f"model '{name}' not found")
        return super().__new__(cls)

    def __call__(self, structures):
        if len(structures) != 1:
            return False

        res = []
        counter = count(1)
        for e, f in self.__get_dbs().items():
            with db_session:
                tmp = f(structures[0]['data'])
                if not isinstance(tmp, list):
                    tmp = [(tmp, None)]

                for r, t in tmp:
                    report = [dict(result='Database', data=e, type=ResultType.TEXT)]
                    if t is not None:
                        report.append(dict(result='Tanimoto', data=t, type=ResultType.TEXT))

                    res.append(dict(structure=next(counter), data=r.structure, type=self.__result_types[self.__object],
                                    status=StructureStatus.CLEAN, results=report))

                    for m in r.metadata:
                        d = m.data
                        if isinstance(d, dict):
                            for k, v in d.items():
                                # AD-HOC for our data
                                if k == 'additives' and isinstance(v, list) and v and isinstance(v[0], dict):
                                    report.append(dict(result=k, type=ResultType.TEXT,
                                                       data=', '.join('{0[name]} ({0[amount]})'.format(x) for x in v
                                                                      if isinstance(x, dict) and
                                                                      'name' in x and 'amount' in x)))
                                elif k == 'description' and isinstance(v, list) and v and isinstance(v[0], dict):
                                    report.append(dict(result=k, type=ResultType.TEXT,
                                                       data=', '.join('{0[key]} = {0[value]}'.format(x) for x in v
                                                                      if isinstance(x, dict)
                                                                      and 'key' in x and 'value' in x)))
                                else:
                                    report.append(dict(result=k, data=v, type=ResultType.TEXT))
        return res

    @classmethod
    def _get_models(cls):
        return list(cls.__names)

    @property
    def name(self):
        return self.__names[self.__object]

    @property
    def object(self):
        return self.__object

    @property
    def description(self):
        return f'{self.name} searcher. frontend for CGRdb lib'

    @property
    def type(self):
        return self.__types[self.__object]

    @property
    def example(self):
        return self.__examples[self.__object]

    def __get_dbs(self):
        db = Loader(password=DB_PASS, host=DB_HOST, database=DB_NAME, port=DB_PORT, workpath=self.__workpath)
        dbs = {}
        for x in DB_LIST:
            table = getattr(db[x], self.__dbes[self.__object])
            dbs[x] = getattr(table, self.__funcs[self.__object])
        return dbs

    rs = ModelType.REACTION_SEARCHING
    ms = ModelType.MOLECULE_SEARCHING
    sr = StructureType.REACTION
    sm = StructureType.MOLECULE
    er = {'data': 'CC=O>>C=CO'}
    em = {'data': 'CC=O'}

    # name, search type, database, search method (object name), result type
    __config = (('Equivalent reaction', rs, er, 'find_structure', sr, 'Reaction'),
                ('Substructure reactions', rs, er, 'find_substructures', sr, 'Reaction'),
                ('Similar reactions', rs, er, 'find_similar', sr, 'Reaction'),

                ('Equivalent molecule', ms, em, 'find_structure', sm, 'Molecule'),
                ('Substructure molecules', ms, em, 'find_substructures', sm, 'Molecule'),
                ('Similar molecules', ms, em, 'find_similar', sm, 'Molecule'),

                ('Reactions with equivalent molecule', ms, em, 'find_reaction_by_molecule', sr, 'Molecule'),
                ('Reactions with equivalent product', ms, em, 'find_reaction_by_product', sr, 'Molecule'),
                ('Reactions with equivalent reagent', ms, em, 'find_reaction_by_reagent', sr, 'Molecule'),
                ('Reactions with similar molecules', ms, em, 'find_reaction_by_similar_molecule', sr, 'Molecule'),
                ('Reactions with similar products', ms, em, 'find_reaction_by_similar_product', sr, 'Molecule'),
                ('Reactions with similar reagents', ms, em, 'find_reaction_by_similar_reagent', sr, 'Molecule'),
                ('Reactions with substructure molecules', ms, em,
                 'find_reaction_by_substructure_molecule', sr, 'Molecule'),
                ('Reactions with substructure products', ms, em,
                 'find_reaction_by_substructure_product', sr, 'Molecule'),
                ('Reactions with substructure reagents', ms, em,
                 'find_reaction_by_substructure_reagent', sr, 'Molecule'))

    __names, __types, __examples, __funcs, __dbes, __result_types = {}, {}, {}, {}, {}, {}
    for x in __config:
        y = f'{x[5]}_{x[3]}'
        __names[y] = x[0]
        __types[y] = x[1]
        __examples[y] = x[2]
        __funcs[y] = x[3]
        __result_types[y] = x[4]
        __dbes[y] = x[5]
    del x, y


def __getattr__(name):
    if name not in ModelLoader._get_models():
        raise AttributeError(f"model '{name}' not found")
    return partial(ModelLoader, name)


def __dir__():
    return ModelLoader._get_models()
