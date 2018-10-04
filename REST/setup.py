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
from CIMM.version import version
from pathlib import Path
from setuptools import setup


setup(
    name='CIMM-REST',
    version=version(),
    packages=['CIMM.REST', 'CIMM.REST.jobs', 'CIMM.REST.jobs.marshal', 'CIMM.REST.jobs.resources'],
    zip_safe=False,
    url='https://github.com/stsouko/ModelManager',
    license='AGPLv3',
    author='Dr. Ramil Nugmanov',
    author_email='stsouko@live.ru',
    description='ChemoInformatics Models Manager',
    install_requires=['CIMM-CORE>=1.4.1,<1.5', 'pony>=0.7.6,<0.8', 'flask>=1.0.2,<1.1', 'flask_apispec>=0.7.0,<0.8',
                      'flask_login>=0.4.1,<0.5', 'rq>=0.12.0,<0.13', 'marshmallow>=3.0.0b16,<3.1'],
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
    command_options={'build_sphinx': {'project': ('setup.py', 'CIMM-REST'),
                                      'version': ('setup.py', version()), 'source_dir': ('setup.py', 'doc'),
                                      'build_dir':  ('setup.py', 'build/doc'),
                                      'all_files': ('setup.py', True),
                                      'copyright': ('setup.py', 'Dr. Ramil Nugmanov <stsouko@live.ru>')}}
)
