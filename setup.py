#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytickersymbols

 Copyright 2019 Christoph Dieck

 Use of this source code is governed by a GNU General Public License v3 or later that can be
 found in the LICENSE file.
"""

from setuptools import setup, find_packages

EXCLUDE_FROM_PACKAGES = ['test', 'test.*', 'test*']
VERSION = '1.0.1'

def get_requirements(requirements):
    with open(requirements) as requirement_file:
        content = requirement_file.readlines()
    content = [x.strip() for x in content]
    return content


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="pytickersymbols",
    version=VERSION,
    author="Christoph Dieck",
    author_email="christoph.dieck@gmail.com",
    py_modules=['pytickersymbols'],
    package_dir={'': 'src'},
    description="The lib provides ticker symbols for yahoo and google finance.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/portfolioplus/pytickersymbols",
    packages=find_packages('src', exclude=EXCLUDE_FROM_PACKAGES),
    package_data={'': ['data/*.yaml']},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
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