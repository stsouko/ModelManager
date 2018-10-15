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
    packages=['CIMM', 'CIMM.CLI', 'CIMM.models'],
    install_requires=['CGRtools>=2.8.32,<2.9'],
    extras_require={'autocomplete': ['argcomplete'], 'sphinx': ['sphinx>=1.6']},
    entry_points={'console_scripts': ['cimm=CIMM.CLI.loader:run']},
    package_data={'CIMM': ['additives.json']},
    zip_safe=False,
    url='https://github.com/stsouko/ModelManager',
    license='GPLv3',
    author='Dr. Ramil Nugmanov',
    author_email='stsouko@live.ru',
    description='ChemoInformatics Models Manager',
    long_description=(Path(__file__).parent / 'README.md').open().read(),
    classifiers=['Environment :: Console',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                 'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 3 :: Only',
                 'Programming Language :: Python :: 3.7',
                 'Topic :: Scientific/Engineering',
                 'Topic :: Scientific/Engineering :: Chemistry',
                 'Topic :: Scientific/Engineering :: Information Analysis',
                 'Topic :: Software Development',
                 'Topic :: Software Development :: Libraries',
                 'Topic :: Software Development :: Libraries :: Python Modules'],
    command_options={'build_sphinx': {'project': ('setup.py', 'CIMM-CORE'),
                                      'version': ('setup.py', version()), 'source_dir': ('setup.py', 'doc'),
                                      'build_dir':  ('setup.py', 'build/doc'),
                                      'all_files': ('setup.py', True),
                                      'copyright': ('setup.py', 'Dr. Ramil Nugmanov <stsouko@live.ru>')}}
)
