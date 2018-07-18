# -*- coding: utf-8 -*-
#
#  Copyright 2016-2018 Ramil Nugmanov <stsouko@live.ru>
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
from CGRtools.files import MRVwrite, MRVread
from io import StringIO, BytesIO
from itertools import count
from MWUI.constants import ModelType, ResultType, StructureType, StructureStatus
from pony.orm import db_session
from pathlib import Path


Loader.load_schemas()


class ModelLoader:
    def __init__(self, name):
        self.__type = self.__types[name][0]
        self.__func = self.__types[name][2]
        self.__structure_type = self.__types[name][3]
        self.__name = name
        self.__dbe = {x: Loader.get_database(x)[self.__types[name][1]] for x in self.__get_db_list()}
        self.__example = self.__examples[self.__types[name][1]]

    __types = {'Similar reactions': (ModelType.REACTION_SEARCHING, 1, 'find_similar', StructureType.REACTION),
               'Similar molecules': (ModelType.MOLECULE_SEARCHING, 0, 'find_similar', StructureType.MOLECULE),
               'Substructure reactions': (ModelType.REACTION_SEARCHING, 1, 'find_substructures',
                                          StructureType.REACTION),
               'Substructure molecules': (ModelType.MOLECULE_SEARCHING, 0, 'find_substructures',
                                          StructureType.MOLECULE),
               'Reaction Structure': (ModelType.REACTION_SEARCHING, 1, 'find_structure', StructureType.REACTION),
               'Molecule Structure': (ModelType.MOLECULE_SEARCHING, 0, 'find_structure', StructureType.MOLECULE),

               'Reactions contains molecule': (ModelType.MOLECULE_SEARCHING, 0, 'find_reaction_by_molecule',
                                               StructureType.REACTION),
               'Reactions contains product': (ModelType.MOLECULE_SEARCHING, 0, 'find_reaction_by_product',
                                              StructureType.REACTION),
               'Reactions contains reagent': (ModelType.MOLECULE_SEARCHING, 0, 'find_reaction_by_reagent',
                                              StructureType.REACTION),

               'Reactions with similar molecules': (ModelType.MOLECULE_SEARCHING, 0,
                                                    'find_reaction_by_similar_molecule', StructureType.REACTION),
               'Reactions with similar products': (ModelType.MOLECULE_SEARCHING, 0, 'find_reaction_by_similar_product',
                                                   StructureType.REACTION),
               'Reactions with similar reagents': (ModelType.MOLECULE_SEARCHING, 0, 'find_reaction_by_similar_reagent',
                                                   StructureType.REACTION),

               'Reactions with substructure molecules': (ModelType.MOLECULE_SEARCHING, 0,
                                                         'find_reaction_by_substructure_molecule',
                                                         StructureType.REACTION),
               'Reactions with substructure products': (ModelType.MOLECULE_SEARCHING, 0,
                                                        'find_reaction_by_substructure_product',
                                                        StructureType.REACTION),
               'Reactions with substructure reagents': (ModelType.MOLECULE_SEARCHING, 0,
                                                        'find_reaction_by_substructure_reagent', StructureType.REACTION)
               }

    __examples = ({'data': 'CC=O'}, {'data': 'CC=O>>C=CO'})

    def get_example(self):
        return self.__example

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

        with BytesIO(structures[0]['data'].encode()) as f, MRVread(f) as r:
            data = r.read()

        if len(data) != 1:
            return False

        res = []
        counter = count(1)
        for e, entity in self.__dbe.items():
            with db_session:
                tmp = getattr(entity, self.__func)(data[0])
                if isinstance(tmp, tuple):
                    it = zip(*tmp)
                elif isinstance(tmp, list):
                    it = ((x, None) for x in tmp)
                else:
                    it = [(tmp, None)]

                for r, t in it:
                    with StringIO() as f:
                        with MRVwrite(f) as w:
                            w.write(r.structure)
                        s = f.getvalue()

                    report = [dict(key='Database', value=e, type=ResultType.TEXT)]
                    if t is not None:
                        report.append(dict(key='Tanimoto', value=t, type=ResultType.TEXT))

                    res.append(dict(structure=next(counter), data=s, type=self.__structure_type,
                                    status=StructureStatus.CLEAR, results=report))

                    for m in r.metadata:
                        d = m.data
                        if isinstance(d, dict):
                            for k, v in d.items():

                                # AD-HOC for our data
                                if k == 'additives' and isinstance(v, list) and v and isinstance(v[0], dict):
                                    report.append(dict(key=k, type=ResultType.TEXT,
                                                       value=', '.join('{0[name]} ({0[amount]})'.format(x) for x in v
                                                                       if isinstance(x, dict) and
                                                                       'name' in x and 'amount' in x)))
                                elif k == 'description' and isinstance(v, list) and v and isinstance(v[0], dict):
                                    report.append(dict(key=k, type=ResultType.TEXT,
                                                       value=', '.join('{0[key]} = {0[value]}'.format(x) for x in v
                                                                       if isinstance(x, dict)
                                                                       and 'key' in x and 'value' in x)))
                                else:
                                    report.append(dict(key=k, value=v, type=ResultType.TEXT))
        return res

    @staticmethod
    def __get_db_list():
        tmp = Path(__file__).resolve()
        config_dir = tmp.parent / tmp.stem
        config_file = config_dir / 'config.ini'

        if not config_dir.exists():
            config_dir.mkdir(mode=0o750)
        elif not config_dir.is_dir():
            raise Exception('path to config dir occupied by file', config_dir)

        if not config_file.exists():
            raise Exception('not configured', config_file)
        elif config_file.stat().st_mode != 33200:
            config_file.chmod(0o660)

        with config_file.open() as f:
            db_list = f.read().split()

        return db_list

    @classmethod
    def load_model(cls, name):
        if name in cls.__types:
            return cls(name)

    @classmethod
    def get_models(cls):
        return [dict(example=x.get_example(), description=x.get_description(),
                     type=x.get_type(), name=x.get_name()) for x in (cls(x) for x in cls.__types)]
