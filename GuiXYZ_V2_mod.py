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

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PIL.ImageQt import ImageQt

#from PyQt5.QtWidgets import QMessageBox,QAction,QLabel
#from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem
#from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
#from PyQt5.QtGui import QIcon
#from PyQt5.QtCore import Qt, QRect, QSize
#from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QTextEdit, QSizePolicy
#from PyQt5.QtGui import QColor, QPainter, QTextFormat

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
from Gimage_V1 import Image_Gcode_Stream 
from Gimage_V1 import GImage 
import GuiXYZ_V1
import GuiXYZ_LSTD
import GuiXYZ_RTD
#import atexit
#import keyboard for keyboard inputs

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
            #print('inside class')             
            try:                
                ui.LSTDialog.quit()                   
            except Exception as e:
                #logging.error(e)     
                pass      
            try:                                
                ui.RTDialog.quit()             
            except Exception as e:
                #logging.error(e)     
                pass      
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
class LayerSelectionToolDialog(QWidget,GuiXYZ_LSTD.Ui_Dialog_LSTD):
    set_clicked= QtCore.pyqtSignal(list)
    #def __init__(self,NumLayers,Selected_Layers,parent=None):    
    #    super().__init__(parent)
    def __init__(self,NumLayers,Selected_Layers, *args, **kwargs):
        super(LayerSelectionToolDialog, self).__init__(*args, **kwargs)    
        self.Number_of_Layers=NumLayers
        if self.Number_of_Layers<1:
            self.Number_of_Layers=1
        self.Selected_Layers=Selected_Layers        
        if self.Selected_Layers is None or len(self.Selected_Layers)<=0:
            self.Selected_Layers=[-1]
        self.Layer_range=[0,0,self.Number_of_Layers]    
        self.openLayerSelectToolDialog()
        self.Set_Checkboxeswith_Selected_Layers(self.Selected_Layers)   
    
    def quit(self):
        self.Dialog_LSTD.close()

    def Assign_Colors_to_Labels(self,Color_Palette):

        for iii in range(self.Number_of_Layers): 
            #CBname="checkBox_LSTD"+'_CB_L'+str(iii)
            Color=(255,255,255)
            Lname="label_LSTD"+'_L_L'+str(iii)                         
            try:
                label = self.Dialog_LSTD.findChild(QtWidgets.QLabel, Lname)                  
                txt="("+str(255)+","+str(255)+","+str(255)+")"    
                label.setText(txt)    
                label.setStyleSheet("background-color:rgb"+txt+"; border: 1px solid black;")
                label.adjustSize()
                if Color_Palette is not None:
                    for ttt in Color_Palette:# (p,c,r,g,b)) palette,count,rgb tuple
                        (p,c,r,g,b)=ttt
                        if p==iii:
                            Color=(r,g,b)
                            txt="("+str(r)+","+str(g)+","+str(b)+")"    
                            label.setText(txt)    
                            label.setStyleSheet("background-color:rgb"+txt+"; border: 1px solid black;")                        
                            break
               

            except Exception as e:
                logging.error(e)
                logging.info("Label Error!"+Lname)
                pass    


    def Clear_allcheckbox(self,val=False):
        for iii in range(self.Number_of_Layers): 
            CBname="checkBox_LSTD"+'_CB_L'+str(iii)
            #Lname="label_LSTD"+'_L_L'+str(iii)                         
            try:
                checkbox = self.Dialog_LSTD.findChild(QtWidgets.QCheckBox, CBname)                  
                checkbox.setChecked(val)
            except Exception as e:
                logging.error(e)
                logging.info("Check Box Error!"+CBname)
                pass    
    
    def Get_Selected_Layers_From_checkbox(self):
        S_L=[]
        sss=0
        for iii in range(self.Number_of_Layers): 
            CBname="checkBox_LSTD"+'_CB_L'+str(iii)
            #Lname="label_LSTD"+'_L_L'+str(iii)                         
            try:
                checkbox = self.Dialog_LSTD.findChild(QtWidgets.QCheckBox, CBname)                  
                if checkbox.isChecked()==True:
                    S_L.append(iii)
                    sss=sss+1
            except Exception as e:
                logging.error(e)
                logging.info("Check Box Error!"+CBname)
                pass    
        if sss==self.Number_of_Layers:
            S_L=[-1]    
        self.Selected_Layers = S_L    

    def Set_Checkboxeswith_Selected_Layers(self,S_L):
        Isall=False
        self.Clear_allcheckbox()
        for iii in S_L:
            CBname="checkBox_LSTD"+'_CB_L'+str(iii)
            #Lname="label_LSTD"+'_L_L'+str(iii)
            if iii==-1:
                Isall=True
                break                       
            checkbox = self.Dialog_LSTD.findChild(QtWidgets.QCheckBox, CBname)
            checkbox.setChecked(True)
        if Isall==True:
            self.Clear_allcheckbox(True)


    def set_objects_fromNum_layers(self,Num_Layers):
        
        Obj_Names=[]
        for iii in range(Num_Layers):
            Obj_Names.append('_CB_L'+str(iii))
            Obj_Names.append('_L_L'+str(iii))
        Obj_Text=[]
        for iii in range(Num_Layers):
            Obj_Text.append('Layer'+str(iii))
            Obj_Text.append(str(iii))
        
        obj_positions = [(iii, jjj) for iii in range(Num_Layers) for jjj in range(2)]

        L_N=0
        for position, name, txt in zip(obj_positions, Obj_Names, Obj_Text):
            if name == '':
                continue
            if '_CB_L' in name:                
                checkbox=QtWidgets.QCheckBox(self.DSLui.frame)
                checkbox.setObjectName("checkBox_LSTD"+name)  
                checkbox.setText(txt)                
                checkbox.clicked.connect(self.Get_Selected_Layers_From_checkbox)
                self.DSLui.gridLayout.addWidget(checkbox, *position)              


            else:
                label=QtWidgets.QLabel(self.DSLui.frame)
                label.setObjectName("label_LSTD"+name)
                label.setText(txt)
                self.DSLui.gridLayout.addWidget(label, *position)
                L_N=L_N+1    
           
    def openLayerSelectToolDialog(self):
        self.Dialog_LSTD = QtWidgets.QDialog()
        self.DSLui = GuiXYZ_LSTD.Ui_Dialog_LSTD()
        self.DSLui.setupUi(self.Dialog_LSTD)
        self.set_objects_fromNum_layers(self.Number_of_Layers)        
        self.Dialog_LSTD.show()             
        self.DSLui.pushButton_LSTD_Set_Preview.clicked.connect(self.PB_LSTD_Set_Preview)
            
    def PB_LSTD_Set_Preview(self):            
        #print('clicked')
        self.set_clicked.emit(self.Selected_Layers)

    def accept(self):
        #print('accepted')
        self.Get_Selected_Layers_From_checkbox()
        return self.Selected_Layers   

    def Get_list_of_Selected_Layers(self,Selected_Layers,pimg_val_range):
        listofSellay=[]
        for sss in Selected_Layers:
            if sss==-1:
                listofSellay=[]
                for iii in range(pimg_val_range[1],pimg_val_range[2]+1):
                    listofSellay.append(iii)
                break
            if sss<=pimg_val_range[2] and sss>=pimg_val_range[1]:
                listofSellay.append(sss)
        if len(Selected_Layers)==0:    
            listofSellay=[]
            for iii in range(pimg_val_range[1],pimg_val_range[2]+1):
                listofSellay.append(iii)
        return listofSellay

class ResizeToolDialog(QWidget,GuiXYZ_RTD.Ui_Dialog_RTD):
    set_clicked= QtCore.pyqtSignal(list)
    #def __init__(self,NumLayers,Selected_Layers,parent=None):    
    #    super().__init__(parent)
    def __init__(self,Resize_Data_List, *args, **kwargs):
        super(ResizeToolDialog, self).__init__(*args, **kwargs)    
        self.IsRTDim=False
        self.Scale=1
        self.Resize_Data_List=Resize_Data_List    
        self.openResizeToolDialog()
        [self.Machine_Size,self.Machine_pos,self.Canvas_pos,self.Canvas_Size,self.Image_pos,self.Image_Size,self.Frame]=self.Resize_Data_List
        self.Set_Data_List(self.Resize_Data_List)
        self.Actualize_labels_positions()
        self.RTD_Connect_Actions()
    
    def quit(self):
        self.Dialog_RTD.close()
           
    def openResizeToolDialog(self):
        self.Dialog_RTD = QtWidgets.QDialog()
        self.DRui = GuiXYZ_RTD.Ui_Dialog_RTD()
        self.DRui.setupUi(self.Dialog_RTD)
        #self.set_objects_fromNum_layers(self.Number_of_Layers)        
        self.Dialog_RTD.show()             
        self.DRui.pushButton_RTD_Set_Resized.clicked.connect(self.PB_RTD_Set_Preview)
            
    def PB_RTD_Set_Preview(self):            
        #print('clicked')
        self.Update_Resize_Data_List()
        self.set_clicked.emit(self.Resize_Data_List)

    def Update_Resize_Data_List(self):
        self.Resize_Data_List=[self.Machine_Size,self.Machine_pos,self.Canvas_pos,self.Canvas_Size,self.Image_pos,self.Image_Size,self.Frame]
    
    def accept(self):
        #print('accepted')
        #self.Get_Selected_Layers_From_checkbox()
        self.Update_Resize_Data_List()
        return self.Resize_Data_List  
    
    def Set_Data_List(self,Data_List):
        #print(Data_List)
        [Machine_Size,Machine_pos,Canvas_pos,Canvas_Size,Image_pos,Image_Size,Frame]=Data_List
        self.Set_Machine_Size(Machine_Size)
        self.Set_Machine_pos(Machine_pos)
        self.Set_Canvas_pos(Canvas_pos)    
        self.Set_Canvas_Size(Canvas_Size)   
        self.Set_Image_pos(Image_pos)   
        self.Set_Image_Size(Image_Size)     
        self.Set_Frame(Frame)                 

    def RTD_Connect_Actions(self):
        #self.DRui.groupBox_RTD_Resize.

        self.DRui.lineEdit_RTD_Machine_Size_x.editingFinished.connect(self.Put_Machine_Size)
        self.DRui.lineEdit_RTD_Machine_Size_y.editingFinished.connect(self.Put_Machine_Size)
        self.DRui.lineEdit_RTD_Machine_Size_z.editingFinished.connect(self.Put_Machine_Size)
        
        self.DRui.lineEdit_RTD_Machine_pos_x.editingFinished.connect(self.Put_Machine_pos)
        self.DRui.lineEdit_RTD_Machine_pos_y.editingFinished.connect(self.Put_Machine_pos)
        self.DRui.lineEdit_RTD_Machine_pos_z.editingFinished.connect(self.Put_Machine_pos) 

        self.DRui.lineEdit_RTD_Canvas_pos_x.editingFinished.connect(self.Put_Canvas_pos)
        self.DRui.lineEdit_RTD_Canvas_pos_y.editingFinished.connect(self.Put_Canvas_pos)

        self.DRui.lineEdit_RTD_Canvas_Size_W.editingFinished.connect(self.Put_Canvas_Size)
        self.DRui.lineEdit_RTD_Canvas_Size_H.editingFinished.connect(self.Put_Canvas_Size)  

        self.DRui.lineEdit_RTD_Image_pos_x.editingFinished.connect(self.Put_Image_pos)
        self.DRui.lineEdit_RTD_Image_pos_y.editingFinished.connect(self.Put_Image_pos)

        self.DRui.lineEdit_RTD_Image_Size_W.editingFinished.connect(self.Put_Image_Size)
        self.DRui.lineEdit_RTD_Image_Size_H.editingFinished.connect(self.Put_Image_Size)

        self.DRui.spinBox_RTD_Frame.valueChanged.connect(self.Put_Frame)
    
    def Put_All(self):
        self.Put_Machine_Size()
        self.Put_Machine_pos()
        self.Put_Canvas_pos()
        self.Put_Canvas_Size()
        self.Put_Image_pos()
        self.Put_Image_Size()
        self.Put_Frame()

    def Put_Machine_Size(self):
        Machine_Size=self.Get_Machine_Size()
        #print('Got '+str(Machine_Size)+' had '+str(self.Machine_Size))
        self.Set_Machine_Size(Machine_Size) #if accepted
        self.Machine_Size=self.Get_Machine_Size()        
        self.Actualize_labels_positions()

    def Put_Machine_pos(self):
        Machine_pos=self.Get_Machine_pos()        
        #print('Got '+str(Machine_pos)+' had '+str(self.Machine_pos))
        self.Set_Machine_pos(Machine_pos) #if accepted
        self.Machine_pos=self.Get_Machine_pos()        
        #print('Got after '+str(Machine_pos)+' had '+str(self.Machine_pos))
        self.Actualize_labels_positions() 

    def Put_Canvas_pos(self):
        Canvas_pos=self.Get_Canvas_pos()        
        self.Set_Canvas_pos(Canvas_pos) #if accepted
        self.Canvas_pos=self.Get_Canvas_pos()        
        self.Actualize_labels_positions() 

    def Put_Canvas_Size(self):
        Canvas_Size=self.Get_Canvas_Size()        
        self.Set_Canvas_Size(Canvas_Size) #if accepted
        self.Canvas_Size=self.Get_Canvas_Size()        
        self.Actualize_labels_positions()     

    def Put_Image_Size(self):
        Image_Size=self.Get_Image_Size()        
        self.Set_Image_Size(Image_Size) #if accepted
        self.Image_Size=self.Get_Image_Size()        
        self.Actualize_labels_positions() 

    def Put_Image_pos(self):
        Image_pos=self.Get_Image_pos()        
        self.Set_Image_pos(Image_pos) #if accepted
        self.Image_pos=self.Get_Image_pos()        
        self.Actualize_labels_positions()     

    def Put_Frame(self):
        self.Frame=self.Get_Frame()
        if self.Frame==0:
           self.DRui.label_RTD_Image.setStyleSheet("border: No border;") 
        else:
           self.DRui.label_RTD_Image.setStyleSheet("border: 2px solid black;")  
           #self.DRui.label_RTD_Image.setStyleSheet("border: 2px solid blue;") 
    
    def Get_Machine_Size(self):
        Data=self.Machine_Size
        try:
            Data[0]=float(self.DRui.lineEdit_RTD_Machine_Size_x.text())
            Data[1]=float(self.DRui.lineEdit_RTD_Machine_Size_y.text())
            Data[2]=float(self.DRui.lineEdit_RTD_Machine_Size_z.text())
        except Exception as e:
            logging.error(e)
            self.Set_Machine_Size(self.Machine_Size)
            Data=self.Machine_Size
        return Data    

    def Set_Machine_Size(self,Machine_Size):
        if Machine_Size is not None:
            
            self.DRui.lineEdit_RTD_Machine_Size_x.setText(str("{0:.2f}".format(Machine_Size[0])))
            self.DRui.lineEdit_RTD_Machine_Size_y.setText(str("{0:.2f}".format(Machine_Size[1])))
            self.DRui.lineEdit_RTD_Machine_Size_z.setText(str("{0:.2f}".format(Machine_Size[2])))        

    def Get_Machine_pos(self):
        Data=self.Machine_pos
        try:
            Data[0]=float(self.DRui.lineEdit_RTD_Machine_pos_x.text())
            Data[1]=float(self.DRui.lineEdit_RTD_Machine_pos_y.text())
            Data[2]=float(self.DRui.lineEdit_RTD_Machine_pos_z.text())
        except Exception as e:
            logging.error(e)
            self.Set_Machine_pos(self.Machine_pos)
            Data=self.Machine_pos
        return Data   
        

    def Set_Machine_pos(self,Machine_pos):
        if Machine_pos is not None:
            self.DRui.lineEdit_RTD_Machine_pos_x.setText(str("{0:.2f}".format(Machine_pos[0])))
            self.DRui.lineEdit_RTD_Machine_pos_y.setText(str("{0:.2f}".format(Machine_pos[1])))
            self.DRui.lineEdit_RTD_Machine_pos_z.setText(str("{0:.2f}".format(Machine_pos[2])))

    def Get_Canvas_pos(self):
        Data=self.Canvas_pos
        try:
            Data[0]=float(self.DRui.lineEdit_RTD_Canvas_pos_x.text())
            Data[1]=float(self.DRui.lineEdit_RTD_Canvas_pos_y.text())            
        except:
            self.Set_Canvas_pos(self.Canvas_pos)
            Data=self.Canvas_pos
        return Data           

    def Set_Canvas_pos(self,Canvas_pos):
        if Canvas_pos is not None:
            self.DRui.lineEdit_RTD_Canvas_pos_x.setText(str("{0:.2f}".format(Canvas_pos[0])))
            self.DRui.lineEdit_RTD_Canvas_pos_y.setText(str("{0:.2f}".format(Canvas_pos[1])))

    def Get_Canvas_Size(self):
        Data=self.Canvas_Size
        try:
            Data[0]=float(self.DRui.lineEdit_RTD_Canvas_Size_W.text())
            Data[1]=float(self.DRui.lineEdit_RTD_Canvas_Size_H.text())            
        except:
            self.Set_Canvas_Size(self.Canvas_Size)
            Data=self.Canvas_Size
        return Data  
        
    def Set_Canvas_Size(self,Canvas_Size):
        if Canvas_Size is not None:
            self.DRui.lineEdit_RTD_Canvas_Size_W.setText(str("{0:.2f}".format(Canvas_Size[0])))
            self.DRui.lineEdit_RTD_Canvas_Size_H.setText(str("{0:.2f}".format(Canvas_Size[1])))    

    def Get_Image_pos(self):
        Data=self.Image_pos
        try:
            Data[0]=float(self.DRui.lineEdit_RTD_Image_pos_x.text())
            Data[1]=float(self.DRui.lineEdit_RTD_Image_pos_y.text())            
        except:
            self.Set_Image_pos(self.Image_pos)
            Data=self.Image_pos
        return Data          

    def Set_Image_pos(self,Image_pos):
        if Image_pos is not None:
            self.DRui.lineEdit_RTD_Image_pos_x.setText(str("{0:.2f}".format(Image_pos[0])))
            self.DRui.lineEdit_RTD_Image_pos_y.setText(str("{0:.2f}".format(Image_pos[1])))

    def Get_Image_Size(self):
        Data=self.Image_Size
        try:
            Data[0]=float(self.DRui.lineEdit_RTD_Image_Size_W.text())
            Data[1]=float(self.DRui.lineEdit_RTD_Image_Size_H.text())            
        except:
            self.Set_Image_Size(self.Image_Size)
            Data=self.Image_Size
        return Data             

    def Set_Image_Size(self,Image_Size):
        if Image_Size is not None:
            self.DRui.lineEdit_RTD_Image_Size_W.setText(str("{0:.2f}".format(Image_Size[0])))
            self.DRui.lineEdit_RTD_Image_Size_H.setText(str("{0:.2f}".format(Image_Size[1])))

    def Get_Frame(self):
        Data=self.Frame
        try:
            Data=int(self.DRui.spinBox_RTD_Frame.value())            
        except:
            self.Set_Frame(self.Frame)
        return Data             
                
    def Set_Frame(self,Frame):
        if Frame >= 0:
            self.DRui.spinBox_RTD_Frame.setValue(int(Frame))

    def Get_Data_List(self):        
        Machine_Size=self.Get_Machine_Size()
        Machine_pos=self.Get_Machine_pos()
        Canvas_pos=self.Get_Canvas_pos()    
        Canvas_Size=self.Get_Canvas_Size()   
        Image_pos=self.Get_Image_pos()   
        Image_Size=self.Get_Image_Size()     
        Frame=self.Get_Frame()    
        Data_List=[Machine_Size,Machine_pos,Canvas_pos,Canvas_Size,Image_pos,Image_Size,Frame]
        
    def Set_Unit_tooltip_info(self,RTD_dict):
        self.DRui.label_RTD_Machine_Size_unit.setText(RTD_dict['RSize'+'_Unit'])
        self.DRui.label_RTD_Machine_pos_unit.setText(RTD_dict['Rpos'+'_Unit'])
        self.DRui.label_RTD_Canvas_pos_unit.setText(RTD_dict['Cpos'+'_Unit'])
        self.DRui.label_RTD_Canvas_Size_unit.setText(RTD_dict['CSize'+'_Unit'])
        self.DRui.label_RTD_Image_pos_unit.setText(RTD_dict['Ipos'+'_Unit'])
        self.DRui.label_RTD_Image_Size_unit.setText(RTD_dict['ISize'+'_Unit'])
        #RTD_dict['Frame'+'_Unit'])

        self.DRui.label_RTD_Machine_Size_unit.setToolTip(RTD_dict['RSize'+'_Info'])
        self.DRui.label_RTD_Machine_pos_unit.setToolTip(RTD_dict['Rpos'+'_Info'])
        self.DRui.label_RTD_Canvas_pos_unit.setToolTip(RTD_dict['Cpos'+'_Info'])
        self.DRui.label_RTD_Canvas_Size_unit.setToolTip(RTD_dict['CSize'+'_Info'])
        self.DRui.label_RTD_Image_pos_unit.setToolTip(RTD_dict['Ipos'+'_Info'])
        self.DRui.label_RTD_Image_Size_unit.setToolTip(RTD_dict['ISize'+'_Info'])
        self.DRui.spinBox_RTD_Frame.setToolTip(RTD_dict['Frame'+'_Info'])

    def Actualize_labels_positions(self):        
        self.Set_Scale()
        self.Set_Machine_label()
        self.Set_Canvas_label()    
        self.Set_Image_label()  
        self.Set_Machine_Point_label()  

    def Set_Scale(self):
        self.Scale=1
        if self.Machine_Size[0]>0 and self.Machine_Size[1]>0:
            FRect=self.DRui.frame_RTD_Images.frameRect()
            FH=FRect.height()
            FW=FRect.width()
            S1=(FW/self.Machine_Size[0])
            S2=(FH/self.Machine_Size[1])
            self.Scale=min(S1,S2)
            #print('Scale->'+str(self.Scale))

    def Set_Machine_label(self):
        try:
            Geo=self.DRui.frame_RTD_Images.geometry()
            MGeo=self.DRui.label_RTD_Machine.geometry()
            x_F,y_F,W_F,H_F=Geo.getRect()            
            MGeo.setRect(0, 0, int(self.Machine_Size[0]*self.Scale), int(self.Machine_Size[1]*self.Scale))
            self.DRui.label_RTD_Machine.setGeometry(MGeo)
        except:
            pass
    
    def TL_to_BL(self,xtl,ytl,W,H,Htlbl):
        return xtl,Htlbl-ytl,W,H

    def BL_to_TL(self,xbl,ybl,W,H,Htlbl):
        return xbl,Htlbl+ybl,W,H    

    def Set_Canvas_label(self):        
        try:
            MGeo=self.DRui.label_RTD_Machine.geometry()
            CGeo=self.DRui.label_RTD_Canvas.geometry()
            x_M,y_M,W_M,H_M=MGeo.getRect() # top, left
            x_MO=int(self.Canvas_pos[0]*self.Scale)
            y_MO=int(self.Canvas_pos[1]*self.Scale)
            W_C=int(self.Canvas_Size[0]*self.Scale)
            H_C=int(self.Canvas_Size[1]*self.Scale)                
            pos=[x_M+x_MO,y_M+(H_M-(y_MO+H_C)),W_C,H_C]        
            CGeo.setRect(pos[0],pos[1],pos[2],pos[3])        
            self.DRui.label_RTD_Canvas.setGeometry(CGeo)    
        except:
            pass    

    def Set_Image_label(self):        
        try:
            #MGeo=self.DRui.label_RTD_Machine.geometry()
            CGeo=self.DRui.label_RTD_Canvas.geometry()
            IGeo=self.DRui.label_RTD_Image.geometry()
            x_C,y_C,W_C,H_C=CGeo.getRect() # top, left
            x_IO=int(self.Image_pos[0]*self.Scale)
            y_IO=int(self.Image_pos[1]*self.Scale)
            W_I=int(self.Image_Size[0]*self.Scale)
            H_I=int(self.Image_Size[1]*self.Scale)         
            pos=[x_C+x_IO,y_C+(H_C-(y_IO+H_I)),W_I,H_I]        
            IGeo.setRect(pos[0],pos[1],pos[2],pos[3])        
            self.DRui.label_RTD_Image.setGeometry(IGeo) 
        except:
            pass     

    def Set_Image_to_Image_label(self,im):
        self.im=im
        qim = ImageQt(im)
        self.the_pixmap=QtGui.QPixmap.fromImage(qim)        
        self.DRui.label_RTD_Image.setPixmap(self.the_pixmap.scaled(
                    self.DRui.label_RTD_Image.size(), QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation))       
        self.IsRTDim=True      
        self.Put_Frame()
    def Set_Machine_Point_label(self):         
        try:
            MGeo=self.DRui.label_RTD_Machine.geometry()
            MPGeo=self.DRui.label_RTD_Machine_Point.geometry()
            x_,y_,W_MP,H_MP=MPGeo.getRect() # top, left
            x_M,y_M,W_M,H_M=MGeo.getRect() # top, left
            x_MPO=int(self.Machine_pos[0]*self.Scale)
            y_MPO=int(self.Machine_pos[1]*self.Scale)            
            W_M=int(self.Machine_Size[0]*self.Scale)
            H_M=int(self.Machine_Size[1]*self.Scale)         
            pos=[x_M+x_MPO-int(W_MP/2),y_M+(H_M-(y_MPO+H_MP-int(H_MP/2))),W_MP,H_MP]        
            MPGeo.setRect(pos[0],pos[1],pos[2],pos[3])        
            self.DRui.label_RTD_Machine_Point.setGeometry(MPGeo) 
        except:
            pass  


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
        #self.plaintextEdit_GcodeScript.setGeometry(QtCore.QRect(10, 20, 431, 351))
        self.plaintextEdit_GcodeScript.setObjectName("plaintextEdit_GcodeScript")
        self.gridLayout_7.addWidget(self.plaintextEdit_GcodeScript, 0, 0, 1, 1)

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
        # ---------GImage Init
        self.Fill_Image_Config_Table()

        self.P_Bar_Update_Gcode=ProgressBar_Update(MainWindow)        
        self.P_Bar_Update_Gcode.tick.connect(self.progressBar_Gcode.setValue)
        self.P_Bar_Update_Gimage=ProgressBar_Update(MainWindow)        
        self.P_Bar_Update_Gimage.tick.connect(self.progressBar_Gimage.setValue)
        
    
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
        self.actionLayer_Selection.triggered.connect(self.Open_LayerSelectionToolDialog)
        self.actionResize.triggered.connect(self.Open_ResizeToolDialog)
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

        self.pushButton_Open_Image.clicked.connect(self.PB_Open_Image)
        self.pushButton_Load_Image_Config.clicked.connect(self.PB_Open_Image_Config)
        self.pushButton_Save_Image_Config.clicked.connect(self.PB_Save_Image_Config)
        self.pushButton_Set_Changes_Image_Config.clicked.connect(self.PB_Set_Changes_Image_Config)

        self.comboBox_Image_Process.currentIndexChanged.connect(self.Combo_Image_Process_Select)
        self.comboBox_Tool_Select.currentIndexChanged.connect(self.Combo_Tool_Select)
        self.comboBox_Technique.currentIndexChanged.connect(self.Combo_Technique_Select)
        self.pushButton_Process_Image.clicked.connect(self.PB_Process_Image)

        self.pushButton_Generate_Gimage_Code.clicked.connect(self.PB_Generate_Gimage_Code)

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
        self.IsImageThread=False
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

    def connect_label_actions(self):    
        #self.label_Image_Preview.clicked.connect(self.Image_Preview_Clicked) 
        self.label_Image_Preview.resize.connect(self.Image_Preview_Resized) 
        #self.label_Image_Preview_Processed.clicked.connect(self.Image_Preview_Clicked) 
        self.label_Image_Preview_Processed.resize.connect(self.Processed_Image_Preview_Resized)        
        self.label_Image_Preview.left_clicked[int].connect(self.left_click)
        self.label_Image_Preview.right_clicked[int].connect(self.right_click)
        self.label_Image_Preview_Processed.left_clicked[int].connect(self.left_click_P)
        self.label_Image_Preview_Processed.right_clicked[int].connect(self.right_click_P)

    def Open_ResizeToolDialog(self):
        RTD_List=self.G_Image.RTD_Get_Data_List()
        self.RTDialog=ResizeToolDialog(RTD_List)
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
        print(R_D_List)
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
        self.LSTDialog=LayerSelectionToolDialog(N_L,S_L)   
        self.LSTDialog.DSLui.buttonBox_LSTD.accepted.connect(lambda: self.LSTD_buttonClicked(self.LSTDialog.Selected_Layers))             
        self.LSTDialog.DSLui.pushButton_LSTD_Set_Preview.clicked.connect(lambda: self.LSTD_Set_buttonClicked(self.LSTDialog.Selected_Layers))
        self.Fill_comboBox_LSTD_Image_Process() 
        Color_Palette=self.G_Image.Get_Color_Palette()
        self.LSTDialog.Assign_Colors_to_Labels(Color_Palette)
   

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
            #logging.error(e)
            pass
        

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
        self.P_Bar_Update_Gcode.SetStatus(0)
        self.xyz_gcodestream_thread.Stream(text2stream,self.P_Bar_Update_Gcode)


        if self.isoncheckedstate_checkbox==True:
            self.xyz_thread.grbl_gcode_cmd('$C')
            logging.info("Checkmode Disabled and Grbl reset") 
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
        #logging.info('Image Process preview entered')
        if self.G_Image.IsProcessedimagetoprint==True:
            qimp = ImageQt(self.G_Image.imp)
            self.the_pixmap_p=QtGui.QPixmap.fromImage(qimp)            
            #logging.info('Image Process preview showing')
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
                logging.info('GImage Gcode Ready!')
            else:    
                logging.info('No processed image available!')
        
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
                logging.error(e)
                logging.error('Some items could not be read! ' +ccc )
                pass   
        #print('Read from file:'+self.G_Image.Image_Config_Data['Robot_XYZ']+' '+data['Robot_XYZ'])     
        self.G_Image.Check_Image_Config_Data()
        self.Fill_Image_Config_Table()    

    def PB_Open_Image(self):
        filename=aDialog.openFileNameDialog(1) #1 Images
        
        if filename is not None:
            logging.info('Opening:'+filename)
            try:    
                            
                self.G_Image.open_image(filename)                                
                self.Show_Image_Preview()
                self.PB_Set_Changes_Image_Config()
                self.Show_Processed_Image_Preview()
            except Exception as e:
                logging.error(e)
                logging.info("Could not open Image!")
    

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

    def Start_Image_Thread(self):
        try:            
            #self.xyz_gimagestream_thread=Image_Gcode_Stream(self.xyz_thread,self.killer_event,self.xyz_thread.grbl_event_hold,self.stream_event_stop)
            self.xyz_gimagestream_thread=Image_Gcode_Stream(self.killer_event,self.plaintextEdit_GcodeScript) 
            self.xyz_gimagestream_thread.setName("Gimage Stream") 
            self.xyz_gimagestream_thread.start()
            logging.info("SUCCESS: Image to Gcode thread Initialized :)")  
            self.IsImageThread=True 
            
        except Exception as e:               
            #logging.error("failed to initialise xyz_thread: ", sys.exc_info()[0])
            logging.error(e)
            logging.error("Failed to initialise Image thread :( -> No Image to Gcode")
            self.IsImageThread=False
            
    def Start_XYZ_Thread(self):            
        try:
            XYZRobot_port=self.COMPort            
            #Baudrate=self.COMBaudRate.encode('utf-8')
            Baudrate=int(self.COMBaudRate)
            self.xyz_thread = XYZGrbl(XYZRobot_port, Baudrate, self.killer_event,self.IsRunning_event)
            self.xyz_thread.start()
            self.xyz_update_thread=XYZ_Update(self.xyz_thread,self.killer_event,self.label_XactPos,self.label_YactPos,self.label_ZactPos,self.pushButton_Pause_Resume,self.frame_GcodePauseStop)
            self.xyz_update_thread.setName("XYZ Update") 
            self.xyz_update_thread.start()
            self.stream_event_stop= threading.Event()
            self.stream_event_stop.clear()
            self.xyz_gcodestream_thread=XYZ_Gcode_Stream(self.xyz_thread,self.killer_event,self.xyz_thread.grbl_event_hold,self.stream_event_stop,self.IsRunning_event)
            self.xyz_gcodestream_thread.setName("XYZ Gcode Stream") 
            self.xyz_gcodestream_thread.start()
            if self.IsImageThread==False:
                self.Start_Image_Thread()
            if self.IsImageThread==True:                    
                self.xyz_gimagestream_thread.Set_xyz_thread(self.xyz_thread,self.stream_event_stop)

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
    
    def Fill_Image_Config_Table(self):  
        #logging.info("Filling Gimage Configuration!")
        self.tableWidget_Image_Config.clear()  
        config=self.G_Image.Get_Image_Config_Data()
        Num_Items=0
        for ccc in config:
            if not '_Info' in ccc and not '_Type' in ccc and not '_Unit' in ccc:                                
                Num_Items=Num_Items+1
        #logging.info("Filling Gimage Configuration! Items found "+ str(Num_Items))        
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
        #logging.info('Numrows->'+str(self.Config_Table_NumRows))
        if self.Image_Config_Table_NumRows==0:
            return True
        else:
            return False          

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
    
    def Load_Image_config_from_file(self):
        filename=aDialog.openFileNameDialog(2) #0 gcode, 1 Images 2 txt else all 
        data={}
        if filename is not None:
            
            logging.info('Opening:'+filename)
            try:
                self.plaintextEdit_GcodeScript.clear()
                with open(filename, 'r') as yourFile:
                    #self.plaintextEdit_GcodeScript.setText(yourFile.read())        #textedit
                    linelist=yourFile.readlines() #makes list of lines  
                data=self.Get_Config_Data_From_List(linelist)                                                
                yourFile.close()                
            except Exception as e:
                logging.error(e)
                logging.info("File was not read!")
        return data        

    
    def Get_Config_Data_From_List(self,linelist):
        data={}
        for line in linelist:
            #logging.info(line)
            try:                           
                #mf = re.search('<(.*)>_<([+-]?\d*[\.,]?\d*?)>_<(.*)>_<(.*)>_<(.*)>',line)                               
                mf = re.search('<(.*)>_<(.*)>_<(.*)>_<(.*)>_<(.*)>',line)                               
            except:
                mf = None
            try:
                if mf is not None: #any type
                    #logging.info('storing float')
                    #logging.info('mf ->'+str(mf.groups()))
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
                logging.error('Bad format for Image Config Read!')
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
                    logging.info('Saving:'+fileName)      
                    Tabledata=[]            
                    for row in range(self.Image_Config_Table_NumRows):  
                        Tabledata.append('<')                                                  
                        for col in range(self.Image_Config_Table_NumCols):
                            Tabledata.append(self.tableWidget_Image_Config.item(row, col).text())
                            if col<self.Image_Config_Table_NumCols-1:
                                Tabledata.append('>_<')                                        
                        Tabledata.append('>\n')                
                    file.writelines(Tabledata)    
                    logging.info("File Saved as:" + fileName)
                    file.close()
                except Exception as e:
                    logging.error(e)
                    logging.info("File was not Written!")        

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
            #print('inside def') 
            try:                
                self.LSTDialog.close()                
            except:                
                pass  
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

class Running_Event_Count_Update(object):
    def __init__(self,IsRunning_event):
        self._observers = []
        self._IsRunning_event=IsRunning_event
        self._lastRunningstate=self._IsRunning_event.is_set()
        self._linesfinalized_count=0         

    @property
    def Count_events(self):
        return self._linesfinalized_count

    @Count_events.setter
    def Count_events(self):
        self.Count_Running_Events()   
        for callback in self._observers:
            print('announcing change')
            callback(self._linesfinalized_count)             
            
    def Count_Reset(self):
        self._linesfinalized_count=0         

    def Count_Running_Events(self):
        logging.info('Running Event has been triggered')
        if not self._IsRunning_event.is_set() and self._lastRunningstate==True:  
            logging.info('Running Event has Changed')       
            self._linesfinalized_count=self._linesfinalized_count+1
        #self._linesfinalized_count=self._linesfinalized_count+1    
        self._lastRunningstate=self._IsRunning_event.is_set()        

    def bind_to(self, callback):
        logging.info('Running Event has been bound')
        self._observers.append(callback)

class XYZ_Gcode_Stream(threading.Thread):
    def __init__(self,xyz_thread,killer_event,holding_event,stoping_event,IsRunning_event):
        threading.Thread.__init__(self, name="XYZ Gcode Stream")
        logging.info("XYZ Gcode Stream Started")        
        self.IsRunning_event=IsRunning_event 
        self.xyz_thread=xyz_thread
        self.killer_event=killer_event
        self.holding_event=holding_event
        self.stoping_event=stoping_event        
        self.cycle_time=0.1                       
        # typeofstream=0 Wait until each Command returns finish signal to send next one.(Slow) Works:Marlin
        # typeofstream=1 Send all to machine and dont wait for response. Works:Marlin
        # typeofstream=2 Send a number of lines and count the returns.
        self.type_of_stream=0 
        self.state_xyz=0
        self.oldstate_xyz=0
        self.istext2stream=False
        self.text_queue = queue.Queue()
        self.streamsize=0
        self.line_count=0
        self.bufflines=0
        self.bufflinesize=5   
        self.linesfinalized_count=0
        self.lastlinesfinalized_count=0
        self.lastRunningstate=self.IsRunning_event.is_set()

        
    '''    
        #self.linesfin_count=Running_Event_Count_Update(self.IsRunning_event) 
        #self.linesfin_count.bind_to(self.Update_RunningCount)   
             
                
    #def Update_RunningCount(self):
    #    self.linesfinalized_count=self.linesfin_count.Count_events()

    def Count_Running_Events(self):
        if not self.IsRunning_event.is_set() and self.lastRunningstate==True:        
            self.linesfinalized_count=self.linesfinalized_count+1  
        self.lastRunningstate=self.IsRunning_event.is_set() 
    '''
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
                    self.Do_the_streaming(self.type_of_stream)            
            except Exception as e:
                if count==0:
                    logging.error(e)
                    logging.info("XYZ Gcode Stream can't get data to update")                         
                else:
                   count=count+1
                if count>=2000:
                    count=0        
        logging.info("XYZ Gcode Stream killed")         

    def Do_the_streaming(self,typeofstream=0):
        # typeofstream=0 Wait until each Command returns finish singl to send next one.(Slow)
        # typeofstream=1 Send all to machine and dont wait for response. 
        # typeofstream=2 Send a number of lines and count the returns.
        if typeofstream==0:
            try:                                        
                if not self.IsRunning_event.is_set():      
                    if self.text_queue.qsize()>0:
                        self.Do_line_count()
                        self.istext2stream=True
                    line2stream= self.text_queue.get_nowait()                            
                    logging.info("Sending command->("+str(self.line_count)+") "+line2stream)
                    self.stream_one_line(line2stream)                                      
                    self.data = self.xyz_thread.read()                
                    self.get_state()
                    if self.state_xyz==11: # error
                        logging.info("Error in Gcode detected! (" + str(line2stream)+') ' )
                        self.Stop_Clear()                                
                    self.wait_until_finished(typeofstream)    #Clears Running_event
            except queue.Empty:                    
                pass   
        elif typeofstream==1:
            try:                      
                if not self.IsRunning_event.is_set() or self.text_queue.qsize()>0:      
                    #logging.info(' type 1 stream Is running event->'+str(self.IsRunning_event.is_set()))                                  
                    if self.text_queue.qsize()>0:
                        self.Do_line_count()
                        self.istext2stream=True
                    line2stream= self.text_queue.get_nowait()                            
                    logging.info("Sending command->("+str(self.line_count)+") "+line2stream)
                    self.stream_one_line(line2stream)                                      
                    self.data = self.xyz_thread.read()                
                    self.get_state()
                    if self.state_xyz==11: # error
                        logging.info("Error in Gcode detected! (" + str(line2stream)+') ' )
                        self.Stop_Clear()   
                    #self.IsRunning_event.clear()                                 
            except queue.Empty:                    
                pass    
        elif typeofstream==2:
            try:                        
                
                if self.bufflines<self.bufflinesize:                        
                    if self.text_queue.qsize()>0:                        
                        self.Do_buffline_count()
                        self.Do_line_count()
                        self.istext2stream=True                    
                    line2stream= self.text_queue.get_nowait()                            
                    logging.info("Sending command->("+str(self.line_count)+") "+line2stream)
                    #logging.info("Buffline->"+str(self.bufflines))
                    self.stream_one_line(line2stream)                                      
                    self.data = self.xyz_thread.read()                
                    self.get_state()
                    if self.state_xyz==11: # error
                        logging.info("Error in Gcode detected! (" + str(line2stream)+') ' )
                        self.Stop_Clear()                       
                    self.wait_until_finished(typeofstream)    #Clears Running_event                                    
                else:
                    self.wait_until_finished(typeofstream)    
            except queue.Empty:                    
                pass            

    def wait_until_finished(self,typeofstream):  
        if typeofstream==1:
            time.sleep(self.cycle_time)
            self.data = self.xyz_thread.read()                
            self.get_state()        
            if self.oldstate_xyz!=self.state_xyz:
                self.oldstate_xyz=self.state_xyz                 
            self.IfEnd_of_Stream()

        if typeofstream==0:            
            while self.IsRunning_event.wait(self.cycle_time): 
                time.sleep(self.cycle_time)
                if self.stoping_event.is_set()==True:
                    self.Stop_Clear()
                if self.killer_event.is_set()==True:
                    break    
                self.data = self.xyz_thread.read()                
                self.get_state()        
                if self.oldstate_xyz!=self.state_xyz:
                    self.oldstate_xyz=self.state_xyz
                self.IfEnd_of_Stream()
            self.linesfinalized_count=self.xyz_thread.Get_linesexecutedCount()  
            linesacknowledged_count=self.xyz_thread.Get_linesacknowledgedCount()
            num_events=self.linesfinalized_count-self.lastlinesfinalized_count+1
            logging.info("Type 0 Number Lines Finished->"+str(self.linesfinalized_count))    
            logging.info("Type 0 Number Lines Acknowledged->"+str(linesacknowledged_count))    
            
            logging.info("Type 0 Number events Finished->"+str(num_events))    

        if typeofstream==2:              
            #logging.info("Debug Buffline->"+str(self.bufflines))                 
            self.linesfinalized_count=self.xyz_thread.Get_linesexecutedCount()  
            linesacknowledged_count=self.xyz_thread.Get_linesacknowledgedCount()
            num_events=self.linesfinalized_count-self.lastlinesfinalized_count+1
            logging.info("Number events Finished->"+str(num_events))
            if num_events>=self.bufflinesize:    
                self.bufflines=0
                self.lastlinesfinalized_count=self.linesfinalized_count            
            self.IfEnd_of_Stream()
    
    def IfEnd_of_Stream(self):                
        if self.text_queue.qsize()==0:   #Nothing in queue             
            self.istext2stream=False
            self.line_count=0
            #self.streamsize=0  
            self.bufflines=0     
            #1=reset, 2=alarm, 3=idle, 4=end, 5=run, 6=hold, 7=probe, 8=cycling,  9=homing, 10 =jogging 11=error                         
            if self.state_xyz<5 or self.state_xyz==11:     # is not running    
                logging.info("End of Gcode Stream :)")       
                self.IsRunning_event.clear() #Event is cleared in INIT state only here else in XYZ thread        
    
    def Do_buffline_count(self):
        if self.line_count==0:
            self.bufflines=0            
        elif self.line_count>self.streamsize:
            self.line_count=0
            self.bufflines=0                
        elif self.line_count<=self.streamsize and self.streamsize>0 and self.line_count>0:            
            if self.bufflines<=self.bufflinesize:       
                self.bufflines=self.bufflines+1  
        else:
            self.bufflines=self.bufflinesize

        

    def Do_line_count(self):
        if self.line_count==0:
            self.bufflines=0
            self.streamsize=self.text_queue.qsize()
            self.line_count=1
            self.xyz_thread.Reset_linesexecutedCount()            
            self.linesfinalized_count=self.xyz_thread.Get_linesexecutedCount()
            self.lastlinesfinalized_count=self.linesfinalized_count
            self.lastRunningstate=self.IsRunning_event.is_set()
            #logging.info('A reset Here')
        elif self.line_count>self.streamsize:
            self.line_count=0
            self.bufflines=0                
        elif self.line_count<=self.streamsize and self.streamsize>0 and self.line_count>0:
            self.line_count=self.line_count+1                        
        try:
            if self.streamsize>0:
                self.Pbarupdate.SetStatus(self.line_count/self.streamsize*100)  
        except:
            pass      
        self.linesfinalized_count=self.xyz_thread.Get_linesexecutedCount()
        

    def Stop_Clear(self):
        if self.istext2stream==True:
            self.text_queue.empty()
            self.istext2stream=False
            logging.info("Gcode Stream Stopped!")
        self.stoping_event.clear()

    def read(self):
        return self.data

    def Stream(self,text2stream,Pbar):
        self.Pbarupdate=Pbar
        self.Pbarupdate.SetStatus(0)
        self.istext2stream=True        
        line=''
        linecount=1
        for lll in text2stream:            
            if lll=='\n':
                if self.killer_event.is_set():
                    break
                if self.stoping_event.is_set():
                    logging.info("Queueing Stopped! ("+str(linecount)+') '+ line )
                    self.Stop_Clear()
                    return                                       
                logging.info("Queueing Line-> ("+str(linecount)+") "+ line)                                            
                self.text_queue.put(line)                    
                self.data = self.xyz_thread.read()                
                self.get_state()                              
                if self.state_xyz==11: # error
                    logging.info("Error in Gcode! ("+str(linecount)+') '+ line )
                    self.Stop_Clear()
                    break                       
                linecount=linecount+1
                line=''
            else:
                line=line+lll   
        logging.info("Queueing Line-> ("+str(linecount)+") "+ line)                                            
        self.text_queue.put(line)                     
        self.istext2stream=False    
        logging.info("End of Queue to Stream!")  
        #Initialize count
        self.line_count=0
        self.Do_line_count()  

    def Islinecontent_ok(self,line):
        contents=line.strip(' ')
        contents=contents.strip('\n')        
        if line=='' or contents=='':
            return False
        return True    

    def stream_one_line(self,line2stream):
        if self.istext2stream==True:                    
            self.xyz_thread.grbl_gcode_cmd(line2stream)
            #logging.info("Sent->"+line2stream)             
        
class ProgressBar_Update(QtCore.QThread):
    tick = QtCore.pyqtSignal(int, name="valchanged") #New style signal

    def __init__(self, parent):
        QtCore.QThread.__init__(self,parent)

    def SetStatus(self,x):
        self.tick.emit(x)                     
        time.sleep(0.1)




if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = MyWindow()#QtWidgets.QMainWindow()
    ui = Ui_MainWindow_V2()
    ui.setupUi(MainWindow)
    ui.setupUi2(MainWindow)    
    #aeventhandler=MainWindowevents(MainWindow)
    handler = ConsolePanelHandler(ui)
    log.addHandler(handler)
    handler.setFormatter(logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s'))        
    aDialog=Dialogs()
    MainWindow.show()
    sys.exit(app.exec_())
