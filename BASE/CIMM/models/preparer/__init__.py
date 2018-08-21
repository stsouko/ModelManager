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
from functools import partial
from ...constants import ModelType


class Model:
    def __init__(self):
        self.__workpath = '.'
        '''
        self.__additives = {x['name'].lower(): x for x in get_additives()}
        
        config_path = path.join(path.dirname(__file__), 'preparer')
        templates = path.join(config_path, 'templates.rdf')
        templates = RDFread(templates, is_template=True) if path.exists(templates) else False

        self.cgr = CGRpreparer(extralabels=True, templates=templates)

        with open(path.join(config_path, 'preparer.xml')) as f:
            self.__pre_rules = f.read()
        self.__pre_filter_chain = [dict(filter="standardizer",
                                        parameters=dict(standardizerDefinition=self.__pre_rules)),
                                   dict(filter="clean", parameters=dict(dim=2))]

        self.__post_rules = None
        self.__post_filter_chain = [dict(filter="clean", parameters=dict(dim=2))]
        if path.exists(path.join(config_path, 'postprocess.xml')):
            with open(path.join(config_path, 'postprocess.xml')) as f:
                self.__post_rules = f.read()
            self.__post_filter_chain.insert(0, dict(filter="standardizer",
                                                    parameters=dict(standardizerDefinition=self.__post_rules)))
        '''

    @staticmethod
    def get_example():
        return None

    @staticmethod
    def get_description():
        return 'Structure checking and possibly restoring'

    @staticmethod
    def get_name():
        return 'pp'

    @staticmethod
    def get_type():
        return 1

    def set_work_path(self, workpath):
        self.__workpath = workpath

    def get_results(self, structures):
        return [self.__parse_structure(s) for s in structures]

    def __parse_structure(self, structure):
        chemaxed = chemax_post('calculate/molExport',
                               dict(structure=structure['data'], parameters="rdf", filterChain=self.__pre_filter_chain))
        if not chemaxed:
            return False

        with StringIO(chemaxed['structure']) as in_file, StringIO() as out_file:
            rdf = RDFwrite(out_file)
            r = next(RDFread(in_file))
            if isinstance(r, ReactionContainer) and r.products and r.reagents:  # ONLY FULL REACTIONS
                # todo: preparation for queries!!!
                g = self.cgr.condense(r)
                _type = StructureType.REACTION
                _report = g.graph.get('CGR_REPORT', [])
                _status = StructureStatus.HAS_ERROR if any('ERROR:' in x for x in _report) else StructureStatus.CLEAR
                rdf.write(self.cgr.dissociate(g))
            elif isinstance(r, MoleculeContainer):  # MOLECULES AND MIXTURES
                _type = StructureType.MOLECULE
                _report = []
                _status = StructureStatus.CLEAR
                rdf.write(r)  # todo: molecules checks.
            else:
                return False

            prepared = out_file.getvalue()

        chemaxed = chemax_post('calculate/molExport',
                               dict(structure=prepared, parameters="mrv", filterChain=self.__post_filter_chain))
        if not chemaxed:
            return False

        structure.update(data=chemaxed['structure'].split('\n')[1], status=_status, type=_type,
                         results=[dict(key='Processed', value=x, type=ResultType.TEXT) for x in _report])
        return structure

    def chkreaction(self, structure):
        data = {"structure": structure, "parameters": "smiles:u",
                "filterChain": [{"filter": "standardizer", "parameters": {"standardizerDefinition": "unmap"}}]}
        smiles = chemax_post('calculate/molExport', data)
        if smiles:
            s, p = loads(smiles)['structure'].split('>>')
            ss = set(s.split('.'))
            ps = set(p.split('.'))
            if ss == ps:
                return self.__warnings['fe']
            if ss.intersection(ps):
                return self.__warnings['pe']

            st = chemax_post('calculate/chemicalTerms', {"structure": s, "parameters": "majorTautomer()"})
            pt = chemax_post('calculate/chemicalTerms', {"structure": p, "parameters": "majorTautomer()"})
            if st and pt:
                st = chemax_post('calculate/molExport',
                                 {"structure": loads(st)['result']['structureData']['structure'],
                                  "parameters": "smiles:u"})
                pt = chemax_post('calculate/molExport',
                                 {"structure": loads(pt)['result']['structureData']['structure'],
                                  "parameters": "smiles:u"})
                if st and pt:
                    sts = set(loads(st)['structure'].split('.'))
                    pts = set(loads(pt)['structure'].split('.'))
                    if sts == pts:
                        return self.__warnings['tfe']
                    if ss.intersection(ps):
                        return self.__warnings['tpe']

                    return None

        return 'reaction check failed'

    __warnings = dict(fe='reagents equal to products',
                      pe='part of reagents equal to part of products',
                      tfe='tautomerized and neutralized reagents equal to products',
                      tpe='tautomerized and neutralized part of reagents equal to part of products')


class ModelLoader:
    def __call__(self, structures):
        pass

    def __init__(self, name, workpath='.'):
        self.__workpath = workpath

    def __new__(cls, name, *args, **kwargs):
        if name != 'Preparer':
            raise ImportError(f"model '{name}' not found")
        return super().__new__(cls)

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
        raise ImportError(f"model '{name}' not found")
    return partial(ModelLoader, name)


def __dir__():
    return ModelLoader._get_models()