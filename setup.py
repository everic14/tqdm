#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tqdm._version import __version__
from setuptools import setup

setup(
    name='tqdm',
    version=__version__,
    description='A Simple And Fast Python Progress Meter',
    license='MIT License',
    author='Noam Yorav-Raphael',
    author_email='noamraph@gmail.com',
    url='https://github.com/tqdm/tqdm',
    maintainer='tqdm developers',
    maintainer_email='python.tqdm@gmail.com',
    platforms = ["any"],
    packages=['tqdm'],
    long_description = open("README.md", "r").read(),
    classifiers=[ # Trove classifiers, see https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Framework :: IPython',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: System :: Monitoring',
        'Topic :: Terminals',
        'Topic :: Utilities',
        'Intended Audience :: Developers',
    ],
    keywords = 'progressbar progressmeter progress bar meter rate eta console terminal time',
)
