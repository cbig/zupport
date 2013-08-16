#!/usr/bin/python
# coding=utf-8

# Bootstrapped easy_install
from ez_setup import use_setuptools
use_setuptools(version='0.6c11')

from zupport.utilities.utilities import __version_info__ 

from setuptools import setup, find_packages
setup(
      # basic package data
      name = "zupport",
      version = '.'.join([str(item) for item in __version_info__ ]),
      author='Joona Lehtom\x84ki',
      author_email='joona.lehtomaki@gmail.com',
      
      license="MIT",

      # package structure
      packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
      package_dir={'zupport':'zupport'},
      package_data={'zupport': ['data/*.xml', 
                                'data/*.yaml',
                                'plugins/*/tools/*.yaml',
                                'resources/*.ini', 
                                'resources/*qrc',
                                'resources/*.ui']},

      # install the executables
      entry_points = {
        'console_scripts': [
            'zupport = zupport.cli:main'],
        'gui_scripts': [
           'zupport_gui = zupport.gui:main']
      },

      install_requires = [
                          'configobj >= 4.7.2',
                          'docutils >= 0.5',
                          'nose >= 0.11.1',
                          'numpy >= 1.6.1',
                          'pyyaml >= 3.09',
                          'xlrd >= 0.7.1',
                          'zope.component >= 3.10.0',
                          'zope.interface >= 3.7.0'
                          ],
      # use nose to run tests
      test_suite='nose.collector',
      zip_safe=False,
)