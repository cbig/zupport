# THIS MODULE SHOULD ONLY BE CALLED FROM ARCGIS TOOLBOX

import os
import arcpy
from zupport.core import Job, Manager
from zupport.plugins.fileio import FileGroupIterator
from zupport.utilities import USER_DATA_DIR
from zupport.utilities.dataframe import read_csv, ZCustom

NAME = "rasigmoidal"

manager = Manager()
plugin = manager.get_plugin('zarcgis')
if plugin and plugin.registered(NAME):

    # Input workspace
    inputws = arcpy.GetParameterAsText(0)
    #inputws = r"C:\Data\Staging\Output\MK_puusto\ositteet"

    # Wildcard
    wildcard = arcpy.GetParameterAsText(1)
    #wildcard = "*.img"

    # Template to be used
    template = arcpy.GetParameterAsText(2)
    #template = "<BODY1>_<ID1>_<BODY2>_<ID2>_<BODY3>"

    # Grouping tags
    grouptags = arcpy.GetParameterAsText(3)
    grouptags = grouptags.split(";")
    #grouptags = ['ID1', 'ID2']
    output_workspace = arcpy.GetParameterAsText(4)

    # Target table file for the parameters DataFrame
    params_file = arcpy.GetParameterAsText(5)
    #params_file = r"C:\Users\admin_jlehtoma\workspace\gdalscripts\R\parameters_new.csv"

    # Field in the params table to idetify the group
    idfield = arcpy.GetParameterAsText(6)
    #idfield = "IPUULAJI"

    debugging = arcpy.GetParameterAsText(7)

    try:
        try:
            parameters = read_csv(params_file, dialect=ZCustom)
        except:
            arcpy.AddError('Could not read in parameter file %s' % params_file)

        # Create a FileGroupIterator to iterate over raster pairs
        iterator = FileGroupIterator(inputws, wildcard, template, grouptags)

        for key, pair in iterator:
            if len(pair) != 2:
                raise ValueError('Only 2 rasters per group can be provided for rasigmoidal')

            raster1 = pair[0]
            raster2 = pair[1]

            # These should be the same for both rasters, note that ID1 is by
            # convention used to signify identifier in params table
            # FIXME: tag use now inconsistent, should not be hard coded
            ID1 = raster1.get_tag('ID1')

            # Create a suitable output raster path passed on the input raster
            # name
            # FIXME: this will only work for FGDBs
            # FIXME: tags return floats, which won't work in names. Coercing
            # into strings/ints should be handled somehow
            output_raster = '_'.join([str(raster1.get_tag('BODY1')),
                                      str(int(raster1.get_tag('ID1'))),
                                      str(raster1.get_tag('BODY2')),
                                      str(int(raster1.get_tag('ID2'))),
                                      'index'])

            output_raster = os.path.join(output_workspace, output_raster)

            # Note that tag matching between the rasters has already been
            # taken care of by the FileGroupIterator

            id_parameter = parameters.where_field_equal(idfield, int(ID1))

            if id_parameter is None:
                raise ValueError('Value %s not found for %s' % (int(ID1),
                                 idfield))

            mod_asym = id_parameter.mod_asym
            xmid = id_parameter.median
            lxmod = id_parameter.xmod
            rxmod = id_parameter.xmod
            lscale = id_parameter.lscale
            rscale = id_parameter.rscale

            manager.run_job(Job(NAME, batch=True, gui=True,
                                raster1=raster1.path,
                                raster2=raster2.path,
                                output_raster=output_raster,
                                raster_type='ERDAS IMAGINE',
                                asymptote=mod_asym,
                                xmid=xmid,
                                lxmod=lxmod,
                                rxmod=rxmod,
                                lscale=lscale,
                                rscale=rscale,
                                debug=debugging))

    except ValueError, e:
        arcpy.AddError(e)
        arcpy.AddMessage("See log file in %s for more information" %
                         USER_DATA_DIR)
    except IOError, e:
        arcpy.AddError(e)
        arcpy.AddMessage("See log file in %s for more information" %
                         USER_DATA_DIR)
else:
    arcpy.AddError("Could not load Zupport tool: %s" % NAME)
    arcpy.AddMessage("See log file in %s for more information" % USER_DATA_DIR)
