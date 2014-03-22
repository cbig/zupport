#!/usr/bin/python
# coding=utf-8


import os
import math
import numpy as np
import numpy.ma as ma

from zope.interface import implements

from zupport.core import ParameterError
from zupport.interfaces import IGISTool
from zupport.plugins.fileio import (size_in_mem, get_nodata_number,
                                    pixeltype_to_pixeltype)
from zupport.utilities import ARC_RASTER_TYPES, msgInitSuccess
from ..core import ArcLogger, ArcTool
from ..utilities import chop_raster


def service():
    return 'rasigmoidal'


def setup(parameters, *args, **kwargs):
    return RASigmoidal(parameters, service=service(), *args, **kwargs)


class RASigmoidal(ArcTool):

    implements(IGISTool)

    id = 0

    def __init__(self, parameters, service, mem_max=500, *args, **kwargs):
        ArcTool.__init__(self, parameters, service, *args, **kwargs)

        self.name = self.__class__.__name__
        # Identifier is a combination of the name and the class counter
        self.id = (self.name, RASigmoidal.id)

        self.log = ArcLogger("Zupport.%s" % (self.__class__.__name__),
                             debugging=True)
        self.mem_max = mem_max * 1000000
        self.log.debug('Memory max set to: %s MB' % mem_max)

        self.service = service

        self.log.debug(msgInitSuccess)

    def __del__(self):
        if RASigmoidal:
            RASigmoidal.id = RASigmoidal.id - 1

    def asym_sigmoidal(self, x, asym=1.0, mod_asym=1.0, xmid=None, lscale=1.0,
                       rscale=1.0):
        if xmid is None:
            xmid = ma.median(x)
        return np.where(x <= xmid,
                        (asym * mod_asym) / (1 + ma.exp((xmid - x) / lscale)),
                        asym / (1 + ma.exp((xmid - x) / rscale)))

    def sigmoidal(self, x, asym=1.0, xmid=None, xmod=0, scale=1.0):
        if xmid is None:
            xmid = ma.median(x)
        xmid = xmid + xmod
        return asym / (1 + ma.exp((xmid - x) / scale))

    def run(self):

        try:

            self.validate_parameters()

            # Raster 1 is the one that will be transformed
            raster1 = self.get_parameter(0)
            # Raster 2 is used in the multiplication
            raster2 = self.get_parameter(1)
            output_raster = self.get_parameter(2)
            raster_type = ARC_RASTER_TYPES[self.get_parameter(3)]
            asym = self.get_parameter(4)
            xmid = self.get_parameter(5)
            lxmod = self.get_parameter(6)
            rxmod = self.get_parameter(7)
            lscale = self.get_parameter(8)
            rscale = self.get_parameter(9)

            self.log.debugging = bool(self.get_parameter(10))

            # Convert input raster paths into Arcpy Raster objects and the the
            # total number of elements in each
            raster1 = self.gp.Raster(raster1)
            raster1_size = raster1.height * raster1.width
            raster2 = self.gp.Raster(raster2)

            self.log.debug('Checking if input raster exist')
            for rasterpath in [raster1.path, raster2.path]:
                if not os.path.exists(rasterpath):
                    raise ParameterError('Path provided does not exist: %s'
                                         % rasterpath)

            # From the following check onwards, it is implicitly assumed that
            # both rasters are the same size, so no further checks are done
            self.log.debug('Checking if input raster dimensions match')
            if raster1.height != raster2.height or raster1.width != raster2.width:
                dim1 = '%sx%s' % (raster1.width, raster1.height)
                dim2 = '%sx%s' % (raster2.width, raster2.height)
                raise ParameterError('Raster dimension do not match: %s %s'
                                     % (dim1, dim2))
            else:
                self.log.debug('Raster dimension: %s rows, %s columns'
                               % (raster1.height, raster1.width))

            # Check for NoData value
            if raster1.noDataValue is not None:
                self.log.debug('Raster 1 NoData value: %s'
                               % raster1.noDataValue)
            else:
                raise ValueError('Fix NoData value for raster %s' % raster1)
            if raster2.noDataValue is not None:
                self.log.debug('Raster 2 NoData value: %s'
                               % raster2.noDataValue)
            else:
                raise ValueError('Fix NoData value for raster %s' % raster2)

            # STEP 1: Calculate the needed memory  and chop up the data ########

            # Raster operations require an array with dtype float64 so
            # calculate how much memory this will consume
            raster1_64_size = size_in_mem(raster1_size, 'float64')
            self.log.debug('%s will require %s B in float64'
                           % (raster1, raster1_64_size))

            # Check if the input needs to be chopped up
            if raster1_64_size > self.mem_max:
                # First try dividing the whole raster in 9 chunks
                nchunks = 9
                while raster1_64_size / nchunks > self.mem_max:
                    nchunks *= 2

                self.log.debug('Input rasters will be divided into %s chunks'
                               % nchunks)

                # Using the same number for rows and columns, get the chunks

                n = int(math.sqrt(nchunks))
                # Use the lower left corner for origin (llc)
                raster_chunks = chop_raster(raster1.height, raster1.width,
                                            nrows=n, ncols=n, origin='llc')
                self.log.debug(raster_chunks)
            else:
                nchunks = 1
                raster_chunks = chop_raster(raster1.height, raster1.width,
                                            nrows=1, ncols=1, origin='llc')

            # Index for the current chunk
            ichunk = 1
            # Indices for the current row and column
            i_y = raster1.extent.YMin
            i_x = raster1.extent.XMin

            # STEP 2: Set up the target raster dataset #########################

            # When using mosaic, the pixel type must be explicitly given,
            # otherwise it will default to 8bit. Keep track what is the
            # largest pixel type and use that for the final raster
            out_pixel_type = 0

            out_pixel_type = pixeltype_to_pixeltype(out_pixel_type,
                                                    'arc_long')
            # 32 bit float will do
            out_pixel_type = '32_BIT_FLOAT'
            # Remember to set the right NoData value as well
            NODATA = get_nodata_number(out_pixel_type)

            if nchunks != 1:
                self.log.debug('Creating target raster %s' % output_raster)
                # For some reason ArcGIS tool Mosaic to New Raster ignores
                # rasters -> create a new data set and mosaic into it  -> this
                # is not true if target workspace is a FGD, however, creating
                # an empty dataset and mosaicing into it seems to be faster
                out_name = os.path.basename(output_raster)
                out_path = os.path.dirname(output_raster)
                self.gp.CreateRasterDataset_management(out_path,
                                                       out_name,
                                                       raster1.meanCellHeight,
                                                       out_pixel_type,
                                                       raster1.spatialReference,
                                                       1,
                                                       pyramids="PYRAMIDS -1 CUBIC LZ77",
                                                       compression='LZ77')

            # Certain parameters are setup for the whole raster, therefore they
            # need to be calculated from the whole raster, not the individual
            # chunks
            self.log.debug('Getting information on the whole raster')
            raster1_max = raster1.maximum
            self.log.debug('Raster max: %s' % raster1_max)
            self.log.debug('Raster xmid: %s' % xmid)

            # STEP 3: Extract the data in chunks ##############################
            for chunk_row in raster_chunks:
                # Each chunk_row is a list of (nrows, ncols) tuples (chunks)
                for chunk in chunk_row:
                    chunk_nodata = False
                    self.log.debug('Reading in chunk %s/%s' % (ichunk,
                                                               nchunks))
                    self.log.debug('i_x: %s' % i_x)
                    self.log.debug('i_y: %s' % i_y)
                    nrows = chunk[0]
                    ncols = chunk[1]
                    # Point x and y coordinates need to relate to raster's
                    # actual coordinates! The direction is - row by row - from
                    # from left to right and bottom to top
                    llc = self.gp.Point(i_x, i_y)
                    # NoData value will be the same as for the raster itself
                    self.log.debug('Reading in raster 1')
                    array1 = self.gp.RasterToNumPyArray(raster1,
                                                        lower_left_corner=llc,
                                                        ncols=ncols,
                                                        nrows=nrows)

                    self.log.debug('Reading in raster 2')
                    array2 = self.gp.RasterToNumPyArray(raster2,
                                                        lower_left_corner=llc,
                                                        ncols=ncols,
                                                        nrows=nrows)
                    # self.log.debug('Array 1 min: %s' % array1.min())
                    # self.log.debug('Array 2 min: %s' % array2.min())
                    # STEP 4: Mask the arrays to account for NoData ############

                    # Create masked arrays so NoData is not used in the
                    # transformations
                    self.log.debug('Masking NoData for raster 1')
                    ma_array1 = ma.masked_where(array1 == raster1.noDataValue,
                                                array1)
                    # self.log.debug('Masked array 1 max: %s' % ma_array1.max())
                    # Check if masked array has any non-mask values
                    # NOTE: Skipping a chunk because it's all NoData will cause
                    # the resulting raster having different dimensions than
                    # the original rasters

                    if ma_array1.count() < 1:
                        self.log.debug('Array 1 completely NoData')
                        chunk_nodata = True

                    else:
                        self.log.debug('Masking NoData for raster 2')
                        ma_array2 = ma.masked_where(array2 == raster2.noDataValue,
                                                    array2)

                    self.log.debug('Data min: %s' % ma_array1.min())
                    self.log.debug('Data max: %s' % ma_array1.max())
                    #self.log.debug('Data mean: %s' % ma_array1.mean())
                    #self.log.debug('Data median: %s' % ma.median(ma_array1))

                    # STEP 5: Perform the data transformation ##################

                    # There are some data elements to be transformed
                    if not chunk_nodata:
                        self.log.debug('Calculationg sigmoidal transformation')
                        ma_trans_array1 = np.where(ma_array1 <= xmid,
                                                   self.sigmoidal(ma_array1,
                                                           asym=asym,
                                                           xmid=(xmid +  lxmod),
                                                           scale = lscale),
                                                   self.sigmoidal(ma_array1, 
                                                           xmid=(xmid + rxmod),
                                                           scale = rscale))
                
                        #self.log.debug('Masked trans array max: %s' % ma_trans_array1.max())
                        #self.log.debug('Masked array (vol) max: %s' % ma_array2.max())
                        
                        self.log.debug('Multiplying transformed array with array 2')

                        ma_index_array = ma_trans_array1 * ma_array2

                        self.log.debug('Filling masked array')
                        # Use the NODATA value, not raster1.noDataValue
                        index_array = ma.filled(ma_index_array,
                                                fill_value=NODATA)

                        del ma_trans_array1

                    # Chunk is completely NoData, no transformation is needed
                    else:
                        self.log.debug('Filling masked array')
                        # Use the NODATA value, not raster1.noDataValue
                        self.log.debug('Data min: %s' % ma_array1.min())
                        index_array = np.where(array1 == raster1.noDataValue,
                                               NODATA,
                                               array1)

                    self.log.debug('Index array min: %s' % index_array.min())
                    # STEP 6: Write our the data ###############################

                    if len(raster_chunks) == 1:
                        self.log.debug('Converting array into a raster %s '
                                       % output_raster)
                        raster = self.gp.NumPyArrayToRaster(index_array,
                                                            lower_left_corner=llc,
                                                            x_cell_size=raster1.meanCellWidth,
                                                            y_cell_size=raster1.meanCellHeight,
                                                            value_to_nodata=NODATA)
                        raster.save(output_raster)
                    else:
                        self.log.debug('Converting array into a temporary Raster')
                        raster = self.gp.NumPyArrayToRaster(index_array,
                                                            lower_left_corner=llc,
                                                            x_cell_size=raster1.meanCellWidth,
                                                            y_cell_size=raster1.meanCellHeight,
                                                            value_to_nodata=NODATA)
                        self.log.debug('Adding raster to output raster dataset %s'
                                       % output_raster)
                        self.gp.Mosaic_management(raster,
                                                  output_raster,
                                                  nodata_value=NODATA)

                    i_x += ncols * raster1.meanCellWidth

                    ichunk += 1

                i_x = raster1.extent.XMin
                i_y += nrows * raster1.meanCellHeight

            return 1

        except ParameterError, e:
            self.log.exception('Error with parameters: %s' % e)
            raise
        except StandardError, e:
            self.log.exception('Exception: %s' % e)
            raise
        except KeyError:
            self.log.exception("Unknown raster type. %s" % raster_type)
            raise
