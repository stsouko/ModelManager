#!/usr/bin/env python3
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
from ModelManager import ModelSet
from ModelManager.config import WORKPATH
from ModelManager.utils import convert_upload
from MWUI.constants import ModelType
from shutil import rmtree
from tempfile import mkdtemp


def run(structures=None, model=None):
    """
    model runner
    :param structures: list of dicts {data: chemical structure (smiles mrv etc), pressure: float, temperature: float,
                                      additives: [{name: str, amount: float, type: AdditiveType(Enum)}]} 
    :param model: dict(name=str, description: str, type: ModelType(Enum), model=int)
    :return: updated list of structure dicts. new key - models: [dict(result: [dict,], **model arg)]
    
    if model not found or crashed return data without results in models[0]
    if model return False for some structures in list of structures then structures skipped from output.
    if model return list of results with with size not equal to structures list size - raise exception. this model BAD! 
    """
    workpath = mkdtemp(dir=WORKPATH)
    mod = ModelSet().load_model(model['name'], workpath=workpath)
    s_len = len(structures)

    results = mod.get_results([x.copy() for x in structures]) if mod is not None else None

    if results:
        if len(results) != s_len and mod.get_type() not in (ModelType.MOLECULE_SEARCHING, ModelType.REACTION_SEARCHING):
            raise Exception('Model lost structures. check model code for correctness')

        if mod.get_type() in (ModelType.REACTION_MODELING, ModelType.MOLECULE_MODELING):
            if any(s[x] != r[x] for s, r in zip(structures, results)
                   for x in ('data', 'structure', 'status', 'type', 'temperature', 'pressure', 'additives')):
                raise Exception("Editing structure, properties and meta denied! ONLY results assign possible!")

        for r in results:  # reformat structure container.
            r['models'] = [dict(results=r.pop('results', []), **model)]
    else:
        print('Model not found or not working')
        for s in structures:
            s['models'] = [model]
        results = structures

    rmtree(workpath)
    return results


def convert(structures=None, model=None):
    tmp = convert_upload(structures)
    if not tmp:
        raise Exception('File converter failed')
    return run(structures=tmp, model=model)
