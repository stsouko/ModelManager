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
from flask_restplus import Model
from flask_restplus.fields import String, Float, List, Nested, Integer, DateTime
from ..restplus import UnEnumField, UserIDField
from ...constants import TaskStatus, TaskType


description = Model('Description',
                    {'key': String,
                     'value': String}
                    )

additives = Model('Additives',
                  {'additive': Integer(title='id of additive', required=True, readonly=True,
                                       description='additive should be in list of available additives'),
                   'name': String(title='name of additive', readonly=True)}
                  )

amounted_additives = additives.clone('AmountedAdditives',
                                     {'amount': Float(title='amount of additive', required=True, exclusiveMin=0,
                                                      description='for solvents amount is part in mixture. '
                                                                  'for pure solvents it should be 1. '
                                                                  'molar concentration for overs.')}
                                     )

common_document = Model('Document',
                        {'temperature': Float(298, title='temperature', exclusiveMin=0,
                                              description='temperature of media in Kelvin'),
                         'pressure': Float(1, title='pressure', exclusiveMin=0,
                                           description='pressure of media in bars'),
                         'description': List(Nested(description, skip_none=True), default=list),
                         'additives': List(Nested(amounted_additives, skip_none=True), default=list)}
                        )

structure_document = common_document.clone('StructureDocument',
                                           {'data': String(title='structure of molecule or reaction', required=True,
                                                           description='string containing marvin document or cml or '
                                                                       'smiles/smirks')}
                                           )


post_response = Model('PostResponse',
                      {'task': String(title='job unique ID'),
                       'status': UnEnumField(title='current state of job',
                                             description='possible one of the following: ' +
                                                         ', '.join('{0.value} - {0.name}'.format(x)
                                                                   for x in TaskStatus)),
                       'type': UnEnumField(title='job type',
                                           description='possible one of the following: ' +
                                                       ', '.join('{0.value} - {0.name}'.format(x)
                                                                 for x in TaskType)),
                       'date': DateTime(dt_format='iso8601'),
                       'user': UserIDField(title='job owner ID')}
                      )
