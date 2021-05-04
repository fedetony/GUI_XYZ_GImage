# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GuiXYZ_VariableButtonDialog.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog_VBD(object):
    def setupUi(self, Dialog_VBD):
        Dialog_VBD.setObjectName("Dialog_VBD")
        Dialog_VBD.resize(761, 591)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog_VBD)
        self.verticalLayout.setContentsMargins(2, 2, 2, 9)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox_VBD = QtWidgets.QGroupBox(Dialog_VBD)
        self.groupBox_VBD.setObjectName("groupBox_VBD")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.groupBox_VBD)
        self.horizontalLayout.setContentsMargins(5, 5, 5, 5)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QtWidgets.QSplitter(self.groupBox_VBD)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.groupBox_VBD_Buttons = QtWidgets.QGroupBox(self.splitter)
        self.groupBox_VBD_Buttons.setMaximumSize(QtCore.QSize(150, 16777215))
        self.groupBox_VBD_Buttons.setObjectName("groupBox_VBD_Buttons")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox_VBD_Buttons)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.pushButton_VBD_ButtonAdd = QtWidgets.QPushButton(self.groupBox_VBD_Buttons)
        self.pushButton_VBD_ButtonAdd.setObjectName("pushButton_VBD_ButtonAdd")
        self.verticalLayout_2.addWidget(self.pushButton_VBD_ButtonAdd)
        self.pushButton_VBD_ButtonEdit = QtWidgets.QPushButton(self.groupBox_VBD_Buttons)
        self.pushButton_VBD_ButtonEdit.setObjectName("pushButton_VBD_ButtonEdit")
        self.verticalLayout_2.addWidget(self.pushButton_VBD_ButtonEdit)
        self.pushButton_VBD_ButtonClone = QtWidgets.QPushButton(self.groupBox_VBD_Buttons)
        self.pushButton_VBD_ButtonClone.setObjectName("pushButton_VBD_ButtonClone")
        self.verticalLayout_2.addWidget(self.pushButton_VBD_ButtonClone)
        self.pushButton_VBD_ButtonRemove = QtWidgets.QPushButton(self.groupBox_VBD_Buttons)
        self.pushButton_VBD_ButtonRemove.setObjectName("pushButton_VBD_ButtonRemove")
        self.verticalLayout_2.addWidget(self.pushButton_VBD_ButtonRemove)
        self.gridLayout.addLayout(self.verticalLayout_2, 0, 0, 1, 1)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.pushButton_VBD_Save = QtWidgets.QPushButton(self.groupBox_VBD_Buttons)
        self.pushButton_VBD_Save.setObjectName("pushButton_VBD_Save")
        self.verticalLayout_3.addWidget(self.pushButton_VBD_Save)
        self.pushButton_VBD_Load = QtWidgets.QPushButton(self.groupBox_VBD_Buttons)
        self.pushButton_VBD_Load.setObjectName("pushButton_VBD_Load")
        self.verticalLayout_3.addWidget(self.pushButton_VBD_Load)
        self.gridLayout.addLayout(self.verticalLayout_3, 1, 0, 1, 1)
        self.frame_VBD_var = QtWidgets.QFrame(self.splitter)
        self.frame_VBD_var.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_VBD_var.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_VBD_var.setObjectName("frame_VBD_var")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.frame_VBD_var)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.verticalLayout_4.addLayout(self.gridLayout_2)
        self.horizontalLayout.addWidget(self.splitter)
        self.verticalLayout.addWidget(self.groupBox_VBD)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog_VBD)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog_VBD)
        self.buttonBox.accepted.connect(Dialog_VBD.accept)
        self.buttonBox.rejected.connect(Dialog_VBD.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_VBD)

    def retranslateUi(self, Dialog_VBD):
        _translate = QtCore.QCoreApplication.translate
        Dialog_VBD.setWindowTitle(_translate("Dialog_VBD", "Variable Button Dialog"))
        self.groupBox_VBD.setTitle(_translate("Dialog_VBD", "Custom Buttons"))
        self.groupBox_VBD_Buttons.setTitle(_translate("Dialog_VBD", "Buttons"))
        self.pushButton_VBD_ButtonAdd.setText(_translate("Dialog_VBD", "Add"))
        self.pushButton_VBD_ButtonEdit.setText(_translate("Dialog_VBD", "Edit"))
        self.pushButton_VBD_ButtonClone.setText(_translate("Dialog_VBD", "Clone"))
        self.pushButton_VBD_ButtonRemove.setText(_translate("Dialog_VBD", "Remove"))
        self.pushButton_VBD_Save.setText(_translate("Dialog_VBD", "Save"))
        self.pushButton_VBD_Load.setText(_translate("Dialog_VBD", "Load"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog_VBD = QtWidgets.QDialog()
    ui = Ui_Dialog_VBD()
    ui.setupUi(Dialog_VBD)
    Dialog_VBD.show()
    sys.exit(app.exec_())
