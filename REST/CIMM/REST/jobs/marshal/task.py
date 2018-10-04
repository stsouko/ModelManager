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
from marshmallow import Schema
from marshmallow.fields import String, Integer, Nested, DateTime
from .common import CountSchema
from .fields import IntEnumField
from .documents import PreparingDocumentSchema, ProcessingDocumentSchema
from ....constants import TaskStatus, TaskType


class MetadataSchema(Schema):
    task = String(description='task unique id')
    status = IntEnumField(TaskStatus, description='current state of task')
    type = IntEnumField(TaskType, description='type of task')
    date = DateTime(format='iso8601')
    user = Integer(description='task owner id')


class PreparedSchema(MetadataSchema):
    structures = Nested(PreparingDocumentSchema, many=True, default=list)


class ProcessedSchema(MetadataSchema):
    structures = Nested(ProcessingDocumentSchema, many=True, default=list)


class ExtendedMetadataSchema(MetadataSchema):
    structures = Nested(CountSchema, description='amount of available data')
