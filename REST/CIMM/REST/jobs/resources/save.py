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


@marshal_with(None, 401, 'user not authenticated')
class SavedCount(MethodResource):
    decorators = (login_required, db_session)

    @marshal_with(CountSchema, 200, 'saved data')
    def get(self):
        """
        user's saves count
        """
        q = self.tasks.select(lambda x: x.user == current_user.id).count()
        return dict(total=q, pages=self.page_number(q)), 200

    @property
    def tasks(self):
        return getattr(database, current_app.config['JOBS_DB_SCHEMA']).Task

    def page_number(self, count):
        return ceil(count / self.page_size) or 1

    @property
    def page_size(self):
        return current_app.config.get('JOBS_REDIS_CHUNK', 50)


@doc(params={'task': {'description': 'task id', 'type': 'string'}})
@marshal_with(None, 403, 'user access deny')
@marshal_with(None, 404, 'invalid task id')
class SavedMetadata(SavedCount):
    @marshal_with(ExtendedSavedMetadataSchema, 200, 'saved data')
    def get(self, task):
        """
        task metadata
        """
        task = self.fetch(task)
        return dict(task=task, structures={'total': task.size, 'pages': self.page_number(task.size)}), 200

    def fetch(self, task):
        task = self.tasks.get(task=task)
        if not task:
            abort(404, 'invalid task id. perhaps this task has already been removed')

        if task.user != current_user.id:
            abort(403, 'user access deny')
        return task


class Saved(SavedMetadata):
    @doc(params={'page': {'description': 'page number', 'type': 'integer'}})
    @marshal_with(SavedSchema, 200, 'saved task')
    @marshal_with(None, 404, 'invalid task id or page not found')
    def get(self, task, page=None):
        """
        task with modeling results of structures with conditions
        """
        task = self.fetch(task)

        if page:
            if self.page_number(task.size) < page:
                abort(404, 'page not found')
            ps = self.page_size
            structures = task.data[ps * (page - 1): ps * page]
        else:
            structures = task.data

        return dict(task=task, structures=structures), 200

    @marshal_with(SavedMetadataSchema, 202, 'task deleted')
    def delete(self, task):
        """
        delete task from db
        """
        task = self.fetch(task)
        task.delete()
        return task, 202


class SavedList(JobMixin, SavedCount):
    @doc(params={'page': {'description': 'page number', 'type': 'integer'}})
    @marshal_with(SavedListSchema(many=True), 200, 'saved tasks')
    @marshal_with(None, 404, 'page not found')
    def get(self, page=1):
        """
        current user's saved tasks
        """
        chunk = current_app.config.get('JOBS_REDIS_CHUNK', 50)
        q = self.tasks.select(lambda x: x.user == current_user.id)

        if self.page_number(q.count()) < page:
            abort(404, 'page not found')

        return q.page(page, pagesize=chunk), 200

    @use_kwargs({'task': String(required=True, description='task id')}, locations=('json',))
    @marshal_with(SavedMetadataSchema, 201, 'processed task saved')
    @marshal_with(None, 403, 'user access deny')
    @marshal_with(None, 404, 'invalid task id/type/status. perhaps this task has already been removed')
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
            abort(409, 'task already exists in db')

        task = self.fetch(task, TaskStatus.PROCESSED)
        if task['type'] != TaskType.MODELING:
            abort(404, 'invalid task type')

        data = ProcessingDocumentSchema(many=True).dump(task['structures'])
        return self.tasks(data=data, date=task['date'], user=task['user'], task=task['task']), 201
