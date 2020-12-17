#!/usr/bin/env python
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QDragEnterEvent
from PyQt5.QtGui import QDropEvent
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtGui import QDrag
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QCursor
#from PyQt5.QtGui import QTableWidget
#from PyQt5.QtGui import *
#from PyQt5.QtGui import QFrame
from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QMimeData
from PyQt5.QtCore import QObject


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
    def __init__(self,CH, batton_data, name, parent):
        QtWidgets.QWidget.__init__(self,parent)
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

        if self.batton_data['Icon']!=None:
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(self.batton_data['Icon']), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.pushButton.setIcon(icon)

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
        self.pushButton.adjustSize()        
        self.Do_connections()
    
    def Do_connections(self):
        self.pushButton.clicked.connect(self.PB_clicked)
        self.tableWidget.itemChanged.connect(self.Parameter_Changed)
    
    def Parameter_Changed(self):
        Parameters=self.Get_Parameter_Values_from_Table(self.tableWidget)
        bparams=self.batton_data['Params']
        for par in Parameters:
            bparams.update({par:Parameters[par]})
        self.batton_data.update({'Params':bparams})
        Gcode=self.Get_Gcode_from_Batton(self.batton_data)
        if Gcode is not '':
            self.batton_data.update({'Gcode':Gcode})
            
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
            if item=='ShowingParams':
                showparams=value   
                self.Fill_Tablewidget(batton_data['Params'])

            

                
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
        self.Signal_Data(self.batton_data)
    
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
                        pval='Fill Me'
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
        
    
    def setColortoRow(self,table, rowIndex, color):
        for jjj in range(table.columnCount()):
            table.item(rowIndex, jjj).setBackground(color)
        

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
    
    def Add_Obj(self,Obj,anid=0):
        #New=VBD_Proxy(Obj)
        if anid==0:
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
                self.Object_List.remove(Obj)
                self.Object_Key_List.remove(anid)
                self.Selected_key=None
                Obj.deleteLater() 
        except:
            pass 
    
class VariableButtonDataDialog(QWidget,GuiXYZ_VBDD.Ui_Dialog_VBDD):

    def __init__(self,Obj, *args, **kwargs):  
        #QtWidgets.QWidget.__init__(self,parent)              
        super(VariableButtonDataDialog, self).__init__(*args, **kwargs)  
        self.__name__="VBDD"
        self.Obj=Obj
        self.CH=self.Obj.CH        
        self.aDialog=class_File_Dialogs.Dialogs()             
        self.Is_Dialog_Open=False              
        self.openVariableButtonDataDialog()   #comment this line to be called only when you want the dialog 
        self.Copy_original_data()
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
        return batton_data        

    def Fill_Form_with_Batton_Data(self,batton_data):
        is_script=False
        is_Gcode=False
        is_action=False
        
        # Check for any missing keys and add default
        batton_data=self.Add_keys(batton_data)
        #print('after Add_key->',batton_data['action'])
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
        if batton_data['action'] is '':
           is_action=False
           #index= self.DVBDui.comboBox_VBDD_action.findText(batton_data['action'],QtCore.Qt.MatchFixedString) 
           index=0
        else:
            if self.CH.Is_action_in_Config(batton_data['action'])==True:
                index= self.DVBDui.comboBox_VBDD_action.findText(batton_data['action'],QtCore.Qt.MatchFixedString)
                is_action=True
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
            else:
                is_Gcode=True 
                is_script=False         
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
        self.Connect_Data_buttons()
    
    def ComboBox_Select_interfaceid(self):
        selid=self.DVBDui.comboBox_VBDD_CHid.currentText()                 
        self.set_d('Force_id',selid,True)        
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
            
    def Name_Changed(self):        
        aName=self.DVBDui.lineEdit_VBDD_Name.text()
        self.set_d('Name',aName,True)


    def Connect_Data_buttons(self):
        self.DVBDui.buttonBox.accepted.connect(self.accept)
        self.DVBDui.buttonBox.rejected.connect(self.reject)
        self.DVBDui.pushButton_VBDD_Icon.clicked.connect(self.PB_Select_Icon)
        self.DVBDui.pushButton_VBDD_Script.clicked.connect(self.PB_Select_Script)
        # activated-When user changes it
        # currentIndexChanged -> when user or program changes it
        self.DVBDui.comboBox_VBDD_action.activated.connect(self.ComboBox_Select_action)
        self.DVBDui.comboBox_VBDD_CHid.currentIndexChanged.connect(self.ComboBox_Select_interfaceid)
        #textEdited->only when user changes, not by the program
        #textChanged-> when user changes or the program changes text
        self.DVBDui.lineEdit_VBDD_Name.textEdited.connect(self.Name_Changed)

        self.DVBDui.plainTextEdit_VBDD_Gcode.textChanged.connect(self.Gcode_Change)

        self.DVBDui.tableWidget_VBDD_parameters.itemChanged.connect(self.Parameter_Changed)
        
        self.DVBDui.groupBox_VBDD_byaction.toggled.connect(self.Groupboxbyaction_Checking)
        self.DVBDui.groupBox_VBDD_byGcode.toggled.connect(self.GroupboxbyGcode_Checking)
        self.DVBDui.groupBox_VBDD_byScript.toggled.connect(self.GroupboxbyScript_Checking)

        self.DVBDui.groupBox_VBDD_Parameters.toggled.connect(self.Groupboxparametersshow_Checking)


    def Parameter_Changed(self):
        Parameters=self.Obj.Get_Parameter_Values_from_Table(self.DVBDui.tableWidget_VBDD_parameters,1,2)
        #print('Got parameters',Parameters)        
        self.set_d('Params',Parameters,True)        

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
            print(Showingparams,par)
            try:
                show=Showingparams[par]
            except:
                show=True
                pass
            print('Set checkable parameters->',Showingparams,par,show)
            item=QTableWidgetItem('%s' % par) 
            item.setFlags(QtCore.Qt.ItemIsUserCheckable |QtCore.Qt.ItemIsEnabled)
            if show==True:
                item.setCheckState(QtCore.Qt.Checked)        
            else:
                item.setCheckState(QtCore.Qt.Unchecked)        
            TableWidget.setItem(iii, Checkcol, item)    
            TableWidget.itemClicked.connect(self.handleItemClicked)

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
            print('Showing --->',Showingpar)   
            self.set_d('ShowingParams',Showingpar,True)
        
        
            

    def Set_Gcode_text(self,Gcode,append=False):
        if append==False:
            self.DVBDui.plainTextEdit_VBDD_Gcode.clear()
        self.DVBDui.plainTextEdit_VBDD_Gcode.appendPlainText(Gcode) 
    
    def Get_Gcode_text(self):        
        return self.DVBDui.plainTextEdit_VBDD_Gcode.toPlainText()        

    def Groupboxparametersshow_Checking(self):
        self.set_d('ShowParams',self.DVBDui.groupBox_VBDD_Parameters.isChecked(),True)
        

    def Groupboxbyaction_Checking(self):
        if self.DVBDui.groupBox_VBDD_byaction.isChecked()==True:
            self.DVBDui.groupBox_VBDD_byGcode.setChecked(False)
            self.DVBDui.groupBox_VBDD_byScript.setChecked(False)
            self.DVBDui.groupBox_VBDD_byaction.setChecked(True)
        else:                    
            self.DVBDui.groupBox_VBDD_byScript.setChecked(False)
            self.DVBDui.groupBox_VBDD_byGcode.setChecked(True)
    
    def GroupboxbyGcode_Checking(self):        
        if self.DVBDui.groupBox_VBDD_byGcode.isChecked()==True:
            self.DVBDui.groupBox_VBDD_byaction.setChecked(False)
            self.DVBDui.groupBox_VBDD_byScript.setChecked(False)
            self.DVBDui.groupBox_VBDD_byGcode.setChecked(True)
        else:            
            self.DVBDui.groupBox_VBDD_byScript.setChecked(True)
            self.DVBDui.groupBox_VBDD_byaction.setChecked(False)

    def GroupboxbyScript_Checking(self):        
        if self.DVBDui.groupBox_VBDD_byScript.isChecked()==True:
            self.DVBDui.groupBox_VBDD_byGcode.setChecked(False)
            self.DVBDui.groupBox_VBDD_byaction.setChecked(False)
            self.DVBDui.groupBox_VBDD_byScript.setChecked(True)
        else:            
            self.DVBDui.groupBox_VBDD_byaction.setChecked(True)
            self.DVBDui.groupBox_VBDD_byGcode.setChecked(False)

    def Gcode_Change(self):
        Gcodetxt=self.Get_Gcode_text()
        self.set_d('Script','',False)            
        self.set_d('action','',False)    
        self.set_d('Params',{},False)
        self.set_d('Format','',False)    
        self.set_d('Gcode',Gcodetxt,True)

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
        
        

    def quit(self):            
        self.Dialog_VBDD.close()
        self.Is_Dialog_Open=False
           
    def Fill_interface_combobox(self):        
        self.DVBDui.comboBox_VBDD_CHid.clear()
        self.DVBDui.comboBox_VBDD_CHid.addItem('')                          
        for iii in self.CH.Configdata['interfaceId']:           
            self.DVBDui.comboBox_VBDD_CHid.addItem(iii)                          
        index= 0 #self.DVBui.comboBox_CCD_interface.findText(self.CH.id,QtCore.Qt.MatchFixedString)
        self.DVBDui.comboBox_VBDD_CHid.setCurrentIndex(index)    
        aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.CH.id)
        self.DVBDui.label_VBDD_CHid.setText('Actual interface '+aname)  

    def Fill_action_combobox(self):
        self.DVBDui.comboBox_VBDD_action.clear()
        allactions=self.CH.getListofActions(['interfaceId','interfaceName','interfaceId_type','interfaceId_info'])
        self.DVBDui.comboBox_VBDD_action.addItem('')
        for iii in allactions:           
            self.DVBDui.comboBox_VBDD_action.addItem(iii)          
        #index= self.DVBDui.comboBox_VBDD_action.findText('interfaceName',QtCore.Qt.MatchFixedString)
        index=0
        self.DVBDui.comboBox_VBDD_action.setCurrentIndex(index)    
        self.CH.Selected_action=self.DVBDui.comboBox_VBDD_action.currentText()
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
        batton_data={'Pos':(0,0),'Size':(200,200),'Name':'New','Icon':None,'action':'','Gcode':'','Params':{}}
        abtn = VBD_Button_set(self.CH,batton_data,"Drag Me", self.DVBui.groupBox_VBD_VarButtons)
        #print('Size-->',abtn.size(),abtn.pos())
        abtn.batton_data.update({'Size':(100,50)})
        abtn.Frame_Resize()
        #print('Size after -->',abtn.size(),abtn.pos())
        anid=self.VBD_H.Add_Obj(abtn)        
        abtn.batton_data.update({'key_id':anid})        
        abtn.show()
        log.info('Batton Object Added ID:'+str(anid))
        #self.btn.pushButton.clicked.connect(self.btn_click)
        self.DVBui.groupBox_VBD_VarButtons.setAcceptDrops(True)
        abtn.data_change[dict].connect(self.VBD_Button_Clicked)
        abtn.mouseHover[int].connect(self.VBD_Hovered)
        abtn.focused_id[int].connect(self.VBD_Selected)
        self.Edit_Batton_Data(abtn)

    def Edit_Batton_Data(self,Obj):
        self.VBDD_Dialog=VariableButtonDataDialog(Obj)

    def VBD_Set_Position(self,newpos):
        apos,anid=newpos
        for iiiid,Obj in zip(self.VBD_H.Object_Key_List,self.VBD_H.Object_List):
            if iiiid is anid:
                Obj.batton_data.update({'Pos':(apos.x(),apos.y())})            
                print('New pos',Obj.batton_data['Pos'])
                

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
            self.DVBui.pushButton_VBD_ButtonEdit.clicked.connect(self.PB_Edit_Button)
        else:
            self.DVBui.pushButton_VBD_ButtonEdit.clicked.connect(self.PB_debugtests)
        self.DVBui.pushButton_VBD_ButtonAdd.clicked.connect(self.PB_Add_Button)        
        self.DVBui.pushButton_VBD_ButtonRemove.clicked.connect(self.PB_Remove_Button)
        #self.DVBui.pushButton_VBD_Save.clicked.connect(self.PB_Save_Button_Layout)
        #self.DVBui.pushButton_VBD_Load.clicked.connect(self.PB_Load_Button_Layout)
        self.DVBui.buttonBox.accepted.connect(self.accept)
        self.DVBui.buttonBox.rejected.connect(self.reject)

    def PB_Remove_Button(self):
        anid=self.Selected_Item                
        for iiiid,Obj in zip(self.VBD_H.Object_Key_List,self.VBD_H.Object_List):
            if iiiid is anid:
                self.VBD_H.Del_Obj(Obj)  
                log.info('Batton Object Deleted ID:'+str(anid))
                break              
        
                        
    def PB_Edit_Button(self):
        anid=self.Selected_Item                
        for iiiid,Obj in zip(self.VBD_H.Object_Key_List,self.VBD_H.Object_List):
            if iiiid is anid:
                self.Edit_Batton_Data(Obj)
                #print('Edit button pressed')
    
    def Refresh_viewed_filenames(self):        
        fff=self.shorten_filename(self.extract_filename(self.CH.filename,False))
        self.DVBui.groupBox_CCD_actionFiles.setTitle("Actual Config File:"+fff)  
    
    
    '''    
    def Test_text_Changed(self):
        self.Do_Test_Read()
    
    def Test_format_Changed(self):
        self.Do_Test_format()

   
            
    def Refresh_after_config_File_change(self):
        #print('refresh called')
        self.Refresh_Tab_index()
        self.Fill_action_combobox()
        self.Fill_read_combobox()
        self.Fill_GenConfigInt_comboboxes()
        self.Refresh_viewed_filenames()
        self.Set_Config_info_To_TableWidget()

        #self.Fill_interface_combobox()        
    def Refresh_Tab_index(self):
        self.Actual_Page=self.DVBui.tabWidget_CCD_configs.currentIndex()
            

    def Delete_action_in_ConfigFile(self,afilename,anaction,data):        
        isok=self.CH.delete_action_in_file(afilename,anaction,data)
        #print('deleted ',isok)
        if isok==True:
            self.file_has_updated(afilename)
            self.Refresh_after_config_File_change()

    def Create_action_in_ConfigFile(self,afilename,anaction,dorefresh=False):        
        isok=self.CH.create_empty_action_in_file(afilename,anaction)
        if dorefresh==True:
            self.Refresh_after_config_File_change()  
        return isok    
 
    def Add_New_action_in_ConfigFile(self,afilename,anaction,aFormat,anid,data):
        isok=self.Create_action_in_ConfigFile(afilename,anaction,False)
        #print('created ',isok)
        if isok==True:            
            self.Replace_Format_in_ConfigFile(afilename,anaction,aFormat,anid,data)    #Refresh inside

        
    
    def Replace_Format_in_ConfigFile(self,afilename,anaction,aFormat,anid,data):
        #print('replaced before')
        isok=self.CH.replace_action_format_in_file(afilename,anaction,aFormat,anid,data)
        #print('replaced ',isok)
        if isok==True:
            self.file_has_updated(afilename)
            self.Refresh_after_config_File_change()
        return isok

    def PB_CCD_Refresh_Commands_File(self):
        self.Refresh_after_config_File_change()

    def PB_CCD_Save_Commands(self):            
        filename=self.aDialog.saveFileDialog(3)       
        if filename == '' or filename is None:
            return            
        issame1,issn1,issp1=self.compare_filenames_paths(filename,self.CH.filename)         
        issame2,issn2,issp2=self.compare_filenames_paths(filename,self.CH.Readfilename) 
        issame3,issn3,issp3=self.compare_filenames_paths(filename,self.CH.Interfacefilename)         
        if issame1 or issame2 or issame3:            
            log.error("Can't overwrite files in use!")
        if issame3==False and issame2==False and issame1==False:
            desfn=self.extract_filename(filename,False)            
            desfn1=desfn+'.cccfg'
            desfn2=desfn+'.rccfg'
            desfn3=desfn+'.iccfg'
            desp=self.extract_path(filename)
            src_file1=self.CH.filename 
            src_file2=self.CH.Readfilename  
            src_file3=self.CH.Interfacefilename         
            temppath=self.get_appPath()+os.sep+'temp'+os.sep
            try:
                os.mkdir(temppath)
            except:
                pass  
            #print(desfn1)    
            shutil.copy(src_file1,temppath+'tempfile1.temp') #copy the file to destination dir
            os.rename(temppath+'tempfile1.temp', temppath+desfn1)#rename
            shutil.move(temppath+desfn1,desp+desfn1) #moves the file to destination dir                
            #print(desfn2)    
            shutil.copy(src_file2,temppath+'tempfile2.temp') #copy the file to destination dir
            os.rename(temppath+'tempfile2.temp', temppath+desfn2)#rename
            shutil.move(temppath+desfn2,desp+desfn2) #moves the file to destination dir            
            #print(desfn3)    
            shutil.copy(src_file3,temppath+'tempfile3.temp') #copy the file to destination dir
            os.rename(temppath+'tempfile3.temp', temppath+desfn3)#rename
            shutil.move(temppath+desfn3,desp+desfn3) #moves the file to destination dir            
        #print(filename,self.CH.filename,issame)

    def PB_CCD_Load_Commands(self):
        filename=self.aDialog.openFileNameDialog(3)   
        if filename == '' or filename is None:
            return     
        issame1,issn1,issp1=self.compare_filenames_paths(filename,self.CH.filename) 
        issame2,issn2,issp2=self.compare_filenames_paths(filename,self.CH.Readfilename) 
        issame3,issn3,issp3=self.compare_filenames_paths(filename,self.CH.Interfacefilename) 
        if issame1 or issame2 or issame3:            
            log.info('Files already loaded!')
        if issame3==False and issame2==False and issame1==False:
            desconfig=self.extract_filename(filename,False)
            desp=self.extract_path(filename)
            ccname=desp+desconfig+'.cccfg'
            rcname=desp+desconfig+'.rccfg'
            icname=desp+desconfig+'.iccfg'
            isfilecc=os.path.exists(ccname)
            isfilerc=os.path.exists(rcname)
            isfileic=os.path.exists(icname)            
            if isfilecc==True and isfilerc==True and isfileic==True:                
                actualcc=self.CH.filename 
                actualrc=self.CH.Readfilename
                actualic=self.CH.Interfacefilename                
                self.CH.filename = ccname                
                self.CH.Setup_Command_Handler(log_check=True)                
                #print('Loaded')            
                if self.CH.Num_interfaces==0:
                    log.error('Errors in File,'+ccname+'\nReverting to actual Configuration file!')
                    self.CH.filename = actualcc
                    self.CH.Setup_Command_Handler(log_check=True)    
                else:    
                    self.CH.Set_Readfilename(rcname)
                    self.CH.Set_Interfacefilename(icname) 
                    isokrc,isokic=self.CH.Init_Read_Interface_Configurations({'interfaceId'},{'interfaceId'},True)                  
                    if isokrc==False:
                        log.error('Errors in File,'+rcname+'\nReverting to actual Configuration file!')
                    if isokic==False:
                        log.error('Errors in File,'+rcname+'\nReverting to actual Configuration file!')    
                    if isokrc==False or isokic==False:
                        self.CH.Set_Readfilename(actualrc)
                        self.CH.Set_Interfacefilename(actualic) 
                        isokrc,isokic=self.CH.Init_Read_Interface_Configurations({'interfaceId'},{'interfaceId'},True)                  



                #self.Fill_interface_combobox()
                self.Refresh_after_config_File_change()
                
            else:
                log.info('Not all Files present! .cccfg .rccfg and .iccfg shall be in the same path!')    

            

    def shorten_filename(self,filename,maxsize=20):
        apppath=self.get_appPath()
        shortfn=filename
        if apppath in filename:
            shortfn=filename.replace(apppath,'')
        if len(shortfn)>maxsize:
            shortfn=self.extract_filename(filename)
        return shortfn


    def get_appPath(self):
        # determine if application is a script file or frozen exe
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(__file__)
        return application_path    
        
    def get_selfPath(self,config_name):
        application_path=self.get_appPath()
        config_path = os.path.join(application_path, config_name)
        return config_path

    def compare_filenames_paths(self,filename1,filename2):
        fname1 = os.path.basename(filename1)  # returns just the name
        fname2 = os.path.basename(filename2)  # returns just the name
        issamepath=False
        issamename=False
        issame=False
        if fname1==fname2:
            #print(' same names')
            issamename=True
        try:
            fpath1 = os.path.abspath(filename1)  # returns complete path
            fpath2 = os.path.abspath(filename2)  
            if fpath1==fpath2:
                #print(' same paths')
                issamepath=True
        except:
            issamepath=False
            pass
        if issamename==True and issamepath==True:
            issame=True        
        return issame,issamename,issamepath

    def extract_filename(self,filename,withextension=True):
        fn= os.path.basename(filename)  # returns just the name
        fnnoext, fext = os.path.splitext(fn)
        fnnoext=fnnoext.replace(fext,'')
        fn=fnnoext+fext        
        if withextension==True:
            return fn
        else:                
            return  fnnoext #fn.rsplit('.', 1)[0]
    def extract_path(self,filename):
        fn= os.path.basename(filename)  # returns just the name
        fpath = os.path.abspath(filename)
        fpath = fpath.replace(fn,'')
        return fpath


    def Set_Config_info_To_TableWidget(self):
        self.DVBui.tableWidget_CCD.clear()
        #Table_NumCols=self.Num_interfaces+1
        Table_NumCols=4
        self.DVBui.tableWidget_CCD.setColumnCount(Table_NumCols)        
        self.DVBui.tableWidget_CCD.setHorizontalHeaderLabels(["Action", "Format","Info","Type"])
        self.DVBui.tableWidget_CCD.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)    
        iii=0
        tabindex=self.Actual_Page
        if tabindex==0:
            Configset=self.CH.Actual_Interface_Formats
            Configsetinfo=self.CH.Configdata_info
            Configsettype=self.CH.Configdata_type
            Table_NumRows=self.CH.Get_Number_of_Actual_Interface_Formats(0)
            Reqset=self.CH.Required_actions
        if tabindex==1:
            Configset=self.CH.Read_Config
            Configsetinfo=self.CH.ReadConfigallids_info
            Configsettype=self.CH.ReadConfigallids_type
            Table_NumRows=self.CH.Get_Number_of_Actual_Interface_Formats(1)
            Reqset=self.CH.Required_read    
        if tabindex==2:
            Configset=self.CH.Int_Config
            Configsetinfo=self.CH.InterfaceConfigallids_info
            Configsettype=self.CH.InterfaceConfigallids_type
            Table_NumRows=self.CH.Get_Number_of_Actual_Interface_Formats(2)
            Reqset=self.CH.Required_interface    

        self.DVBui.tableWidget_CCD.setRowCount(Table_NumRows)
        #print(Configsetinfo)
        for ccc in Configset:   
            self.DVBui.tableWidget_CCD.setItem(iii,0, QTableWidgetItem(ccc))
            self.DVBui.tableWidget_CCD.setItem(iii,1, QTableWidgetItem(Configset[ccc]))
            try:
                ainfo=self.CH.get_info_type_from_id(Configsetinfo,ccc,self.CH.id)                 
                #print(ccc,'-->',ainfo)
                self.DVBui.tableWidget_CCD.setItem(iii,2, QTableWidgetItem(ainfo))
            except: # Exception as e:
                #log.error(e) 
                self.DVBui.tableWidget_CCD.setItem(iii,2, QTableWidgetItem(''))
                pass    
            try:
                atype=self.CH.get_info_type_from_id(Configsettype,ccc,self.CH.id)
                self.DVBui.tableWidget_CCD.setItem(iii,3, QTableWidgetItem(atype))
            except:
                self.DVBui.tableWidget_CCD.setItem(iii,3, QTableWidgetItem(''))
                pass    
            if ccc in Reqset:
                color=QColor('yellow')
                self.setColortoRow(self.DVBui.tableWidget_CCD, iii, color)                
            iii=iii+1
        self.DVBui.tableWidget_CCD.resizeColumnsToContents()            
    
    def setColortoRow(self,table, rowIndex, color):
        for jjj in range(table.columnCount()):
            table.item(rowIndex, jjj).setBackground(color)

    def Fill_interface_combobox(self):        
        self.DVBui.comboBox_CCD_interface.clear()
        for iii in self.CH.Configdata['interfaceId']:           
            self.DVBui.comboBox_CCD_interface.addItem(iii)                          
        index= self.DVBui.comboBox_CCD_interface.findText(self.CH.id,QtCore.Qt.MatchFixedString)
        self.DVBui.comboBox_CCD_interface.setCurrentIndex(index)    
        aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.CH.id)
        self.DVBui.label_CCD_interfaceName.setText(aname)    
    
    def Fill_action_combobox(self):
        self.DVBui.comboBox_CCD_action.clear()
        allactions=self.CH.getListofActions(['interfaceId','interfaceId_type','interfaceId_info'])
        self.DVBui.comboBox_CCD_action.addItem('')
        for iii in allactions:           
            self.DVBui.comboBox_CCD_action.addItem(iii)          
        #index= self.DVBui.comboBox_CCD_action.findText('interfaceName',QtCore.Qt.MatchFixedString)
        index=0
        self.DVBui.comboBox_CCD_action.setCurrentIndex(index)    
        self.CH.Selected_action=self.DVBui.comboBox_CCD_action.currentText()

    def Fill_read_combobox(self):
        self.DVBui.comboBox_CCD_readaction.clear()
        allactions=self.CH.getListofReadactions(['interfaceId','interfaceId_type','interfaceId_info'])
        self.DVBui.comboBox_CCD_readaction.addItem('')
        for iii in allactions:           
            self.DVBui.comboBox_CCD_readaction.addItem(iii)          
        #index= self.DVBui.comboBox_CCD_readaction.findText('interfaceName',QtCore.Qt.MatchFixedString)
        index=0
        self.DVBui.comboBox_CCD_readaction.setCurrentIndex(index)    
        self.Selected_read_dict.update({'action':self.DVBui.comboBox_CCD_readaction.currentText()})

    def Fill_GenConfigInt_comboboxes(self):
        self.Fill_GenConfigInt_combobox()
        self.Fill_GenConfigInttype_combobox()

    def Fill_GenConfigInt_combobox(self):
        self.DVBui.comboBox_CCD_Intaction.clear()
        allactions=self.CH.getListofInterfaceactions(['interfaceId','interfaceId_type','interfaceId_info'])
        self.DVBui.comboBox_CCD_Intaction.addItem('')
        for iii in allactions:           
            self.DVBui.comboBox_CCD_Intaction.addItem(iii)                  
        index=0
        self.DVBui.comboBox_CCD_Intaction.setCurrentIndex(index)    
        self.Selected_Int_dict.update({'action':self.DVBui.comboBox_CCD_Intaction.currentText()})    
    
    def Fill_GenConfigInttype_combobox(self):
        self.typelist=['','str','float','int','bool','char','list','dict','regex','byte','char','action']
        self.DVBui.comboBox_CCD_Inttype.clear()
        for iii in self.typelist:           
            self.DVBui.comboBox_CCD_Inttype.addItem(iii)                  
        index=0
        self.DVBui.comboBox_CCD_Inttype.setCurrentIndex(index)  
        #self.Selected_Int_dict.update({'type':self.DVBui.comboBox_CCD_Inttype.currentText()})  
        


    def ComboBox_Select_action(self):
        self.Selected_action=self.DVBui.comboBox_CCD_action.currentText()         
        self.DVBui.lineEdit_CCD_action.setText(self.Selected_action)     
        aFormat=self.CH.getGformatforActionid(self.Selected_action,self.id)
        #self.DVBui.lineEdit_CCD_action.setText(self.Selected_action)     
        self.DVBui.lineEdit_CCD_Format.setText(aFormat) 
        self.fill_actionParameters_Table(aFormat)
    
    def ComboBox_Select_Readaction(self):
        self.Selected_Readaction=self.DVBui.comboBox_CCD_readaction.currentText()         
        self.DVBui.lineEdit_CCD_readaction.setText(self.Selected_Readaction)     
        aFormat=self.CH.getGformatforReadactionid(self.Selected_Readaction,self.id)
        #self.DVBui.lineEdit_CCD_readaction.setText(self.Selected_Readaction)     
        self.DVBui.lineEdit_CCD_readFormat.setText(aFormat) 
        self.fill_ReadactionParameters_Table(aFormat)

    def ComboBox_Select_Intaction(self):
        self.Selected_Intaction=self.DVBui.comboBox_CCD_Intaction.currentText()         
        self.DVBui.lineEdit_CCD_Intaction.setText(self.Selected_Intaction)     
        aFormat=self.CH.getGformatforIntactionid(self.Selected_Intaction,self.id)
        atype=self.CH.getGformatforActiondataid(self.CH.InterfaceConfigallids_type,self.Selected_Intaction,self.id)
        #self.DVBui.lineEdit_CCD_readaction.setText(self.Selected_Readaction)     
        self.DVBui.lineEdit_CCD_IntFormat.setText(aFormat) 
        self.set_combobox_Genint_type(atype)
        

    def ComboBox_Select_Inttype(self):
        self.Selected_Intaction=self.DVBui.comboBox_CCD_Intaction.currentText() 
        combotype=self.DVBui.comboBox_CCD_Inttype.currentText()
        #atype=self.CH.getGformatforActiondataid(self.CH.InterfaceConfigallids_type,self.Selected_Intaction,self.id)
        reqtypelist,isreq=self.get_list_Genint_required_types(self.Selected_Intaction)
        numitems= len(reqtypelist)
        if numitems>0:
            isok=False
            #check is one of the required types
            for reqtype in reqtypelist:
                if combotype==reqtype:
                    isok=True
                    break
        else:
            isok=True
        
        if isok == True:
            atype=combotype
        #elif isok == False and isreq==False:
        #    atype=atype
        else:
            atype=reqtypelist[0]    
        self.set_combobox_Genint_type(atype)   
         

    def get_list_Genint_required_types(self,action):
        iactionslist=self.CH.getListofInterfaceactions()
        basesia=action
        basesia=basesia.replace('_type','')
        isreq=False
        reqtypelist=[]
        if basesia in iactionslist:
            for reqia in self.CH.Required_interface:
                if basesia==reqia :
                    isreq=True 
                    try:
                        reqtypelist=self.CH.Required_interface[requia]
                    except:
                        pass
                    break
        return reqtypelist,isreq

    def set_combobox_Genint_type(self,atype):        
        index=0
        index=self.DVBui.comboBox_CCD_Inttype.findText(atype,QtCore.Qt.MatchFixedString)    
        if index==-1:
            self.DVBui.comboBox_CCD_Inttype.addItem(atype)
            index=self.DVBui.comboBox_CCD_Inttype.findText(atype,QtCore.Qt.MatchFixedString)    
        self.DVBui.comboBox_CCD_Inttype.setCurrentIndex(index) 
        self.Selected_Int_dict.update({'Type':atype})
        #print('Type to ',atype)
    
    def Do_Test_Int(self):
        aFormat=self.DVBui.lineEdit_CCD_IntFormat.text()   
        action=self.DVBui.lineEdit_CCD_Intaction.text()
        isok=False
        if action!=self.Selected_Int_dict['action']:
            self.Selected_Int_dict['action']=action
        reqtypelist,isreq=self.get_list_Genint_required_types(action)   
        
        atype=self.DVBui.comboBox_CCD_Inttype.currentText()       
        if atype not in reqtypelist and len(reqtypelist)>0 and isreq==True:
            atype=reqtypelist[0]
        isok,val=self.check_Genint_format_type(aFormat,atype)    
        if atype != self.Selected_Int_dict['Type']:                  
            self.Selected_Int_dict.update({'Type':atype})      
        if val is None:
            return isok      
        if aFormat != self.Selected_Int_dict['Format']:             
            if isok==True:
                self.Selected_Int_dict.update({'Format':aFormat})            
        return isok  

    def check_Genint_format_type(self,aFormat,atype,showlog=True):
        isok=False
        if atype=='':
            val=aFormat
            isok=True
        elif atype=='bool':
            try:
                aFormat=str(aFormat)
                if aFormat.lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly']:                
                    val=True
                    isok=True
                elif aFormat.lower() in ['false', '0', 'f', 'n', 'no', 'naah', 'not', 'maybe']:
                    val=False
                    isok=True
                else:
                    val=None                       
                    isok=False
            except Exception as e:
                if showlog==True:
                    log.error(e)     
                val=None   
                isok=False                
                pass        
        elif atype=='list':   
            try:         
                aFormat=str(aFormat)                                
                txtlist,Num=self.CH.Split_text(',',aFormat)
                if Num>0:
                    val=txtlist
                    isok=True
                elif Num==0 and aFormat!='':
                    val=[aFormat]
                    isok=True
                else:
                    val=[]
                    isok=False
            except Exception as e:
                if showlog==True:
                    log.error(e)     
                val=None 
                isok=False                   
                pass  
        elif atype=='dict':   
            try:         
                aFormat=str(aFormat)                                
                txtlist,Num=self.CH.Split_text(',',aFormat)                
                val={}
                if Num>0:
                    for item in txtlist:
                        varpar,Numvp=self.CH.Split_text(':',item)                
                        if Numvp==0 or Numvp==1:
                            val.update({item:''})
                        if Numvp==2:
                            val.update({varpar(0):varpar(1)})    
                        else:
                            isok=False                            
                            break
                if Num==0:                    
                    varpar,Numvp=self.CH.Split_text(':',aFormat)                
                    if Numvp==0 or Numvp==1:
                        val.update({aFormat:''})
                    if Numvp==2:
                        val.update({varpar(0):varpar(1)})    
                    else:
                        isok=False                                                    
            except Exception as e:
                if showlog==True:
                    log.error(e)     
                val=None 
                isok=False                   
                pass                                              
        elif atype=='str' or atype=='string':
            try:
                val=str(aFormat)
                isok=True
            except Exception as e:
                if showlog==True:
                    log.error(e)     
                val=None 
                isok=False                   
                pass                    
        elif atype=='int':
            try:
                val=int(aFormat)
                isok=True    
            except Exception as e:
                if showlog==True:
                    log.error(e)     
                val=None
                isok=False    
                pass
        elif atype=='float':
            try:
                val=float(aFormat)
                isok=True    
            except Exception as e:
                if showlog==True:
                    log.error(e)     
                val=None
                isok=False    
                pass    
        elif atype=='byte':
            try:
                val=bytes(aFormat.encode())
                isok=True    
            except Exception as e:
                if showlog==True:
                    log.error(e)     
                val=None
                isok=False    
                pass    
        elif atype=='char':
            try:
                val=chr(int(aFormat))
                isok=True    
            except Exception as e:
                if showlog==True:
                    log.error(e)     
                val=None
                isok=False    
                pass     
        elif atype=='action':
            isok,val=self.Test_a_format(aFormat)
            if isok==True:
                val=self.CH.Format_replace_actions(aFormat)
        elif atype=='read' or atype=='regex':
            isok,val=self.Test_a_read(aFormat)    
        else:
            isok=True
            val=aFormat    
        if showlog==True:
            if isok == False:
                msgtxt="Bad format of type "+atype
                log.error(msgtxt)
                self.DVBui.label_CCD_testIntResultFormat.setText(msgtxt)
            else:
                try:
                    msgtxt="Format of type "+atype+" accepted: " + str(val)
                except:
                    msgtxt="Format of type "+atype+" accepted"
                    pass
                log.info(msgtxt)
                self.DVBui.label_CCD_testIntResultFormat.setText(msgtxt)    
        return isok,val    
    
    def Test_a_read(self,aFormat):
        befaFormat=self.DVBui.lineEdit_CCD_readFormat.text()   
        befaction=self.DVBui.lineEdit_CCD_readaction.text()
        self.DVBui.lineEdit_CCD_readFormat.setText(aFormat)   
        self.DVBui.DVBui.lineEdit_CCD_readaction.setText('__Test__')
        isok=self.Do_Test_Read()
        if isok==False:
            val=None  
        else:
            val= self.Selected_read_dict['Format']    
        self.DVBui.lineEdit_CCD_readFormat.setText(befaFormat)   
        self.DVBui.DVBui.lineEdit_CCD_readaction.setText(befaction)

    def Test_a_format(self,aFormat):
        befaFormat=self.DVBui.lineEdit_CCD_Format.text()   
        befaction=self.DVBui.lineEdit_CCD_action.text()
        self.DVBui.lineEdit_CCD_Format.setText(aFormat)   
        self.DVBui.lineEdit_CCD_action.setText('__Test__')
        isok=self.Do_Test_format()
        if isok==False:
            val=None  
        else:
            val= self.Selected_action_dict['Format']    
        self.DVBui.lineEdit_CCD_Format.setText(befaFormat)   
        self.DVBui.lineEdit_CCD_action.setText(befaction)
        return isok,val

    def Do_Test_Read(self): 
        #print("entered Read")       
        aFormat=self.DVBui.lineEdit_CCD_readFormat.text()   
        action=self.DVBui.lineEdit_CCD_readaction.text()
        isok=False
        if action!=self.Selected_read_dict['action']:
            self.Selected_read_dict['action']=action
        isok=self.fill_ReadactionParameters_Table(aFormat)    
        if aFormat != self.Selected_read_dict['Format']:             
            if isok==True:
                self.Selected_read_dict.update({'Format':aFormat})                
        return isok  

    def Do_Test_format(self):
        aFormat=self.DVBui.lineEdit_CCD_Format.text()   
        action=self.DVBui.lineEdit_CCD_action.text()
        if action!=self.Selected_action_dict['action']:
            self.Selected_action_dict['action']=action
        if aFormat != self.Selected_action_dict['Format']:      
            isok=self.fill_actionParameters_Table(aFormat) 
            if isok==True:
                self.Selected_action_dict.update({'Format':aFormat})        
        else:
            numrowTable=self.DVBui.tableWidget_CCD_actionParam.rowCount()
            ReqOpParamsdict=self.Selected_action_dict['ReqOpParamsdict']
            numReqopparams=len(ReqOpParamsdict)
            if numrowTable!=numReqopparams:
                isok=self.fill_actionParameters_Table(aFormat)
                return isok
            newParameters=self.Replace_Parameter_Values_from_Table(self.Selected_action_dict['Parameters'])  
            isok=self.CH.Check_Format(aFormat,newParameters)  
            if isok==True:
                Gcode=self.CH.Get_code(aFormat,newParameters)
            #if aFormat is not '' and Gcode is '':
            else:
                Gcode='Missing Required Parameters or bad Format'
            self.DVBui.label_CCD_testResult.setText("Evaluated Gcode: "+str(Gcode))
            self.Selected_action_dict.update({'Format':aFormat})
            self.Selected_action_dict.update({'action':action})
        return isok    
    
    def Replace_Parameter_Values_from_Table(self,Parameters):    
        newparam={}    
        try:
            for row in range(len(Parameters)):                                   
                Tpar=self.DVBui.tableWidget_CCD_actionParam.item(row, 0).text()             
                Tvalue=self.DVBui.tableWidget_CCD_actionParam.item(row, 1).text()            
                for param in Parameters:
                    if param == Tpar and Tvalue is not '':
                        newparam.update({param:Tvalue})
                        break
        except:
            newparam={}
            pass            
        return newparam        

    def fill_actionParameters_Table(self,aFormat):
        isok=False
        self.DVBui.tableWidget_CCD_actionParam.clear()
        Table_NumCols=3
        self.DVBui.tableWidget_CCD_actionParam.setColumnCount(Table_NumCols)
        Table_NumRows=0
        self.DVBui.tableWidget_CCD_actionParam.setRowCount(Table_NumRows)
        self.DVBui.label_CCD_testResult.setText("Evaluated Gcode: ")
        self.DVBui.label_CCD_testResultFormat.setText("Processed Format: ")  
        #Table_NumCols=self.Num_interfaces+1
        if self.CH.Check_Format(aFormat)==False:
            self.DVBui.label_CCD_testResult.setText("Wrong Parenthesis")
            return isok
        try:    
            P_Allinfo=self.CH.get_all_info_from_Format(aFormat)
        except:
            P_Allinfo={}
            self.DVBui.label_CCD_testResult.setText("Format contains Errors")
            pass
        if P_Allinfo is not {}:            
            if P_Allinfo['IsRegex']==True:
                self.DVBui.label_CCD_testResult.setText("Format contains regex read Code")
                return isok
            isok=True    
            ReqOpParamsdict=P_Allinfo['ReqOpParamsdict']
            paramlist=P_Allinfo['Parameterlist']
            optionlist=P_Allinfo['Optionlist']
            optiontxtlist=P_Allinfo['Optiontxtlist']
            minop=P_Allinfo['minRequiredOptions']
            self.DVBui.label_CCD_testResultFormat.setText("Processed Format: "+str(P_Allinfo['processedFormat']))                            
            Table_NumRows=len(ReqOpParamsdict)
            self.DVBui.tableWidget_CCD_actionParam.setRowCount(Table_NumRows)
            self.DVBui.tableWidget_CCD_actionParam.setHorizontalHeaderLabels(["Parameter", "Value","Constraint"])
            self.DVBui.tableWidget_CCD_actionParam.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)    
            iii=0
            befaconstraint=''
            if P_Allinfo['IsOred']==True:
                befaconstraint=befaconstraint+'OR '
            
            aconstraint=befaconstraint  
            Parameters={}  
            for ccc in ReqOpParamsdict:   
                self.DVBui.tableWidget_CCD_actionParam.setItem(iii,0, QTableWidgetItem(ccc))
                self.DVBui.tableWidget_CCD_actionParam.setItem(iii,1, QTableWidgetItem(str(iii)))
                Parameters.update({ccc:iii})
            
                self.DVBui.tableWidget_CCD_actionParam.setItem(iii,2, QTableWidgetItem(befaconstraint+ReqOpParamsdict[ccc]))
                if ReqOpParamsdict[ccc]=='required':
                    color=QColor('lightblue')
                    self.setColortoRow(self.DVBui.tableWidget_CCD_actionParam, iii, color)                
                iii=iii+1
            self.DVBui.tableWidget_CCD_actionParam.resizeColumnsToContents()
            Gcode=self.CH.Get_code(aFormat,Parameters)
            self.DVBui.label_CCD_testResult.setText("Evaluated Gcode: "+str(Gcode))
            self.Selected_action_dict={'action':self.DVBui.lineEdit_CCD_action.text(),'Format':aFormat,'Parameters':Parameters,'ReqOpParamsdict':ReqOpParamsdict}

        return isok    
    
    def fill_ReadactionParameters_Table(self,aFormat):
        isok=False
        self.DVBui.tableWidget_CCD_readactionParam.clear()
        Table_NumCols=4
        self.DVBui.tableWidget_CCD_readactionParam.setColumnCount(Table_NumCols)
        Table_NumRows=0
        self.DVBui.tableWidget_CCD_readactionParam.setRowCount(Table_NumRows)
        self.DVBui.label_CCD_testreadResult.setText("Evaluated all Read: ")
        self.DVBui.label_CCD_testreadResultFormat.setText("Evaluated Format read: ")  
        #Table_NumCols=self.Num_interfaces+1
        if self.CH.Check_Format(aFormat)==False:
            self.DVBui.label_CCD_testreadResult.setText("Wrong Parenthesis")
            return isok
        #print('pass check format')    
        try:    
            P_Allinfo=self.CH.get_all_info_from_Format(aFormat)
            #print('pass get all info from format')   
            #print(P_Allinfo) 
        except:
            P_Allinfo={}
            self.DVBui.label_CCD_testreadResult.setText("Format contains Errors")
            pass
        if P_Allinfo is not {}:                        
            if P_Allinfo['IsRegex']==False or P_Allinfo['IsOred']==True:
                self.DVBui.label_CCD_testreadResult.setText("Format contains action Code")
                return isok
            #print('pass check or and regex')    
            isok=True    
            ReqOpParamsdict=P_Allinfo['ReqOpParamsdict']
            paramlist=P_Allinfo['Parameterlist']
            optionlist=P_Allinfo['Optionlist']
            optiontxtlist=P_Allinfo['Optiontxtlist']
            minop=P_Allinfo['minRequiredOptions']
            regexcmd=P_Allinfo['RegexCommand']
            self.DVBui.label_CCD_testreadResultFormat.setText("Search pattern: "+regexcmd)                            
            
            iii=0                        
            Parameters={}  
            texteval=self.DVBui.lineEdit_CCD_testRead_text.text()
            #print(texteval)
            
            try:
                rm=re.search(regexcmd,texteval)
                nummatch=len(rm.groups())
                #print(nummatch)
                if nummatch==0:
                    self.DVBui.label_CCD_testreadResult.setText("No matches found!")
                if nummatch>0:
                    #log.info('Test found '+str(nummatch)+' match(es)')
                    self.DVBui.label_CCD_testreadResult.setText('Test found '+str(nummatch)+' match(es)!')
                    Table_NumRows=nummatch
                    self.DVBui.tableWidget_CCD_readactionParam.setRowCount(Table_NumRows)
                    self.DVBui.tableWidget_CCD_readactionParam.setHorizontalHeaderLabels(["Match", "Parameter","Value","Option"])
                    self.DVBui.tableWidget_CCD_readactionParam.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)    
                    #print(optiontxtlist)
                    #print(optionlist)
                    #print(paramlist)
                    for iii in range(nummatch):   
                        optxt=''
                        oppos=0
                        op=''
                        ptxt=''
                        for ccc in optiontxtlist:                            
                            if str(ccc)==str(iii+1):
                                optxt=str(ccc)
                                op=optionlist[oppos]
                                ptxt=paramlist[oppos]
                                break
                            oppos=oppos+1
                        readvalue=rm.group(iii+1)    
                        self.DVBui.tableWidget_CCD_readactionParam.setItem(iii,0, QTableWidgetItem(optxt))
                        self.DVBui.tableWidget_CCD_readactionParam.setItem(iii,1, QTableWidgetItem(ptxt))
                        self.DVBui.tableWidget_CCD_readactionParam.setItem(iii,2, QTableWidgetItem(str(readvalue)))
                        self.DVBui.tableWidget_CCD_readactionParam.setItem(iii,3, QTableWidgetItem(op))
                        Parameters.update({op:readvalue})                    
                        
                    self.DVBui.tableWidget_CCD_readactionParam.resizeColumnsToContents()
            except Exception as e:
                #log.error(e) 
                #log.info('Test found no matches!')
                self.DVBui.label_CCD_testreadResult.setText("No matches found!")
                pass

            self.Selected_read_dict.update({'action':self.DVBui.lineEdit_CCD_readaction.text()})
            self.Selected_read_dict.update({'Format':aFormat})
            self.Selected_read_dict.update({'Parameters':Parameters})
            self.Selected_read_dict.update({'testRead':self.DVBui.label_CCD_testreadResult.text()})
        return isok    


    def ComboBox_Select_interface(self):
        anid=self.DVBui.comboBox_CCD_interface.currentText()
        if str(anid)!=str(self.CH.id):            
            self.CH.Set_id(str(anid))
            aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.CH.id)
            self.DVBui.label_CCD_interfaceName.setText(aname)  
            self.Force_CH_refresh_info_From_file(False)            
            self.id=self.CH.id  
            self.Refresh_after_config_File_change()
    
    def Force_CH_refresh_info_From_file(self,log):
        self.CH.Setup_Command_Handler(log)   #Refresh info in CH 
        self.CH.Init_Read_Interface_Configurations(self.CH.Required_read,self.CH.Required_interface,log) 
    
    def PB_CCD_Set_Preview(self):            
        #print('clicked')
        self.aList=[]
        self.set_clicked.emit(self.aList)
    
    

    def getGformatforActionfromTable(self,action):
        ActionFormat=None
        try:       
            Table_NumRows=self.Get_Number_of_Actual_Interface_Formats()
            for row in range(Table_NumRows):                        
                hhh=self.DVBui.tableWidget_CCD.item(row, 0).text()
                hhhval=self.DVBui.tableWidget_CCD.item(row, 1).text()     
                if hhh==action:            
                    ActionFormat=hhhval
        except:
            pass
        #print('get from table '+ActionFormat)
        return ActionFormat

    def accept(self):
        #print('accepted')        
        return self.CH.id   
    '''
    def PB_debugtests(self):
        
        print('--------------------------------------------------')
        #Gcodeline='G0 X0.5 Y0.8 Z3'
        #print(self.CH.get_action_from_gcode(Gcodeline,2))
        Gcodeline='G1 X0.5 Z3 Y0.8 F100'
        print(self.CH.get_action_from_gcode(Gcodeline,2))
        #Gcodeline='G0 X0.5 Z0.8 Y3'
        #print(self.CH.get_action_from_gcode(Gcodeline))
        #Gcodeline='G0 Z8'
        #print(self.CH.get_action_from_gcode(Gcodeline))
        #Gcodeline='G92 X0.5'
        #print(self.CH.get_action_from_gcode(Gcodeline))
        #Gcodeline='G1 X0.5 E0.8 Z3 F200'
        #print(self.CH.get_action_from_gcode(Gcodeline,2))
        Gcodeline='G1 G0 X0.5 Y0.8 Z3 F200'
        print(self.CH.get_action_from_gcode(Gcodeline,2))
        Gcodeline='G28 Z'
        print(self.CH.get_action_from_gcode(Gcodeline,2))
        #Gcodeline='G54 G0 X0.5 Y0.8 Z3'
        #print(self.CH.get_action_from_gcode(Gcodeline,1))
    '''
    def left_click_P(self, nb):
        if nb == 1: print('Single left click')
        else: print('Double left click')

    def right_click_P(self, nb):
        if nb == 1: print('Single right click')
        else: print('Double right click')
    '''    


def main():
    anid='0'
    app = QtWidgets.QApplication(sys.argv)
    VBD_test=VariableButtonDialog(anid)                
    sys.exit(app.exec_())   

if __name__ == '__main__':
    main()
