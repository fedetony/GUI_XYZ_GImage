# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\GuiXYZ_ResizeToolDialog.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog_RTD(object):
    def setupUi(self, Dialog_RTD):
        Dialog_RTD.setObjectName("Dialog_RTD")
        Dialog_RTD.resize(680, 488)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog_RTD)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox_RTD_Resize = QtWidgets.QGroupBox(Dialog_RTD)
        self.groupBox_RTD_Resize.setObjectName("groupBox_RTD_Resize")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox_RTD_Resize)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.splitter_RTD = QtWidgets.QSplitter(self.groupBox_RTD_Resize)
        self.splitter_RTD.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_RTD.setObjectName("splitter_RTD")
        self.frame_RTD_Commands = QtWidgets.QFrame(self.splitter_RTD)
        self.frame_RTD_Commands.setMaximumSize(QtCore.QSize(310, 16777215))
        self.frame_RTD_Commands.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_RTD_Commands.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_RTD_Commands.setObjectName("frame_RTD_Commands")
        self.gridLayout = QtWidgets.QGridLayout(self.frame_RTD_Commands)
        self.gridLayout.setObjectName("gridLayout")
        self.label_RTD_Frame = QtWidgets.QLabel(self.frame_RTD_Commands)
        self.label_RTD_Frame.setObjectName("label_RTD_Frame")
        self.gridLayout.addWidget(self.label_RTD_Frame, 9, 0, 1, 1)
        self.label_RTD_Machine_pos = QtWidgets.QLabel(self.frame_RTD_Commands)
        self.label_RTD_Machine_pos.setObjectName("label_RTD_Machine_pos")
        self.gridLayout.addWidget(self.label_RTD_Machine_pos, 1, 0, 1, 1)
        self.lineEdit_RTD_Image_Size_W = QtWidgets.QLineEdit(self.frame_RTD_Commands)
        self.lineEdit_RTD_Image_Size_W.setObjectName("lineEdit_RTD_Image_Size_W")
        self.gridLayout.addWidget(self.lineEdit_RTD_Image_Size_W, 7, 1, 1, 1)
        self.lineEdit_RTD_Machine_Size_z = QtWidgets.QLineEdit(self.frame_RTD_Commands)
        self.lineEdit_RTD_Machine_Size_z.setObjectName("lineEdit_RTD_Machine_Size_z")
        self.gridLayout.addWidget(self.lineEdit_RTD_Machine_Size_z, 0, 3, 1, 1)
        self.line_2 = QtWidgets.QFrame(self.frame_RTD_Commands)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.gridLayout.addWidget(self.line_2, 5, 1, 1, 1)
        self.lineEdit_RTD_Machine_pos_y = QtWidgets.QLineEdit(self.frame_RTD_Commands)
        self.lineEdit_RTD_Machine_pos_y.setObjectName("lineEdit_RTD_Machine_pos_y")
        self.gridLayout.addWidget(self.lineEdit_RTD_Machine_pos_y, 1, 2, 1, 1)
        self.label_RTD_Machine_pos_unit = QtWidgets.QLabel(self.frame_RTD_Commands)
        self.label_RTD_Machine_pos_unit.setObjectName("label_RTD_Machine_pos_unit")
        self.gridLayout.addWidget(self.label_RTD_Machine_pos_unit, 1, 4, 1, 1)
        self.line = QtWidgets.QFrame(self.frame_RTD_Commands)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 2, 1, 1, 1)
        self.label_RTD_Canvas_pos = QtWidgets.QLabel(self.frame_RTD_Commands)
        self.label_RTD_Canvas_pos.setObjectName("label_RTD_Canvas_pos")
        self.gridLayout.addWidget(self.label_RTD_Canvas_pos, 3, 0, 1, 1)
        self.lineEdit_RTD_Canvas_Size_H = QtWidgets.QLineEdit(self.frame_RTD_Commands)
        self.lineEdit_RTD_Canvas_Size_H.setObjectName("lineEdit_RTD_Canvas_Size_H")
        self.gridLayout.addWidget(self.lineEdit_RTD_Canvas_Size_H, 4, 2, 1, 1)
        self.lineEdit_RTD_Machine_pos_z = QtWidgets.QLineEdit(self.frame_RTD_Commands)
        self.lineEdit_RTD_Machine_pos_z.setObjectName("lineEdit_RTD_Machine_pos_z")
        self.gridLayout.addWidget(self.lineEdit_RTD_Machine_pos_z, 1, 3, 1, 1)
        self.lineEdit_RTD_Image_pos_x = QtWidgets.QLineEdit(self.frame_RTD_Commands)
        self.lineEdit_RTD_Image_pos_x.setObjectName("lineEdit_RTD_Image_pos_x")
        self.gridLayout.addWidget(self.lineEdit_RTD_Image_pos_x, 6, 1, 1, 1)
        self.lineEdit_RTD_Image_pos_y = QtWidgets.QLineEdit(self.frame_RTD_Commands)
        self.lineEdit_RTD_Image_pos_y.setObjectName("lineEdit_RTD_Image_pos_y")
        self.gridLayout.addWidget(self.lineEdit_RTD_Image_pos_y, 6, 2, 1, 1)
        self.lineEdit_RTD_Canvas_pos_y = QtWidgets.QLineEdit(self.frame_RTD_Commands)
        self.lineEdit_RTD_Canvas_pos_y.setObjectName("lineEdit_RTD_Canvas_pos_y")
        self.gridLayout.addWidget(self.lineEdit_RTD_Canvas_pos_y, 3, 2, 1, 1)
        self.lineEdit_RTD_Canvas_pos_x = QtWidgets.QLineEdit(self.frame_RTD_Commands)
        self.lineEdit_RTD_Canvas_pos_x.setObjectName("lineEdit_RTD_Canvas_pos_x")
        self.gridLayout.addWidget(self.lineEdit_RTD_Canvas_pos_x, 3, 1, 1, 1)
        self.label_RTD_Image_Size = QtWidgets.QLabel(self.frame_RTD_Commands)
        self.label_RTD_Image_Size.setObjectName("label_RTD_Image_Size")
        self.gridLayout.addWidget(self.label_RTD_Image_Size, 7, 0, 1, 1)
        self.lineEdit_RTD_Machine_pos_x = QtWidgets.QLineEdit(self.frame_RTD_Commands)
        self.lineEdit_RTD_Machine_pos_x.setObjectName("lineEdit_RTD_Machine_pos_x")
        self.gridLayout.addWidget(self.lineEdit_RTD_Machine_pos_x, 1, 1, 1, 1)
        self.label_RTD_Canvas_Size = QtWidgets.QLabel(self.frame_RTD_Commands)
        self.label_RTD_Canvas_Size.setObjectName("label_RTD_Canvas_Size")
        self.gridLayout.addWidget(self.label_RTD_Canvas_Size, 4, 0, 1, 1)
        self.lineEdit_RTD_Machine_Size_x = QtWidgets.QLineEdit(self.frame_RTD_Commands)
        self.lineEdit_RTD_Machine_Size_x.setObjectName("lineEdit_RTD_Machine_Size_x")
        self.gridLayout.addWidget(self.lineEdit_RTD_Machine_Size_x, 0, 1, 1, 1)
        self.lineEdit_RTD_Machine_Size_y = QtWidgets.QLineEdit(self.frame_RTD_Commands)
        self.lineEdit_RTD_Machine_Size_y.setObjectName("lineEdit_RTD_Machine_Size_y")
        self.gridLayout.addWidget(self.lineEdit_RTD_Machine_Size_y, 0, 2, 1, 1)
        self.lineEdit_RTD_Canvas_Size_W = QtWidgets.QLineEdit(self.frame_RTD_Commands)
        self.lineEdit_RTD_Canvas_Size_W.setObjectName("lineEdit_RTD_Canvas_Size_W")
        self.gridLayout.addWidget(self.lineEdit_RTD_Canvas_Size_W, 4, 1, 1, 1)
        self.pushButton_RTD_Set_Resized = QtWidgets.QPushButton(self.frame_RTD_Commands)
        self.pushButton_RTD_Set_Resized.setObjectName("pushButton_RTD_Set_Resized")
        self.gridLayout.addWidget(self.pushButton_RTD_Set_Resized, 11, 0, 1, 1)
        self.label_RTD_Machine_Size = QtWidgets.QLabel(self.frame_RTD_Commands)
        self.label_RTD_Machine_Size.setObjectName("label_RTD_Machine_Size")
        self.gridLayout.addWidget(self.label_RTD_Machine_Size, 0, 0, 1, 1)
        self.spinBox_RTD_Frame = QtWidgets.QSpinBox(self.frame_RTD_Commands)
        self.spinBox_RTD_Frame.setMaximum(1)
        self.spinBox_RTD_Frame.setObjectName("spinBox_RTD_Frame")
        self.gridLayout.addWidget(self.spinBox_RTD_Frame, 9, 1, 1, 1)
        self.label_RTD_Canvas_pos_unit = QtWidgets.QLabel(self.frame_RTD_Commands)
        self.label_RTD_Canvas_pos_unit.setObjectName("label_RTD_Canvas_pos_unit")
        self.gridLayout.addWidget(self.label_RTD_Canvas_pos_unit, 3, 3, 1, 1)
        self.lineEdit_RTD_Image_Size_H = QtWidgets.QLineEdit(self.frame_RTD_Commands)
        self.lineEdit_RTD_Image_Size_H.setObjectName("lineEdit_RTD_Image_Size_H")
        self.gridLayout.addWidget(self.lineEdit_RTD_Image_Size_H, 7, 2, 1, 1)
        self.label_RTD_Machine_Size_unit = QtWidgets.QLabel(self.frame_RTD_Commands)
        self.label_RTD_Machine_Size_unit.setObjectName("label_RTD_Machine_Size_unit")
        self.gridLayout.addWidget(self.label_RTD_Machine_Size_unit, 0, 4, 1, 1)
        self.label_RTD_Image_pos = QtWidgets.QLabel(self.frame_RTD_Commands)
        self.label_RTD_Image_pos.setObjectName("label_RTD_Image_pos")
        self.gridLayout.addWidget(self.label_RTD_Image_pos, 6, 0, 1, 1)
        self.label_RTD_Image_pos_unit = QtWidgets.QLabel(self.frame_RTD_Commands)
        self.label_RTD_Image_pos_unit.setObjectName("label_RTD_Image_pos_unit")
        self.gridLayout.addWidget(self.label_RTD_Image_pos_unit, 6, 3, 1, 1)
        self.label_RTD_Image_Size_unit = QtWidgets.QLabel(self.frame_RTD_Commands)
        self.label_RTD_Image_Size_unit.setObjectName("label_RTD_Image_Size_unit")
        self.gridLayout.addWidget(self.label_RTD_Image_Size_unit, 7, 3, 1, 1)
        self.label_RTD_Canvas_Size_unit = QtWidgets.QLabel(self.frame_RTD_Commands)
        self.label_RTD_Canvas_Size_unit.setObjectName("label_RTD_Canvas_Size_unit")
        self.gridLayout.addWidget(self.label_RTD_Canvas_Size_unit, 4, 3, 1, 1)
        self.line_3 = QtWidgets.QFrame(self.frame_RTD_Commands)
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.gridLayout.addWidget(self.line_3, 8, 1, 1, 1)
        self.frame_RTD_Images = QtWidgets.QFrame(self.splitter_RTD)
        self.frame_RTD_Images.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_RTD_Images.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_RTD_Images.setObjectName("frame_RTD_Images")
        self.label_RTD_Canvas = QtWidgets.QLabel(self.frame_RTD_Images)
        self.label_RTD_Canvas.setGeometry(QtCore.QRect(100, 90, 171, 191))
        self.label_RTD_Canvas.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.label_RTD_Canvas.setText("")
        self.label_RTD_Canvas.setPixmap(QtGui.QPixmap("img/Canvas.png"))
        self.label_RTD_Canvas.setScaledContents(True)
        self.label_RTD_Canvas.setObjectName("label_RTD_Canvas")
        self.label_RTD_Image = QtWidgets.QLabel(self.frame_RTD_Images)
        self.label_RTD_Image.setGeometry(QtCore.QRect(200, 130, 47, 13))
        self.label_RTD_Image.setText("")
        self.label_RTD_Image.setPixmap(QtGui.QPixmap("img/PreImage.png"))
        self.label_RTD_Image.setObjectName("label_RTD_Image")
        self.label_RTD_Machine = QtWidgets.QLabel(self.frame_RTD_Images)
        self.label_RTD_Machine.setGeometry(QtCore.QRect(20, 140, 260, 260))
        self.label_RTD_Machine.setFrameShape(QtWidgets.QFrame.WinPanel)
        self.label_RTD_Machine.setText("")
        self.label_RTD_Machine.setPixmap(QtGui.QPixmap("img/Machine.png"))
        self.label_RTD_Machine.setScaledContents(True)
        self.label_RTD_Machine.setObjectName("label_RTD_Machine")
        self.label_RTD_Machine_Point = QtWidgets.QLabel(self.frame_RTD_Images)
        self.label_RTD_Machine_Point.setGeometry(QtCore.QRect(20, 370, 30, 30))
        self.label_RTD_Machine_Point.setText("")
        self.label_RTD_Machine_Point.setPixmap(QtGui.QPixmap("img/MachinePoint.png"))
        self.label_RTD_Machine_Point.setScaledContents(True)
        self.label_RTD_Machine_Point.setObjectName("label_RTD_Machine_Point")
        self.label_RTD_Machine.raise_()
        self.label_RTD_Canvas.raise_()
        self.label_RTD_Image.raise_()
        self.label_RTD_Machine_Point.raise_()
        self.verticalLayout_2.addWidget(self.splitter_RTD)
        self.verticalLayout.addWidget(self.groupBox_RTD_Resize)
        self.buttonBox_RTD = QtWidgets.QDialogButtonBox(Dialog_RTD)
        self.buttonBox_RTD.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox_RTD.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox_RTD.setObjectName("buttonBox_RTD")
        self.verticalLayout.addWidget(self.buttonBox_RTD)

        self.retranslateUi(Dialog_RTD)
        self.buttonBox_RTD.accepted.connect(Dialog_RTD.accept)
        self.buttonBox_RTD.rejected.connect(Dialog_RTD.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_RTD)

    def retranslateUi(self, Dialog_RTD):
        _translate = QtCore.QCoreApplication.translate
        Dialog_RTD.setWindowTitle(_translate("Dialog_RTD", "Resize Tool Dialog"))
        self.groupBox_RTD_Resize.setTitle(_translate("Dialog_RTD", "Resize Tool"))
        self.label_RTD_Frame.setText(_translate("Dialog_RTD", "Frame Image"))
        self.label_RTD_Machine_pos.setText(_translate("Dialog_RTD", "Robot_XYZ"))
        self.label_RTD_Machine_pos_unit.setText(_translate("Dialog_RTD", "mm"))
        self.label_RTD_Canvas_pos.setText(_translate("Dialog_RTD", "Canvas Position"))
        self.label_RTD_Image_Size.setText(_translate("Dialog_RTD", "Image Size"))
        self.label_RTD_Canvas_Size.setText(_translate("Dialog_RTD", "Canvas Size"))
        self.pushButton_RTD_Set_Resized.setText(_translate("Dialog_RTD", "Set Position Info"))
        self.label_RTD_Machine_Size.setText(_translate("Dialog_RTD", "Machine Size"))
        self.label_RTD_Canvas_pos_unit.setText(_translate("Dialog_RTD", "mm"))
        self.label_RTD_Machine_Size_unit.setText(_translate("Dialog_RTD", "mm"))
        self.label_RTD_Image_pos.setText(_translate("Dialog_RTD", "Image Position"))
        self.label_RTD_Image_pos_unit.setText(_translate("Dialog_RTD", "mm"))
        self.label_RTD_Image_Size_unit.setText(_translate("Dialog_RTD", "mm"))
        self.label_RTD_Canvas_Size_unit.setText(_translate("Dialog_RTD", "mm"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog_RTD = QtWidgets.QDialog()
    ui = Ui_Dialog_RTD()
    ui.setupUi(Dialog_RTD)
    Dialog_RTD.show()
    sys.exit(app.exec_())
