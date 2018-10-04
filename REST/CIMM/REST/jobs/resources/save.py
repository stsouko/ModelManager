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
from flask import current_app
from flask_apispec import MethodResource, use_kwargs, marshal_with, doc
from flask_login import login_required, current_user
from marshmallow.fields import String
from math import ceil
from pony.orm import db_session
from .common import JobMixin
from ..marshal import (SavedMetadataSchema, SavedSchema, ProcessingDocumentSchema, SavedListSchema, CountSchema,
                       ExtendedSavedMetadataSchema)
from .. import database
from ...utils import abort
from ....constants import TaskStatus, TaskType


class SavedMixin:
    decorators = (login_required, db_session)

    def fetch(self, task):
        task = self.tasks.get(task=task)
        if not task:
            abort(404, message='invalid task id. perhaps this task has already been removed')

        if task.user != current_user.get_id():
            abort(403, message='user access deny')
        return task

    @property
    def tasks(self):
        return getattr(database, current_app.config['JOBS_DB_SCHEMA']).Task


@doc(params={'task': {'description': 'task id', 'type': 'string'}})
class Saved(SavedMixin, MethodResource):
    @doc(params={'page': {'description': 'page number', 'type': 'integer'}})
    @marshal_with(SavedSchema, 200, 'saved task')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 403, 'user access deny')
    @marshal_with(None, 404, 'invalid task id or page not found')
    def get(self, task, page=None):
        """
        task with modeling results of structures with conditions
        """
        chunk = current_app.config.get('REDIS_CHUNK', 50)
        task = self.fetch(task)
        structures = task.data
        if page:
            cs = chunk * (page - 1)
            if len(structures) <= cs:
                abort(404, message='page not found')
            structures = structures[cs: chunk * page]

        return dict(task=task, structures=structures), 200

    @marshal_with(SavedMetadataSchema, 202, 'task deleted')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 403, 'user access deny')
    @marshal_with(None, 404, 'invalid task id or page not found')
    def delete(self, task):
        """
        delete task from db
        """
        task = self.fetch(task)
        task.delete()
        return task, 202


class SavedMetadata(SavedMixin, MethodResource):
    @doc(params={'task': {'description': 'task id', 'type': 'string'}})
    @marshal_with(ExtendedSavedMetadataSchema, 200, 'saved data')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 403, 'user access deny')
    @marshal_with(None, 404, 'invalid task id')
    def get(self, task):
        """
        task metadata
        """
        chunk = current_app.config.get('REDIS_CHUNK', 50)
        task = self.fetch(task)
        return dict(task=task, structures={'total': task.size, 'pages': ceil(task.size / chunk)}), 200


class SavedList(JobMixin, SavedMixin, MethodResource):
    @doc(params={'page': {'description': 'page number', 'type': 'integer'}})
    @marshal_with(SavedListSchema(many=True), 200, 'saved tasks')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 403, 'user access deny')
    @marshal_with(None, 404, 'page not found')
    def get(self, page):
        """
        current user's saved tasks
        """
        chunk = current_app.config.get('REDIS_CHUNK', 50)
        q = self.tasks.select(lambda x: x.user == current_user.get_id())
        if q.count() <= (page - 1) * chunk:
            abort(404, message='page not found')
        return list(q.page(page, pagesize=chunk))

    @use_kwargs({'task': String(required=True, description='task id')}, locations=('json',))
    @marshal_with(SavedMetadataSchema, 201, 'processed task saved')
    @marshal_with(None, 401, 'user not authenticated')
    @marshal_with(None, 403, 'user access deny')
    @marshal_with(None, 404, 'invalid task id. perhaps this task has already been removed')
    @marshal_with(None, 406, 'task status/type is invalid. only modeling tasks acceptable')
    @marshal_with(None, 409, 'task already exists in db')
    @marshal_with(None, 500, 'modeling/dispatcher server error')
    @marshal_with(None, 512, 'task not ready')
    def post(self, task):
        """
        store in database modeled task

        only modeled tasks can be saved.
        failed models in structures skipped.
        """
        if self.tasks.exists(task=task):
            abort(409, message='task already exists in db')

        task = self.fetch(task, TaskStatus.PROCESSED)
        if task['type'] != TaskType.MODELING:
            abort(406, message='invalid task type')

        data = ProcessingDocumentSchema.dump(task['structures'])
        return self.tasks(data=data, date=task['date'], user=task['user'], task=task['task']), 201


class SavedCount(SavedMixin, MethodResource):
    @marshal_with(CountSchema, 200, 'saved data')
    @marshal_with(None, 401, 'user not authenticated')
    def get(self):
        """
        user's saves count
        """
        q = self.tasks.select(lambda x: x.user == current_user.get_id()).count()
        return dict(total=q, pages=ceil(q / current_app.config.get('REDIS_CHUNK', 50))), 200
