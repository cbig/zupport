#!/usr/bin/python
# coding=utf-8

###############################################################################
# Customized version of ArcGIS ConversionUtils

"""*****************************************************************************
ConversionUtils.py
Version: ArcGIS 9.0

Description: This module provides functions and the geoprocessor which is used
by both the FeatureclassConversion.py and TableConversion.py modules.

Requirements: Python 2.5

Author: ESRI, Redlands

Date Created: Jan 28 2004
Updated: Sep 19, 2007
            - modified create() as arcgisscripting.create(9.3)
*****************************************************************************"""

import copy
import os

from zupport.zlogging import Logger

def get_geoprocessor(version):
    try:
        if version == 9.3:
            # Try importing arcgisscripting, will fail if ArcGIS not present
            # Raise the exception if not present
            
            import arcgisscripting
            return arcgisscripting.create(version)
        elif version == 10:
            import arcpy
            return arcpy
    except ImportError, e:
        raise e

#Define message constants so they may be translated easily
msgErrorGenOutput = "Problem generating Output Name"
msgErrorGenOutputRaster = "Problem generating Output Raster Name"
msgErrorSplittingInput = "Problem encountered parse input list"
msgErrorValidateInputRaster ="Problem encountered validate input raster"


def copyfeatures(inFeatures, outFeatureClass):
    ''' Copy the contents (features) of the input feature class to the output 
    feature class.'''
    
    # Create the geoprocessing object
    gp = get_geoprocessor(10)
    
    try:
        gp.CopyFeatures_management(inFeatures, outFeatureClass)
    except:
        raise Exception, gp.GetMessages(2).replace("\n"," ")


def copyrasters(inRasters, outRasters, keyword):
    ''' Copy the contents (rasters) of the input raster dataset to the output 
    raster dataset.'''
    
    # Create the geoprocessing object
    gp = get_geoprocessor(10)
    
    try:
        gp.CopyRaster_management(inRasters, outRasters, keyword)
    except:
        raise Exception, gp.GetMessages(2).replace("\n"," ")


def copyrows(inTable, outTable):
    ''' Copy the contents (rows) of the input table to the output table.'''
    
    # Create the geoprocessing object
    gp = get_geoprocessor(10)
    
    try:
        gp.CopyRows_management(inTable, outTable)
    except:
        raise Exception, gp.GetMessages(2).replace("\n"," ")

def exceptionmsgs(msgWarning, msgStr, ErrDesc):
    
    # Create the geoprocessing object
    gp = get_geoprocessor(10)
    
    if msgStr != "":
        msgWarning = msgWarning + ". " + msgStr
    elif str(ErrDesc) != "":
        msgWarning = msgWarning + ". " + str(ErrDesc)
    return msgWarning


def extract_workspace(input):
    
    try:
        # Check if the input has multiple feature classes
        input = multisplit(input)

        # Extract the the workspace path from the 1st feature class location
        # TODO: create a smarter way to deal with multiple workspaces
        ws = os.path.dirname(input[0])
        if os.path.exists(ws):
            return ws
    except:
        ErrDesc = "Error: Failed in parsing the inputs."
        raise StandardError, ErrDesc

def generate_outputname(inName, outWorkspace, prefix='', suffix=''):
    ''' Generates a valid output feature class or table name based on the input 
    and destination.'''
    
    # Create the geoprocessing object
    gp = get_geoprocessor(10)
    
    try:
        # Extract the basename for the input fc from the path (ie. the input
        # feature class or table name)
        outName = os.path.basename(inName)

        #Describe the FeatureClass to determine it's type (shp, cov fc, gdb fc,
        # etc...)
        dsc = gp.Describe(inName)

        # Get the path to the input feature class (basically the fc container).
        # This could be a dataset, coverage, geodatabase, etc...
        inContainer = os.path.dirname(inName)   # Full path excluding the
                                                # featureclass.
                                                # D:\Data\redlands.mdb\city

        if inContainer:
            # Extract the basename for the fc container (ie. the geodatabase
            # name, or feature dataset name)
            # This will be used in certain cases to generate the output name
            # Full path excluding the featureclass. D:\Data\redlands.mdb\city
            inContainerName = os.path.basename(inContainer)

            # Describe the type of the Feature class container (cov, gdb, vpf,
            # etc...)
            dscInContainer = gp.Describe(inContainer)

            # If the input fc is a feature dataset (Coverage, CAD or VPF), then
            # set the output name to be a combination of the input feature
            # dataset and feature class name. For example if the input
            # is "c:\gdb.mdb\fds\fc" the name for the output feature class would
            # be "fds_fc"
            if (dsc.DataType == "CoverageFeatureClass"
                or dscInContainer.DataType == "VPFCoverage"
                or dscInContainer.DataType == "CadDrawingDataset"
                or dscInContainer.DataType == "RasterDataset"):
                outName = inContainerName + "_" + outName

            # If the input is a shapefile, txt or dbf, do not include the
            # extention (".shp", ".dbf", ".txt") as part of the output name
            # Do this everytime since the output could may or may not be a
            # geodatabase feature class or table
            elif ((dsc.DataType == "DbaseTable")
                  or (dsc.DataType == "ShapeFile")
                  or (dsc.DataType == "TextFile")):
                outName = outName[:outName.find(".")]

        # The next 3 steps (get rid of invalid chars, add extention (if the
        # output will have one), and generate a unique name)

        # If output workspace is a folder, the output is either a shp file or a
        # dbase table, so determine if the output name need to add .shp or .dbf
        # extention to the output
        desOutWorkspace = gp.Describe(outWorkspace)
        if desOutWorkspace.DataType == "Folder":
            if ((dsc.DatasetType == "FeatureClass") and
                (not outName.lower().endswith(".shp"))):
                outName = outName.replace(":","_").replace(".","_") + ".shp"
            elif ((dsc.DatasetType == "Table") and
                  (not outName.lower().endswith(".dbf"))):
                outName = outName.replace(":","_").replace(".","_") + ".dbf"

        # If the output location is a Geodatabase (SDE or Personal) we can use
        # gp.ValidateTableName to generate
        # a valid name for the output table or feature class.
        elif desOutWorkspace.DataType == "Workspace" :
            try:
                outName = gp.ValidateTableName(outName, outWorkspace)
            except:
                pass

        elif desOutWorkspace.DataType == "FeatureDataset":
            try:
                outName = gp.ValidateTableName(outName,
                                               os.path.dirname(outWorkspace))
            except:
                pass

        # TODO: check if this really works
        outName = prefix + outName + suffix
        # Check if the name which has been generated so far already exist, if
        # yes, create a unique one ValidateTableName will return something
        # unique for that workspace (not yet though) so this (eventually) should
        # move into the >if desOutWorkspace.DataType == "Folder"< block
        outName = generate_uniquename(outName, outWorkspace)

        #Return the name full path to the name which was generated
        return outWorkspace + os.sep + outName

    except Exception, ErrorDesc:
        ErrorDesc0 = ErrorDesc
        ErrorDesc = ""
        for sErr in ErrorDesc0:
            ErrorDesc = ErrorDesc + sErr
        raise Exception, "%s (%s)" % (msgErrorGenOutput, ErrorDesc)

def generate_rastername(inName, outWorkspace, ext, suffix=None):
    ''' Generate a valid output raster dataset name with extension.'''
    
    # Create the geoprocessing object
    gp = get_geoprocessor(10)
    
    try:

        # Extract the basename for the input raster dataset
        outName = os.path.basename(inName)

        # Get the path to the input dataset. This could be a raster catalog or
        # workspace.

        # Full path excluding the raster dataset
        inContainer = os.path.dirname(inName)
        
        # If inContainer is empty then only basename is provided
        if inContainer != '':
            des = gp.Describe(inContainer)
            # use raster catalog name as basename
            if (des.DataType == "RasterCatalog"): #rastercatalog
                outName = os.path.basename(inContainer)
            elif (des.WorkspaceType =="FileSystem"): #file with extension
                ids = outName.find(".")
                if (ids > -1):
                    outName = outName[:ids]
        else:
            ids = outName.find(".")
            if (ids > -1):
                outName = outName[:ids]

        # Id a custom suffix is provided, concatenate it to the raster name
        if suffix:
            outName = outName + '_' + str(suffix)

        # for ArcSDE
        outName.replace(":",".")
        ids = outName.rfind(".")
        if (ids > -1):
            outName = outName[(ids+1):]

        desOutWorkspace = gp.Describe(outWorkspace) #workspace
        if (desOutWorkspace.DataType == "RasterCatalog"):
            return outWorkspace

        # If the output location is a Geodatabase (SDE or Personal) we can use
        # gp.ValidateTableName to generate a valid name for the output table or
        # feature class.
        if desOutWorkspace.DataType == "Workspace":
            try:
                outName = gp.ValidateTableName(outName, outWorkspace)
            except:
                pass

        if (desOutWorkspace.WorkspaceType == "FileSystem"): #filesystem
            outName = outName + ext
            if (ext == ""): #Grid format, make sure the filename is 8.3 standard
                grdlen = len(outName)
                if (grdlen > 12):
                    outName = outName[:8]
        #else:
        #    outName = gp.QualifyTableName(outName,outWorkspace)

        outName = generate_uniquename(outName, outWorkspace)

        return outWorkspace + os.sep + outName

    except Exception, ErrorDesc:
        ErrorDesc0 = ErrorDesc
        ErrorDesc = ""
        for sErr in ErrorDesc0:
            ErrorDesc = ErrorDesc + sErr
        raise Exception, "%s (%s)" % (msgErrorGenOutputRaster, ErrorDesc)


def generate_uniquename(name, workspace):
    ''' Generates a unique name. If the name already exists, adds "_1" at the 
    end, if that exists, adds "_2", and so on...'''
    
    # Create the geoprocessing object
    gp = get_geoprocessor(10)
    
    if gp.Exists(workspace + os.sep + name):

        # If there is an extention, figure out what it is
        extention = ""
        if ((name.find(".shp") != -1) or (name.find(".dbf") != -1)
             or (name.find(".img") != -1) or (name.find(".tif") != -1)):
            name,extention = name.split(".")
            extention = "." + extention
        i = 1
        name2 = name + "_" + str(i) + extention
        while gp.Exists(workspace + os.sep + name2):
            # While the output exists, add 1 to it. So if "tab_1" exists, try
            # "tab_2", then "tab_3", ...
            i += 1
            name2 = name + "_" + str(i) + extention
        name = name2
    return name

def legacy_arcgisscripting(licensetype=None, verbose=True):
    
    logger = Logger("zupport.utilities")

    try:
        import win32com.client
    except ImportError:
        logger.error('Could not import win32com.client.')
        return

    gp = win32com.client.Dispatch("esriGeoprocessing.GpDispatch.1")
    if licensetype is not None:
        Licensed=gp.SetProduct(licensetype)
        if not (Licensed in ["NotLicensed","Failed"]):
            return gp

    #Either the licensetype was not set, or it failed
    #Try to get the highest possible license
    types = ["ArcInfo","ArcEditor","ArcView"]

    for license in types:
        Licensed=gp.CheckProduct(license)
        if not (Licensed in ["NotLicensed","Failed"]):
            Licensed = gp.SetProduct(license)
            logger.debug("Geoprocessor started with license: %s (%s)" %
                         (license, Licensed))
            return gp
        else:
            logger.debug("License %s is %s" % (license, Licensed))

    gp.AddError("No License available for geoprocessor")
    raise ValueError,"No License available for geoprocessor"


def multisplit(multiInputs):
    ''' Split the semi-colon (;) delimited input string (tables or feature 
    classes) into a list.'''
    try:
        # Remove the single quotes and parenthesis around each input
        # featureclass
        # Changed at June 2007, instead of replace "(" and ")" with "", just
        # strip them if they're first or last character in multiInputs
        multiInputs = multiInputs.replace("'","")
        if multiInputs.startswith("("):
            multiInputs = multiInputs[1:]
        if multiInputs.endswith(")"):
            multiInputs = multiInputs[:-1]

        #split input tables by semicolon ";"
        return multiInputs.split(";")
    except:
        raise Exception, msgErrorSplittingInput

def chop_raster(height, width, nrows, ncols, origin='llc'):
    '''Chops up a given raster (matrix) into as-equal-as-possible chunks based
    on raster width and height. If the raster has odd number of rows or columns
    the last chunk will hold more rows and/or columns. Note that the origin is
    lower left corner (llc) by default.
    
    Parameters:
    
    height     int height of the raster (rows)
    width      int width of the raster (columns)
    nrows      int how many rows is the raster chopped up into
    ncols      int how many cols is the raster chopped up into
    
    return     A nested list of tuples holding chunk dimension [[(h, w), (h, w)], 
                                                                [(h, w), (h, w)]]
    
                Original raster:    A    A
                                    A    A
                                    
                Return order:       C    D
                                    A    B   -> [A, B, C, D]
    
    '''
    chunks = []

    if nrows < 1:
        raise ValueError('nrows must be a positive integer')

    if ncols < 1:
        raise ValueError('ncols must be a positive integer')

    # Enforce integers for nrows and ncols by casting
    height_element = height / int(nrows)
    height_modulus = height % int(nrows)
    
    width_element = width / int(ncols)
    width_modulus = width % int(ncols)
    
    for i in range(0, nrows):
        if i == nrows - 1:
                row_element = height_element + height_modulus
        else:
            row_element = height_element
        row = []
        for j in range(0, ncols):
            
            # Add the modulus only to the last element 
            if j == ncols - 1:
                col_element = width_element + width_modulus
            else:
                col_element = width_element
            row.append((row_element, col_element))
        chunks.append(row)

    if origin == 'ulc':
        pass
    elif origin == 'llc':
        chunks.reverse()
        
    return chunks
        
def validate_inraster(inName):
    try:
        if inName.startswith("'") and inName.endswith("'"):
            inName = inName[1:-1]
        return inName

    except:
        raise Exception, msgErrorValidateInputRaster
    
if __name__ == '__main__':
    print chop_raster(8444, 9131, nrows=3, ncols=3, origin='llc')