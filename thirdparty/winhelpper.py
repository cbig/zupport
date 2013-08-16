#!usr/var/env python
# coding=utf-8

import os, sys, time
import csv
#import xlrd
import fileinput
from types import IntType, StringType
#from yamltools import Yamlwrapper
#import ConversionUtils
from zupport.arcgis import get_geoprocessor, LicenseError
def print_timing(func):
    def wrapper(*arg, **kwargs):
        for i in range(1):
            t1 = time.time()
            func(*arg, **kwargs)
            t2 = time.time()
            elapsed = ''
            if t2 - t1 < 1.0:
                print t2 - t1
                elapsed =  '%0.1f ms' % ((t2 - t1) * 1000.0)
            elif t2 - t1 < 60.0:
                elapsed = '%0.1f s' % (t2 - t1)
            else:
                elapsed = '%s m %s s' % (int((t2 - t1) / 60), int((t2 - t1) % 60))
            print str(i + 1) + ': %s took %s' % (func.func_name, elapsed)
    return wrapper

class Archelper(object):
    '''Archelper class instantiates into a helper object for various
    geoprocessing tasks in ESRI ArcGIS environment.
    '''

    def __init__(self, parent=None, overwrite=False):
        # Try to create the Geoprocessor
        try:
            self.gp = get_geoprocessor()

            # Set available extents
            # !!! Southern (and eastern) extent is deliberately 100 m more south than most
            # southern MSNFI coordinate - MSNFI coordinates fixed left upper corner
            self.extents = {'north': '3243187.5 7255237.5 3628087.5 7779737.5',
                            'south': '3159087.5 6620112.5 3733087.5 7378212.5',
                            # whole & metso: added 200m for E for 300 m res
                            'whole': '3159087.5 6620037.5 3733287.5 7779537.5',
                            'metso': '3159087.5 6620037.5 3733287.5 7411537.5',
                            'local': '3514667.5 7284110.5 3614668.5 7384111.5',
                            'custom': '3139300.0 6611200.0 3753700.0 7788800.0',
                            'ESMK': '3459440.0 6782480.0 3642060.0 6951360.0'}

            # Set available input features
            self.infeats = ['Biotooppi_p', 'Lahopuu_p', 'Luonto_p', 'Pensasto_p',
                            'Toimenpide_ehdotus_p', 'Tuho_p']

            # Set cell counts restult file name
            self.cellresult = 'cell_counts.txt'

            # Set overwrite if necessary
            if overwrite:
                self.gp.OverwriteOutput = overwrite

        except LicenseError:
            # If ArcGIS is unavailable, delegate error message back
            if parent:
                parent.log("ArcGIS unavailable.")
                raise
            else:
                print "ArcGIS unavailable."


    @print_timing
    def batch_ASCII_to_GRID(self, wdir, fgdbase, extension='GRID'):
        '''Method for batch converting all ASCII grids in a target directory
        into ESRI grids in target file geodatabase. Most of the functionality
        is from ExportRasters.py in ArcToolbox/Scripts'''

        msgNonExist = "\nOutput location does not exist: "
        msgSuccess = "\nSuccessfully converted: "
        msgFail = "\nFailed to convert: "

        try:

            # Construct a list holding proper input raster names
            inRasters = []
            for raster in os.listdir(wdir):
                inRasters.append(os.path.join(wdir, raster))

            # The output workspace where the shapefiles are created
            outWorkspace = fgdbase

            ext = extension

            # Get proper extension based on the format string
            if (ext == "IMAGINE Image"):
                ext = ".img"
            elif (ext == "TIFF"):
                ext = ".tif"
            elif (ext == "BMP"):
                ext = ".bmp"
            elif (ext == "PNG"):
                ext = ".png"
            elif (ext == "JPEG"):
                ext = ".jpg"
            elif (ext == "JP2000"):
                ext = ".jp2"
            elif (ext == "GIF"):
                ext = ".gif"
            elif (ext == "GRID"):
                ext = ""

            # Error trapping, in case the output workspace doesn't exist
            if not ConversionUtils.gp.Exists(outWorkspace):
                raise Exception, msgNonExist + "%s" % (outWorkspace)

            # Loop through the list of input Rasters and convert/copy each to
            # the output geodatabase or folder
            for inRaster in inRasters:
                raster = inRaster
                try:
                    raster = ConversionUtils.ValidateInputRaster(raster)
                    outRaster = ConversionUtils.GenerateRasterName(raster, outWorkspace, ext)

                    # Copy/Convert the inRaster to the outRaster
                    ConversionUtils.CopyRasters(raster, outRaster, "")

                    # If the Copy/Convert was successfull add a message
                    print msgSuccess + "%s To %s" % (raster, outRaster)

                except Exception, ErrorDesc:
                    # Except block for the loop. If the tool fails to convert
                    # one of the Rasters, it will come into this block and add
                    # warnings to the messages, then proceed to attempt to
                    # convert the next input Raster.
                    WarningMessage = (msgFail + "%s" % (raster))

                    if ConversionUtils.gp.GetMessages(2) != "":
                        WarningMessage = WarningMessage + ". " + \
                                         (ConversionUtils.gp.GetMessages(2))
                    elif ErrorDesc != "":
                        WarningMessage = WarningMessage + (str(ErrorDesc))

                    # Add the message as a warning.
                    ConversionUtils.gp.AddWarning(WarningMessage)

        except Exception, ErrorDesc:
            # Except block if the tool could not run at all.
            # For example, not all parameters are provided, or if the output
            # path doesn't exist.
            ConversionUtils.gp.AddError(str(ErrorDesc))

    def batch_calculate_ppixel(self, sourceWorkpace, targetWorkspcae, value, count):
        pass

    def batch_change_nodata(self, sourceWorkspace, targetWorkspace, oldND,
                            newND, ext='GRID'):
        try:
            self.gp.workspace = sourceWorkspace
            self.gp.toolbox = "SP"

            # Check out any necessary licenses
            self.gp.CheckOutExtension("spatial")

            # Load required toolboxes...
            self.gp.AddToolbox(r"C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Spatial Analyst Tools.tbx")

            rasters = self.gp.ListRasters('', ext)
            raster = rasters.next()
            while raster:
                sys.stdout.write('Changing %s to %s in %s...' % (oldND, newND, raster))
                raster = os.path.join(sourceWorkspace, raster)
                inExpression = "con(%s == %s, %s, %s)" % (raster, oldND, newND, raster)
                outRaster = os.path.join(targetWorkspace, os.path.basename(raster))
                self.gp.SingleOutputMapAlgebra_sa(inExpression, outRaster)
                raster = rasters.next()

        except:
            print self.gp.GetMessages()

    def batch_change_nodata_header(self, path, stext, rtext):

        import glob, string

        print "finding: " + stext + " replacing with: " + rtext + " in: " + path + '...'

        path = os.path.join(path, "*.asc")
        files = glob.glob(path)

        for line in fileinput.input(files, inplace=1):
            lineno = 0
            lineno = string.find(line, stext)
            if lineno >0:
                line =line.replace(stext, rtext)
            sys.stdout.write(line)

        print 'Replacements done.'

    def batch_cross_select(self, first_workspace, second_workspace,
                           target_workspace, prefix, exc=[], ext='GRID'):
        try:
            self.gp.toolbox = "SP"
            # Check out any necessary licenses
            self.gp.CheckOutExtension("spatial")

            # Load required toolboxes...
            self.gp.AddToolbox(r"C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Spatial Analyst Tools.tbx")

            self.gp.workspace = first_workspace
            rasters1 = self.gp.ListRasters('', ext)
            raster1 = rasters1.next()

            # Although the order of workspaces does not matter the result,
            # it does affect the naming of result rasters
            while raster1:
                if raster1 in exc:
                    raster1 = rasters1.next()
                    continue
                raster1 = os.path.join(first_workspace, raster1)

                self.gp.workspace = second_workspace
                rasters2 = self.gp.ListRasters('', ext)
                raster2 = rasters2.next()

                while raster2:
                    sys.stdout.write('Crossing %s and %s...' % (os.path.basename(raster1),
                                                                os.path.basename(raster2)))
                    out_raster = os.path.join(target_workspace, '%s%s' %
                                              (os.path.basename(raster1),
                                               os.path.basename(raster2).replace(prefix, '')))
                    raster2 = os.path.join(second_workspace, raster2)
                    inExpression = "con(%s&%s, %s)" % (raster1, raster2, raster1)
                    self.gp.SingleOutputMapAlgebra_sa(inExpression, out_raster)
                    print 'done.'
                    raster2 = rasters2.next()
                raster1 = rasters1.next()
        except:
            print self.gp.GetMessages()

    def batch_define_projection(self, targetWorkspace):
        try:
            self.gp.workspace = targetWorkspace
            self.gp.toolbox = "management"
            coordsys = "C:/Program Files/ArcGIS/Coordinate Systems/Projected" +\
            " Coordinate Systems/National Grids/Finland Zone 3.prj"

            rasters = self.gp.ListRasters('', 'GRID')
            raster = rasters.next()
            while raster:
                self.gp.defineprojection(raster, coordsys)
                raster = rasters.next()

        except:
            print self.gp.GetMessages()

    @print_timing
    def batch_delete_empty(self, targetWorkspace):
        '''A method for deleting empty rasters (i.e. NullData only rasters.
        '''
        #try:
        # Check out any necessary licenses
        self.gp.CheckOutExtension("spatial")
        self.gp.toolbox = "SA"

        # Check whether input is legitimate
        if not os.path.exists(targetWorkspace):
            print 'Unknown %s: %s, exiting.' % targetWorkspace
            sys.exit(0)

        self.gp.workspace = targetWorkspace
        rasters = self.gp.ListRasters('', 'GRID')
        raster = rasters.next()
        while raster:
            # Check the maximum value of raster
            max = self.gp.GetRasterProperties_management(raster, 'MAXIMUM')
            if max < 0:
                sys.stdout.write('Raster %s empty, deleting...' % raster)
                self.gp.Delete_management(raster)
                print 'done.'

            raster = rasters.next()

        #except:
        #    print self.gp.GetMessages()


    @print_timing
    def batch_extract_by_attribute(self, sourceRaster, targetWs, field=None, preValue=None,
                                  reclass=False):
        '''A method for extracting categorical data based on value. Works through a
        workspace and extracts each specified value to a new raster. Can also reclassify
        extracted values to 1.
        '''

        # Check out any necessary licenses
        self.gp.CheckOutExtension("spatial")
        self.gp.toolbox = "SA"

        # Check whether input is legitimate
        if not os.path.exists(sourceRaster):
            print 'Unknown input raster: %s, exiting.' % sourceRaster
            sys.exit(0)

        # If a target field is specified, read in the values
        if field is None:
            print 'No field provided, exiting.'
            sys.exit(0)
        # If no specific value for a field is provided read in all
        fvalues = self.__get_field_values(field, preValue)

        current_value = 1

        try:
            # Loop through all given fields
            for value in fvalues.iterkeys():
                print 'Extracting raster %s with value %s (%s//%s)' % (field, value,
                                                                       current_value,
                                                                       len(fvalues))
                # Set local variables
                inWhereClause = '"VALUE" = %s' % value
                temp_field = 't%s' % field
                outRaster = self.__valid_raster_name(targetWs, temp_field, value)
                #outRaster = os.path.join(targetWs, '%s_%s' % (field, value))
                # Process: ExtractByAttributes
                self.gp.ExtractByAttributes_sa(sourceRaster, inWhereClause, outRaster)

                if reclass and value is not '1':
                    print 'Reclassifying raster %s value %s to 1' % (field, value)
                    # Do reclassification if reclass feature is selected
                    outRaster_rc = self.__valid_raster_name(targetWs, field, value)
                    rcRange = '%s %s 1' % (value, value)
                    self.gp.Reclassify_sa(outRaster, "VALUE", rcRange, outRaster_rc, "DATA")
                    print 'Building pyramids'
                    self.gp.BuildPyramids_management(outRaster_rc)
                    self.gp.Delete_management(outRaster)
                current_value += 1


        except:
            # Print error message if an error occurs
            print self.gp.GetMessages()

    @print_timing
    def batch_extract_by_mask(self, inputws, outputws, mask, extent='whole', prefix=''):
        '''Method for batch extracting data from target directory based on
        a mask feature (i.e. batch clipping).
        '''
        try:
            # Check out any necessary licenses
            self.gp.CheckOutExtension("spatial")
            self.gp.toolbox = "SA"

            # Check whether input is legitimate
            input = {'input': inputws, 'output': outputws}
            for key, item in input.iteritems():
                if not os.path.exists(item):
                    print 'Unknown %s: %s, exiting.' % (key, item)

            self.gp.Extent = self.extents[extent]

            self.gp.workspace = inputws
            rasters = self.gp.ListRasters()
            for raster in rasters:
                if raster is not os.path.basename(mask):
                    raster = os.path.join(inputws, raster)
                    outRaster = os.path.join(outputws, (prefix + os.path.basename(raster)))
                    print 'Extracting %s by %s...' % (raster, mask)
                    self.gp.ExtractByMask_sa(raster, mask, outRaster)
                    print 'Produced % s' % outRaster

        except:
            print self.gp.GetMessages()


    @print_timing
    def batch_extract_by_pixel(self, inputws, maskws, outputws, exclist=[]):
        '''Method for batch extracting data from target directory based on
        a positive pixels.
        '''

        nullvalue = -1
        try:
            # Check out any necessary licenses
            self.gp.CheckOutExtension("spatial")
            self.gp.toolbox = "SA"

            # Check whether input is legitimate
            input = {'input': inputws, 'maskws': maskws, 'output': outputws}
            for key, item in input.iteritems():
                if not os.path.exists(item):
                    print 'Unknown %s: %s, exiting.' % (key, item)

            self.gp.workspace = maskws
            masksall = self.gp.ListRasters()
            mask = masksall.next()
            masks = []
            while mask:
                masks.append(os.path.join(maskws, mask))
                mask = masksall.next()

            self.gp.workspace = inputws

            for mask in masks:
                rasters = self.gp.ListRasters()
                raster = rasters.next()
                while raster:
                    raster = os.path.join(inputws, raster)
                    if raster not in masks and raster not in exclist:
                        outRaster = os.path.join(outputws, '%s_%s' %
                                                 (os.path.basename(raster),
                                                  os.path.basename(mask)[3:]))
                        sys.stdout.write('Extracting %s by %s...' % (os.path.basename(raster),
                                                                     os.path.basename(mask)))
                        inExpression = "con(%s>0, %s, %s)" % (mask, raster, nullvalue)
                        self.gp.SingleOutputMapAlgebra_sa(inExpression, outRaster)
                        print 'done.'
                        print 'Produced %s' % outRaster
                        print
                    raster = rasters.next()

        except:
            print self.gp.GetMessages()


    @print_timing
    def batch_fix_nulldata(self, sourceWorkspace, targetWorkspace, 
                           ND='-1', setnodata=False, ext='GRID'):
        try:
            self.gp.workspace = sourceWorkspace
            self.gp.toolbox = "SP"

            # Check out any necessary licenses
            self.gp.CheckOutExtension("spatial")

            subdir = None
            if sourceWorkspace == targetWorkspace:
                subdir = os.path.join(targetWorkspace, 'ndsub')
                if not os.path.exists(subdir):
                    os.mkdir(subdir)
                targetWorkspace = subdir

            rasters = self.gp.ListRasters('', ext)
            for raster in rasters:
                sys.stdout.write('Fixing %s...' % raster)
                raster = os.path.join(sourceWorkspace, raster)
                
                if not setnodata:
                    inExpression = "con(IsNull(%s), %s, %s)" % (raster, ND, raster)
                else:
                    inExpression = "setnull(%s == %s, %s)" % (raster, ND, raster)
                
                outRaster = os.path.join(targetWorkspace, os.path.basename(raster))
                self.gp.SingleOutputMapAlgebra_sa(inExpression, outRaster)
                print 'done.'
                '''if subdir is not None:
                    sys.stdout.write('Moving file...')
                    self.gp.Delete_management(raster)
                    self.gp.copy_management(outRaster, raster)
                    print 'done.'
            if subdir is not None:
                os.rmdir(subdir)'''

        except:
            print self.gp.GetMessages(2)

    @print_timing
    def batch_GRID_to_ASCII(self, wdir, outWorkspace, ext='GRID'):

        msgNonExist = "\nOutput location does not exist: "
        msgSuccess = "\nSuccessfully converted: "
        msgFail = "\nFailed to convert: "
        self.gp.workspace = wdir

        try:

            # Error trapping, in case the output workspace doesn't exist
            if not ConversionUtils.gp.Exists(outWorkspace):
                raise Exception, msgNonExist + "%s" % (outWorkspace)

            # Get a list of grids in the workspace.
            rasters = self.gp.ListRasters()

            for raster in rasters:
                try:
                    #raster = ConversionUtils.ValidateInputRaster(raster)
                    raster = os.path.join(wdir, raster)
                    outAsciiFile = os.path.basename(raster)
                    outAsciiFile= outAsciiFile.replace('.tif', '.asc')
                    outAsciiFile  = os.path.join(outWorkspace, outAsciiFile)
                    print raster
                    print outAsciiFile

                    # Convert to ASCII
                    self.gp.RasterToASCII_conversion(raster, outAsciiFile)

                    # If the Copy/Convert was successfull add a message
                    print msgSuccess + "%s To %s" % (raster,  outAsciiFile)

                except Exception, ErrorDesc:
                    # Except block for the loop. If the tool fails to convert
                    # one of the Rasters, it will come into this block and add
                    # warnings to the messages, then proceed to attempt to
                    # convert the next input Raster.
                    WarningMessage = (msgFail + "%s" % (raster))

                    if ConversionUtils.gp.GetMessages(2) != "":
                        WarningMessage = WarningMessage + ". " + \
                                         (ConversionUtils.gp.GetMessages(2))
                    elif ErrorDesc != "":
                        WarningMessage = WarningMessage + (str(ErrorDesc))

                    # Add the message as a warning.
                    ConversionUtils.gp.AddWarning(WarningMessage)

        except Exception, ErrorDesc:
            # Except block if the tool could not run at all.
            # For example, not all parameters are provided, or if the output
            # path doesn't exist.
            ConversionUtils.gp.AddError(str(ErrorDesc))

    def batch_mosaic_raster(self, sourceWorkspace, targetRasterdataset, ext='GRID'):

        msgNonExist = "Output raster dataset does not exist: "
        msgSuccess = "Successfully added to mosaic: "
        msgFail = "Failed to mosaic: "

        # List of non-existent files
        non_ex_files = open(os.path.join(os.getcwd(), 'missing_files.txt'), 'w')

        try:

            # Error trapping, in case the output workspace doesn't exist
            if not ConversionUtils.gp.Exists(targetRasterdataset):
                raise Exception, msgNonExist + "%s" % (targetRasterdataset)

            self.gp.workspace = sourceWorkspace

            rasters = self.gp.ListRasters('', ext)
            raster = rasters.next()
            counter = 1
            while raster:
                try:
                    sys.stdout.write('%s Adding %s ...' % (counter, raster))
                    raster = os.path.join(sourceWorkspace, raster)
                    self.gp.Mosaic_management(raster, targetRasterdataset, "LAST","MATCH", "0", "#", "NONE", "0")
                    print 'done.'
                    print msgSuccess + "%s to %s" % (raster,  targetRasterdataset)
                    counter += 1
                    raster = rasters.next()
                    #if counter == 2:
                    #    break
                except Exception, ErrorDesc:
                    # Except block for the loop. If the tool fails to convert
                    # one of the Rasters, it will come into this block and add
                    # warnings to the messages, then proceed to attempt to
                    # convert the next input Raster.
                    WarningMessage = (msgFail + "%s" % (raster))

                    if ConversionUtils.gp.GetMessages(2) != "":
                        WarningMessage = WarningMessage + ". " + \
                                         (ConversionUtils.gp.GetMessages(2))
                    elif ErrorDesc != "":
                        WarningMessage = WarningMessage + (str(ErrorDesc))

                    # Add the message as a warning.
                    ConversionUtils.gp.AddWarning(WarningMessage)
                    # Write to the non-existent files-file
                    non_ex_files.write(raster + '\n')
                    raster = rasters.next()
            non_ex_files.close()

        except Exception, ErrorDesc:
            # Except block if the tool could not run at all.
            # For example, not all parameters are provided, or if the output
            # path doesn't exist.
            ConversionUtils.gp.AddError(str(ErrorDesc))

    @print_timing
    def batch_multiply_rasters(self, sourceWorkspace, targetWorkspace, multiplier, ext='GRID'):
        try:
            self.gp.workspace = sourceWorkspace
            self.gp.toolbox = "SP"

            # Check out any necessary licenses
            self.gp.CheckOutExtension("spatial")

            # Load required toolboxes...
            self.gp.AddToolbox(r"C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Spatial Analyst Tools.tbx")

            rasters = self.gp.ListRasters('', ext)
            raster = rasters.next()
            while raster:

                sys.stdout.write('%s Multiplying %s with %s...' % (raster, os.path.basename(multiplier)))
                raster = os.path.join(sourceWorkspace, raster)
                outRaster = os.path.join(targetWorkspace, os.path.basename(raster))
                self.gp.Times_sa(raster, multiplier, outRaster)
                print 'done.'
                raster = rasters.next()
        except:
            print self.gp.GetMessages()

    @print_timing
    def batch_set_nodata(self, sourceWorkspace, targetWorkspace, orgv=0, newv=-1, ext='GRID'):
        try:
            self.gp.workspace = sourceWorkspace
            self.gp.toolbox = "SP"

            # Check out any necessary licenses
            self.gp.CheckOutExtension("spatial")

            # Load required toolboxes...
            self.gp.AddToolbox(r"C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Spatial Analyst Tools.tbx")

            rasters = self.gp.ListRasters('', ext)
            raster = rasters.next()
            while raster:
                raster = os.path.join(sourceWorkspace, raster)
                inExpression = "con(%s == %s, %s, %s)" % (raster, orgv, newv, raster)
                outRaster = os.path.join(targetWorkspace, os.path.basename(raster))
                self.gp.SingleOutputMapAlgebra_sa(inExpression, outRaster)
                raster = rasters.next()

        except:
            print self.gp.GetMessages()

    def batch_sum_rasters(self, first_workspace, second_workspace,
                          target_workspace, ext='GRID'):
        try:
            self.gp.toolbox = "SP"
            # Check out any necessary licenses
            self.gp.CheckOutExtension("spatial")

            # Load required toolboxes...
            self.gp.AddToolbox(r"C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Spatial Analyst Tools.tbx")

            self.gp.workspace = second_workspace
            rasters2 = self.gp.ListRasters('', ext)
            raster2 = rasters2.next()

            # Set 1 needs to be the more incusive one! (Needs to contain at least
            # same rasters as set 2
            while raster2:
                self.gp.workspace = first_workspace
                rasters1 = self.gp.ListRasters('', ext)
                raster1 = rasters1.next()
                while raster1:
                    if raster1 == raster2:
                        sys.stdout.write('Adding %s and %s...' % (os.path.basename(raster1),
                                                                  os.path.basename(raster2)))
                        raster1 = os.path.join(first_workspace, raster1)
                        raster2 = os.path.join(second_workspace, raster2)
                        temp = os.path.join(target_workspace,
                                                  "temp")
                        out_raster = os.path.join(target_workspace,
                                                  os.path.basename(raster1))
                        self.gp.Plus_sa(raster1, raster2, out_raster)
                        #self.gp.Plus_sa(temp, 1, out_raster)
                        #self.gp.Delete_management(temp)
                        print 'done.'
                        break
                    raster1 = rasters1.next()
                raster2 = rasters2.next()
        except:
            print self.gp.GetMessages()

    def calculate_cell_counts(self, sourceWorkspace):

        sys.stdout.write('\n Calculating cell counts...')
        self.gp.workspace = sourceWorkspace

        outFile = open(os.path.join(sourceWorkspace, self.cellresult), 'w')

        rasters = self.gp.ListRasters()
        raster = rasters.next()

        i = 1
        valueField = 'VALUE'
        countField = 'COUNT'
        columnMsg = "%10s  %15s"

        while raster:

            rasterPath = self.gp.workspace + "\\" + raster

            msgpath = '\n%s\n' % rasterPath
            #self.gp.addmessage()
            #print msg
            #outFile.write(msg + '\n')

            try:
                rows = self.gp.searchcursor(rasterPath)
            except:
                self.gp.CalculateStatistics_management(rasterPath)
                try:
                    rows = self.gp.searchcursor(rasterPath)
                except:
                    print '%s is not an integer grid, skipping.' % rasterPath
                    raster = rasters.next()
                    continue

            row = rows.next()

            msgheader = columnMsg %(valueField, countField)
            outFile.write('%s%s\n' % (msgpath, msgheader))
            #print msg
            #self.gp.addmessage(msg)
            #outFile.write(msg + '\n')

            while row:
                msg = columnMsg %(row.getvalue(valueField), row.getvalue(countField))
                #print msg
                #self.gp.addmessage(msg)
                outFile.write('%s\n' % msg)

                row = rows.next()
            raster = rasters.next()
        outFile.close()
        print 'created cell statistics for: %s' % sourceWorkspace

    def calculate_cell_ratios(self, rasterA, rasterB):
        '''Calculates simple above 0 valued cell ratios for two
        rasters.
        '''
        count_fileA = os.path.join(os.path.dirname(rasterA), self.cellresult)
        count_fileB = os.path.join(os.path.dirname(rasterB), self.cellresult)
        for file in (count_fileA, count_fileB):
            if not os.path.exists(file):
                self.calculate_cell_counts(os.path.dirname(file))

        linesA = open(count_fileA, 'r').readlines()
        linesB = open(count_fileB, 'r').readlines()

        sumA = float(self.__get_count_sum(rasterA, linesA))
        sumB = float(self.__get_count_sum(rasterB, linesB))
        try:
            ratio = sumB / sumA
        except ZeroDivisionError:
            ratio = 0.0

        return ratio

    @print_timing
    def convert_raster_extent(self, sourcefeat, outWs, field=None, extent='whole'):
        #snapRaster
        self.gp.workspace = r'E:\Data\Metsahallitus\AnalysisLayers\Source\Kuviot25'
        self.gp.toolbox = "conversion"
        self.gp.Extent = self.extents[extent]
        print "Using extent: %s(%s)" % (extent, self.extents[extent])

        fvalues = self.__get_field_values(os.path.basename(sourcefeat), field)

        try:
            # Loop through all given fields
            for value in fvalues.iterkeys():
                # Set local variables
                inField = value
                inCellSize= "25"
                outRaster = self.__valid_raster_name(outWs, inField, inCellSize)

                # Process: FeatureToRaster_conversion
                print "Converting feature: %s" % value
                self.gp.FeatureToRaster_conversion(sourcefeat, inField, outRaster, inCellSize)
                print "Building pyramids..."
                self.gp.BuildPyramids_management(outRaster)

        except:
            # Print error message if an error occurs
            print self.gp.GetMessages()

    @print_timing
    def pca_selection(self, workspace, xlfile, xlsheet,
                      xlcolumn={'dir':'Dirpath', 'file':'Filename'}):
        '''A function to perform a Principal Component Analysis (PCA) on
        set of selected rasters defined in an Excel file.
        '''

        try:
            self.gp.workspace = workspace
            self.gp.toolbox = "SP"
            print 'Target workspace: %s' % workspace

            # Check out any necessary licenses
            self.gp.CheckOutExtension("spatial")

            # Load required toolboxes...
            self.gp.AddToolbox(r"C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Spatial Analyst Tools.tbx")

            # Read in the Excel file
            xl = Readexcel(xlfile)
            dirlist = xl.getcol(xlsheet, xlcolumn['dir'])
            filelist = xl.getcol(xlsheet, xlcolumn['file'])
            # Create a string holding all the input files
            pathlist = ''
            pathlist = pathlist.join([(os.path.join(dir, file) + '; ')
                                      for dir, file in zip(dirlist, filelist)])
            # Trim away the trailing semicolon and white space
            pathlist = pathlist[:-2]
            outraster = 'pca_out'
            no_comps = 5
            outparams = 'pca_params.asc'

            # Perform the PCA on selected rasters
            self.gp.PrincipalComponents_sa(pathlist, outraster, no_comps, outparams)
            print 'Done.'

        except:
            print self.gp.GetMessages()

    @print_timing
    def set_nodata_aggregation(self, sourceWorkspace, targetWorkspace,
                               cellfactor,
                               cellsize,
                               ndmode=False,
                               nd=-1,
                               extent=None,
                               mask=None,
                               include=[],
                               nameimp='',
                               fileext='img'):

        try:
            # Check out any necessary licenses
            self.gp.CheckOutExtension("spatial")

            # Load required toolboxes...
            #self.gp.AddToolbox(r"C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Spatial Analyst Tools.tbx")
            self.gp.workspace = sourceWorkspace
            #self.gp.toolbox = "SP"

            if extent is not None:
                self.gp.Extent = self.extents[extent]
                print 'Using extent: %s (%s)' % (extent, self.extents[extent])

            if mask is not None:
                self.gp.Mask = mask
                print 'Using mask: %s' % mask

            # Create local variables
            org_agg = os.path.join(targetWorkspace, "org_agg")
            nodata = os.path.join(targetWorkspace, "nodata")
            nodata_agg = os.path.join(targetWorkspace, "nodata_agg")

            # Nodata value used in the final ASCII grid
            ND = nd
            # Cell factor for aggregation
            cell_f = cellfactor
            print "Cell factor: %s" % cell_f

            rasters = self.gp.ListRasters()

            for raster in rasters:
                if include != [] and raster not in include:
                    continue
                else:
                    sys.stdout.write("Aggregating raster: %s " % raster)
                    if nameimp != '':
                        presc = True
                    else:
                        presc = False

                    ## TODO: HACK! Modified for Anni's data aggregation. Uncomment
                    ## the first two outRaster to go to default

                    #outRaster = self.__valid_grid_name(raster, pres=presc,
                    #                                   strip=nameimp, sep='_')
                    outRaster = raster.split('.')
                    meter_res = '_' + str(cellsize * cellfactor)
                    if not fileext:
                        fileext = outRaster[1]
                    outRaster = outRaster[0] + meter_res + '.' + fileext
                    outRaster = os.path.join(targetWorkspace, outRaster)

                    sys.stdout.write("into %s..." % outRaster)

                    # Aggregate the original grid to desired resolution
                    # If nd = 0 go no further
                    if not ndmode and nd == 0:
                        self.gp.Aggregate_sa(raster, outRaster, cell_f, "SUM", "EXPAND", "DATA")
                        print ' done'
                        sys.stdout.write('Building pyramids...')
                        self.gp.BuildPyramids_management(outRaster)
                        print ' done'
                        continue
                    else:
                        self.gp.Aggregate_sa(raster, org_agg, cell_f, "SUM", "EXPAND", "DATA")

                    # Create a NoData -> -1 version from the original grid
                    inExpression = "con(IsNull(%s), %s, %s)" % (raster, ND, raster)
                    self.gp.SingleOutputMapAlgebra_sa(inExpression, nodata)

                    # Aggregate -1 -nodata version to desired resolution
                    self.gp.Aggregate_sa(nodata, nodata_agg, cell_f, "SUM", "EXPAND", "DATA")

                    # Create finished grid:
                    #   if -1 -version aggregate has a value equal to all cells
                    #   being -1 -> true NoData, assign ND value
                    #   else -> only part of the original cells are NoData, assign
                    #   true value from original aggregate

                    nd_target = cell_f ** 2 * ND
                    # Version 1: create raster with nodata = -1
                    # Version 2: create raster with nodata = NoData
                    if not ndmode:
                        inExpression = "con(%s > %s, %s)" % (nodata_agg, nd_target, org_agg)
                        self.gp.SingleOutputMapAlgebra_sa(inExpression, outRaster)
                    else:
                        inExpression = "con(%s == %s, %s, %s)" % (nodata_agg, nd_target, ND, org_agg)
                        self.gp.SingleOutputMapAlgebra_sa(inExpression, outRaster)

                    print ' done'
                    sys.stdout.write('Building pyramids...')
                    self.gp.BuildPyramids_management(outRaster)
                    print ' done'

                    # Finally delete temporary layers
                    self.gp.Delete_management(org_agg)
                    self.gp.Delete_management(nodata)
                    self.gp.Delete_management(nodata_agg)

        except:
            print self.gp.GetMessages()
    # General helper methods

    def __get_count_sum(self, raster, lines):
        sum = 0
        for i, line in enumerate(lines):
            if line == '%s\n' % raster:
                start = i
                for line in lines[start+2:]:
                    if line == '\n' or len(line) < 2:
                        break
                    values = line.split()
                    try:
                        if int(values[0]) > 0:
                            sum = sum + int(values[1])
                    except ValueError:
                        continue
                break
        return sum

    def __get_field_values(self, target, value=None):
        """This methodreads in a csv file containing unique values of target
        in a specified directory and returns a dictionary with unique values as keys
        and value names as dictionary values.
        """

        # Directory for fields is hardocoded
        infile = os.path.join('E:\Data\Metsahallitus\ArcGIS\Geodatabases\FieldLoaders',
                              '%s.csv' % target)
        try:
            # Read in the csv-file and convert it to a dictionary
            values = dict(csv.reader(open(infile), delimiter=';'))

            # If a specific value is given return only that else everything
            if value:
                return {str(value): values[str(value)]}
            else:
                return values

        except IOError:
            print 'No input file describing target values.'
            return None

    def __valid_grid_name(self, raster, pres, strip, sep):
        if len(raster) > 12 and pres:
            raster = raster.replace(strip, '')
            i = 1
            while (len(raster) + len(strip)) > 12:
                raster = '_'.join(short[:-1] for short in raster.split(sep))
                i += 1

            raster = '%s%s' % (strip, raster)
        elif len(raster) > 12:
            raster = raster.replace(strip, '')
            i = 1
            while len(raster) > 12:
                raster = '_'.join(short[:-i] for short in raster.split(sep))
                i += 1

        return raster

    def __valid_raster_name(self, outws, infield, cellsize):
        if (len(infield) + len(cellsize)) > 12:
            sub = '_int'
            if sub in infield.lower():
                infield = ''.join(infield.lower().split(sub))
            toolong = True
            away = 0
            if (len(infield) + len(cellsize)) > 12:
                while toolong:
                    away = away - 1
                    sub = '_'
                    if sub in infield.lower():
                        temp = ''.join(syl[:away] for syl in infield.split(sub))
                        if (len(temp) + len(cellsize) <= 12):
                            infield = temp
                            toolong = False
                    else:
                        temp = infield[:away]
                        if (len(temp) + len(cellsize) <= 12):
                            infield = temp
                            toolong = False

        infield = '%s%s' % (infield, cellsize)

        return os.path.join(outws, infield)

class Readexcel(object):
    """ Simple OS Independent Class for Extracting Data from Excel Files
        the using xlrd module found at http://www.lexicon.net/sjmachin/xlrd.htm

        Versions of Excel supported: 2004, 2002, XP, 2000, 97, 95, 5, 4, 3
        xlrd version tested: 0.5.2

        Data is extracted by creating a iterator object which can be used to
        return data one row at a time. The default extraction method assumes
        that the worksheet is in tabular format with the first nonblank row
        containing variable names and all subsequent rows containing values.
        This method returns a dictionary which uses the variables names as keys
        for each piece of data in the row.  Data can also be extracted with
        each row represented by a list.

        Extracted data is represented fairly logically. By default dates are
        returned as strings in "yyyy/mm/dd" format or "yyyy/mm/dd hh:mm:ss",
        as appropriate.  However, dates can be return as a tuple containing
        (Year, Month, Day, Hour, Min, Second) which is appropriate for usage
        with mxDateTime or DateTime.  Numbers are returned as either INT or
        FLOAT, whichever is needed to support the data.  Text, booleans, and
        error codes are also returned as appropriate representations.

        Quick Example:
        xl = readexcel('testdata.xls')
        sheetnames = xl.worksheets()
        for sheet in sheetnames:
            print sheet
            for row in xl.getiter(sheet):
                # Do Something here
        """
    def __init__(self, filename):
        """ Returns a readexcel object of the specified filename - this may
        take a little while because the file must be parsed into memory """
        if not os.path.isfile(filename):
            raise NameError, "%s is not a valid filename" % filename
        self.__filename__ = filename
        self.__book__ = xlrd.open_workbook(filename)
        self.__sheets__ = {}
        self.__sheetnames__ = []
        for i in self.__book__.sheet_names():
            uniquevars = []
            firstrow = 0
            sheet = self.__book__.sheet_by_name(i)
            for row in range(sheet.nrows):
                types, values = sheet.row_types(row), sheet.row_values(row)
                nonblank = False
                for j in values:
                    if j != '':
                        nonblank=True
                        break
                if nonblank:
                    # Generate a listing of Unique Variable Names for Use as
                    # Dictionary Keys In Extraction. Duplicate Names will
                    # be replaced with "F#"
                    variables = self.__formatrow__(types, values, False)
                    unknown = 1
                    while variables:
                        var = variables.pop(0)
                        if var in uniquevars or var == '':
                            var = 'F' + str(unknown)
                            unknown += 1
                        uniquevars.append(str(var))
                    firstrow = row + 1
                    break
            self.__sheetnames__.append(i)
            self.__sheets__.setdefault(i, {}).__setitem__('rows', sheet.nrows)
            self.__sheets__.setdefault(i,{}).__setitem__('cols', sheet.ncols)
            self.__sheets__.setdefault(i,{}).__setitem__('firstrow', firstrow)
            self.__sheets__.setdefault(i,{}).__setitem__('variables', uniquevars[:])

    def getcol(self, sheetname, col):
        """Return the content of a single column as a list. Parameter col can
        be either a string (column name) or an integer (column index). Returns
        column values without the column header.
        """
        if sheetname not in self.__sheets__.keys():
            raise NameError, "%s is not present in %s" % (sheetname,\
                                                          self.__filename__)

        if type(col) is StringType:
            if col not in self.variables(sheetname):
                raise NameError, "%s is not present in %s" % (col, sheetname)
            else:
                index = self.variables(sheetname).index(col)
                values = self.__book__.sheet_by_name(sheetname).col_values(index)
                return values[1:]
        if type(col) is IntType:
            if col < 0 or col > self.ncols(sheetname):
                raise IndexError, "Column index %s does not exist for %s" % \
                                                            (col, sheetname)
            else:
                values = self.__book__.sheet_by_name(sheetname).col_values(col)
                return values[1:]

    def getiter(self, sheetname, returnlist=False, returntupledate=False):
        """ Return an generator object which yields the lines of a worksheet;
        Default returns a dictionary, specifing returnlist=True causes lists
        to be returned.  Calling returntupledate=True causes dates to returned
        as tuples of (Year, Month, Day, Hour, Min, Second) instead of as a
        string """
        if sheetname not in self.__sheets__.keys():
            raise NameError, "%s is not present in %s" % (sheetname,\
                                                          self.__filename__)
        if returnlist:
            return __iterlist__(self, sheetname, returntupledate)
        else:
            return __iterdict__(self, sheetname, returntupledate)

    def worksheets(self):
        """ Returns a list of the Worksheets in the Excel File """
        return self.__sheetnames__

    def nrows(self, worksheet):
        """ Return the number of rows in a worksheet """
        return self.__sheets__[worksheet]['rows']

    def ncols(self, worksheet):
        """ Return the number of columns in a worksheet """
        return self.__sheets__[worksheet]['cols']

    def variables(self, worksheet):
        """ Returns a list of Column Names in the file,
            assuming a tabular format of course. """
        return self.__sheets__[worksheet]['variables']

    def __formatrow__(self, types, values, wanttupledate):
        """ Internal function used to clean up the incoming excel data """
        ##  Data Type Codes:
        ##  EMPTY 0
        ##  TEXT 1 a Unicode string
        ##  NUMBER 2 float
        ##  DATE 3 float
        ##  BOOLEAN 4 int; 1 means TRUE, 0 means FALSE
        ##  ERROR 5
        returnrow = []
        for i in range(len(types)):
            type,value = types[i],values[i]
            if type == 2:
                if value == int(value):
                    value = int(value)
            elif type == 3:
                datetuple = xlrd.xldate_as_tuple(value, self.__book__.datemode)
                if wanttupledate:
                    value = datetuple
                else:
                    # time only no date component
                    if datetuple[0] == 0 and datetuple[1] == 0 and \
                       datetuple[2] == 0:
                        value = "%02d:%02d:%02d" % datetuple[3:]
                    # date only, no time
                    elif datetuple[3] == 0 and datetuple[4] == 0 and \
                         datetuple[5] == 0:
                        value = "%04d/%02d/%02d" % datetuple[:3]
                    else: # full date
                        value = "%04d/%02d/%02d %02d:%02d:%02d" % datetuple
            elif type == 5:
                value = xlrd.error_text_from_code[value]
            returnrow.append(value)
        return returnrow

def __iterlist__(excel, sheetname, tupledate):
    """ Function Used To Create the List Iterator """
    sheet = excel.__book__.sheet_by_name(sheetname)
    for row in range(excel.__sheets__[sheetname]['rows']):
        types, values = sheet.row_types(row), sheet.row_values(row)
        yield excel.__formatrow__(types, values, tupledate)

def __iterdict__(excel, sheetname, tupledate):
    """ Function Used To Create the Dictionary Iterator """
    sheet = excel.__book__.sheet_by_name(sheetname)
    for row in range(excel.__sheets__[sheetname]['firstrow'],\
                     excel.__sheets__[sheetname]['rows']):
        types, values = sheet.row_types(row), sheet.row_values(row)
        formattedrow = excel.__formatrow__(types, values, tupledate)
        # Pad a Short Row With Blanks if Needed
        for i in range(len(formattedrow),\
                       len(excel.__sheets__[sheetname]['variables'])):
            formattedrow.append('')
        yield dict(zip(excel.__sheets__[sheetname]['variables'], formattedrow))

if __name__ == '__main__':
    arc = Archelper(overwrite=True)
    #arc.batch_ASCII_to_GRID(r'E:\Data\Metla\ProcessedGrids\ASCII\sub',
    #                        r'E:\Data\Metla\temp.gdb')
    #arc.batch_define_projection(r'E:\Data\Metla\MSNFI_grids100m.gdb')
    '''
    attributes = ['NAT_TYYPPI2_INT']

    for attribute in attributes:
        arc.convert_raster_extent(r'E:\Data\Metsahallitus\ArcGIS\Geodatabases\Luontotyypit_metso.gdb\Biotooppi_metso\Biotooppi_m',
                                  r'E:\Data\Metsahallitus\AnalysisLayers\Source\Metso\Metsatalousmaa\Biotooppi25',
                                  field=attribute,
                                  extent='metso')
    '''
    #arc.convert_raster_extent(r'E:\Data\Metsahallitus\ArcGIS\Geodatabases\Luontotyypit.gdb\Metsahallitus\MH_alue',
    #                          r'E:\Data\Metsahallitus\AnalysisLayers\Source\Fin\Metsatalousmaa',
    #                          field='PALSTANRO',
    #                          extent='whole')

    #arc.batch_extract_by_mask(r'E:\Data\Metsahallitus\AnalysisLayers\Target\Fin',
    #                          r'E:\Data\Metsahallitus\AnalysisLayers\Target\Metso_nd',
    #                          r'E:\Data\Metso\MetsoII.gdb\Alue\Metso_extent',
    #                          extent='metso')
    #arc.batch_extract_by_mask('E:\Data\Metsahallitus\AnalysisLayers\Target\Fin',
    #                          'E:\Data\Metsahallitus\AnalysisLayers\Target\Metso_nd',
    #                          'E:\Data\Metso\MetsoII.gdb\Alue\Metso_extent',
    #                          extent='metso')
#    maskdir = r'C:\Data\Staging\Output\ESMK_metsavara\kasvupaikat'
#    arc.gp.workspace = maskdir
#    masks = arc.gp.ListRasters()
#    masks = [os.path.join(maskdir, mask) for mask in masks]
#    for i, mask in enumerate(masks):
#        arc.batch_extract_by_mask('C:\Data\Staging\Output\ESMK_metsavara\merge',
#                                  'C:\Data\Staging\Output\ESMK_metsavara\merge\ind_kp',
#                                  mask,
#                                  extent='ESMK',
#                                  prefix='kp%s_' % (i+1))
    #arc.batch_GRID_to_ASCII(r'C:\Users\jlehtoma\Documents\EclipseWorkspace\Framework\trunk\framework\zonation\real_input',
    #                        r'C:\Users\jlehtoma\Documents\EclipseWorkspace\Framework\trunk\framework\zonation\real_input\ASCII',
    #                        ext='TIFF')
    #arc.batch_GRID_to_ASCII(r'E:\Data\Metla\AnalysisLayers\Target\Fin\Metsatalousmaa\sr_kpsp',
    #                        r'E:\Data\Zonation\input_mt\Fin\Metsatalousmaa')
    #inc = []

    #inc = ['in_koivu_kuiva']
    extent = 'whole'
    #mask = r'E:\Data\Metso\MetsoII.gdb\Alue\Metso_extent'

    # Set the workspace
    in_workspace = r'H:\GRADU\LTI2010\Rasterit_LTI2010\Suo'
    out_workspace = r'H:\GRADU\LTI2010\Rasterit_LTI2010\IMGt'

    # Following cell factors are set
    # 500m = 5
    # 1km  = 10
    # 5km  = 50
    # 10km = 100
    # 50km = 500
    resolutions = [8]
    for resolution in resolutions:
        arc.set_nodata_aggregation(in_workspace,
                                   out_workspace,
                                   cellfactor=resolution,
                                   cellsize=25,
                                   extent=extent,
                                   #mask=mask,
                                   #nameimp='in_',
                                   #include=inc
                                   fileext='img'
                                   )
    '''arc.set_nodata_aggregation(r'E:\Data\Metla\MSNFI_grids100m_calcs_sr_kpsp.gdb',
                               r'E:\Data\Metla\AnalysisLayers\Target\Fin\Metsatalousmaa\sr_kpsp',
                               cellfactor=5,
                               ndmode=True,
                               extent='whole',
                               nameimp='sr_')'''
    #values = arc.__get_field_values('Biotooppi_p', 'ARV_TAPA')
    #print values
    #arc.batch_extract_by_attribute(r'E:\Data\Metsahallitus\AnalysisLayers\Source\Fin\Metsatalousmaa\Biotooppi25\nat_tyyppi225',
    #                               r'E:\Data\Metsahallitus\AnalysisLayers\Source\Fin\Metsatalousmaa\Biotooppi25\nat_tyyppi225sub',
    #                               field='NAT_TYYPPI2', preValue=None, reclass=True)
    #exclist = [r'E:\Data\Metla\MSNFI_grids100m_calcs_in_kp.gdb\in_all',
    #           r'E:\Data\Metla\MSNFI_grids100m_calcs_sr_kp.gdb\sr_ika']
    #arc.batch_extract_by_pixel(r'E:\Data\Metla\MSNFI_grids100m_calcs_in_sp.gdb',
    #                           r'E:\Data\Metla\MSNFI_grids100m_calcs_in_kp.gdb',
    #                           r'E:\Data\Metla\MSNFI_grids100m_calcs_in_kpsp.gdb',
    #                           exclist)
    #arc.batch_extract_by_pixel(r'E:\Data\Metla\MSNFI_grids100m_calcs_sr_sp.gdb',
    #                           r'E:\Data\Metla\MSNFI_grids100m_calcs_sr_kp.gdb',
    #                           r'E:\Data\Metla\MSNFI_grids100m_calcs_sr_kpsp.gdb',
    #                           exclist)
    #arc.batch_set_nodata('E:\Data\Metsa hallitus\AnalysisLayers\Target\Metso500',
    #                     'E:\Data\Metsahallitus\AnalysisLayers\Target\Metso500ND',
    #                     -9999, -1)
    #arc.batch_fix_nulldata(r'E:\Data\ESMK_testi\data\tiff',
    #                       r'E:\Data\ESMK_testi\data\tiff',
    #                       ND=0, 
    #                       setnodata=True,
    #                       ext='tif')
    #xl = Readexcel('E:\Data\Zonation\ConfigureData.xls')
    #sheet = 'Selected300608'
    #print xl.getcol(sheet, 'Filename')
    #print xl.getcol(sheet, 3)
    #print xl.variables(sheet)

    #arc.pca_selection(r'E:\Data\Scratch',
    #              r'E:\Data\Zonation\ConfigureData.xls',
    #              'Selected_mtm_full_small')
    #arc.batch_delete_empty(r'E:\Data\Metsahallitus\AnalysisLayers\Metsatalousmaa\Target_mtm_local\Biotooppi100loc\invent_lk100subloc')
    #arc.calculate_cell_counts('E:\Data\Metla\AnalysisLayers\Source\Local\Metsatalousmaa\\100m')
    #rat = arc.calculate_cell_ratios('E:\Data\Metla\AnalysisLayers\Source\Kokomaa\Metsatalousmaa\\100m\kpkuiva',
    #                                'E:\Data\Metla\AnalysisLayers\Source\Local\Metsatalousmaa\\100m\kpkuiva')
    #print 'Ratio: %10.3f' % rat
    #arc.batch_multiply_rasters(r'E:\Data\Metsahallitus\AnalysisLayers\Source\Fin\Metsatalousmaa\Biotooppi25\nat_tyyppi125sub',
    #                           r'E:\Data\Metsahallitus\AnalysisLayers\Source\Fin\Metsatalousmaa\Biotooppi25\nat_tyyppi125sub\nat_tyyppi125sub_edust',
    #                           r'E:\Data\Metsahallitus\AnalysisLayers\Source\Fin\Metsatalousmaa\Biotooppi25\nat_edust125r')
    #arc.batch_multiply_rasters(r'E:\Data\Metsahallitus\AnalysisLayers\Source\Fin\Metsatalousmaa\Biotooppi25\nat_tyyppi125sub',
    #                           r'E:\Data\Metsahallitus\AnalysisLayers\Source\Fin\Metsatalousmaa\Biotooppi25\nat_yhd1',
    #                           r'E:\Data\Metsahallitus\AnalysisLayers\Source\Fin\Metsatalousmaa\Biotooppi25\nat_edust125r')
    #arc.batch_multiply_rasters(r'E:\Data\Metsahallitus\AnalysisLayers\Source\Fin\Metsatalousmaa\Biotooppi25\nat_tyyppi225sub',
    #                           r'E:\Data\Metsahallitus\AnalysisLayers\Source\Fin\Metsatalousmaa\Biotooppi25\nat_yhd2',
    #                           r'E:\Data\Metsahallitus\AnalysisLayers\Source\Fin\Metsatalousmaa\Biotooppi25\nat_edust225r')
    #arc.batch_sum_rasters(r'E:\Data\Metsahallitus\AnalysisLayers\Target\Fin\Metsatalousmaa\Biotooppi500\nat_yhd1',
    #                      r'E:\Data\Metsahallitus\AnalysisLayers\Target\Fin\Metsatalousmaa\Biotooppi500\nat_yhd2',
    #                      r'E:\Data\Metsahallitus\AnalysisLayers\Target\Fin\Metsatalousmaa\Biotooppi500\nat_kooste')
    #arc.batch_change_nodata(r'',
    #                        r'',
    #                        oldND='0',
    #                        newND='-1')
    #arc.batch_cross_select(r'E:\Data\Metla\MSNFI_grids100m_calcs_sr_sp.gdb',
    #                       r'E:\Data\Metla\MSNFI_grids100m_calcs_sr_kp.gdb',
    #                       r'E:\Data\Metla\MSNFI_grids100m_calcs_sr_kpsp.gdb',
    #                       prefix='sr')
    #exc = ['in_koivu', 'in_kuusi', 'in_manty']
    #arc.batch_cross_select(r'E:\Data\Metla\MSNFI_grids100m_calcs_in_sp.gdb',
    #                       r'E:\Data\Metla\MSNFI_grids100m_calcs_in_kp.gdb',
    #                      r'E:\Data\Metla\MSNFI_grids100m_calcs_in_kpsp.gdb',
    #                      prefix='in', exc=exc)
    #sourceWorkspace = r'C:\Data\Metsakeskukset\Etela-Savo\Peruskartta\Karttalehdet'
    #targetRasterdataset = r'C:\Data\Metsakeskukset\Etela-Savo\Peruskartta\PK_ES.gdb\Peruskarttalehdet'
    #arc.batch_mosaic_raster(sourceWorkspace, targetRasterdataset, 'tif')