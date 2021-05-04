#!/usr/bin/env python
#from PyQt5 import QtCore, QtGui, QtWidgets
#from PyQt5.QtWidgets import *
#from PyQt5.QtGui import QColor
#from PyQt5.QtCore import QPoint
#from PyQt5.QtGui import QDragEnterEvent
#from PyQt5.QtGui import QDropEvent
#from PyQt5.QtGui import QMouseEvent
#from PyQt5.QtGui import QDrag
#from PyQt5.QtGui import QPixmap
#from PyQt5.QtGui import QCursor

##from PyQt5.QtGui import QListWidget
##from PyQt5.QtGui import QTableWidget
##from PyQt5.QtGui import *
##from PyQt5.QtGui import QFrame

#from PyQt5.QtCore import QSize
#from PyQt5.QtCore import Qt
#from PyQt5.QtCore import QMimeData

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui, QtWidgets 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 

import re
import logging
import GuiXYZ_VBD
import GuiXYZ_VBDD
import class_File_Dialogs
import class_CH
from types import *
import os
import shutil
import sys
import json

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
ahandler=logging.StreamHandler()
ahandler.setLevel(logging.INFO)
ahandler.setFormatter(formatter)
log.addHandler(ahandler)

class Dnd_CustomGroupbox(QGroupBox):    
    new_position = QtCore.pyqtSignal(tuple)
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):    
        e.accept()    

    def Set_Obj_Position(self, target):
        #x,y,W,H=target.get_size_position()
        position = target.frame.rect().topLeft() 
        #print('inside set_obj_pos',position.x(),position.y())
        (x,y)=target.batton_data['Pos'] 
        target.move(position + QPoint(int(x), int(y)))
        anid=target.batton_data['key_id']                
        newpos=(position + QPoint(int(x), int(y)), anid)
        self.new_position.emit(newpos)
        

    def dropEvent(self, e):      
                  
        # find the widget under the cursor
        target=e.source()
        position = e.pos()
        # Receive the sent data
        # Correct the widget position by calculating the mouse position value at the time of the grab
        offset = e.mimeData().data("application/hotspot")
        x, y = offset.data().decode('utf-8').split()
        
        
        target.move(position - QPoint(int(x), int(y)))
        #target.setCursor(QCursor(QtCore.Qt.OpenHandCursor))
        anid=target.batton_data['key_id']
        newpos=(position - QPoint(int(x), int(y)), anid)
        self.new_position.emit(newpos)
        e.accept()

class VBD_Button_set(QWidget):
    mouseHover = QtCore.pyqtSignal(int)
    data_change=QtCore.pyqtSignal(dict)
    focused_id=QtCore.pyqtSignal(int)
    set_position=QtCore.pyqtSignal(int)
    def __init__(self,CH, batton_data, name, parent):
        QtWidgets.QWidget.__init__(self,parent)
        self.parent=parent
        self.setMouseTracking(True)
        self.key_id=None
        self.CH=CH
        self.setObjectName(name)
        self.batton_data=batton_data
        self.Create_VBD_Button()        
        QtCore.QMetaObject.connectSlotsByName(self)
        self.offset = 0    
        
    
    def enterEvent(self, event):
        self.mouseHover.emit(self.batton_data['key_id'])
    
    def leaveEvent(self, event):
        self.mouseHover.emit(-1)

    def Frame_Resize(self):
        W,H=self.batton_data['Size']        
        self.frame.resize(int(W),int(H))
        self.resize(int(W),int(H))
        PBsize=self.pushButton.size()
        self.pushButton.setIconSize(PBsize)
    
    def Frame_Reposition(self):        
        self.set_position.emit(self.batton_data['key_id'])
        #x,y=self.batton_data['Pos']  
        #position=self.parent.rect().topLeft()              
        #print("before move->",position.x(),position.y())     
        #self.frame.rect().setX(x)         
        #self.frame.rect().setY(y)         
        #self.frame.rect().moveTo(QPoint(int(x), int(y)))        
        #position=self.frame.rect().topLeft()              
        #print("after move->",position.x(),position.y())
        
    
    def Signal_Data(self,datadict):
        self.data_change.emit(datadict)

    def get_size_position(self):
        W,H=self.batton_data['Size']
        if W<20:            
            W=self.frame.width()
            self.batton_data.update({'Size':(W,H)})  
        if H<20:
            H=self.frame.height()
            self.batton_data.update({'Size':(W,H)})  
        try:
            x,y=self.batton_data['Pos']
        except:
            x=0
            y=0
            self.batton_data.update({'Pos':(0,0)})
            pass
        return x,y,W,H

    def Create_VBD_Button(self):        
        self.frame = QtWidgets.QFrame(self)
        x,y,W,H=self.get_size_position()
        self.frame.setGeometry(QtCore.QRect(int(x), int(y),int(W), int(H) ))    
        self.frame.setMinimumSize(QSize(40, 40))
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.frame.setSizePolicy(sizePolicy)    
        self.frame.setMouseTracking(True)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")        
        
        #self.splitter = QtWidgets.QSplitter(self.frame)
        #self.splitter.setGeometry(QtCore.QRect(10, 10, int(W)-2*10, int(H)-2*10))
        #sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        #self.splitter.setSizePolicy(sizePolicy)
        #self.splitter.setOrientation(QtCore.Qt.Vertical)
        #self.splitter.setObjectName("splitter")
        
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName("verticalLayout")
        self.pushButton = QtWidgets.QPushButton(self.frame)
        #self.pushButton = QtWidgets.QPushButton(self.splitter)
        try:
            if self.batton_data['Icon']!=None:
                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(self.batton_data['Icon']), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                self.pushButton.setIcon(icon)
        except:
            pass
        self.pushButton.setObjectName("pushButton")        
        self.pushButton.setText(self.batton_data['Name'])
        
        self.pushButton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.pushButton.setSizePolicy(sizePolicy)
        self.verticalLayout.addWidget(self.pushButton)
        
        self.tableWidget = QtWidgets.QTableWidget(self.frame)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setRowCount(0)
        self.verticalLayout.addWidget(self.tableWidget)
        #self.tableWidget = QtWidgets.QTableWidget(self.splitter)
        Parameters=self.batton_data['Params']
        #print('Parameters->',Parameters)
        if len(Parameters)==0:            
            self.batton_data['ShowParams']=False
            self.tableWidget.setHidden(True)
        else:
            self.batton_data['ShowParams']=True
        
        self.tableWidget_2 = QtWidgets.QTableWidget(self.frame)
        self.tableWidget_2.setObjectName("tableWidget_2")
        self.tableWidget_2.setColumnCount(3)
        self.tableWidget_2.setRowCount(0)
        self.verticalLayout.addWidget(self.tableWidget_2)
        #self.tableWidget = QtWidgets.QTableWidget(self.splitter)
        try:
            Parameters_2=self.batton_data['Params_2']
        except:
            Parameters_2={}
            pass
        #print('Parameters->',Parameters)
        if len(Parameters_2)==0:            
            self.batton_data['ShowParams_2']=False
            self.tableWidget_2.setHidden(True)
        else:
            self.batton_data['ShowParams_2']=True

        self.pushButton.adjustSize()        
        self.Do_connections()
    
    def Do_connections(self):
        self.pushButton.pressed.connect(self.PB_Pressed)
        self.pushButton.released.connect(self.PB_Released)
        self.pushButton.clicked.connect(self.PB_clicked)
        self.tableWidget.itemChanged.connect(self.Parameter_Changed)
        self.tableWidget_2.itemChanged.connect(self.Parameter_Changed_2)
    
    def Parameter_Changed(self):
        Parameters=self.Get_Parameter_Values_from_Table(self.tableWidget)
        bparams=self.batton_data['Params']
        for par in Parameters:
            bparams.update({par:Parameters[par]})
        self.batton_data.update({'Params':bparams})
        Gcode=self.Get_Gcode_from_Batton(self.batton_data)
        if Gcode is not '':
            self.batton_data.update({'Gcode':Gcode})
    
    def Parameter_Changed_2(self):
        Parameters=self.Get_Parameter_Values_from_Table(self.tableWidget_2)
        bparams=self.batton_data['Params_2']
        for par in Parameters:
            bparams.update({par:Parameters[par]})
        self.batton_data.update({'Params_2':bparams})
        Gcode=self.Get_Gcode_from_Batton_2(self.batton_data)
        if Gcode is not '':
            self.batton_data.update({'Gcode_2':Gcode})
            
    def Get_Gcode_from_Batton(self,batton_data,warlog=False):
        Gcode=''
        try:
            anid=batton_data['Force_id']
            if anid is '':
                anid=self.CH.id    
        except:
            anid=self.CH.id
            pass
        if self.CH.Is_action_in_Config(batton_data['action'])==True:
            Gcode,isok=self.CH.Get_Gcode_for_Action_id(batton_data['action'],anid,Parameters=batton_data['Params'],Parammustok=True)            
            if isok==False and warlog==True:
                log.warning(batton_data['Name']+' has incorrect Gcode! Check the Parameters!')            
        return Gcode
    
    def Get_Gcode_from_Batton_2(self,batton_data,warlog=False):
        Gcode=''
        try:
            anid=batton_data['Force_id_2']
            if anid is '':
                anid=self.CH.id    
        except:
            anid=self.CH.id
            pass
        if self.CH.Is_action_in_Config(batton_data['action_2'])==True:
            Gcode,isok=self.CH.Get_Gcode_for_Action_id(batton_data['action_2'],anid,Parameters=batton_data['Params_2'],Parammustok=True)            
            if isok==False and warlog==True:
                log.warning(batton_data['Name']+' has incorrect Gcode! Check the second state Parameters!')            
        return Gcode


    def set_data_to_VBD_Button(self,batton_data):
        for item in batton_data:
            value=batton_data[item]
            if item=='Params':
                Parameters=value
                if len(Parameters)==0:                    
                    self.pushButton.adjustSize()
                else:                    
                    self.pushButton.adjustSize()
                    self.Fill_Tablewidget(Parameters)
            if item=='Params_2':
                Parameters=value
                if len(Parameters)==0:                    
                    self.pushButton.adjustSize()
                else:                    
                    self.pushButton.adjustSize()
                    self.Fill_Tablewidget_2(Parameters)
            if item=='Icon':
                Iconfilename=value
                self.Set_button_icon(Iconfilename)
            if item=='Name':
                name=value
                self.pushButton.setText(name)
            if item=='ShowParams':
                showparams=not value     
                #print('hiding->',showparams)           
                self.tableWidget.setHidden(showparams)
            if item=='ShowParams_2':
                showparams=not value     
                #print('hiding->',showparams)           
                self.tableWidget_2.setHidden(showparams)            
            if item=='ShowingParams':
                showparams=value   
                self.Fill_Tablewidget(batton_data['Params'])
            if item=='ShowingParams_2':
                showparams=value   
                self.Fill_Tablewidget_2(batton_data['Params_2'])

            

                
    def Set_button_icon(self,iconfilename):
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(iconfilename), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon)
        PBsize=self.pushButton.size()
        self.pushButton.setIconSize(PBsize)
            
    def Fill_Tablewidget(self,Parameters):
        try:
            ReqOpParamsdict=self.batton_data['ReqOpParamsdict']
        except:
            return
        try:
            Showingparam=self.batton_data['ShowingParams']
        except:
            Showingparam={}
            for par in ReqOpParamsdict:
                Showingparam.update({par:True})
            pass
        Table_NumRows=0
        for ccc in ReqOpParamsdict:  
            if Showingparam[ccc]==True:
                Table_NumRows=Table_NumRows+1
        #Table_NumRows=len(ReqOpParamsdict)
        self.tableWidget.setRowCount(Table_NumRows)
        self.tableWidget.setHorizontalHeaderLabels(["Par", "Val","Const"])
        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)    
        iii=0        
        for ccc in ReqOpParamsdict:  
            if Showingparam[ccc]==True: 
                self.tableWidget.setItem(iii,0, QTableWidgetItem(ccc))
                try:
                    aval=str(Parameters[ccc])
                except:
                    aval=''
                self.tableWidget.setItem(iii,1, QTableWidgetItem(aval))                    
                self.tableWidget.setItem(iii,2, QTableWidgetItem(ReqOpParamsdict[ccc]))
                if ReqOpParamsdict[ccc]=='required':
                    color=QColor('lightblue')
                    self.setColortoRow(self.tableWidget, iii, color)                
                iii=iii+1
        self.tableWidget.resizeColumnsToContents()
    
    def Fill_Tablewidget_2(self,Parameters):
        try:
            ReqOpParamsdict=self.batton_data['ReqOpParamsdict_2']
        except:
            return
        try:
            Showingparam=self.batton_data['ShowingParams_2']
        except:
            Showingparam={}
            for par in ReqOpParamsdict:
                Showingparam.update({par:True})
            pass
        Table_NumRows=0
        for ccc in ReqOpParamsdict:  
            if Showingparam[ccc]==True:
                Table_NumRows=Table_NumRows+1
        #Table_NumRows=len(ReqOpParamsdict)
        self.tableWidget_2.setRowCount(Table_NumRows)
        self.tableWidget_2.setHorizontalHeaderLabels(["Par", "Val","Const"])
        self.tableWidget_2.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)    
        iii=0        
        for ccc in ReqOpParamsdict:  
            if Showingparam[ccc]==True: 
                self.tableWidget_2.setItem(iii,0, QTableWidgetItem(ccc))
                try:
                    aval=str(Parameters[ccc])
                except:
                    aval=''
                self.tableWidget_2.setItem(iii,1, QTableWidgetItem(aval))                    
                self.tableWidget_2.setItem(iii,2, QTableWidgetItem(ReqOpParamsdict[ccc]))
                if ReqOpParamsdict[ccc]=='required':
                    color=QColor('lightblue')
                    self.setColortoRow(self.tableWidget_2, iii, color)                
                iii=iii+1
        self.tableWidget_2.resizeColumnsToContents()

    
    def Get_Parameter_Values_from_Table(self,tableWidget,parcol=0,valcol=1):    
        newparam={}    
        numrows=tableWidget.rowCount()
        try:
            for row in range(numrows):                                   
                Tpar=tableWidget.item(row, parcol).text()             
                Tvalue=tableWidget.item(row, valcol).text()            
                if Tpar is not '' and Tvalue is not '':
                    newparam.update({Tpar:Tvalue})                    
        except:
            newparam={}
            pass            
        return newparam

    def PB_clicked(self):
        print('clicked')
        self.Signal_Data(self.batton_data)
    
    def PB_Pressed(self):
        print('pressed')
        #self.Signal_Data(self.batton_data)
    
    def PB_Released(self):
        print('released')
        #self.Signal_Data(self.batton_data)
    
    # overriding the mousePressEvent method 
    def mouseReleaseEvent(self, event): 
        self.setCursor(QCursor(QtCore.Qt.ArrowCursor))
    
    def mouseMoveEvent(self, e: QMouseEvent): 
        # Left button is for click, so right button input is allowed
        Hf=self.frame.height()
        Wf=self.frame.width()        
        dx=5
        dy=5        

        if e.buttons() == Qt.LeftButton:
            self.focused_id.emit(self.batton_data['key_id'])
            #print('Frame:',self.frame.geometry(),'epos:',e.pos())        
            if e.buttons() == Qt.LeftButton and e.x()>=Wf-dx and e.y()>=Hf-dy:   
                self.focused_id.emit(self.batton_data['key_id'])
                self.setCursor(QCursor(QtCore.Qt.SizeFDiagCursor))         
                self.batton_data.update({'Size':(e.x(),e.y())})  
                self.Frame_Resize()            
        elif e.buttons() == Qt.RightButton:    
            #self.setCursor(QCursor(QtCore.Qt.ClosedHandCursor))
            # Declaration of MIME object for data transmission
            # Save data type and data to be sent in Bytes 
            mime_data = QMimeData()
            mime_data.setData("application/hotspot", b"%d %d" % (e.x(), e.y()))
            drag = QDrag(self)
            # Set MIME type data to Drag
            drag.setMimeData(mime_data)
            # Render the shape to the QPixmap to preserve the shape of the widget when dragging
            pixmap = QPixmap(self.size())
            #print(e.pos(),self.frame.size(),self)
            #print(e.pos(),self.size(),self)
            self.render(pixmap)
            drag.setPixmap(pixmap)        
            drag.setHotSpot(e.pos() - self.rect().topLeft())                       
            drag.exec_(Qt.MoveAction)
        
        if e.x()>=Wf-dx and e.y()>=Hf-dy:   
           self.setCursor(QCursor(QtCore.Qt.SizeFDiagCursor))  
        else:
           self.setCursor(QCursor(QtCore.Qt.ArrowCursor))
    
    def Copy_data(self,adict):
        newdict={}
        for item in adict:
            newdict.update({item:adict[item]})
        return newdict

    def Fill_actionParameters_batton_2(self,batton_data):
        batton_data_2={}#self.Copy_data(batton_data)
        batton_data_2.update({'action':batton_data['action_2']})
        batton_data_2.update({'Force_id':batton_data['Force_id_2']})
        batton_data_2.update({'Gcode':batton_data['Gcode_2']})        
        batton_data_2.update({'Params':batton_data['Params_2']})
        batton_data_2.update({'Format':batton_data['Format_2']})        
        batton_data_2.update({'ReqOpParamsdict':batton_data['ReqOpParamsdict_2']})
        batton_data_2.update({'ShowingParams':batton_data['ShowingParams_2']})
          
        isok,batton_data_2=self.Fill_actionParameters_batton(batton_data_2)
        
        batton_data.update({'action_2':batton_data_2['action']})
        batton_data.update({'Force_id_2':batton_data_2['Force_id']})
        batton_data.update({'Gcode_2':batton_data_2['Gcode']})        
        batton_data.update({'Params_2':batton_data_2['Params']})
        batton_data.update({'Format_2':batton_data_2['Format']})        
        batton_data.update({'ReqOpParamsdict_2':batton_data_2['ReqOpParamsdict']})
        batton_data.update({'ShowingParams_2':batton_data_2['ShowingParams']})

        return isok,batton_data
    
    
    def Fill_actionParameters_batton(self,batton_data):
        action=batton_data['action']
        if batton_data['Force_id'] is '':
            aFormat=self.CH.getGformatforActionid(action,self.CH.id)
        else:
            aFormat=self.CH.getGformatforActionid(action,batton_data['Force_id'])
        isok=False
        
        if self.CH.Check_Format(aFormat)==False:
            log.error("Wrong Format for action "+action)
            batton_data.update({'Gcode':''})
            batton_data.update({'Params':{}})
            return isok
        try:    
            P_Allinfo=self.CH.get_all_info_from_Format(aFormat)
        except:
            P_Allinfo={}
            log.error("Format contains Errors")
            batton_data.update({'Gcode':''})
            batton_data.update({'Params':{}})
            pass
        if P_Allinfo is not {}:            
            if P_Allinfo['IsRegex']==True:
                log.error("Format contains regex read Code")
                batton_data.update({'Gcode':''})
                batton_data.update({'Params':{}})
                return isok
            isok=True    
            ReqOpParamsdict=P_Allinfo['ReqOpParamsdict']
            paramlist=P_Allinfo['Parameterlist']
            optionlist=P_Allinfo['Optionlist']
            optiontxtlist=P_Allinfo['Optiontxtlist']
            minop=P_Allinfo['minRequiredOptions']
            log.info("Processed Format: "+str(P_Allinfo['processedFormat']))                                    
            iii=0            
            Parameters={}  
            givenparams=batton_data['Params']            
            for ccc in ReqOpParamsdict:           
                try:
                    if ccc in givenparams:        
                        pval=givenparams[ccc]                        
                    elif ReqOpParamsdict[ccc]=='required' and ccc not in givenparams:
                        pval='0'
                    else:                        
                        pval=''
                except:
                    pval=iii
                    pass                
                Parameters.update({ccc:pval})                                            
                iii=iii+1            
            Gcode=self.CH.Get_code(aFormat,Parameters)
            log.info("Evaluated Gcode: "+str(Gcode))
            batton_data.update({'action':action})
            batton_data.update({'Params':Parameters})
            batton_data.update({'Format':aFormat})
            batton_data.update({'Gcode':Gcode})
            batton_data.update({'ReqOpParamsdict':ReqOpParamsdict})
            try:
                do_newshow=False
                Showingparams=batton_data['ShowingParams']
                for par in batton_data['ReqOpParamsdict']:                    
                    if par not in Showingparams:
                        do_newshow=True                        
                        break                        
                if do_newshow==True:          
                    Showingparam={}
                    for par in ReqOpParamsdict:
                        Showingparam.update({par:True})
                    batton_data.update({'ShowingParams':Showingparam})                    
            except Exception as e:
                log.error(e)
                Showingparam={}                
                for par in ReqOpParamsdict:                    
                    Showingparam.update({par:True})
                batton_data.update({'ShowingParams':Showingparam})    
                
                                            
        return isok,batton_data    

    def Fill_actionParameters_Table_2(self,tableWidget,batton_data,parcol=0,showall=False):
        batton_data_2={}#self.Copy_data(batton_data)
        batton_data_2.update({'action':batton_data['action_2']})
        batton_data_2.update({'Force_id':batton_data['Force_id_2']})
        batton_data_2.update({'Gcode':batton_data['Gcode_2']})        
        batton_data_2.update({'Params':batton_data['Params_2']})
        batton_data_2.update({'Format':batton_data['Format_2']})        
        batton_data_2.update({'ReqOpParamsdict':batton_data['ReqOpParamsdict_2']})
        batton_data_2.update({'ShowingParams':batton_data['ShowingParams_2']})

        self.Fill_actionParameters_Table(tableWidget,batton_data_2,parcol,showall)

    def Fill_actionParameters_Table(self,tableWidget,batton_data,parcol=0,showall=False):                
        tableWidget.clear()
        Table_NumCols=parcol+3
        tableWidget.setColumnCount(Table_NumCols)
        Table_NumRows=0
        tableWidget.setRowCount(Table_NumRows)       
        
        try:
            ReqOpParamsdict=batton_data['ReqOpParamsdict']
            reqsize=len(ReqOpParamsdict)
        except:
            reqsize=0
            pass
        if batton_data['action'] is '':
            return
        if reqsize>0:            
            #print('Entered FAT ',reqsize)
            Table_NumRows=len(ReqOpParamsdict)
            tableWidget.setRowCount(Table_NumRows)
            if Table_NumCols==3:
                tableWidget.setHorizontalHeaderLabels(["Parameter", "Value","Constraint"])
            elif Table_NumCols==4:
                tableWidget.setHorizontalHeaderLabels(["Show","Parameter", "Value","Constraint"])
            else:
                alphabets_in_capital=[]
                iii=0
                chri=65
                while iii <Table_NumCols:
                    alphabets_in_capital.append(chr(chri))
                    if chri>=91:
                        chri=64
                    chri=chri+1
                    iii=iii+1
                tableWidget.setHorizontalHeaderLabels(alphabets_in_capital)

            tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)    
            iii=0              
            Parameters=batton_data['Params']  
            Showingparam=batton_data['ShowingParams']  
            print('batton in Table-->',batton_data)
            for ccc in ReqOpParamsdict:   
                if Showingparam[ccc]==True or showall==True:
                    tableWidget.setItem(iii,parcol+0, QTableWidgetItem(ccc))
                    try:
                        tableWidget.setItem(iii,parcol+1, QTableWidgetItem(str(Parameters[ccc])))    
                    except:
                        tableWidget.setItem(iii,parcol+1, QTableWidgetItem(''))    

                    tableWidget.setItem(iii,parcol+2, QTableWidgetItem(ReqOpParamsdict[ccc]))
                    if ReqOpParamsdict[ccc]=='required':
                        color=QColor('lightblue')
                        self.setColortoRow(tableWidget, iii, color)                                                        
                iii=iii+1
            tableWidget.resizeColumnsToContents()                        
        
    
    def setColortoRow(self,tableWidget, rowIndex, color):
        try:
            for jjj in range(tableWidget.columnCount()):
                tableWidget.item(rowIndex, jjj).setBackground(color)
        except:
            pass
        

class VBD_Proxy(object):
    def __init__(self, obj):
        self.obj = obj
        obj.handler = self        

    def __getattr__(self, key):
        return getattr(self.obj, key)

    def __setattr__(self, key, value):
        try:
            oldvalue = getattr(self.obj, key)
            if oldvalue != value:
                log.info('Obj Key Value changed from '+str(oldvalue)+' to '+str(value))
            setattr(self.obj, key, value)
        except:
            setattr(self, key, value)
            pass
        else:
            setattr(self, key, value)

class VBD_Handler(object):
    def __init__(self):
        self.key=-1
        self.Object_Key_List=[]
        self.Object_List=[]
        self.Selected_key=None
    
    def Add_Obj(self,Obj,anid=-1):
        #New=VBD_Proxy(Obj)
        if anid==-1:
            anid=self.Get_a_new_id()
        #New.__setattr__("Key_id",anid)
        Obj.key_id=anid
        #self.Object_List.append(New)
        self.Object_List.append(Obj)
        self.Object_Key_List.append(anid)
        self.Selected_key=anid
        #print('added ',anid)
        return anid
    
    def Get_a_new_id(self):
        anid=0
        while anid in self.Object_Key_List:
            anid=anid+1
        return anid             
    
    def Get_Objects_List_Info(self):        
        # Gives a dict of id:Name of battons
        Info_List={}
        for iiiid,Obj in zip(self.Object_Key_List,self.Object_List):
            Info_List.update({iiiid:Obj.batton_data['Name']})
        return Info_List

    def Get_Selected_Object(self):        
        if self.Selected_key in self.Object_Key_List:
            for iiiid,Obj in zip(self.Object_Key_List,self.Object_List):
                if iiiid is self.Selected_key: 
                    #print('Obj type',type(Obj))                   
                    return Obj    
            

    def Select_Object(self,anid):
        if anid in self.Object_Key_List:
            self.Selected_key=anid
        else:
            self.Selected_key=None

    def Del_Obj(self,Obj):
        try:                        
            #anid=Obj. __getattr__("Key_id")
            anid=Obj.key_id
            if Obj in self.Object_List: 
                Obj.batton_data={}               
                Obj.frame.destroy()
                self.Object_List.remove(Obj)
                self.Object_Key_List.remove(anid)
                self.Selected_key=None
                Obj.deleteLater() 
                QApplication.processEvents()
        except:
            pass 
    
class VariableButtonDataDialog(QWidget,GuiXYZ_VBDD.Ui_Dialog_VBDD):

    def __init__(self,Obj,Objs_Info, *args, **kwargs):  
        #QtWidgets.QWidget.__init__(self,parent)              
        super(VariableButtonDataDialog, self).__init__(*args, **kwargs)  
        self.__name__="VBDD"
        self.Obj=Obj
        self.Objs_Info=Objs_Info
        self.CH=self.Obj.CH        
        self.aDialog=class_File_Dialogs.Dialogs()             
        self.Is_Dialog_Open=False  
        self.Copy_original_data()            
        self.openVariableButtonDataDialog()   #comment this line to be called only when you want the dialog         
        self.Obj.batton_data=self.Fill_Form_with_Batton_Data(self.Obj.batton_data)
        self.Obj_refresh()
    
    def Add_keys(self,batton_data):
        try:
            kid=batton_data['key_id']
        except:
            try:
                kid=self.Obj.batton_data['key_id']           
            except Exception as e:
                log.error(e)
                log.error('No key_id in object!')
                self.quit()                
            batton_data.update({'key_id':kid})
        try:
            scriptname=batton_data['Script']
        except:
            batton_data.update({'Script':None})            
            pass
        try:
            icon=batton_data['Icon']
        except:
            batton_data.update({'Icon':None})            
            pass
        try:
            fid=batton_data['Force_id']
        except:
            batton_data.update({'Force_id':''})            
            pass
        try:
            action=batton_data['action']
        except:
            batton_data.update({'action':''})            
            pass
        
        try:
            Params=batton_data['Params']
        except:
            batton_data.update({'Params':{} })            
            pass
        try:
            ReqParams=batton_data['ReqOpParamsdict']
        except:
            batton_data.update({'ReqOpParamsdict':{} })            
            pass        
        try:
            Params=batton_data['Gcode']
        except:
            batton_data.update({'Gcode':''})            
            pass
        try:
            Format=batton_data['Format']
        except:
            batton_data.update({'Format':''})            
            pass
        try:
            Pos=batton_data['Pos']
        except:
            batton_data.update({'Pos':(0, 0)})            
            pass
        try:
            Size=batton_data['Size']
        except:
            batton_data.update({'Size':(100, 50)})            
            pass
        try:
            Name=batton_data['Name']
        except:
            batton_data.update({'Name': 'New'})            
            pass    
        try:
            showparams=batton_data['ShowParams']
        except:
            batton_data.update({'ShowParams': True})            
            pass 
        try:
            showparams=batton_data['ShowingParams']
        except:
            batton_data.update({'ShowingParams': {}})            
            pass  
        try:
            showparams=batton_data['Batton_type']
        except:
            batton_data.update({'Batton_type': 'Push Button'})            
            pass    
        try:
            showparams=batton_data['Batton_is']
        except:
            batton_data.update({'Batton_is': ''})            
            pass
        try:
            showparams=batton_data['Batton_is_2']
        except:
            batton_data.update({'Batton_is_2': ''})            
            pass
        try:
            showparams=batton_data['Batton_type_2']
        except:
            batton_data.update({'Batton_type_2': ''})            
            pass     
        try:
            scriptname=batton_data['Script_2']
        except:
            batton_data.update({'Script_2':None})            
            pass
        try:
            icon=batton_data['Icon_2']
        except:
            batton_data.update({'Icon_2':None})            
            pass
        try:
            fid=batton_data['Force_id_2']
        except:
            batton_data.update({'Force_id_2':''})            
            pass
        try:
            action=batton_data['action_2']
        except:
            batton_data.update({'action_2':''})            
            pass        
        try:
            Params=batton_data['Params_2']
        except:
            batton_data.update({'Params_2':{} })            
            pass
        try:
            ReqParams=batton_data['ReqOpParamsdict_2']
        except:
            batton_data.update({'ReqOpParamsdict_2':{} })            
            pass        
        try:
            Params=batton_data['Gcode_2']
        except:
            batton_data.update({'Gcode_2':''})            
            pass
        try:
            Format=batton_data['Format_2']
        except:
            batton_data.update({'Format_2':''})            
            pass
                
        try:
            showparams=batton_data['ShowParams_2']
        except:
            batton_data.update({'ShowParams_2': False})            
            pass 
        try:
            showparams=batton_data['ShowingParams_2']
        except:
            batton_data.update({'ShowingParams_2': {}})            
            pass  
        try:
            isonestate=batton_data['Is_one_state']
        except:
            batton_data.update({'Is_one_state': True})            
            pass 
        try:
            Linkfrom=batton_data['Link_from']
        except:
            batton_data.update({'Link_from': {}})            
            pass 
        try:
            Linkfrom=batton_data['Link_to']
        except:
            batton_data.update({'Link_to': {}})            
            pass 
        return batton_data        

    def Fill_Form_with_Batton_Data(self,batton_data):
        # Check for any missing keys and add default
        batton_data=self.Add_keys(batton_data)
        #print('after Add_key->',batton_data['action'])
        
        if batton_data['Batton_is']=='script':
            is_script=True
            is_Gcode=False
            is_action=False
        elif batton_data['Batton_is']=='action':
            is_script=False
            is_Gcode=False
            is_action=True
        elif batton_data['Batton_is']=='gcode':    
            is_script=False
            is_Gcode=True
            is_action=False
        else:
            is_script=False
            is_Gcode=False
            is_action=False

        if batton_data['Batton_is_2']=='script':
            is_script_2=True
            is_Gcode_2=False
            is_action_2=False
        elif batton_data['Batton_is_2']=='action':
            is_script_2=False
            is_Gcode_2=False
            is_action_2=True
        elif batton_data['Batton_is_2']=='gcode':    
            is_script_2=False
            is_Gcode_2=True
            is_action_2=False
        else:
            is_script_2=False
            is_Gcode_2=False
            is_action_2=False
        
        
        # Set icon
        
        if batton_data['Icon'] is not None:
            try:
                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(batton_data['Icon']), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                self.Dialog_VBDD.setWindowIcon(icon)
            except Exception as e:
                log.error(e)
                pass
        #Set id label
        self.DVBDui.label_VBDD_id.setText('Batton ID:'+str(batton_data['key_id']))
        #Set interface id combo
        self.Is_Forcedid=False
        try:            
            if self.CH.Check_id_in_dataConfig(self.CH.Configdata,batton_data['Force_id'])==True:
                self.id=batton_data['Force_id']
                self.Is_Forcedid=True
            else:
                self.id=self.CH.id
                batton_data['Force_id']=''
        except:
            self.id=self.CH.id
            batton_data['Force_id']=''
            pass

        if self.Is_Forcedid==True:
            aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.id)
            self.DVBDui.label_VBDD_CHid.setText('Forced to interface: '+aname)                        
        else:
            aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.CH.id)
            self.DVBDui.label_VBDD_CHid.setText('Actual interface: '+aname)
        index= self.DVBDui.comboBox_VBDD_CHid.findText(batton_data['Force_id'],QtCore.Qt.MatchFixedString)
        self.DVBDui.comboBox_VBDD_CHid.setCurrentIndex(index) 
        # Set Name
        self.DVBDui.lineEdit_VBDD_Name.setText(batton_data['Name'])
        # Set action
        index=0
        if batton_data['action'] == '' and batton_data['Batton_is'] != 'action':
           is_action=False
           #index= self.DVBDui.comboBox_VBDD_action.findText(batton_data['action'],QtCore.Qt.MatchFixedString) 
           index=0
        else:
            if self.CH.Is_action_in_Config(batton_data['action'])==True:
                index= self.DVBDui.comboBox_VBDD_action.findText(batton_data['action'],QtCore.Qt.MatchFixedString)
                is_action=True     
                batton_data['Batton_is']='action'           
            else:
                index=0
                #self.set_d('action','',True)
                batton_data['action']=''
                is_action=False
        self.DVBDui.comboBox_VBDD_action.setCurrentIndex(index)        
        #print('after Set action->',batton_data['action'])
        # Set Gcode Result and Params
        if is_action==True:                      
            isok,newbatton_data=self.Obj.Fill_actionParameters_batton(batton_data)                                    
            is_Gcode=False  
            is_script=False
            if isok==False:
                is_Gcode=True  
            else:
                #print('Showing params->',batton_data['ShowingParams'])
                self.Obj.Fill_actionParameters_Table(self.DVBDui.tableWidget_VBDD_parameters,batton_data,parcol=1,showall=True) 
                    
                self.Set_checkable_Parameters(self.DVBDui.tableWidget_VBDD_parameters,0,1,batton_data)
                batton_data=self.Set_checking_Parameters_from_batton(self.DVBDui.tableWidget_VBDD_parameters,0,1,batton_data)
                self.Obj.Fill_actionParameters_Table(self.Obj.tableWidget,batton_data,parcol=0,showall=False)
                
                batton_data=self.Copy_data(newbatton_data)
                #print('after newbattoncopy->',newbatton_data['action'])
                Gcode=self.Obj.Get_Gcode_from_Batton(batton_data)
                if Gcode is not '':
                    #self.set_d('Gcode',Gcode,True)
                    batton_data['Gcode']=Gcode
                    is_Gcode=False                                 
                self.DVBDui.label_VBDD_Result.setText(Gcode)
        else:                        
            # Clean params
            #self.set_d('Params',{},True) 
            batton_data['Params']={}
            self.DVBDui.tableWidget_VBDD_parameters.clear()
            self.DVBDui.tableWidget_VBDD_parameters.setRowCount(0) 
            self.Obj.tableWidget.clear()
            self.Obj.tableWidget.setRowCount(0) 

            if (batton_data['Gcode'] is None or batton_data['Gcode'] is '') and batton_data['Script'] is not None:
                is_Gcode=False  
                is_script=True
                batton_data['Batton_is']='script'
            else:
                is_Gcode=True 
                is_script=False 
                batton_data['Batton_is']='gcode'        
        #print('after Set Gcode and params->',batton_data['action'])    
        # Set Script
        if is_script==True:
            self.DVBDui.label_VBDD_Script.setText('Script:'+batton_data['Script'])
        else:
            #self.set_d('Script',None,True) 
            batton_data['Script']=None
            self.DVBDui.label_VBDD_Script.setText('No Script Selected')
        # Set Gcode   
        self.Set_Gcode_text(batton_data['Gcode'])
        # Set parameter being viewed        
        self.DVBDui.groupBox_VBDD_Parameters.setEnabled(is_action)
        if is_action==False:
            batton_data['ShowParams']=False
        '''    
        else:
            showingparams=batton_data['ShowingParams']
            onetrue=False
            for sp in showingparams:
                if showingparams[sp]==True:
                    onetrue=True
                    break
            if onetrue==False:
                batton_data['ShowParams']=False
        '''
        if batton_data['ShowParams']==True:
            self.DVBDui.groupBox_VBDD_Parameters.setChecked(True)
        else:
            self.DVBDui.groupBox_VBDD_Parameters.setChecked(False)
        #print('after->',batton_data['action'])
        #---------------------------------------------------------------------------------
        # Second state
        #---------------------------------------------------------------------------------
        try:
            index=self.DVBDui.comboBox_VBDD_batton_type.findText(batton_data['Batton_type'],QtCore.Qt.MatchFixedString)
            self.DVBDui.comboBox_VBDD_batton_type.setCurrentIndex(index)                      
        except Exception as e:
            #print(e)
            index=0
            self.DVBDui.comboBox_VBDD_batton_type.setCurrentIndex(index)                                  
            pass
        try:            
            index=self.DVBDui.comboBox_VBDD_batton_type_2.findText(batton_data['Batton_type_2'],QtCore.Qt.MatchFixedString)
            self.DVBDui.comboBox_VBDD_batton_type_2.setCurrentIndex(index)          
        except Exception as e:
            #print(e)
            index=0            
            self.DVBDui.comboBox_VBDD_batton_type_2.setCurrentIndex(index)
            pass
        # Set if is one state or two
        if batton_data['Batton_type'] == 'Push Button':
            Is_one_state=True
        elif batton_data['Batton_type'] == 'Two state toggle': 
            Is_one_state=False
        elif batton_data['Batton_type'] == 'Do while Pressed':
            Is_one_state=True
            if batton_data['Batton_type_2'] == 'Do once on Released':
                Is_one_state=False
        elif batton_data['Batton_type'] == 'Do once on Pressed':
            Is_one_state=True
            if batton_data['Batton_type_2'] == 'Do once on Released':
                Is_one_state=False    
        else:
            Is_one_state=True                                                      
        batton_data.update({'Is_one_state': Is_one_state})    
        if Is_one_state==True:
            batton_data.update({'ShowParams_2': False})    
        #self.DVBDui.tabWidget_VBDFPage2.setEnabled(not Is_one_state)
        self.DVBDui.groupBox_VBDD_byaction_2.setEnabled(not Is_one_state)
        self.DVBDui.groupBox_VBDD_byGcode_2.setEnabled(not Is_one_state)
        self.DVBDui.groupBox_VBDD_byScript_2.setEnabled(not Is_one_state)

        #Set interface id combo
        self.Is_Forcedid_2=False
        try:            
            if self.CH.Check_id_in_dataConfig(self.CH.Configdata,batton_data['Force_id_2'])==True:
                self.id_2=batton_data['Force_id_2']
                self.Is_Forcedid_2=True
            else:
                #self.id=self.CH.id
                batton_data['Force_id_2']=''
        except:
            #self.id=self.CH.id
            batton_data['Force_id_2']=''
            pass

        if self.Is_Forcedid_2==True:
            aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.id_2)
            self.DVBDui.label_VBDD_CHid_2.setText('Forced to interface: '+aname)                        
        else:
            aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.CH.id)
            self.DVBDui.label_VBDD_CHid_2.setText('Actual interface: '+aname)
        index= self.DVBDui.comboBox_VBDD_CHid_2.findText(batton_data['Force_id_2'],QtCore.Qt.MatchFixedString)
        self.DVBDui.comboBox_VBDD_CHid_2.setCurrentIndex(index) 
        
        # Set action
        index=0
        if batton_data['action_2'] == '' and batton_data['Batton_is_2']!='action':
           is_action_2=False
           #index= self.DVBDui.comboBox_VBDD_action.findText(batton_data['action'],QtCore.Qt.MatchFixedString) 
           index=0
        else:
            if self.CH.Is_action_in_Config(batton_data['action_2'])==True:
                index= self.DVBDui.comboBox_VBDD_action_2.findText(batton_data['action_2'],QtCore.Qt.MatchFixedString)
                is_action_2=True
                batton_data['Batton_is_2']='action'
            else:
                index=0
                #self.set_d('action','',True)
                batton_data['action_2']=''
                is_action_2=False
        self.DVBDui.comboBox_VBDD_action_2.setCurrentIndex(index)        
        #print('after Set action->',batton_data['action'])
        # Set Gcode Result and Params
        if is_action_2==True:                                                          
            isok,newbatton_data=self.Obj.Fill_actionParameters_batton_2(batton_data)                                    
            is_Gcode_2=False  
            is_script_2=False
            if isok==False:
                is_Gcode_2=True  
            else:
                #print('Showing params->',batton_data['ShowingParams'])
                self.Obj.Fill_actionParameters_Table_2(self.DVBDui.tableWidget_VBDD_parameters_2,batton_data,parcol=1,showall=True) 
                    
                self.Set_checkable_Parameters_2(self.DVBDui.tableWidget_VBDD_parameters_2,0,1,batton_data)
                batton_data=self.Set_checking_Parameters_from_batton_2(self.DVBDui.tableWidget_VBDD_parameters_2,0,1,batton_data)
                
                self.Obj.Fill_actionParameters_Table_2(self.Obj.tableWidget_2,batton_data,parcol=0,showall=False)
                
                batton_data=self.Copy_data(newbatton_data)
                #print('after newbattoncopy->',newbatton_data['action'])
                Gcode=self.Obj.Get_Gcode_from_Batton_2(batton_data)
                if Gcode is not '':
                    #self.set_d('Gcode',Gcode,True)
                    batton_data['Gcode_2']=Gcode
                    is_Gcode_2=False                                 
                self.DVBDui.label_VBDD_Result_2.setText(Gcode)
        else:                        
            # Clean params
            #self.set_d('Params',{},True) 
            batton_data['Params_2']={}
            self.DVBDui.tableWidget_VBDD_parameters_2.clear()
            self.DVBDui.tableWidget_VBDD_parameters_2.setRowCount(0)             
            self.Obj.tableWidget_2.clear()
            self.Obj.tableWidget_2.setRowCount(0) 

            if (batton_data['Gcode_2'] is None or batton_data['Gcode_2'] is '') and batton_data['Script_2'] is not None:
                is_Gcode_2=False  
                is_script_2=True
                batton_data['Batton_is_2']='script'
            else:
                is_Gcode_2=True 
                is_script_2=False  
                batton_data['Batton_is_2']='gcode'       
        #print('after Set Gcode and params->',batton_data['action'])    
        # Set Script
        if is_script_2==True:
            self.DVBDui.label_VBDD_Script_2.setText('Script:'+batton_data['Script_2'])
        else:
            #self.set_d('Script',None,True) 
            batton_data['Script_2']=None
            self.DVBDui.label_VBDD_Script_2.setText('No Script Selected')
        # Set Gcode   
        self.Set_Gcode_text_2(batton_data['Gcode_2'])
        # Set parameter being viewed        
        self.DVBDui.groupBox_VBDD_Parameters_2.setEnabled(is_action_2)
        if is_action_2==False:
            batton_data['ShowParams_2']=False
        
        if batton_data['ShowParams_2']==True:
            self.DVBDui.groupBox_VBDD_Parameters_2.setChecked(True)
        else:
            self.DVBDui.groupBox_VBDD_Parameters_2.setChecked(False)
        # Linking Connections
        if batton_data['Link_from'] is not {}:
            for LFids in batton_data['Link_from']:
                for index in range(self.DVBDui.listWidget_VBDD_Linkfrom.count()):                    
                    name=self.DVBDui.listWidget_VBDD_Linkfrom.item(index).text()
                    idstr,Num=self.CH.Format_which_Inside_Parenthesees(name,IniP=r'\(',EndP=r'\)')
                    if LFids == idstr[0] and Num > 0:
                        self.DVBDui.listWidget_VBDD_Linkfrom.item(index).setCheckState(QtCore.Qt.Checked)                        
                        break        
        if batton_data['Link_to'] is not {}:
            for LTids in batton_data['Link_to']:
                for index in range(self.DVBDui.listWidget_VBDD_Linkto.count()):                    
                    name=self.DVBDui.listWidget_VBDD_Linkto.item(index).text()
                    idstr,Num=self.CH.Format_which_Inside_Parenthesees(name,IniP=r'\(',EndP=r'\)')
                    if LTids == idstr[0] and Num > 0:
                        self.DVBDui.listWidget_VBDD_Linkfrto.item(index).setCheckState(QtCore.Qt.Checked)                        
                        break        

        return batton_data



    def accept(self):
        log.info("Edit accepted!")
        pass
    
    def Are_battons_the_same(self,battonA,battonB):
        for bbb in battonA:
            try:
                if battonA[bbb] is not battonB[bbb]:
                    return False
            except:
                return False
        return True

    def reject(self):        
        log.info("Edit canceled reverting to Original batton Data")
        #print('Original->',self.Original_batton)
        #print('Changed->',self.Obj.batton_data)
        if self.Are_battons_the_same(self.Original_batton,self.Obj.batton_data)==False:
            self.Obj.batton_data=self.Copy_data(self.Original_batton)  
            self.Obj.batton_data=self.Fill_Form_with_Batton_Data(self.Obj.batton_data)     
            self.Obj_refresh() 

    def Copy_data(self,adict):
        newdict={}
        for item in adict:
            newdict.update({item:adict[item]})
        return newdict

    def Copy_original_data(self):
        self.Original_batton=self.Copy_data(self.Obj.batton_data)
    
    def openVariableButtonDataDialog(self):        
        self.Dialog_VBDD = QtWidgets.QDialog()
        self.DVBDui = GuiXYZ_VBDD.Ui_Dialog_VBDD()
        self.DVBDui.setupUi(self.Dialog_VBDD)        
        self.Dialog_VBDD.show()    
        self.Is_Dialog_Open=True     
        self.Fill_interface_combobox()
        self.Fill_action_combobox()
        self.Fill_Batton_Type_combobox()  
        self.Fill_interface_combobox_2()
        self.Fill_action_combobox_2() 
        self.Fill_Linking_Lists()     
        self.Connect_Data_buttons()
    
    def ComboBox_Select_batton_type(self):
        self.Fill_Batton_Type_2_combobox()
        selbt=self.DVBDui.comboBox_VBDD_batton_type.currentText() 
        self.set_d('Batton_type_2','',False)
        self.set_d('Batton_type',selbt,True)        
        self.Obj.batton_data=self.Fill_Form_with_Batton_Data(self.Obj.batton_data)
        self.Obj_refresh()
    
    def ComboBox_Select_batton_type_2(self):
        selid=self.DVBDui.comboBox_VBDD_batton_type_2.currentText()                                 
        self.set_d('Batton_type_2',selid,True)        
        self.Obj.batton_data=self.Fill_Form_with_Batton_Data(self.Obj.batton_data)
        self.Obj_refresh()

    def ComboBox_Select_interfaceid(self):
        selid=self.DVBDui.comboBox_VBDD_CHid.currentText()                 
        self.set_d('Force_id',selid,True)        
        self.Obj.batton_data=self.Fill_Form_with_Batton_Data(self.Obj.batton_data)
        self.Obj_refresh()
    
    def ComboBox_Select_interfaceid_2(self):
        selid=self.DVBDui.comboBox_VBDD_CHid_2.currentText()                 
        self.set_d('Force_id_2',selid,True)        
        self.Obj.batton_data=self.Fill_Form_with_Batton_Data(self.Obj.batton_data)
        self.Obj_refresh()

    def ComboBox_Select_action(self):
        selaction=self.DVBDui.comboBox_VBDD_action.currentText()                 
        self.set_d('action',selaction,False)
        if selaction is not '':
            aFormat=self.CH.Get_action_format_from_id(self.CH.Configdata,selaction,self.id) 
            self.set_d('Script','',False)            
        else:
            aFormat=''
            self.set_d('Params',{},False)        
        self.set_d('Format',aFormat,True)
        self.DVBDui.label_VBDD_Format.setText(aFormat) 
        #print('Info to be filled:',self.Obj.batton_data)                
        self.Obj.batton_data=self.Fill_Form_with_Batton_Data(self.Obj.batton_data)
        self.Obj_refresh()

    def ComboBox_Select_action_2(self):
        selaction=self.DVBDui.comboBox_VBDD_action_2.currentText()                 
        self.set_d('action_2',selaction,False)
        if selaction is not '':
            aFormat=self.CH.Get_action_format_from_id(self.CH.Configdata,selaction,self.id) 
            self.set_d('Script_2','',False)            
        else:
            aFormat=''
            self.set_d('Params_2',{},False)        
        self.set_d('Format_2',aFormat,True)
        self.DVBDui.label_VBDD_Format_2.setText(aFormat) 
        #print('Info to be filled:',self.Obj.batton_data)                
        self.Obj.batton_data=self.Fill_Form_with_Batton_Data(self.Obj.batton_data)
        self.Obj_refresh()

    def Obj_refresh(self):
        self.Obj.set_data_to_VBD_Button(self.Obj.batton_data)

    def set_d(self,Key,Value,refresh=False):
        self.Obj.batton_data.update({Key:Value})
        if refresh==True:
            self.Obj.set_data_to_VBD_Button(self.Obj.batton_data)

    def PB_Select_Icon(self):
        iconfilename=self.aDialog.openFileNameDialog(1)   #1->Images (*.png *.xpm *.jpg *.bmp)
        self.set_d('Icon',iconfilename,True)    
        self.Obj.batton_data=self.Fill_Form_with_Batton_Data(self.Obj.batton_data) 
        self.Obj_refresh()   

    def PB_Select_Icon_2(self):
        iconfilename=self.aDialog.openFileNameDialog(1)   #1->Images (*.png *.xpm *.jpg *.bmp)
        self.set_d('Icon_2',iconfilename,True)    
        self.Obj.batton_data=self.Fill_Form_with_Batton_Data(self.Obj.batton_data) 
        self.Obj_refresh()    
            
    def Name_Changed(self):        
        aName=self.DVBDui.lineEdit_VBDD_Name.text()
        self.set_d('Name',aName,True)


    def Connect_Data_buttons(self):
        self.DVBDui.buttonBox.accepted.connect(self.accept)
        self.DVBDui.buttonBox.rejected.connect(self.reject)
        self.DVBDui.pushButton_VBDD_Icon.clicked.connect(self.PB_Select_Icon)
        self.DVBDui.pushButton_VBDD_Script.clicked.connect(self.PB_Select_Script)
        self.DVBDui.pushButton_VBDD_Icon_2.clicked.connect(self.PB_Select_Icon_2)
        self.DVBDui.pushButton_VBDD_Script_2.clicked.connect(self.PB_Select_Script_2)
        # activated-When user changes it
        # currentIndexChanged -> when user or program changes it
        self.DVBDui.comboBox_VBDD_action.activated.connect(self.ComboBox_Select_action)
        self.DVBDui.comboBox_VBDD_CHid.currentIndexChanged.connect(self.ComboBox_Select_interfaceid)
        self.DVBDui.comboBox_VBDD_action_2.activated.connect(self.ComboBox_Select_action_2)
        self.DVBDui.comboBox_VBDD_CHid_2.currentIndexChanged.connect(self.ComboBox_Select_interfaceid_2)
        self.DVBDui.comboBox_VBDD_batton_type.activated.connect(self.ComboBox_Select_batton_type)
        self.DVBDui.comboBox_VBDD_batton_type_2.activated.connect(self.ComboBox_Select_batton_type_2)
        #textEdited->only when user changes, not by the program
        #textChanged-> when user changes or the program changes text
        self.DVBDui.lineEdit_VBDD_Name.textEdited.connect(self.Name_Changed)

        self.DVBDui.plainTextEdit_VBDD_Gcode.textChanged.connect(self.Gcode_Change)
        self.DVBDui.plainTextEdit_VBDD_Gcode_2.textChanged.connect(self.Gcode_Change_2)

        self.DVBDui.tableWidget_VBDD_parameters.itemChanged.connect(self.Parameter_Changed)
        self.DVBDui.tableWidget_VBDD_parameters_2.itemChanged.connect(self.Parameter_Changed_2)
        
        self.DVBDui.groupBox_VBDD_byaction.toggled.connect(self.Groupboxbyaction_Checking)
        self.DVBDui.groupBox_VBDD_byGcode.toggled.connect(self.GroupboxbyGcode_Checking)
        self.DVBDui.groupBox_VBDD_byScript.toggled.connect(self.GroupboxbyScript_Checking)

        self.DVBDui.groupBox_VBDD_byaction_2.toggled.connect(self.Groupboxbyaction_Checking_2)
        self.DVBDui.groupBox_VBDD_byGcode_2.toggled.connect(self.GroupboxbyGcode_Checking_2)
        self.DVBDui.groupBox_VBDD_byScript_2.toggled.connect(self.GroupboxbyScript_Checking_2)

        self.DVBDui.groupBox_VBDD_Parameters.toggled.connect(self.Groupboxparametersshow_Checking)
        self.DVBDui.groupBox_VBDD_Parameters_2.toggled.connect(self.Groupboxparametersshow_Checking_2)

        self.DVBDui.listWidget_VBDD_Linkfrom.itemClicked.connect(self.List_widget_Item_Changed_from)
        self.DVBDui.listWidget_VBDD_Linkto.itemClicked.connect(self.List_widget_Item_Changed_to)

    def List_widget_Item_Changed_from(self,anitem):
        #print("item from ",anitem)
        Link_from={}
        for index in range(self.DVBDui.listWidget_VBDD_Linkfrom.count()):                                              
            #print("index ->",index)
            #print(self.DVBDui.listWidget_VBDD_Linkfrom.item(index).checkState(),'==?',QtCore.Qt.Checked)
            if self.DVBDui.listWidget_VBDD_Linkfrom.item(index).checkState() == QtCore.Qt.Checked:
                name=self.DVBDui.listWidget_VBDD_Linkfrom.item(index).text()
                idstr,Num=self.CH.Format_which_Inside_Parenthesees(name,IniP=r'\(',EndP=r'\)')
                if Num==1:
                    Link_from.update({idstr[0]:name})
                print("checked from ->",idstr)
        
        print(Link_from)
        self.set_d('Link_from',Link_from,True)
            

    def List_widget_Item_Changed_to(self,item_index):
        Link_to={}
        for index in range(self.DVBDui.listWidget_VBDD_Linkto.count()):                                              
            #print("index ->",index)
            #print(self.DVBDui.listWidget_VBDD_Linkto.item(index).checkState(),'==?',QtCore.Qt.Checked)
            if self.DVBDui.listWidget_VBDD_Linkto.item(index).checkState() == QtCore.Qt.Checked:
                name=self.DVBDui.listWidget_VBDD_Linkto.item(index).text()
                idstr,Num=self.CH.Format_which_Inside_Parenthesees(name,IniP=r'\(',EndP=r'\)')
                if Num==1:
                    Link_to.update({idstr[0]:name})
                print("checked to ->",idstr)
        
        print(Link_to)
        self.set_d('Link_to',Link_to,True)

    def Parameter_Changed(self):
        Parameters=self.Obj.Get_Parameter_Values_from_Table(self.DVBDui.tableWidget_VBDD_parameters,1,2)
        #print('Got parameters',Parameters)        
        self.set_d('Params',Parameters,True)        
    
    def Parameter_Changed_2(self):
        Parameters=self.Obj.Get_Parameter_Values_from_Table(self.DVBDui.tableWidget_VBDD_parameters_2,1,2)
        #print('Got parameters 2',Parameters)        
        self.set_d('Params_2',Parameters,True)        

    def Get_checked_Parameters_from_Table(self,TableWidget,Checkcol,parcol):
        Numrows=TableWidget.rowCount()        
        Showingparam={}
        for row in range(Numrows):
            item = TableWidget.itemAt(row, Checkcol)
            par=TableWidget.item(row, parcol).text() 
            #print(row,item.checkState())
            if item.checkState() == QtCore.Qt.Checked:                              
                Showingparam.update({par:True})
            elif item.checkState() == QtCore.Qt.Unchecked:
                Showingparam.update({par:False})
            else:
                Showingparam.update({par:None})        
        return Showingparam    

    def Set_checking_Parameters_from_batton(self,TableWidget,Checkcol,parcol,batton_data):          
        try:      
            Showingparam=batton_data['ShowingParams']
            newShowingparam=self.Get_checked_Parameters_from_Table(TableWidget,Checkcol,parcol)
            for par in newShowingparam:
                Showingparam.update({par:newShowingparam[par]})
            batton_data.update({'ShowingParams':Showingparam})            
        except:
            Showingparam={}
            Showingparam=self.Get_checked_Parameters_from_Table(TableWidget,Checkcol,parcol)
            batton_data.update({'ShowingParams':Showingparam})
            pass
        
        return batton_data

    def Set_checking_Parameters_from_batton_2(self,TableWidget,Checkcol,parcol,batton_data):          
        try:      
            Showingparam=batton_data['ShowingParams_2']
            newShowingparam=self.Get_checked_Parameters_from_Table(TableWidget,Checkcol,parcol)
            for par in newShowingparam:
                Showingparam.update({par:newShowingparam[par]})
            batton_data.update({'ShowingParams_2':Showingparam})            
        except:
            Showingparam={}
            Showingparam=self.Get_checked_Parameters_from_Table(TableWidget,Checkcol,parcol)
            batton_data.update({'ShowingParams_2':Showingparam})
            pass
        
        return batton_data    


    def Set_checkable_Parameters(self,TableWidget,Checkcol,parcol,batton_data):
        Numrows=TableWidget.rowCount()
        #NumCols=TableWidget.columnCount()        
        for iii in range(Numrows):              
            '''
            cell_widget = QWidget()
            chk_bx = QCheckBox()
            chk_bx.setTristate(False)
            #chk_bx.setCheckState(Qt.Checked)    
            chk_bx.setCheckState(isChecked)   
            lay_out = QHBoxLayout(cell_widget)
            lay_out.addWidget(chk_bx)
            lay_out.setAlignment(Qt.AlignCenter)
            lay_out.setContentsMargins(0,0,0,0)
            cell_widget.setLayout(lay_out)
            TableWidget.setCellWidget(iii, Checkcol, cell_widget)    
            '''    
            par=TableWidget.item(iii, parcol).text() 
            Showingparams=batton_data['ShowingParams']
            #print(Showingparams,par)
            try:
                show=Showingparams[par]
            except:
                show=True
                pass
            #print('Set checkable parameters->',Showingparams,par,show)
            item=QTableWidgetItem('%s' % par) 
            item.setFlags(QtCore.Qt.ItemIsUserCheckable |QtCore.Qt.ItemIsEnabled)
            if show==True:
                item.setCheckState(QtCore.Qt.Checked)        
            else:
                item.setCheckState(QtCore.Qt.Unchecked)        
            TableWidget.setItem(iii, Checkcol, item)    
            TableWidget.itemClicked.connect(self.handleItemClicked)

    def Set_checkable_Parameters_2(self,TableWidget,Checkcol,parcol,batton_data):
        Numrows=TableWidget.rowCount()
        #NumCols=TableWidget.columnCount()        
        for iii in range(Numrows):              
            
            par=TableWidget.item(iii, parcol).text() 
            Showingparams=batton_data['ShowingParams_2']
            #print(Showingparams,par)
            try:
                show=Showingparams[par]
            except:
                show=True
                pass
            #print('Set checkable parameters->',Showingparams,par,show)
            item=QTableWidgetItem('%s' % par) 
            item.setFlags(QtCore.Qt.ItemIsUserCheckable |QtCore.Qt.ItemIsEnabled)
            if show==True:
                item.setCheckState(QtCore.Qt.Checked)        
            else:
                item.setCheckState(QtCore.Qt.Unchecked)        
            TableWidget.setItem(iii, Checkcol, item)    
            TableWidget.itemClicked.connect(self.handleItemClicked_2)

    def handleItemClicked(self, item):     
        parse=item.text()   
        if item.column()==0:
            if item.checkState() == QtCore.Qt.Checked:
                #print('"%s" Checked' % parse)   
                ischecked=True                
            else:
                parse=item.text()
                #print('"%s" Not Checked' % parse)
                ischecked=False
            Showingpar=self.Obj.batton_data['ShowingParams']
            Showingpar.update({parse:ischecked})
            #print('Showing --->',Showingpar)   
            self.set_d('ShowingParams',Showingpar,True)
    
    def handleItemClicked_2(self, item):     
        parse=item.text()   
        if item.column()==0:
            if item.checkState() == QtCore.Qt.Checked:
                #print('"%s" Checked' % parse)   
                ischecked=True                
            else:
                parse=item.text()
                #print('"%s" Not Checked' % parse)
                ischecked=False
            Showingpar=self.Obj.batton_data['ShowingParams_2']
            Showingpar.update({parse:ischecked})
            #print('Showing --->',Showingpar)   
            self.set_d('ShowingParams_2',Showingpar,True)
        
        
            

    def Set_Gcode_text(self,Gcode,append=False):
        if append==False:
            self.DVBDui.plainTextEdit_VBDD_Gcode.clear()
        self.DVBDui.plainTextEdit_VBDD_Gcode.appendPlainText(Gcode) 
    
    def Set_Gcode_text_2(self,Gcode,append=False):
        if append==False:
            self.DVBDui.plainTextEdit_VBDD_Gcode_2.clear()
        self.DVBDui.plainTextEdit_VBDD_Gcode_2.appendPlainText(Gcode)
    
    def Get_Gcode_text(self):        
        return self.DVBDui.plainTextEdit_VBDD_Gcode.toPlainText()   

    def Get_Gcode_text_2(self):        
        return self.DVBDui.plainTextEdit_VBDD_Gcode_2.toPlainText()      

    def Groupboxparametersshow_Checking(self):
        self.set_d('ShowParams',self.DVBDui.groupBox_VBDD_Parameters.isChecked(),True)
    
    def Groupboxparametersshow_Checking_2(self):
        self.set_d('ShowParams_2',self.DVBDui.groupBox_VBDD_Parameters_2.isChecked(),True)
        

    def Groupboxbyaction_Checking(self):
        if self.DVBDui.groupBox_VBDD_byaction.isChecked()==True:
            self.DVBDui.groupBox_VBDD_byGcode.setChecked(False)
            self.DVBDui.groupBox_VBDD_byScript.setChecked(False)
            self.DVBDui.groupBox_VBDD_byaction.setChecked(True)
        else:                    
            self.DVBDui.groupBox_VBDD_byScript.setChecked(False)
            self.DVBDui.groupBox_VBDD_byGcode.setChecked(True)
    
    def Groupboxbyaction_Checking_2(self):
        if self.DVBDui.groupBox_VBDD_byaction_2.isChecked()==True:
            self.DVBDui.groupBox_VBDD_byGcode_2.setChecked(False)
            self.DVBDui.groupBox_VBDD_byScript_2.setChecked(False)
            self.DVBDui.groupBox_VBDD_byaction_2.setChecked(True)
        else:                    
            self.DVBDui.groupBox_VBDD_byScript_2.setChecked(False)
            self.DVBDui.groupBox_VBDD_byGcode_2.setChecked(True)

    def GroupboxbyGcode_Checking(self):        
        if self.DVBDui.groupBox_VBDD_byGcode.isChecked()==True:
            self.DVBDui.groupBox_VBDD_byaction.setChecked(False)
            self.DVBDui.groupBox_VBDD_byScript.setChecked(False)
            self.DVBDui.groupBox_VBDD_byGcode.setChecked(True)
        else:            
            self.DVBDui.groupBox_VBDD_byScript.setChecked(True)
            self.DVBDui.groupBox_VBDD_byaction.setChecked(False)

    def GroupboxbyGcode_Checking_2(self):        
        if self.DVBDui.groupBox_VBDD_byGcode_2.isChecked()==True:
            self.DVBDui.groupBox_VBDD_byaction_2.setChecked(False)
            self.DVBDui.groupBox_VBDD_byScript_2.setChecked(False)
            self.DVBDui.groupBox_VBDD_byGcode_2.setChecked(True)
        else:            
            self.DVBDui.groupBox_VBDD_byScript_2.setChecked(True)
            self.DVBDui.groupBox_VBDD_byaction_2.setChecked(False)

    def GroupboxbyScript_Checking(self):        
        if self.DVBDui.groupBox_VBDD_byScript.isChecked()==True:
            self.DVBDui.groupBox_VBDD_byGcode.setChecked(False)
            self.DVBDui.groupBox_VBDD_byaction.setChecked(False)
            self.DVBDui.groupBox_VBDD_byScript.setChecked(True)
        else:            
            self.DVBDui.groupBox_VBDD_byaction.setChecked(True)
            self.DVBDui.groupBox_VBDD_byGcode.setChecked(False)
    
    def GroupboxbyScript_Checking_2(self):        
        if self.DVBDui.groupBox_VBDD_byScript_2.isChecked()==True:
            self.DVBDui.groupBox_VBDD_byGcode_2.setChecked(False)
            self.DVBDui.groupBox_VBDD_byaction_2.setChecked(False)
            self.DVBDui.groupBox_VBDD_byScript_2.setChecked(True)
        else:            
            self.DVBDui.groupBox_VBDD_byaction_2.setChecked(True)
            self.DVBDui.groupBox_VBDD_byGcode_2.setChecked(False)

    def Gcode_Change(self):
        Gcodetxt=self.Get_Gcode_text()
        self.set_d('Script','',False)            
        self.set_d('action','',False)    
        self.set_d('Params',{},False)
        self.set_d('Format','',False)    
        self.set_d('Gcode',Gcodetxt,True)
    
    def Gcode_Change_2(self):
        Gcodetxt=self.Get_Gcode_text_2()
        self.set_d('Script_2','',False)            
        self.set_d('action_2','',False)    
        self.set_d('Params_2',{},False)
        self.set_d('Format_2','',False)    
        self.set_d('Gcode_2',Gcodetxt,True)

    def PB_Select_Script(self):
        scriptfilename=self.aDialog.openFileNameDialog(4)  #4->Gcode and Action Files (*.gcode *.acode) 
        if scriptfilename is not None:
            self.set_d('Script',scriptfilename,False)    
            self.set_d('Gcode',None,False)    
            self.set_d('Format','',False)    
            self.set_d('action','',False)    
            self.set_d('Params',{},True)    
        
        self.Obj.batton_data=self.Fill_Form_with_Batton_Data(self.Obj.batton_data)
        self.Obj_refresh()
    
    def PB_Select_Script_2(self):
        scriptfilename=self.aDialog.openFileNameDialog(4)  #4->Gcode and Action Files (*.gcode *.acode) 
        if scriptfilename is not None:
            self.set_d('Script_2',scriptfilename,False)    
            self.set_d('Gcode_2',None,False)    
            self.set_d('Format_2','',False)    
            self.set_d('action_2','',False)    
            self.set_d('Params_2',{},True)    
        
        self.Obj.batton_data=self.Fill_Form_with_Batton_Data(self.Obj.batton_data)
        self.Obj_refresh()
        

    def quit(self):            
        self.Dialog_VBDD.close()
        self.Is_Dialog_Open=False

    def Fill_Batton_Type_combobox(self):        
        self.DVBDui.comboBox_VBDD_batton_type.clear()
        self.DVBDui.comboBox_VBDD_batton_type.addItem('Push Button') 
        self.DVBDui.comboBox_VBDD_batton_type.addItem('Two state toggle')                          
        self.DVBDui.comboBox_VBDD_batton_type.addItem('Do while Pressed')                          
        self.DVBDui.comboBox_VBDD_batton_type.addItem('Do once on Pressed')                          
        #self.DVBDui.comboBox_VBDD_batton_type.addItem('Link from Batton') 
        self.DVBDui.comboBox_VBDD_batton_type_2.clear()         
                                           
        try:            
            index= self.DVBDui.comboBox_VBDD_batton_type.findText(self.Obj.batton_data['Batton_type'],QtCore.Qt.MatchFixedString)
            if index==-1:
                index= 0     
        except:                     
            index= 0 
            pass   
        self.DVBDui.comboBox_VBDD_batton_type.setCurrentIndex(index)    
        self.Fill_Batton_Type_2_combobox()          
    
    def Fill_Linking_Lists(self):
        self.DVBDui.listWidget_VBDD_Linkfrom.clear()
        self.DVBDui.listWidget_VBDD_Linkto.clear()
        for xObj in self.Objs_Info:
            xxxid=str(xObj)
            xxxname='('+xxxid+') '+str(self.Objs_Info[xObj])
            item = QtWidgets.QListWidgetItem()
            item.setText(xxxname)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.DVBDui.listWidget_VBDD_Linkfrom.addItem(item)
            item2 = QtWidgets.QListWidgetItem()
            item2.setText(xxxname)
            item2.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item2.setCheckState(QtCore.Qt.Unchecked)
            self.DVBDui.listWidget_VBDD_Linkto.addItem(item2)
        
    def Fill_Batton_Type_2_combobox(self):  
          
        sel_bt=self.DVBDui.comboBox_VBDD_batton_type.currentText()          
        #print('Fill batton 2 call...',sel_bt)  
        #index=self.DVBui.comboBox_VBDD_batton_type.findText('Push Button',QtCore.Qt.MatchFixedString)
        self.DVBDui.comboBox_VBDD_batton_type_2.clear()         
        if sel_bt == 'Push Button':            
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('')              
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('Link to Batton')
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('Link to Loop')
        elif sel_bt == 'Two state toggle':  
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('Two state toggle') 
        elif sel_bt == 'Do while Pressed':  
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('')     
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('Do once on Released')         
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('Link to Batton')
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('Link to Loop')
        elif sel_bt == 'Do once on Pressed':  
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('')     
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('Do once on Released')         
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('Link to Batton')
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('Link to Loop')
        elif sel_bt == 'Link from Batton':  
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('')     
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('Do once on Released')         
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('Link to Batton')
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('Link to Loop')
        else:
            print('in else')
            self.DVBDui.comboBox_VBDD_batton_type_2.addItem('') 
        try:            
            index= self.DVBDui.comboBox_VBDD_batton_type_2.findText(self.Obj.batton_data['Batton_type_2'],QtCore.Qt.MatchFixedString)
            if index==-1:
                index= 0     
        except:                     
            index= 0 
            pass                      
        index= 0 #index=self.DVBui.comboBox_VBDD_batton_type.findText('Push Button',QtCore.Qt.MatchFixedString)
        self.DVBDui.comboBox_VBDD_batton_type_2.setCurrentIndex(index)          

    def Fill_interface_combobox(self):        
        self.DVBDui.comboBox_VBDD_CHid.clear()
        self.DVBDui.comboBox_VBDD_CHid.addItem('')                          
        for iii in self.CH.Configdata['interfaceId']:           
            self.DVBDui.comboBox_VBDD_CHid.addItem(iii)     
        try:            
            index= self.DVBDui.comboBox_VBDD_CHid.findText(self.Obj.batton_data['Force_id'],QtCore.Qt.MatchFixedString)
            if index==-1:
                index= 0
        except:                     
            index= 0 
            pass

        self.DVBDui.comboBox_VBDD_CHid.setCurrentIndex(index)    
        aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.CH.id)
        self.DVBDui.label_VBDD_CHid.setText('Actual interface '+aname)  

    def Fill_interface_combobox_2(self):        
        self.DVBDui.comboBox_VBDD_CHid_2.clear()
        self.DVBDui.comboBox_VBDD_CHid_2.addItem('')                          
        for iii in self.CH.Configdata['interfaceId']:           
            self.DVBDui.comboBox_VBDD_CHid_2.addItem(iii)                          
        try:            
            index= self.DVBDui.comboBox_VBDD_CHid.findText(self.Obj.batton_data['Force_id_2'],QtCore.Qt.MatchFixedString)
            if index==-1:
                index= 0
        except:                     
            index= 0 
            pass
        self.DVBDui.comboBox_VBDD_CHid_2.setCurrentIndex(index)    
        aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.CH.id)
        self.DVBDui.label_VBDD_CHid_2.setText('Actual interface '+aname)  

    def Fill_action_combobox(self):
        self.DVBDui.comboBox_VBDD_action.clear()
        allactions=self.CH.getListofActions(['interfaceId','interfaceName','interfaceId_type','interfaceId_info'])
        self.DVBDui.comboBox_VBDD_action.addItem('')
        for iii in allactions:           
            self.DVBDui.comboBox_VBDD_action.addItem(iii)          
        try:            
            index= self.DVBDui.comboBox_VBDD_action.findText(self.Obj.batton_data['action'],QtCore.Qt.MatchFixedString)
            if index==-1:
                index= 0
        except:                     
            index= 0 
            pass
        self.DVBDui.comboBox_VBDD_action.setCurrentIndex(index)    
        self.CH.Selected_action=self.DVBDui.comboBox_VBDD_action.currentText()
        #self.Obj.batton_data['key_id']
    
    def Fill_action_combobox_2(self):
        self.DVBDui.comboBox_VBDD_action_2.clear()
        allactions=self.CH.getListofActions(['interfaceId','interfaceName','interfaceId_type','interfaceId_info'])
        self.DVBDui.comboBox_VBDD_action_2.addItem('')
        for iii in allactions:           
            self.DVBDui.comboBox_VBDD_action_2.addItem(iii)          
        try:            
            index= self.DVBDui.comboBox_VBDD_action_2.findText(self.Obj.batton_data['action_2'],QtCore.Qt.MatchFixedString)
            if index==-1:
                index= 0
        except:                     
            index= 0 
            pass
        self.DVBDui.comboBox_VBDD_action_2.setCurrentIndex(index)    
        self.CH.Selected_action=self.DVBDui.comboBox_VBDD_action_2.currentText()
        #self.Obj.batton_data['key_id']

class VariableButtonDialog(QWidget,GuiXYZ_VBD.Ui_Dialog_VBD):
    set_clicked=QtCore.pyqtSignal(list)
    #file_update=QtCore.pyqtSignal(str)
    send_action=QtCore.pyqtSignal(str)

    def __init__(self,selected_interface_id, *args, **kwargs):                
        super(VariableButtonDialog, self).__init__(*args, **kwargs)  
        self.__name__="VBD"
        self.aDialog=class_File_Dialogs.Dialogs()     
        self.id=selected_interface_id #equivalent to is_tinyg
        self.Is_Dialog_Open=False   
        self.Selected_Item=None
        self.Setup_Command_Config()
        self.Activate_test_button=False  #Edit as test
        self.openVariableButtonDialog()   #comment this line to be called only when you want the dialog 
        self.VBD_H=VBD_Handler()   
    
    def Setup_Command_Config(self):
        self.CH=class_CH.Command_Handler(self.id)
        self.Set_Required_actions_to_CH(None,None,None)
        self.id=self.CH.id                  
    
    def send_action(self,actioninfo):
        self.send_action.emit(actioninfo)
    
    #def file_has_updated(self,filename):
    #    self.file_update.emit(filename)

    def Set_Required_actions_to_CH(self,Reqcc,Reqic,Reqrc):
        if Reqcc is None or Reqcc is {}:
            Reqcc={'interfaceId','interfaceName'}
        if Reqic is None or Reqic is {}:
            Reqic={'interfaceId'}         
        if Reqrc is None or Reqrc is {}:
            Reqrc={'interfaceId'}       
        self.CH.Required_read=Reqrc           
        self.CH.Required_actions=Reqcc    
        self.CH.Required_interface=Reqic    

    def accept(self):
        try:
            self.VBDD_Dialog.quit()
        except:
            pass
        log.info("Accepted Closing Dialog")
        pass
    
    def reject(self):        
        try:
            self.VBDD_Dialog.quit()
        except:
            pass
        log.info("Rejected Closing Dialog")
        

    def quit(self):
        try:
            self.VBDD_Dialog.quit()
        except:
            pass
        self.Dialog_VBD.close()
        self.Is_Dialog_Open=False
           
    def openVariableButtonDialog(self):
        self.Dialog_VBD = QtWidgets.QDialog()
        self.DVBui = GuiXYZ_VBD.Ui_Dialog_VBD()
        self.DVBui.setupUi(self.Dialog_VBD)        
        self.Dialog_VBD.show()           
        self.Is_Dialog_Open=True    
        self.Connect_Main_Button()
        
        self.DVBui.groupBox_VBD_VarButtons = Dnd_CustomGroupbox("Custom Buttons",self.DVBui.frame_VBD_var)
        self.DVBui.groupBox_VBD_VarButtons.setMouseTracking(True)
        self.DVBui.groupBox_VBD_VarButtons.setAcceptDrops(True)
        self.DVBui.groupBox_VBD_VarButtons.setObjectName("groupBox_VBD_VarButtons")        
        self.DVBui.gridLayout_2.addWidget(self.DVBui.groupBox_VBD_VarButtons, 0, 1, 1, 1)
        self.DVBui.groupBox_VBD_VarButtons.new_position[tuple].connect(self.VBD_Set_Position)
        self.clickable(self.DVBui.groupBox_VBD_VarButtons).connect(self.VBD_Deselect)
    
    def clickable(self,widget):    
        class Filter(QObject):        
            clicked = QtCore.pyqtSignal()
            def eventFilter(self, obj, event):            
                if obj == widget:
                    if event.type() == QtCore.QEvent.MouseButtonRelease:
                        if obj.rect().contains(event.pos()):
                            self.clicked.emit()
                            # The developer can opt for .emit(obj) to get the object within the slot.
                            return True                
                return False       
        filter = Filter(widget)
        widget.installEventFilter(filter)
        return filter.clicked 

    def PB_Add_Button(self):
        abtn=self.create_batton()
        self.Edit_Batton_Data(abtn)
    
    def create_batton(self,b_data=None):
        
        batton_data={'Pos':(0,0),'Size':(200,200),'Name':'New','Icon':None,'action':'','Gcode':'','Params':{}}
        if b_data==None:
            anid=-1
        else:            
            anid=int(b_data['key_id'])
        abtn = VBD_Button_set(self.CH,batton_data,"Drag Me", self.DVBui.groupBox_VBD_VarButtons)
        #print('Size-->',abtn.size(),abtn.pos())
        abtn.batton_data.update({'Size':(100,50)})
        abtn.Frame_Resize()
        #print('Size after -->',abtn.size(),abtn.pos())
        anid=self.VBD_H.Add_Obj(abtn,anid)        
        abtn.batton_data.update({'key_id':anid})        
        abtn.show()
        log.info('Batton Object Added ID:'+str(anid))
        #self.btn.pushButton.clicked.connect(self.btn_click)
        self.DVBui.groupBox_VBD_VarButtons.setAcceptDrops(True)
        abtn.data_change[dict].connect(self.VBD_Button_Clicked)
        abtn.mouseHover[int].connect(self.VBD_Hovered)
        abtn.focused_id[int].connect(self.VBD_Selected)  
        abtn.set_position[int].connect(self.VBD_Reposition)  
              
        return abtn


    def Edit_Batton_Data(self,Obj):
        Objs_Info=self.VBD_H.Get_Objects_List_Info()
        self.VBDD_Dialog=VariableButtonDataDialog(Obj,Objs_Info)

    def Clone_Batton_Data(self,Obj):
        newbatton_data=self.Copy_data(Obj.batton_data)
        anid=self.VBD_H.Get_a_new_id()
        newbatton_data.update({'key_id':anid})
        newbatton_data.update({'Name':newbatton_data['Name']+'_'+str(anid)})
        newbatton_data.update({'Pos':(0,0)})
        #print(newbatton_data)
        abtn=self.create_batton(newbatton_data)
        abtn.batton_data=self.Copy_data(newbatton_data)
        abtn.set_data_to_VBD_Button(abtn.batton_data)   
        abtn.Frame_Resize()            
        abtn.Frame_Reposition()
        


    def VBD_Set_Position(self,newpos):
        apos,anid=newpos
        for iiiid,Obj in zip(self.VBD_H.Object_Key_List,self.VBD_H.Object_List):
            if iiiid is anid:
                Obj.batton_data.update({'Pos':(apos.x(),apos.y())})            
                #print('New pos',Obj.batton_data['Pos'])
                

    def VBD_Hovered(self,anid):
        #print('Hovered',anid)
        for iiiid,Obj in zip(self.VBD_H.Object_Key_List,self.VBD_H.Object_List):
            if iiiid is anid:
                #Obj.frame.setStyleSheet("border: 2px solid blue;")
                Obj.frame.setFrameShadow(QFrame.Plain)
            else:
                Obj.frame.setFrameShadow(QFrame.Raised)

    def VBD_Deselect(self):
        #print('Pressed GB')
        self.VBD_Selected(-1)

    def VBD_Reposition(self,anid):
         #print('reposition',anid)
         for iiiid,Obj in zip(self.VBD_H.Object_Key_List,self.VBD_H.Object_List):
            if iiiid is anid:
                #Obj.batton_data.update({'Pos':(apos.x(),apos.y())})
                self.DVBui.groupBox_VBD_VarButtons.Set_Obj_Position(Obj)

    def VBD_Selected(self,anid):        
        self.VBD_H.Select_Object(anid)
        self.Selected_Item=self.VBD_H.Selected_key                
        for iiiid,Obj in zip(self.VBD_H.Object_Key_List,self.VBD_H.Object_List):
            if iiiid is anid:
                Obj.frame.setStyleSheet("border: 2px solid blue;")
            else:
                Obj.frame.setStyleSheet("")
        '''
        #Not returning obj but method :S
        Obj=self.VBD_H.Get_Selected_Object
        print(type(Obj))
        if Obj is not None:
            Obj.frame.setStyleSheet("border: 2px solid blue;")
        else:
            for Objiii in self.VBD_H.Object_List:
                Objiii.frame.setStyleSheet("")
        '''        

    def VBD_Button_Clicked(self,batton_data):
        print(batton_data)

    def dragEnterEvent(self, e: QDragEnterEvent):
        e.accept()

    def Connect_Main_Button(self):    
        #Connect buttons
        if self.Activate_test_button==False:
            self.DVBui.pushButton_VBD_ButtonClone.clicked.connect(self.PB_Clone_Button)
        else:
            self.DVBui.pushButton_VBD_ButtonEdit.clicked.connect(self.PB_debugtests)
            self.DVBui.pushButton_VBD_ButtonEdit.setText('Debug!')
        self.DVBui.pushButton_VBD_ButtonEdit.clicked.connect(self.PB_Edit_Button)
        self.DVBui.pushButton_VBD_ButtonAdd.clicked.connect(self.PB_Add_Button)        
        self.DVBui.pushButton_VBD_ButtonRemove.clicked.connect(self.PB_Remove_Button)
        self.DVBui.pushButton_VBD_Save.clicked.connect(self.PB_Save_Button_Layout)
        self.DVBui.pushButton_VBD_Load.clicked.connect(self.PB_Load_Button_Layout)
        self.DVBui.buttonBox.accepted.connect(self.accept)
        self.DVBui.buttonBox.rejected.connect(self.reject)

    def PB_Remove_Button(self):
        anid=self.Selected_Item                
        for iiiid,Obj in zip(self.VBD_H.Object_Key_List,self.VBD_H.Object_List):
            if iiiid is anid:
                self.VBD_H.Del_Obj(Obj)  
                log.info('Batton Object Deleted ID:'+str(anid))
                break                      
    
    def Remove_all_Obj(self):
        self.Selected_Item=None
        #print('List before ',self.VBD_H.Object_Key_List)        
        #print('size',len(self.VBD_H.Object_List))
        while self.VBD_H.Object_Key_List!=[]:
            #anid=self.VBD_H.Object_Key_List[0]
            Obj=self.VBD_H.Object_List[0]
            anid=Obj.key_id
            self.VBD_H.Del_Obj(Obj)        
            #print('Deleted ',anid)
                

        self.VBD_H.Object_Key_List=[]
        self.VBD_H.Object_List=[]
        log.info('Removed all batton objects!')

    def Copy_data(self,adict):
        newdict={}
        for item in adict:
            newdict.update({item:adict[item]})
        return newdict

    def PB_Edit_Button(self):
        anid=self.Selected_Item                
        for iiiid,Obj in zip(self.VBD_H.Object_Key_List,self.VBD_H.Object_List):
            if iiiid is anid:
                self.Edit_Batton_Data(Obj)
                #print('Edit button pressed')
    def PB_Clone_Button(self):
        anid=self.Selected_Item                
        for iiiid,Obj in zip(self.VBD_H.Object_Key_List,self.VBD_H.Object_List):
            if iiiid is anid:
                self.Clone_Batton_Data(Obj)
                #print('Edit button pressed')
    
    def Refresh_viewed_filenames(self):        
        fff=self.shorten_filename(self.extract_filename(self.CH.filename,False))
        self.DVBui.groupBox_CCD_actionFiles.setTitle("Actual Config File:"+fff)  
    
    def PB_debugtests(self):        
        print('--------------------------------------------------')
        
    '''
    def left_click_P(self, nb):
        if nb == 1: print('Single left click')
        else: print('Double left click')

    def right_click_P(self, nb):
        if nb == 1: print('Single right click')
        else: print('Double right click')
    ''' 
    def PB_Save_Button_Layout(self):
        self.Save_Button_Layout(None)
    
    def extract_filename(self,filename,withextension=True):
        fn= os.path.basename(filename)  # returns just the name
        fnnoext, fext = os.path.splitext(fn)
        fnnoext=fnnoext.replace(fext,'')
        fn=fnnoext+fext        
        if withextension==True:
            return fn
        else:                
            return  fnnoext #fn.rsplit('.', 1)[0]

    def Save_Button_Layout(self,afilename=None):  
        if afilename is None:
            filename=self.aDialog.saveFileDialog(5)       #batton *.btncfg
        else:
            filename=afilename
        print(afilename)
        
        if filename == '' or filename is None:
            return      
        if filename is not None:                   
            try:
                mfile=re.search('(\.btncfg$)',filename)
                if mfile.group(1)!='.btncfg': 
                    filename=filename+'.btncfg'
            except:
                filename=filename+'.btncfg'        
            log.info('Saving:'+filename) 
            self.Dialog_VBD.setWindowTitle('VBD_'+self.extract_filename(filename,withextension=False))
            try:
                b_dict=self.get_batton_dict()
                with open(filename, 'w') as yourFile:                                                  
                    json.dump(b_dict, yourFile,indent=2)                    
                yourFile.close()                
            except Exception as e:
                log.error(e)
                log.info("Batton configuration File was not Written!")    
        
    def get_batton_dict(self):
        b_dict={}
        b_dict.update({'Batton_Key_List':self.VBD_H.Object_Key_List})
        b_dict.update({'Window_Settings':self.get_window_settings()})
        for iiiid,Obj in zip(self.VBD_H.Object_Key_List,self.VBD_H.Object_List):             
            b_dict.update({iiiid:Obj.batton_data})
        return b_dict
    
    def get_window_settings(self):
        windowsettigs={}
        #self.Dialog_VBD.settings = QtCore.QSettings('VBDCompany', 'VBDtool')
        #geometry=self.Dialog_VBD.settings.value('geometry', '')        
        #geometry = self.Dialog_VBD.saveGeometry()     
        #W = self.Dialog_VBD.geometry.Width()   
        #H = self.Dialog_VBD.geometry.Height()   
        #geometry=(W,H)
        #self.Dialog_VBD.settings.setValue('geometry', geometry)
        windowsettigs.update({'windowTitle':self.Dialog_VBD.windowTitle() })
        #windowsettigs.update({'geometry':geometry})
        #windowsettigs.update({'W_Size':(1000,1000)})
        #windowsettigs.update({'Slide_pos':(1000,1000)})
        return windowsettigs
    
    def set_window_settings(self,windowsettigs):
         #Obj.frame.setGeometry(QtCore.QRect(int(x), int(y),int(W), int(H) ))          
        self.Dialog_VBD.setWindowTitle(windowsettigs['windowTitle'])
        geometry=windowsettigs['geometry']
        #(W,H)=geometry
        #x=0
        #y=0
        #self.restoreGeometry(geometry)
        #geometry = self.Dialog_VBD.saveGeometry()        
        #self.Dialog_VBD.settings.setValue('geometry', geometry)
        #self.Dialog_VBD.setGeometry(QtCore.QRect(int(x), int(y),int(W), int(H) )) 
        print('Window settings',windowsettigs)                
    
    def set_batton_dict(self,b_dict,flushall=True):
        if flushall==True:
            self.Remove_all_Obj()
        try:
            self.set_window_settings(b_dict['Window_Settings'])    
        except:
            log.error('No Window settings in Load File!')
            pass
        objlist=b_dict['Batton_Key_List']
        #print(objlist)
        for iiiid in objlist:                         
            #print(b_dict[str(iiiid)])
            self.create_batton(b_dict[str(iiiid)])
        for iiiid,Obj in zip(self.VBD_H.Object_Key_List,self.VBD_H.Object_List):             
            Obj.batton_data=self.Copy_data(b_dict[str(iiiid)])
            Obj.set_data_to_VBD_Button(Obj.batton_data)   
            Obj.Frame_Resize()            
            Obj.Frame_Reposition()
            #x,y,W,H=Obj.get_size_position()
            #Obj.set_position.emit(iiiid)
            #print(x,y,W,H)
            
            #Obj.frame.setGeometry(QtCore.QRect(int(x), int(y),int(W), int(H) ))                     
        
    def PB_Load_Button_Layout(self):
        self.Load_Button_Layout(None)

    def Load_Button_Layout(self,fn=None):            
        if fn==None:
            filename=self.aDialog.openFileNameDialog(5)       #batton *.btncfg
        else:
            filename=fn
        if filename == '' or filename is None:
            return      
        if filename is not None:                           
            log.info('Loading:'+filename) 
            try:                                
                with open(filename, 'r') as yourFile:          
                    b_dict=json.load(yourFile)
                    #print(b_dict)
                    self.set_batton_dict(b_dict,True)
                yourFile.close()                
            except Exception as e:
                log.error(e)
                log.info("Batton configuration File was not Read!")    

        

def main():
    anid='0'
    app = QtWidgets.QApplication(sys.argv)
    VBD_test=VariableButtonDialog(anid)                
    sys.exit(app.exec_())   

if __name__ == '__main__':
    main()
