# -*- coding: utf-8 -*-
#
#  Copyright 2016-2018 Ramil Nugmanov <stsouko@live.ru>
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
from CGRtools.containers import ReactionContainer, CGRContainer, MoleculeContainer
from CGRtools.files import RDFread, MRVread, SDFread, SMILESread
from io import StringIO, BytesIO
from re import split
from requests import get
from shutil import rmtree
from tempfile import mkdtemp
from traceback import format_exc
from warnings import warn
from . import loader
from ..additives import Additive
from ..constants import ModelType, ResultType, StructureStatus, StructureType


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
            s['results'] = [dict(result='Modeling Failed', data=reason, type=ResultType.TEXT)]
        rmtree(workpath)
        return structures

    workpath = mkdtemp()
    try:
        mod = getattr(loader, model)(workpath)
    except:
        warn(f'Model not found or not loadable.\n{format_exc()}', ImportWarning)
        return fail_prep('Model not found or not loadable')

    try:
        results = mod([x.copy() for x in structures])
    except:
        warn(f'Model not working:\n{format_exc()}')
        return fail_prep('Model not working')

    if not results:
        return fail_prep('Model returned nothing')

    if len(results) != len(structures) and mod.type not in (ModelType.MOLECULE_SEARCHING,
                                                            ModelType.REACTION_SEARCHING):
        warn('Model lost structures. check model code for correctness')
        return fail_prep('Model lost data')

    if mod.type in (ModelType.REACTION_MODELING, ModelType.MOLECULE_MODELING):
        if any(s[x] != r[x] for s, r in zip(structures, results)
               for x in ('data', 'structure', 'status', 'type', 'temperature', 'pressure', 'additives', 'description')):
            warn('Editing structure, properties and meta denied! ONLY results assign possible!')
            return fail_prep('Model broke data')

    if mod.type == ModelType.PREPARER:
        if any(s[x] != r[x] for s, r in zip(structures, results) for x in ('structure', 'additives', 'description')):
            warn('Editing meta denied! '
                 'ONLY results assigning, data, temperature, pressure type and status editing possible!')
            return fail_prep('Preparing model not working')

    del mod
    rmtree(workpath)
    return results


def convert(structures, model):
    """
    $DTYPE additive.amount.1
    $DATUM name = .5
    $DTYPE temperature
    $DATUM 40
    $DTYPE pressure
    $DATUM 0.9
    $DTYPE additive.2
    $DATUM name
    $DTYPE amount.2
    $DATUM 0.5
    """
    r = get(structures)
    if r.status_code != 200:
        raise Exception('File download failed')

    if b'MChemicalStruct' in r.content:
        with BytesIO(r.content) as f, MRVread(f) as r:
            data = r.read()
    else:
        with StringIO(r.text) as f:
            if b'$RXN' in r.content:
                with RDFread(f) as r:
                    data = r.read()
            elif b'V2000' in r.content or b'V3000' in r.content:
                with SDFread(f) as r:
                    data = r.read()
            else:
                with SMILESread(f) as r:
                    data = r.read()

    out = []
    for n, s in enumerate(data, start=1):
        if isinstance(s, ReactionContainer):
            _type = StructureType.REACTION
        elif isinstance(s, MoleculeContainer) and not isinstance(s, CGRContainer):  # MOLECULES AND MIXTURES
            _type = StructureType.MOLECULE
        else:
            continue

        _meta = s.meta.copy()
        s.meta.clear()

        tmp_add, found_add = {}, {}
        for k, v in _meta.items():
            if k.startswith('additive.amount.'):
                key = k[16:]
                if key and key not in found_add:
                    try:
                        a_name, *_, a_amount = split('[:=]+', v)
                        _v = float(a_amount.replace('%', '')) / 100 if '%' in a_amount else float(a_amount)
                        found_add[key] = Additive(amount=_v, name=a_name.strip().lower())
                    except (ValueError, KeyError):
                        continue
            elif k.startswith('additive.'):
                key = k[9:]
                if key and key not in found_add:
                    if key in tmp_add:
                        if 'name' in tmp_add[key]:
                            continue
                        tmp_add[key]['name'] = v.lower()
                    else:
                        tmp_add[key] = {'name': v.lower()}

            elif k.startswith('amount.'):
                key = k[7:]
                if key and key not in found_add:
                    try:
                        _v = float(v.replace('%', '')) / 100 if '%' in v else float(v)
                    except ValueError:
                        continue
                    else:
                        if key in tmp_add:
                            if 'amount' in tmp_add[key]:
                                continue
                            tmp_add[key]['amount'] = _v
                        else:
                            tmp_add[key] = {'amount': _v}

        for k, v in tmp_add.items():
            try:
                found_add[k] = Additive(*v)
            except (ValueError, KeyError):
                continue

        tmp = _meta.get('pressure', 1)
        try:
            pressure = float(tmp)
        except ValueError:
            pressure = 1

        tmp = _meta.get('temperature', 298)
        try:
            temperature = float(tmp)
        except ValueError:
            temperature = 298

        out.append(dict(structure=n, data=s, status=StructureStatus.RAW, type=_type, additives=found_add,
                        pressure=pressure, temperature=temperature))

    if not out:
        raise Exception('File converter failed')
    return run(out, model)
