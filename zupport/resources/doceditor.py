from zupport.resources.ui_doceditor import Ui_editorWindow

#!/usr/bin/python
# coding=utf-8
'''
Created on 1.12.2009

@author: admin_jlehtoma
'''

# Standard system imports

import platform
import sys

# Import Qt modules

from PyQt4.QtCore import pyqtSignature, QT_VERSION_STR, PYQT_VERSION_STR, \
    QString, QSettings, QVariant, QTimer, QFile
from PyQt4.QtGui import QApplication, QMainWindow, QMessageBox, \
    QFileDialog

# Other packages

from yaml import load_all

# Local packages

from zupport.resources.ui_doceditor import Ui_editorWindow

__version__ = "0.0.1"

class InterfaceError(Exception):
    """
    """

    def __init__(self, e):
        Exception.__init__(self, e)
        self.e = e

    def __str__(self):
        return self.e


class DocEditorWindow(Ui_editorWindow, QMainWindow):
    """
    """
    '''
    classdocs
    '''

    def __init__(self, parent=None):
        '''
        Constructor
        '''
        super(DocEditorWindow, self).__init__(parent)
        self.setupUi(self)

        self._reader = None
        self._document = None
        self.filename = None
        self.dirty = False

        self.docs_listWidget.currentRowChanged.connect(self.__set_document)
        self.nameLineEdit.textEdited.connect(self.setDirty)
        self.administratorLineEdit.textEdited.connect(self.setDirty)
        self.updatedDateEdit.dateChanged.connect(self.setDirty)
        self.publicityComboBox.editTextChanged.connect(self.setDirty)
        self.plannedusageTextEdit.textChanged.connect(self.setDirty)
        self.characteristicsTextEdit.textChanged.connect(self.setDirty)
        self.analysisusageTextEdit.textChanged.connect(self.setDirty)
        self.descriptionTextEdit.textChanged.connect(self.setDirty)

        # Handle the window settings
        settings = QSettings()
        self.recentFiles = settings.value("RecentFiles").toStringList()
        self.restoreGeometry(settings.value("MainWindow/Geometry").toByteArray())
        self.restoreState(settings.value("MainWindow/State").toByteArray())
        QTimer.singleShot(1, self.loadInitialFile)

    def closeEvent(self, event):
        if self.okToContinue():
            settings = QSettings()
            filename = QVariant(QString(self.filename)) \
                    if self.filename is not None else QVariant()
            settings.setValue("LastFile", filename)
            recentFiles = QVariant(self.recentFiles) \
                    if self.recentFiles else QVariant()
            settings.setValue("RecentFiles", recentFiles)
            settings.setValue("MainWindow/State", QVariant(self.saveState()))
            settings.setValue("MainWindow/Geometry", QVariant(self.saveGeometry()))
        else:
            event.ignore()

    def loadInitialFile(self):
        settings = QSettings()
        fname = unicode(settings.value("LastFile").toString())
        if fname and QFile.exists(fname):
            self.loadFile(fname)

    def loadFile(self, fname):
        self.reader = self.filename = fname
        self.document = 0
        self.populate_list()
        self.filename = fname
        self.setDirty(False)

    def okToContinue(self):
        if self.dirty:
            reply = QMessageBox.question(self,
                                         "DocEditor - Unsaved changes",
                                         "Save unsaved changes?",
                                         QMessageBox.Yes|QMessageBox.No|
                                         QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                pass # self.fileSave()
        return True


#===============================================================================
# User actions

    @pyqtSignature("")
    def on_actionAbout_triggered(self):
        QMessageBox.about(self, "About Sppeculate",
                """<b>DocEditor</b> v %s
                <p>Copyright &copy; 2009 Joona Lehtomaki.
                All rights reserved.
                <p>This application can be used for training stuff.
                <p>Python %s - Qt %s - PyQt %s on %s""" % (
                __version__, platform.python_version(),
                QT_VERSION_STR, PYQT_VERSION_STR, platform.system()))

    @pyqtSignature("")
    def on_actionOpen_triggered(self):
        fname = QFileDialog.getOpenFileName(None,
                                    self.trUtf8("Select documentation file"),
                                    QString(),
                                    self.trUtf8("*.yml, *.yaml"),
                                    None)
        if fname and QFile.exists(fname):
            self.loadFile(unicode(fname))

    @pyqtSignature("")
    def on_actionSave_triggered(self):
        self.setDirty(False)

#===============================================================================
#  Getters and setters

    def setDirty(self, value=True):
        if value:
            self.dirty = True
        else:
            self.dirty = False

        self.setWindowModified(self.dirty)
        self.actionSave.setEnabled(self.dirty)

    def __get_document(self):
        return self._document

    def __set_document(self, index):
        if index in range(len(self.reader.documents)):
            self._document = self.reader.documents[index]
            self.update_ui()

    def __get_fields(self):
        return self.reader.__field_interface__

    def __set_reader(self, docpath):
        if docpath.endswith('.yml') or docpath.endswith('.yaml'):
            reader = YamlReader(docpath)
        else:
            raise NotImplementedError('Other formats than yaml not supported.')

        # Check that the reader object provides necessary interface
        if hasattr(reader , '__field_interface__'):
            self._reader = reader
        else:
            raise AttributeError('The data reader object does not provide' +
                                 ' a field interface.')

    def __get_reader(self):
        return self._reader

    document = property(__get_document, __set_document)
    fields = property(__get_fields)
    reader = property(__get_reader, __set_reader)

#===============================================================================
# Populators and updaters for the UI

    def populate_list(self):
        self.docs_listWidget.clear()

        for document in self.reader.documents:
            self.docs_listWidget.addItem(document[self.fields['name']])

        self.docs_listWidget.setCurrentRow(0)

    def populate_fields(self):
        self.nameLineEdit.setText(self.document[self.fields['name']])
        self.administratorLineEdit.setText(self.document[self.fields['administrator']])
        self.updatedDateEdit.setDate(self.document[self.fields['updated']])
        self.plannedusageTextEdit.setText(self.document[self.fields['plannedusage']])
        self.characteristicsTextEdit.setText(self.document[self.fields['characteristics']])
        self.analysisusageTextEdit.setText(self.document[self.fields['analysisusage']])
        self.descriptionTextEdit.setText(self.document[self.fields['description']])

    def update_ui(self):
        self.populate_fields()

class YamlReader(object):
    """
    """

    def __init__(self, inputdata, key='fields'):
        self.documents = []
        self.key = key
        self.fields = None

        self.load_data(inputdata)

    def __iter__(self):
        return self

    @property
    def __field_interface__(self):

        if len(self.fields) != 10:
            raise InterfaceError('Too few fields!')

        return {'name': self.fields[0],
                'administrator': self.fields[1],
                'updated': self.fields[2],
                'publicity': self.fields[3],
                'plannedusage': self.fields[4],
                'characteristics': self.fields[5],
                'analysisusage': self.fields[6],
                'description': self.fields[7],
                'meta_creator': self.fields[8],
                'meta_modified': self.fields[9]}

    def next(self):
        if not self.documents:
            raise StopIteration
        return self.documents.pop(0)

    def load_data(self, inputdata):
        try:
            data = load_all(file(inputdata, 'r'))
            for document in data:
                if document.has_key(self.key):
                    self.fields = document[self.key]
                else:
                    self.documents.append(document)

        except IOError, e:
            print 'No such file: %s!' % e

def main():
    # Create the main application
    app = QApplication(sys.argv)
    app.setOrganizationName("University of Helsinki")
    app.setOrganizationDomain("uh.fi")
    app.setApplicationName("DocEditor")
    app.setApplicationVersion(__version__)
    win = DocEditorWindow()
    win.show()
    app.exec_()

if __name__ == '__main__':
    sys.exit(main())
