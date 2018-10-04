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
from marshmallow.fields import String, Integer, Nested, DateTime, Raw, Constant
from .common import CountSchema
from ....constants import TaskStatus, TaskType


class SavedMetadataSchema(Schema):
    task = String(description='job unique id')
    status = Constant(TaskStatus.PROCESSED.value,
                      description=f'state of job. only {TaskStatus.PROCESSED.value} - {TaskStatus.PROCESSED.name}')
    type = Constant(TaskType.MODELING.value,
                    description=f'type of job. only {TaskType.MODELING.value} - {TaskType.MODELING.name}')
    date = DateTime(format='iso8601')
    user = Integer(description='job owner id')


class SavedSchema(SavedMetadataSchema):
    task = String(description='job unique id', attribute='task.task')
    date = DateTime(format='iso8601', attribute='task.date')
    user = Integer(description='job owner id', attribute='task.user')
    structures = Raw(description='saved processed structures')


class ExtendedSavedMetadataSchema(SavedSchema):
    structures = Nested(CountSchema, description='amount of available data')


class SavedListSchema(Schema):
    task = String(description='job unique id')
    date = DateTime(format='iso8601')
