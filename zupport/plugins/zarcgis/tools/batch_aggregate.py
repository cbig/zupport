import os
import types

from zope.interface import implements
from zupport.interfaces import IGISTool

from zupport.plugins.zarcgis import ArcTool, LicenseError
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
    
    (1) Input workspace [inworkspace] 
        - String representing the source workspace that contains rasters to be
          aggregated (required)
          
    (2) Output workspace [outworkspace] 
        - String for the location of the resulting rasters (required)
    
    (3) Cell factor [factors] 
        - Integer cell factor (multiplier) to be used in the aggregation. 
          Original cell size will be taken from the rasters in the input 
          workspace. (required)
    
    (4) Nodata mode [nodata] 
        - Boolean defining whether NoData mode is used. 
          True -> resulting aggregated rasters will have NoData
          False -> resulting aggregated rasters will not have NoData
         (required, default: True)
    
    (5) Extent [extent]
        - String containing 'minX minY maxX maxY' that will be passed on
          to Arcpy.Extent class.
          (optional)
          
    (6) Mask (mask)
        - String representing raster that will be used as a mask
          (optional)
        
    (7) Raster type [raster_type] 
        - String file extension for output raster type 
          (optional)
    

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
        
        # Lazy loading of tools!
        from ..utilities import generate_rastername
        
        self.validate_parameters()
        if self.ready:
            try:
    
                self.workspace = self.get_parameter(0)
                outworkspace = str(self.get_parameter(1))
                factor = self.get_parameter(2)
                nodata = self.get_parameter(3)
                extent = self.get_parameter(4)
                mask = self.get_parameter(5)
                include = self.get_parameter(6)
                raster_type = self.get_parameter(7)
                raster_type = ARC_RASTER_TYPES[raster_type]
                
                # Set the extent if provided
                if extent is not None and extent != '':
                    self.log.debug(extent)
                    if type(extent) is types.StringType:
                        extent = [float(coord) for coord in extent.split(',')]
                    self.gp.env.extent = self.gp.Extent(extent)
                    
                # Set the mask if provided
                if mask != '':
                    self.gp.env.mask = mask
                    
                rasters_all = self.gp.ListRasters()
                self.log.debug('Rasters found:\n%s' % rasters_all)
                    
                if include:
                    job_length = len(include)
                else:
                    job_length = len(rasters_all)
                
                counter = 1
                    
                # List to control that all input rasters are of the same resolution
                check_resolutions = []
                    
                # Loop through all the target rasters
                self.log.info('Using cell factor: %s' % factor)
                for raster in rasters_all:
                    
                    # If includes are provided, see if current raster is in
                    if include and raster not in include:
                        continue
                    
                    # Convert raster string into a Raster object
                    raster = self.gp.sa.Raster(raster)
                    
                    # Get the native resolution from the raster
                    yresolution = raster.meanCellHeight
                    xresolution = raster.meanCellWidth
                    
                    if counter > 1:
                        if xresolution not in check_resolutions:
                            self.log.warning('Different resolution (%s) for raster %s' % (xresolution, raster))
                    
                    # Use only xresolution
                    check_resolutions.append(xresolution)
                    
                    if yresolution != xresolution:
                        self.log.warning('Cell width (%s) and height (%s) do not match for raster %s' % (xresolution,
                                                                    yresolution,
                                                                    raster))
                    
                    # Calculate the desired target resolution and figure out
                    # if suitable sub folders exist
                    target_resolution = factor * xresolution
                    outdir = os.path.join(outworkspace, str(int(target_resolution)))
                    if not os.path.exists(outdir):
                        self.log.info('Creating directory %s' % outdir)
                        try:
                            os.mkdir(outdir)
                        except OSError, e:
                            self.log.error('Could not create directory %s: %s' % (outdir, e))
                    
                    self.log.info('[%s/%s] Aggregating %s' % (counter, 
                                                              job_length,
                                                              raster))
                    
                    output = generate_rastername(raster.name, 
                                                 outdir, 
                                                 ext=raster_type, 
                                                 suffix='%s' % int(target_resolution))
                    
                    # Aggregate the original grid to desired resolution
                    # FIXME: ArcGIS Spatial Analyst Aggregate tool will
                    # create zeros instead of NoData unless all NoData is taken
                    # into account ("NODATA" instead of "DATA"). The current 
                    # version will convert all zeros back to NoData if nodata
                    # mode is on under the assumption that the data has no 
                    # real zeros. This should be handled better.
                        
                    out_agg = self.gp.sa.Aggregate(raster, 
                                                       factor, 
                                                       "SUM", 
                                                       "EXPAND", 
                                                       "DATA")
                    
                    # If NoData mode is on, set all zeros null
                    if nodata:
                        self.log.debug('Setting zeros to null for %s' % out_agg)
                        out_agg = self.gp.sa.SetNull(out_agg,
                                                         out_agg,
                                                         "VALUE = 0")
                    
                    out_agg.save(output)
                    #self.log.add_result(out_agg)
                    
                    self.log.debug('Finished with %s' % output)
                    self.log.debug('Building pyramids')
                    
                    self.gp.BuildPyramids_management(output)
                        
                    counter += 1
                        
                self.log.success = True
    
            except StandardError:
                self.log.exception('Exception')
            except KeyError:
                self.log.exception("Unknown raster type. %s" % raster_type)
    
            self.log.info('Finished running tool %s' % self.name)
