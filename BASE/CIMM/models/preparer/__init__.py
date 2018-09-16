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
from CGRtools import CGRpreparer
from CGRtools.containers import QueryContainer
from CIMtools.preprocessing import StandardizeChemAxon
from CIMtools.preprocessing.common import reaction_support
from functools import partial
from pkg_resources import resource_string
from ...constants import ModelType, StructureType, ResultType, StructureStatus


class ModelLoader:
    def __init__(self, name, workpath='.'):
        self.__workpath = workpath
        self.__std_step_1 = StandardizeChemAxon(resource_string(__package__, 'step_1.xml').decode(), workpath)
        self.__std_step_2 = reaction_support(StandardizeChemAxon)(resource_string(__package__,
                                                                                  'step_2.xml').decode(), workpath)
        self.__cgr = CGRpreparer()

    def __new__(cls, name, *args, **kwargs):
        if name != 'Preparer':
            raise NameError(f"model '{name}' not found")
        return super().__new__(cls)

    def __call__(self, structures):
        """
        structure preparation procedure:

        return error for CGR and Query input
        return error if some of reaction checks failed

        aromatize
        return error if molecules has invalid valence

        implicify
        return error if some of reaction checks failed

        do chemaxon standardize.
        return error if structure invalid.
        return error if some of reaction checks failed
        """
        filtered_1 = []
        for s in structures:
            data = s['data']
            if isinstance(data, QueryContainer) or s['type'] == StructureType.REACTION and \
                    any(isinstance(x, QueryContainer) for x in (data.reagents, data.products) for x in x):
                s.update(status=StructureStatus.HAS_ERROR,
                         results=[dict(result='invalid structure', type=ResultType.TEXT,
                                       data='Query or CGR types structures not supported')])
                continue

            s['results'] = tmp = []

            if s['type'] == StructureType.REACTION:
                r, e = self.__check_reaction(data)
                if e:
                    s['status'] = StructureStatus.HAS_ERROR
                    tmp.extend(r)
                    continue

            o = data.aromatize()
            if o:
                tmp.append(dict(result='Aromatized', data=f'processed {o} molecules in reaction or rings in molecule',
                                type=ResultType.TEXT))

            if s['type'] == StructureType.REACTION:
                o = False
                for ml in (data.reagents, data.products):
                    for m in ml:
                        e = m.check_valence()
                        if e:
                            o = True
                            tmp.append(dict(result='Error', data='; '.join(e), type=ResultType.TEXT))
                if o:
                    s['status'] = StructureStatus.HAS_ERROR
                    continue
            else:
                e = data.check_valence()
                if e:
                    s['status'] = StructureStatus.HAS_ERROR
                    tmp.append(dict(result='Error', data='; '.join(e), type=ResultType.TEXT))
                    continue

            o = data.implicify_hydrogens()
            if o:
                tmp.append(dict(result='Implicified', data=f'removed {o} H atoms', type=ResultType.TEXT))

            if s['type'] == StructureType.REACTION:
                r, e = self.__check_reaction(data)
                if e:
                    s['status'] = StructureStatus.HAS_ERROR
                    tmp.extend(r)
                    continue
            filtered_1.append(s)

        if not filtered_1:
            return structures

        filtered_2 = []
        for s, data in zip(filtered_1, self.__std_step_1.transform([x['data'] for x in filtered_1])):
            if data is not None:
                s['data'] = data
                s['results'].append(dict(result='standardize', type=ResultType.TEXT,
                                         data='ChemAxon standardize passed'))
                if s['type'] == StructureType.REACTION:
                    r, e = self.__check_reaction(data)
                    if e:
                        s['status'] = StructureStatus.HAS_ERROR
                        s['results'].extend(r)
                        continue
                    filtered_2.append(s)
                else:  # molecules processing done
                    s['status'] = StructureStatus.CLEAN
            else:
                s['status'] = StructureStatus.HAS_ERROR
                s['results'].append(dict(result='invalid structure', type=ResultType.TEXT,
                                         data='ChemAxon standardize returned error'))
                continue

        if not filtered_2:
            return structures

        for s, data in zip(filtered_2, self.__std_step_2.transform([x['data'] for x in filtered_2])):
            if data is not None:
                s['results'].append(dict(result='standardize', type=ResultType.TEXT,
                                         data='ChemAxon standardize tautomerize passed'))
                r, _ = self.__check_reaction(data)
                s['results'].extend(r)
                s['status'] = StructureStatus.CLEAN
            else:
                s['status'] = StructureStatus.HAS_ERROR
                s['results'].append(dict(result='invalid structure', type=ResultType.TEXT,
                                         data='ChemAxon standardize tautomerize returned error'))

        return structures

    def __check_reaction(self, structure):
        error = False
        report = []
        rs = set(structure.reagents)
        ps = set(structure.products)

        if rs == ps:
            report.append(dict(result='Warning', data='all reagents and products is equal', type=ResultType.TEXT))
            error = True
        elif rs.issubset(ps):
            report.append(dict(result='Warning', data='all reagents presented in products', type=ResultType.TEXT))
            error = True
        elif rs.issuperset(ps):
            report.append(dict(result='Warning', data='all products presented in reagents', type=ResultType.TEXT))
            error = True
        elif rs.intersection(ps):
            report.append(dict(result='Warning', data='part of reagents and products is equal', type=ResultType.TEXT))

        cgr = self.__cgr.condense(structure)
        center = cgr.get_center_atoms()
        if not center:
            report.append(dict(result='Warning', data='Atom-to-atom mapping invalid', type=ResultType.TEXT))
        else:
            lg = len(cgr)
            lc = len(center)
            if lg > 10 and lc / lg > .4:
                report.append(dict(result='Warning', data=f'To many changed bonds and atoms. {lc} out of {lg}',
                                   type=ResultType.TEXT))
        return report, error

    @staticmethod
    def _get_models():
        return ['Preparer']

    @property
    def name(self):
        return 'Structure Preparer'

    @property
    def class_name(self):
        return 'Preparer'

    @property
    def description(self):
        return 'Structure checking and possibly fixing'

    @property
    def type(self):
        return ModelType.PREPARER

    @property
    def example(self):
        return None


def __getattr__(name):
    if name not in ModelLoader._get_models():
        raise AttributeError(f"model '{name}' not found")
    return partial(ModelLoader, name)


def __dir__():
    return ModelLoader._get_models()
