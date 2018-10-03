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
from CIMM.version import version
from pathlib import Path
from setuptools import setup, find_packages


setup(
    name='CIMM-CGRDB',
    version=version(),
    packages=find_packages(),
    namespace_packages=['CIMM', 'CIMM.models', 'CIMM.REST', 'CIMM.CLI'],
    zip_safe=True,
    url='https://github.com/stsouko/ModelManager',
    license='AGPLv3',
    author='Dr. Ramil Nugmanov',
    author_email='stsouko@live.ru',
    description='ChemoInformatics Models Manager',
    install_requires=['CIMM-BASE>=1.4.1,<1.5', 'CGRdb>=1.3.0.<1.4'],
    extras_require={'sphinx': ['sphinx>=1.6']},
    long_description=(Path(__file__).parent / 'README.md').open().read(),
    keywords="tools cgr cli",
    classifiers=['Environment :: Console',
                 'Intended Audience :: Science/Research',
                 'Intended Audience :: Developers',
                 'Topic :: Scientific/Engineering :: Chemistry',
                 'Topic :: Software Development :: Libraries :: Python Modules',
                 'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.7'],
    command_options={'build_sphinx': {'project': ('setup.py', 'CIMM-CGRDB'),
                                      'version': ('setup.py', version()), 'source_dir': ('setup.py', 'doc'),
                                      'build_dir':  ('setup.py', 'build/doc'),
                                      'all_files': ('setup.py', True),
                                      'copyright': ('setup.py', 'Dr. Ramil Nugmanov <stsouko@live.ru>')}}
)
