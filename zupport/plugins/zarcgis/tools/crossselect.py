#!/usr/bin/python
# coding=utf-8

from zope.interface import implements
from zupport.interfaces import IGISTool

from zupport.core import ParameterError
from ..errors import LicenseError
from ..utilities import generate_rastername
from ..core import ArcTool
from zupport.utilities import msgInitStart, msgInitSuccess, ARC_RASTER_TYPES
from zupport.zlogging import ArcLogger

def service():
    return 'crossselect'

def setup(parameters, *args, **kwargs):
    return CrossSelect(parameters, service=service(), *args, **kwargs)

class CrossSelect(ArcTool):
    
    implements(IGISTool)
    
    """ ArcTool for batch selecting pixels from rasters in workspace based on 
    a single raster.
    
    Tool works on a set of rasters in a workspace and uses a reference raster's
    unique values to select pixels from target rasters. For example, if 
    reference raster would represent land use classes [1, 2, 3] and rasters A
    and B would have continuous values ArcCrossSelect would create 6 new rasters
    -> 1 / land use class / value raster.

    (0) Reference raster [refraster] - String representing reference raster 
                                       based on which the selection will be 
                                       made (required)
    (1) Input workspace [inworkspace] - String representing the source 
                                         workspace that contains value rasters
                                         (required)
    (2) Output workspace [outworkspace] - String for the location of the 
                                          resulting rasters (required)
    (3) Include values [include] - List holding values in the reference raster
                                   to include (optional, default: None)
    (4) Exclude values [exclude] - List holding values in the reference raster
                                   to exclude (optional, default: None)
    (5) Raster format [raster_type] - String for the output raster format
                                     (optional, default: "img")
    (6) Output name tag [tag] - String to tag the the output names. Will be 
                                placed between the raster name body and value 
                                identifier. tag = kp -> A_kp1.img
    """

    id = 0

    def __init__(self, parameters, service, *args, **kwargs):
        ArcTool.__init__(self, parameters, service, *args, **kwargs)

        CrossSelect.id = CrossSelect.id + 1
        self.id = CrossSelect.id
        self.name = self.__module__.split('.')[-1]
        
        self.log = ArcLogger("Zupport.%s" % (self.__class__.__name__), 
                                             debugging=True)

        self.log.debug(msgInitStart)

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
        if CrossSelect:
            CrossSelect.id = CrossSelect.id - 1

    def run(self):
    
        try:
            self.validate_parameters()
                
            refraster = self.gp.sa.Raster(self.get_parameter(0))
            self.workspace = self.get_parameter(1)
            outworkspace = self.get_parameter(2)
            # FIXME: currently there is no way of reading all the unique values 
            # in the raster, but they must be provided as a list
            include = self.get_parameter(3)
            exclude = self.get_parameter(4)
            raster_type = self.get_parameter(5)
            tag = self.get_parameter(6)
            raster_type = ARC_RASTER_TYPES[raster_type]
        
            # Get all the rasters in the input workspace
            rasters_all = self.gp.ListRasters()
            
            # Get exclude out of include
            include = set(include) -  set(exclude)
            
            # Calculate the job queue length based on provided options
            job_length = len(rasters_all) * len(include)
            
            # Set the tool progressor
            if self.log.gui:
                self.log.setProgressor("Cross selecting multiple rasters...",
                                        max=job_length)
            
            # Loop through all the rasters in the input workspace
            for raster in rasters_all:
                # Loop through all the values in include list
                for value in include:
                    
                    self.log.info('Selecting from %s with %s value %s' % 
                                  (raster, refraster.name, value))
                    
                    output = generate_rastername(raster, 
                                                 outworkspace, 
                                                 ext=raster_type, 
                                                 suffix='%s_%s' % (tag, value))
                    
                    outCon = self.gp.sa.Con(refraster, raster, 
                                                "#", "VALUE = %s" % value)
                    outCon.save(output)
                    #self.log.add_result(outCon)
                
                    if self.log.gui:
                        self.log.setProgressorPosition()
       
        except Exception, error_desc:
                self.log.exception(error_desc)
                raise

        except ParameterError, fte:
            self.log.exception(fte.value)
            raise

        self.log.info('Finished running tool %s' % self.name)
        return 0