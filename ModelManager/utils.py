# -*- coding: utf-8 -*-
#
#  Copyright 2017 Ramil Nugmanov <stsouko@live.ru>
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
from CGRtools.files.RDFrw import RDFread
from CGRtools.files.MRVrw import MRVwrite
from CGRtools.files import ReactionContainer
from CIMtools.config import MOLCONVERT
from io import StringIO
from json import dumps
from MWUI.constants import AdditiveType, StructureType, StructureStatus
from re import split
from requests import post, get
from subprocess import Popen, PIPE, STDOUT
from .config import CHEMAXON, ADDITIVES, PREDICTOR, WORKPATH


def chemax_post(url, data):
    for _ in range(2):
        try:
            q = post("%s/rest-v0/util/%s" % (CHEMAXON, url), data=dumps(data),
                     headers={'content-type': 'application/json'}, timeout=20)
        except:
            continue
        else:
            if q.status_code in (201, 200):
                return q.json()
            else:
                continue
    else:
        return False


def get_additives():
    for _ in range(2):
        try:
            q = get(ADDITIVES, timeout=20)
        except:
            continue
        else:
            if q.status_code in (201, 200):
                res = q.json()
                for a in res:
                    a['type'] = AdditiveType(a['type'])
                return res
            else:
                continue
    else:
        return []


def server_post(data, user, password):
    for _ in range(2):
        try:
            q = post(PREDICTOR, json=data, timeout=20, auth=(user, password))
        except:
            continue
        else:
            if q.status_code in (201, 200):
                return q.json()
            else:
                continue
    else:
        return []


def convert_upload(url):
    additives = {x['name'].lower(): x for x in get_additives()}
    r = get(url)
    if r.status_code != 200:
        return False

    with Popen([MOLCONVERT, 'rdf'], stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=WORKPATH) as convert_mol:
        res = convert_mol.communicate(input=r.content)[0].decode()
        if convert_mol.returncode != 0:
            return False

    report = []
    with StringIO(res) as mol_in:
        for n, r in enumerate(RDFread(mol_in), start=1):
            _meta = r.meta.copy()
            r.meta.clear()

            if isinstance(r, ReactionContainer):
                _type = StructureType.REACTION
            else:  # MOLECULES AND MIXTURES
                _type = StructureType.MOLECULE

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
            tmp_add = {}
            for k, v in _meta.items():
                if k.startswith('additive.amount.'):
                    key = k[16:]
                    try:
                        a_name, *_, a_amount = split('[:=]+', v)
                        additive = additives.get(a_name.strip().lower())
                        if additive and key:
                            _v = float(a_amount.replace('%', '')) / 100 if '%' in a_amount else float(a_amount)
                            tmp_add[key] = dict(amount=_v, **additive)
                    except ValueError:
                        pass
                elif k.startswith('additive.'):
                    key = k[9:]
                    additive = additives.get(v.lower())
                    if additive and key:
                        tmp_add.setdefault(key, dict(amount=1)).update(additive)

                elif k.startswith('amount.'):
                    key = k[7:]
                    if key:
                        try:
                            _v = float(v.replace('%', '')) / 100 if '%' in v else float(v)
                            tmp_add.setdefault(key, {})['amount'] = _v
                        except ValueError:
                            pass

            additives = []
            for i in sorted(tmp_add):
                if 'name' in tmp_add[i]:
                    additives.append(tmp_add[i])

            tmp = _meta.pop('pressure', 1)
            try:
                pressure = float(tmp)
            except ValueError:
                pressure = 1

            tmp = _meta.pop('temperature', 298)
            try:
                temperature = float(tmp)
            except ValueError:
                temperature = 298

            with StringIO() as mol_out:
                mrv = MRVwrite(mol_out)
                mrv.write(r)
                mrv.finalize()
                structure = mol_out.getvalue()

            report.append(dict(structure=n, data=structure, status=StructureStatus.RAW, type=_type, additives=additives,
                               pressure=pressure, temperature=temperature))

    return report
