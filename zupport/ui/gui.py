#!/usr/bin/python
# coding=utf-8

import os 
import platform
import sys
from types import BooleanType, FloatType, IntType, ListType, StringType

from guidata.dataset import datatypes, dataitems
from guidata.qthelpers import get_icon
from guidata.qt.QtGui import (QAction, QActionGroup, QColor, QMainWindow, QMenu,  
                              QMessageBox, QTextCursor, QTreeWidgetItem)
from guidata.qt.QtCore import (QPoint, QSettings, QSize, QStringList, QVariant, 
                               Slot)
from guidata.qt.QtCore import PYQT_VERSION, QT_VERSION

from zupport.resources.ui_toolloader import Ui_MainWindow
from zupport.core import (ExtentContainer, Manager, Parameter)
from zupport.utilities import (APP_RESOURCES, USER_DATA_DIR, __version__)
from zupport.zlogging import Logger

"""
Zupport specific GUI operations.

This module provides wrappers and parsers for :mod:guidata module. Main purpose
is to provide an easy way to provide a GUI for :mod:Zupport plugins by 
dynamically constructing the GUI from Parameters object.
"""

#------------------------------------------------------------------------------ 
# Main graphical components

class MainWindow(QMainWindow, Ui_MainWindow):
    '''Mainwindow for initial loading of different plugins.
    '''
    
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowIcon(get_icon(os.path.join(APP_RESOURCES, 'icons',
                                                  'python.png')))
        self.setupUi(self)
        
        # Redirect output to GUI's QTextEdit
        sys.stdout = OutLog(self.outputTextEdit, sys.stdout)
        sys.stderr = OutLog(self.outputTextEdit, sys.stderr, QColor(255,0,0) )
        
        settings = QSettings()
        size = settings.value("MainWindow/Size",
                              QVariant(QSize(600, 500))).toSize()
        self.resize(size)
        position = settings.value("MainWindow/Position",
                                  QVariant(QPoint(0, 0))).toPoint()
        self.move(position)
        self.restoreState(
        settings.value("MainWindow/State").toByteArray())
    
        self.logger = Logger('Zupport.GUIloader')
        self.logger.debugging = settings.value("Logging/debugging").toBool()
         
        # Set up a ZupportManager to deal with the plugins
        self.manager = Manager(self)
        self.plugins = {}

        # Set up the extents menu
        self.extent = ExtentContainer()
        self.menuExtent = QMenu("Extent")
        resolutions = self.extent.resolutions
        self.extenactiongroup = QActionGroup(self.menuExtent)  
        noneaction = QAction("None", self.menuExtent)
        self.extenactiongroup.addAction(noneaction)
        self.menuExtent.addAction(noneaction)
        for resolution in resolutions:
            resolution_text = str(resolution)
            submenu = self.menuExtent.addMenu(resolution_text) 
            self.menuExtent.addMenu(submenu)
            for area in self.extent.get_names(resolution):
                subaction = QAction(str(area) + ": %s" % resolution_text, 
                                    submenu)
                subaction.setCheckable(True)
                self.extenactiongroup.addAction(subaction)
                submenu.addAction(subaction)
        
        noneaction.isChecked()
        self.menuSettings.addMenu(self.menuExtent)
        
        self.actionDebugging_messages.setChecked(self.logger.debugging)

        self.setWindowTitle("Zupport GUI")
        
        self.load_tools()
        
        self.toolTreeWidget.itemSelectionChanged.connect(self.update_ui)
        self.actionDebugging_messages.toggled.connect(self._set_debugging)
        self.menuExtent.triggered.connect(self.update_ui)
        self.actionLoad_tool.triggered.connect(self.show_tool_gui)
        self.toolTreeWidget.doubleClicked.connect(self.show_tool_gui)
    
    def closeEvent(self, event):
        settings = QSettings()
        settings.setValue("Logging/debugging", self.logger.debugging)
        settings.setValue("MainWindow/Size", QVariant(self.size()))
        settings.setValue("MainWindow/Position",
                          QVariant(self.pos()))
        settings.setValue("MainWindow/State",
                          QVariant(self.saveState()))
    
    def load_tools(self):
        plugins = self.manager.plugins
        for name, plugin in plugins.iteritems():
            item = QTreeWidgetItem(QStringList(name.capitalize()))
            tool_items = []
            for tool_name in plugin.tool_names():
                tool_items.append(QTreeWidgetItem(QStringList(tool_name)))
            item.addChildren(tool_items)
            self.toolTreeWidget.addTopLevelItem(item)
            item.setExpanded(True)
        
        self.statusbar.showMessage("Succesfully loaded %s plugins" % len(plugins), 
                         4000)
    
    def show_tool_gui(self):
        selected_tool = self.toolListWidget.currentItem()
        toolname = str(selected_tool.text())
        parameters = self.manager.plugins[toolname]
        
        # Check if extent is available
        extent = self.extenactiongroup.checkedAction()
        if extent:
            extent = str(extent.text())
            # Extent is a String of the form "area: resolution"
            area, resolution = extent.split(':')
            resolution = int(resolution)
            self.extent.resolution = resolution
            # This is a list of coordinates
            coordinates = self.extent.get_extent(area)
            # Create a string for the GUI
            coord_text = ', '.join([str(coord) for coord in coordinates])
            self.manager.plugins[toolname].set_parameter_value('extent', coord_text)
        
        dataset = ToolLoader(toolname, parameters)
        if dataset.edit():
            self.logger.debug('User pressed OK, proceeding to execution')
            self.manager.plugins[toolname] = dataset.get_parameters()
        
            # Run the tool
        
            if self.actionArcGIS.isChecked():
                backend = 'arcgis'
            else:
                backend = 'osgeo'
            
        else:
            self.logger.debug('User pressed cancel')
            return
    
        self.manager.executetool(toolname, backend)
    
    def update_ui(self):
        if self.toolTreeWidget.currentItem():
            self.actionLoad_tool.setEnabled(True)
            selected_tool = str(self.toolTreeWidget.currentItem().text(0))
            help_text = self.manager.plugins[selected_tool].help
            self.helpTextEdit.setText(help_text)
        
        extent = self.extenactiongroup.checkedAction()
        if extent: 
            self.extentLabel.setText("Current extent: %s" % extent.text())
    
    @Slot()
    def on_actionAbout_triggered(self):
        QMessageBox.about(self, "About Zupport GUI",
                          """<b>Zupport GUI</b> v %s
                            <p>Copyright &copy; 2011 Joona Lehtomaki 
                            <joona.lehtomaki@gmail.com>.
                            All rights reserved.
                            <p>Support zools for Zonation related pre- and post-processing operations.</p>
                            <p>Python %s - Qt %s - PySide %s on %s</p>""" % (
                            __version__, platform.python_version(),
                            QT_VERSION,
                            PYQT_VERSION, platform.system()))
           
    @Slot()
    def on_actionOpen_log_triggered(self):
        logfile = os.path.join(USER_DATA_DIR, 'zupport.log')
        if os.path.exists(logfile):
            import webbrowser
            webbrowser.open(logfile)
            self.logger.debug('Opened log file %s' % logfile)
        else:
            msg = "Zupport log file cannot be found in default location %s" % os.path.dirname(logfile)
            self.logger.debug(msg)
            QMessageBox.warning(self, "File not found", 
                                msg, 
                                buttons=QMessageBox.Ok, 
                                defaultButton=QMessageBox.NoButton)
            
    def _set_debugging(self, toggle):
        self.logger.debugging = toggle
        
class OutLog:
    def __init__(self, edit, out=None, color=None):
        """(edit, out=None, color=None) -> can write stdout, stderr to a
        QTextEdit.
        edit = QTextEdit
        out = alternate stream ( can be the original sys.stdout )
        color = alternate color (i.e. color stderr a different color)
        Example usage:
        import sys
        sys.stdout = OutLog( edit, sys.stdout)
        sys.stderr = OutLog( edit, sys.stderr, QtGui.QColor(255,0,0) )
        """
        self.edit = edit
        self.out = out
        self.color = color

    def write(self, m):
        if self.color:
            tc = self.edit.textColor()
            self.edit.setTextColor(self.color)

        self.edit.moveCursor(QTextCursor.End)
        self.edit.insertPlainText( m )

        if self.color:
            self.edit.setTextColor(tc)

        if self.out:
            self.out.write(m)
        
#------------------------------------------------------------------------------ 
# Zupport DataSets

class ToolLoader(datatypes.DataSet):
    '''Base class for other loaders. 
    
    Parameters' value modification will be done in-place after which the actual 
    tool is executed. If parameter values are provided as args or kwargs these 
    will be used as default values for the GUI, else parameter definition 
    default values will be used if present.
    '''
    
    def __init__(self, toolname, parameters, *args, **kwargs):
        
        # HACK - by default there seems to be object persistent between the 
        # creation of different ToolLoader objects
        self._items = []
        
        datatypes.DataSet.__init__(self, title=toolname, comment='', 
                                   *args, **kwargs)
        
        self.logger = Logger('Zupport.GUIloader.ToolLoader', debugging=True)
        self.logger.debug("Creating GUI for tool %s" % toolname)
        self.parameters = parameters
        
        for parameter in parameters:
            self.add_dataitem(parameter)
            
    def add_dataitem(self, item):
        ''' Adds a data item to a :mod:`guidata` DataSet. 
        
        Normally items are created from class attributes by metaclass 
        DataSetMeta and dynamically created class attributes are not converted
        into data items. 
        
        TODO: Method is a hack to guidata and a more clean API access should be
        implemented.
        
        Parameters:
        item - Object to be converted to a DataItem
        '''

        if isinstance(item, Parameter):
            dataitem = self.parameter_to_dataitem(item)
            name = item.name
        else:
            name = ''
        
        # Following block borrowed from DataSetMeta, self._items is a list of 
        # DataItems
        
        if isinstance(dataitem, datatypes.DataItem):
            dataitem.set_name(name)
            # Check if the attribute is already in self._items
            for _item in self._items:
                if name == _item._name:
                    dataitem._order = _item._order
            self._items.insert(dataitem._order, dataitem)
        
    def parameter_to_dataitem(self, parameter):
        ''' Method converts a given Parameter object to a suitable guidata 
        DataItem
        '''
        
        param_type = type(parameter.value)
        dataitem = None
        
        if param_type is BooleanType:
            dataitem = dataitems.BoolItem(label=parameter.label, 
                                          default=parameter.value,
                                          required=parameter.required,
                                          help=parameter.tip)
        elif param_type is FloatType:
            dataitem = dataitems.FloatItem(label=parameter.label, 
                                          default=parameter.value,
                                          required=parameter.required,
                                          help=parameter.tip)
        elif param_type is IntType:
            dataitem = dataitems.IntItem(label=parameter.label, 
                                          default=parameter.value,
                                          required=parameter.required,
                                          help=parameter.tip)
        elif param_type is ListType:
            dataitem = dataitems.ChoiceItem(label=parameter.label, 
                                            choices=parameter.value,
                                            required=parameter.required,
                                            help=parameter.tip)
        elif param_type is StringType:
            if parameter.name == 'help':
                #dataitem = dataitems.TextItem(label=parameter.name,
                #                                default=parameter.value,
                #                                help=parameter.tip)
                self.__doc__ = parameter.value
                return None
            else:
                values = parameter.value.split(':')
                if 'PATH' in values[0]:
                    path = ''
                    if len(values) > 1:
                        path = path + ''.join(values[1:])
                    dataitem = dataitems.DirectoryItem(label=parameter.label,
                                                       default=path,
                                                       notempty=parameter.required,
                                                       help=parameter.tip)
                else:
                    dataitem = dataitems.StringItem(label=parameter.label,
                                                    default=parameter.value,
                                                    required=parameter.required,
                                                    help=parameter.tip)
        return dataitem
    
    def get_parameters(self):
        
        # TODO: guidata apparently mangles the object attribute names so that
        # attributeA becomes object._attributeA --> shouldn't be so, might 
        # have something to do with the dynamic creation of object attributes
        
        for parameter in self.parameters:
            try:
                if parameter.name != 'help':
                    parameter.value = getattr(self, '_' + parameter.name)
                    self.logger.debug("Updated dataset parameter %s to value %s" % (parameter.name, parameter.value))
            except AttributeError:
                self.logger.error("Parameter / attribute mismatch: %s " % parameter.name)
                
        return self.parameters

#------------------------------------------------------------------------------ 
# Run the main GUI

def main():
    
    # Init the Qt basics
    from guidata.qt.QtGui import QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Zupport")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("HU")
    app.setOrganizationDomain("MRG")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()
    