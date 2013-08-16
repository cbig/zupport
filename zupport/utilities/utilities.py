#!/usr/bin/python
# coding=utf-8

import imp
import os
import time

from appdirs import AppDirs

#===============================================================================
# Zupport common data

# Version information
__version_info__ = (0, 2, 1)
__version__ = '.'.join(map(str, __version_info__))

# Generic plugin message strings
msgInitStart =      'Initializing tool...'
msgInitSuccess =    'Tool sucesfully loaded'
msgInitStop =       'Tool sucesfully unloaded'

# Generic tool message strings
msgInWsNonExist =   'Input workspace <%s> does not exist.'
msgOutWsNonExist =  'Output workspace <%s> does not exist.'
msgConvSuccess =    'Successfully converted: %s'
msgConvFail =       'Failed to convert: %s'

# Set the project paths
# WARNING! Because of this way of setting up the paths eggs must be created
# in zip-safe manner
# TODO: all configuration and ini-files should be moved to ~.zupport folder
APP_RESOURCES = os.path.join(os.path.dirname(__file__), 
                             'resources')
APP_ROOT = os.path.abspath(os.path.join(os.path.basename(APP_RESOURCES),
                                            '../'))
APP_DATA = os.path.join(APP_ROOT, 'data')
APP_DOCS = os.path.join(APP_ROOT, 'doc')
APP_PLUGINS = os.path.join(APP_ROOT, 'plugins')
APP_RESOURCES = os.path.join(APP_ROOT, 'resources')

appdirs = AppDirs('Zupport', 'HelsinkiUniversity', version=__version__)

USER_DATA_DIR = appdirs.user_data_dir
USER_HISTORY_DIR = os.path.join(USER_DATA_DIR, 'history')
USER_PLUGINS_DIR = os.path.join(USER_DATA_DIR, 'plugins')
SITE_DATA_DIR = appdirs.site_data_dir
USER_CACHE_DIR = appdirs.user_cache_dir

LOGGING_INI = os.path.join(APP_RESOURCES, 'logging.ini')

# ArcGIS-specific raster types
ARC_RASTER_TYPES = {'ERDAS IMAGINE': '.img', 'GeoTIFF': '.tif', 
                    'ESRI GRID': '', 'ESRI FGDB': ''}

#===============================================================================
# Zupport common helper functions

def get_tools(module):
    
    # TODO: for some reason get_tools requires __all__ to be defined in the 
    # plugin.tools package
    
    import inspect
    tools = None
    for name, data in inspect.getmembers(module, inspect.ismodule):
        if name == 'tools':
            tools = data
            break
    if tools:
        return ([(name, data) for name, data in 
                            inspect.getmembers(tools, inspect.ismodule)])
    else:
        return None

def print_timing(func):
    def wrapper(*arg, **kwargs):
        for i in range(1):
            t1 = time.time()
            func(*arg, **kwargs)
            t2 = time.time()
            elapsed = ''
            if t2 - t1 < 1.0:
                print t2 - t1
                elapsed =  '%0.1f ms' % ((t2 - t1) * 1000.0)
            elif t2 - t1 < 60.0:
                elapsed = '%0.1f s' % (t2 - t1)
            else:
                elapsed = '%s m %s s' % (int((t2 - t1) / 60), int((t2 - t1) % 60))
            print str(i + 1) + ': %s took %s' % (func.func_name, elapsed)
    return wrapper

def load_from_file(filepath, expected_class):
    class_inst = None

    mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])

    if file_ext.lower() == '.py':
        py_mod = imp.load_source(mod_name, filepath)

    elif file_ext.lower() == '.pyc':
        py_mod = imp.load_compiled(mod_name, filepath)

    if expected_class in dir(py_mod):
        class_inst = py_mod.MyClass() 

    return class_inst

#===============================================================================
# Zupport common classes

class Singleton(object):
    """
    Singleton interface:
    http://www.python.org/download/releases/2.2.3/descrintro/#__new__
    """
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it

    def init(self, *args, **kwds):
        pass