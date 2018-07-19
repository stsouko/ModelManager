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


#  _____    _____       ___   _____       ___  ___   _____
# |  _  \  | ____|     /   | |  _  \     /   |/   | | ____|
# | |_| |  | |__      / /| | | | | |    / /|   /| | | |__
# |  _  /  |  __|    / /_| | | | | |   / / |__/ | | |  __|
# | | \ \  | |___   / /__| | | |_| |  / /       | | | |___
# |_|  \_\ |_____| /_/   |_| |_____/ /_/        |_| |_____|
#
# This __init__.py file is part of namespace package CIMM. This file needs to contain only the following:

__import__('pkg_resources').declare_namespace('CIMM')

# Every distribution that uses the namespace package CIMM must include an identical __init__.py.
# If any distribution does not,
# it will cause the namespace logic to fail and the other sub-packages will not be importable.
# Any additional code in __init__.py will be inaccessible.
