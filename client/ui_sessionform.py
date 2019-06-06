# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_sessionform.ui'
#
# Created by: PyQt5 UI code generator 5.10
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SessionForm(object):
    def setupUi(self, SessionForm):
        SessionForm.setObjectName("SessionForm")
        SessionForm.resize(291, 344)
        self.buttonBox = QtWidgets.QDialogButtonBox(SessionForm)
        self.buttonBox.setGeometry(QtCore.QRect(-60, 310, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayoutWidget = QtWidgets.QWidget(SessionForm)
        self.formLayoutWidget.setGeometry(QtCore.QRect(10, 10, 261, 291))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")
        self.technicianNameLabel = QtWidgets.QLabel(self.formLayoutWidget)
        self.technicianNameLabel.setObjectName("technicianNameLabel")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.technicianNameLabel)
        self.technicianNameLineEdit = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.technicianNameLineEdit.setStatusTip("")
        self.technicianNameLineEdit.setObjectName("technicianNameLineEdit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.technicianNameLineEdit)
        self.collectionCodeLabel = QtWidgets.QLabel(self.formLayoutWidget)
        self.collectionCodeLabel.setObjectName("collectionCodeLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.collectionCodeLabel)
        self.collectionCodeComboBox = QtWidgets.QComboBox(self.formLayoutWidget)
        self.collectionCodeComboBox.setObjectName("collectionCodeComboBox")
        self.collectionCodeComboBox.addItem("")
        self.collectionCodeComboBox.addItem("")
        self.collectionCodeComboBox.addItem("")
        self.collectionCodeComboBox.addItem("")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.collectionCodeComboBox)
        self.projectCodeLabel = QtWidgets.QLabel(self.formLayoutWidget)
        self.projectCodeLabel.setObjectName("projectCodeLabel")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.projectCodeLabel)
        self.projectCodeComboBox = QtWidgets.QComboBox(self.formLayoutWidget)
        self.projectCodeComboBox.setObjectName("projectCodeComboBox")
        self.projectCodeComboBox.addItem("")
        self.projectCodeComboBox.addItem("")
        self.projectCodeComboBox.addItem("")
        self.projectCodeComboBox.addItem("")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.projectCodeComboBox)
        self.taxaLabel = QtWidgets.QLabel(self.formLayoutWidget)
        self.taxaLabel.setObjectName("taxaLabel")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.taxaLabel)
        self.taxaLineEdit = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.taxaLineEdit.setStatusTip("")
        self.taxaLineEdit.setObjectName("taxaLineEdit")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.taxaLineEdit)
        self.notesLabel = QtWidgets.QLabel(self.formLayoutWidget)
        self.notesLabel.setObjectName("notesLabel")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.notesLabel)
        self.plainTextNotes = QtWidgets.QPlainTextEdit(self.formLayoutWidget)
        self.plainTextNotes.setObjectName("plainTextNotes")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.plainTextNotes)

        self.retranslateUi(SessionForm)
        self.buttonBox.accepted.connect(SessionForm.accept)
        self.buttonBox.rejected.connect(SessionForm.reject)
        QtCore.QMetaObject.connectSlotsByName(SessionForm)

    def retranslateUi(self, SessionForm):
        _translate = QtCore.QCoreApplication.translate
        SessionForm.setWindowTitle(_translate("SessionForm", "Dialog"))
        self.technicianNameLabel.setText(_translate("SessionForm", "Technician Name"))
        self.collectionCodeLabel.setText(_translate("SessionForm", "Collection Code"))
        self.collectionCodeComboBox.setItemText(0, _translate("SessionForm", "BRIT"))
        self.collectionCodeComboBox.setItemText(1, _translate("SessionForm", "VDB"))
        self.collectionCodeComboBox.setItemText(2, _translate("SessionForm", "NLU"))
        self.collectionCodeComboBox.setItemText(3, _translate("SessionForm", "[other]"))
        self.projectCodeLabel.setText(_translate("SessionForm", "Project Code"))
        self.projectCodeComboBox.setItemText(0, _translate("SessionForm", "TCN-Endless"))
        self.projectCodeComboBox.setItemText(1, _translate("SessionForm", "TCN-Ferns"))
        self.projectCodeComboBox.setItemText(2, _translate("SessionForm", "BRIT-Texas"))
        self.projectCodeComboBox.setItemText(3, _translate("SessionForm", "BRIT-General"))
        self.taxaLabel.setText(_translate("SessionForm", "Taxa"))
        self.notesLabel.setText(_translate("SessionForm", "Notes"))

