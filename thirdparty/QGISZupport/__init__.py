"""
/***************************************************************************
Name			 	 : Zupport plugin
Description          : QGIS interface to Zupport related tools
Date                 : 12/Aug/11 
copyright            : (C) 2011 by Joona Lehtomaki
email                : joona.lehtomaki@gmail.com 
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""
def name(): 
  return "Zupport plugin" 
def description():
  return "QGIS interface to Zupport related tools"
def version(): 
  return "Version 0.1" 
def qgisMinimumVersion():
  return "1.0"
def classFactory(iface): 
  # load QGISZupport class from file QGISZupport
  from QGISZupport import QGISZupport 
  return QGISZupport(iface)
