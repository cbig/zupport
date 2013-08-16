import types

from zope.interface import implements
from zupport.interfaces import IGISTool

from ..core import ArcTool, LicenseError
from zupport.utilities import (ARC_RASTER_TYPES, msgInitStart, msgInitSuccess)
from zupport.zlogging import ArcLogger

def service():
    return 'aggregate'

def setup(parameters, *args, **kwargs):
    return Aggregate(parameters, service=service(), *args, **kwargs)

class Aggregate(ArcTool):
    """ ArcTool for aggregating data to desired resolution while preserving 
    true NoData values.
    
    Tool will create new subfolders into the output workspace according to 
    target resolution if they do not exist.

    Parameters:
    
    (1) Input raster [inraster] 
    
        String representing the source workspace that contains rasters to be
        aggregated (required)
          
    (2) Output raster [outraster] 
        
        String for the location of the resulting rasters (required)
    
    (3) Cell factor [factors] 
        
        Integer cell factor (multiplier) to be used in the aggregation. 
        Original cell size will be taken from the rasters in the input 
        workspace. (required)
    
    (4) Nodata mode [nodata] 
        
        Boolean defining whether NoData mode is used. 
        True -> resulting aggregated rasters will have NoData
        False -> resulting aggregated rasters will not have NoData
        (required, default: True)
    
    (5) Extent [extent]
    
        String containing 'minX minY maxX maxY' that will be passed on
        to Arcpy.Extent class.
        (optional)
          
    (6) Mask (mask)
    
        String representing raster that will be used as a mask (optional)
        
    (7) Raster type [raster_type] 
    
        String file extension for output raster type (optional)
    

    """
    implements(IGISTool)

    id = 0

    def __init__(self, parameters, service, *args, **kwargs):
        ArcTool.__init__(self, parameters, service, *args, **kwargs)

        Aggregate.id = Aggregate.id + 1
        self.name = self.__class__.__name__
        # Identifier is a combination of the name and the class counter
        self.id = (self.name, Aggregate.id)
        
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
        if Aggregate:
            Aggregate.id = Aggregate.id - 1

    def run(self):
        
        self.validate_parameters()
        if self.ready:
            try:
    
                inraster = str(self.get_parameter(0))
                outraster = str(self.get_parameter(1))
                factor = self.get_parameter(2)
                nodata = self.get_parameter(3)
                raster_type = str(self.get_parameter(4))
                extent = str(self.get_parameter(5))
                snap_raster = str(self.get_parameter(6))
                mask = self.get_parameter(7)
                raster_type = ARC_RASTER_TYPES[raster_type]
                self.log.debugging = self.get_parameter(8)
                
                # Fix the outraster name
                # TODO: do this is more sensible way
                if outraster.endswith('.'):
                    outraster = outraster.replace('.', raster_type)
                    self.log.debug('Output raster name extension fixed to: %s' % outraster)
                
                # Set the extent if provided
                if extent is not None and extent != '':
                    self.log.debug(extent)
                    self.gp.env.extent = extent
                    
                # Set the snap raster if provided
                if snap_raster is not None:
                    self.gp.env.snapRaster = snap_raster
                    self.log.debug('Snapping to raster %s' % snap_raster)
                    
                # Set the mask if provided
                if mask != '':
                    self.gp.env.mask = mask
                    
                # Loop through all the target rasters
                self.log.info('Using cell factor: %s' % factor)
                
                self.log.debug(inraster)
                inraster = self.gp.Raster(inraster)
                
                # Get the native resolution from the raster
                yresolution = inraster.meanCellHeight
                xresolution = inraster.meanCellWidth
                
                if yresolution != xresolution:
                    self.log.warning('Cell width (%s) and height (%s) do not match for raster %s' % (xresolution,
                                                                yresolution,
                                                                inraster))
                
                self.log.info('Aggregating %s' % (inraster))
                
                # Aggregate the original grid to desired resolution
                # FIXME: ArcGIS Spatial Analyst Aggregate tool will
                # create zeros instead of NoData unless all NoData is taken
                # into account ("NODATA" instead of "DATA"). The current 
                # version will convert all zeros back to NoData if nodata
                # mode is on under the assumption that the data has no 
                # real zeros. This should be handled better.
                    
                out_agg = self.gp.sa.Aggregate(inraster, factor, "SUM", 
                                               "EXPAND", "DATA")
                
                # If NoData mode is on, set all zeros null
                if nodata:
                    self.log.debug('Setting zeros to null for %s' % outraster)
                    out_agg = self.gp.sa.SetNull(out_agg,
                                                 out_agg,
                                                 "VALUE = 0")
                
                out_agg.save(outraster)
                #self.log.add_result(out_agg)
                
                self.log.debug('Finished with %s' % outraster)
                self.log.debug('Building pyramids')
                
                self.gp.BuildPyramids_management(outraster)
                    
                self.log.success = True
    
            except StandardError:
                self.log.exception('Exception')
            except KeyError:
                self.log.exception("Unknown raster type. %s" % raster_type)
    
            self.log.info('Finished running tool %s' % self.name)
