#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages


def get_version():
    about = {}
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, 'autoextract/__version__.py')) as f:
        exec(f.read(), about)
    return about['__version__']


setup(
    name='zyte-autoextract',
    version=get_version(),
    description='Python interface to Zyte Automatic Extraction API',
    long_description=open('README.rst').read() + "\n\n" + open('CHANGES.rst').read(),
    long_description_content_type='text/x-rst',
    author='Mikhail Korobov',
    author_email='kmike84@gmail.com',
    url='https://github.com/zytedata/zyte-autoextract',
    packages=find_packages(exclude=['tests', 'examples']),
    install_requires=[
        'requests',
        'tenacity;python_version>="3.6"',
        'aiohttp >= 3.6.0;python_version>="3.6"',
        'tqdm;python_version>="3.6"',
        'attrs',
        'runstats',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
