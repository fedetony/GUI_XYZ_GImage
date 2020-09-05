# -*- coding: utf-8 -*-
"""
Created on 16.06.2020
Python 3.7 pyQt5
@author: F.Garcia
"""
# Form implementation generated from reading ui file 'GuiXYZ_V1.ui'
#
# Created by: PyQt5 UI code generator 5.13.0


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox,QAction
from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QTextEdit
from PyQt5.QtGui import QColor, QPainter, QTextFormat

import sys
import glob
import serial

import datetime
import time
import csv
import re
import io #TextIOWrapper
import binascii
import logging
import queue

import threading
from xyz_grbl_ThreadNC import XYZGrbl
#import atexit
#import keyboard for keyboard inputs





class QLineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class QCodeEditor(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = QLineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)

    def lineNumberAreaWidth(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)

        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        # Just to make sure I use the right font
        height = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.lineNumberArea.width(), height, Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1



log = logging.getLogger()
log.setLevel(logging.INFO)
class MyWindow(QtWidgets.QMainWindow):
    def closeEvent(self,event):
        result = QtWidgets.QMessageBox.question(self,
                      "Confirm Exit...",
                      "Are you sure you want to exit ?",
                      QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
        event.ignore()

        if result == QtWidgets.QMessageBox.Yes:
            
            #ui.App_Close_Event()
            ui.killer_event.set()
            event.accept()

class Dialogs(QWidget):
    def __init__(self):
        super().__init__()
        self.options = QFileDialog.Options()
        self.options |= QFileDialog.DontUseNativeDialog
        self.dir=""
    def get_filter(self,filter):
        if filter==0:
            self.filters="All Files (*);;Gcode Files (*.gcode)"
            self.selected_filter = "Gcode Files (*.gcode)"
        elif filter==1:
            self.filters="All Files (*);;Images (*.png *.xpm *.jpg *.bmp)"
            self.selected_filter = "Images (*.png *.xpm *.jpg *.bmp)"
        elif filter==2:
            self.filters="All Files (*);;Text Files (*.txt)"
            self.selected_filter = "Text Files (*.txt)"
        else:
            self.filters="All Files (*)"
            self.selected_filter = "All Files (*)"    

    def openFileNameDialog(self,filter=0):
                
        #dir = self.sourceDir
        self.get_filter(filter)        
        
        fileObj = QFileDialog.getOpenFileName(self, "Open File dialog ", self.dir, self.filters, self.selected_filter, options=self.options)
        fileName, _ = fileObj
        if fileName:
            return fileName
        else:
            return None    
    
    def openFileNamesDialog(self,filter=0):
        self.get_filter(filter) 
        files, _ = QFileDialog.getOpenFileNames(self, "Open File Names Dialog", self.dir, self.filters, self.selected_filter, options=self.options)
        if files:
            return files
        else:
            return None    
    
    def saveFileDialog(self,filter=0): #";;Text Files (*.txt)"       
        self.get_filter(filter)         
        fileName, _ = QFileDialog.getSaveFileName(self, "Save File dialog ", self.dir, self.filters, self.selected_filter, options=self.options)
        if fileName:
            return fileName
        else:
            return None



class Ui_MainWindow(object):
    def __init__(self, *args, **kwargs):
        super(Ui_MainWindow, self).__init__(*args, **kwargs)

    def setupUi(self, MainWindow):      
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(564, 618)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.textEdit_Logger = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit_Logger.setGeometry(QtCore.QRect(10, 480, 481, 101))
        self.textEdit_Logger.setObjectName("textEdit_Logger")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(0, 0, 561, 481))
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.groupBoxConnect = QtWidgets.QGroupBox(self.tab)
        self.groupBoxConnect.setGeometry(QtCore.QRect(0, 10, 311, 101))
        self.groupBoxConnect.setObjectName("groupBoxConnect")
        self.comboBox_COM = QtWidgets.QComboBox(self.groupBoxConnect)
        self.comboBox_COM.setGeometry(QtCore.QRect(150, 10, 69, 22))
        self.comboBox_COM.setObjectName("comboBox_COM")
        self.pushButton_Refresh = QtWidgets.QPushButton(self.groupBoxConnect)
        self.pushButton_Refresh.setGeometry(QtCore.QRect(10, 70, 75, 23))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("img/Actions-view-refresh-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_Refresh.setIcon(icon)
        self.pushButton_Refresh.setObjectName("pushButton_Refresh")
        self.comboBox_ConnSpeed = QtWidgets.QComboBox(self.groupBoxConnect)
        self.comboBox_ConnSpeed.setGeometry(QtCore.QRect(150, 40, 69, 22))
        self.comboBox_ConnSpeed.setCurrentText("")
        self.comboBox_ConnSpeed.setObjectName("comboBox_ConnSpeed")
        self.label_COM = QtWidgets.QLabel(self.groupBoxConnect)
        self.label_COM.setGeometry(QtCore.QRect(10, 20, 47, 13))
        self.label_COM.setObjectName("label_COM")
        self.label_ConnSpeed = QtWidgets.QLabel(self.groupBoxConnect)
        self.label_ConnSpeed.setGeometry(QtCore.QRect(10, 40, 111, 16))
        self.label_ConnSpeed.setObjectName("label_ConnSpeed")
        self.pushButton_Connect = QtWidgets.QPushButton(self.groupBoxConnect)
        self.pushButton_Connect.setGeometry(QtCore.QRect(210, 70, 91, 23))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("img/connect-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_Connect.setIcon(icon1)
        self.pushButton_Connect.setObjectName("pushButton_Connect")
        self.label_ConnectedStatus = QtWidgets.QLabel(self.groupBoxConnect)
        self.label_ConnectedStatus.setEnabled(True)
        self.label_ConnectedStatus.setGeometry(QtCore.QRect(240, 10, 51, 51))
        self.label_ConnectedStatus.setText("")
        self.label_ConnectedStatus.setPixmap(QtGui.QPixmap("img/connect-icon.png"))
        self.label_ConnectedStatus.setScaledContents(True)
        self.label_ConnectedStatus.setObjectName("label_ConnectedStatus")
        self.groupBox_XYZ = QtWidgets.QGroupBox(self.tab)
        self.groupBox_XYZ.setEnabled(False)
        self.groupBox_XYZ.setGeometry(QtCore.QRect(0, 110, 551, 341))
        self.groupBox_XYZ.setObjectName("groupBox_XYZ")
        self.pushButton_YUp = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_YUp.setGeometry(QtCore.QRect(60, 30, 51, 51))
        self.pushButton_YUp.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("img/Actions-go-Up-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_YUp.setIcon(icon2)
        self.pushButton_YUp.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_YUp.setObjectName("pushButton_YUp")
        self.pushButton_XLeft = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_XLeft.setGeometry(QtCore.QRect(10, 80, 51, 51))
        self.pushButton_XLeft.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("img/Actions-go-Left-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_XLeft.setIcon(icon3)
        self.pushButton_XLeft.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_XLeft.setObjectName("pushButton_XLeft")
        self.pushButton_XRight = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_XRight.setGeometry(QtCore.QRect(110, 80, 51, 51))
        self.pushButton_XRight.setText("")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("img/Actions-go-next-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_XRight.setIcon(icon4)
        self.pushButton_XRight.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_XRight.setObjectName("pushButton_XRight")
        self.pushButton_YDown = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_YDown.setGeometry(QtCore.QRect(60, 130, 51, 51))
        self.pushButton_YDown.setText("")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("img/Actions-go-Down-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_YDown.setIcon(icon5)
        self.pushButton_YDown.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_YDown.setObjectName("pushButton_YDown")
        self.pushButton_ZUp = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_ZUp.setGeometry(QtCore.QRect(170, 30, 51, 51))
        self.pushButton_ZUp.setText("")
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap("img/Actions-go-next-view-icon_ZUp.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_ZUp.setIcon(icon6)
        self.pushButton_ZUp.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_ZUp.setObjectName("pushButton_ZUp")
        self.pushButton_ZDown = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_ZDown.setGeometry(QtCore.QRect(170, 130, 51, 51))
        self.pushButton_ZDown.setText("")
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap("img/Actions-go-next-view-icon_Zdown.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_ZDown.setIcon(icon7)
        self.pushButton_ZDown.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_ZDown.setObjectName("pushButton_ZDown")
        self.lineEdit_X = QtWidgets.QLineEdit(self.groupBox_XYZ)
        self.lineEdit_X.setGeometry(QtCore.QRect(40, 220, 113, 20))
        self.lineEdit_X.setObjectName("lineEdit_X")
        self.lineEdit_Y = QtWidgets.QLineEdit(self.groupBox_XYZ)
        self.lineEdit_Y.setGeometry(QtCore.QRect(40, 250, 113, 20))
        self.lineEdit_Y.setObjectName("lineEdit_Y")
        self.lineEdit_Z = QtWidgets.QLineEdit(self.groupBox_XYZ)
        self.lineEdit_Z.setGeometry(QtCore.QRect(40, 280, 113, 20))
        self.lineEdit_Z.setObjectName("lineEdit_Z")
        self.label_Xpos = QtWidgets.QLabel(self.groupBox_XYZ)
        self.label_Xpos.setGeometry(QtCore.QRect(20, 220, 47, 13))
        self.label_Xpos.setObjectName("label_Xpos")
        self.label_Ypos = QtWidgets.QLabel(self.groupBox_XYZ)
        self.label_Ypos.setGeometry(QtCore.QRect(20, 250, 47, 13))
        self.label_Ypos.setObjectName("label_Ypos")
        self.label_Zpos = QtWidgets.QLabel(self.groupBox_XYZ)
        self.label_Zpos.setGeometry(QtCore.QRect(20, 280, 47, 13))
        self.label_Zpos.setObjectName("label_Zpos")
        self.groupBox_actPosition = QtWidgets.QGroupBox(self.groupBox_XYZ)
        self.groupBox_actPosition.setGeometry(QtCore.QRect(430, 20, 111, 191))
        self.groupBox_actPosition.setObjectName("groupBox_actPosition")
        self.pushButton_SetPos = QtWidgets.QPushButton(self.groupBox_actPosition)
        self.pushButton_SetPos.setGeometry(QtCore.QRect(10, 120, 91, 61))
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap("img/Map-Marker-Push-Pin-1-Right-Chartreuse-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_SetPos.setIcon(icon8)
        self.pushButton_SetPos.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_SetPos.setObjectName("pushButton_SetPos")
        self.label_ZactPos = QtWidgets.QLabel(self.groupBox_actPosition)
        self.label_ZactPos.setGeometry(QtCore.QRect(20, 90, 34, 13))
        self.label_ZactPos.setObjectName("label_ZactPos")
        self.label_YactPos = QtWidgets.QLabel(self.groupBox_actPosition)
        self.label_YactPos.setGeometry(QtCore.QRect(20, 60, 34, 13))
        self.label_YactPos.setObjectName("label_YactPos")
        self.label_XactPos = QtWidgets.QLabel(self.groupBox_actPosition)
        self.label_XactPos.setGeometry(QtCore.QRect(20, 30, 34, 13))
        self.label_XactPos.setObjectName("label_XactPos")
        self.pushButton_Go = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_Go.setGeometry(QtCore.QRect(184, 240, 81, 81))
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap("img/Alarm-Tick-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_Go.setIcon(icon9)
        self.pushButton_Go.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_Go.setObjectName("pushButton_Go")
        self.pushButton_Stop = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_Stop.setGeometry(QtCore.QRect(290, 240, 91, 81))
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap("img/Button-Pause-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_Stop.setIcon(icon10)
        self.pushButton_Stop.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_Stop.setObjectName("pushButton_Stop")
        self.pushButton_Home = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_Home.setGeometry(QtCore.QRect(440, 270, 91, 23))
        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap("img/Actions-go-home-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_Home.setIcon(icon11)
        self.pushButton_Home.setObjectName("pushButton_Home")
        self.pushButton_Reset = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_Reset.setGeometry(QtCore.QRect(440, 300, 91, 23))
        icon12 = QtGui.QIcon()
        icon12.addPixmap(QtGui.QPixmap("img/Reset-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_Reset.setIcon(icon12)
        self.pushButton_Reset.setObjectName("pushButton_Reset")
        self.groupBox_DeltaMove = QtWidgets.QGroupBox(self.groupBox_XYZ)
        self.groupBox_DeltaMove.setGeometry(QtCore.QRect(340, 60, 91, 101))
        self.groupBox_DeltaMove.setObjectName("groupBox_DeltaMove")
        self.label_DeltaZ = QtWidgets.QLabel(self.groupBox_DeltaMove)
        self.label_DeltaZ.setGeometry(QtCore.QRect(10, 70, 16, 20))
        self.label_DeltaZ.setObjectName("label_DeltaZ")
        self.lineEdit_DeltaY = QtWidgets.QLineEdit(self.groupBox_DeltaMove)
        self.lineEdit_DeltaY.setGeometry(QtCore.QRect(20, 46, 61, 20))
        self.lineEdit_DeltaY.setObjectName("lineEdit_DeltaY")
        self.lineEdit_DeltaX = QtWidgets.QLineEdit(self.groupBox_DeltaMove)
        self.lineEdit_DeltaX.setGeometry(QtCore.QRect(20, 20, 61, 20))
        self.lineEdit_DeltaX.setObjectName("lineEdit_DeltaX")
        self.lineEdit_DeltaZ = QtWidgets.QLineEdit(self.groupBox_DeltaMove)
        self.lineEdit_DeltaZ.setGeometry(QtCore.QRect(20, 72, 61, 20))
        self.lineEdit_DeltaZ.setObjectName("lineEdit_DeltaZ")
        self.label_DeltaX = QtWidgets.QLabel(self.groupBox_DeltaMove)
        self.label_DeltaX.setGeometry(QtCore.QRect(10, 20, 6, 20))
        self.label_DeltaX.setObjectName("label_DeltaX")
        self.label_DeltaY = QtWidgets.QLabel(self.groupBox_DeltaMove)
        self.label_DeltaY.setGeometry(QtCore.QRect(10, 50, 16, 16))
        self.label_DeltaY.setObjectName("label_DeltaY")
        self.label_Feedrate = QtWidgets.QLabel(self.groupBox_XYZ)
        self.label_Feedrate.setGeometry(QtCore.QRect(20, 310, 47, 13))
        self.label_Feedrate.setObjectName("label_Feedrate")
        self.lineEdit_Feedrate = QtWidgets.QLineEdit(self.groupBox_XYZ)
        self.lineEdit_Feedrate.setGeometry(QtCore.QRect(40, 310, 113, 20))
        self.lineEdit_Feedrate.setObjectName("lineEdit_Feedrate")
        self.pushButton_CleanAlarm = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_CleanAlarm.setGeometry(QtCore.QRect(440, 240, 91, 23))
        icon13 = QtGui.QIcon()
        icon13.addPixmap(QtGui.QPixmap("img/Clear-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_CleanAlarm.setIcon(icon13)
        self.pushButton_CleanAlarm.setObjectName("pushButton_CleanAlarm")
        self.pushButton_XYRU = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_XYRU.setGeometry(QtCore.QRect(110, 30, 51, 51))
        self.pushButton_XYRU.setText("")
        icon14 = QtGui.QIcon()
        icon14.addPixmap(QtGui.QPixmap("img/Actions-go-next-icon-DiagRU.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_XYRU.setIcon(icon14)
        self.pushButton_XYRU.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_XYRU.setObjectName("pushButton_XYRU")
        self.pushButton_XYLU = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_XYLU.setGeometry(QtCore.QRect(10, 30, 51, 51))
        self.pushButton_XYLU.setText("")
        icon15 = QtGui.QIcon()
        icon15.addPixmap(QtGui.QPixmap("img/Actions-go-next-icon-DiagLU.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_XYLU.setIcon(icon15)
        self.pushButton_XYLU.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_XYLU.setObjectName("pushButton_XYLU")
        self.pushButton_XYRD = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_XYRD.setGeometry(QtCore.QRect(110, 130, 51, 51))
        self.pushButton_XYRD.setText("")
        icon16 = QtGui.QIcon()
        icon16.addPixmap(QtGui.QPixmap("img/Actions-go-next-icon-DiagRD.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_XYRD.setIcon(icon16)
        self.pushButton_XYRD.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_XYRD.setObjectName("pushButton_XYRD")
        self.pushButton_XYLD = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_XYLD.setGeometry(QtCore.QRect(10, 130, 51, 51))
        self.pushButton_XYLD.setText("")
        icon17 = QtGui.QIcon()
        icon17.addPixmap(QtGui.QPixmap("img/Actions-go-next-icon-DiagLD.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_XYLD.setIcon(icon17)
        self.pushButton_XYLD.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_XYLD.setObjectName("pushButton_XYLD")
        self.pushButton_XZLU = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_XZLU.setGeometry(QtCore.QRect(230, 10, 51, 51))
        self.pushButton_XZLU.setText("")
        icon18 = QtGui.QIcon()
        icon18.addPixmap(QtGui.QPixmap("img/Actions-go-next-view-icon_DiagLU.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_XZLU.setIcon(icon18)
        self.pushButton_XZLU.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_XZLU.setObjectName("pushButton_XZLU")
        self.pushButton_XZRU = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_XZRU.setGeometry(QtCore.QRect(280, 10, 51, 51))
        self.pushButton_XZRU.setText("")
        icon19 = QtGui.QIcon()
        icon19.addPixmap(QtGui.QPixmap("img/Actions-go-next-view-icon_DiagRU.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_XZRU.setIcon(icon19)
        self.pushButton_XZRU.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_XZRU.setObjectName("pushButton_XZRU")
        self.pushButton_XZLD = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_XZLD.setGeometry(QtCore.QRect(230, 60, 51, 51))
        self.pushButton_XZLD.setText("")
        icon20 = QtGui.QIcon()
        icon20.addPixmap(QtGui.QPixmap("img/Actions-go-next-view-icon_DiagLD.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_XZLD.setIcon(icon20)
        self.pushButton_XZLD.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_XZLD.setObjectName("pushButton_XZLD")
        self.pushButton_XZRD = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_XZRD.setGeometry(QtCore.QRect(280, 60, 51, 51))
        self.pushButton_XZRD.setText("")
        icon21 = QtGui.QIcon()
        icon21.addPixmap(QtGui.QPixmap("img/Actions-go-next-view-icon_DiagRD.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_XZRD.setIcon(icon21)
        self.pushButton_XZRD.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_XZRD.setObjectName("pushButton_XZRD")
        self.label_XZ = QtWidgets.QLabel(self.groupBox_XYZ)
        self.label_XZ.setGeometry(QtCore.QRect(270, 50, 31, 20))
        self.label_XZ.setObjectName("label_XZ")
        self.label_Z = QtWidgets.QLabel(self.groupBox_XYZ)
        self.label_Z.setGeometry(QtCore.QRect(190, 100, 47, 13))
        self.label_Z.setObjectName("label_Z")
        self.label_XY = QtWidgets.QLabel(self.groupBox_XYZ)
        self.label_XY.setGeometry(QtCore.QRect(80, 100, 47, 13))
        self.label_XY.setObjectName("label_XY")
        self.pushButton_YZLU = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_YZLU.setGeometry(QtCore.QRect(230, 120, 51, 51))
        self.pushButton_YZLU.setText("")
        self.pushButton_YZLU.setIcon(icon18)
        self.pushButton_YZLU.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_YZLU.setObjectName("pushButton_YZLU")
        self.pushButton_YZLD = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_YZLD.setGeometry(QtCore.QRect(230, 170, 51, 51))
        self.pushButton_YZLD.setText("")
        self.pushButton_YZLD.setIcon(icon20)
        self.pushButton_YZLD.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_YZLD.setObjectName("pushButton_YZLD")
        self.pushButton_YZRU = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_YZRU.setGeometry(QtCore.QRect(280, 120, 51, 51))
        self.pushButton_YZRU.setText("")
        self.pushButton_YZRU.setIcon(icon19)
        self.pushButton_YZRU.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_YZRU.setObjectName("pushButton_YZRU")
        self.pushButton_YZRD = QtWidgets.QPushButton(self.groupBox_XYZ)
        self.pushButton_YZRD.setGeometry(QtCore.QRect(280, 170, 51, 51))
        self.pushButton_YZRD.setText("")
        self.pushButton_YZRD.setIcon(icon21)
        self.pushButton_YZRD.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_YZRD.setObjectName("pushButton_YZRD")
        self.label_YZ = QtWidgets.QLabel(self.groupBox_XYZ)
        self.label_YZ.setGeometry(QtCore.QRect(270, 160, 51, 20))
        self.label_YZ.setObjectName("label_YZ")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tableWidget_Config = QtWidgets.QTableWidget(self.tab_2)
        self.tableWidget_Config.setGeometry(QtCore.QRect(10, 30, 451, 411))
        self.tableWidget_Config.setObjectName("tableWidget_Config")
        self.tableWidget_Config.setColumnCount(0)
        self.tableWidget_Config.setRowCount(0)
        self.pushButton_SetConfig = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_SetConfig.setGeometry(QtCore.QRect(464, 390, 91, 51))
        self.pushButton_SetConfig.setIcon(icon9)
        self.pushButton_SetConfig.setObjectName("pushButton_SetConfig")
        self.lineEdit_ConfigValue = QtWidgets.QLineEdit(self.tab_2)
        self.lineEdit_ConfigValue.setGeometry(QtCore.QRect(110, 0, 91, 20))
        self.lineEdit_ConfigValue.setObjectName("lineEdit_ConfigValue")
        self.comboBox_ConfigItem = QtWidgets.QComboBox(self.tab_2)
        self.comboBox_ConfigItem.setGeometry(QtCore.QRect(10, 0, 91, 21))
        self.comboBox_ConfigItem.setObjectName("comboBox_ConfigItem")
        self.label_ConfigInfo = QtWidgets.QLabel(self.tab_2)
        self.label_ConfigInfo.setGeometry(QtCore.QRect(210, 0, 47, 16))
        self.label_ConfigInfo.setObjectName("label_ConfigInfo")
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.groupBox_Gcode = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_Gcode.setGeometry(QtCore.QRect(0, 10, 541, 61))
        self.groupBox_Gcode.setObjectName("groupBox_Gcode")
        self.lineEdit_Gcode = QtWidgets.QLineEdit(self.groupBox_Gcode)
        self.lineEdit_Gcode.setGeometry(QtCore.QRect(10, 20, 441, 20))
        self.lineEdit_Gcode.setObjectName("lineEdit_Gcode")
        self.pushButton_Gcodesend = QtWidgets.QPushButton(self.groupBox_Gcode)
        self.pushButton_Gcodesend.setGeometry(QtCore.QRect(460, 20, 75, 23))
        self.pushButton_Gcodesend.setObjectName("pushButton_Gcodesend")
        self.groupBox_GcodeScript = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_GcodeScript.setGeometry(QtCore.QRect(0, 70, 541, 381))
        self.groupBox_GcodeScript.setObjectName("groupBox_GcodeScript")
        self.pushButton_LoadGcode = QtWidgets.QPushButton(self.groupBox_GcodeScript)
        self.pushButton_LoadGcode.setGeometry(QtCore.QRect(440, 40, 91, 23))
        icon22 = QtGui.QIcon()
        icon22.addPixmap(QtGui.QPixmap("img/open-file-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_LoadGcode.setIcon(icon22)
        self.pushButton_LoadGcode.setObjectName("pushButton_LoadGcode")
        self.PushButton_RunGcodeScript = QtWidgets.QPushButton(self.groupBox_GcodeScript)
        self.PushButton_RunGcodeScript.setGeometry(QtCore.QRect(454, 350, 81, 23))
        self.PushButton_RunGcodeScript.setObjectName("PushButton_RunGcodeScript")
        self.checkBox_Gcode = QtWidgets.QCheckBox(self.groupBox_GcodeScript)
        self.checkBox_Gcode.setGeometry(QtCore.QRect(450, 320, 91, 20))
        self.checkBox_Gcode.setObjectName("checkBox_Gcode")
        self.pushButton_SaveGcode = QtWidgets.QPushButton(self.groupBox_GcodeScript)
        self.pushButton_SaveGcode.setGeometry(QtCore.QRect(440, 70, 91, 23))
        icon23 = QtGui.QIcon()
        icon23.addPixmap(QtGui.QPixmap("img/Floppy-Small-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_SaveGcode.setIcon(icon23)
        self.pushButton_SaveGcode.setObjectName("pushButton_SaveGcode")
        self.plaintextEdit_GcodeScript = QtWidgets.QPlainTextEdit(self.groupBox_GcodeScript)
        self.plaintextEdit_GcodeScript.setGeometry(QtCore.QRect(10, 20, 421, 351))
        self.plaintextEdit_GcodeScript.setObjectName("plaintextEdit_GcodeScript")
        self.frame_GcodePauseStop = QtWidgets.QFrame(self.groupBox_GcodeScript)
        self.frame_GcodePauseStop.setGeometry(QtCore.QRect(430, 170, 111, 111))
        self.frame_GcodePauseStop.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_GcodePauseStop.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_GcodePauseStop.setObjectName("frame_GcodePauseStop")
        self.pushButton_Hold_Start_Gcode = QtWidgets.QPushButton(self.frame_GcodePauseStop)
        self.pushButton_Hold_Start_Gcode.setGeometry(QtCore.QRect(20, 10, 81, 41))
        self.pushButton_Hold_Start_Gcode.setIcon(icon10)
        self.pushButton_Hold_Start_Gcode.setObjectName("pushButton_Hold_Start_Gcode")
        self.pushButton_StopGcode = QtWidgets.QPushButton(self.frame_GcodePauseStop)
        self.pushButton_StopGcode.setGeometry(QtCore.QRect(20, 60, 81, 41))
        icon24 = QtGui.QIcon()
        icon24.addPixmap(QtGui.QPixmap("img/Actions-process-stop-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_StopGcode.setIcon(icon24)
        self.pushButton_StopGcode.setObjectName("pushButton_StopGcode")
        self.tabWidget.addTab(self.tab_3, "")
        self.pushButton_Emergency = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_Emergency.setGeometry(QtCore.QRect(490, 520, 71, 61))
        self.pushButton_Emergency.setText("")
        icon25 = QtGui.QIcon()
        icon25.addPixmap(QtGui.QPixmap("img/Perspective-Button-Shutdown-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_Emergency.setIcon(icon25)
        self.pushButton_Emergency.setIconSize(QtCore.QSize(60, 60))
        self.pushButton_Emergency.setFlat(True)
        self.pushButton_Emergency.setObjectName("pushButton_Emergency")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 564, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuConfig = QtWidgets.QMenu(self.menuFile)
        self.menuConfig.setObjectName("menuConfig")
        self.menuGcode = QtWidgets.QMenu(self.menuFile)
        self.menuGcode.setObjectName("menuGcode")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionOpen = QtWidgets.QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave_Config = QtWidgets.QAction(MainWindow)
        self.actionSave_Config.setObjectName("actionSave_Config")
        self.actionLoad_Gcode = QtWidgets.QAction(MainWindow)
        self.actionLoad_Gcode.setObjectName("actionLoad_Gcode")
        self.actionSave_Gcode = QtWidgets.QAction(MainWindow)
        self.actionSave_Gcode.setObjectName("actionSave_Gcode")
        self.menuConfig.addSeparator()
        self.menuConfig.addAction(self.actionSave_Config)
        self.menuGcode.addAction(self.actionLoad_Gcode)
        self.menuGcode.addAction(self.actionSave_Gcode)
        self.menuFile.addAction(self.menuConfig.menuAction())
        self.menuFile.addAction(self.menuGcode.menuAction())
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        #-------------------------------------------------------
        self.Icon_stop=icon10
        icon10a = QtGui.QIcon()
        icon10a.addPixmap(QtGui.QPixmap("img/Button-Play-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.Icon_start=icon10a
        #--------------------------------------------------------        
        self.plaintextEdit_GcodeScript = QCodeEditor(self.groupBox_GcodeScript)        
        self.plaintextEdit_GcodeScript.setGeometry(QtCore.QRect(10, 20, 431, 351))
        self.plaintextEdit_GcodeScript.setObjectName("plaintextEdit_GcodeScript")

        #
        #Combobox Fill
        self.comboBox_ConnSpeed.addItem("9600")
        self.comboBox_ConnSpeed.addItem("14400")
        self.comboBox_ConnSpeed.addItem("19200")
        self.comboBox_ConnSpeed.addItem("28800")
        self.comboBox_ConnSpeed.addItem("38400")
        self.comboBox_ConnSpeed.addItem("57600")
        self.comboBox_ConnSpeed.addItem("91600")
        self.comboBox_ConnSpeed.addItem("115200")
        self.comboBox_ConnSpeed.addItem("250000")
        #Set default
        self.COMBaudRate="115200"
        index= self.comboBox_ConnSpeed.findText(self.COMBaudRate,QtCore.Qt.MatchFixedString)
        self.comboBox_ConnSpeed.setCurrentIndex(index)

        self.Fill_COM_Combo()
        
        self.Connect_Actions()
        
        

        self.init_Values()
        
        # Set Icons and status off
        self.Set_Icons_Status_OnOFF(False)
        
        self.Fill_Deltas()
        self.PB_Set_Position()
    
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "XYZ Mover by FG"))
        self.groupBoxConnect.setTitle(_translate("MainWindow", "Connect"))
        self.pushButton_Refresh.setText(_translate("MainWindow", "Refresh"))
        self.label_COM.setText(_translate("MainWindow", "COM Port"))
        self.label_ConnSpeed.setText(_translate("MainWindow", "Connection Speed"))
        self.pushButton_Connect.setText(_translate("MainWindow", "Connect"))
        self.groupBox_XYZ.setTitle(_translate("MainWindow", "XYZ Mover"))
        self.label_Xpos.setText(_translate("MainWindow", "X"))
        self.label_Ypos.setText(_translate("MainWindow", "Y"))
        self.label_Zpos.setText(_translate("MainWindow", "Z "))
        self.groupBox_actPosition.setTitle(_translate("MainWindow", "Actual Position"))
        self.pushButton_SetPos.setText(_translate("MainWindow", "Set"))
        self.label_ZactPos.setText(_translate("MainWindow", "Z=  NA"))
        self.label_YactPos.setText(_translate("MainWindow", "Y=  NA"))
        self.label_XactPos.setText(_translate("MainWindow", "X=  NA"))
        self.pushButton_Go.setText(_translate("MainWindow", "GO"))
        self.pushButton_Stop.setText(_translate("MainWindow", "Hold"))
        self.pushButton_Home.setText(_translate("MainWindow", "Home"))
        self.pushButton_Reset.setText(_translate("MainWindow", "Reset Signal"))
        self.groupBox_DeltaMove.setTitle(_translate("MainWindow", "Delta"))
        self.label_DeltaZ.setText(_translate("MainWindow", "Z"))
        self.label_DeltaX.setText(_translate("MainWindow", "X"))
        self.label_DeltaY.setText(_translate("MainWindow", "Y"))
        self.label_Feedrate.setText(_translate("MainWindow", "F"))
        self.pushButton_CleanAlarm.setText(_translate("MainWindow", "Clear Alarm"))
        self.label_XZ.setText(_translate("MainWindow", "  XZ"))
        self.label_Z.setText(_translate("MainWindow", "Z"))
        self.label_XY.setText(_translate("MainWindow", "XY"))
        self.label_YZ.setText(_translate("MainWindow", "  YZ"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Move"))
        self.pushButton_SetConfig.setText(_translate("MainWindow", "Set Value"))
        self.label_ConfigInfo.setText(_translate("MainWindow", "NA"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Config"))
        self.groupBox_Gcode.setTitle(_translate("MainWindow", "Gcode input"))
        self.pushButton_Gcodesend.setText(_translate("MainWindow", "Gcode Send"))
        self.groupBox_GcodeScript.setTitle(_translate("MainWindow", "Gcode Script"))
        self.pushButton_LoadGcode.setText(_translate("MainWindow", "Load Gcode"))
        self.PushButton_RunGcodeScript.setText(_translate("MainWindow", "Run Gcode"))
        self.checkBox_Gcode.setText(_translate("MainWindow", "Check Gcode"))
        self.pushButton_SaveGcode.setText(_translate("MainWindow", "Save Gcode"))
        self.pushButton_Hold_Start_Gcode.setText(_translate("MainWindow", "Pause"))
        self.pushButton_StopGcode.setText(_translate("MainWindow", "STOP"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("MainWindow", "Gcode"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuConfig.setTitle(_translate("MainWindow", "Config"))
        self.menuGcode.setTitle(_translate("MainWindow", "Gcode"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))
        self.actionSave_Config.setText(_translate("MainWindow", "Save Config"))
        self.actionLoad_Gcode.setText(_translate("MainWindow", "Load Gcode"))
        self.actionSave_Gcode.setText(_translate("MainWindow", "Save Gcode "))


    def Connect_Actions(self):
        self.pushButton_Connect.clicked.connect(self.PB_Connect)
        self.pushButton_Refresh.clicked.connect(self.PB_Refresh)
        self.pushButton_SetPos.clicked.connect(self.PB_Set_Position)
        self.pushButton_Reset.clicked.connect(self.PB_Reset_Signal)
        self.pushButton_Go.clicked.connect(self.PB_Go)
        self.pushButton_Stop.clicked.connect(self.PB_Stop)
        self.actionSave_Config.triggered.connect(self.Save_config_to_file)
        self.comboBox_ConfigItem.currentIndexChanged.connect(self.Combo_config_Select)
        self.tableWidget_Config.cellClicked.connect(self.Config_Table_cellClick)
        self.pushButton_SetConfig.clicked.connect(self.Set_Config_Value)

        self.pushButton_XLeft.clicked.connect(self.PB_XLeft)
        self.pushButton_XRight.clicked.connect(self.PB_XRight)
        self.pushButton_YUp.clicked.connect(self.PB_YUp)
        self.pushButton_YDown.clicked.connect(self.PB_YDown)
        self.pushButton_ZUp.clicked.connect(self.PB_ZUp)
        self.pushButton_ZDown.clicked.connect(self.PB_ZDown)
        
        self.pushButton_XYLD.clicked.connect(self.PB_XYLD)
        self.pushButton_XYLU.clicked.connect(self.PB_XYLU)
        self.pushButton_XYRD.clicked.connect(self.PB_XYRD)
        self.pushButton_XYRU.clicked.connect(self.PB_XYRU)
        
        self.pushButton_XZRU.clicked.connect(self.PB_XZRU)
        self.pushButton_XZRD.clicked.connect(self.PB_XZRD)
        self.pushButton_XZLU.clicked.connect(self.PB_XZLU)
        self.pushButton_XZLD.clicked.connect(self.PB_XZLD)
        
        self.pushButton_YZRU.clicked.connect(self.PB_YZRU)
        self.pushButton_YZRD.clicked.connect(self.PB_YZRD)
        self.pushButton_YZLU.clicked.connect(self.PB_YZLU)
        self.pushButton_YZLD.clicked.connect(self.PB_YZLD)
        
        self.pushButton_Gcodesend.clicked.connect(self.PB_Gcodesend)
        self.pushButton_Home.clicked.connect(self.PB_Home)
        self.pushButton_CleanAlarm.clicked.connect(self.PB_CleanAlarm)

        #self.tabWidget.tabs.tabBarClicked(2).connect(self.Fill_Config_Combo)
        self.pushButton_LoadGcode.clicked.connect(self.PB_LoadGcode)
        self.pushButton_SaveGcode.clicked.connect(self.PB_SaveGcode)
        self.PushButton_RunGcodeScript.clicked.connect(self.PB_RunGcodeScript)
        self.pushButton_Emergency.clicked.connect(self.PB_Emergency)

        self.pushButton_StopGcode.clicked.connect(self.PB_StopGcode)
        """
        for i,self.tabWidget in enumerate(bars):
            tabbar.setContextMenuPolicy(Qt.ActionsContextMenu)
            renameAction = QtGui.QAction("Rename",tabbar)
            renameAction.triggered.connect(lambda x: self.renameTabSlot(i))
            tabbar.addAction(renameAction)
        """    
        #self.lineEdit_DeltaX.textChanged['QString'].connect(self.Set_DeltaX_Value)
        
        #self.label_XactPos.textChanged['QString'].connect(self.Set_actX_Value)
        #self.label_YactPos.textChanged['QString'].connect(self.Set_actY_Value)
        #self.label_ZactPos.textChanged['QString'].connect(self.Set_actZ_Value)


    def init_Values(self):
        self.killer_event = threading.Event()  
        self.killer_event.clear() 
        self.XYZRobot_com_port ='COM10'
        self.Version ='2.0.1'
        self.x_pos = 0
        self.y_pos = 0
        self.z_pos = 0
        self.DeltaX= 1
        self.DeltaY= 1
        self.DeltaZ= 1
        self.XYZRobot_found=0
        self.Config_Table_NumRows=0
        self.Config_Table_NumCols=0
        self.isoncheckedstate_checkbox=False
    
    def PB_Emergency(self):
        self.killer_event.set()
    
    def PB_StopGcode(self):
        self.stream_event_stop.set()

    def PB_RunGcodeScript(self):
        if self.checkBox_Gcode.isChecked()==True or self.isoncheckedstate_checkbox==True:
            self.isoncheckedstate_checkbox=not self.isoncheckedstate_checkbox # Case was not terminated correctly last time
            self.xyz_thread.grbl_gcode_cmd('$C')
            time.sleep(0.2) # wait to react 
        logging.info("Sending stream to thread")    
        text2stream=self.plaintextEdit_GcodeScript.toPlainText()
        self.xyz_gcodestream_thread.Stream(text2stream)


        if self.isoncheckedstate_checkbox==True:
            self.xyz_thread.grbl_gcode_cmd('$C')
            self.isoncheckedstate_checkbox=False
            self.checkBox_Gcode.setChecked(False)
            


    def PB_LoadGcode(self):        
        filename=aDialog.openFileNameDialog(0) #0 gcode
        
        if filename is not None:
            logging.info('Opening:'+filename)
            try:
                self.plaintextEdit_GcodeScript.clear()
                with open(filename, 'r') as yourFile:
                    #self.plaintextEdit_GcodeScript.setText(yourFile.read())        #textedit
                    self.plaintextEdit_GcodeScript.appendPlainText(yourFile.read())        #plaintextedit
                              
                yourFile.close()                
            except Exception as e:
                logging.error(e)
                logging.info("File was not read!")
            
    def PB_SaveGcode(self):        
        filename=aDialog.saveFileDialog(0) #0 gcode        
        if filename is not None:       
            mfile=re.search('(\.gcode$)',filename)
            try:
                if mfile.group(1)!='.gcode': 
                    filename=filename+'.gcode'
            except:
                filename=filename+'.gcode'        
            logging.info('Saving:'+filename) 
            try:
                with open(filename, 'w') as yourFile:
                    yourFile.write(str(self.plaintextEdit_GcodeScript.toPlainText()))                
                yourFile.close()                
            except Exception as e:
                logging.error(e)
                logging.info("File was not Written!")


    

    def Set_Icons_Status_OnOFF(self,Is_on):
        self.StatusConnected=Is_on
        self.groupBox_XYZ.setEnabled(self.StatusConnected)
        self.label_ConnectedStatus.setEnabled(self.StatusConnected)
        self.tab_2.setEnabled(self.StatusConnected)
        self.tab_3.setEnabled(self.StatusConnected)

    def Set_actX_Value(self):
        text=self.label_XactPos.text()
        text=text.replace('X','')
        text=text.replace('=','')        
        text=text.replace(' ','')  
        Val=float(text)
        if self.x_pos!=Val:
            self.x_pos=Val

    def Set_actY_Value(self):
        text=self.label_YactPos.text()
        text=text.replace('Y','')
        text=text.replace('=','')       
        text=text.replace(' ','')  
        Val=float(text)
        if self.y_pos!=Val:
            self.y_pos=Val

    def Set_actZ_Value(self):
        text=self.label_YactPos.text()
        text=text.replace('Z','')
        text=text.replace('=','')     
        text=text.replace(' ','')     
        Val=float(text)
        if self.z_pos!=Val:
            self.z_pos=Val
    
    def PB_CleanAlarm(self):
        self.xyz_thread.clear_state()

    def PB_Home(self):
        self.xyz_thread.Send_Homing()

    def Set_DeltaXYZ_Values(self):
        
        try:
            value=float(self.lineEdit_DeltaX.text())
            self.DeltaX=value
        except:       
            self.lineEdit_DeltaX.setText(str(self.DeltaX))
        try:
            value=float(self.lineEdit_DeltaY.text())
            self.DeltaY=value
        except:       
            self.lineEdit_DeltaY.setText(str(self.DeltaY))    
        try:
            value=float(self.lineEdit_DeltaZ.text())
            self.DeltaZ=value
        except:       
            self.lineEdit_DeltaZ.setText(str(self.DeltaZ)) 
        #self.Fill_Deltas()    

    def Move_Delta(self,DeltaX,DeltaY,DeltaZ):    
        self.pushButton_Stop.setIcon(self.Icon_stop)
        self.pushButton_Stop.setText("STOP")
        self.Get_Actual_Pos()
        self.ini_pos=[self.x_pos,self.y_pos,self.z_pos]                
        self.end_pos=[self.ini_pos[0]+DeltaX,self.ini_pos[1]+DeltaY,self.ini_pos[2]+DeltaZ]               
        if self.XYZRobot_found==1:
            logging.info("Going to: X = " + str(self.X) + ", Y = " + str(self.Y)+", Z = " + str(self.Z))            
            self.xyz_thread.goto_xyz(self.end_pos[0],self.end_pos[1],self.end_pos[2])
            #usefixedtime=0
            #self.wait_response_xyz(usefixedtime,5)
        else:
            logging.info("XYZ Robot Not Found for Moving") 
    def PB_Gcodesend(self):
        gcodeline=self.lineEdit_Gcode.text()
        logging.info("Sending Gcode: "+gcodeline)
        self.xyz_thread.grbl_gcode_cmd(gcodeline)

    def PB_XLeft(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(-1*self.DeltaX,0,0)    
    def PB_XRight(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(1*self.DeltaX,0,0)
    def PB_YUp(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(0,1*self.DeltaY,0)
    def PB_YDown(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(0,-1*self.DeltaY,0)
    def PB_ZUp(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(0,0,1*self.DeltaZ)        
    def PB_ZDown(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(0,0,-1*self.DeltaZ)

    def PB_XYLD(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(-1*self.DeltaX,-1*self.DeltaY,0)
    def PB_XYRD(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(1*self.DeltaX,-1*self.DeltaY,0)    
    def PB_XYRU(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(1*self.DeltaX,1*self.DeltaY,0)    
    def PB_XYLU(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(-1*self.DeltaX,1*self.DeltaY,0)

    def PB_XZLD(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(-1*self.DeltaX,0,-1*self.DeltaZ)
    def PB_XZRD(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(1*self.DeltaX,0,-1*self.DeltaZ)    
    def PB_XZRU(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(1*self.DeltaX,0,1*self.DeltaZ)    
    def PB_XZLU(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(-1*self.DeltaX,0,1*self.DeltaZ)

    def PB_YZLD(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(0,-1*self.DeltaY,-1*self.DeltaZ)
    def PB_YZRD(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(0,1*self.DeltaY,-1*self.DeltaZ)    
    def PB_YZRU(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(0,1*self.DeltaY,1*self.DeltaZ)    
    def PB_YZLU(self):
        self.Set_DeltaXYZ_Values()
        self.Move_Delta(0,-1*self.DeltaY,1*self.DeltaZ)    

    def Fill_Deltas(self):
        self.lineEdit_DeltaX.setText(str(self.DeltaX))
        self.lineEdit_DeltaY.setText(str(self.DeltaY))
        self.lineEdit_DeltaZ.setText(str(self.DeltaZ))


    def write_GUI_Log(self, sss):
        self.textEdit_Logger.setFontWeight(QtGui.QFont.Normal)
        self.textEdit_Logger.append(sss)

    def Start_XYZ_Thread(self):            
        try:
            XYZRobot_port=self.COMPort            
            #Baudrate=self.COMBaudRate.encode('utf-8')
            Baudrate=int(self.COMBaudRate)
            self.xyz_thread = XYZGrbl(XYZRobot_port, Baudrate, self.killer_event)
            self.xyz_thread.start()
            self.xyz_update_thread=XYZ_Update(self.xyz_thread,self.killer_event,self.label_XactPos,self.label_YactPos,self.label_ZactPos,self.pushButton_Stop,self.frame_GcodePauseStop)
            self.xyz_update_thread.setName("XYZ Update") 
            self.xyz_update_thread.start()
            self.stream_event_stop= threading.Event()
            self.stream_event_stop.clear()
            self.xyz_gcodestream_thread=XYZ_Gcode_Stream(self.xyz_thread,self.killer_event,self.xyz_thread.grbl_event_hold,self.stream_event_stop)
            self.xyz_gcodestream_thread.setName("XYZ Gcode Stream") 
            self.xyz_gcodestream_thread.start()

            logging.info("First Run Calibrating to: X = " + str(self.x_pos) + ", Y = " + str(self.y_pos) + ", Z = " + str(self.z_pos))
            self.xyz_thread.home_offset_xyz(self.x_pos,self.y_pos,self.z_pos)
            self.XYZRobot_found=1
            
            logging.info("SUCCESS: XYZ Initialized :)")   
            
        except Exception as e:   
            self.XYZRobot_found=0
            #logging.error("failed to initialise xyz_thread: ", sys.exc_info()[0])
            logging.error(e)
            logging.error("Failed to initialise xyz_thread :( -> No Robot ")
            self.Show_Message("Error","Failed to Initialize XYZ Robot :( (Check Port)")
            print("Is XYZRobot in port "+ XYZRobot_port + "?")
        #finally:
        #    self.App_Close_Event()

    def Show_Message(self,title,text):
        msg=QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.exec_()

    def Set_Actual_Position_Values(self,xxx,yyy,zzz):        
        try:
            self.x_pos = xxx
            self.y_pos = yyy
            self.z_pos = zzz
            self.xyz_update_thread.x_pos = xxx
            self.xyz_update_thread.y_pos = yyy
            self.xyz_update_thread.z_pos = zzz
            self.xyz_update_thread.Set_Actual_Position_Values(xxx,yyy,zzz)
        except:    
            self.x_pos = xxx
            self.y_pos = yyy
            self.z_pos = zzz
            _translate = QtCore.QCoreApplication.translate
            self.label_XactPos.setText(_translate("MainWindow","X = "+str(xxx)))
            self.label_XactPos.adjustSize()
            self.label_YactPos.setText(_translate("MainWindow","Y = "+str(yyy)))
            self.label_YactPos.adjustSize()
            self.label_ZactPos.setText(_translate("MainWindow","Z = "+str(zzz)))
            self.label_ZactPos.adjustSize()
        

    

    def Fill_Config_Combo(self):    
        if self.XYZRobot_found==1:       
            self.comboBox_ConfigItem.clear()  
            if self.Is_Config_Table_Empty()==True:
                config=self.xyz_thread.read_grbl_config(True,0)
            else:
                config=self.xyz_thread.read_grbl_config(False,0)   
            for ccc in config:
                if not '_Info' in ccc and not '_Type' in ccc:
                    self.comboBox_ConfigItem.addItem(ccc) 
            self.Fill_Config_Table()        

    def Fill_Config_Table(self):
        if self.XYZRobot_found==1:       
            self.tableWidget_Config.clear()
            config=self.xyz_thread.read_grbl_config(True,0)   
            Num_Items=0
            for ccc in config:
                if not '_Info' in ccc and not '_Type' in ccc:
                    Num_Items=Num_Items+1
            self.Config_Table_NumRows=Num_Items        
            self.Config_Table_NumCols=4
            self.tableWidget_Config.setRowCount(self.Config_Table_NumRows)
            self.tableWidget_Config.setColumnCount(self.Config_Table_NumCols)
            self.tableWidget_Config.setHorizontalHeaderLabels(["Id", "Value", "Info", "Type"])
            self.tableWidget_Config.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)            
            iii=0
            for ccc in config:
                if not '_Info' in ccc and not '_Type' in ccc:                
                    self.tableWidget_Config.setItem(iii,0, QTableWidgetItem(ccc))
                    self.tableWidget_Config.setItem(iii,1, QTableWidgetItem(str(config[ccc])))
                    self.tableWidget_Config.setItem(iii,2, QTableWidgetItem(str(config[ccc+'_Info'])))
                    self.tableWidget_Config.setItem(iii,3, QTableWidgetItem(str(config[ccc+'_Type'])))
                    iii=iii+1
            self.tableWidget_Config.resizeColumnsToContents()        
        
    def Config_Table_cellClick(self, row, col):
        self.Config_Table_row = row
        self.Config_Table_col = col

    def Combo_config_Select(self):
        self.Combo_Config_Selected=self.comboBox_ConfigItem.currentText()
        config=self.xyz_thread.read_grbl_config(False,0)   
        for ccc in config:
            if not '_Info' in ccc and not '_Type' in ccc:
                if ccc == self.Combo_Config_Selected:
                    self.lineEdit_ConfigValue.setText(str(config[ccc])) 
                    self.label_ConfigInfo.setText(str(config[ccc+'_Info']))
                    self.label_ConfigInfo.adjustSize()
                    break
    
    def Is_Config_Table_diff_to_device(self):
        config=self.xyz_thread.read_grbl_config(True,0)
        is_different=False
        for row in range(self.Config_Table_NumRows):                        
            hhh=self.tableWidget_Config.item(row, 0).text()
            hhhval=self.tableWidget_Config.item(row, 1).text()            
            #logging.info(self.xyz_thread.Read_Config_Parameter(hhh.replace('$', '')))                        
            if str(config[hhh])!=hhhval:
                is_different=True
                break
        return is_different        
            
    def write_Config_to_device(self):
        config=self.xyz_thread.read_grbl_config(False,0)

        for row in range(self.Config_Table_NumRows):                        
            hhh=self.tableWidget_Config.item(row, 0).text()            
            Param=hhh.replace('$', '')           
            hhhval=self.tableWidget_Config.item(row, 1).text()  
            #hhhinfo=self.tableWidget_Config.item(row, 2).text()  
            hhhtype=self.tableWidget_Config.item(row, 3).text()  
            if hhhtype =='int':
                Value=int(hhhval)
            elif hhhtype == 'float':
                Value=float(hhhval)
            else:
                Value=str(hhhval)    
            for ccc in list(config):
                if ccc == hhh:   
                    if config[ccc]!=Value:                        
                        self.xyz_thread.change_grbl_config_parameter(Param,Value)
                        while self.xyz_thread.Is_system_ready()==False:
                            time.sleep(0.2)
                            logging.info("Stuck here?")
                        #logging.info(self.xyz_thread.Read_Config_Parameter(Param))
              

    def Is_Config_Table_Empty(self):
        #logging.info('Numrows->'+str(self.Config_Table_NumRows))
        if self.Config_Table_NumRows==0:
            return True
        else:
            return False

    def Set_Config_Value(self):
        if self.Is_Config_Table_Empty()==True:
            self.Fill_Config_Combo()
        if self.Is_Config_Table_diff_to_device()==True:
            logging.info("Writting Configuration Table to Device")
            self.write_Config_to_device()
            self.Fill_Config_Table()
        else:
            logging.info("No Configuration Changes found")
            

    def Save_config_to_file(self):
        if self.Is_Config_Table_Empty()==False: 
            fileName = "Config_grbl"
            ext='.txt'
            now = datetime.datetime.now()
            fileName = now.strftime("%Y-%m-%d_%H-%M")+'_'+fileName+ext

            fileName=aDialog.saveFileDialog(2) #2 is txt
            if fileName is not None:
                try:
                    file = open(fileName+'.txt','w')         
                    Tabledata=[]            
                    for row in range(self.Config_Table_NumRows):            
                        for col in range(self.Config_Table_NumCols):
                            Tabledata.append(self.tableWidget_Config.item(row, col).text())
                            Tabledata.append(' ')                                        
                        Tabledata.append('\n')                
                    file.writelines(Tabledata)    
                    logging.info("File Saved as:" + fileName)
                    file.close()
                except Exception as e:
                    logging.error(e)
                    logging.info("File was not Written!")
            

    def Fill_COM_Combo(self):
        self.comboBox_COM.clear() 
        ports = self.Get_serial_ports()
        for port in ports:
            self.comboBox_COM.addItem(port)

    def ComboBox_Select_Item(self):
        self.COMPort=self.comboBox_COM.currentText()
        self.COMBaudRate=self.comboBox_ConnSpeed.currentText()
    
    def PB_Connect(self):
        if self.StatusConnected==False:
            self.ComboBox_Select_Item()
            logging.info("Opening XYZ Robot port")
            self.Start_XYZ_Thread()
            self.Enable_GroupXYZ_ComIcon()
            self.Set_Icons_Status_OnOFF(True)
        else:
            self.Disable_GroupXYZ_ComIcon()  
            self.Set_Icons_Status_OnOFF(False)  

            
    def Disable_GroupXYZ_ComIcon(self):
        if self.XYZRobot_found==1:      
            if self.StatusConnected==True:
               self.StatusConnected=False                   
            logging.info("Disconnecting Robot")
            self.App_Close_Event()
            self.pushButton_Connect.setText("Connect")
            
    
    def Enable_GroupXYZ_ComIcon(self):
        if self.XYZRobot_found==1:      
            self.StatusConnected=True                  
            logging.info("Waiting for XYZ Robot Setup to finish")
            """
            count=1
            while not self.xyz_thread.Is_system_ready() and count<100:
                time.sleep(0.2)
                count=count+1
            #self.groupBox_XYZ.setEnabled(True)   
            if count>=100:
                self.XYZRobot_found=0
            """    
            self.pushButton_Connect.setText("Disconnect")    
        
        if self.XYZRobot_found!=1:
            self.StatusConnected=False            
        
        self.groupBox_XYZ.setEnabled(self.StatusConnected)   
        self.label_ConnectedStatus.setEnabled(self.StatusConnected)
        self.tab_2.setEnabled(self.StatusConnected)
        self.tab_3.setEnabled(self.StatusConnected)
        
        #self.Fill_Config_Combo()        
        #self.groupBox_XYZ.setEnabled(True)    #---------------------HERE--->set comment this line when runs    
    
    def PB_Refresh(self):
        self.Fill_COM_Combo()

    def PB_Stop(self):
        if self.XYZRobot_found==1:
            self.data_LastPos= self.xyz_thread.read() #get last known value
            if self.data_LastPos['STATE_XYZ']==6:
                self.PB_Start()
                self.pushButton_Stop.setIcon(self.Icon_stop)
                self.pushButton_Stop.setText("STOP")
            else:    
                logging.info("Stopping XYZRobot")

                self.pushButton_Stop.setIcon(self.Icon_start)
                self.pushButton_Stop.setText("Start")
                self.pushButton_Stop.setEnabled(False)    
                #time.sleep(0.3)          
                self.pushButton_Stop.setEnabled(True)
                
                #self.XYZRobot_port.write(str.encode(chr(24)))
                
                self.xyz_thread.grbl_feed_hold()
                #time.sleep(2)
                self.x_pos=self.data_LastPos['XPOS']
                self.y_pos=self.data_LastPos['YPOS']
                self.z_pos=self.data_LastPos['ZPOS']
                self.Set_Actual_Position_Values(self.x_pos,self.y_pos,self.z_pos)
        else:
            if self.data_LastPos['STATE_XYZ']==6:
                logging.info("XYZ Robot Not Found for Start") 
            else:
                logging.info("XYZ Robot Not Found for Stop") 
    
    def PB_Start(self):
        if self.XYZRobot_found==1:            
            #self.XYZRobot_port.write(str.encode(chr(24)))
            #Last_Data= self.xyz_thread.read() #get last known value
            Last_Data= self.data_LastPos
            #logging.info("Starting XYZRobot--->" +str(Last_Data['STATE_XYZ']))
            if Last_Data['STATE_XYZ']==6:
                logging.info("Starting XYZRobot")
                self.xyz_thread.grbl_feed_start()      
            self.pushButton_Stop.setEnabled(False)    
            time.sleep(0.1)          
            self.pushButton_Stop.setEnabled(True)
        else:
            logging.info("XYZ Robot Not Found for Starting") 

    def PB_Reset_Signal(self):
        self.pushButton_Stop.setIcon(self.Icon_stop)
        self.pushButton_Stop.setText("STOP")
        if self.XYZRobot_found==1:
            logging.info("Reseting XYZRobot")
            #self.XYZRobot_port.write(str.encode(chr(24)))
            self.data_LastPos= self.xyz_thread.read() #get last known value
            self.xyz_thread.clear_state()
            time.sleep(10)
            self.x_pos=self.data_LastPos['XPOS']
            self.y_pos=self.data_LastPos['YPOS']
            self.z_pos=self.data_LastPos['ZPOS']
            self.Set_Actual_Position_Values(self.x_pos,self.y_pos,self.z_pos)
        else:
            logging.info("XYZ Robot Not Found for Reset")    

    def Read_Input_xyz(self):
        try :                        
            self.X = float(self.lineEdit_X.text())
        except:
            self.X = self.x_pos
            self.lineEdit_X.setText(str(self.X))
        try :
            self.Y = float(self.lineEdit_Y.text())
        except:
            self.Y = self.y_pos           
            self.lineEdit_Y.setText(str(self.Y))
        try :
            self.Z = float(self.lineEdit_Z.text())
        except:
            self.Z = self.z_pos    
            self.lineEdit_Z.setText(str(self.Z))   
            

    def PB_Set_Position(self):
        self.Read_Input_xyz()            
        #self.xyz_update_thread.Set_Actual_Position_Values(self.X,self.Y,self.Z)
        self.Set_Actual_Position_Values(self.X,self.Y,self.Z)
        self.Get_Actual_Pos()
        if self.XYZRobot_found==1:
            self.xyz_thread.home_offset_xyz(self.x_pos,self.y_pos,self.z_pos)
        else:            
            logging.info("XYZ Robot not Connected for setting Position")        
        #try:
        #    logging.info("Calibrating table to: X = " + str(self.X) + ", Y = " + str(self.Y)+", Z = " + str(self.Z))
        #    self.XYZRobot_port.write(str.encode('g92 x' + str(self.X) + ' y' + str(self.Y)+ ' z' + str(self.Z) + '\n'))
        #except:
        #    logging.info("Calibrating Error!")    

    def PB_Go(self):  
        self.pushButton_Stop.setIcon(self.Icon_stop)
        self.pushButton_Stop.setText("STOP")
        self.Read_Input_xyz()   
        self.end_pos=[self.X,self.Y,self.Z]               
        self.ini_pos=[self.x_pos,self.y_pos,self.z_pos]                
        if self.XYZRobot_found==1:
            logging.info("Going to: X = " + str(self.X) + ", Y = " + str(self.Y)+", Z = " + str(self.Z))
            #self.XYZRobot_port.write(str.encode('g0 x' + str(self.X) + ' y' + str(self.Y)+ ' z' + str(self.Z) + '\n'))
            self.xyz_thread.goto_xyz(self.X,self.Y,self.Z)
            #usefixedtime=0
            #self.wait_response_xyz(usefixedtime,5)
        else:
            logging.info("XYZ Robot Not Found for Going")        
            
            
                


    def Get_serial_ports(self):
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result
    def closeEvent(self,event):
        result = QtWidgets.QMessageBox.question(self,
                      "Confirm Exit...",
                      "Are you sure you want to exit ?",
                      QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
        event.ignore()

        if result == QtWidgets.QMessageBox.Yes:
            self.App_Close_Event()    
            event.accept()

    def App_Close_Event(self):
        logging.info("Close Event Triggered -> stopping threads")
        self.killer_event.set()
        if self.XYZRobot_found==1:
            self.xyz_update_thread.join()
            self.xyz_thread.join()
            self.XYZRobot_found=0
        self.xyz_thread=None 
        self.xyz_update_thread=None    

        logging.info("waiting 1s")        
        time.sleep(1)
        logging.info("cleaning kill event")
        self.killer_event.clear()   
        logging.info("finished")

        self.XYZRobot_found=0
    
    def Get_Actual_Pos(self):
        try:
            self.x_pos=self.xyz_update_thread.x_pos
            self.y_pos=self.xyz_update_thread.y_pos
            self.z_pos=self.xyz_update_thread.z_pos
            self.state_xyz=self.xyz_update_thread.state_xyz
        except:    
            self.x_pos=self.x_pos
        

    def wait_response_xyz(self,usefixedtime,Fix_time_spec):
        if usefixedtime==1:
            time.sleep(0.1)
            xy_data=self.xyz_thread.read()
            xystate=int(xy_data['STAT_XZpos'])
            #print("state---->>>>" +str(xystate))  
            if xystate == 11:            
                #self.xyz_thread.clear_state()
                #time.sleep(10)                  
                self.PB_Reset_Signal()
                        
            if xystate == 3 or xystate==0:
                time.sleep(0.5)                  
                xystate=88    
            nnn=1
            while xystate != 3:   #5 is moving 3 is stopped                     
                xy_data=self.xyz_thread.read()
                xystate=int(xy_data['STAT_XZpos'])
                #print("state end---->>>>" +str(xystate))
                time.sleep(0.1)
                nnn=nnn+1
                if nnn>200 or xystate==0:
                    logging.info("No Response! More than 2 min waiting response")
                    break
            #if xystate==0:
            #    print("XYZ robot not responding.")
            nnn=1
            while xystate == 3 or xystate==0:
                time.sleep(0.1)
                xy_data=self.xyz_thread.read()
                xystate=int(xy_data['STAT_XZpos'])
                nnn=nnn+1
                if nnn>5 :
                    #print("Waiting: 0.5 sec or state response: "+str(xystate)  )
                    break
            return 1
        else:
            time.sleep(Fix_time_spec)
            return 1

class ConsolePanelHandler(logging.Handler):

    def __init__(self, parent):
        logging.Handler.__init__(self)
        self.parent = parent

    def emit(self, record):
        self.parent.write_GUI_Log(self.format(record))





class XYZ_Update(threading.Thread):
    def __init__(self,xyz_thread,killer_event,label_XactPos,label_YactPos,label_ZactPos,button_hold_start_1,frame_hold_stop):
        threading.Thread.__init__(self, name="XYZ Update")
        logging.info("XYZ Update Started")
        self.xyz_thread=xyz_thread
        self.cycle_time=0.1
        self.label_XactPos=label_XactPos
        self.label_YactPos=label_YactPos
        self.label_ZactPos=label_ZactPos
        self.killer_event=killer_event
        self.button_hold_start_1=button_hold_start_1
        self.frame_hold_stop=frame_hold_stop
        self.state_xyz=0
        self.oldstate_xyz=0


    def run(self):                
        count=0
        while not self.killer_event.wait(self.cycle_time):   
            try:
                self.data = self.xyz_thread.read()
                self.Set_Actual_Position_Values(self.data['XPOS'],self.data['YPOS'],self.data['ZPOS']) 
                self.state_xyz=self.data['STATE_XYZ'] 
                self.Enable_Disable_Hold_Start()
                #time.sleep(self.cycle_time)
            except:
                if count==0:
                    logging.info("XYZ Update can't get data to update")                         
                else:
                   count=count+1
                if count>=2000:
                    count=0        
        logging.info("XYZ Update killed")          

    def read(self):
        return self.data

    def Enable_Disable_Hold_Start(self):
        #1=reset, 2=alarm, 3=stop, 4=end, 5=run, 6=hold, 7=probe, 9=homing
        if self.state_xyz==1:
            self.button_hold_start_1.setEnabled(False) 
            self.frame_hold_stop.setEnabled(False) 
        elif self.state_xyz==2:
            self.button_hold_start_1.setEnabled(True)  
            self.frame_hold_stop.setEnabled(True)    
        elif self.state_xyz==3:
            self.button_hold_start_1.setEnabled(False)
            self.frame_hold_stop.setEnabled(False) 
        elif self.state_xyz==4:
            self.button_hold_start_1.setEnabled(False) 
            self.frame_hold_stop.setEnabled(False)  
        elif self.state_xyz==5:
            self.button_hold_start_1.setEnabled(True)
            self.frame_hold_stop.setEnabled(True)
        elif self.state_xyz==6:
            self.button_hold_start_1.setEnabled(True)
            self.frame_hold_stop.setEnabled(True)
        elif self.state_xyz==7:
            self.button_hold_start_1.setEnabled(False) 
            self.frame_hold_stop.setEnabled(False) 
        elif self.state_xyz==9:
            self.button_hold_start_1.setEnabled(True)
            self.frame_hold_stop.setEnabled(True)  
        else:
            self.button_hold_start_1.setEnabled(False)
            self.frame_hold_stop.setEnabled(False)                      

    def Set_Actual_Position_Values(self,xxx,yyy,zzz):                            
        self.x_pos = xxx
        self.y_pos = yyy
        self.z_pos = zzz
        _translate = QtCore.QCoreApplication.translate
        self.label_XactPos.setText(_translate("MainWindow","X = "+str(xxx)))
        self.label_XactPos.adjustSize()
        self.label_YactPos.setText(_translate("MainWindow","Y = "+str(yyy)))
        self.label_YactPos.adjustSize()
        self.label_ZactPos.setText(_translate("MainWindow","Z = "+str(zzz)))
        self.label_ZactPos.adjustSize()    

class XYZ_Gcode_Stream(threading.Thread):
    def __init__(self,xyz_thread,killer_event,holding_event,stoping_event):
        threading.Thread.__init__(self, name="XYZ Gcode Stream")
        logging.info("XYZ Gcode Stream Started")
        self.xyz_thread=xyz_thread
        self.killer_event=killer_event
        self.holding_event=holding_event
        self.stoping_event=stoping_event        
        self.cycle_time=0.1               
        self.state_xyz=0
        self.oldstate_xyz=0
        self.istext2stream=False
        self.text_queue = queue.Queue()

    def wait_until_finished(self,a_count):
        count=0
        if self.state_xyz==3:
            while self.state_xyz==self.oldstate_xyz and count<a_count:
                self.data = self.xyz_thread.read()                
                self.get_state()
                time.sleep(self.cycle_time)
                count=count+1            
        self.oldstate_xyz=self.state_xyz
        while self.state_xyz==5:
            self.data = self.xyz_thread.read()                
            self.get_state()
            time.sleep(self.cycle_time)

         

    def get_state(self):        
        self.state_xyz=self.data['STATE_XYZ'] 

    def run(self):                
        count=0
        while not self.killer_event.wait(self.cycle_time):   
            try:
                self.data = self.xyz_thread.read()                
                self.get_state()
                if self.stoping_event.is_set()==True:
                    self.Stop_Clear()
                if self.holding_event.is_set()==False:                    
                    try:
                        #logging.info("Run entered 7")
                        line2stream= self.text_queue.get_nowait()
                        self.stream_one_line(line2stream)          
                        self.data = self.xyz_thread.read()                
                        self.get_state()
                        if self.state_xyz==11: # error
                            logging.info("Error in Gcode detected! (" + str(line2stream)+') ' )
                            self.Stop_Clear()
                        self.wait_until_finished(20000)    
                    except queue.Empty:                    
                        pass
                
                
            except:
                if count==0:
                    logging.info("XYZ Gcode Stream can't get data to update")                         
                else:
                   count=count+1
                if count>=2000:
                    count=0        
        logging.info("XYZ Gcode Stream killed")          
    
    def Stop_Clear(self):
        if self.istext2stream==True:
            self.text_queue.empty()
            self.istext2stream=False
            logging.info("Gcode Stream Stopped!")
        self.stoping_event.clear()

    def read(self):
        return self.data

    def Stream(self,text2stream):
        self.istext2stream=True
        line=''
        linecount=1
        for lll in text2stream:            
            if lll=='\n':
                logging.info("Sending Line-> ("+str(linecount)+") "+ line)
                 
                self.xyz_thread.grbl_gcode_cmd(line)   
                time.sleep(self.cycle_time) # wait to react
                self.data = self.xyz_thread.read()                
                self.get_state()                              
                if self.state_xyz==11: # error
                    logging.info("Error in Gcode! ("+str(linecount)+') '+ line )
                    self.Stop_Clear()
                    break    
                if self.killer_event.is_set()==True:
                    break
                linecount=linecount+1
                line=''
            else:
                line=line+lll
        if line!='':
            self.xyz_thread.grbl_gcode_cmd(line)
        self.istext2stream=False    
        logging.info("End of Stream!")    




    def stream_one_line(self,line2stream):
        if self.istext2stream==True:
            self.xyz_thread.grbl_gcode_cmd(line2stream)





if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = MyWindow()#QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    handler = ConsolePanelHandler(ui)
    log.addHandler(handler)
    handler.setFormatter(logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s'))        
    aDialog=Dialogs()
    MainWindow.show()
    sys.exit(app.exec_())
