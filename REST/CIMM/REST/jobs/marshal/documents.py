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
from flask import current_app
from marshmallow import Schema, ValidationError, pre_dump, post_load, post_dump
from marshmallow.fields import String, Integer, Float, Nested, Boolean, Method
from marshmallow.validate import Range
from pony.orm import ObjectNotFound
from pony.orm.core import Entity
from .common import EmptyCheck
from .fields import IntEnumField, StructureField
from .. import database
from ....additives import Additive
from ....constants import TaskStatus, TaskType, AdditiveType, StructureType, StructureStatus, ModelType, ResultType


class DescriptionSchema(Schema):
    key = String()
    value = String()


class AdditiveSchema(Schema):
    additive = Integer(required=True, validate=Range(1), attribute='id',
                       description='id of additive. additive should be in list of available additives')
    amount = Float(required=True, validate=Range(0),
                   description='amount of additive. for solvents amount is part in mixture. '
                               'for pure solvents it should be 1. molar concentration for overs')
    name = String(dump_only=True, title='name of additive')
    structure = String(dump_only=True, description='structure of additive')
    type = IntEnumField(AdditiveType, dump_only=True, description='type of additive')

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
        raise ValidationError(f'expected {Additive}. {type(obj)} received')


class ResultSchema(Schema):
    type = IntEnumField(ResultType, description='type of result')
    result = String(description='key of result. key is a header or title or uid of result')
    data = Method('_dump_data', dump_only=True, description='result data')

    @staticmethod
    def _dump_data(obj):
        return obj['data']  # todo: extend

    @post_dump
    def _ad_hoc_compat(self, data):
        return dict(type=data['type'], key=data['result'], value=data['data'])


class StructureTypeSet:
    @post_load
    def set_type_status(self, data):
        if 'data' in data:
            data['type'] = StructureType.REACTION if isinstance(data['data'], ReactionContainer) else \
                StructureType.MOLECULE
            data['status'] = StructureStatus.RAW
        return data


class ModelSchema(Schema):
    model = Integer(required=True, validate=Range(1), attribute='model.id',
                    description='id of model. need for selecting models which will be applied to structure')
    name = String(dump_only=True, description='name of model', attribute='model.name')
    type = Integer(dump_only=True, attribute='model._type', description='type of model')
    description = String(dump_only=True, description='description of model', attribute='model.description')
    results = Nested(ResultSchema, many=True, dump_only=True)

    @post_load
    def fix_load(self, data):
        try:
            data = self.models[data['model']['id']]
        except ObjectNotFound:
            raise ValidationError('invalid model id')
        return data

    @pre_dump
    def fix_dump(self, data):
        if not isinstance(data['model'], Entity):
            return {'model': self.models[data['model']], 'results': data['results']}
        return data

    @property
    def models(self):
        if self.__models_cache is None:
            self.__models_cache = getattr(database, current_app.config['JOBS_DB_SCHEMA']).Model
        return self.__models_cache

    __models_cache = None


class CreatingDocumentSchema(StructureTypeSet, EmptyCheck, Schema):
    temperature = Float(missing=298, validate=Range(100, 600), description='temperature of media in Kelvin')
    pressure = Float(missing=1, validate=Range(0, 100000), description='pressure of media in bars')
    description = Nested(DescriptionSchema, many=True, missing=list, default=list)
    additives = Nested(AdditiveSchema, many=True, missing=list, default=list)
    data = StructureField(required=True, description='string containing MRV or MDL RDF|SDF or SMILES|SMIRKS structure')


class DocumentSchema(StructureTypeSet, EmptyCheck, Schema):
    temperature = Float(validate=Range(100, 600), description='temperature of media in Kelvin')
    pressure = Float(validate=Range(0, 100000), description='pressure of media in bars')
    description = Nested(DescriptionSchema, many=True, default=list)
    additives = Nested(AdditiveSchema, many=True, default=list)
    structure = Integer(required=True, validate=Range(1),
                        description='structure id for mapping of changes to records in previously validated document')
    status = IntEnumField(StructureStatus, dump_only=True, description='validation status of structure')
    type = IntEnumField(StructureType, dump_only=True, description='type of validated structure')


class PreparingDocumentSchema(DocumentSchema):
    data = StructureField(description='string containing MRV or MDL RDF|SDF or SMILES|SMIRKS structure')
    todelete = Boolean(load_only=True,
                       description='exclude this structure from document before revalidation or modeling')
    models = Nested(ModelSchema, many=True, dump_only=True)


class ProcessingDocumentSchema(DocumentSchema):
    data = StructureField(dump_only=True, description='string containing MRV structure')
    models = Nested(ModelSchema, many=True, required=True)
