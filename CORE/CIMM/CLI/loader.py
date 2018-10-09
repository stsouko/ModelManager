# -*- coding: utf-8 -*-
#
#  Copyright 2018 Ramil Nugmanov <stsouko@live.ru>
#  This file is part of CIMM (ChemoInformatics Models Manager).
#
#  CIMM is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, see <https://www.gnu.org/licenses/>.
#
from argparse import ArgumentParser
from importlib import import_module
from importlib.util import find_spec
from pkgutil import iter_modules
from .. import CLI
from ..version import version


def run():
    parser = ArgumentParser(description="CIMM", epilog="(c) Dr. Ramil Nugmanov")
    parser.add_argument("--version", "-v", action="version", version=version(), default=False)
    subparsers = parser.add_subparsers(title='subcommands', description='available utilities')

    for module_info in iter_modules(CLI.__path__):
        if not module_info.ispkg:
            module = import_module(f'{__package__}.{module_info.name}')
            if hasattr(module, 'cmd'):
                module.cmd(subparsers)

    if find_spec('argcomplete'):
        from argcomplete import autocomplete
        autocomplete(parser)

    args = parser.parse_args()
    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()
