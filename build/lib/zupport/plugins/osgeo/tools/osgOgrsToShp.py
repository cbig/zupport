#!/usr/bin/python
# coding=utf-8
###############################################################################
# $Id$
#
# Project:  OGR Python samples
# Purpose:  Apply a transformation to all OGR geometries.
# Author:   Frank Warmerdam, warmerdam@pobox.com
#
###############################################################################
# Copyright (c) 2006, Frank Warmerdam <warmerdam@pobox.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
###############################################################################

import os

from zupport.core.gisutils import OSGeoBatchTool
from zupport.resources.messages import msgConvSuccess, msgConvFail
from zupport.resources.drivers import drivers

class BatchMapinfoToShp:
    """
    DooBar
    """

    def __init__(self, inworkspace=None, outworkspace=None):
        OSGeoBatchTool.__init__(self, inworkspace, outworkspace)

        # What's this??
        self.layer_name = None

        # Set the driver
        self.workspace.set_driver(drivers['MapInfo File'])

    def run(self):

        for in_file in self.workspace:

            print 'Starting with file: %s...' % in_file

            ####################################################################
            # Open the datasource to operate on.

            in_dsource = self.ogr.Open(in_file, update=0)

            if self.layer_name is not None:
                in_layer = in_dsource.GetLayerByName(self.layer_name)
            else:
                in_layer = in_dsource.GetLayer(0)

            in_defn = in_layer.GetLayerDefn()

            ####################################################################
            # Create a suitable output file name
            outfile = os.path.join(self.output, os.path.basename(in_file))

            ####################################################################
            #    Create output file with similar information.

            shp_driver = self.ogr.GetDriverByName('ESRI Shapefile')
            if os.path.exists(outfile):
                shp_driver.DeleteDataSource(outfile)

            shp_ds = shp_driver.CreateDataSource(self.output)

            shp_layer = shp_ds.CreateLayer(in_defn.GetName(),
                                            geom_type=in_defn.GetGeomType(),
                                            srs=in_layer.GetSpatialRef())

            in_field_count = in_defn.GetFieldCount()

            for fld_index in range(in_field_count):
                src_fd = in_defn.GetFieldDefn(fld_index)

                fd = self.ogr.FieldDefn(src_fd.GetName(), src_fd.GetType())
                fd.SetWidth(src_fd.GetWidth())
                fd.SetPrecision(src_fd.GetPrecision())
                shp_layer.CreateField(fd)

            ####################################################################
            # Process all features in input layer.

            in_feat = in_layer.GetNextFeature()
            FID = 0
            while in_feat is not None:

                try:
                    geom = in_feat.GetGeometryRef().Clone()

                    #geom = WalkAndTransform(geom)

                    out_feat = self.ogr.Feature(
                                            feature_def=shp_layer.GetLayerDefn()
                                            )
                    out_feat.SetFrom(in_feat)
                    out_feat.SetGeometryDirectly(geom)

                    shp_layer.CreateFeature(out_feat)
                    out_feat.Destroy()
                except AttributeError, e:
                    #print '%s FID %s has void geometry.' % (e, FID)
                    pass

                in_feat.Destroy()
                in_feat = in_layer.GetNextFeature()
                FID = FID + 1

            print msgConvSuccess % in_file

            #############################################################################
            # Cleanup

            shp_ds.Destroy()
            in_dsource.Destroy()

if __name__ == '__main__':

    inws = r'H:\Data\Metsahallitus\ArcGIS\Mapinfo\2009\LP_Pohjanmaa'
    outws = r'H:\Data\Metsahallitus\ArcGIS\Shapefiles\2009\Pohjanmaa'

    tool = BatchMapinfoToShp(inws, outws)
    tool.run()
