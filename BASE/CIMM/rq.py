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
from shutil import rmtree
from tempfile import mkdtemp
from traceback import format_exc
from warnings import warn
from .config import WORKPATH
from .constants import ModelType, ResultType
from .models import loader
from .utils import download_data


def run(structures, model):
    """
    model runner
    :param structures: list of {data: chemical structure (smiles mrv etc), pressure: float, temperature: float,
                                additives: [{name: str, amount: float, type: MWUI.constants[AdditiveType(Enum)]}],
                                structure: int, description: [{key: str, value: str}],
                                status: MWUI.constants[StructureStatus], type: MWUI.constants[StructureType]}
    :param model: model name
    :return: updated list of structure dicts. new key - models: [dict(result: [dict,], **model arg)]
    
    if model not found or crashed return data without results in models[0]
    if model return list of results with size not equal to structures list size - raise exception. this model BAD! 
    """
    def fail_prep(reason):
        for s in structures:
            s['results'] = [dict(key='Modeling Failed', value=reason, type=ResultType.TEXT)]
        return structures

    workpath = mkdtemp(dir=WORKPATH)
    try:
        mod = getattr(loader, model)(workpath)
    except AttributeError:
        warn('Model not found or not loadable', ImportWarning)
        rmtree(workpath)
        return fail_prep('Model not found or not loadable')

    try:
        results = mod([x.copy() for x in structures])
    except:
        warn(f'Model not working:\n {format_exc()}', UserWarning)
        rmtree(workpath)
        return fail_prep('Model not working')

    rmtree(workpath)
    if not results:
        return fail_prep('Model returned nothing')

    if len(results) != len(structures) and mod.type not in (ModelType.MOLECULE_SEARCHING,
                                                            ModelType.REACTION_SEARCHING):
        print('Model lost structures. check model code for correctness')
        return fail_prep('Model lost data')

    if mod.type in (ModelType.REACTION_MODELING, ModelType.MOLECULE_MODELING):
        if any(s[x] != r[x] for s, r in zip(structures, results)
               for x in ('data', 'structure', 'status', 'type', 'temperature', 'pressure', 'additives', 'description')):
            print("Editing structure, properties and meta denied! ONLY results assign possible!")
            return fail_prep('Model broke data')

    if mod.type == ModelType.PREPARER:
        if any(s[x] != r[x] for s, r in zip(structures, results) for x in ('structure', 'additives', 'description')):
            print("Editing meta denied! "
                  "ONLY results assigning, data, temperature, pressure type and status editing possible!")
            return fail_prep('Preparing model not working')

    return results


def convert(structures, model):
    tmp = download_data(structures)
    if not tmp:
        raise Exception('File converter failed')
    return run(tmp, model)
