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
"""
from PyQt4 import QtCore, QtGui 
from Ui_QGISZupport import Ui_QGISZupport
# create the dialog for QGISZupport
class QGISZupportDialog(QtGui.QDialog):
    def __init__(self): 
        QtGui.QDialog.__init__(self) 
        # Set up the user interface from Designer. 
        self.ui = Ui_QGISZupport ()
        self.ui.setupUi(self)