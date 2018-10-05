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
from flask import make_response, url_for
from flask.views import MethodView, View
from flask_login import current_user, login_required


class SubscribeAuth(MethodView):
    @login_required
    def get(self):
        resp = make_response()
        resp.headers['X-Accel-Redirect'] = url_for('.subscribe', channel=current_user.id)
        resp.headers['X-Accel-Buffering'] = 'no'
        return resp


class PubSubURL(View):
    methods = ('GET', 'POST')

    def dispatch_request(self, channel):
        return 'USE NGINX NCHAN'
