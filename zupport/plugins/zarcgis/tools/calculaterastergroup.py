#!/usr/bin/python
# coding=utf-8


import os

from zope.interface import implements
from zupport.interfaces import IGISTool

from ..core import ArcRasterTool, ArcRasterGroupIterator
from zupport.core import ParameterError
from zupport.plugins.fileio import parse_operator
from zupport.utilities import msgInitSuccess
from zupport.zlogging import ArcLogger

def service():
	return 'calculaterastergroup'

def setup(parameters, *args, **kwargs):
	return CalculateRasterGroup(parameters, service=service(), *args, **kwargs)

class CalculateRasterGroup(ArcRasterTool):
	""" ArcTool for doing arithmetics on multiple rasters with NoData.
	
	Normally NoData propagates with summation (value + NoData = NoData), 
	subtraction, multiplication and converting NoData to a value (e.g. 0) is 
	not desirable in order not to mix NoData with real values. 
	ArcCalculateRasterGroup works with a set of rasters  (defined by a naming 
	convention) and builds a result raster where NoData values are preserved
	and value cells are used in a simple raster algebra operation.

	Parameters:
	(0) Input workspace [inws] - String input workspace holding the rasters
								  	(required)
	(1) Output workspace [outws] -  String path to output workspace (required)
	(2) Operator [operator] -  String defining which raster algebra operation
							   is applied to rasters (required)
	(3) Group template [template] - String used to define which rasters are
							  		grouped into a set (optional); syntax is 
							  		based on key identifiers: name_body_<ID>
							  		where name body is a common sub string
							  		shared by all rasters in the same group and
							  		<ID> is identifies rasters within group
	(4) Group identifier [identifier] - String identifying template tag that 
										is/are used as a basis for grouping 
										(optional); 
	(5) Reference table [reftable] - DataFrame object used for lookup 
									(optional); this lookup table can be used
									for extra grouping not apparent from the 
									naming convention. <ID2> is used for lookup
									link from <ID1>. For example 
									index_PUULAJI_11.img with template 
									<BODY1>_<BODY2>_<ID2> would match column
									"PUULAJI" with value 11 to a grouping 
									variable in reference group [refgroup]
	(6) Reference fields [reffields] - Tuple defining the field mapping in the 
									  dataframe. ("A", "B") would match values
									  from <ID1> in field A to a value in field
									  "B".
									  

	"""
	implements(IGISTool)

	id = 0

	def __init__(self, parameters, service,  *args, **kwargs):
		ArcRasterTool.__init__(self, parameters, service, *args, **kwargs)

		CalculateRasterGroup.id = CalculateRasterGroup.id + 1
		self.name = self.__class__.__name__
		# Identifier is a combination of the name and the class counter
		self.id = (self.name, CalculateRasterGroup.id)

		self.log = ArcLogger("Zupport.%s" % (self.__class__.__name__), 
                                             debugging=True)

		self.service = service

		self.log.debug(msgInitSuccess)

	def __del__(self):
		if  CalculateRasterGroup:
			CalculateRasterGroup.id = CalculateRasterGroup.id - 1
	
	def run(self):
		
		try:
			self.validate_parameters()
				
			self.workspace = str(self.get_parameter(0))
			self.log.debug('Found %s rasters in workspace %s' % (len(self.files),
																 self.workspace))
			wildcard = self.get_parameter(1)
			template = self.get_parameter(2)
			grouptags = self.get_parameter(3)
			operator = parse_operator(self.get_parameter(4))
			
			outws = self.get_parameter(5)
			# These will be None if not provided
			reftable = self.get_parameter(6)
			reffields = self.get_parameter(7)
			self.log.debugging = bool(self.get_parameter(8))
			
			# Use mapping reffields[0] -> reffields[1] from reftable
			
			fields = reftable.get_fields()
			if reffields[0] not in fields:
				raise ParameterError("Provided reference field %s not found in refernce table %s" % (reffields[0], reftable))
			if reffields[1] not in fields:
				raise ParameterError("Provided reference field %s not found in refernce table %s" % (reffields[1], reftable))
			
			mapping = {}
			for value in reftable.get_all_values(reffields[0]):
				# 9999 is missing value
				if value == 9999:
					continue
				match_row = reftable.where_field_equal(reffields[0], value)
				mapping[value] = getattr(match_row, reffields[1])
				
			
			# Parse the raster files in the workspace based on the group tags
			rasteriterator = ArcRasterGroupIterator(self, self.workspace, 
												    wildcard, template)
			rasteriterator.set_grouping(grouptags, mapping)
			
			# Calculate the job queue length based on provided options. If no
			# identifying field is used, the length of rasters defines the job
			# queue length
			job_length = len(rasteriterator)
			
			# Set the tool progressor
			if self.log.gui:
				self.log.setProgressor("Summing multiple rasters...",
										max=job_length)
			
			# Iterate over the parsed workspace. Remember that group is a list
			# of ParsedFileNames
			for group_id, group in rasteriterator.iteritems():
				
				self.log.debug('Group %s (%s) has %s rasters' % (int(group_id), 
																 reffields[1],
																 len(group)))
				
				# Each raster within the group is summed to a common result 
				# raster -> each group has one output raster
				
				# Check that body identifiers are ok
				name_bodies = [raster.body for raster in group]
				if not all([item == name_bodies[0] for item in name_bodies]):
					self.log.progressor('Multiple name bodies found, defaulting to %s' % (name_bodies[0]), 
									log='warning')
					
				if group[0].extension:
					extension = group[0].extension
				else:
					extension = ""
				
				output_zero = os.path.join(outws, '%s_%s_%s%s%s' % (group[0].get_tag('BODY1'),
																  int(group_id),
																  group[0].get_tag('BODY3'),
																  "TMP",
																  extension))																  
				cmds = []
				
				for raster in group:
					
					cmds.append("self.gp.sa.Con(self.gp.sa.IsNull('%s'), 0, '%s')" % (raster, raster))
					
				cmd = operator.join(cmds)
				
				self.log.info('Summing rasters in group %s' % int(group_id))
				#res = self.gp.sa.SingleOutputMapAlgebra(cmd, output_zero)
				op1 = eval(cmd)
				op1.save(output_zero)
				
				self.log.debug('Reclassifying NoData for group %s' % int(group_id))
				output = output_zero.replace('TMP', '')
				cmd = 'self.gp.sa.SetNull(%s == 0)' % output_zero
				op2 = self.gp.sa.SetNull(output_zero, output_zero, "VALUE <= 0")
				op2.save(output)
				self.gp.Delete_management(output_zero)
				
				if self.log.gui:
					self.log.setProgressorPosition()
			
			return 1
					
		except Exception, e:
			self.log.exception(e)
			return 1

		self.log.info('Finished running tool %s' % self.name)
		return 0
