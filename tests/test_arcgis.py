#!/usr/bin/python
# coding=utf-8
'''
Created on 30.12.2009

@author: admin_jlehtoma
'''

import unittest
from nose import with_setup
from zupport.arcgis import get_geoprocessor

def setup_func():
        "set up test fixtures"
        import arcpy
    
def teardown_func():
        "tear down test fixtures"
        pass

@with_setup(setup_func, teardown_func)    
def testGeneral():
    assert False
