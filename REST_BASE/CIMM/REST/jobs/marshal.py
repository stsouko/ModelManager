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
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
from enum import Enum
from marshmallow import Schema, pre_dump, post_load, ValidationError
from marshmallow.fields import String, Integer, Float, Nested, Boolean, DateTime
from marshmallow.validate import Range, Length
from ...additives import Additive
from ...constants import TaskStatus, TaskType, AdditiveType


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
        except ValueError as err:
            self.fail('unknown_enum')

    default_error_messages = {'invalid': 'not a valid integer',
                              'not_enum': 'not a Enum', 'unknown_enum': 'not a valid Enum key'}


class DescriptionSchema(Schema):
    key = String()
    value = String()


class AdditiveSchema(Schema):
    additive = Integer(required=True, validate=Range(1), attribute='id',
                       title='id of additive', description='additive should be in list of available additives')
    amount = Float(required=True, validate=Range(0), title='amount of additive',
                   description='for solvents amount is part in mixture. for pure solvents it should be 1. '
                               'molar concentration for overs')
    name = String(dump_only=True, title='name of additive')
    structure = String(dump_only=True, title='structure of additive')
    type = IntEnumField(AdditiveType, dump_only=True, title='type of additive',
                        description='possible one of the following: ' +
                                    ', '.join('{0.value} - {0.name}'.format(x) for x in AdditiveType))

    @post_load
    def _make_additive(self, data):
        try:
            return Additive(amount=data['amount'], _id=data['id'])
        except KeyError:
            raise ValidationError('invalid id of additive')
        except ValueError as e:
            raise ValidationError(str(e))

    @pre_dump
    def _check_additive(self, obj):
        if isinstance(obj, Additive):
            return obj
        raise ValidationError('expected %s. %s received' % (Additive, type(obj)))


class DocumentSchema(Schema):
    temperature = Float(missing=298, validate=Range(100, 600), title='temperature',
                        description='temperature of media in Kelvin')
    pressure = Float(missing=1, validate=Range(0, 100000), title='pressure',
                     description='pressure of media in bars')
    description = Nested(DescriptionSchema, many=True, missing=list, default=list)
    additives = Nested(AdditiveSchema, many=True, missing=list, default=list)

    data = String(required=True, validate=Length(2), title='structure of molecule or reaction',
                  description='string containing marvin document or MDL RDF|SDF or smiles/smirks')

    structure = Integer()
    todelete = Boolean(load_only=True, title='delete structure',
                       description='exclude this structure from document before revalidation or modeling')


class PostResponseSchema(Schema):
    task = String(title='job unique id')
    status = IntEnumField(TaskStatus, title='current state of job',
                          description='possible one of the following: ' +
                                      ', '.join('{0.value} - {0.name}'.format(x) for x in TaskStatus))
    type = IntEnumField(TaskType, title='job type',
                        description='possible one of the following: ' +
                                    ', '.join('{0.value} - {0.name}'.format(x) for x in TaskType))

    date = DateTime(format='iso8601')
    user = Integer(attribute='id', title='job owner ID')
