# THIS MODULE SHOULD ONLY BE CALLED FROM ARCGIS TOOLBOX

import arcpy
from zupport.core import Job, Manager
from zupport.utilities import USER_DATA_DIR

NAME = "batch_aggregate"

manager = Manager()
plugin = manager.get_plugin('zarcgis')
if plugin and plugin.registered(NAME):
    job = Job(NAME)
    manager.add_job(job)
    manager.run_jobs()
else:
    arcpy.AddError("Could not load Zupport tool: %s" % NAME)
    arcpy.AddMessage("See log file in %s for more information" % USER_DATA_DIR)
    