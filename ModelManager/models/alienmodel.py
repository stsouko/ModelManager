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
from CGRtools.containers import ReactionContainer, MoleculeContainer
from CGRtools.files.RDFrw import RDFread, RDFwrite
from CGRtools.files.SDFrw import SDFwrite
from CIMtools.config import MOLCONVERT
from io import StringIO
from itertools import count
from json import load as json_load
from MWUI.constants import ModelType, ResultType
from pickle import load, dump
from pathlib import Path
from subprocess import call, Popen, PIPE, STDOUT
from sys import stderr
from traceback import format_exc
from ..utils import chemax_post


class Model(object):
    def __init__(self, directory):
        self.__conf = self.__load_model(directory)
        self.__type = ModelType(self.__conf.get('type'))
        if self.__type not in (ModelType.MOLECULE_MODELING, ModelType.REACTION_MODELING):
            raise Exception('Alien models must be only MODELING type')
        self.__starter = [str(directory / self.__conf['start'])]
        self.__workpath = Path('.')

    @staticmethod
    def __load_model(directory):
        with (directory / 'model.json').open() as f:
            tmp = json_load(f)
        return tmp

    def get_example(self):
        return self.__conf.get('example')

    def get_description(self):
        return self.__conf.get('desc')

    def get_name(self):
        return self.__conf.get('name')

    def get_type(self):
        return self.__type

    def set_work_path(self, workpath):
        self.__workpath = Path(workpath)

    def get_results(self, structures):
        structure_file = self.__workpath / 'structures'
        results_file = self.__workpath / 'results.csv'
        # prepare input file
        if len(structures) == 1:
            chemaxed = chemax_post('calculate/molExport',
                                   dict(structure=structures[0]['data'], parameters="rdf"))
            if not chemaxed:
                return False
            data = chemaxed['structure']
        else:
            with Popen([MOLCONVERT, 'rdf'], stdin=PIPE, stdout=PIPE, stderr=STDOUT) as convert_mol:
                data = convert_mol.communicate(input=''.join(s['data'] for s in structures).encode())[0].decode()
                if convert_mol.returncode != 0:
                    return False

        counter = count()
        with StringIO(data) as in_file, structure_file.open('w') as out_file:
            out = RDFwrite(out_file) if self.__type == ModelType.REACTION_MODELING else SDFwrite(out_file)
            for r, meta in zip(RDFread(in_file), structures):
                next(counter)
                r.meta.update(pressure=meta['pressure'], temperature=meta['temperature'])
                for n, a in enumerate(meta['additives'], start=1):
                    r.meta['additive.%d' % n] = a['name']
                    r.meta['amount.%d' % n] = '%f' % a['amount']

                if self.__type == ModelType.REACTION_MODELING and isinstance(r, ReactionContainer):
                    out.write(r)
                elif self.__type == ModelType.MOLECULE_MODELING and isinstance(r, MoleculeContainer):
                    out.write(r)

        if len(structures) != next(counter):
            return False

        if call(self.__starter, cwd=str(self.__workpath)) != 0:
            return False

        results = []
        with results_file.open() as f:
            header = [dict(key=k, type=ResultType[t]) for t, k in
                      (x.split(':') for x in next(f).rstrip().split(','))]
            for l in f:
                rep = []
                for h, v in zip(header, l.rstrip().split(',')):
                    if v:
                        tmp = dict(value=v)
                        tmp.update(h)
                        rep.append(tmp)
                results.append(dict(results=rep))

        if len(structures) != len(results):
            return False

        for s, r in zip(structures, results):
            r.update(s)
        return results


class ModelLoader(object):
    def __init__(self, **_):
        tmp = Path(__file__).resolve()
        self.__models_path = tmp.parent / tmp.stem
        self.__cache_path = self.__models_path / '.cache'

        if not self.__models_path.exists():
            self.__models_path.mkdir(mode=0o750)
        elif not self.__models_path.is_dir():
            raise Exception('path to config dir occupied by file', self.__models_path)

        if not self.__cache_path.exists():
            self.__cache_path.touch(mode=0o660)
        elif not self.__cache_path.is_file():
            raise Exception('path to cache file occupied by dir', self.__cache_path)
        elif self.__cache_path.stat().st_mode != 33200:
            self.__cache_path.chmod(0o660)

        self.__models = self.__scan_models()

    def __scan_models(self):
        if self.__cache_path.stat().st_size:
            with self.__cache_path.open('rb') as f:
                directories = {x['directory']: x for x in load(f)}
        else:
            directories = {}

        cache = {}
        for directory in (f for f in self.__models_path.iterdir() if f.is_dir() and f.suffix == '.model'):
            dir_name = directory.stem
            if dir_name not in directories:
                try:
                    model = Model(directory)
                    cache[model.get_name()] = dict(directory=dir_name, example=model.get_example(),
                                                   description=model.get_description(),
                                                   type=model.get_type(), name=model.get_name())
                except Exception:
                    print('module %s consist errors: %s' % (directory, format_exc()), file=stderr)
            else:
                cache[directories[dir_name]['name']] = directories[dir_name]

        with self.__cache_path.open('wb') as f:
            dump(list(cache.values()), f)
        return cache

    def load_model(self, name):
        if name in self.__models:
            return Model(self.__models_path / ('%s.model' % self.__models[name]['directory']))

    def get_models(self):
        return list(self.__models.values())
