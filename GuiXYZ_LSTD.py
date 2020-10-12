# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\GuiXYZ_LayerSelectToolDialog.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog_LSTD(object):
    def setupUi(self, Dialog_LSTD):
        Dialog_LSTD.setObjectName("Dialog_LSTD")
        Dialog_LSTD.resize(417, 202)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Dialog_LSTD)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBox_LSTD_Layer_Select = QtWidgets.QGroupBox(Dialog_LSTD)
        self.groupBox_LSTD_Layer_Select.setObjectName("groupBox_LSTD_Layer_Select")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_LSTD_Layer_Select)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout_3 = QtWidgets.QGridLayout()
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.label_LSTD_Image_Process = QtWidgets.QLabel(self.groupBox_LSTD_Layer_Select)
        self.label_LSTD_Image_Process.setObjectName("label_LSTD_Image_Process")
        self.gridLayout_3.addWidget(self.label_LSTD_Image_Process, 0, 0, 1, 1)
        self.comboBox_LSTD_Image_Process = QtWidgets.QComboBox(self.groupBox_LSTD_Layer_Select)
        self.comboBox_LSTD_Image_Process.setObjectName("comboBox_LSTD_Image_Process")
        self.gridLayout_3.addWidget(self.comboBox_LSTD_Image_Process, 0, 1, 1, 1)
        self.pushButton_LSTD_Set_Preview = QtWidgets.QPushButton(self.groupBox_LSTD_Layer_Select)
        self.pushButton_LSTD_Set_Preview.setObjectName("pushButton_LSTD_Set_Preview")
        self.gridLayout_3.addWidget(self.pushButton_LSTD_Set_Preview, 1, 1, 1, 1)
        self.checkBox_LSTD_checkall = QtWidgets.QCheckBox(self.groupBox_LSTD_Layer_Select)
        self.checkBox_LSTD_checkall.setObjectName("checkBox_LSTD_checkall")
        self.gridLayout_3.addWidget(self.checkBox_LSTD_checkall, 1, 0, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout_3, 0, 1, 1, 1)
        self.frame = QtWidgets.QFrame(self.groupBox_LSTD_Layer_Select)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout_LSTD_Layers = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout_LSTD_Layers.setObjectName("verticalLayout_LSTD_Layers")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout_LSTD_Layers.addLayout(self.gridLayout)
        self.gridLayout_2.addWidget(self.frame, 0, 0, 1, 1)
        self.verticalLayout_2.addWidget(self.groupBox_LSTD_Layer_Select)
        self.buttonBox_LSTD = QtWidgets.QDialogButtonBox(Dialog_LSTD)
        self.buttonBox_LSTD.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox_LSTD.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox_LSTD.setObjectName("buttonBox_LSTD")
        self.verticalLayout_2.addWidget(self.buttonBox_LSTD)

        self.retranslateUi(Dialog_LSTD)
        self.buttonBox_LSTD.accepted.connect(Dialog_LSTD.accept)
        self.buttonBox_LSTD.rejected.connect(Dialog_LSTD.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_LSTD)

    def retranslateUi(self, Dialog_LSTD):
        _translate = QtCore.QCoreApplication.translate
        Dialog_LSTD.setWindowTitle(_translate("Dialog_LSTD", "Select Layer Tool Dialog"))
        self.groupBox_LSTD_Layer_Select.setTitle(_translate("Dialog_LSTD", "Layer_Select"))
        self.label_LSTD_Image_Process.setText(_translate("Dialog_LSTD", "Image Process"))
        self.pushButton_LSTD_Set_Preview.setText(_translate("Dialog_LSTD", "Set_Preview"))
        self.checkBox_LSTD_checkall.setText(_translate("Dialog_LSTD", "Check All"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog_LSTD = QtWidgets.QDialog()
    ui = Ui_Dialog_LSTD()
    ui.setupUi(Dialog_LSTD)
    Dialog_LSTD.show()
    sys.exit(app.exec_())
