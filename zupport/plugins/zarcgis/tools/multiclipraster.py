#!/usr/bin/python
# coding=utf-8

__all__ = ['setup']

import sys

#from zope.interface import implements
#from zupport.core.izupport import IGisTool

from zupport.arcgis import (multisplit, generate_rastername, FeatureTypeError, 
							FieldError, LicenseError)
from zupport.core import ArcTool, OSGeoTool
from zupport.utilities import ParameterError, ARC_RASTER_TYPES
from zupport.zupportlogging import ArcLogger

def setup(backend):
	if backend == 'arcgis':
		return ArcMultiClipRaster
	if backend == 'osgeo':
		return OSGeoMultiClipRaster
	else:
		raise ValueError('Bad backend description: %s.' % backend)

class ArcMultiClipRaster(ArcTool):
	""" ArcTool for clipping several rasters in batch.

	Parameters:
	(0) Rasters [rasters] - List of rasters (;-separated) to be clipped 
							(required)
	(1) Output workspace [outws] -  String path to output workspace (required)
	(2) Raster type [raster_type] - String file extension for outpur raster type 
									(optional)
	(3) Clipper [clipper] - String path to clip Feature Layer (required)
	(4) ID Field [id_field] - String identifying field (optional)

	"""
	#implements(IGisTool)

	id = 0

	def __init__(self, backend, parameters, *args, **kwargs):
		ArcTool.__init__(self, backend, parameters, *args, **kwargs)

		ArcMultiClipRaster.id = ArcMultiClipRaster.id + 1
		self.id = ArcMultiClipRaster.id
		self.name = self.__module__.split('.')[-1]
		
		self.log = ArcLogger("%s [%s]" % (self.__module__, backend))

		# Tool needs spatial analyst in order to run
		# TODO: this should be moved to ToolValidator
		try:
			self.register_extension('spatial')
		except LicenseError, e:
			self.log.error(e)
			return 1

	def __del__(self):
		if ArcMultiClipRaster:
			ArcMultiClipRaster.id = ArcMultiClipRaster.id - 1

	def run(self):
		
		try:
			self.validate_parameters()
				
			rasters = multisplit(self.get_parameter(0))
			outws = self.get_parameter(1)
			raster_type = self.get_parameter(2)
			raster_type = ARC_RASTER_TYPES[raster_type]
		
		except ParameterError:
			self.log.exception('Error with parameters')
			raise
		except StandardError:
			self.log.exception('Exception')
			raise
		except KeyError:
			self.log.exception("Unknown raster type. %s" % raster_type)
			raise

		clipper = self.get_parameter(3)
		id_field = self.get_parameter(4)

		try:
			# Check clipper feature properties
			fc_desc = self.gp.Describe(clipper)
			if fc_desc.ShapeType != "Polygon":
				raise FeatureTypeError("Clipping Feature Class not polygon.")

			# Check id_field
			if not id_field in fc_desc.Fields:
				id_field = None

			# Use a set to get the unique field identifiers
			uniques = set()

			if id_field:
				if not self.gp.ListFields(clipper, id_field):
					raise FieldError(id_field, clipper)
				else:
					# Get all the *unique* values in the id field
					rows = self.gp.SearchCursor(clipper)
					row = rows.Next()

					while row:
						uniques.add(row.Getvalue(id_field))
						row = rows.Next()

			# Calculate the job queue length based on provided options. If no
			# identifying field is used, the length of rasters defines the job
			# queue length
			job_length = len(rasters) + len(uniques)

			# Set the tool progressor
			if self.log.gui:
				self.log.setProgressor("Extracting multiple rasters...",
										max=job_length)

			for raster in rasters:
				try:
					# Using identifying field
					if id_field:
						# Make a feature layer from the feature class
						self.gp.MakeFeatureLayer(clipper, "clip_feature")

						for field_value in uniques:
						
							self.log.progressor("Extracting %s with field value %s" %  
										  		(raster, field_value), 
										  		log='info')

							# Create a valid name for the ouput raster
							out_raster = generate_rastername(raster, outws,
															raster_type,
															suffix="_%s_%s" % (id_field, field_value))

							# Select the right clipping feature
							# FIXME: this does not work for personal
							# geodatabases
							self.gp.SelectLayerByAttribute("clip_feature", "NEW_SELECTION", "%s = %s" % (id_field, field_value))

							# Extract raster by mask
							self.gp.ExtractByMask_sa(raster, "clip_feature",
														 out_raster)

							# Build pyramids
							self.log.progressor("Building pyramids", log='info')
							self.gp.BuildPyramids_management(out_raster)

							self.log.info("Finished extracting %s with %s value %s" %
									 	  (raster, id_field, field_value))

							self.log.SetProgressorPosition()

					# Using one clipper feature class
					else:
						# Update the progressor label
						self.log.progressor("Extracting %s" % raster, log='info')

						# Create a valid name for the ouput raster
						out_raster = generate_rastername(raster, outws,
														 raster_type)

						# Extract raster by mask
						self.gp.ExtractByMask_sa(raster, clipper,
													  out_raster)

						# Build pyramids
						self.log.progressor("Building pyramids", log='info')
						self.gp.BuildPyramids_management(out_raster)

						self.log.info("Finished extracting %s with %s" %
									 (raster, clipper))

				except Exception, error_desc:
					self.log.exception("Failed to extract %s: %s" % (raster, error_desc))
					raise

				self.log.setProgressorPosition()

		except FeatureTypeError, fte:
			self.log.exception(fte.value)
			raise

		except FieldError, fe:
			self.log.exception(fe.value)
			raise

		self.log.info('Finished running tool %s' % self.name)
		return 0

class OSGeoMultiClipRaster(OSGeoTool):

	def __init__(self, *args, **kwargs):
		pass

if __name__ == '__main__':
#	tool = MultiClipRaster.setup('arcgis',
#				 r"G:\Data\Metsakeskukset\Etela-Savo\VMI\MSNFI.gdb\Keskipituus;G:\Data\Metsakeskukset\Etela-Savo\VMI\MSNFI.gdb\Tilavuus_koivu",
#				 r"G:\Data\tmp\Scratch", "ERDAS IMAGINE",
#				 r"G:\Data\GRASS\ArcData\sample_area_N_es.shp", None)
#	tool = MultiClipRaster.setup('arcgis')
#	tool.run()
#	p = MultiClipRaster.parameters()
#	print p
	pass
