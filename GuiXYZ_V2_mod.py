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
import GuiXYZ_V1
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



class Ui_MainWindow_V2(GuiXYZ_V1.Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(Ui_MainWindow_V2, self).__init__(*args, **kwargs)
        

    def setupUi2(self, MainWindow):   
        # Before you copy -paste here all Object code, now is called directly from GuiXYZ_V1.py

        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap("img/Button-Pause-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
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
        #try to get initial position from the machine
        self.Get_Actual_Pos()
        # by setting the text to nothing will use .xpos instead of .X variables
        #self.lineEdit_X.setText('')
        #self.lineEdit_Y.setText('')
        #self.lineEdit_Z.setText('')
        #self.lineEdit_Feedrate.setText('')
        
        self.PB_Set_Position()
    
    #No More retranslate in this class-> inherits from GuiXYZ_V1


    def Connect_Actions(self):
        self.pushButton_Connect.clicked.connect(self.PB_Connect)
        self.pushButton_Refresh.clicked.connect(self.PB_Refresh)
        self.pushButton_SetPos.clicked.connect(self.PB_Set_Position)
        self.pushButton_Reset.clicked.connect(self.PB_Reset_Signal)
        self.pushButton_Go.clicked.connect(self.PB_Go)
        self.pushButton_Pause_Resume.clicked.connect(self.PB_Pause_Resume)
        self.pushButton_Hold_Start_Gcode.clicked.connect(self.PB_Pause_Resume)
        self.pushButton_StopGcode.clicked.connect(self.PB_StopGcode)

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
        self.xyz_thread.grbl_stop()

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
        self.pushButton_Pause_Resume.setIcon(self.Icon_stop)
        self.pushButton_Hold_Start_Gcode.setIcon(self.Icon_stop)
        self.pushButton_Pause_Resume.setText("Hold")
        self.pushButton_Hold_Start_Gcode.setText("Hold")
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
            self.xyz_update_thread=XYZ_Update(self.xyz_thread,self.killer_event,self.label_XactPos,self.label_YactPos,self.label_ZactPos,self.pushButton_Pause_Resume,self.frame_GcodePauseStop)
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

    def PB_Pause_Resume(self):
        if self.XYZRobot_found==1:
            self.data_LastPos= self.xyz_thread.read() #get last known value
            if self.data_LastPos['STATE_XYZ']==6: # on Hold
                logging.info("Resuming XYZRobot")
                self.pushButton_Pause_Resume.setIcon(self.Icon_stop)
                self.pushButton_Hold_Start_Gcode.setIcon(self.Icon_stop)
                self.pushButton_Pause_Resume.setText("Hold")
                self.pushButton_Hold_Start_Gcode.setText("Hold")
                self.PB_Resume()
            else:    
                logging.info("Pausing XYZRobot")
                self.pushButton_Pause_Resume.setIcon(self.Icon_start)
                self.pushButton_Hold_Start_Gcode.setIcon(self.Icon_start)
                self.pushButton_Pause_Resume.setText("Start")
                self.pushButton_Hold_Start_Gcode.setText("Start")
                self.xyz_thread.grbl_feed_hold()
                #time.sleep(2)
                self.x_pos=self.data_LastPos['XPOS']
                self.y_pos=self.data_LastPos['YPOS']
                self.z_pos=self.data_LastPos['ZPOS']
                self.Set_Actual_Position_Values(self.x_pos,self.y_pos,self.z_pos)
                
                self.pushButton_Pause_Resume.setEnabled(False)
                self.pushButton_Hold_Start_Gcode.setEnabled(False)    
                time.sleep(0.3)          
                self.pushButton_Pause_Resume.setEnabled(True)
                self.pushButton_Hold_Start_Gcode.setEnabled(True)
                
        else:
            if self.data_LastPos['STATE_XYZ']==6:
                logging.info("XYZ Robot Not Found for Starting") 
            else:
                logging.info("XYZ Robot Not Found for Holding") 
    
    def PB_Resume(self):
        if self.XYZRobot_found==1:
            time.sleep(0.3)
            Last_Data= self.xyz_thread.read() #get last known value
            Last_Data= self.data_LastPos
            #logging.info("Starting XYZRobot--->" +str(Last_Data['STATE_XYZ']))
            if Last_Data['STATE_XYZ']==6:
                logging.info("Starting XYZRobot")
                self.xyz_thread.grbl_feed_start()      
            self.pushButton_Pause_Resume.setEnabled(False) 
            self.pushButton_Hold_Start_Gcode.setEnabled(False)   
            time.sleep(0.3)          
            self.pushButton_Pause_Resume.setEnabled(True)
            self.pushButton_Hold_Start_Gcode.setEnabled(True)
        else:
            logging.info("XYZ Robot Not Found for Starting") 

    def PB_Reset_Signal(self):
        self.pushButton_Pause_Resume.setIcon(self.Icon_stop)
        self.pushButton_Hold_Start_Gcode.setIcon(self.Icon_stop)
        self.pushButton_Pause_Resume.setText("Hold")
        self.pushButton_Hold_Start_Gcode.setText("Hold")
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
        self.pushButton_Pause_Resume.setIcon(self.Icon_stop)
        self.pushButton_Hold_Start_Gcode.setIcon(self.Icon_stop)
        self.pushButton_Pause_Resume.setText("Hold")
        self.pushButton_Hold_Start_Gcode.setText("Hold")
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
         #1=reset, 2=alarm, 3=idle, 4=end, 5=run, 6=hold, 7=probe, 8=cycling,  9=homing, 10 =jogging 11=error
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
            self.button_hold_start_1.setEnabled(True) 
            self.frame_hold_stop.setEnabled(True)
        elif self.state_xyz==8:
            self.button_hold_start_1.setEnabled(True) 
            self.frame_hold_stop.setEnabled(True)     
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
    ui = Ui_MainWindow_V2()
    ui.setupUi(MainWindow)
    ui.setupUi2(MainWindow)
    handler = ConsolePanelHandler(ui)
    log.addHandler(handler)
    handler.setFormatter(logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s'))        
    aDialog=Dialogs()
    MainWindow.show()
    sys.exit(app.exec_())
