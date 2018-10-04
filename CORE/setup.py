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
from CIMM.version import version
from pathlib import Path
from setuptools import setup


setup(
    name='CIMM-CORE',
    version=version(),
    packages=['CIMM', 'CIMM.models', 'CIMM.models.preparer', 'CIMM.CLI'],
    zip_safe=False,
    url='https://github.com/stsouko/ModelManager',
    license='AGPLv3',
    author='Dr. Ramil Nugmanov',
    author_email='stsouko@live.ru',
    description='ChemoInformatics Models Manager',
    entry_points={'console_scripts': ['cimm_worker=CIMM.CLI.worker:run', 'cimm_register=CIMM.CLI.register:run']},
    package_data={'CIMM.models.preparer': ['step_1.xml', 'step_2.xml'], 'CIMM': ['additives.json']},
    install_requires=['CIMtools>=1.4.7,<1.5'],
    extras_require={'autocomplete': ['argcomplete'], 'sphinx': ['sphinx>=1.6']},
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
    command_options={'build_sphinx': {'project': ('setup.py', 'CIMM-CORE'),
                                      'version': ('setup.py', version()), 'source_dir': ('setup.py', 'doc'),
                                      'build_dir':  ('setup.py', 'build/doc'),
                                      'all_files': ('setup.py', True),
                                      'copyright': ('setup.py', 'Dr. Ramil Nugmanov <stsouko@live.ru>')}}
)
