# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file Ui_QGISZupport.ui
# Created with: PyQt4 UI code generator 4.4.4
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_QGISZupport(object):
    def setupUi(self, QGISZupport):
        QGISZupport.setObjectName("QGISZupport")
        QGISZupport.resize(400, 300)
        self.buttonBox = QtGui.QDialogButtonBox(QGISZupport)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")

        self.retranslateUi(QGISZupport)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), QGISZupport.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), QGISZupport.reject)
        QtCore.QMetaObject.connectSlotsByName(QGISZupport)

    def retranslateUi(self, QGISZupport):
        QGISZupport.setWindowTitle(QtGui.QApplication.translate("QGISZupport", "QGISZupport", None, QtGui.QApplication.UnicodeUTF8))
