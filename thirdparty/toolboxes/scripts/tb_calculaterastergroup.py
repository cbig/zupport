# THIS MODULE SHOULD ONLY BE CALLED FROM ARCGIS TOOLBOX

import arcpy
from zupport.core import Job, Manager
from zupport.utilities import USER_DATA_DIR
from zupport.utilities.dataframe import read_csv, ZCustom


NAME = "calculaterastergroup"

manager = Manager()
plugin = manager.get_plugin('zarcgis')
if plugin and plugin.registered(NAME):
    
    # Input workspace
    inputws = arcpy.GetParameterAsText(0)
    
    wildcard = arcpy.GetParameterAsText(1)
    
    template = arcpy.GetParameterAsText(2)
    
    grouptags = arcpy.GetParameterAsText(3)
    grouptags = grouptags.split(";")
    
    operator = arcpy.GetParameterAsText(4)
    
    outws = arcpy.GetParameterAsText(5)
    
    # These will be None if not provided
    reftable_file = arcpy.GetParameterAsText(6)
    
    reftable = read_csv(reftable_file, dialect=ZCustom)
    
    reffields = (arcpy.GetParameterAsText(7), arcpy.GetParameterAsText(8))
    debugging = bool(arcpy.GetParameterAsText(9))
    
    manager.run_job(Job(NAME, batch=True, gui=True,
                        input_workspace=inputws,
                        wildcard=wildcard,
                        template=template,
                        grouptags=grouptags,
                        operator=operator,
                        output_workspace=outws,
                        reference_table=reftable,
                        reference_fields=reffields,
                        debug=debugging))
else:
    arcpy.AddError("Could not load Zupport tool: %s" % NAME)
    arcpy.AddMessage("See log file in %s for more information" % USER_DATA_DIR)
    