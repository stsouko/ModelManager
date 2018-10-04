# -*- coding: utf-8 -*-
#
#  Copyright 2018 Ramil Nugmanov <stsouko@live.ru>
#  This file is part of CIMM (ChemoInformatics Models Manager).
#
#  CIMM is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, see <https://www.gnu.org/licenses/>.
#
from enum import Enum


class StructureStatus(Enum):
    RAW = 0
    HAS_ERROR = 1
    CLEAN = 2


class StructureType(Enum):
    UNDEFINED = 0
    MOLECULE = 1
    REACTION = 2


class TaskStatus(Enum):
    PREPARING = 1
    PREPARED = 2
    PROCESSING = 3
    PROCESSED = 4


class ModelType(Enum):
    PREPARER = 0
    MOLECULE_MODELING = 1
    REACTION_MODELING = 2
    MOLECULE_SEARCHING = 3
    REACTION_SEARCHING = 4

    def compatible(self, structure_type, task_type):
        return self.name == '%s_%s' % (structure_type.name, task_type.name)


class TaskType(Enum):
    MODELING = 0
    SEARCHING = 1
    POPULATING = 2


class AdditiveType(Enum):
    SOLVENT = 0
    CATALYST = 1
    OVER = 2


class ResultType(Enum):
    TEXT = 0
    STRUCTURE = 1
    TABLE = 2
    IMAGE = 3
    GRAPH = 4
    GTM = 5
