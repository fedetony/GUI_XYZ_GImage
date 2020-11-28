# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GuiXYZ_TranslateToolDialog.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog_TTD(object):
    def setupUi(self, Dialog_TTD):
        Dialog_TTD.setObjectName("Dialog_TTD")
        Dialog_TTD.resize(412, 372)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog_TTD)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox_TTD_from = QtWidgets.QGroupBox(Dialog_TTD)
        self.groupBox_TTD_from.setObjectName("groupBox_TTD_from")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_TTD_from)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.pushButton_TTD_Load_Code = QtWidgets.QPushButton(self.groupBox_TTD_from)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("img/open-file-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_TTD_Load_Code.setIcon(icon)
        self.pushButton_TTD_Load_Code.setObjectName("pushButton_TTD_Load_Code")
        self.gridLayout_2.addWidget(self.pushButton_TTD_Load_Code, 1, 2, 1, 1)
        self.label_TTD_File_Loaded = QtWidgets.QLabel(self.groupBox_TTD_from)
        self.label_TTD_File_Loaded.setObjectName("label_TTD_File_Loaded")
        self.gridLayout_2.addWidget(self.label_TTD_File_Loaded, 1, 0, 1, 1)
        self.label_TTD_File_from_ID = QtWidgets.QLabel(self.groupBox_TTD_from)
        self.label_TTD_File_from_ID.setObjectName("label_TTD_File_from_ID")
        self.gridLayout_2.addWidget(self.label_TTD_File_from_ID, 2, 2, 1, 1)
        self.label_TTD_File_from_Type = QtWidgets.QLabel(self.groupBox_TTD_from)
        self.label_TTD_File_from_Type.setObjectName("label_TTD_File_from_Type")
        self.gridLayout_2.addWidget(self.label_TTD_File_from_Type, 2, 0, 1, 1)
        self.checkBox_TTD_FromGcodetxt = QtWidgets.QCheckBox(self.groupBox_TTD_from)
        self.checkBox_TTD_FromGcodetxt.setChecked(True)
        self.checkBox_TTD_FromGcodetxt.setObjectName("checkBox_TTD_FromGcodetxt")
        self.gridLayout_2.addWidget(self.checkBox_TTD_FromGcodetxt, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.groupBox_TTD_from)
        self.groupBox_TTD_to = QtWidgets.QGroupBox(Dialog_TTD)
        self.groupBox_TTD_to.setObjectName("groupBox_TTD_to")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox_TTD_to)
        self.gridLayout.setObjectName("gridLayout")
        self.comboBox_TTD_ID_Code = QtWidgets.QComboBox(self.groupBox_TTD_to)
        self.comboBox_TTD_ID_Code.setObjectName("comboBox_TTD_ID_Code")
        self.gridLayout.addWidget(self.comboBox_TTD_ID_Code, 0, 1, 1, 1)
        self.pushButton_TTD_Save_Code = QtWidgets.QPushButton(self.groupBox_TTD_to)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("img/Floppy-Small-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_TTD_Save_Code.setIcon(icon1)
        self.pushButton_TTD_Save_Code.setObjectName("pushButton_TTD_Save_Code")
        self.gridLayout.addWidget(self.pushButton_TTD_Save_Code, 2, 1, 1, 1)
        self.label_TTD_Saved = QtWidgets.QLabel(self.groupBox_TTD_to)
        self.label_TTD_Saved.setObjectName("label_TTD_Saved")
        self.gridLayout.addWidget(self.label_TTD_Saved, 2, 0, 1, 1)
        self.comboBox_TTD_Type_Code = QtWidgets.QComboBox(self.groupBox_TTD_to)
        self.comboBox_TTD_Type_Code.setObjectName("comboBox_TTD_Type_Code")
        self.gridLayout.addWidget(self.comboBox_TTD_Type_Code, 0, 0, 1, 1)
        self.label_TTD_ID_to_Name = QtWidgets.QLabel(self.groupBox_TTD_to)
        self.label_TTD_ID_to_Name.setObjectName("label_TTD_ID_to_Name")
        self.gridLayout.addWidget(self.label_TTD_ID_to_Name, 1, 1, 1, 1)
        self.verticalLayout.addWidget(self.groupBox_TTD_to)
        self.progressBar_TTD_Buffer = QtWidgets.QProgressBar(Dialog_TTD)
        self.progressBar_TTD_Buffer.setProperty("value", 0)
        self.progressBar_TTD_Buffer.setObjectName("progressBar_TTD_Buffer")
        self.verticalLayout.addWidget(self.progressBar_TTD_Buffer)
        self.progressBar_TTD_State = QtWidgets.QProgressBar(Dialog_TTD)
        self.progressBar_TTD_State.setProperty("value", 0)
        self.progressBar_TTD_State.setObjectName("progressBar_TTD_State")
        self.verticalLayout.addWidget(self.progressBar_TTD_State)
        self.pushButton_TTD_Translate = QtWidgets.QPushButton(Dialog_TTD)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("img/move-icon (1).png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_TTD_Translate.setIcon(icon2)
        self.pushButton_TTD_Translate.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_TTD_Translate.setObjectName("pushButton_TTD_Translate")
        self.verticalLayout.addWidget(self.pushButton_TTD_Translate)
        self.buttonBox_TTD = QtWidgets.QDialogButtonBox(Dialog_TTD)
        self.buttonBox_TTD.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox_TTD.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox_TTD.setObjectName("buttonBox_TTD")
        self.verticalLayout.addWidget(self.buttonBox_TTD)

        self.retranslateUi(Dialog_TTD)
        self.buttonBox_TTD.accepted.connect(Dialog_TTD.accept)
        self.buttonBox_TTD.rejected.connect(Dialog_TTD.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_TTD)

    def retranslateUi(self, Dialog_TTD):
        _translate = QtCore.QCoreApplication.translate
        Dialog_TTD.setWindowTitle(_translate("Dialog_TTD", "Translate Tool Dialog"))
        self.groupBox_TTD_from.setTitle(_translate("Dialog_TTD", "Input"))
        self.pushButton_TTD_Load_Code.setText(_translate("Dialog_TTD", "Load Code"))
        self.label_TTD_File_Loaded.setText(_translate("Dialog_TTD", "TextLabel"))
        self.label_TTD_File_from_ID.setText(_translate("Dialog_TTD", "TextLabel"))
        self.label_TTD_File_from_Type.setText(_translate("Dialog_TTD", "TextLabel"))
        self.checkBox_TTD_FromGcodetxt.setText(_translate("Dialog_TTD", "From Gcode Text"))
        self.groupBox_TTD_to.setTitle(_translate("Dialog_TTD", "Output"))
        self.pushButton_TTD_Save_Code.setText(_translate("Dialog_TTD", "Save Code"))
        self.label_TTD_Saved.setText(_translate("Dialog_TTD", "TextLabel"))
        self.label_TTD_ID_to_Name.setText(_translate("Dialog_TTD", "TextLabel"))
        self.pushButton_TTD_Translate.setText(_translate("Dialog_TTD", "Translate"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog_TTD = QtWidgets.QDialog()
    ui = Ui_Dialog_TTD()
    ui.setupUi(Dialog_TTD)
    Dialog_TTD.show()
    sys.exit(app.exec_())
