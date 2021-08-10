#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytickersymbols
  Copyright 2019 Slash Gordon
  Use of this source code is governed by an MIT-style license that
  can be found in the LICENSE file.
"""
import re
from setuptools import setup, find_packages

EXCLUDE_FROM_PACKAGES = ['test', 'test.*', 'test*']

VERSION = '0.0.0'

with open("README.md", "r") as fh:
    long_description = fh.read()

INSTALL_REQUIRES = (
    ['wheel==0.37.0', 'PyYAML==5.4.1']
)

with open('src/pytickersymbols/__init__.py', 'r') as fd:
    VERSION = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE
    ).group(1)

setup(
    name="pytickersymbols",
    version=VERSION,
    author="Slash Gordon",
    author_email="slash.gordon.dev@gmail.com",
    py_modules=['pytickersymbols'],
    package_dir={'': 'src'},
    description="The lib provides ticker symbols for yahoo and google finance.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    url="https://github.com/portfolioplus/pytickersymbols",
    packages=find_packages('src', exclude=EXCLUDE_FROM_PACKAGES),
    install_requires=INSTALL_REQUIRES,
    package_data={'': ['data/*.json']},
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
)