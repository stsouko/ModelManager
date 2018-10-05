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
from CGRtools.containers import ReactionContainer
from marshmallow import Schema, ValidationError, pre_dump
from marshmallow.fields import String, Integer, Float, Nested, DateTime, Constant, Function
from ...jobs.marshal.fields import StructureField, IntEnumField
from ...jobs.marshal.documents import DescriptionSchema
from ....additives import Additive
from ....constants import StructureStatus, StructureType, AdditiveType


class AdditiveSchema(Schema):
    additive = Integer(required=True, attribute='id', description='id of additive')
    amount = Float(required=True, description='amount of additive')
    name = String(dump_only=True, title='name of additive')
    structure = String(dump_only=True, description='structure of additive')
    type = IntEnumField(AdditiveType, dump_only=True, description='type of additive')

    @pre_dump
    def _restore_additive(self, obj):
        if 'amount' not in obj:
            raise ValidationError('amount information not found')
        try:
            if 'name' in obj:
                return Additive(obj['amount'], obj['name'])
            if 'additive' in obj:
                return Additive(obj['amount'], _id=obj['additive'])
        except ValueError as e:
            raise ValidationError from e


class RecordMetadataSchema(Schema):
    structure = Integer(attribute='structure.id')
    metadata = Integer(attribute='id')
    date = DateTime(format='iso8601')
    user = Integer(attribute='user_id')


class RecordSchema(RecordMetadataSchema):
    data = StructureField(attribute='structure.structure', description='string containing MRV structure')
    temperature = Float(attribute='data.temperature', description='temperature of media in Kelvin')
    pressure = Float(attribute='data.pressure', description='pressure of media in bars')
    description = Nested(DescriptionSchema, many=True, attribute='data.description', default=list)
    additives = Nested(AdditiveSchema, many=True, attribute='data.additives', default=list)

    status = Constant(StructureStatus.CLEAN.value,
                      description=f'state of job. only {StructureStatus.CLEAN.value} - {StructureStatus.CLEAN.name}')
    type = Function(lambda x: isinstance(x, ReactionContainer) and StructureType.REACTION.value or
                    StructureType.MOLECULE.value, attribute='structure.structure',
                    description='type of validated structure')
