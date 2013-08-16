# THIS MODULE SHOULD ONLY BE CALLED FROM ARCGIS TOOLBOX

from zupport.core import ZupportManager

manager = ZupportManager()
manager.executetool('MultiClipRaster', 'arcgis')