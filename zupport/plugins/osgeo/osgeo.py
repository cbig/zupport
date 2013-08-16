#!/usr/bin/python
# coding=utf-8

import os
from zupport.core import Tool
from zupport.utilities import Workspace

class OSGeoTool(Tool):
    """
    Class to represent a generic OSGeo scripting tool.

    This class is intended mostly to be subclassed and provides methods for
    getting the input parameters. Parameters are provided by sub classes when
    they are instantiated and the super class is called.
    """

    def __init__(self, backend, parameters, *args, **kwargs):
        """Constructor will try to import all the necessary GDAL related modules
        (:mod:`osr`, :mod:`ogr`, :mod:`gdal`) and bind them as instance
        variables. If GDAL is not present in the system program execution will
        terminate.
        
        Parameters:
        backend - string describing the backend in use
        parameters - parameters object holding parameter information
        arclogging - boolean defining whether ArcGIS logging system is used
        """

        Tool.__init__(self, backend, parameters, arclogging=False)

        # Try importing GDAL, will fail if GDAL not present
        try:
            from osgeo import osr, ogr, gdal
        except ImportError:
            self.logger.error('GDAL/OGR not present in the system.')
            return 1

        # TODO: how does this really work? Does it mean, that each instance
        # has own copy or are they shared?
        # TODO: implement engine attribute
        self.osr = osr
        self.ogr = ogr
        self.gdal = gdal

        for parameter in args:
            self._parameters.append(parameter)

        for parameter, value in kwargs.iteritems():
            self._parameters.append(value)

        # Check for keyword arguments
        if kwargs.has_key('inworkspace'):
            self.input = kwargs['inworkspace']
        # Check for regular arguments
        elif len(args) > 0:
            self.input = args[0]
        # If input is defined create a workspace
        if self.input:
            self.workspace = Workspace(self.input)

        # Check for keyword arguments
        if kwargs.has_key('outworkspace'):
            self.output = kwargs['outworkspace']
        # Check for regular arguments
        elif len(args) > 1:
            self.output = args[1]

    # Override the setters
    def _setInput(self, value):
        if value is None or os.path.exists(value):
            self._input = value
            self.workspace = value
        else:
            pass # LOG

    def _setOutput(self, value):
        if value is None or os.path.exists(value):
            self._output = value
        else:
            pass # LOG