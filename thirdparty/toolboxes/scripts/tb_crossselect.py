# THIS MODULE SHOULD ONLY BE CALLED FROM ARCGIS TOOLBOX

import arcpy
from zupport.core import Job, Manager
from zupport.utilities import USER_DATA_DIR

NAME = "crossselect"

manager = Manager()
plugin = manager.get_plugin('zarcgis')
if plugin and plugin.registered(NAME):
    
    reference_raster = arcpy.GetParameterAsText(0)

    inputws = arcpy.GetParameterAsText(1)
    
    outws = arcpy.GetParameterAsText(2)
    
    include = arcpy.GetParameterAsText(3)
    include = include.split(",")
    exclude = arcpy.GetParameterAsText(4)
    exclude = exclude.split(",")
    try:
        if include != ['']:
            include = [int(value.strip()) for value in include]
    except ValueError, e:
        arcpy.AddError("Include values must be integers")
    try:
        if exclude != ['']:
            exclude = [int(value.strip()) for value in exclude]
    except ValueError, e:
        arcpy.AddError("Exclude values must be integers")
    
    
    raster_format = arcpy.GetParameterAsText(5)
    
    raster_name_tag = arcpy.GetParameterAsText(6)
    
    debugging = bool(arcpy.GetParameterAsText(7))
    
    manager.run_job(Job(NAME, batch=True, gui=True,
                        reference_raster=reference_raster,
                        input_workspace=inputws,
                        output_workspace=outws,
                        include=include,
                        exclude=exclude,
                        raster_format=raster_format,
                        raster_name_tag=raster_name_tag,
                        debug=debugging))
else:
    arcpy.AddError("Could not load Zupport tool: %s" % NAME)
    arcpy.AddMessage("See log file in %s for more information" % USER_DATA_DIR)
    