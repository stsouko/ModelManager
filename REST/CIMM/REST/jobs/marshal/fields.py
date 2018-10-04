# -*- coding: utf-8 -*-
#
#  Copyright 2018 Ramil Nugmanov <stsouko@live.ru>
#  This file is part of CIMM (ChemoInformatics Models Manager).
#
#  CIMM is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program; if not, see <https://www.gnu.org/licenses/>.
#
from CGRtools.containers import MoleculeContainer, ReactionContainer
from CGRtools.files import RDFread, SDFread, MRVread, MRVwrite, SMILESread
from enum import Enum
from io import StringIO, BytesIO
from marshmallow.fields import String, Integer


class StructureField(String):
    def _serialize(self, value, attr, obj):
        if isinstance(value, (MoleculeContainer, ReactionContainer)):
            with StringIO() as f:
                with MRVwrite(f) as w:
                    try:
                        w.write(value)
                    except (ValueError, KeyError):
                        self.fail('not_container')
                return f.getvalue()
        self.fail('not_container')

    def _deserialize(self, value, attr, data):
        value = super()._deserialize(value, attr, data)
        if not value:
            self.fail('empty')

        if 'MChemicalStruct' in value:
            with BytesIO(value.encode()) as f, MRVread(f) as r:
                try:
                    return next(r)
                except StopIteration:
                    self.fail('not_mrv')
        else:
            with StringIO(value) as f:
                if '$RXN' in value:
                    with RDFread(f) as r:
                        try:
                            return next(r)
                        except StopIteration:
                            self.fail('not_rdf')
                elif 'V2000' in value or 'V3000' in value:
                    with SDFread(f) as r:
                        try:
                            return next(r)
                        except StopIteration:
                            self.fail('not_sdf')
                else:
                    with SMILESread(f) as r:
                        try:
                            return next(r)
                        except StopIteration:
                            self.fail('unknown')

    default_error_messages = {'invalid': 'not a valid string', 'invalid_utf8': 'not a valid utf-8 string',
                              'not_container': 'not a valid CGRtools container', 'not_mrv': 'not a valid mrv file',
                              'not_rdf': 'not a valid rdf file', 'not_sdf': 'not a valid sdf file',
                              'unknown': 'unknown structure file', 'empty': 'empty structure data'}


class IntEnumField(Integer):
    def __init__(self, enum, **kwargs):
        self.enum = enum
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj):
        if isinstance(value, Enum):
            return super()._serialize(value.value, attr, obj)
        self.fail('not_enum')

    def _deserialize(self, value, attr, data):
        try:
            return self.enum(super()._deserialize(value, attr, data))
        except ValueError:
            self.fail('unknown_enum')

    default_error_messages = {'invalid': 'not a valid integer',
                              'not_enum': 'not a Enum', 'unknown_enum': 'not a valid Enum key'}
