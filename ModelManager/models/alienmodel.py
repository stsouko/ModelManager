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
from CGRtools.files import ReactionContainer, MoleculeContainer
from CGRtools.files.RDFrw import RDFread, RDFwrite
from CGRtools.files.SDFrw import SDFwrite
from CIMtools.config import MOLCONVERT
from io import StringIO
from itertools import count
from json import load as json_load
from MWUI.constants import ModelType, ResultType
from os import listdir, mkdir, chmod
from os.path import join, abspath, splitext, exists, isdir
from pickle import load, dump
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
        self.__starter = [join(directory, self.__conf['start'])]
        self.__workpath = '.'

    @staticmethod
    def __load_model(directory):
        with open(join(directory, 'model.json')) as f:
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
        self.__workpath = workpath

    def get_results(self, structures):
        structure_file = join(self.__workpath, 'structures')
        results_file = join(self.__workpath, 'results.csv')
        # prepare input file
        if len(structures) == 1:
            chemaxed = chemax_post('calculate/molExport',
                                   dict(structure=structures[0]['data'], parameters="rdf"))
            if not chemaxed:
                return False
            data = chemaxed['structure']
        else:
            with Popen([MOLCONVERT, 'rdf'], stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=self.__workpath) as convert_mol:
                data = convert_mol.communicate(input=''.join(s['data'] for s in structures).encode())[0].decode()
                if convert_mol.returncode != 0:
                    return False

        counter = count()
        with StringIO(data) as in_file, open(structure_file, 'w') as out_file:
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

        if call(self.__starter, cwd=self.__workpath) != 0:
            return False

        results = []
        with open(results_file) as f:
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
        self.__models_path = splitext(abspath(__file__))[0]
        self.__cache_path = join(self.__models_path, '.cache')

        if not exists(self.__models_path):
            mkdir(self.__models_path, 750)
        elif not isdir(self.__models_path):
            raise Exception('path to config dir occupied by file', self.__models_path)

        self.__models = self.__scan_models()

    def __scan_models(self):
        if exists(self.__cache_path):
            with open(self.__cache_path, 'rb') as f:
                directories = {x['directory']: x for x in load(f)}
        else:
            directories = {}
        cache = {}
        for directory in (join(self.__models_path, f) for f in listdir(self.__models_path)
                          if splitext(f)[1] == '.model' and isdir(join(self.__models_path, f))):

            if directory not in directories:
                try:
                    model = Model(directory)
                    cache[model.get_name()] = dict(directory=directory, example=model.get_example(),
                                                   description=model.get_description(),
                                                   type=model.get_type(), name=model.get_name())
                except Exception:
                    print('module %s consist errors: %s' % (directory, format_exc()), file=stderr)
            else:
                cache[directories[directory]['name']] = directories[directory]
        with open(self.__cache_path, 'wb') as f:
            dump(list(cache.values()), f)
        chmod(self.__cache_path, 0o660)
        return cache

    def load_model(self, name):
        if name in self.__models:
            return Model(self.__models[name]['directory'])

    def get_models(self):
        return list(self.__models.values())
