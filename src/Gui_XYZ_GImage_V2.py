# -*- coding: utf-8 -*-
"""
Created on 16.06.2020
Python 3.7 pyQt5
@author: F. Garcia
"""
__author__ = "FG"
__authorname__ = "Federico García"
__version__="2.1.0 Beta"
__creationdate__="16.06.2020"
__gitaccount__="<a href=\"https://github.com/fedetony\">' Github for fedetony'</a>"
__CR__="Copyright (C) <year> "+__authorname__
__CRstatement__="""This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details."""

# Form implementation generated from reading ui file 'GuiXYZ_V1.ui'
# All Ui interfaces:
# Created by: PyQt5 UI code generator 5.13.0

from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PIL.ImageQt import ImageQt

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
import os
#import atexit
#import keyboard for keyboard inputs

#Configure logger before importing classes (so they become child loggers)
import class_LogHandler
ap=class_LogHandler.get_appPath()
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] (%(threadName)-10s) %(message)s',
                    datefmt='%y-%m-%d %H:%M',
                    filename=ap+'/temp/__last_run__.log',
                    filemode='w')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(ap+'/temp/__last_run__.log')
fh.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s [%(levelname)s] (%(threadName)-10s) %(message)s')
fh.setFormatter(formatter)
# add the handlers to logger
log.addHandler(fh)

#log_queue = queue.Queue()  
#queue_handler= class_LogHandler.QueueHandler(log_queue)  
#queue_handler.setLevel(logging.INFO)      
#formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
#queue_handler.setFormatter(formatter)
#log.addHandler(queue_handler) 
#print(log.handlers)

#from thread_xyz_grbl import XYZGrbl
from thread_xyz_multi_interface import XYZMulti
import thread_Gcode_Stream
import thread_XYZ_Update
from Gimage_V1 import Image_Gcode_Stream 
from Gimage_V1 import GImage 
import GuiXYZ_V1
import GuiXYZ_LSTD
import GuiXYZ_CCD
import GuiXYZ_RTD
import class_CCD   
import class_LSTD 
import class_RTD
import class_TTD
import class_File_Dialogs
import class_ST

#print(log.__dict__)


class QLabel_altered(QLabel):
    resize=pyqtSignal()
    #clicked=pyqtSignal()
    #def __init__(self, parent=None):
    #    QLabel.__init__(self, parent)
    #    self.last = ""

    #def mousePressEvent(self, ev):        
    #    self.clicked.emit()    
     
    left_clicked= QtCore.pyqtSignal(int)
    right_clicked = QtCore.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(250)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.timeout)
        self.left_click_count = self.right_click_count = 0

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.left_click_count += 1
            if not self.timer.isActive():
                self.timer.start()
        if event.button() == QtCore.Qt.RightButton:
            self.right_click_count += 1
            if not self.timer.isActive():
                self.timer.start()

    def timeout(self):
        if self.left_click_count >= self.right_click_count:
            self.left_clicked.emit(self.left_click_count)
        else:
            self.right_clicked.emit(self.right_click_count)
        self.left_click_count = self.right_click_count = 0

    def resizeEvent(self, ev):
        self.resize.emit()                         

class QLineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class QCodeEditor(QtWidgets.QPlainTextEdit,QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = QLineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        self._highlight_lines = dict()        
        self.extraselections_lines=[]
        self.block_from=0
        self.block_to=0
    
    def setFromTo(self,b_from,b_to):        
        if b_from<=0 or b_to<=0:
            self.block_from=0
            self.block_to=self.blockCount()
            return
        if b_to<b_from:
            self.block_from=0
            self.block_to=self.blockCount()
            return
        else:
            self.block_from=b_from
            self.block_to=b_to


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
            selection.cursor = self.textCursor()            
            block = selection.cursor.block()
            blockNumber = block.blockNumber()          
            if blockNumber>=self.block_from-1 and blockNumber<self.block_to:
                lineColor = QColor(Qt.blue).lighter(160)
            else:
                lineColor = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)            
            selection.cursor.clearSelection()
            
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)

        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + self.blockBoundingRect(block).height()

        # Just to make sure I use the right font
        height = int(self.fontMetrics().height())
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1)
                
                if blockNumber>=self.block_from-1 and blockNumber<self.block_to:
                    painter.setPen(Qt.black)
                else:
                    painter.setPen(Qt.red)
                painter.drawText(0, int(top), int(self.lineNumberArea.width()), int(height), Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def highlight_line(self, line, fmt):        
        if isinstance(line, int) and line >= 0 and isinstance(fmt, QTextCharFormat):
            self._highlight_lines[line] = fmt
            tb = self.document().findBlockByLineNumber(line)
            extraSelections =  self.extraselections_lines            
            try:
                if not self.isReadOnly():                
                    selection = QTextEdit.ExtraSelection()
                    lineColor = QColor(Qt.blue).lighter(160)
                    selection.format.setBackground(lineColor)
                    selection.format.setProperty(QTextFormat.FullWidthSelection, True)
                    selection.cursor = QTextCursor(tb) #self.textCursor()
                    selection.cursor.clearSelection()
                    selection.cursor.setBlockCharFormat(fmt)
                    extraSelections.append(selection)
                    self.extraselections_lines.append(selection)
                self.setExtraSelections(extraSelections)
                #cursor = QTextCursor(tb)
                #cursor.setBlockFormat(fmt)
                #cursor.setBlockCharFormat(fmt) #QTextCursor class
                #QtGui.QSyntaxHighlighter.rehighlightBlock(tb)
                
            except:
                pass    

    def clear_highlight(self):
        self._highlight_lines = dict()
        #self.setCurrentCharFormat(self.original_format)
        self.extraselections_lines=[]
        #QtGui.QSyntaxHighlighter.rehighlight()

    def highlightBlock(self, text):
        line = self.currentBlock().blockNumber()
        fmt = self._highlight_lines.get(line)
        if fmt is not None:
            self.setFormat(0, len(text), fmt)



class MyWindow(QtWidgets.QMainWindow):
    def closeEvent(self,event):
        result = QtWidgets.QMessageBox.question(self,
                      "Confirm Exit...",
                      "Are you sure you want to exit ?",
                      QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
        event.ignore()

        if result == QtWidgets.QMessageBox.Yes:
            #print('inside class')       
            # self.CCDialog      
            try:                
                ui.CCDialog.quit()                   
            except Exception as e:
                #log.error(e)     
                pass      
            try:                
                ui.LSTDialog.quit()                   
            except Exception as e:
                #log.error(e)     
                pass      
            try:                                
                ui.RTDialog.quit()             
            except Exception as e:
                #log.error(e)     
                pass    
            try:                                
                ui.TTDialog.quit()             
            except Exception as e:
                #log.error(e)     
                pass    
            ui.killer_event.set()            
            event.accept()
    
class Ui_MainWindow_V2(GuiXYZ_V1.Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(Ui_MainWindow_V2, self).__init__(*args, **kwargs)  
        #Start the log queue  
        ''' 
        self.log_queue = queue.Queue()        
        self.queue_handler= QueueHandler(self.log_queue)  
        self.queue_handler.setLevel(logging.INFO)      
        self.formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
        self.queue_handler.setFormatter(self.formatter)
        log.addHandler(self.queue_handler)                                
        '''       
        #self.kill_log_ev=threading.Event() 
        #self.kill_log_ev.clear()
        #self.LH_T=class_LogHandler.Log_Update(self.kill_log_ev) 
        #self.LH_T.start()
           
    def Show_aboutbox(self):
        title='About '+self.Metitle
        now = datetime.datetime.now()
        year = str(now.strftime("%Y"))
        thecr=str(__CR__.replace('<year>',year))
        amsg='<h1 style="font-size:160%;color:red;">Programmed with love</h1>'+'<h1 style="font-size:160%;color:black;">by '+ __author__+'</h1> <p style="color:black;">github: '+__gitaccount__+'</p> <p style="color:black;"> Current version: V'+__version__+'</p> <p style="color:black;">Creation date: '+__creationdate__+'</p> <p style="font-size:25%;color:black;"><small>'+thecr+'</small></p> <p style="font-size:25%;color:black;"><small>'+__CRstatement__+"</small></p>"          
        msgbox = QtWidgets.QMessageBox()
        msgbox.setWindowTitle(title)
        msgbox.setWindowIcon(self.iconMain)
        if self.iconMainpixmap!=None:            
            thepm=self.iconMainpixmap.scaled(160,160, QtCore.Qt.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)#QtCore.Qt.FastTransformation)         
            msgbox.setIconPixmap(thepm)
        msgbox.setText(amsg)           
        msgbox.setTextFormat(QtCore.Qt.RichText)
        msgbox.exec_()

    def setupUi2(self, MainWindow):   
        # Before you copy -paste here all Object code, now is called directly from GuiXYZ_V1.py
        
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap("img/Button-Pause-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        #-------------------------------------------------------
        self.Icon_pause=icon10
        icon10a = QtGui.QIcon()
        icon10a.addPixmap(QtGui.QPixmap("img/Button-Play-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.Icon_start=icon10a
        windowicon = QtGui.QIcon()
        self.iconMainpixmap=QtGui.QPixmap("img/eye-in-a-sky-icon.png")
        windowicon.addPixmap(self.iconMainpixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.iconMain=windowicon
        MainWindow.setWindowIcon(windowicon)
        self.Metitle="XYZ Mover by FG V"+str(__version__)
        MainWindow.setWindowTitle(self.Metitle)
        #--------------------------------------------------------        
        self.plaintextEdit_GcodeScript = QCodeEditor(self.groupBox_GcodeScript)        
        #self.plaintextEdit_GcodeScript.setGeometry(QtCore.QRect(10, 20, 431, 351))
        self.plaintextEdit_GcodeScript.setObjectName("plaintextEdit_GcodeScript")
        self.gridLayout_7.addWidget(self.plaintextEdit_GcodeScript, 0, 0, 1, 1)
        self.plaintextEdit_GcodeScript.blockCountChanged[int].connect(self.Set_from_to_Spinbox)
        self.plaintextEdit_GcodeScript.updateRequest.connect(self.Update_Highlights_Spinbox)
        
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

        self.comboBox_GcodeStreamType.addItem("0")
        self.comboBox_GcodeStreamType.addItem("1")
        self.comboBox_GcodeStreamType.addItem("2")
        self.comboBox_GcodeStreamType.addItem("3")
        self.comboBox_GcodeStreamType.addItem("4")
        self.comboBox_GcodeStreamType.addItem("5")
        typeofstream='''typeofstream=0 Wait until each Command returns finish signal to send next one.(Slow) 
typeofstream=1 Send all to machine and dont wait for response. 
typeofstream=2 Send a number of lines and count the returns.
typeofstream=3 No command interpretation. Wait until each Command returns finish signal to send next one.(Slow) 
typeofstream=4 No command interpretation. Send all to machine and dont wait for response. 
typeofstream=5 No command interpretation. Send a number of lines and count the returns.'''
        
        self.comboBox_GcodeStreamType.setToolTip(typeofstream)
        

        self.GcodeStreamType="5"
        index= self.comboBox_GcodeStreamType.findText(self.GcodeStreamType,QtCore.Qt.MatchFixedString)
        self.comboBox_GcodeStreamType.setCurrentIndex(index)

        self.Fill_COM_Combo()
        self.Connect_Actions()
        self.init_Values()
        #Init Commands configuration class
        self.CCDialog=class_CCD.CommandConfigurationDialog(self.Actual_Interface)
        
        self.CCDialog.file_update[str].connect(self.Configuration_Changed_Refresh)
        self.CCDialog.change_interface_id[str].connect(self.Configuration_id_Changed)
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
        # ---------GImage Init
        self.Fill_Image_Config_Table()

        self.P_Bar_Update_Gcode=ProgressBar_Update(MainWindow)        
        self.P_Bar_Update_Gcode.tick.connect(self.Update_value_and_time_elapsed)
        self.P_Bar_Update_Gimage=ProgressBar_Update(MainWindow)        
        self.P_Bar_Update_Gimage.tick.connect(self.progressBar_Gimage.setValue)
        self.P_Bar_buffer_Gcode=ProgressBar_Update(MainWindow) 
        self.P_Bar_buffer_Gcode.tick.connect(self.progressBar_Gcodebuffer.setValue)         
        #--------------connect logger class
        #self.LH_T.ST.log_update.connect(self.poll_log_queue) 
        #------------create signal tracker class
        self.ST=class_ST.SignalTracker()
        self.ST.enable_bHOLD.connect(self.Enable_HOLD_Button)
        self.ST.enable_bSTOP.connect(self.Enable_STOP_Button)
        self.ST.timer_change[str].connect(self.label_time.setText)
        self.ST.enable_isSTREAMING.connect(self.Enable_STREAMING)
        self.ST.data_change[dict].connect(self.Data_Change_Actualize)
        self.ST.is_hold_state.connect(self.Pause_Messagebox_Stream)
        self.ST.stream_info_change.connect(self.Stream_Info_Update)    
        
    def Spinbox_val_change_from(self,val):
        numlines=self.plaintextEdit_GcodeScript.blockCount() #self.spinBox_Stream_Linefrom.maximum()        
        try:
            val=int(val)
        except:
            val=0
            pass
        self.spinBox_Stream_Linefrom.setValue(val)
        self.Stream_Linefrom=val
        self.Stream_Lineto=self.spinBox_Stream_Lineto.value()
        self.Set_from_to_Spinbox(numlines)
        

    def Spinbox_val_change_to(self,val):
        numlines=self.plaintextEdit_GcodeScript.blockCount() #self.spinBox_Stream_Linefrom.maximum()
        try:
            val=int(val)
        except:
            val=0
            pass
        self.spinBox_Stream_Lineto.setValue(val)
        self.Stream_Linefrom=self.spinBox_Stream_Linefrom.value()
        self.Stream_Lineto=val
        self.Set_from_to_Spinbox(numlines)
    
    def Update_Highlights_Spinbox(self):
        numlines=self.plaintextEdit_GcodeScript.blockCount()
        #self.Set_from_to_Spinbox(numlines)

    def Set_from_to_Spinbox(self,numlines):
        self.spinBox_Stream_Linefrom.setMinimum(0)
        self.spinBox_Stream_Linefrom.setMaximum(numlines)
        if self.spinBox_Stream_Linefrom.value()>numlines or self.spinBox_Stream_Linefrom.value()<=0:
            self.spinBox_Stream_Linefrom.setValue(0)
            self.spinBox_Stream_Lineto.setValue(numlines)
            self.plaintextEdit_GcodeScript.clear_highlight()
        self.spinBox_Stream_Lineto.setMinimum(self.spinBox_Stream_Linefrom.value())
        self.spinBox_Stream_Lineto.setMaximum(numlines)               
        self.Stream_Linefrom=self.spinBox_Stream_Linefrom.value()
        self.Stream_Lineto=self.spinBox_Stream_Lineto.value()
        self.plaintextEdit_GcodeScript.setFromTo(self.Stream_Linefrom,self.Stream_Lineto)        
        #self.Set_from_to_Color_Highlight(numlines)
    '''
    def Set_from_to_Color_Highlight(self,numlines):  
        color_format = self.plaintextEdit_GcodeScript.currentCharFormat()             
        color_format1 = color_format
        color=QColor('black')
        color_format1.setForeground(color) 
        color_format1.setFontItalic(False)   
        color_format2=color_format1
        color=QColor('blue')
        color_format2.setForeground(color) 
        color_format2.setFontItalic(True)             
        self.plaintextEdit_GcodeScript.clear_highlight()
        #self.plaintextEdit_GcodeScript.setCurrentCharFormat(color_format)    
        block=self.plaintextEdit_GcodeScript.firstVisibleBlock()             
        while block.isVisible() and block.isValid():
            line =block.blockNumber()
            #print('entered while')
            if self.Stream_Linefrom>0 and line>=self.Stream_Linefrom-1 and line<self.Stream_Lineto:    
                #self.plaintextEdit_GcodeScript.highlight_line(line,color_format1)
                #only change it if is different (recursion issue)
                #print(color_format.fontItalic())
                self.plaintextEdit_GcodeScript.highlight_line(line,color_format2)
                #if color_format.fontItalic()==False:
                #    print('entered')
                #    self.setLineFormat(self.plaintextEdit_GcodeScript,line,color_format2)
                #    self.plaintextEdit_GcodeScript.highlight_line(line,color_format2)
            else:
                if color_format.fontItalic()==True:
                    self.setLineFormat(self.plaintextEdit_GcodeScript,line,color_format1)                
            block=block.next()                                                    

    def setLineFormat(self, textEdit,lineNumber, charformat):
        cursor = QTextCursor(textEdit.document().findBlockByNumber(lineNumber))
        cursor.setBlockCharFormat(charformat)
        #cursor.setBlockFormat(format)             
    '''    
        

    def poll_log_queue(self,logit=True):
        # Check every 100ms if there is a new message in the queue to display 
        #print('logger signal working?',log_queue.qsize())                       
        while log_queue.qsize()>0:
            try:
                record = log_queue.get(block=False)
                if logit==True:
                    self.write_GUI_Log(record)
            except queue.Empty:
                break

    def Stream_Info_Update(self,streaminfolist):
        atxt="Line "+str(streaminfolist[1])+ " of "+ str(streaminfolist[2])
        self.label_GcodeLines.setText(atxt)
        self.label_GcodeLines.adjustSize()        

    def Data_Change_Actualize(self,data):        
        try:
            xxx=data['XPOS']
            yyy=data['YPOS']
            zzz=data['ZPOS']
            StateXYZ=data['STATE_XYZ']
            Status=data['STATUS']
            self.x_pos = xxx
            self.y_pos = yyy
            self.z_pos = zzz            
            self.state_xyz=StateXYZ
            self.Status=Status
        except:            
            xxx=self.x_pos
            yyy=self.y_pos 
            zzz=self.z_pos 
            StateXYZ=self.state_xyz
            Status=self.Status
            pass        
        self.label_XactPos.setText("X = "+str(xxx))
        self.label_XactPos.adjustSize()
        self.label_YactPos.setText("Y = "+str(yyy))
        self.label_YactPos.adjustSize()
        self.label_ZactPos.setText("Z = "+str(zzz))
        self.label_ZactPos.adjustSize()                
        self.label_Stateact.setText("S_XYZ = "+str(StateXYZ)+" "+str(Status) )            
        self.label_Stateact.adjustSize()
        
    

    def Enable_HOLD_Button(self,isEnabled):   
        self.pushButton_Pause_Resume.setEnabled(isEnabled) 
        self.pushButton_Hold_Start_Gcode.setEnabled(isEnabled)
    
    def Enable_STOP_Button(self,isEnabled):   
       self.pushButton_MoveStop.setEnabled(isEnabled) 
       self.pushButton_StopGcode.setEnabled(isEnabled)

    def Enable_STREAMING(self,isEnabled):
        self.Is_streaming=isEnabled
        #self.frame_GcodePauseStop.setEnabled(isEnabled)     
        self.PushButton_RunGcodeScript.setEnabled(self.isnot(isEnabled))     

    def isnot(self,val):
        if val==False:
            return True
        return False

    def Pause_Messagebox_Stream(self,ShowMsg=False):
        if ShowMsg==True:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setWindowTitle('Stream on Pause ...')
            msgbox.setIcon(QtWidgets.QMessageBox.Question)
            msgbox.setText("Would you like to Resume the Stream? \nor\n"+
                        "Would you like to Stop the Stream?")
            msgbox.addButton(QtWidgets.QPushButton('Resume'), QtWidgets.QMessageBox.AcceptRole)
            msgbox.addButton(QtWidgets.QPushButton('Stop'), QtWidgets.QMessageBox.YesRole)
            msgbox.addButton(QtWidgets.QPushButton('Cancel'), QtWidgets.QMessageBox.NoRole)
            msgbox.setDefaultButton(QtWidgets.QMessageBox.Cancel)        
            result = msgbox.exec_()
            #print(result)
            if result == 0: #Resume QtWidgets.QMessageBox.AcceptRole:      
                self.xyz_thread.send_immediate_command('userResume',{},True)       
                log.info('------------------------Stream Resumed -----------------------------')
            elif result == 1: #Stop QtWidgets.QMessageBox.YesRole:  
                self.xyz_gcodestream_thread.stoping_event.set()                      
                self.PB_StopGcode()                
                log.info('------------------------Stream Stop -----------------------------')
                

        
    def Update_value_and_time_elapsed(self,aValue):
        self.progressBar_Gcode.setValue(aValue)
        try:            
            if aValue==100:
                self.xyz_update_thread.Stop_Timer()                 
        except:
            pass

    def Connect_Actions(self):
        self.pushButton_Connect.clicked.connect(self.PB_Connect)
        self.pushButton_Refresh.clicked.connect(self.PB_Refresh)
        self.pushButton_SetPos.clicked.connect(self.PB_Set_Position)
        self.pushButton_Reset.clicked.connect(self.PB_Reset_Signal)
        self.pushButton_Go.clicked.connect(self.PB_Go)
        self.pushButton_Pause_Resume.clicked.connect(self.PB_Pause_Resume)
        self.pushButton_MoveStop.clicked.connect(self.PB_MoveStop)
        self.pushButton_Hold_Start_Gcode.clicked.connect(self.PB_Pause_Resume)
        self.pushButton_StopGcode.clicked.connect(self.PB_StopGcode)

        self.actionSave_Config.triggered.connect(self.Save_config_to_file)
        self.actionReload_Interface_Configuration.triggered.connect(self.Reload_Interface_Configuration)
        '''
        self.actionOpen.triggered.connect()         
        self.actionLoad_Gcode.triggered.connect() 
        self.actionSave_Gcode.triggered.connect() 
        self.actionSave_Gimage_Config.triggered.connect() 
        self.actionLoad_Gimage_Config.triggered.connect() 
        self.actionLoad_Image.triggered.connect() 
        self.actionSave_Processed_Image.triggered.connect() 
        self.actionSave_Gimage_Gcode.triggered.connect() 
        self.actionSave_svg_Gimage.triggered.connect() 
        '''
        self.actionLayer_Selection.triggered.connect(self.Open_LayerSelectionToolDialog)
        self.actionResize.triggered.connect(self.Open_ResizeToolDialog)
        self.actionCommand_Configuration.triggered.connect(self.Open_CommandConfigurationDialog)
        self.actionTranslate_Code.triggered.connect(self.Open_TranslateToolDialog)
        #Aboutbox
        self.actionAbout.triggered.connect(self.Show_aboutbox)
        
        self.comboBox_ConfigItem.currentIndexChanged.connect(self.Combo_config_Select)
        self.tableWidget_Config.cellClicked.connect(self.Config_Table_cellClick)
        self.pushButton_SetConfig.clicked.connect(self.Set_Config_Value)
        self.pushButton_RefreshConfig.clicked.connect(self.PB_RefreshConfig)

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
        self.lineEdit_Gcode.returnPressed.connect(self.PB_Gcodesend)
        self.pushButton_Home.clicked.connect(self.PB_Home)
        self.pushButton_Home_X.clicked.connect(self.PB_HomeX)
        self.pushButton_Home_Y.clicked.connect(self.PB_HomeY)
        self.pushButton_Home_Z.clicked.connect(self.PB_HomeZ)
        self.pushButton_CleanAlarm.clicked.connect(self.PB_CleanAlarm)

        #self.tabWidget.tabs.tabBarClicked(2).connect(self.Fill_Config_Combo_and_Table)
        self.pushButton_LoadGcode.clicked.connect(self.PB_LoadGcode)
        self.pushButton_SaveGcode.clicked.connect(self.PB_SaveGcode_)
        self.PushButton_RunGcodeScript.clicked.connect(self.PB_RunGcodeScript)
        self.pushButton_Emergency.clicked.connect(self.PB_Emergency)

        self.pushButton_StopGcode.clicked.connect(self.PB_StopGcode)

        self.pushButton_Open_Image.clicked.connect(self.PB_Open_Image)
        self.pushButton_Load_Image_Config.clicked.connect(self.PB_Open_Image_Config)
        self.pushButton_Save_Image_Config.clicked.connect(self.PB_Save_Image_Config)
        self.pushButton_Set_Changes_Image_Config.clicked.connect(self.PB_Set_Changes_Image_Config)

        self.comboBox_Image_Process.currentIndexChanged.connect(self.Combo_Image_Process_Select)
        self.comboBox_Tool_Select.currentIndexChanged.connect(self.Combo_Tool_Select)
        self.comboBox_Technique.currentIndexChanged.connect(self.Combo_Technique_Select)
        self.pushButton_Process_Image.clicked.connect(self.PB_Process_Image)

        self.pushButton_Generate_Gimage_Code.clicked.connect(self.PB_Generate_Gimage_Code)

        self.spinBox_Stream_Linefrom.valueChanged.connect(self.Spinbox_val_change_from)
        self.spinBox_Stream_Lineto.valueChanged.connect(self.Spinbox_val_change_to)

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
        self.IsRunning_event= threading.Event()
        self.IsRunning_event.clear()
        self.XYZRobot_com_port ='COM12'
        self.Version =__version__
        self.author=__author__ 
        self.state_xyz=0
        self.Status=''
        self.x_pos = 0
        self.y_pos = 0
        self.z_pos = 0
        self.DeltaX= 1
        self.DeltaY= 1
        self.DeltaZ= 1
        self.Feedrate= None
        self.XYZRobot_found=0
        self.Config_Table_NumRows=0
        self.Config_Table_NumCols=0
        self.isoncheckedstate_checkbox=False
        self.IsImageThread=False
        self.LoggerCount=0
        #------------
        self.G_Image=GImage() #Class instance initialization
        #self.G_Image.Set_Initial_Image_Config_Data() # Setup Variables
        # this ensures the label can also re-size downwards
        self.label_Image_Preview.setMinimumSize(1, 1)
        # get resize events for the label        
        self.label_Image_Preview.setAlignment(QtCore.Qt.AlignCenter)
        #self.setCentralWidget(self.label_Image_Preview)
        #self.tabWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        QtWidgets.QApplication.instance().processEvents()        
        #self.label_Image_Preview.adjustSize()
        self.label_Image_Preview = QLabel_altered(self.groupBox_Image_Preview)
        self.gridLayout_10.addWidget(self.label_Image_Preview, 0, 0, 1, 1)
        self.label_Image_Preview.setToolTip("Double Click to Open Image")   
        self.label_Image_Preview_Processed = QLabel_altered(self.groupBox_Image_Preview_Processed)
        self.gridLayout_11.addWidget(self.label_Image_Preview_Processed, 0, 0, 1, 1)
        self.label_Image_Preview_Processed.setToolTip("Double Click to Open Image")
        self.connect_label_actions()
        self.Fill_Image_process_Tool_Technique_Combo()
        self.Actual_Interface=0 #0=Grbl,1=TinyG,2=Marlin
        self.Stream_Linefrom=0
        self.Stream_Lineto=0

    def connect_label_actions(self):    
        #self.label_Image_Preview.clicked.connect(self.Image_Preview_Clicked) 
        self.label_Image_Preview.resize.connect(self.Image_Preview_Resized) 
        #self.label_Image_Preview_Processed.clicked.connect(self.Image_Preview_Clicked) 
        self.label_Image_Preview_Processed.resize.connect(self.Processed_Image_Preview_Resized)        
        self.label_Image_Preview.left_clicked[int].connect(self.left_click)
        self.label_Image_Preview.right_clicked[int].connect(self.right_click)
        self.label_Image_Preview_Processed.left_clicked[int].connect(self.left_click_P)
        self.label_Image_Preview_Processed.right_clicked[int].connect(self.right_click_P)

    def Open_CommandConfigurationDialog(self):        
        self.CCDialog.openCommandConfigDialog()

    def Open_TranslateToolDialog(self):  
        try:
            isok=self.TTDialog.Is_Translating
            newTTD=False
        except:
            newTTD=True
            pass
        if newTTD==True:
            self.TTDialog=class_TTD.TranslateToolDialog(self.Actual_Interface,None,None)   
            self.TTDialog.save_gcode_to_file[str].connect(self.SaveGcode_Temp)    
            self.TTDialog.DTTui.buttonBox_TTD.accepted.connect(self.TTD_acceptbuttonClicked)  
            self.TTDialog.DTTui.buttonBox_TTD.rejected.connect(self.TTD_rejectbuttonClicked) 
        else:
            self.TTDialog.Dialog_TTD.show()

    def TTD_acceptbuttonClicked(self):
        print('TTD Accept clicked')
    
    def TTD_rejectbuttonClicked(self):
        print('TTD Reject clicked')
        #self.TTDialog.quit()

    def SaveGcode_Temp(self,f_n):
        self.PB_SaveGcode(f_n)

    def Open_ResizeToolDialog(self):
        RTD_List=self.G_Image.RTD_Get_Data_List()
        self.RTDialog=class_RTD.ResizeToolDialog(RTD_List)
        RTD_Info=self.G_Image.RTD_Get_Units_Info_List()   
        self.RTDialog.Set_Unit_tooltip_info(RTD_Info)
        self.RTDialog.DRui.buttonBox_RTD.accepted.connect(lambda: self.RTD_buttonClicked(self.RTDialog.Resize_Data_List))             
        self.RTDialog.DRui.pushButton_RTD_Set_Resized.clicked.connect(lambda: self.RTD_buttonClicked(self.RTDialog.Resize_Data_List))
        self.Set_Image_to_RTD()

    def Set_Image_to_RTD(self):    
        if self.G_Image.Isimagetoprint == True:
            if self.G_Image.IsProcessedimagetoprint == True:
                self.RTDialog.Set_Image_to_Image_label(self.G_Image.imp)
            else:
                self.RTDialog.Set_Image_to_Image_label(self.G_Image.im)
        
    def RTD_buttonClicked(self,R_D_List):                    
        #print(R_D_List)
        self.G_Image.RTD_Set_Data_List(R_D_List)        
        self.Fill_Image_Config_Table()
        self.PB_Process_Image()        
        self.RTD_Refresh()

    def RTD_Refresh(self):    
        try:
            #Refresh info if its open
            RTD_List=self.G_Image.RTD_Get_Data_List()
            self.RTDialog.Set_Data_List(RTD_List)
            RTD_Info=self.G_Image.RTD_Get_Units_Info_List()   
            self.RTDialog.Set_Unit_tooltip_info(RTD_Info)
            self.Set_Image_to_RTD()
            self.RTDialog.Put_All()            
        except:
            pass    

    def Open_LayerSelectionToolDialog(self):   
        S_L=self.G_Image.LSTD_Get_Selected_Layers()
        N_L=self.G_Image.LSTD_Get_Num_Layers()            
        self.LSTDialog=class_LSTD.LayerSelectionToolDialog(N_L,S_L)   
        self.LSTDialog.DSLui.buttonBox_LSTD.accepted.connect(lambda: self.LSTD_buttonClicked(self.LSTDialog.Selected_Layers))             
        self.LSTDialog.DSLui.pushButton_LSTD_Set_Preview.clicked.connect(lambda: self.LSTD_Set_buttonClicked(self.LSTDialog.Selected_Layers))
        self.LSTDialog.DSLui.checkBox_LSTD_checkall.clicked.connect(self.LSTR_Checkall_checkbox)
        self.Fill_comboBox_LSTD_Image_Process() 
        Color_Palette=self.G_Image.Get_Color_Palette()
        self.LSTDialog.Assign_Colors_to_Labels(Color_Palette)
    
    def LSTR_Checkall_checkbox(self):
        val=self.LSTDialog.DSLui.checkBox_LSTD_checkall.isChecked()
        self.LSTDialog.Clear_allcheckbox(val)
        

    def LSTD_Set_buttonClicked(self,S_L):
        self.LSTD_buttonClicked(S_L)        

    def LSTD_buttonClicked(self,S_L):
        #print(S_L)
        data=self.Get_data_from_Image_Config_Table()
        sss=0
        SLtext=''
        IncLastLtxt='False'
        for iii in S_L:
            if sss>0:
                SLtext=SLtext+' '        
            if iii==-1:
                IncLastLtxt='True'
            if iii==data['Img_Num_Colors']-1: 
                IncLastLtxt='True'   
            SLtext=SLtext+str(iii)
            sss=sss+1    
        data['Selected_Layers']=SLtext                
        data['Include_Last_Layer']=IncLastLtxt
        self.Set_Data_in_Image_Config(data)
        self.G_Image.Process_Image()
        self.PB_Process_Image()

    def Fill_comboBox_LSTD_Image_Process(self):
        imgprocess=self.G_Image.Image_Process_List
        self.LSTDialog.DSLui.comboBox_LSTD_Image_Process.clear()
        for ccc in imgprocess:
            self.LSTDialog.DSLui.comboBox_LSTD_Image_Process.addItem(ccc)
        self.Change_comboBox_LSTD_from_Image_Process()    
        self.LSTDialog.DSLui.comboBox_LSTD_Image_Process.currentIndexChanged.connect(self.Change_comboBox_Image_Process_from_LSTD)    

    def Change_comboBox_Image_Process_from_LSTD(self):
        if self.LSTDialog.DSLui.comboBox_LSTD_Image_Process.currentText()!=self.comboBox_Image_Process.currentText():    
            index= self.comboBox_Image_Process.findText(self.LSTDialog.DSLui.comboBox_LSTD_Image_Process.currentText(),QtCore.Qt.MatchFixedString)
            self.comboBox_Image_Process.setCurrentIndex(index)   
            Color_Palette=self.G_Image.Get_Color_Palette()
            self.LSTDialog.Assign_Colors_to_Labels(Color_Palette)                   
            
    def Change_comboBox_LSTD_from_Image_Process(self):
        if self.LSTDialog.DSLui.comboBox_LSTD_Image_Process.currentText()!=self.comboBox_Image_Process.currentText():                 
            index= self.LSTDialog.DSLui.comboBox_LSTD_Image_Process.findText(self.comboBox_Image_Process.currentText(),QtCore.Qt.MatchFixedString)
            self.LSTDialog.DSLui.comboBox_LSTD_Image_Process.setCurrentIndex(index)   
            Color_Palette=self.G_Image.Get_Color_Palette()
            self.LSTDialog.Assign_Colors_to_Labels(Color_Palette)                             

    def left_click(self, nb):
        if nb == 1: 
            print('Single left click')
        else: 
            self.G_Image.show_image() #print('Double left click')

    def right_click(self, nb):
        if nb == 1: print('Single right click')
        else: print('Double right click')

    def left_click_P(self, nb):
        if nb == 1: print('Single left click')
        else: print('Double left click')

    def right_click_P(self, nb):
        if nb == 1: print('Single right click')
        else: print('Double right click')
    
    def Configuration_id_Changed(self,newid):
        self.Actual_Interface=newid
        if self.XYZRobot_found==1:
            log.info("Changing command handler configuration to id {}".format(newid))             
            self.xyz_thread.CH.id=newid
            self.xyz_thread.CH.Setup_Command_Handler(True)
            aname=self.xyz_thread.CH.Get_action_format_from_id(self.xyz_thread.CH.Configdata,'interfaceName',self.xyz_thread.CH.id)
            log.info("Command handler configuration {} Set".format(aname))             

    def Configuration_Changed_Refresh(self,afilename):
        #print(self.XYZRobot_found)
        if self.XYZRobot_found==1:
            if self.xyz_thread.CH.filename==afilename:   
                log.info("Close connection to Machine refresh Threads using "+afilename+' configurations.')             
                #log.info("Refreshing Configuration in Threads using "+afilename)             
                #while self.xyz_thread.IsRunning_event.wait(0.5):
                #    log.info("....waiting to refresh configuration")
                #self.xyz_thread.CH.Setup_Command_Handler(log_check=False)
        else:            
            log.info("Event filename changed!"+afilename)
        


    def Image_Preview_Clicked(self):
        print("Image clicked!!!!! ")

    def Processed_Image_Preview_Resized(self):
        #print("Image resized!!!!!") 
        if self.G_Image.IsProcessedimagetoprint == True:
            self.label_Image_Preview_Processed.setPixmap(self.the_pixmap_p.scaled(
                self.label_Image_Preview_Processed.size(), QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation))

    def Image_Preview_Resized(self):
        #print("Image resized!!!!!") 
        if self.G_Image.Isimagetoprint == True:
            if (self.the_pixmap):
                self.label_Image_Preview.setPixmap(self.the_pixmap.scaled(
                    self.label_Image_Preview.size(), QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation))               

    def PB_Set_Changes_Image_Config(self):
        data=self.Get_data_from_Image_Config_Table()
        Value=self.G_Image.Get_Variable_from_Image_Config_Data('Img_Num_Colors')        
        self.Set_Data_in_Image_Config(data)
        self.G_Image.Process_Image()
        try:    
            if data['Img_Num_Colors']!=Value:                
                self.LSTDialog.close()
            self.Open_LayerSelectionToolDialog()
        except Exception as e:
            #log.error(e)
            pass
        

    def PB_Emergency(self):
        self.killer_event.set()
    
    def PB_StopGcode(self):
        self.stream_event_stop.set()
        self.xyz_thread.grbl_stop()
        try:
            self.xyz_gcodestream_thread.stoping_event.set()                      
            self.xyz_thread.ser_read_thread.Streamwriting=False                                                                          
            self.Stop_Clear() 
        except:
            pass

    def PB_RunGcodeScript(self):        
        if self.checkBox_Gcode.isChecked()==True or self.isoncheckedstate_checkbox==True:
            self.isoncheckedstate_checkbox=not self.isoncheckedstate_checkbox # Case was not terminated correctly last time
            self.xyz_thread.send_queue_command('checkgcodeMode_On',{},True) 
            time.sleep(0.2) # wait to react 
        log.info("Sending stream to thread")    
        text2stream=self.Get_Text_to_Stream(self.Stream_Linefrom,self.Stream_Lineto)
        self.P_Bar_Update_Gcode.SetStatus(0)
        self.P_Bar_buffer_Gcode.SetStatus(0)
        self.ComboBox_Select_GcodeStreamType()
        self.xyz_gcodestream_thread.type_of_stream=int(self.GcodeStreamType)        
        self.xyz_update_thread.Start_Timer()
        self.xyz_gcodestream_thread.Stream_queue(text2stream,self.P_Bar_Update_Gcode,self.P_Bar_buffer_Gcode)

        if self.isoncheckedstate_checkbox==True:
            self.xyz_thread.send_queue_command('checkgcodeMode_Off',{},True) 
            log.info("Checkmode Disabled and Grbl reset") 
            self.isoncheckedstate_checkbox=False
            self.checkBox_Gcode.setChecked(False)
            
    def Get_Text_to_Stream(self,linefrom=-1,lineto=0):
        if linefrom<=0:
            text2stream=self.plaintextEdit_GcodeScript.toPlainText() 
            return text2stream
        text2stream=''
        f_n=self.get_temppathFilename()
        self.PB_SaveGcode(f_n)        
        mylines = []                             # Declare an empty list named mylines.
        with open (f_n, 'rt') as myfile: # Open lorem.txt for reading text data.
            for myline in myfile:                # For each line, stored as myline,
                mylines.append(myline)           # add its contents to mylines.
        
        num_lines=self.plaintextEdit_GcodeScript.blockCount()
        
        if linefrom>num_lines:
            log.error('Wrong Stream Start Line Number!')
        if lineto>=num_lines or lineto<linefrom:
            lineto=num_lines
        if linefrom>=1 and lineto<=num_lines:
            block=self.plaintextEdit_GcodeScript.document().findBlockByLineNumber(linefrom-1)
            #block.text()
            for n_line, myline in enumerate(mylines, start=1):
                if n_line>=linefrom and n_line<=lineto:
                  text2stream=text2stream+myline           # add its contents to txt.
        return text2stream

    def get_appPath(self):
        # determine if application is a script file or frozen exe
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(__file__)
        return application_path      

    def get_temppathFilename(self):
        temppath=self.get_appPath()+os.sep+'temp'+os.sep
        try:
            os.mkdir(temppath)
        except:
            pass
        return temppath+'__TempMStream__.gcode'

    def PB_LoadGcode(self):        
        filename=aDialog.openFileNameDialog(0) #0 gcode
        
        if filename is not None:
            log.info('Opening:'+filename)
            self.Spinbox_val_change_from(0)
            #self.Spinbox_val_change_to(0)
            try:
                self.plaintextEdit_GcodeScript.clear()
                with open(filename, 'r') as yourFile:
                    #self.plaintextEdit_GcodeScript.setText(yourFile.read())        #textedit
                    self.plaintextEdit_GcodeScript.appendPlainText(yourFile.read())        #plaintextedit
                              
                yourFile.close() 
                self.Set_from_to_Spinbox(self.plaintextEdit_GcodeScript.blockCount())               
            except Exception as e:
                log.error(e)
                log.info("File was not read!")

    def PB_SaveGcode_(self):
        self.PB_SaveGcode(f_n=None)

    def PB_SaveGcode(self,f_n=None):        
        if f_n==None:
            filename=aDialog.saveFileDialog(0) #0 gcode        
        else:
            filename=f_n

        if filename is not None:       
            mfile=re.search('(\.gcode$)',filename)
            try:
                if mfile.group(1)!='.gcode': 
                    filename=filename+'.gcode'
            except:
                filename=filename+'.gcode'        
            log.info('Saving:'+filename) 
            try:
                with open(filename, 'w') as yourFile:
                    yourFile.write(str(self.plaintextEdit_GcodeScript.toPlainText()))                
                yourFile.close()                
            except Exception as e:
                log.error(e)
                log.info("File was not Written!")

    def setImage(self,alabel, image):
        alabel.setPixmap(QtGui.QPixmap.fromImage(image).scaled(
                alabel.size(), QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation))
    def setPixmap(self,alabel, aPixmap):
        alabel.setPixmap(aPixmap.scaled(
                alabel.size(), QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation))
        #self.label_Image_Preview.setPixmap(aPixmap)    

    def Show_Image_Preview(self):
        if self.G_Image.Isimagetoprint == True:
            self.the_pixmap=QtGui.QPixmap(self.G_Image.imagefilename)
            if (self.the_pixmap):
                self.the_pixmap=self.the_pixmap
            else:
                qim = ImageQt(self.G_Image.im)
                self.the_pixmap=QtGui.QPixmap.fromImage(qim) 
            self.setPixmap(self.label_Image_Preview,self.the_pixmap)    
            try:
                self.RTD_Refresh()
            except:
                pass
    
    def Show_Processed_Image_Preview(self):
        #log.info('Image Process preview entered')
        if self.G_Image.IsProcessedimagetoprint==True:
            qimp = ImageQt(self.G_Image.imp)
            self.the_pixmap_p=QtGui.QPixmap.fromImage(qimp)            
            #log.info('Image Process preview showing')
            self.setPixmap(self.label_Image_Preview_Processed,self.the_pixmap_p)
            try:
                self.RTD_Refresh()
            except:
                pass
    
    def PB_Generate_Gimage_Code(self):
        
        if self.IsImageThread==False:
            self.Start_Image_Thread()        
        if self.IsImageThread==True:
            Gimage_Data=self.G_Image.Get_Gimage_Data_for_Stream()
            if self.G_Image.IsProcessedimagetoprint==True:
                self.plaintextEdit_GcodeScript.clear()
                Gimage_Code=self.xyz_gimagestream_thread.Generate_Gimage_Code(self.G_Image.imp,Gimage_Data,self.P_Bar_Update_Gimage)
                self.plaintextEdit_GcodeScript.appendPlainText(Gimage_Code)
                self.P_Bar_Update_Gimage.SetStatus(0)                
                log.info('GImage Gcode Ready!')
            else:    
                log.info('No processed image available!')
        
    def PB_Process_Image(self):
        self.G_Image.Process_Image()
        self.Show_Processed_Image_Preview()
        try:
            self.Set_Image_to_RTD()
        except:
            pass

           
    def PB_Save_Image_Config(self):
        self.Save_Image_config_to_file()

    def PB_Open_Image_Config(self):    
        data=self.Load_Image_config_from_file()
        self.Set_Data_in_Image_Config(data)
    
    def Set_Data_in_Image_Config(self,data):
        if type(data) != 'NoneType':
            try:
                for ccc in data:
                    if ccc in self.G_Image.Image_Config_Data:
                        if not '_Info' in ccc and not '_Type' in ccc and not '_Unit' in ccc:                            
                            self.G_Image.Image_Config_Data=self.G_Image.Set_ConfVar(self.G_Image.Image_Config_Data,ccc,data[ccc],data[ccc+'_Unit'],data[ccc+'_Type'],data[ccc+'_Info'])                            
                            #print(aaa+':'+data[ccc])
                            #break                
            except Exception as e:
                log.error(e)
                log.error('Some items could not be read! ' +ccc )
                pass   
        #print('Read from file:'+self.G_Image.Image_Config_Data['Robot_XYZ']+' '+data['Robot_XYZ'])     
        self.G_Image.Check_Image_Config_Data()
        self.Fill_Image_Config_Table()    

    def PB_Open_Image(self):
        filename=aDialog.openFileNameDialog(1) #1 Images
        
        if filename is not None:
            log.info('Opening:'+filename)
            try:    
                            
                self.G_Image.open_image(filename)                                
                self.Show_Image_Preview()
                self.PB_Set_Changes_Image_Config()
                self.Show_Processed_Image_Preview()
            except Exception as e:
                log.error(e)
                log.info("Could not open Image!")
    

    def Set_Icons_Status_OnOFF(self,Is_on):
        self.StatusConnected=Is_on
        self.groupBox_XYZ.setEnabled(self.StatusConnected)
        self.label_ConnectedStatus.setEnabled(self.StatusConnected)
        self.tab_2.setEnabled(self.StatusConnected)
        self.Enable_Gcode_View(False)

    def Enable_Gcode_View(self,Istotal=True):        
        if Istotal==True:
            self.tab_3.setEnabled(self.StatusConnected)
        else:
            self.frame_GcodePauseStop.setEnabled(self.StatusConnected)
            self.checkBox_Gcode.setEnabled(self.StatusConnected)
            self.PushButton_RunGcodeScript.setEnabled(self.StatusConnected)
            self.comboBox_GcodeStreamType.setEnabled(self.StatusConnected)
            self.groupBox_Gcode.setEnabled(self.StatusConnected)

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
        self.xyz_thread.Send_Homing(0)

    def PB_HomeX(self):
        self.xyz_thread.Send_Homing(1)

    def PB_HomeY(self):
        self.xyz_thread.Send_Homing(2)        

    def PB_HomeZ(self):
        self.xyz_thread.Send_Homing(3)    

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
        try:
            if self.lineEdit_Feedrate.text() != '':
                value=int(self.lineEdit_Feedrate.text())
                self.Feedrate=value
                self.lineEdit_Feedrate.setText(str(self.Feedrate))    
        except:      
            self.Feedrate=None 
            self.lineEdit_Feedrate.setText('')    
        #self.Fill_Deltas()    

    def Move_Delta(self,DeltaX,DeltaY,DeltaZ):    
        self.Show_inbutton_pause()
        self.Get_Actual_Pos()                
        self.ini_pos=[0*self.x_pos,0*self.y_pos,0*self.z_pos]                
        self.end_pos=[self.ini_pos[0]+DeltaX,self.ini_pos[1]+DeltaY,self.ini_pos[2]+DeltaZ]               
        if self.XYZRobot_found==1:
            #Set relative movement
            self.xyz_thread.send_queue_command('relativePositioning',{},True)                        
            log.info("Delta Move: dX = " + str(DeltaX) + ", dY = " + str(DeltaY)+", dZ = " + str(DeltaZ))            
            if self.Feedrate==None:
                self.xyz_thread.goto_xyz(self.end_pos[0],self.end_pos[1],self.end_pos[2])
            else:
                self.xyz_thread.goto_xyzf(self.end_pos[0],self.end_pos[1],self.end_pos[2],self.Feedrate)                        
            #Set absolute movement            
            self.xyz_thread.send_queue_command('absolutePositioning',{},True)
        else:
            log.info("XYZ Robot Not Found for Moving") 

    def PB_Gcodesend(self):
        gcodeline=self.lineEdit_Gcode.text()
        log.info("Sending Gcode: "+gcodeline)
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
        try:       
            if self.LoggerCount==0:
                self.textEdit_Logger.setText('')
                self.textEdit_Logger.setFontWeight(QtGui.QFont.Normal)                
            self.textEdit_Logger.append(sss)
            if self.LoggerCount>10000:
                self.LoggerCount=0        
            else:
                self.LoggerCount=self.LoggerCount+1
        except:
            pass
    
        

    def Start_Image_Thread(self):
        try:            
            #self.xyz_gimagestream_thread=Image_Gcode_Stream(self.xyz_thread,self.killer_event,self.xyz_thread.grbl_event_hold,self.stream_event_stop)
            self.xyz_gimagestream_thread=Image_Gcode_Stream(self.killer_event,self.plaintextEdit_GcodeScript) 
            self.xyz_gimagestream_thread.setName("Gimage Stream") 
            self.xyz_gimagestream_thread.start()
            log.info("SUCCESS: Image to Gcode thread Initialized :)")  
            self.IsImageThread=True 
            
        except Exception as e:               
            #log.error("failed to initialise xyz_thread: ", sys.exc_info()[0])
            log.error(e)
            log.error("Failed to initialise Image thread :( -> No Image to Gcode")
            self.IsImageThread=False
            
    def Start_XYZ_Thread(self):            
        try:
            XYZRobot_port=self.COMPort            
            #Baudrate=self.COMBaudRate.encode('utf-8')
            Baudrate=int(self.COMBaudRate)
            #self.xyz_thread = XYZGrbl(XYZRobot_port, Baudrate, self.killer_event,self.IsRunning_event)
            self.xyz_thread = XYZMulti(XYZRobot_port, Baudrate, self.killer_event,self.IsRunning_event)            
            self.xyz_thread.start()                        
            self.stream_event_stop= threading.Event()
            self.stream_event_stop.clear()
            self.xyz_gcodestream_thread=thread_Gcode_Stream.XYZ_Gcode_Stream(self.xyz_thread,self.killer_event,self.xyz_thread.grbl_event_hold,self.stream_event_stop,self.IsRunning_event)
            self.xyz_gcodestream_thread.setName("XYZ Gcode Stream") 
            self.xyz_gcodestream_thread.start()
            self.xyz_update_thread=thread_XYZ_Update.XYZ_Update(self.ST,self.xyz_thread,self.xyz_gcodestream_thread,self.killer_event)
            self.xyz_update_thread.setName("XYZ Update") 
            self.xyz_update_thread.start()
            if self.IsImageThread==False:
                self.Start_Image_Thread()
            if self.IsImageThread==True:                    
                self.xyz_gimagestream_thread.Set_xyz_thread(self.xyz_thread,self.stream_event_stop)

            log.info("First Run Calibrating to: X = " + str(self.x_pos) + ", Y = " + str(self.y_pos) + ", Z = " + str(self.z_pos))
            self.xyz_thread.home_offset_xyz(self.x_pos,self.y_pos,self.z_pos)
            self.XYZRobot_found=1
            
            log.info("SUCCESS: XYZ Initialized :)")   
            
        except Exception as e:   
            self.XYZRobot_found=0
            #log.error("failed to initialise xyz_thread: ", sys.exc_info()[0])
            log.error(e)
            log.error("Failed to initialise xyz_thread :( -> No Robot ")
            self.Show_Message("Error","Failed to Initialize XYZ Robot :( (Check Port)")
            #print("Is XYZRobot in port "+ XYZRobot_port + "?")
        #finally:
        #    self.App_Close_Event()

    def Show_Message(self,title,text):
        msg=QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.exec_()

    def Set_Actual_Position_Values(self,xxx,yyy,zzz):        
        try:
            self.xyz_update_thread.Set_Actual_Position_Values(xxx,yyy,zzz)
            self.ST.Signal_Data(self.xyz_update_thread.read())
            '''
            self.x_pos = xxx
            self.y_pos = yyy
            self.z_pos = zzz
            self.xyz_update_thread.x_pos = xxx
            self.xyz_update_thread.y_pos = yyy
            self.xyz_update_thread.z_pos = zzz
            self.xyz_update_thread.Set_Actual_Position_Values(xxx,yyy,zzz)
            self.xyz_update_thread.state_xyz=self.state_xyz            
            self.xyz_update_thread.Status=self.Status   
            self.xyz_update_thread.Set_Actual_State_Value(self.state_xyz,self.Status)
            '''
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
        
    def Fill_Image_process_Tool_Technique_Combo(self):        
        self.comboBox_Image_Process.clear()  
        self.comboBox_Tool_Select.clear()
        techniques=self.G_Image.Technique_List
        tools=self.G_Image.Tool_List
        imgprocess=self.G_Image.Image_Process_List
        for ccc in imgprocess:
            self.comboBox_Image_Process.addItem(ccc) 
        for ccc in tools:
            self.comboBox_Tool_Select.addItem(ccc)  
        for ccc in techniques:
            self.comboBox_Technique.addItem(ccc)   
            

    def Fill_Config_Combo_and_Table(self):    
        if self.XYZRobot_found==1:       
            self.comboBox_ConfigItem.clear()  
            if self.Is_Config_Table_Empty()==True:
                config=self.xyz_thread.read_grbl_config(True,False)
            else:
                config=self.xyz_thread.read_grbl_config(False,False)   
            for ccc in config:
                if not '_Info' in ccc and not '_Type' in ccc:
                    self.comboBox_ConfigItem.addItem(ccc) 
            self.Fill_Config_Table()        
    
    def Fill_Image_Config_Table(self):  
        #log.info("Filling Gimage Configuration!")
        self.tableWidget_Image_Config.clear()  
        config=self.G_Image.Get_Image_Config_Data()
        Num_Items=0
        for ccc in config:
            if not '_Info' in ccc and not '_Type' in ccc and not '_Unit' in ccc:                                
                Num_Items=Num_Items+1
        #log.info("Filling Gimage Configuration! Items found "+ str(Num_Items))        
        self.Image_Config_Table_NumRows=Num_Items        
        self.Image_Config_Table_NumCols=5
        self.tableWidget_Image_Config.setRowCount(self.Image_Config_Table_NumRows)
        self.tableWidget_Image_Config.setColumnCount(self.Image_Config_Table_NumCols)
        self.tableWidget_Image_Config.setHorizontalHeaderLabels(["Id", "Value","Unit", "Info", "Type"])
        self.tableWidget_Image_Config.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)            
        iii=0
        for ccc in config:
            if not '_Info' in ccc and not '_Type' in ccc and not '_Unit' in ccc:                
                self.tableWidget_Image_Config.setItem(iii,0, QTableWidgetItem(ccc))
                self.tableWidget_Image_Config.setItem(iii,1, QTableWidgetItem(str(config[ccc])))
                self.tableWidget_Image_Config.setItem(iii,2, QTableWidgetItem(str(config[ccc+'_Unit'])))
                self.tableWidget_Image_Config.setItem(iii,3, QTableWidgetItem(str(config[ccc+'_Info'])))
                self.tableWidget_Image_Config.setItem(iii,4, QTableWidgetItem(str(config[ccc+'_Type'])))
                iii=iii+1
        self.tableWidget_Image_Config.resizeColumnsToContents()
        self.tableWidget_Image_Config.adjustSize()
        self.groupBox_Image_Select.adjustSize()

    def Fill_Config_Table(self):
        if self.XYZRobot_found==1:       
            self.tableWidget_Config.clear()
            config=self.xyz_thread.read_grbl_config(True,False)   
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
    
    def Combo_Image_Process_Select(self):
        self.G_Image.Selected_Image_Process=self.comboBox_Image_Process.currentText()
        try:
            self.Change_comboBox_LSTD_from_Image_Process()
        except:
            pass
        self.G_Image.Process_Image()

    def Combo_Tool_Select(self):
        self.G_Image.Selected_Tool=self.comboBox_Tool_Select.currentText()

    def Combo_Technique_Select(self):
        self.G_Image.Selected_Technique=self.comboBox_Technique.currentText()

    def Combo_config_Select(self):
        self.Combo_Config_Selected=self.comboBox_ConfigItem.currentText()        
        config=self.xyz_thread.read_grbl_config(False,False)   
        for ccc in config:
            if not '_Info' in ccc and not '_Type' in ccc:
                if ccc == self.Combo_Config_Selected:
                    self.lineEdit_ConfigValue.setText(str(config[ccc])) 
                    self.label_ConfigInfo.setText(str(config[ccc+'_Info']))
                    self.label_ConfigInfo.adjustSize()
                    break
    
    def Is_Config_Table_diff_to_device(self):
        config=self.xyz_thread.read_grbl_config(True,False)
        is_different=False
        for row in range(self.Config_Table_NumRows):                        
            hhh=self.tableWidget_Config.item(row, 0).text()
            hhhval=self.tableWidget_Config.item(row, 1).text()            
            #log.info(self.xyz_thread.Read_Config_Parameter(hhh.replace('$', '')))                        
            if str(config[hhh])!=hhhval:
                is_different=True
                break
        return is_different        
            
    def write_Config_to_device(self):
        config=self.xyz_thread.read_grbl_config(False,False)
        changed=False
        for row in range(self.Config_Table_NumRows):                        
            hhh=self.tableWidget_Config.item(row, 0).text()                                 
            hhhval=self.tableWidget_Config.item(row, 1).text()  
            #hhhinfo=self.tableWidget_Config.item(row, 2).text()  
            hhhtype=self.tableWidget_Config.item(row, 3).text()                          
            if hhh in list(config):                
                if str(config[hhh])!=hhhval:                        
                    Value=self.xyz_thread.set_correct_type(hhhval,False)            
                    isaccepted=self.xyz_thread.change_grbl_config_parameter(hhh,Value)
                    if isaccepted==False:
                        log.error('Parameter '+ hhh + ' was not accepted as '+str(Value)) 
                        changed=True
                        break
                    changed=True
                    while self.xyz_thread.Is_system_ready()==False:
                        time.sleep(0.2)
                        log.info("Stuck here?")
        #No need is done in fill                
        #if changed==True:
        #    config=self.xyz_thread.read_grbl_config(True,False)

    def Get_data_from_Image_Config_Table(self):   
        data={}             
        for row in range(self.Image_Config_Table_NumRows):                        
            hhh    =self.tableWidget_Image_Config.item(row, 0).text()                        
            hhhval =self.tableWidget_Image_Config.item(row, 1).text()  
            hhhunit=self.tableWidget_Image_Config.item(row, 2).text()  
            hhhinfo=self.tableWidget_Image_Config.item(row, 3).text()  
            hhhtype=self.tableWidget_Image_Config.item(row, 4).text()  
            try:
                if hhhtype =='int':
                    Value=int(hhhval)
                elif hhhtype == 'float':
                    Value=float(hhhval)
                else:
                    Value=str(hhhval)  
            except:                          
                Value=self.G_Image.Get_Variable_from_Image_Config_Data(hhh) #Revert to last value           
            for ccc in list(self.G_Image.Image_Config_Data):
                if ccc == hhh:
                    data[ccc]=Value
                    data[ccc+'_Unit']=hhhunit
                    data[ccc+'_Info']=hhhinfo
                    data[ccc+'_Type']=hhhtype
        
                
        return data            

    def Is_Image_Config_Table_Empty(self):
        #log.info('Numrows->'+str(self.Config_Table_NumRows))
        if self.Image_Config_Table_NumRows==0:
            return True
        else:
            return False          

    def Is_Config_Table_Empty(self):
        #log.info('Numrows->'+str(self.Config_Table_NumRows))
        if self.Config_Table_NumRows==0:
            return True
        else:
            return False
    
    def PB_RefreshConfig(self):
        self.tableWidget_Config.clear()
        self.Fill_Config_Combo_and_Table()


    def Set_Config_Value(self):
        if self.Is_Config_Table_Empty()==True:
            self.Fill_Config_Combo_and_Table()
        if self.Is_Config_Table_diff_to_device()==True:
            log.info("Writting Configuration Table to Device")
            self.write_Config_to_device()
            self.Fill_Config_Table()
        else:
            log.info("No Configuration Changes found")
    
    def Load_Image_config_from_file(self):
        filename=aDialog.openFileNameDialog(2) #0 gcode, 1 Images 2 txt else all 
        data={}
        if filename is not None:
            
            log.info('Opening:'+filename)
            try:
                self.plaintextEdit_GcodeScript.clear()
                with open(filename, 'r') as yourFile:
                    #self.plaintextEdit_GcodeScript.setText(yourFile.read())        #textedit
                    linelist=yourFile.readlines() #makes list of lines  
                data=self.Get_Config_Data_From_List(linelist)                                                
                yourFile.close()                
            except Exception as e:
                log.error(e)
                log.info("File was not read!")
        return data        

    
    def Get_Config_Data_From_List(self,linelist):
        data={}
        for line in linelist:
            #log.info(line)
            try:                           
                #mf = re.search('<(.*)>_<([+-]?\d*[\.,]?\d*?)>_<(.*)>_<(.*)>_<(.*)>',line)                               
                mf = re.search('<(.*)>_<(.*)>_<(.*)>_<(.*)>_<(.*)>',line)                               
            except:
                mf = None
            try:
                if mf is not None: #any type
                    #log.info('storing float')
                    #log.info('mf ->'+str(mf.groups()))
                    if mf.group(5):    
                        data[str(mf.group(1))+'_Type']=str(mf.group(5))
                    else:
                        data[str(mf.group(1))+'_Type']=''
                    if  str(mf.group(5))=='float':   
                        data[str(mf.group(1))]=float(mf.group(2))
                    elif  str(mf.group(5))=='int':   
                        data[str(mf.group(1))]=int(mf.group(2))                    
                    else:
                        data[str(mf.group(1))]=str(mf.group(2))      

                    if mf.group(3):
                        data[str(mf.group(1))+'_Unit']=str(mf.group(3))
                    else:
                        data[str(mf.group(1))+'_Unit']=''    
                    if mf.group(4):    
                        data[str(mf.group(1))+'_Info']=str(mf.group(4))
                    else:
                        data[str(mf.group(1))+'_Info']=''
                        
            except:
                log.error('Bad format for Image Config Read!')
                pass
        return data    


    def Save_Image_config_to_file(self):
        if self.Is_Image_Config_Table_Empty()==False: 
            fileName = "Image_Config_"
            ext='.txt'
            now = datetime.datetime.now()
            fileName = now.strftime("%Y-%m-%d_%H-%M")+'_'+fileName+ext

            fileName=aDialog.saveFileDialog(2) #2 is txt
            if fileName is not None:
                try:
                    
                    mfile=re.search('(\.txt$)',fileName)
                    try:
                        if mfile.group(1)!='.txt': 
                            fileName=fileName+'.txt'
                    except:
                        fileName=fileName+'.txt'        
                    file = open(fileName,'w')   
                    log.info('Saving:'+fileName)      
                    Tabledata=[]            
                    for row in range(self.Image_Config_Table_NumRows):  
                        Tabledata.append('<')                                                  
                        for col in range(self.Image_Config_Table_NumCols):
                            Tabledata.append(self.tableWidget_Image_Config.item(row, col).text())
                            if col<self.Image_Config_Table_NumCols-1:
                                Tabledata.append('>_<')                                        
                        Tabledata.append('>\n')                
                    file.writelines(Tabledata)    
                    log.info("File Saved as:" + fileName)
                    file.close()
                except Exception as e:
                    log.error(e)
                    log.info("File was not Written!")        
    
    def Reload_Interface_Configuration(self):
        if self.XYZRobot_found==1:
            try:
                self.xyz_thread.CH.Setup_Command_Handler()
                self.xyz_thread.Init_Configurations(Logcheck=True)
            except:
                pass    

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
                    log.info("File Saved as:" + fileName)
                    file.close()
                except Exception as e:
                    log.error(e)
                    log.info("File was not Written!")
            

    def Fill_COM_Combo(self):
        self.comboBox_COM.clear() 
        ports = self.Get_serial_ports()
        for port in ports:
            self.comboBox_COM.addItem(port)

    def ComboBox_Select_Item(self):
        self.COMPort=self.comboBox_COM.currentText()
        self.COMBaudRate=self.comboBox_ConnSpeed.currentText()
    
    def ComboBox_Select_GcodeStreamType(self):
        self.GcodeStreamType=self.comboBox_GcodeStreamType.currentText()                              
    
    def PB_Connect(self):
        if self.StatusConnected==False:
            self.ComboBox_Select_Item()
            log.info("Opening XYZ Robot port")
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
            log.info("Disconnecting Robot")
            self.App_Close_Event()
            self.pushButton_Connect.setText("Connect")
            
    
    def Enable_GroupXYZ_ComIcon(self):
        if self.XYZRobot_found==1:      
            self.StatusConnected=True                  
            log.info("Waiting for XYZ Robot Setup to finish")
            #log.info('-------------Reading device configuration-----------------------')
            #config=self.xyz_thread.read_grbl_config(True,True)
            #log.info('----------------------------------------------------------------')
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
        
        #self.Fill_Config_Combo_and_Table()        
        #self.groupBox_XYZ.setEnabled(True)    #---------------------HERE--->set comment this line when runs    
    
    def PB_Refresh(self):
        self.Fill_COM_Combo()

    def PB_MoveStop(self):
        if self.XYZRobot_found==1:
            self.data_LastPos= self.xyz_thread.read() #get last known value
            log.info("Resuming XYZRobot")
            self.Show_inbutton_pause()
            self.pushButton_Pause_Resume.setEnabled(False) 
            self.pushButton_Hold_Start_Gcode.setEnabled(False)
            self.xyz_thread.grbl_stop()

    def PB_Pause_Resume(self):
        if self.XYZRobot_found==1:
            self.data_LastPos= self.xyz_thread.read() #get last known value
            if self.data_LastPos['STATE_XYZ']==6: # on Hold
                log.info("Resuming XYZRobot")
                self.Show_inbutton_pause()
                self.PB_Resume()
            else:    
                log.info("Pausing XYZRobot")
                self.Show_inbutton_play()                
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
                log.info("XYZ Robot Not Found for Starting") 
            else:
                log.info("XYZ Robot Not Found for Holding") 
    
    def PB_Resume(self):
        if self.XYZRobot_found==1:
            time.sleep(0.3)
            Last_Data= self.xyz_thread.read() #get last known value
            Last_Data= self.data_LastPos
            #log.info("Starting XYZRobot--->" +str(Last_Data['STATE_XYZ']))
            if Last_Data['STATE_XYZ']==6:
                log.info("Starting XYZRobot")
                self.xyz_thread.grbl_feed_start()      
            self.pushButton_Pause_Resume.setEnabled(False) 
            self.pushButton_Hold_Start_Gcode.setEnabled(False)   
            time.sleep(0.3)          
            self.pushButton_Pause_Resume.setEnabled(True)
            self.pushButton_Hold_Start_Gcode.setEnabled(True)
        else:
            log.info("XYZ Robot Not Found for Starting") 
    
    def Show_inbutton_pause(self):
        self.pushButton_Pause_Resume.setIcon(self.Icon_pause)
        self.pushButton_Hold_Start_Gcode.setIcon(self.Icon_pause)
        self.pushButton_Pause_Resume.setText("Hold")
        self.pushButton_Hold_Start_Gcode.setText("Hold")

    def Show_inbutton_play(self):
        self.pushButton_Pause_Resume.setIcon(self.Icon_start)
        self.pushButton_Hold_Start_Gcode.setIcon(self.Icon_start)
        self.pushButton_Pause_Resume.setText("Start")
        self.pushButton_Hold_Start_Gcode.setText("Start")

    def PB_Reset_Signal(self):
        self.Show_inbutton_pause()
        
        if self.XYZRobot_found==1:
            log.info("Reseting XYZRobot")
            #self.XYZRobot_port.write(str.encode(chr(24)))
            self.data_LastPos= self.xyz_thread.read() #get last known value
            self.xyz_thread.clear_state()
            time.sleep(10)
            self.x_pos=self.data_LastPos['XPOS']
            self.y_pos=self.data_LastPos['YPOS']
            self.z_pos=self.data_LastPos['ZPOS']
            self.Set_Actual_Position_Values(self.x_pos,self.y_pos,self.z_pos)
        else:
            log.info("XYZ Robot Not Found for Reset")    

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
        try :
            if self.lineEdit_Feedrate.text() == '':
                self.Feedrate=None
            else:    
                self.Feedrate = int(self.lineEdit_Feedrate.text())
        except:
            self.Feedrate=None
            self.lineEdit_Feedrate.setText('')
            
            

    def PB_Set_Position(self):
        self.Read_Input_xyz()            
        self.Set_Actual_Position_Values(self.X,self.Y,self.Z)        
        self.Get_Actual_Pos()
        if self.XYZRobot_found==1:
            self.xyz_thread.home_offset_xyz(self.x_pos,self.y_pos,self.z_pos)   
            #Show new position         
            self.xyz_thread.status_Report()
            self.xyz_thread.grbl_status()
            self.ST.Signal_Data(self.xyz_update_thread.read())
        else:            
            log.info("XYZ Robot not Connected for setting Position")  

    def PB_Go(self):  
        self.Show_inbutton_pause()
        self.Read_Input_xyz()   
        self.end_pos=[self.X,self.Y,self.Z]               
        self.ini_pos=[self.x_pos,self.y_pos,self.z_pos]                
        if self.XYZRobot_found==1:
            log.info("Going to: X = " + str(self.X) + ", Y = " + str(self.Y)+", Z = " + str(self.Z))            
            #Set absolute movement            
            self.xyz_thread.send_queue_command('absolutePositioning',{},True)

            if self.Feedrate==None:
                self.xyz_thread.goto_xyz(self.X,self.Y,self.Z)
            else:
                self.xyz_thread.goto_xyzf(self.X,self.Y,self.Z,self.Feedrate)

            
            #usefixedtime=0
            
        else:
            log.info("XYZ Robot Not Found for Going")        
            
            
                


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
    '''    
    def closeEvent(self,event):
        result = QtWidgets.QMessageBox.question(self,
                      "Confirm Exit...",
                      "Are you sure you want to exit ?",
                      QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
        event.ignore()

        if result == QtWidgets.QMessageBox.Yes:            
            self.App_Close_Event() 
            #print('inside def') 
            try:                
                self.LSTDialog.close()                
            except:                
                pass                                                  
            event.accept()
    '''
    def App_Close_Event(self):          
        try:      
            log.info("Close Event Triggered -> stopping threads")
            #self.LH_T.quit()
            self.killer_event.set()
            if self.XYZRobot_found==1:
                self.xyz_update_thread.join()
                self.xyz_thread.join()            
                self.XYZRobot_found=0
            self.xyz_thread=None 
            self.xyz_update_thread=None               
                                    
        except:
            raise
        

        log.info("waiting 1s")        
        time.sleep(1)
        log.info("cleaning kill event")
        self.killer_event.clear()   
        log.info("finished")

        self.XYZRobot_found=0
    
    def Get_Actual_Pos(self):
        try:
            self.x_pos=self.xyz_update_thread.x_pos
            self.y_pos=self.xyz_update_thread.y_pos
            self.z_pos=self.xyz_update_thread.z_pos
            self.state_xyz=self.xyz_update_thread.state_xyz
            self.Status=self.xyz_update_thread.Status
        except:    
            self.x_pos=self.x_pos
            self.y_pos=self.y_pos
            self.z_pos=self.z_pos
            log.warning("Position unknown!")
            self.state_xyz=-11
            pass
        

class ProgressBar_Update(QtCore.QThread):
    tick = QtCore.pyqtSignal(int, name="valchanged") #New style signal

    def __init__(self, parent):
        QtCore.QThread.__init__(self,parent)

    def SetStatus(self,x):
        self.tick.emit(x)                     
        time.sleep(0.1)

    def info(self, message):
        self.logger.info("{}".format(message))

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = MyWindow()#QtWidgets.QMainWindow()
    ui = Ui_MainWindow_V2()
    ui.setupUi(MainWindow)
    ui.setupUi2(MainWindow)    
    
    handler = class_LogHandler.ConsolePanelHandler(ui)          
    formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
    handler.setFormatter(formatter)           
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)    
    #if (log.hasHandlers()):
    #    log.handlers.clear()
    log.addHandler(handler)
    #my_logger = ToFileLogger("Logging debug")
    # add the handler to the root logger
    #logging.getLogger('').addHandler(handler)    
    print('----------------------------------------------Logging info--------------------------------------------')
    print(log.__dict__)
    print('------------------------------------------------------------------------------------------------------')
    
    aDialog=class_File_Dialogs.Dialogs()
    MainWindow.show()
    sys.exit(app.exec_())
