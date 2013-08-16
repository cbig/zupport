#!/usr/bin/python
# coding=utf-8

import os
import sys
import glob

from arcpy import Result

from zupport.core import ParameterError, Tool
from zupport.plugins.fileio import (FileGroupIterator, ParseError, 
								    ParsedFileName, Workspace)
from zupport.plugins.zarcgis.utilities import get_geoprocessor
from zupport.plugins.zarcgis.errors import LicenseError
from zupport.zlogging import ArcLogger

#===============================================================================
# Zupport classes

class ArcResult(Result):

	pass

class ArcRasterWorkspace(Workspace):
	""" Extends the regular Zupport fileio workspace with some ESRI specific
	functionality. For example, instead of listing files based on a wildcard 
	it has specific ways of listing all the rasters in a given
	workspace.
	"""
	
	def __init__(self, parent, inpath, wildcard="*", raster_type="All"):
		""" A parent must be provided in order to gain access to the gp object.
		"""
		self.parent = parent
		self.raster_type = raster_type
		
		# Point the path to gp workspace 
		self._path = self.parent.gp.env.workspace
		
		Workspace.__init__(self, inpath)

		try:
			self.parent.gp.env.workspace = inpath
		except AttributeError, e:
			raise AttributeError(e)

	def refresh(self):
		""" Override refresh method. Will do nothing as listings are evaluated
		lazilly on need-to-know basis.
		"""
		self._files = self.parent.gp.ListRasters(self.wildcard, 
												self.raster_type)
		if len(self.files) == 0:
			if hasattr(self.parent, "logger"):
				self.parent.logger.warning('Created an empty workspace')

	def set_path(self, path):
		if os.path.exists(path):
			self.parent.gp.env.workspace = path
		else:
			# TODO: log
			raise ValueError('Workspace path %s does not exist.' % path)

	def get_path(self):
		return self.parent.gp.env.workspace

	path = property(get_path, set_path, None, "Path to an existing location \
                                                in the file system.")

class ArcParsedRasterWorkspace(ArcRasterWorkspace):
	'''Extends the regular ArcRasterWorkspace by being able to parse and process file
	names within the workspace. Instead of referring to individual files by
	path strings, ParserWorkspace contains files as instances of 
	ParsedFileName class.'''
	
	def __init__(self, parent, template, *args, **kwargs):
		self._template = template
		ArcRasterWorkspace.__init__(self, parent, *args, **kwargs)
	
	def refresh(self):
		"""Override Workspace method
		"""
		if self.recursive:
			# TODO: implement this
			pass
		else:
			files = self.parent.gp.ListRasters(self.wildcard, 
												self.raster_type)
			
			if len(files) == 0:
				if hasattr(self.parent, "logger"):
					self.parent.logger.warning('Created an empty workspace')
			else:
				try:
					self._files = [ParsedFileName(_file, self._template) for _file in files]
				except ParseError:
					raise

class ArcRasterGroupIterator(FileGroupIterator):
	
	def __init__(self, parent, inputws, wildcard, template, grouptags=None):
		self.parent = parent
		FileGroupIterator.__init__(self, inputws, wildcard, template, grouptags)
		
	def parse_workspace(self, template, inputws, wildcard):
		return ArcParsedRasterWorkspace(self.parent, template, inputws, wildcard)

class ArcTool(Tool):
	
	"""
	Class to represent a generic ArcGIS scripting tool.

	This class is intended mostly to be subclassed and provides methods for
	getting the input parameters for the Geoprocessor (GP). ArcGIS must be
	present in the system. Class should not be instantiated, but instead used as
	a super class. Class and its derivatives have three user cases:

	1. Subclasses are instantiated *from within ArcGIS* (Toolbox): the
	GP will get all the provided parameters and it is up to the
	subclasses to handle them correctly.

	2. Subclasses are instantiated *directly from command line*: the
	GP will get all the provided parameters and it is up to the
	subclasses to handle them correctly.

	3. Subclasses are instantiated *from elsewhere in code*: the parameters
	provided by the Geoprocessor will not be what expected.

	Setting the workspace is the responsibility of subclasses.
	"""

	def __init__(self, parameters, service, *args, **kwargs):
		"""Constructor initializes the Geoprocessor using
		:mod:`arcgisscripting` and loops thorugh all the available parameters
		in the Geoprocessor. Will raise an exception if problems occur with the
		Geoprocessor. Parameters are intended to be used in subclasses.
		
		Parameters:
		parameters - parameters object holding parameter information
		
		"""
		Tool.__init__(self, parameters)
		
		self._backend = 'arcgis'
		
		# TODO: handle the ArcGIS versions correctly
		try:
		
			# Inialize the logger for this tool. Logging system must be set up
			# before doing thishis
			self.logger = ArcLogger("Zupport.ArcTool", debugging=True)
			self.logger.debug('[%s] Acquiring geoprocessor' % service)
			self.gp = get_geoprocessor(10)
			# Set the scratch workspace explicitly to ESRI default
			self.gp.ScratchWorkspace = os.path.join(os.path.expanduser('~'), 
														'AppData', 'Local', 
														'Temp')
		
		except ImportError, e:
			self.logger.error('ArcGIS not present in the system.')
			sys.exit(1)
		except:
			raise

	def register_extension(self, extension):
		try:
			if self.gp.CheckExtension(extension ) == "Available":
				self.gp.CheckOutExtension(extension)
			else:
				raise LicenseError(extension)
		except LicenseError, e:
			raise

	def update(self, use_gp_params, gui, *args, **kwargs):
		""" Parse the provided *args and **kwargs into Parameters object 
		(self.parameters).
		"""
			
		paramsno = int(self.gp.GetArgumentCount())
		
		try:
			if gui:
				self.logger.gui = True
			
			# If parameters come from gp -> Tool being called from ArcGIS
			if paramsno > 0 and use_gp_params:
		
				# Last parameter toggles debugging
				self.logger.debugging = bool(self.gp.GetParameter(paramsno - 1))
				
				self.logger.debug(str(paramsno))
				
				gp_parameters = self.gp.GetParameterInfo()
				#self.logger.debug(self.parameters.parameter_names)
				for n in range(paramsno):
					self.logger.debug('param: ' + str(n))
					self.logger.debug('name: ' + gp_parameters[n].name)
					self.logger.debug('value: ' + str(gp_parameters[n].value))
					self.parameters.set_parameter_value(n, gp_parameters[n].value)
					
			# Otherwise parameters are provided as args or kwargs, this is also
			# the case if parameters are processed and provided for at batch 
			# operation (parameters from ArcGIS form are different to those
			# provided for the actual tool)
			else:
				Tool.update(self, *args, **kwargs)
				self.logger.debugging = bool(self.get_parameter('debug'))
			
			self.gp.LogHistory = self.logger.debugging
			self.ready = True
		
		except ParameterError, e:
			self.log.exception('%s' % e)

	def _setWorkspace(self, value):
		if value is None or self.gp.Exists(value):
			self.gp.env.workspace = value
		else:
			self.logger.warning('Input workspace <%s> does not exist.' % value)

	def _getWorkspace(self):
		return self.gp.env.workspace
	
	workspace = property(_getWorkspace, _setWorkspace, None, '')

class ArcRasterTool(ArcTool):
	
	def __init__(self, parameters, service, *args, **kwargs):
		ArcTool.__init__(self, parameters, service, *args, **kwargs)
		self._workspace = None

	@property
	def files(self):
		return self._workspace.files

	def _setWorkspace(self, value):
		if value is not None and self.gp.Exists(value):
			try:
				self._workspace = ArcRasterWorkspace(self, value)
			except AttributeError, e:
				self.log.exception(e)
		else:
			self.logger.warning('Input workspace <%s> does not exist.' % value)

	def _getWorkspace(self):
		return self._workspace.path
	
	workspace = property(_getWorkspace, _setWorkspace, None, '')

def get_tools():
	import inspect
	import tools
	return ([(name, data) for name, data in 
								inspect.getmembers(tools, inspect.ismodule)])