#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" setup.py

Packaging for cci's python API
"""

import os
from setuptools import setup, find_packages


def get_version():
    basedir = os.path.dirname(__file__)
    with open(os.path.join(basedir, 'cci/version.py')) as f:
        VERSION = None
        exec(f.read())
        return VERSION
    raise RuntimeError("No version found")


if __name__ == '__main__':

    setup(name='cci',
          version=get_version(),
          description="A python API for VUIIS CCI Infrastructure",
          author="VUIIS CCI",
          author_email="vuiis-cci@googlegroups.com",
          packages=find_packages(),
          package_data={},
          install_requires=['pyxnat'],
          classifiers=[
                       # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
                       # "Development Status :: 1 - Planning",
                       # "Development Status :: 2 - Pre-Alpha",
                       "Development Status :: 3 - Alpha",
                       # "Development Status :: 4 - Beta",
                       # "Development Status :: 5 - Production/Stable",
                       # "Development Status :: 6 - Mature",
                       # "Development Status :: 7 - Inactive",
                       "Environment :: Console",
                       "Intended Audience :: Science/Research",
                       "Operating System :: MacOS :: MacOS X",
                       "Operating System :: POSIX",
                       "Operating System :: POSIX :: Linux",
                       "Operating System :: Unix",
                       "Programming Language :: Python :: 2.6",
                       "Programming Language :: Python :: 2.7",
                       "Programming Language :: Python :: 2 :: Only",
                       "Topic :: Scientific/Engineering",
                       "Topic :: Scientific/Engineering :: Information Analysis",
                       ],
          )
