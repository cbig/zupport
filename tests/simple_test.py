import os, sys
import numpy as np
from arcpy import RasterToNumPyArray, NumPyArrayToRaster, Raster

# Maximum memory available for each block
MAXMEM = 500000 # = 500 MB
# Amount of bytes required by raster pixel type
PIXELTYPE = {'U1': 0.125,
             'U2': 0.25,
             'U4': 0.5,
             'U8': 1.0,
             'uint8': 1.0,
             'S8': 1.0,
             'int8': 1.0,
             'U16': 2.0,
             'uint16': 2.0,
             'S16': 2.0,
             'int16': 2.0,
             'U32': 4.0,
             'uint32': 4.0,
             'S32': 4.0,
             'int32': 4.0,
             'F32': 4.0,
             'float32': 4.0,
             'F64': 8.0,
             'float64': 8.0}

def size_in_mem(size, type, unit='MB'):
    
    if isinstance(type, np.dtype):
        type = str(type)
        
    units = {'kB': 1000, 
             'MB': 1000000,
             'GB': 1000000000}
    return (size * PIXELTYPE[type] / units[unit])

inraster = r"C:\Data\Staging\Output\MLVMI_puusto\ositteet\PUULAJI_1_OSITE_1_lpm.img"
ws = os.path.dirname(inraster)

raster = Raster(inraster)
raster_size = raster.width * raster.height

print('Raster shape: %s x %s' % (raster.height, raster.width))
print('Raster size: %s' % (raster_size))
print('Raster pixel type: %s' % raster.pixelType)
# In reality uncrompessed size is smaller (as seen from ArcCatalog) -> maybe
# NoData doesn't take that much space?
print('Raster uncompressed size: %s MB' % (size_in_mem(raster_size, 
                                                       raster.pixelType)))
print('float64 will consume: %s MB' % (size_in_mem(raster_size, 'F64')))

array = RasterToNumPyArray(inraster)
print('Array shape: %s x %s' % (array.shape[0], array.shape[1]))
print('Array size: %s' % array.size)
print('Array dtype: %s' % array.dtype)
array_mem_size = size_in_mem(array.size, array.dtype)
print('Array consumes memory: %s MB' % (array_mem_size))
array_sum = array.sum(1)
array_sum.shape = (array.shape[0], 1)
print('Array sum shape: %s x %s' % (array_sum.shape[0], array_sum.shape[1]))
print('Array sum size: %s' % array_sum.size)
print('Array sum dtype: %s ' % array_sum.dtype)
array_sum_mem_size = size_in_mem(array_sum.size, array_sum.dtype)
array_sum_mem_size_max = array_sum_mem_size * array_sum.shape[0]
print('Array sum consumes memory: %s MB' % (array_sum_mem_size))
print('Array sum consumes memory (multiplied by rows (%s)): %s MB' % (array_sum.shape[0],
                                                                      array_sum_mem_size_max))
float_array = array * 1.0
print('Float array size: %s' % float_array.size)
print('Float array dtype: %s ' % float_array.dtype)
float_array_mem_size = size_in_mem(float_array.size, float_array.dtype)
print('Float array consumes memory: %s MB' % (float_array_mem_size))
print('%s' % float_array.nbytes) 

print('Combined memory usage so far: %s MB' % (array_mem_size + array_sum_mem_size + float_array_mem_size))
print('Combined MAX memory usage so far: %s MB' % (array_mem_size + array_sum_mem_size_max + float_array_mem_size))

try:
    array_perc = float_array / array_sum
except MemoryError:
    print(str(sys.exc_info()))
#new_array_perc = (array * 1.0) / new_array_sum
#new_raster = NumPyArrayToRaster(new_array_perc)
#new_raster.save(os.path.join(ws, 'new_raster.img'))
print("Done")
