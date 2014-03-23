from zupport.core.gisutils_legacy import ArcBatchTool

#!/usr/bin/python
# coding=utf-8

import os

from zupport.core.gisutils import ArcBatchTool
from zupport.resources.messages import msgInWsNonExist, msgConvSuccess, msgConvFail

class ArcBatchRasterToAscii(ArcBatchTool):

    def __init__(self, input=None, output=None, overwrite=True):
        ArcBatchTool.__init__(self, input, output)

        try:
            self.__overwrite = overwrite

            # Rest of the parameters are specific to this tool class

            # Get raster name filter
            if self.parameters > 2:
                self.__filter = self.parameters[2]
            else:
                self.__filter = filter

            if self.parameters > 3:
                # Check overwrite
                self.gp.OverwriteOutput = self.parameters[3]
            else:
                self.gp.OverwriteOutput = overwrite

        except Exception, ErrorDesc:
            # Except block if the tool could not run at all.
            # For example, not all parameters are provided, or if the output
            # path doesn't exist.
            self.gp.AddError(str(ErrorDesc))

    def run(self):

        try:

            # Check that the workspace exists
            if not self.gp.Exists(self.input):
                raise Exception, msgInWsNonExist % (self.input)

            # The raster datasets in the input workspace
            in_rasters = self.gp.ListRasters()

            #The first raster dataset in the list
            in_raster = in_rasters.next()

            while in_raster:
                try:
                    raster = os.path.join(self.input, in_raster)
                    in_raster = in_raster.split('.')[0]
                    outAsciiFile = '%s.asc' % os.path.basename(in_raster)
                    outAsciiFile  = os.path.join(self.output, outAsciiFile)

                    # Convert to ASCII
                    self.gp.RasterToASCII_conversion(raster, outAsciiFile)

                    # If the Copy/Convert was successful add a message
                    self.gp.AddMessage(msgConvSuccess % (in_raster))
                    in_raster = in_rasters.next()

                except Exception, ErrorDesc:
                    # Except block for the loop. If the tool fails to convert
                    # one of the Rasters, it will come into this block and add
                    # warnings to the messages, then proceed to attempt to
                    # convert the next input Raster.
                    WarningMessage = (msgConvFail + "%s" % (raster))

                    if self.gp.GetMessages(2) != "":
                        WarningMessage = WarningMessage + ". " + \
                                         (self.gp.GetMessages(2))
                    elif ErrorDesc != "":
                        WarningMessage = WarningMessage + (str(ErrorDesc))

                    # Add the message as a warning.
                    self.gp.AddWarning(WarningMessage)
                    in_raster = in_rasters.next()

        except Exception, ErrorDesc:
            # Except block if the tool could not run at all.
            # For example, not all parameters are provided, or if the output
            # path doesn't exist.
            self.gp.AddError(str(ErrorDesc))

if __name__ == '__main__':
    #input = r'H:\Data\tmp\TestGround\Raster'
    #output = r'H:\Data\tmp\TestGround\ASCII'
    #batch = BatchRasterToAscii(input=input, output=output)
    batch = ArcBatchRasterToAscii()
    batch.run()
