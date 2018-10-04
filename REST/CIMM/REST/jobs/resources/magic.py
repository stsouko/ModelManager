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
from flask_apispec import MethodResource, marshal_with
from flask_login import login_required
from ....constants import AdditiveType, ModelType, TaskType, TaskStatus, StructureType, StructureStatus, ResultType


class MagicNumbers(MethodResource):
    @login_required
    @marshal_with(None, 200, 'magic numbers', apply=False)
    @marshal_with(None, 401, 'user not authenticated')
    def get(self):
        """
        Get Magic numbers

        Dict of all magic numbers with values.
        """
        data = {x.__name__: self.__to_dict(x) for x in (TaskType, TaskStatus, StructureType, StructureStatus,
                                                        AdditiveType, ResultType, ModelType)}

        return data, 200

    @staticmethod
    def __to_dict(enum):
        return {x.name: x.value for x in enum}
