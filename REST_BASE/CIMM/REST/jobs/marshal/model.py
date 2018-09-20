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
from marshmallow import Schema
from marshmallow.fields import String, Integer, Nested, Raw
from marshmallow.validate import Length, Range
from .common import EmptyCheck
from .documents import CreatingDocumentSchema
from .fields import IntEnumField
from ....constants import ModelType


class DestinationSchema(Schema):
    host = String(validate=Length(5), required=True)
    port = Integer(missing=6379, validate=Range(1001, 65536))
    password = String(validate=Length(6, 20))
    name = String(validate=Length(3), required=True)


class DeployModelSchema(EmptyCheck, Schema):
    name = String(required=True, validate=Length(5, 20), description='name of model')
    object = String(required=True, validate=Length(5, 20), description='internal name of model')
    type = IntEnumField(ModelType, required=True, description='type of model')
    description = String(required=True, validate=Length(10), description='description of model')
    example = Nested(CreatingDocumentSchema, required=True)
    destination = Nested(DestinationSchema, required=True)


class DataBaseModelSchema(Schema):
    model = Integer(attribute='id', description='id of model')
    name = String(description='name of model')
    description = String(description='description of model')
    type = Integer(attribute='_type', description='type of model')
    example = Raw(description='example structure')
