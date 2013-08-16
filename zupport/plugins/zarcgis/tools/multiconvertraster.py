#!/usr/bin/python
# coding=utf-8

import types

from zope.interface import implements
from zupport.interfaces import IGISTool

from itertools import product

from ..core import ArcTool
from ..errors import FeatureTypeError, FieldError, LicenseError
from ..utilities import generate_rastername

from zupport.core import ParameterError
from zupport.utilities import ARC_RASTER_TYPES, msgInitSuccess
from zupport.zlogging import ArcLogger

def service():
	return 'multiconvertraster'

def setup(parameters, *args, **kwargs):
	return MultiConvertRaster(parameters, service=service(), *args, **kwargs)

class MultiConvertRaster(ArcTool):
	""" ArcTool for converting feature layers to rasters based on multiple
	attribute selections.

	TODO: parameters require a dictionary -> how will this handled by Toolbox
		  GUI?

	Parameters:
	(0) Input feature [infeature]:
	
		String representing source feature class (required)
		 
	(1) Input condition fields [inconfields]: 
	
		';'-separated list (String) of field names or a dictionary. List of 
		field names will create a cartesian product of all unique values in the 
		fields (same as ['all']below). 
		
		A dictionary {field_name: [values]} defines which fields and 
		values will be used for conditions. If [values] = [x1, x2, ..., x3]
		then x-values are used as values, if [values] = ['all'] then all values 
		are used (required)
		
	(2) Input value field [invalue]:
	
		String naming the field for output raster values [required]
									  
	(3) Output workspace [outws]:
	
		String path to output workspace (required)
		
	(4) Pixel size [pixelsize]: 
	
		Integer defining the output resolution (required)
	
	(5) Raster type [raster_type]:
		
		String file extension for output raster type (optional)
	
	(6) Fixed extent [extent]: 
	
		String defining a feature class or raster which extent will be used 
		(optional)
		
	(7) Snap raster [snap_raster]:
	
		String defining a raster to which result will be snapped
		(optional)

	"""
	implements(IGISTool)

	id = 0

	def __init__(self, parameters, service, *args, **kwargs):
		ArcTool.__init__(self, parameters, service, *args, **kwargs)

		MultiConvertRaster.id = MultiConvertRaster.id + 1
		self.id = MultiConvertRaster.id
		self.name = self.__module__.split('.')[-1]
		
		self.log = ArcLogger("Zupport.%s" % (self.__class__.__name__), 
											 debugging=True)
		

		# Tool needs spatial analyst in order to run
		# TODO: this should be moved to ToolValidator
		try:
			self.register_extension('spatial')
		except LicenseError, e:
			self.log.error(e)
			return 1
		
		self.service = service
		
		self.log.debug(msgInitSuccess)


	def __del__(self):
		if MultiConvertRaster:
			MultiConvertRaster.id = MultiConvertRaster.id - 1

	def run(self):
		
		try:
			self.validate_parameters()
				
			infeature = self.get_parameter(0)
			inconfields = self.get_parameter(1)
			invalue = str(self.get_parameter(2))
			outputws = str(self.get_parameter(3))
			pixelsize = int(str(self.get_parameter(4)))
			raster_type = self.get_parameter(5)
			raster_type = ARC_RASTER_TYPES[raster_type]
			extent = str(self.get_parameter(6))
			snap_raster = str(self.get_parameter(7))
			self.log.debugging = bool(self.get_parameter(8))
			
			try:
				# Is it a ValueField object?
				inconfields = str(inconfields.exportToString())
			except AttributeError:
				# No, it's something else (String or dict)
				pass
			
			if type(inconfields) is types.StringType:
				temp = {}
				for field in inconfields.split(';'):
					temp[field] = 'all'
				inconfields = temp
			
			# Set the extent if provided
			if extent is not None and extent != '':
				self.gp.env.extent = extent
				self.log.debug('Extent set to %s' % self.gp.env.extent)
		
			# Set the snap raster if provided
			if snap_raster is not None:
				self.gp.env.snapRaster = snap_raster
				self.log.debug('Snapping to raster %s' % self.gp.env.snapRaster)
		
			# Check input feature properties
			self.log.debug('Getting Feature Class properties')
			fc_desc = self.gp.Describe(infeature)
			if fc_desc.ShapeType != "Polygon":
				raise FeatureTypeError("Input Feature Class type (%s) not polygon." % fc_desc.ShapeType)

			# Check the input fields
			self.log.debug('Checking if input conditions field(s) %s exists' % ';'.join([key for key in inconfields.keys()]))
			for field in inconfields.keys():
				if not self.gp.ListFields(infeature, field):
					raise FieldError(field, infeature)

			self.log.debug('Checking if output value field %s exists' % invalue)
			if not self.gp.ListFields(infeature, invalue):
				raise FieldError(invalue, infeature)
		
		except FeatureTypeError, fte:
			self.log.exception(fte.value)
			raise

		except FieldError, fe:
			self.log.exception(fe.value)
			raise

		try:
			# all_values is a list of lists holding ALL values for ALL fields
			all_values = []
			field_names = []
			
			# Iterate through a list holding {field_name: fiel_values} 
			# dictionaries
			for field_name, values in inconfields.iteritems():
				field_names.append(field_name)
				
				# Check if values are provided
				if values == 'all':
					# No values provided, get unique values
					self.log.debug('Getting all unique values for field %s' % field_name)
					# Use a set to get the unique field identifiers
					values = set()
	
					rows = self.gp.SearchCursor(infeature)
	
					for row in rows:
						values.add(int(row.getValue(field_name)))
						
					self.log.debug('Unique values for %s: %s' % (field_name, values))
						

				all_values.append(values)
				
			# Cross product all possible combinations of field values
			products = list(product(*all_values))
				
			# Calculate the job queue length based on the number of products
			job_length = len(products)

			# Set the tool progressor
			if self.log.gui:
				self.log.setProgressor("Extracting feature class with multiple field values...",
										max=job_length)

			# Make a feature layer from the feature class
			self.gp.MakeFeatureLayer_management(infeature, "input_feature")

			for i, combination in enumerate(products):
				try:
					
					# Create a valid name for the ouput raster
					raster = '_'.join([name + '_' + str(value) for name, value in zip(field_names, combination)])
					raster = generate_rastername(raster, outputws, raster_type,
												suffix=invalue)
					
					msg = "Selecting and converting %s with following configuration: %s (%s / %s)" % (invalue, (' '.join([name + ': ' + str(value) for name, value in zip(field_names, combination)])), i + 1, job_length)
					
					self.log.progressor(msg, log='info')
					
					# Check that field names and values correspond
					if len(field_names) != len(combination):
						raise ParameterError('Number of field names <%> and values <%s> does not match' % 
											(len(field_names), len(combination)))
					
					# Make the selections
					for name, value in zip(field_names, combination):
						# Set the selection types -> first is a new selection,
						# all consecutive selection are subsets
						if name == field_names[0]:
							selection = "NEW_SELECTION"
						else:
							selection = "SUBSET_SELECTION"
						self.gp.SelectLayerByAttribute_management("input_feature", 
													   	   selection, 
													       "%s = %s" % 
													   		(name, value))
						
					# See if any features are selected
					result = self.gp.GetCount_management("input_feature")
					count = int(result.getOutput(0)) 
					
					self.log.progressor("Polygons: %s." % count, log='info')
					#continue
					
					if not count > 0:
						self.log.progressor("Empty selection, skipping.", log='info')
						continue	
					
					self.log.debug('Extent STILL is %s' % self.gp.env.extent)
					
					# Make the actual conversion
					self.gp.FeatureToRaster_conversion("input_feature", invalue, 
													   raster, pixelsize)
					
					# Build pyramids
					self.log.progressor("Building pyramids", log='info')
					self.gp.BuildPyramids_management(raster)

					self.log.info("Finished conversion")

					# Clear the selection
					self.gp.SelectLayerByAttribute_management("input_feature", 
													   "CLEAR_SELECTION", 
													   "%s = %s" % 
													   (name, value))

					self.log.setProgressorPosition()

				except Exception, error_desc:
					self.log.exception("Failed to convert %s: %s" % (raster, error_desc))
					raise

				self.log.setProgressorPosition()
			
			#self.gp.setParameterAsText(1, outputws)
			
		except FeatureTypeError, fte:
			self.log.exception(fte.value)
			raise

		except FieldError, fe:
			self.log.exception(fe.value)
			raise

		self.log.info('Finished running tool %s' % self.name)
		return 0