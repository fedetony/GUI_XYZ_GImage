# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GuiXYZ_VariableButtonDataDialog.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog_VBDD(object):
    def setupUi(self, Dialog_VBDD):
        Dialog_VBDD.setObjectName("Dialog_VBDD")
        Dialog_VBDD.resize(428, 471)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog_VBDD)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox_VBDF = QtWidgets.QGroupBox(Dialog_VBDD)
        self.groupBox_VBDF.setObjectName("groupBox_VBDF")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox_VBDF)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_VBDD_id = QtWidgets.QLabel(self.groupBox_VBDF)
        self.label_VBDD_id.setObjectName("label_VBDD_id")
        self.horizontalLayout_4.addWidget(self.label_VBDD_id)
        self.pushButton_VBDD_Icon = QtWidgets.QPushButton(self.groupBox_VBDF)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("img/Actions-arrow-up-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_VBDD_Icon.setIcon(icon)
        self.pushButton_VBDD_Icon.setObjectName("pushButton_VBDD_Icon")
        self.horizontalLayout_4.addWidget(self.pushButton_VBDD_Icon)
        self.gridLayout.addLayout(self.horizontalLayout_4, 0, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_VBDD_Name = QtWidgets.QLabel(self.groupBox_VBDF)
        self.label_VBDD_Name.setObjectName("label_VBDD_Name")
        self.horizontalLayout.addWidget(self.label_VBDD_Name)
        self.lineEdit_VBDD_Name = QtWidgets.QLineEdit(self.groupBox_VBDF)
        self.lineEdit_VBDD_Name.setObjectName("lineEdit_VBDD_Name")
        self.horizontalLayout.addWidget(self.lineEdit_VBDD_Name)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.groupBox_VBDD_byaction = QtWidgets.QGroupBox(self.groupBox_VBDF)
        self.groupBox_VBDD_byaction.setObjectName("groupBox_VBDD_byaction")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_VBDD_byaction)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_VBDD_CHid = QtWidgets.QLabel(self.groupBox_VBDD_byaction)
        self.label_VBDD_CHid.setObjectName("label_VBDD_CHid")
        self.horizontalLayout_3.addWidget(self.label_VBDD_CHid)
        self.label_VBDD_Force_id = QtWidgets.QLabel(self.groupBox_VBDD_byaction)
        self.label_VBDD_Force_id.setObjectName("label_VBDD_Force_id")
        self.horizontalLayout_3.addWidget(self.label_VBDD_Force_id)
        self.comboBox_VBDD_CHid = QtWidgets.QComboBox(self.groupBox_VBDD_byaction)
        self.comboBox_VBDD_CHid.setObjectName("comboBox_VBDD_CHid")
        self.horizontalLayout_3.addWidget(self.comboBox_VBDD_CHid)
        self.gridLayout_2.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_VBDD_action = QtWidgets.QLabel(self.groupBox_VBDD_byaction)
        self.label_VBDD_action.setObjectName("label_VBDD_action")
        self.horizontalLayout_2.addWidget(self.label_VBDD_action)
        self.comboBox_VBDD_action = QtWidgets.QComboBox(self.groupBox_VBDD_byaction)
        self.comboBox_VBDD_action.setObjectName("comboBox_VBDD_action")
        self.horizontalLayout_2.addWidget(self.comboBox_VBDD_action)
        self.gridLayout_2.addLayout(self.horizontalLayout_2, 3, 0, 1, 1)
        self.tableWidget_VBDD_parameters = QtWidgets.QTableWidget(self.groupBox_VBDD_byaction)
        self.tableWidget_VBDD_parameters.setObjectName("tableWidget_VBDD_parameters")
        self.tableWidget_VBDD_parameters.setColumnCount(0)
        self.tableWidget_VBDD_parameters.setRowCount(0)
        self.gridLayout_2.addWidget(self.tableWidget_VBDD_parameters, 4, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_VBDD_byaction, 2, 0, 1, 1)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_VBDD_Format = QtWidgets.QLabel(self.groupBox_VBDF)
        self.label_VBDD_Format.setObjectName("label_VBDD_Format")
        self.verticalLayout_2.addWidget(self.label_VBDD_Format)
        self.label_VBDD_Result = QtWidgets.QLabel(self.groupBox_VBDF)
        self.label_VBDD_Result.setObjectName("label_VBDD_Result")
        self.verticalLayout_2.addWidget(self.label_VBDD_Result)
        self.gridLayout.addLayout(self.verticalLayout_2, 3, 0, 1, 1)
        self.textEdit_VBDD_Gcode = QtWidgets.QTextEdit(self.groupBox_VBDF)
        self.textEdit_VBDD_Gcode.setObjectName("textEdit_VBDD_Gcode")
        self.gridLayout.addWidget(self.textEdit_VBDD_Gcode, 4, 0, 1, 1)
        self.verticalLayout.addWidget(self.groupBox_VBDF)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog_VBDD)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog_VBDD)
        self.buttonBox.accepted.connect(Dialog_VBDD.accept)
        self.buttonBox.rejected.connect(Dialog_VBDD.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_VBDD)

    def retranslateUi(self, Dialog_VBDD):
        _translate = QtCore.QCoreApplication.translate
        Dialog_VBDD.setWindowTitle(_translate("Dialog_VBDD", "Variable Button Data Dialog"))
        self.groupBox_VBDF.setTitle(_translate("Dialog_VBDD", "Custom Button Data"))
        self.label_VBDD_id.setText(_translate("Dialog_VBDD", "Id:"))
        self.pushButton_VBDD_Icon.setText(_translate("Dialog_VBDD", "Select Icon"))
        self.label_VBDD_Name.setText(_translate("Dialog_VBDD", "Name:"))
        self.groupBox_VBDD_byaction.setTitle(_translate("Dialog_VBDD", "By action"))
        self.label_VBDD_CHid.setText(_translate("Dialog_VBDD", "Force Id"))
        self.label_VBDD_Force_id.setText(_translate("Dialog_VBDD", "Force interface to:"))
        self.label_VBDD_action.setText(_translate("Dialog_VBDD", "Action"))
        self.label_VBDD_Format.setText(_translate("Dialog_VBDD", "Action Format"))
        self.label_VBDD_Result.setText(_translate("Dialog_VBDD", "Action Result"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog_VBDD = QtWidgets.QDialog()
    ui = Ui_Dialog_VBDD()
    ui.setupUi(Dialog_VBDD)
    Dialog_VBDD.show()
    sys.exit(app.exec_())
