from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
import re
import logging
import GuiXYZ_CCD
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

class CommandConfigurationDialog(QWidget,GuiXYZ_CCD.Ui_Dialog_CCD):
    set_clicked= QtCore.pyqtSignal(list)
    file_update= QtCore.pyqtSignal(str)
    change_interface_id= QtCore.pyqtSignal(str)
    
    #def __init__(self,NumLayers,Selected_Layers,parent=None):    
    #    super().__init__(parent)
    def __init__(self,selected_interface_id, *args, **kwargs):                
        super(CommandConfigurationDialog, self).__init__(*args, **kwargs)  
        self.__name__="CCD"
        self.aDialog=class_File_Dialogs.Dialogs()     
        self.id=selected_interface_id #equivalent to is_tinyg
        self.Is_Dialog_Open=False   
        self.Actual_Tab=0
        self.Setup_Command_Config()
        self.Activate_test_button=False
        #self.openCommandConfigDialog()   #comment this line to be called only when you want the dialog    
    
    def Setup_Command_Config(self):
        self.CH=class_CH.Command_Handler(self.id)
        self.Set_Required_actions_to_CH(None,None,None)
        self.id=self.CH.id          
        self.Selected_action=None
        self.Num_interfaces=self.CH.Num_interfaces
        self.Selected_action_dict={'action':'','Format':'','Parameters':{},'ReqOpParamsdict':{}}
        self.Selected_read_dict={'action':'','Format':'','Parameters':{},'AlltestRead':{},'testRead':''}
        self.Selected_Int_dict={'action':'','Format':'','Type':''}

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

          

    def quit(self):
        self.Dialog_CCD.close()
        self.Is_Dialog_Open=False
           
    def openCommandConfigDialog(self):
        self.Dialog_CCD = QtWidgets.QDialog()
        self.DCCui = GuiXYZ_CCD.Ui_Dialog_CCD()
        self.DCCui.setupUi(self.Dialog_CCD)        
        self.Dialog_CCD.show()    
        self.Is_Dialog_Open=True    
        self.Fill_interface_combobox()
        self.Refresh_after_config_File_change()
        
        #Connect buttons
        if self.Activate_test_button==False:
            self.DCCui.pushButton_CCD_Refresh_Commands_File.clicked.connect(self.PB_CCD_Refresh_Commands_File)
        else:
            self.DCCui.pushButton_CCD_Refresh_Commands_File.clicked.connect(self.PB_debugtests)
        self.DCCui.pushButton_CCD_Save_Commands.clicked.connect(self.PB_CCD_Save_Commands)
        self.DCCui.pushButton_CCD_Load_Commands.clicked.connect(self.PB_CCD_Load_Commands)
        self.DCCui.pushButton_CCD_actionTest.clicked.connect(self.PB_CCD_actionTest)
        self.DCCui.pushButton_CCD_readactionTest.clicked.connect(self.PB_CCD_readactionTest)
        self.DCCui.pushButton_CCD_actionAdd.clicked.connect(self.PB_CCD_actionAdd)
        self.DCCui.pushButton_CCD_actionDel.clicked.connect(self.PB_CCD_actionDel)        
        self.DCCui.pushButton_CCD_readactionAdd.clicked.connect(self.PB_CCD_readactionAdd)
        self.DCCui.pushButton_CCD_readactionDel.clicked.connect(self.PB_CCD_readactionDel)
        self.DCCui.pushButton_CCD_AddInterface.clicked.connect(self.PB_Add_Interface)
        self.DCCui.pushButton_CCD_DelInterface.clicked.connect(self.PB_Del_Interface)
        self.DCCui.pushButton_CCD_IntactionAdd.clicked.connect(self.PB_CCD_IntactionAdd)
        self.DCCui.pushButton_CCD_IntactionDel.clicked.connect(self.PB_CCD_IntactionDel)
        self.DCCui.pushButton_CCD_IntactionTest.clicked.connect(self.PB_CCD_IntactionTest)

        self.DCCui.tabWidget_CCD_configs.currentChanged.connect(self.TW_Tab_Change)
        # activated-When user changes it
        # currentIndexChanged -> when user or program changes it
        self.DCCui.comboBox_CCD_interface.activated.connect(self.ComboBox_Select_interface)
        self.DCCui.comboBox_CCD_action.currentIndexChanged.connect(self.ComboBox_Select_action)
        self.DCCui.comboBox_CCD_readaction.currentIndexChanged.connect(self.ComboBox_Select_Readaction)  
        self.DCCui.comboBox_CCD_Intaction.currentIndexChanged.connect(self.ComboBox_Select_Intaction)
        self.DCCui.comboBox_CCD_Inttype.currentIndexChanged.connect(self.ComboBox_Select_Inttype)
        
        #textEdited->only when user changes, not by the program
        #textChanged-> when user changes or the program changes text
        self.DCCui.lineEdit_CCD_testRead_text.textEdited.connect(self.Test_text_Changed) 
        self.DCCui.lineEdit_CCD_readFormat.textChanged.connect(self.Test_text_Changed)
        self.DCCui.lineEdit_CCD_Format.textChanged.connect(self.Test_format_Changed)
        
        
        #self.DCCui.label_CCD_testResultFormat.left_clicked[int].connect(self.left_click_P)
        #self.DCCui.label_CCD_testResultFormat.right_clicked[int].connect(self.right_click_P)
        self.DCCui.pushButton_CCD_Force_Interface.clicked.connect(self.Force_Interface)

    def Force_Interface(self):            
        aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.CH.id)
        msgbox = QtWidgets.QMessageBox()
        msgbox.setWindowTitle('Force Interface ...')
        msgbox.setIcon(QtWidgets.QMessageBox.Question)
        msgbox.setText("Would you like to force program to use "+aname+" interface?")        
        msgbox.addButton(QtWidgets.QPushButton('Yes'), QtWidgets.QMessageBox.YesRole)
        msgbox.addButton(QtWidgets.QPushButton('No'), QtWidgets.QMessageBox.NoRole)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.No)
        
        result = msgbox.exec_()
        #print(result)
        if result == 0: #QtWidgets.QMessageBox.AcceptRole:                                 
            self.change_interface_id.emit(self.CH.id)
        

    def Test_text_Changed(self):
        self.Do_Test_Read()
    
    def Test_format_Changed(self):
        self.Do_Test_format()

    def TW_Tab_Change(self,tabindex):
        #QtWidgets.QMessageBox.information(self,"Tab Index Changed!","Current Tab Index: %d" % tabindex )
        self.Actual_Tab=tabindex        
        self.Set_Config_info_To_TableWidget()
            

    def PB_CCD_actionDel(self):
        action=self.DCCui.lineEdit_CCD_action.text()
        if action == '':
            msgtxt="No action to Delete!"
            log.error(msgtxt)
            self.DCCui.label_CCD_testResult.setText(msgtxt)
            return
        if action == 'interfaceId' or 'interfaceId' in action:
            msgtxt=="Can't change this action"
            log.error(msgtxt)
            self.DCCui.label_CCD_testResult.setText(msgtxt)
            return
        allactions=self.CH.getListofActions(['interfaceId'])
        knownaction=False
        delonlyFormat=False
        if action in allactions:                
            knownaction=True
        #check if other ids are empty    
        if  knownaction==True:           
            formatlist=self.CH.Configdata[action]
            idlist=self.CH.Configdata['interfaceId']
            for jjj in range(len(formatlist)):
                if formatlist[jjj] != '' and  idlist[jjj]!= self.id:
                    msgtxt="Can't delete this action. Formats in other ids!"
                    log.error(msgtxt)
                    self.DCCui.label_CCD_testResult.setText(msgtxt)
                    delonlyFormat=True
                    break       
        #check if is required action     
        if knownaction==True and delonlyFormat==False:
            reqactions=self.CH.Required_actions
            for reqa in reqactions:
                if action is reqa:
                    msgtxt="Can't delete this action, is a Required action!"
                    log.error(msgtxt)
                    self.DCCui.label_CCD_testResult.setText(msgtxt)                    
                    delonlyFormat=True
                    break
        #delete only the format        
        if knownaction==True and delonlyFormat==True:
            oldFormat=self.CH.Get_action_format_from_id(self.CH.Configdata,action,self.id)                    
            result = QtWidgets.QMessageBox.question(self,
                    "Confirm Format delete...",
                    "Old Format: "+str(oldFormat)+"\n"+
                    "Are you sure you want to delete the Format?",
                    QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.Yes:
                self.Replace_Format_in_ConfigFile(self.CH.filename,action,'',self.id,self.CH.Configdata) 
                msgtxt=msgtxt="action:  "+action+" Format cleared!"
                log.info(msgtxt)
                self.DCCui.label_CCD_testResult.setText(msgtxt)   
        #delete the action       
        if knownaction==True and delonlyFormat==False:             
            result = QtWidgets.QMessageBox.question(self,
                    "Confirm action, info and type delete...",
                    "You are about to permanently delete action: "+action+"\n"                    
                    "Are you sure you want to delete the action?",
                    QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.Yes:
                #first info and type
                self.Delete_action_in_ConfigFile(self.CH.filename,action+'_info',self.CH.Configdata_info) 
                self.Delete_action_in_ConfigFile(self.CH.filename,action+'_type',self.CH.Configdata_type) 
                self.Delete_action_in_ConfigFile(self.CH.filename,action,self.CH.Configdata)                 
                msgtxt=action+" Deleted!"
                log.info(msgtxt)
                self.DCCui.label_CCD_testResult.setText(msgtxt)   
    
    def PB_CCD_IntactionDel(self):
        action=self.DCCui.lineEdit_CCD_Intaction.text()
        if action == '':
            msgtxt="No action to Delete!"
            log.error(msgtxt)
            self.DCCui.label_CCD_testIntResult.setText(msgtxt)
            return
        if action == 'interfaceId' or 'interfaceId' in action:
            msgtxt=="Can't change this action"
            log.error(msgtxt)
            self.DCCui.label_CCD_testIntResult.setText(msgtxt)
            return
        if '_type' in action:    
            msgtxt=="Can't delete types of an Interface action. Use + to replace them."
            log.error(msgtxt)
            self.DCCui.label_CCD_testIntResult.setText(msgtxt)
            return
        allactions=self.CH.getListofInterfaceactions(['interfaceId'])
        knownaction=False
        delonlyFormat=False
               
        if action in allactions:                
            knownaction=True
        #check if other ids are empty    
        if  knownaction==True:           
            formatlist=self.CH.InterfaceConfigallids[action]
            idlist=self.CH.InterfaceConfigallids['interfaceId']
            for jjj in range(len(formatlist)):
                if formatlist[jjj] != '' and  idlist[jjj]!= self.id:
                    msgtxt="Can't delete this action. Formats in other ids!"
                    log.error(msgtxt)
                    self.DCCui.label_CCD_testIntResult.setText(msgtxt)
                    delonlyFormat=True
                    break       
        #check if is required action     
        if knownaction==True and delonlyFormat==False:
            reqtypelist,isreq=self.get_list_Genint_required_types(action)            
            if isreq==True:
                msgtxt="Can't delete this action, is a Required action!"
                log.error(msgtxt)
                self.DCCui.label_CCD_testIntResult.setText(msgtxt)                    
                delonlyFormat=True
                    
        #delete only the format        
        if knownaction==True and delonlyFormat==True:
            oldFormat=self.CH.Get_action_format_from_id(self.CH.InterfaceConfigallids,action,self.id)                    
            result = QtWidgets.QMessageBox.question(self,
                    "Confirm Format delete...",
                    "Old Format: "+str(oldFormat)+"\n"+
                    "Are you sure you want to delete the Format?",
                    QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.Yes:
                self.Replace_Format_in_ConfigFile(self.CH.Interfacefilename,action,'',self.id,self.CH.InterfaceConfigallids) 
                msgtxt=msgtxt="action:  "+action+" Format cleared!"
                log.info(msgtxt)
                self.DCCui.label_CCD_testIntResult.setText(msgtxt)   
        #delete the action       
        if knownaction==True and delonlyFormat==False:             
            result = QtWidgets.QMessageBox.question(self,
                    "Confirm action, info and type delete...",
                    "You are about to permanently delete action: "+action+"\n"                    
                    "Are you sure you want to delete the action?",
                    QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.Yes:
                #first info and type
                self.Delete_action_in_ConfigFile(self.CH.Interfacefilename,action+'_info',self.CH.InterfaceConfigallids_info) 
                self.Delete_action_in_ConfigFile(self.CH.Interfacefilename,action+'_type',self.CH.InterfaceConfigallids_type) 
                self.Delete_action_in_ConfigFile(self.CH.Interfacefilename,action,self.CH.InterfaceConfigallids)                 
                msgtxt=action+" Deleted!"
                log.info(msgtxt)
                self.DCCui.label_CCD_testIntResult.setText(msgtxt)   

    def PB_CCD_readactionDel(self):
        action=self.DCCui.lineEdit_CCD_readaction.text()
        if action == '':
            msgtxt="No Read action to Delete!"
            log.error(msgtxt)
            self.DCCui.label_CCD_testreadResult.setText(msgtxt)
            return 
        if action == 'interfaceId' or 'interfaceId' in action:
            msgtxt=="Can't change this Read action"
            log.error(msgtxt)
            self.DCCui.label_CCD_testreadResult.setText(msgtxt)
            return
        allactions=self.CH.getListofReadactions(['interfaceId'])
        knownaction=False
        delonlyFormat=False
        if action in allactions:                
            knownaction=True
        #check if other ids are empty    
        if  knownaction==True:           
            formatlist=self.CH.ReadConfigallids[action]
            idlist=self.CH.ReadConfigallids['interfaceId']
            for jjj in range(len(formatlist)):
                if formatlist[jjj] != '' and  idlist[jjj] != self.id:
                    msgtxt="Can't delete this Read action. Formats exist in other ids!"
                    log.error(msgtxt)
                    self.DCCui.label_CCD_testreadResult.setText(msgtxt)
                    delonlyFormat=True
                    break       
        #check if is required action     
        if knownaction==True and delonlyFormat==False:
            reqactions=self.CH.Required_read
            for reqa in reqactions:
                if action is reqa:
                    msgtxt="Can't delete this Read action, is a Required Read action!"
                    log.error(msgtxt)
                    self.DCCui.label_CCD_testreadResult.setText(msgtxt)                    
                    delonlyFormat=True
                    break
        #delete only the format        
        if knownaction==True and delonlyFormat==True:
            oldFormat=self.CH.Get_action_format_from_id(self.CH.ReadConfigallids,action,self.id)                    
            result = QtWidgets.QMessageBox.question(self,
                    "Confirm Format delete...",
                    "Old Format: "+str(oldFormat)+"\n"+
                    "Are you sure you want to delete the Format?",
                    QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.Yes:
                self.Replace_Format_in_ConfigFile(self.CH.Readfilename,action,'',self.id,self.CH.ReadConfigallids) 
                msgtxt=msgtxt="Read action:  "+action+" Format cleared!"
                log.info(msgtxt)
                self.DCCui.label_CCD_testreadResult.setText(msgtxt)   
        #delete only the action       
        if knownaction==True and delonlyFormat==False:             
            result = QtWidgets.QMessageBox.question(self,
                    "Confirm action, info and type delete...",
                    "You are about to permanently delete read action: "+action+"\n"                    
                    "Are you sure you want to delete the action?",
                    QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.Yes:
                #First info and type
                self.Delete_action_in_ConfigFile(self.CH.Readfilename,action+'_info',self.CH.ReadConfigallids_info) 
                self.Delete_action_in_ConfigFile(self.CH.Readfilename,action+'_type',self.CH.ReadConfigallids_type) 
                self.Delete_action_in_ConfigFile(self.CH.Readfilename,action,self.CH.ReadConfigallids)                 
                msgtxt=action+" Deleted!"
                log.info(msgtxt)
                self.DCCui.label_CCD_testreadResult.setText(msgtxt)   
    
    def Create_new_id(self):                
        idlist=self.CH.Configdata['interfaceId']
        idvallist=[]
        for iii in idlist:
            try:
                val=int(iii)
                idvallist.append(val)
            except:
                pass
        for jjj in range(10000):
            if jjj not in idvallist:
                anid=str(jjj)
                break
        return anid

    def PB_Add_Interface(self):        
        anid=self.Create_new_id()  
        aname=self.CH.getGformatforActionid('interfaceName',self.id)
        msgbox = QtWidgets.QMessageBox()
        msgbox.setWindowTitle('Add Interface ...')
        msgbox.setIcon(QtWidgets.QMessageBox.Question)
        msgbox.setText("Would you like to clone the "+aname+" interface? \nor\n"+
                      "Would you like to Create an empty interface?")
        msgbox.addButton(QtWidgets.QPushButton('Clone '+str(self.id)), QtWidgets.QMessageBox.AcceptRole)
        msgbox.addButton(QtWidgets.QPushButton('Empty'), QtWidgets.QMessageBox.YesRole)
        msgbox.addButton(QtWidgets.QPushButton('Cancel'), QtWidgets.QMessageBox.NoRole)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
        additional={}
        additional.update({'interfaceId_info':''})
        additional.update({'interfaceId_type':''})
        result = msgbox.exec_()
        #print(result)
        if result == 0: #QtWidgets.QMessageBox.AcceptRole:      
            aname=aname+'_clone'
            Configdata_all=self.CH.join_datasets(self.CH.Configdata,'',self.CH.Configdata_type,'_type')
            Configdata_all=self.CH.join_datasets(Configdata_all,'',self.CH.Configdata_info,'_info')
            Configdata_all=self.CH.join_datasets(Configdata_all,'',additional,'')
            self.CH.create_new_interface_in_file(self.CH.filename,anid,Configdata_all,False,Logopen=False,newname=aname,cloneid=self.id)
            ReadConfigallids_all=self.CH.join_datasets(self.CH.ReadConfigallids,'',self.CH.ReadConfigallids_type,'_type')
            ReadConfigallids_all=self.CH.join_datasets(ReadConfigallids_all,'',self.CH.ReadConfigallids_info,'_info')
            ReadConfigallids_all=self.CH.join_datasets(ReadConfigallids_all,'',additional,'')
            self.CH.create_new_interface_in_file(self.CH.Readfilename,anid,ReadConfigallids_all,False,Logopen=False,newname=aname,cloneid=self.id)
            InterfaceConfigallids_all=self.CH.join_datasets(self.CH.InterfaceConfigallids,'',self.CH.InterfaceConfigallids_type,'_type')
            InterfaceConfigallids_all=self.CH.join_datasets(InterfaceConfigallids_all,'',self.CH.InterfaceConfigallids_info,'_info')
            InterfaceConfigallids_all=self.CH.join_datasets(InterfaceConfigallids_all,'',additional,'')
            self.CH.create_new_interface_in_file(self.CH.Interfacefilename,anid,InterfaceConfigallids_all,True,Logopen=False,newname=aname,cloneid=self.id)
            
            self.Fill_interface_combobox()
            log.info("Succesfully Added Cloned Interface!")
        elif result == 1: #QtWidgets.QMessageBox.YesRole:    
            aname='New'
            
            Configdata_all=self.CH.join_datasets(self.CH.Configdata,'',self.CH.Configdata_type,'_type')
            Configdata_all=self.CH.join_datasets(Configdata_all,'',self.CH.Configdata_info,'_info')
            Configdata_all=self.CH.join_datasets(Configdata_all,'',additional,'')
            self.CH.create_new_interface_in_file(self.CH.filename,anid,Configdata_all,False,Logopen=False,newname=aname,cloneid=None)
            ReadConfigallids_all=self.CH.join_datasets(self.CH.ReadConfigallids,'',self.CH.ReadConfigallids_type,'_type')
            ReadConfigallids_all=self.CH.join_datasets(ReadConfigallids_all,'',self.CH.ReadConfigallids_info,'_info')
            ReadConfigallids_all=self.CH.join_datasets(ReadConfigallids_all,'',additional,'')
            self.CH.create_new_interface_in_file(self.CH.Readfilename,anid,ReadConfigallids_all,False,Logopen=False,newname=aname,cloneid=None)
            InterfaceConfigallids_all=self.CH.join_datasets(self.CH.InterfaceConfigallids,'',self.CH.InterfaceConfigallids_type,'_type')
            InterfaceConfigallids_all=self.CH.join_datasets(InterfaceConfigallids_all,'',self.CH.InterfaceConfigallids_info,'_info')
            InterfaceConfigallids_all=self.CH.join_datasets(InterfaceConfigallids_all,'',additional,'')
            self.CH.create_new_interface_in_file(self.CH.Interfacefilename,anid,InterfaceConfigallids_all,True,Logopen=False,newname=aname,cloneid=None)
            
            self.Fill_interface_combobox()
            log.info("Succesfully Added Empty Interface!")
    
    def PB_Del_Interface(self):        
        anid=self.CH.id
        aname=self.CH.getGformatforActionid('interfaceName',anid)
        numinterfaces=self.CH.Num_interfaces
        if numinterfaces<=1:
            amsg="Can't delete the interface at least one interface must be present in the configuration files!"
            log.error(amsg)            
            msgbox = QtWidgets.QMessageBox()
            msgbox.setWindowTitle('Delete Interface ...')
            msgbox.setIcon(QtWidgets.QMessageBox.Critical)
            msgbox.setText(amsg)            
            msgbox.exec_()
            return False
        else:
            for iii in self.CH.Configdata['interfaceId']:
                if str(iii)!=str(anid):
                    newid = str(iii)
                    break    

        if aname=='DELETE':
            additional={}
            additional.update({'interfaceId_info':''})
            additional.update({'interfaceId_type':''})
            Configdata_all=self.CH.join_datasets(self.CH.Configdata,'',self.CH.Configdata_type,'_type')
            Configdata_all=self.CH.join_datasets(Configdata_all,'',self.CH.Configdata_info,'_info')
            Configdata_all=self.CH.join_datasets(Configdata_all,'',additional,'')
            self.CH.delete_interface_in_file(self.CH.filename,anid,Configdata_all,False,Logopen=False)
            ReadConfigallids_all=self.CH.join_datasets(self.CH.ReadConfigallids,'',self.CH.ReadConfigallids_type,'_type')
            ReadConfigallids_all=self.CH.join_datasets(ReadConfigallids_all,'',self.CH.ReadConfigallids_info,'_info')
            ReadConfigallids_all=self.CH.join_datasets(ReadConfigallids_all,'',additional,'')
            self.CH.delete_interface_in_file(self.CH.Readfilename,anid,ReadConfigallids_all,False,Logopen=False)
            InterfaceConfigallids_all=self.CH.join_datasets(self.CH.InterfaceConfigallids,'',self.CH.InterfaceConfigallids_type,'_type')
            InterfaceConfigallids_all=self.CH.join_datasets(InterfaceConfigallids_all,'',self.CH.InterfaceConfigallids_info,'_info')
            InterfaceConfigallids_all=self.CH.join_datasets(InterfaceConfigallids_all,'',additional,'')
            self.CH.delete_interface_in_file(self.CH.Interfacefilename,anid,InterfaceConfigallids_all,False,Logopen=False)
            self.CH.Set_id(newid)
            self.id=newid
            self.Force_CH_refresh_info_From_file(False)
            self.Fill_interface_combobox()
            log.info('Interface ID:'+str(anid)+ ' has been deleted!')
            return True
        else:            
            msgbox = QtWidgets.QMessageBox()
            msgbox.setWindowTitle('Delete Interface ...')
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setText("To delete " +aname +" interface you must set the interfaceName to DELETE")            
            msgbox.exec_()
            return False

    def PB_CCD_actionAdd(self):
        isok=self.Do_Test_format()
        if isok==True:
            action=self.Selected_action_dict['action']
            if action == '':
                msgtxt="No action to Add!"
                log.error(msgtxt)
                self.DCCui.label_CCD_testResult.setText(msgtxt)                
                return
            newFormat=self.Selected_action_dict['Format']
            #print(action,newFormat)
            if action == 'interfaceId' or 'interfaceId' in action:
                msgtxt="Can't change this action"
                log.error(msgtxt)
                self.DCCui.label_CCD_testResult.setText(msgtxt)                
                return

            isexit,knownaction,isinfo,istype,dataset=self.revise_data_to_add(0,action)                                   
            if isexit==-1:
                return         
                    
            if knownaction==True:    
                oldFormat=self.CH.Get_action_format_from_id(dataset,action,self.id)                    
                result = QtWidgets.QMessageBox.question(self,
                      "Confirm Format Replace...",
                      "Old Format: "+str(oldFormat)+"\nfor New Format: "+ str(newFormat)+"\n"+
                      "Are you sure you want to Replace the Format?",
                      QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
                if result == QtWidgets.QMessageBox.Yes:
                    self.Replace_Format_in_ConfigFile(self.CH.filename,action,newFormat,self.id,dataset)
                    msgtxt="action:  "+action+" Format replaced for "+newFormat+" "
                    log.info(msgtxt)
                    self.DCCui.label_CCD_testResult.setText(msgtxt)      
            else:
                self.Add_New_action_in_ConfigFile(self.CH.filename,action,newFormat,self.id,dataset)
                msgtxt="Action "+action+" Added!"
                log.info(msgtxt)
                self.DCCui.label_CCD_testResult.setText(msgtxt)
            if action=='interfaceName':
                self.Fill_interface_combobox()    

    def PB_CCD_readactionAdd(self):
        isok=self.Do_Test_Read()
        if isok==True:
            action=self.Selected_read_dict['action']
            if action == '':
                msgtxt="No Read action to Add!"
                log.error(msgtxt)
                self.DCCui.label_CCD_testreadResult.setText(msgtxt)                
                return
            newFormat=self.Selected_read_dict['Format']
            #print(action,newFormat)
            if action == 'interfaceId' or 'interfaceId' in action:
                msgtxt="Can't change this Read action"
                log.error(msgtxt)
                self.DCCui.label_CCD_testreadResult.setText(msgtxt)                
                return            
                                                
            isexit,knownaction,isinfo,istype,dataset=self.revise_data_to_add(1,action)                                   
            if isexit==-1:
                return 

            if knownaction==True:    
                oldFormat=self.CH.Get_action_format_from_id(dataset,action,self.id)                    
                result = QtWidgets.QMessageBox.question(self,
                      "Confirm Format Replace...",
                      "Old Format: "+str(oldFormat)+"\nfor New Format: "+ str(newFormat)+"\n"+
                      "Are you sure you want to Replace the Format?",
                      QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
                if result == QtWidgets.QMessageBox.Yes:
                    self.Replace_Format_in_ConfigFile(self.CH.Readfilename,action,newFormat,self.id,dataset)
                    msgtxt="action:  "+action+" Format replaced for "+newFormat+" "
                    log.info(msgtxt)
                    self.DCCui.label_CCD_testreadResult.setText(msgtxt)      
            else:
                #print('here ok?')
                self.Add_New_action_in_ConfigFile(self.CH.Readfilename,action,newFormat,self.id,dataset)
                msgtxt="Read action "+action+" Added!"
                log.info(msgtxt)
                self.DCCui.label_CCD_testreadResult.setText(msgtxt)            
    def PB_CCD_IntactionTest(self):
        self.Do_Test_Int()
        
    def PB_CCD_IntactionAdd(self):
        isok=self.Do_Test_Int()
        if isok==True:
            action=self.Selected_Int_dict['action']
            if action == '':
                msgtxt="No Read action to Add!"
                log.error(msgtxt)
                self.DCCui.label_CCD_testIntResult.setText(msgtxt)                
                return            
            newFormat=self.Selected_Int_dict['Format']
            #print(action,newFormat)
            if action == 'interfaceId' or 'interfaceId' in action:
                msgtxt="Can't change this general action"
                log.error(msgtxt)
                self.DCCui.label_CCD_testIntResult.setText(msgtxt)                
                return            
                                                
            isexit,knownaction,isinfo,istype,dataset=self.revise_data_to_add(2,action)                                   
            if isexit==-1:
                return 
            if istype==False and isinfo==False:                
                newType=self.Selected_Int_dict['Type'] 
                #print('Entered no type ->>>',newType)
            if knownaction==True:    
                oldFormat=self.CH.Get_action_format_from_id(dataset,action,self.id)                    
                result = QtWidgets.QMessageBox.question(self,
                      "Confirm Format Replace...",
                      "Old Format: "+str(oldFormat)+"\nfor New Format: "+ str(newFormat)+"\n"+
                      "Are you sure you want to Replace the Format?",
                      QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
                if result == QtWidgets.QMessageBox.Yes:
                    if istype==False and isinfo==False:
                        self.Replace_Format_in_ConfigFile(self.CH.Interfacefilename,action+'_type',newType,self.id,self.CH.InterfaceConfigallids_type)
                        #print('Replaced type',newType)
                    self.Replace_Format_in_ConfigFile(self.CH.Interfacefilename,action,newFormat,self.id,dataset)                    
                    msgtxt="General action:  "+action+" Format replaced for "+newFormat+" "
                    log.info(msgtxt)
                    self.DCCui.label_CCD_testIntResult.setText(msgtxt)      
            else:
                #print('here ok?')                
                if istype==False and isinfo==False:
                    self.Add_New_action_in_ConfigFile(self.CH.Interfacefilename,action+'_type',newType,self.id,self.CH.InterfaceConfigallids_type)
                self.Add_New_action_in_ConfigFile(self.CH.Interfacefilename,action,newFormat,self.id,dataset)
                for iii in dataset['interfaceId']:                
                    if iii!=self.id:
                        if isinfo==True:
                            self.Replace_Format_in_ConfigFile(self.CH.Interfacefilename,action,'*('+str(self.id)+')',iii,self.CH.InterfaceConfigallids_info)
                        if istype==False and isinfo==False:
                            self.Replace_Format_in_ConfigFile(self.CH.Interfacefilename,action,newFormat,iii,dataset)                    
                            self.Replace_Format_in_ConfigFile(self.CH.Interfacefilename,action+'_type','*('+str(self.id)+')',iii,self.CH.InterfaceConfigallids_type)

                msgtxt="General action "+action+" Added! For all Interfaces!"
                log.info(msgtxt)
                self.DCCui.label_CCD_testIntResult.setText(msgtxt)            




    def revise_data_to_add(self,typeofdata,action):
        '''
        typeofdata=0 -> action config
        typeofdata=1 -> read
        typeofdata=2 -> interface
        '''
        knownaction=False
        isinfo=False
        istype=False
        
        if typeofdata==1:
            maindataset=self.CH.ReadConfigallids
        elif typeofdata==2:
            maindataset=self.CH.InterfaceConfigallids
        else:
            maindataset=self.CH.Configdata   
        dataset=maindataset    
        baseaction=action
        if '_info' in action:                 
            isinfo=True            
            if typeofdata==1:
                dataset=self.CH.ReadConfigallids_info  
            elif typeofdata==2:
                dataset=self.CH.InterfaceConfigallids_info
            else:
                dataset=self.CH.Configdata_info
            baseaction=action.replace('_info','') 
        if '_type' in action:
            istype=True 
            if typeofdata==1:
                dataset=self.CH.ReadConfigallids_type  
            elif typeofdata==2:
                dataset=self.CH.InterfaceConfigallids_type
            else:
                dataset=self.CH.Configdata_type  
            baseaction=action.replace('_type','')
        exceptlist=['interfaceId']
        allactions=self.CH.getListofAnyactionsindata(maindataset,exceptlist)     
        for aaa in allactions:
            if baseaction == aaa:                
                knownaction=True                       
                break                                     
        # if unknown action don't allow to set info     
        if knownaction==False and isinfo==True:                                
            msgtxt="Can't add info without an action! Add first:"+action.replace('_info','')
            log.error(msgtxt)
            self.DCCui.label_CCD_testResult.setText(msgtxt)   
            return -1,knownaction,isinfo,istype,dataset
        # if unknown action don't allow to set type                  
        if knownaction==False and istype==True:                   
            msgtxt="Can't add a type without an action! Add first:"+action.replace('_type','')
            log.error(msgtxt)
            self.DCCui.label_CCD_testResult.setText(msgtxt)                
            return -1,knownaction,isinfo,istype,dataset         
        #check if info or type are in file
        allactions=self.CH.getListofAnyactionsindata(dataset,exceptlist)     
        if knownaction==True and (isinfo == True or istype ==True):
            knownaction=False 
            for aaa in allactions:
                if baseaction == aaa:                
                    knownaction=True                               
                    break    
        return 0,knownaction,isinfo,istype,dataset                 
            

    def Refresh_viewed_filenames(self):        
        fff=self.shorten_filename(self.extract_filename(self.CH.filename,False))
        self.DCCui.groupBox_CCD_actionFiles.setTitle("Actual Config File:"+fff)  

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
        self.Actual_Tab=self.DCCui.tabWidget_CCD_configs.currentIndex()
            

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
        self.DCCui.tableWidget_CCD.clear()
        #Table_NumCols=self.Num_interfaces+1
        Table_NumCols=4
        self.DCCui.tableWidget_CCD.setColumnCount(Table_NumCols)        
        self.DCCui.tableWidget_CCD.setHorizontalHeaderLabels(["Action", "Format","Info","Type"])
        self.DCCui.tableWidget_CCD.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)    
        iii=0
        tabindex=self.Actual_Tab
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

        self.DCCui.tableWidget_CCD.setRowCount(Table_NumRows)
        #print(Configsetinfo)
        for ccc in Configset:   
            self.DCCui.tableWidget_CCD.setItem(iii,0, QTableWidgetItem(ccc))
            self.DCCui.tableWidget_CCD.setItem(iii,1, QTableWidgetItem(Configset[ccc]))
            try:
                ainfo=self.CH.get_info_type_from_id(Configsetinfo,ccc,self.CH.id)                 
                #print(ccc,'-->',ainfo)
                self.DCCui.tableWidget_CCD.setItem(iii,2, QTableWidgetItem(ainfo))
            except: # Exception as e:
                #log.error(e) 
                self.DCCui.tableWidget_CCD.setItem(iii,2, QTableWidgetItem(''))
                pass    
            try:
                atype=self.CH.get_info_type_from_id(Configsettype,ccc,self.CH.id)
                self.DCCui.tableWidget_CCD.setItem(iii,3, QTableWidgetItem(atype))
            except:
                self.DCCui.tableWidget_CCD.setItem(iii,3, QTableWidgetItem(''))
                pass    
            if ccc in Reqset:
                color=QColor('yellow')
                self.setColortoRow(self.DCCui.tableWidget_CCD, iii, color)                
            iii=iii+1
        self.DCCui.tableWidget_CCD.resizeColumnsToContents()            
    
    def setColortoRow(self,table, rowIndex, color):
        for jjj in range(table.columnCount()):
            table.item(rowIndex, jjj).setBackground(color)

    def Fill_interface_combobox(self):        
        self.DCCui.comboBox_CCD_interface.clear()
        for iii in self.CH.Configdata['interfaceId']:           
            self.DCCui.comboBox_CCD_interface.addItem(iii)                          
        index= self.DCCui.comboBox_CCD_interface.findText(self.CH.id,QtCore.Qt.MatchFixedString)
        self.DCCui.comboBox_CCD_interface.setCurrentIndex(index)    
        aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.CH.id)
        self.DCCui.label_CCD_interfaceName.setText(aname)    
    
    def Fill_action_combobox(self):
        self.DCCui.comboBox_CCD_action.clear()
        allactions=self.CH.getListofActions(['interfaceId','interfaceId_type','interfaceId_info'])
        self.DCCui.comboBox_CCD_action.addItem('')
        for iii in allactions:           
            self.DCCui.comboBox_CCD_action.addItem(iii)          
        #index= self.DCCui.comboBox_CCD_action.findText('interfaceName',QtCore.Qt.MatchFixedString)
        index=0
        self.DCCui.comboBox_CCD_action.setCurrentIndex(index)    
        self.CH.Selected_action=self.DCCui.comboBox_CCD_action.currentText()

    def Fill_read_combobox(self):
        self.DCCui.comboBox_CCD_readaction.clear()
        allactions=self.CH.getListofReadactions(['interfaceId','interfaceId_type','interfaceId_info'])
        self.DCCui.comboBox_CCD_readaction.addItem('')
        for iii in allactions:           
            self.DCCui.comboBox_CCD_readaction.addItem(iii)          
        #index= self.DCCui.comboBox_CCD_readaction.findText('interfaceName',QtCore.Qt.MatchFixedString)
        index=0
        self.DCCui.comboBox_CCD_readaction.setCurrentIndex(index)    
        self.Selected_read_dict.update({'action':self.DCCui.comboBox_CCD_readaction.currentText()})

    def Fill_GenConfigInt_comboboxes(self):
        self.Fill_GenConfigInt_combobox()
        self.Fill_GenConfigInttype_combobox()

    def Fill_GenConfigInt_combobox(self):
        self.DCCui.comboBox_CCD_Intaction.clear()
        allactions=self.CH.getListofInterfaceactions(['interfaceId','interfaceId_type','interfaceId_info'])
        self.DCCui.comboBox_CCD_Intaction.addItem('')
        for iii in allactions:           
            self.DCCui.comboBox_CCD_Intaction.addItem(iii)                  
        index=0
        self.DCCui.comboBox_CCD_Intaction.setCurrentIndex(index)    
        self.Selected_Int_dict.update({'action':self.DCCui.comboBox_CCD_Intaction.currentText()})    
    
    def Fill_GenConfigInttype_combobox(self):
        self.typelist=['','str','float','int','bool','char','list','dict','regex','byte','char','action']
        self.DCCui.comboBox_CCD_Inttype.clear()
        for iii in self.typelist:           
            self.DCCui.comboBox_CCD_Inttype.addItem(iii)                  
        index=0
        self.DCCui.comboBox_CCD_Inttype.setCurrentIndex(index)  
        #self.Selected_Int_dict.update({'type':self.DCCui.comboBox_CCD_Inttype.currentText()})  
        


    def ComboBox_Select_action(self):
        self.Selected_action=self.DCCui.comboBox_CCD_action.currentText()         
        self.DCCui.lineEdit_CCD_action.setText(self.Selected_action)     
        aFormat=self.CH.getGformatforActionid(self.Selected_action,self.id)
        #self.DCCui.lineEdit_CCD_action.setText(self.Selected_action)     
        self.DCCui.lineEdit_CCD_Format.setText(aFormat) 
        self.fill_actionParameters_Table(aFormat)
    
    def ComboBox_Select_Readaction(self):
        self.Selected_Readaction=self.DCCui.comboBox_CCD_readaction.currentText()         
        self.DCCui.lineEdit_CCD_readaction.setText(self.Selected_Readaction)     
        aFormat=self.CH.getGformatforReadactionid(self.Selected_Readaction,self.id)
        #self.DCCui.lineEdit_CCD_readaction.setText(self.Selected_Readaction)     
        self.DCCui.lineEdit_CCD_readFormat.setText(aFormat) 
        self.fill_ReadactionParameters_Table(aFormat)

    def ComboBox_Select_Intaction(self):
        self.Selected_Intaction=self.DCCui.comboBox_CCD_Intaction.currentText()         
        self.DCCui.lineEdit_CCD_Intaction.setText(self.Selected_Intaction)     
        aFormat=self.CH.getGformatforIntactionid(self.Selected_Intaction,self.id)
        atype=self.CH.getGformatforActiondataid(self.CH.InterfaceConfigallids_type,self.Selected_Intaction,self.id)
        #self.DCCui.lineEdit_CCD_readaction.setText(self.Selected_Readaction)     
        self.DCCui.lineEdit_CCD_IntFormat.setText(aFormat) 
        self.set_combobox_Genint_type(atype)
        

    def ComboBox_Select_Inttype(self):
        self.Selected_Intaction=self.DCCui.comboBox_CCD_Intaction.currentText() 
        combotype=self.DCCui.comboBox_CCD_Inttype.currentText()
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
        index=self.DCCui.comboBox_CCD_Inttype.findText(atype,QtCore.Qt.MatchFixedString)    
        if index==-1:
            self.DCCui.comboBox_CCD_Inttype.addItem(atype)
            index=self.DCCui.comboBox_CCD_Inttype.findText(atype,QtCore.Qt.MatchFixedString)    
        self.DCCui.comboBox_CCD_Inttype.setCurrentIndex(index) 
        self.Selected_Int_dict.update({'Type':atype})
        #print('Type to ',atype)
    
    def Do_Test_Int(self):
        aFormat=self.DCCui.lineEdit_CCD_IntFormat.text()   
        action=self.DCCui.lineEdit_CCD_Intaction.text()
        isok=False
        if action!=self.Selected_Int_dict['action']:
            self.Selected_Int_dict['action']=action
        reqtypelist,isreq=self.get_list_Genint_required_types(action)   
        
        atype=self.DCCui.comboBox_CCD_Inttype.currentText()       
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
                self.DCCui.label_CCD_testIntResultFormat.setText(msgtxt)
            else:
                try:
                    msgtxt="Format of type "+atype+" accepted: " + str(val)
                except:
                    msgtxt="Format of type "+atype+" accepted"
                    pass
                log.info(msgtxt)
                self.DCCui.label_CCD_testIntResultFormat.setText(msgtxt)    
        return isok,val    
    
    def Test_a_read(self,aFormat):
        befaFormat=self.DCCui.lineEdit_CCD_readFormat.text()   
        befaction=self.DCCui.lineEdit_CCD_readaction.text()
        self.DCCui.lineEdit_CCD_readFormat.setText(aFormat)   
        self.DCCui.DCCui.lineEdit_CCD_readaction.setText('__Test__')
        isok=self.Do_Test_Read()
        if isok==False:
            val=None  
        else:
            val= self.Selected_read_dict['Format']    
        self.DCCui.lineEdit_CCD_readFormat.setText(befaFormat)   
        self.DCCui.DCCui.lineEdit_CCD_readaction.setText(befaction)

    def Test_a_format(self,aFormat):
        befaFormat=self.DCCui.lineEdit_CCD_Format.text()   
        befaction=self.DCCui.lineEdit_CCD_action.text()
        self.DCCui.lineEdit_CCD_Format.setText(aFormat)   
        self.DCCui.lineEdit_CCD_action.setText('__Test__')
        isok=self.Do_Test_format()
        if isok==False:
            val=None  
        else:
            val= self.Selected_action_dict['Format']    
        self.DCCui.lineEdit_CCD_Format.setText(befaFormat)   
        self.DCCui.lineEdit_CCD_action.setText(befaction)
        return isok,val

    def Do_Test_Read(self): 
        #print("entered Read")       
        aFormat=self.DCCui.lineEdit_CCD_readFormat.text()   
        action=self.DCCui.lineEdit_CCD_readaction.text()
        isok=False
        if action!=self.Selected_read_dict['action']:
            self.Selected_read_dict['action']=action
        isok=self.fill_ReadactionParameters_Table(aFormat)    
        if aFormat != self.Selected_read_dict['Format']:             
            if isok==True:
                self.Selected_read_dict.update({'Format':aFormat})                
        return isok  

    def Do_Test_format(self):
        aFormat=self.DCCui.lineEdit_CCD_Format.text()   
        action=self.DCCui.lineEdit_CCD_action.text()
        if action!=self.Selected_action_dict['action']:
            self.Selected_action_dict['action']=action
        if aFormat != self.Selected_action_dict['Format']:      
            isok=self.fill_actionParameters_Table(aFormat) 
            if isok==True:
                self.Selected_action_dict.update({'Format':aFormat})        
        else:
            numrowTable=self.DCCui.tableWidget_CCD_actionParam.rowCount()
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
            self.DCCui.label_CCD_testResult.setText("Evaluated Gcode: "+str(Gcode))
            self.Selected_action_dict.update({'Format':aFormat})
            self.Selected_action_dict.update({'action':action})
        return isok    
    
    def Replace_Parameter_Values_from_Table(self,Parameters):    
        newparam={}    
        try:
            for row in range(len(Parameters)):                                   
                Tpar=self.DCCui.tableWidget_CCD_actionParam.item(row, 0).text()             
                Tvalue=self.DCCui.tableWidget_CCD_actionParam.item(row, 1).text()            
                for param in Parameters:
                    if param == Tpar and Tvalue != '':
                        newparam.update({param:Tvalue})
                        break
        except:
            newparam={}
            pass            
        return newparam        

    def fill_actionParameters_Table(self,aFormat):
        isok=False
        self.DCCui.tableWidget_CCD_actionParam.clear()
        Table_NumCols=3
        self.DCCui.tableWidget_CCD_actionParam.setColumnCount(Table_NumCols)
        Table_NumRows=0
        self.DCCui.tableWidget_CCD_actionParam.setRowCount(Table_NumRows)
        self.DCCui.label_CCD_testResult.setText("Evaluated Gcode: ")
        self.DCCui.label_CCD_testResultFormat.setText("Processed Format: ")  
        #Table_NumCols=self.Num_interfaces+1
        if self.CH.Check_Format(aFormat)==False:
            self.DCCui.label_CCD_testResult.setText("Wrong Parenthesis")
            return isok
        try:    
            P_Allinfo=self.CH.get_all_info_from_Format(aFormat)
        except:
            P_Allinfo={}
            self.DCCui.label_CCD_testResult.setText("Format contains Errors")
            pass
        if P_Allinfo is not {}:            
            if P_Allinfo['IsRegex']==True:
                self.DCCui.label_CCD_testResult.setText("Format contains regex read Code")
                return isok
            isok=True    
            ReqOpParamsdict=P_Allinfo['ReqOpParamsdict']
            paramlist=P_Allinfo['Parameterlist']
            optionlist=P_Allinfo['Optionlist']
            optiontxtlist=P_Allinfo['Optiontxtlist']
            minop=P_Allinfo['minRequiredOptions']
            self.DCCui.label_CCD_testResultFormat.setText("Processed Format: "+str(P_Allinfo['processedFormat']))                            
            Table_NumRows=len(ReqOpParamsdict)
            self.DCCui.tableWidget_CCD_actionParam.setRowCount(Table_NumRows)
            self.DCCui.tableWidget_CCD_actionParam.setHorizontalHeaderLabels(["Parameter", "Value","Constraint"])
            self.DCCui.tableWidget_CCD_actionParam.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)    
            iii=0
            befaconstraint=''
            if P_Allinfo['IsOred']==True:
                befaconstraint=befaconstraint+'OR '
            
            aconstraint=befaconstraint  
            Parameters={}  
            for ccc in ReqOpParamsdict:   
                self.DCCui.tableWidget_CCD_actionParam.setItem(iii,0, QTableWidgetItem(ccc))
                self.DCCui.tableWidget_CCD_actionParam.setItem(iii,1, QTableWidgetItem(str(iii)))
                Parameters.update({ccc:iii})
            
                self.DCCui.tableWidget_CCD_actionParam.setItem(iii,2, QTableWidgetItem(befaconstraint+ReqOpParamsdict[ccc]))
                if ReqOpParamsdict[ccc]=='required':
                    color=QColor('lightblue')
                    self.setColortoRow(self.DCCui.tableWidget_CCD_actionParam, iii, color)                
                iii=iii+1
            self.DCCui.tableWidget_CCD_actionParam.resizeColumnsToContents()
            Gcode=self.CH.Get_code(aFormat,Parameters)
            self.DCCui.label_CCD_testResult.setText("Evaluated Gcode: "+str(Gcode))
            self.Selected_action_dict={'action':self.DCCui.lineEdit_CCD_action.text(),'Format':aFormat,'Parameters':Parameters,'ReqOpParamsdict':ReqOpParamsdict}

        return isok    
    
    def fill_ReadactionParameters_Table(self,aFormat):
        isok=False
        self.DCCui.tableWidget_CCD_readactionParam.clear()
        Table_NumCols=4
        self.DCCui.tableWidget_CCD_readactionParam.setColumnCount(Table_NumCols)
        Table_NumRows=0
        self.DCCui.tableWidget_CCD_readactionParam.setRowCount(Table_NumRows)
        self.DCCui.label_CCD_testreadResult.setText("Evaluated all Read: ")
        self.DCCui.label_CCD_testreadResultFormat.setText("Evaluated Format read: ")  
        #Table_NumCols=self.Num_interfaces+1
        if self.CH.Check_Format(aFormat)==False:
            self.DCCui.label_CCD_testreadResult.setText("Wrong Parenthesis")
            return isok
        #print('pass check format')    
        try:    
            P_Allinfo=self.CH.get_all_info_from_Format(aFormat)
            #print('pass get all info from format')   
            #print(P_Allinfo) 
        except:
            P_Allinfo={}
            self.DCCui.label_CCD_testreadResult.setText("Format contains Errors")
            pass
        if P_Allinfo is not {}:                        
            if P_Allinfo['IsRegex']==False or P_Allinfo['IsOred']==True:
                self.DCCui.label_CCD_testreadResult.setText("Format contains action Code")
                return isok
            #print('pass check or and regex')    
            isok=True    
            ReqOpParamsdict=P_Allinfo['ReqOpParamsdict']
            paramlist=P_Allinfo['Parameterlist']
            optionlist=P_Allinfo['Optionlist']
            optiontxtlist=P_Allinfo['Optiontxtlist']
            minop=P_Allinfo['minRequiredOptions']
            regexcmd=P_Allinfo['RegexCommand']
            self.DCCui.label_CCD_testreadResultFormat.setText("Search pattern: "+regexcmd)                            
            
            iii=0                        
            Parameters={}  
            texteval=self.DCCui.lineEdit_CCD_testRead_text.text()
            #print(texteval)
            
            try:
                rm=re.search(regexcmd,texteval)
                nummatch=len(rm.groups())
                #print(nummatch)
                if nummatch==0:
                    self.DCCui.label_CCD_testreadResult.setText("No matches found!")
                if nummatch>0:
                    #log.info('Test found '+str(nummatch)+' match(es)')
                    self.DCCui.label_CCD_testreadResult.setText('Test found '+str(nummatch)+' match(es)!')
                    Table_NumRows=nummatch
                    self.DCCui.tableWidget_CCD_readactionParam.setRowCount(Table_NumRows)
                    self.DCCui.tableWidget_CCD_readactionParam.setHorizontalHeaderLabels(["Match", "Parameter","Value","Option"])
                    self.DCCui.tableWidget_CCD_readactionParam.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)    
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
                        self.DCCui.tableWidget_CCD_readactionParam.setItem(iii,0, QTableWidgetItem(optxt))
                        self.DCCui.tableWidget_CCD_readactionParam.setItem(iii,1, QTableWidgetItem(ptxt))
                        self.DCCui.tableWidget_CCD_readactionParam.setItem(iii,2, QTableWidgetItem(str(readvalue)))
                        self.DCCui.tableWidget_CCD_readactionParam.setItem(iii,3, QTableWidgetItem(op))
                        Parameters.update({op:readvalue})                    
                        
                    self.DCCui.tableWidget_CCD_readactionParam.resizeColumnsToContents()
            except Exception as e:
                #log.error(e) 
                #log.info('Test found no matches!')
                self.DCCui.label_CCD_testreadResult.setText("No matches found!")
                pass

            self.Selected_read_dict.update({'action':self.DCCui.lineEdit_CCD_readaction.text()})
            self.Selected_read_dict.update({'Format':aFormat})
            self.Selected_read_dict.update({'Parameters':Parameters})
            self.Selected_read_dict.update({'testRead':self.DCCui.label_CCD_testreadResult.text()})
        return isok    


    def ComboBox_Select_interface(self):
        anid=self.DCCui.comboBox_CCD_interface.currentText()
        if str(anid)!=str(self.CH.id):            
            self.CH.Set_id(str(anid))
            aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.CH.id)
            self.DCCui.label_CCD_interfaceName.setText(aname)  
            self.Force_CH_refresh_info_From_file(False)            
            self.id=self.CH.id  
            self.Refresh_after_config_File_change()
    
    def Force_CH_refresh_info_From_file(self,alog):
        self.CH.Setup_Command_Handler(alog)   #Refresh info in CH 
        self.CH.Init_Read_Interface_Configurations(self.CH.Required_read,self.CH.Required_interface,alog) 
    
    def PB_CCD_Set_Preview(self):            
        #print('clicked')
        self.aList=[]
        self.set_clicked.emit(self.aList)
    
    def file_has_updated(self,filename):
        self.file_update.emit(filename)

    def getGformatforActionfromTable(self,action):
        ActionFormat=None
        try:       
            Table_NumRows=self.Get_Number_of_Actual_Interface_Formats()
            for row in range(Table_NumRows):                        
                hhh=self.DCCui.tableWidget_CCD.item(row, 0).text()
                hhhval=self.DCCui.tableWidget_CCD.item(row, 1).text()     
                if hhh==action:            
                    ActionFormat=hhhval
        except:
            pass
        #print('get from table '+ActionFormat)
        return ActionFormat

    def accept(self):
        #print('accepted')        
        return self.CH.id   
    
    def PB_CCD_actionTest(self):
        self.Do_Test_format()
    
    def PB_CCD_readactionTest(self):
        '''
        Do all action tests including or replacing the test format in the read sequence.
        Read sequence is the same as in the file order. 
        When is a new Read action then is executed after all the others.        
        '''
        isok=self.Do_Test_Read()
        if isok==True:
            ini_read_dict={}
            for aaa in self.Selected_read_dict:
                ini_read_dict.update({aaa:self.Selected_read_dict[aaa]})
                #self.Selected_read_dict.update({aaa:None})
            iniread_done=False
            allread={}
            self.Selected_read_dict.update({'AlltestRead':allread})
            log.info('---------------All read actions Test---------------')
            iniindex=None
            txtlog=''
            for iii in self.CH.Read_Config:
                if iii != 'interfaceId' and iii != '':
                    index= self.DCCui.comboBox_CCD_readaction.findText(iii,QtCore.Qt.MatchFixedString)        
                    try:
                        #Clean last result
                        self.Selected_read_dict.update({'testRead':''})
                        if iii!=ini_read_dict['action']:
                            #test runs the test auomatically when selected
                            self.DCCui.comboBox_CCD_readaction.setCurrentIndex(index)
                        else:
                            #test does not run the test auomatically when selected from program
                            #print('entered else')
                            self.DCCui.lineEdit_CCD_readaction.setText(ini_read_dict['action'])
                            self.DCCui.lineEdit_CCD_readFormat.setText(ini_read_dict['Format'])    
                            self.Do_Test_Read()
                            iniindex=index
                            iniread_done=True

                        read=self.Selected_read_dict['testRead']
                        action=self.Selected_read_dict['action']                    
                        evformat=self.Selected_read_dict['Format']                                        
                        log.info(action+'-->'+read)
                        txtlog=txtlog+action+'-->'+read+'\n'
                        allread.update({index:{action,read,evformat}})                        
                    except:
                        pass
            
            # set the original values   
            if iniindex==None:
                self.DCCui.lineEdit_CCD_readaction.setText(ini_read_dict['action'])
                self.DCCui.lineEdit_CCD_readFormat.setText(ini_read_dict['Format'])        
            else:
                self.DCCui.comboBox_CCD_readaction.setCurrentIndex(iniindex)
                self.DCCui.lineEdit_CCD_readFormat.setText(ini_read_dict['Format'])        

            if iniread_done==False:
                self.Do_Test_Read()
                iniread_done=True
                read=self.Selected_read_dict['testRead']
                action=self.Selected_read_dict['action']                    
                evformat=self.Selected_read_dict['Format']                                        
                allread.update({index:{action,read,evformat}})
            
            self.Selected_read_dict.update({'AlltestRead':allread})            
            self.Selected_read_dict.update({'testRead':txtlog})            
            #print(self.Selected_read_dict['AlltestRead'])
            

    def PB_debugtests(self):
        '''
        newFormat='[a][b][c][d][4][?{7}]{8}'
        print(self.get_list_in_between_txt(newFormat,'[',']'))

        print(self.Format_which_Inside_Parenthesees(newFormat,r'\{',r'\}') ) 
        print(self.Format_which_Inside_Parenthesees(newFormat) ) 
        '''
        '''
        Reqactions={'test','interfaceId','interfaceName'}
        isok=self.CH.Check_command_config_file_Content('test/testConfig.config',Reqactions,False)
        print('Check Passed:',isok)
        '''
        
        '''
        Params=self.CH.Get_Parameters_Needed_for_action(self.Selected_action,self.id)
        print(Params)
        print(self.CH.Get_list_of_all_parameters_in_interface(self.id))
        print(self.CH.Get_Gcode_for_Action(action,Parameters))
        '''
        '''
        print('--------------------------------------------------')
        Reqactions={'interfaceId'}
        isok=self.CH.Check_command_config_file_Content('config/InterfaceConfig.config',Reqactions,False)
        print('Check Passed:',isok)
        data=self.CH.Load_command_config_from_file('config/InterfaceConfig.config')
        print(data)
        print('--------------------------------------------------')
        action='test'    
        Parameters={'X':15,'Y':20.1,'Z':'8','str_var':'X'}    
        Gcode,isok=self.CH.Get_Gcode_for_Action(action,Parameters)
        print(Gcode)        
        self.DCCui.label_test.setText(Gcode)  
        '''
        '''
        print('--------------------------------------------------')
        aFormat=self.CH.getGformatforAction('linearMove')
        print(aFormat,'->',self.CH.regex_for_parameters(aFormat))
        aFormat=self.CH.getGformatforAction('rapidMove')
        print(aFormat,'->',self.CH.regex_for_parameters(aFormat))
        action=self.DCCui.comboBox_CCD_action.currentText()
        aFormat=self.CH.getGformatforAction(action)
        print(aFormat,'->',self.CH.regex_for_parameters(aFormat))
        Parameters={'X':15,'Y':20.1,'Z':'8','str_var':'X'}  
        Gcode,isok=self.CH.Get_Gcode_for_Action(action,Parameters)
        print(Gcode)        
        self.DCCui.label_test.setText(Gcode) 
        '''
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



