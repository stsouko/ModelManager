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
from CGRtools.CGRpreparer import CGRcombo
from CGRtools.files.RDFrw import RDFread, RDFwrite
from CGRtools.files import ReactionContainer, MoleculeContainer
from json import loads
from io import StringIO
from MWUI.constants import ModelType, ResultType, StructureType, StructureStatus
from os import path
from ..utils import get_additives, chemax_post


model_name = 'Preparer'


class Model(CGRcombo):
    def __init__(self):
        self.__workpath = '.'
        self.__additives = {x['name'].lower(): x for x in get_additives()}

        config_path = path.join(path.dirname(__file__), 'preparer')
        b_path = path.join(config_path, 'b_templates.rdf')
        m_path = path.join(config_path, 'm_templates.rdf')

        b_templates = open(b_path) if path.exists(b_path) else None
        m_templates = open(m_path) if path.exists(m_path) else None

        CGRcombo.__init__(self, cgr_type='0', extralabels=True, isotope=False, element=True, stereo=False,
                          b_templates=b_templates, m_templates=m_templates)

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

    @staticmethod
    def get_example():
        return None

    @staticmethod
    def get_description():
        return 'Structure checking and possibly restoring'

    @staticmethod
    def get_name():
        return model_name

    @staticmethod
    def get_type():
        return ModelType.PREPARER

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
            if isinstance(r, ReactionContainer) and r.products and r.substrats:  # ONLY FULL REACTIONS
                # todo: preparation for queries!!!
                g = self.getCGR(r)
                _type = StructureType.REACTION
                _report = g.graph.get('CGR_REPORT', [])
                _status = StructureStatus.HAS_ERROR if any('ERROR:' in x for x in _report) else StructureStatus.CLEAR
                rdf.write(self.dissCGR(g))
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

        return dict(data=chemaxed['structure'].split('\n')[1], status=_status, type=_type,
                    results=[dict(key='Processed', value=x, type=ResultType.TEXT) for x in _report])

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
