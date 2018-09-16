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
from CGRtools.containers import MoleculeContainer, ReactionContainer
from CGRtools.files import RDFread, SDFread, MRVread, MRVwrite, SMILESread
from enum import Enum
from io import StringIO, BytesIO
from marshmallow import Schema, pre_dump, post_load, ValidationError, pre_load
from marshmallow.fields import String, Integer, Float, Nested, Boolean, DateTime, Method, Raw, Constant
from marshmallow.validate import Range
from ...additives import Additive
from ...constants import TaskStatus, TaskType, AdditiveType, StructureType, StructureStatus, ModelType, ResultType


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


class CountSchema(Schema):
    total = Integer(description='amount of available data')
    pages = Integer(description='amount of pages of data')


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
    type = IntEnumField(AdditiveType, dump_only=True,
                        description='type of additive. possible one of the following: ' +
                                    ', '.join(f'{x.value} - {x.name}' for x in AdditiveType))

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
    type = IntEnumField(ResultType, description='type of result. possible one of the following: ' +
                                                ', '.join(f'{x.value} - {x.name}' for x in ResultType))
    result = String(description='key of result. key is a header or title or uid of result')
    data = Method('_dump_data', dump_only=True, description='result data')

    @staticmethod
    def _dump_data(obj):
        return obj['data']  # todo: extend


class ModelSchema(Schema):
    model = Integer(required=True, validate=Range(1), attribute='model.id',
                    description='id of model. need for selecting models which will be applied to structure')
    name = String(dump_only=True, description='name of model', attribute='model.name')
    type = Integer(dump_only=True, attribute='model._type',
                   description='type of model. possible one of the following: ' +
                               ', '.join(f'{x.value} - {x.name}' for x in ModelType))
    description = String(dump_only=True, description='description of model', attribute='model.description')
    results = Nested(ResultSchema, many=True, dump_only=True)

    @post_load
    def _fix_model(self, data):
        data['model'] = data['model']['id']
        return data


class DocumentMixin:
    @post_load
    def _set_type(self, data):
        if 'data' in data:
            data['type'] = StructureType.REACTION if isinstance(data['data'], ReactionContainer) else \
                StructureType.MOLECULE
            data['status'] = StructureStatus.RAW
        return data

    @pre_load(pass_many=True)
    def _check_empty(self, data, many):
        if many:
            if not isinstance(data, (list, tuple)):
                raise ValidationError('invalid data')
            if not data:
                raise ValidationError('empty data')
        return data


class CreatingDocumentSchema(Schema, DocumentMixin):
    temperature = Float(missing=298, validate=Range(100, 600), description='temperature of media in Kelvin')
    pressure = Float(missing=1, validate=Range(0, 100000), description='pressure of media in bars')
    description = Nested(DescriptionSchema, many=True, missing=list, default=list)
    additives = Nested(AdditiveSchema, many=True, missing=list, default=list)
    data = StructureField(required=True, description='string containing MRV or MDL RDF|SDF or SMILES|SMIRKS structure')


class PreparingDocumentSchema(CreatingDocumentSchema):
    temperature = Float(validate=Range(100, 600), description='temperature of media in Kelvin')
    pressure = Float(validate=Range(0, 100000), description='pressure of media in bars')
    description = Nested(DescriptionSchema, many=True, default=list)
    additives = Nested(AdditiveSchema, many=True, default=list)
    data = StructureField(description='string containing MRV or MDL RDF|SDF or SMILES|SMIRKS structure')

    structure = Integer(required=True, validate=Range(1),
                        description='structure id for mapping of changes to records in previously validated document')
    todelete = Boolean(load_only=True,
                       description='exclude this structure from document before revalidation or modeling')
    status = IntEnumField(StructureStatus, dump_only=True,
                          description='validation status of structure. possible one of the following: ' +
                                      ', '.join(f'{x.value} - {x.name}' for x in StructureStatus))
    type = IntEnumField(StructureType, dump_only=True,
                        description='type of validated structure. possible one of the following: ' +
                                    ', '.join(f'{x.value} - {x.name}' for x in StructureType))

    models = Nested(ModelSchema, many=True, dump_only=True)


class ProcessingDocumentSchema(PreparingDocumentSchema):
    data = StructureField(dump_only=True, description='string containing MRV structure')
    models = Nested(ModelSchema, many=True, required=True)


class MetadataSchema(Schema):
    task = String(description='job unique id')
    status = IntEnumField(TaskStatus, description='current state of job. possible one of the following: ' +
                                                  ', '.join(f'{x.value} - {x.name}' for x in TaskStatus))
    type = IntEnumField(TaskType, description='type of job. possible one of the following: ' +
                                              ', '.join(f'{x.value} - {x.name}' for x in TaskType))
    date = DateTime(format='iso8601')
    user = Integer(description='job owner id')


class PreparedSchema(MetadataSchema):
    structures = Nested(PreparingDocumentSchema, many=True, default=list)


class ProcessedSchema(MetadataSchema):
    structures = Nested(ProcessingDocumentSchema, many=True, default=list)


class ExtendedMetadataSchema(MetadataSchema):
    structures = Nested(CountSchema, description='amount of available data')


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
