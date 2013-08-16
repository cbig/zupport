:mod:`Gisutils` - GIS utility tools
===================================

.. automodule:: zupport.core
   :platform: Unix, Windows

ArcGIS Tool Chain
-----------------

.. warning:: In order to use the ArcGIS tool chain you will need an existing and
	operational installation of `ArcGIS <http://www.esri.com/software/arcgis/>`_
	(version >= 9.3.1) and in most cases also
	Spatial Analyst.

.. autoclass:: ArcTool
  :show-inheritance:
  :members:
  :inherited-members:
  :undoc-members:

OSGeo Tool Chain
-----------------

.. warning:: In order to use the OSGeo tool chain you will need an existing and
	operational installation of `GDAL <http://www.gdal.org/>`_ and the
	associated Python bindings.

.. autoclass:: OSGeoTool
  :show-inheritance:
  :members:
  :undoc-members:

Common tools
------------

.. autoclass:: Workspace
  :show-inheritance:
  :members: files, refresh, filter, path
  :undoc-members:

.. moduleauthor:: Joona Lehtomaki <joona.lehtomaki@gmail.com>