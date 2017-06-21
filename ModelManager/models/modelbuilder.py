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
from bz2 import open as bz2_open
from CGRtools.files.RDFrw import RDFread
from CGRtools.files.SDFrw import SDFread
from CIMtools.config import MOLCONVERT
from CIMtools.estimators.svmodel import SVModel
from collections import defaultdict
from functools import reduce
from hashlib import md5
from io import StringIO
from math import ceil
from MWUI.constants import ModelType, ResultType
from pandas import Series, merge
from pathlib import Path
from pickle import load, dump
from subprocess import Popen, PIPE, STDOUT
from sys import stderr
from traceback import format_exc
from ..consensus import ConsensusDragos
from ..utils import chemax_post


class Model(ConsensusDragos):
    def __init__(self, file):
        tmp = load(bz2_open(str(file), 'rb'))
        self.__models = [SVModel.unpickle(x) for x in tmp['models']]
        self.__conf = tmp['config']
        self.__workpath = '.'

        self.Nlim = self.__conf.get('nlim', 1)
        self.TOL = self.__conf.get('tol', 1e10)
        self.__units = self.__conf.get('report_units')
        self.__show_structures = self.__conf.get('show_structures')

    def get_example(self):
        return self.__conf.get('example')

    def get_description(self):
        return self.__conf.get('desc')

    def get_name(self):
        return self.__conf['name']

    def get_type(self):
        return ModelType(self.__conf['type'])

    def set_work_path(self, workpath):
        self.__workpath = workpath
        for m in self.__models:
            m.set_work_path(workpath)

    @property
    def __format(self):
        return "rdf" if self.get_type() == ModelType.REACTION_MODELING else "sdf"

    @staticmethod
    def __merge_wrap(x, y):
        return merge(x, y, how='outer', left_index=True, right_index=True)

    @staticmethod
    def __report_atoms(atoms):
        return atoms and ' [Modeled site atoms: %s]' % ', '.join(str(x) for x in atoms) or ''

    def get_results(self, structures):
        # prepare input file
        if len(structures) == 1:
            chemaxed = chemax_post('calculate/molExport',
                                   dict(structure=structures[0]['data'], parameters=self.__format))
            if not chemaxed:
                return False
            additions = dict(pressure=structures[0]['pressure'], temperature=structures[0]['temperature'])
            for n, a in enumerate(structures[0]['additives'], start=1):
                additions['additive.%d' % n] = a['name']
                additions['amount.%d' % n] = a['amount']

            data_str = chemaxed['structure']
        else:
            with Popen([MOLCONVERT, self.__format],
                       stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=self.__workpath) as convert_mol:
                data_str = convert_mol.communicate(input=''.join(s['data'] for s in structures).encode())[0].decode()
                if convert_mol.returncode != 0:
                    return False

            additions = dict(pressure=[], temperature=[])
            for m, s in enumerate(structures):
                additions['pressure'].append(s['pressure'])
                additions['temperature'].append(s['temperature'])
                for n, a in enumerate(s['additives']):
                    additions.setdefault('additive.%d' % n, {})[m] = a['name']
                    additions.setdefault('amount.%d' % n, {})[m] = a['amount']

        res = []
        with StringIO(data_str) as f:
            data = (RDFread(f) if self.get_type() == ModelType.REACTION_MODELING else SDFread(f)).read()

        for m in self.__models:
            res.append(m.predict(data, **additions))

        all_domains = reduce(self.__merge_wrap, (x.domain for x in res)).fillna(False)

        all_predictions = reduce(self.__merge_wrap, (x.prediction for x in res))
        in_predictions = all_predictions.mask(all_domains ^ True)

        trust = Series(5, index=all_predictions.index)
        report = Series('', index=all_predictions.index)

        # mean predicted property
        avg_all = all_predictions.mean(axis=1)
        sigma_all = all_predictions.var(axis=1)

        avg_in = in_predictions.mean(axis=1)
        sigma_in = in_predictions.var(axis=1)

        avg_diff = (avg_in - avg_all).abs()  # difference bt in AD and all predictions. NaN for empty in predictions.
        avg_diff_tol = avg_diff > self.TOL  # ignore NaN
        trust.loc[avg_diff_tol] -= 1
        report.loc[avg_diff_tol] += [self.errors['diff'] % x for x in avg_diff.loc[avg_diff_tol]]

        avg_in_nul = avg_in.isnull()
        trust.loc[avg_in_nul] -= 2  # totally not in domain
        report.loc[avg_in_nul] += [self.errors['zad']] * len(avg_in_nul.loc[avg_in_nul].index)

        avg_domain = all_domains.mean(axis=1)
        avg_domain_bad = (avg_domain < self.Nlim) ^ avg_in_nul  # ignore totally not in domain
        trust.loc[avg_domain_bad] -= 1
        report.loc[avg_domain_bad] += [self.errors['lad'] % ceil(100 * x) for x in avg_domain.loc[avg_domain_bad]]

        # update avg and sigma based on consensus
        good = avg_domain >= self.Nlim
        avg_all.loc[good] = avg_in.loc[good]
        sigma_all.loc[good] = sigma_in.loc[good]

        proportion = sigma_all / self.TOL
        proportion_bad = proportion > 1
        trust.loc[proportion_bad] -= 1
        report.loc[proportion_bad] += [self.errors['stp'] % (x * 100 - 100) for x in proportion.loc[proportion_bad]]

        collector = defaultdict(list)
        for r, d in trust.items():
            s, *n = r if isinstance(r, tuple) else (r,)
            atoms = self.__report_atoms(n)
            collector[s].extend([dict(key='Predicted ± sigma%s%s' % ((self.__units and ' (%s)' % self.__units or ''),
                                                                     atoms),
                                      value='%.2f ± %.2f' % (avg_all.loc[r], sigma_all.loc[r]), type=ResultType.TEXT),
                                 dict(key='Trust of prediction%s' % atoms, value=self.trust_desc[d],
                                      type=ResultType.TEXT),
                                 dict(key='Distrust reason%s' % atoms, value=report.loc[r], type=ResultType.TEXT)])

        if len(structures) != len(collector):
            return False

        return [dict(results=collector[s], **structures[s]) for s in sorted(collector)]


class ModelLoader(object):
    def __init__(self, fast_load=True):
        tmp = Path(__file__).resolve()
        self.__models_path = tmp.parent / tmp.stem
        self.__cache_path = self.__models_path / '.cache'
        self.__skip_md5 = fast_load

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

    @staticmethod
    def __md5(file):
        hash_md5 = md5()
        with file.open('rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def __scan_models(self):
        if self.__cache_path.stat().st_size:
            with self.__cache_path.open('rb') as f:
                files = {x['file']: x for x in load(f)}
        else:
            files = {}

        cache = {}
        for file in (f for f in self.__models_path.iterdir() if f.is_file() and f.suffix == '.model'):
            file_name = file.stem
            if file_name not in files or files[file_name]['size'] != file.stat().st_size or \
                    not self.__skip_md5 and self.__md5(file) != files[file_name]['hash']:
                try:
                    model = Model(file)
                    cache[model.get_name()] = dict(file=file_name, hash=self.__md5(file), example=model.get_example(),
                                                   description=model.get_description(), size=file.stat().st_size,
                                                   type=model.get_type(), name=model.get_name())
                except Exception:
                    print('model %s consist errors: %s' % (file, format_exc()), file=stderr)
            else:
                cache[files[file_name]['name']] = files[file_name]

        with self.__cache_path.open('wb') as f:
            dump(list(cache.values()), f)
        return cache

    def load_model(self, name):
        if name in self.__models:
            return Model(self.__models_path / ('%s.model' % self.__models[name]['file']))

    def get_models(self):
        return list(self.__models.values())
