# THIS MODULE SHOULD ONLY BE CALLED FROM ARCGIS TOOLBOX

import arcpy
from zupport.core import Job, Manager
from zupport.utilities import USER_DATA_DIR

NAME = "aggregate"

manager = Manager()
plugin = manager.get_plugin('zarcgis')
if plugin and plugin.registered(NAME):
    manager.run_job(Job(NAME, batch=False, gui=True))
else:
    arcpy.AddError("Could not load Zupport tool: %s" % NAME)
    arcpy.AddMessage("See log file in %s for more information" % USER_DATA_DIR)