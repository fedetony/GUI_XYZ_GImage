# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\GuiXYZ_CommandConfigurationDialog.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog_CCD(object):
    def setupUi(self, Dialog_CCD):
        Dialog_CCD.setObjectName("Dialog_CCD")
        Dialog_CCD.resize(605, 439)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog_CCD)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox_CCD = QtWidgets.QGroupBox(Dialog_CCD)
        self.groupBox_CCD.setObjectName("groupBox_CCD")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox_CCD)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter = QtWidgets.QSplitter(self.groupBox_CCD)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.tableWidget_CCD = QtWidgets.QTableWidget(self.splitter)
        self.tableWidget_CCD.setObjectName("tableWidget_CCD")
        self.tableWidget_CCD.setColumnCount(0)
        self.tableWidget_CCD.setRowCount(0)
        self.frame_CCD = QtWidgets.QFrame(self.splitter)
        self.frame_CCD.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_CCD.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_CCD.setObjectName("frame_CCD")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.frame_CCD)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.pushButton_CCD_set_commands = QtWidgets.QPushButton(self.frame_CCD)
        self.pushButton_CCD_set_commands.setObjectName("pushButton_CCD_set_commands")
        self.gridLayout_2.addWidget(self.pushButton_CCD_set_commands, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.groupBox_CCD)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog_CCD)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog_CCD)
        self.buttonBox.accepted.connect(Dialog_CCD.accept)
        self.buttonBox.rejected.connect(Dialog_CCD.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_CCD)

    def retranslateUi(self, Dialog_CCD):
        _translate = QtCore.QCoreApplication.translate
        Dialog_CCD.setWindowTitle(_translate("Dialog_CCD", "Command Configuration Dialog"))
        self.groupBox_CCD.setTitle(_translate("Dialog_CCD", "Command Configuration"))
        self.pushButton_CCD_set_commands.setText(_translate("Dialog_CCD", "Set Commands"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog_CCD = QtWidgets.QDialog()
    ui = Ui_Dialog_CCD()
    ui.setupUi(Dialog_CCD)
    Dialog_CCD.show()
    sys.exit(app.exec_())
