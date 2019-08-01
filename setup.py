#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='scrapinghub-autoextract',
    version='0.1',
    description='Python interface to Scrapinghub Automatic Extraction API',
    long_description=open('README.rst').read() + "\n\n" + open('CHANGES.rst').read(),
    author='Mikhail Korobov',
    author_email='kmike84@gmail.com',
    url='https://github.com/scrapinghub/scrapinghub-autoextract',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'requests',
    ],
    extras_require={
        'async': ['aiohttp >= 3.5.0'],
    },
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
    ],
)
