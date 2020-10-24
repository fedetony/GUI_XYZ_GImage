from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
import re
import logging
import GuiXYZ_CCD
import class_CH
from types import *

class CommandConfigurationDialog(QWidget,GuiXYZ_CCD.Ui_Dialog_CCD):
    set_clicked= QtCore.pyqtSignal(list)
    file_update= QtCore.pyqtSignal(str)
    #def __init__(self,NumLayers,Selected_Layers,parent=None):    
    #    super().__init__(parent)
    def __init__(self,selected_interface_id, *args, **kwargs):                
        super(CommandConfigurationDialog, self).__init__(*args, **kwargs)       
        self.id=selected_interface_id #equivalent to is_tinyg
        self.Is_Dialog_Open=False   
        self.Setup_Command_Config()
        self.openCommandConfigDialog()   #comment this line to be called only when you want the dialog    
    
    def Setup_Command_Config(self):
        self.CH=class_CH.Command_Handler(self.id)
        self.id=self.CH.id          
        self.Selected_action=None
        self.Num_interfaces=self.CH.Num_interfaces
        self.Selected_action_dict={'action':'','Format':'','Parameters':{},'ReqOpParamsdict':{}}


    def Refresh_viewed_filenames(self):
        self.DCCui.groupBox_CCD_actionFiles.setTitle("Actual Config File:"+self.CH.filename)

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
        self.DCCui.pushButton_CCD_Load_Commands.clicked.connect(self.PB_CCD_Load_Commands)
        self.DCCui.comboBox_CCD_interface.currentIndexChanged.connect(self.ComboBox_Select_interface)
        self.DCCui.comboBox_CCD_action.currentIndexChanged.connect(self.ComboBox_Select_action)
        self.DCCui.pushButton_CCD_actionTest.clicked.connect(self.PB_CCD_actionTest)
        self.DCCui.pushButton_CCD_actionAdd.clicked.connect(self.PB_CCD_actionAdd)
        self.DCCui.pushButton_CCD_actionDel.clicked.connect(self.PB_CCD_actionDel)
        #self.DCCui.label_CCD_testResultFormat.left_clicked[int].connect(self.left_click_P)
        #self.DCCui.label_CCD_testResultFormat.right_clicked[int].connect(self.right_click_P)

    def PB_CCD_actionDel(self):
        action=self.DCCui.lineEdit_CCD_action.text()
        if action == '':
            msgtxt="No action to Delete!"
            logging.error(msgtxt)
            self.DCCui.label_CCD_testResult.setText(msgtxt)
            return
        if action == 'interfaceId':
            msgtxt=="Can't change this action"
            logging.error(msgtxt)
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
                if formatlist[jjj] is not '' and  idlist[jjj]!= self.id:
                    msgtxt="Can't delete this action. Formats in other ids!"
                    logging.error(msgtxt)
                    self.DCCui.label_CCD_testResult.setText(msgtxt)
                    delonlyFormat=True
                    break       
        #check if is required action     
        if knownaction==True and delonlyFormat==False:
            reqactions=self.CH.Required_actions
            for reqa in reqactions:
                if action is reqa:
                    msgtxt="Can't delete this action, is a Required action!"
                    logging.error(msgtxt)
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
                self.Replace_Format_in_ConfigFile(self.CH.filename,action,'',self.id) 
                msgtxt=msgtxt="action:  "+action+" Format cleared!"
                logging.info(msgtxt)
                self.DCCui.label_CCD_testResult.setText(msgtxt)   
        #delete only the action       
        if knownaction==True and delonlyFormat==False:             
            result = QtWidgets.QMessageBox.question(self,
                    "Confirm action delete...",
                    "You are about to permanently delete action: "+action+"\n"                    
                    "Are you sure you want to delete the action?",
                    QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.Yes:
                self.Delete_action_in_ConfigFile(self.CH.filename,action) 
                msgtxt=action+" Deleted!"
                logging.info(msgtxt)
                self.DCCui.label_CCD_testResult.setText(msgtxt)   
 
    def PB_CCD_actionAdd(self):
        isok=self.Do_Test_format()
        if isok==True:
            action=self.Selected_action_dict['action']
            if action == '':
                msgtxt="No action to Add!"
                logging.error(msgtxt)
                self.DCCui.label_CCD_testResult.setText(msgtxt)                
                return
            newFormat=self.Selected_action_dict['Format']
            print(action,newFormat)
            if action == 'interfaceId':
                msgtxt="Can't change this action"
                logging.error(msgtxt)
                self.DCCui.label_CCD_testResult.setText(msgtxt)                
                return
            allactions=self.CH.getListofActions(['interfaceId'])
            knownaction=False
            if action in allactions:                
                knownaction=True                    
            print(knownaction)           
            if knownaction==True:    
                oldFormat=self.CH.Get_action_format_from_id(self.CH.Configdata,action,self.id)                    
                result = QtWidgets.QMessageBox.question(self,
                      "Confirm Format Replace...",
                      "Old Format: "+str(oldFormat)+"\nfor New Format: "+ str(newFormat)+"\n"+
                      "Are you sure you want to Replace the Format?",
                      QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
                if result == QtWidgets.QMessageBox.Yes:
                    self.Replace_Format_in_ConfigFile(self.CH.filename,action,newFormat,self.id)
                    msgtxt="action:  "+action+" Format replaced for "+newFormat+" "
                    logging.info(msgtxt)
                    self.DCCui.label_CCD_testResult.setText(msgtxt)      
            else:
                self.Add_New_action_in_ConfigFile(self.CH.filename,action,newFormat,self.id)
                msgtxt=action+" Added!"
                logging.info(msgtxt)
                self.DCCui.label_CCD_testResult.setText(msgtxt)
   
    def Refresh_after_config_File_change(self):
        self.Refresh_viewed_filenames()
        self.Set_Config_info_To_TableWidget()
        #self.Fill_interface_combobox()
        self.Fill_action_combobox()

    def Delete_action_in_ConfigFile(self,afilename,anaction):        
        isok=self.CH.delete_action_in_file(afilename,anaction)
        if isok==True:
            self.file_has_updated(afilename)
            self.Refresh_after_config_File_change()

    def Create_action_in_ConfigFile(self,afilename,anaction,dorefresh=False):        
        isok=self.CH.create_empty_action_in_file(afilename,anaction)
        if dorefresh==True:
            self.Refresh_after_config_File_change()
        return isok    
 
    def Add_New_action_in_ConfigFile(self,afilename,anaction,aFormat,anid):
        isok=self.Create_action_in_ConfigFile(afilename,anaction,False)
        if isok==True:            
            self.Replace_Format_in_ConfigFile(afilename,anaction,aFormat,anid)    #Refresh inside
        
    
    def Replace_Format_in_ConfigFile(self,afilename,anaction,aFormat,anid):
        isok=self.CH.replace_action_format_in_file(afilename,anaction,aFormat,anid)
        if isok==True:
            self.file_has_updated(afilename)
            self.Refresh_after_config_File_change()
        return isok
                
    def PB_CCD_Load_Commands(self):
        self.Set_Config_info_To_TableWidget()
        self.Fill_interface_combobox()
        self.Fill_action_combobox()

    def Set_Config_info_To_TableWidget(self):
        self.DCCui.tableWidget_CCD.clear()
        #Table_NumCols=self.Num_interfaces+1
        Table_NumCols=2
        self.DCCui.tableWidget_CCD.setColumnCount(Table_NumCols)
        
        Table_NumRows=self.CH.Get_Number_of_Actual_Interface_Formats()
        self.DCCui.tableWidget_CCD.setRowCount(Table_NumRows)
        self.DCCui.tableWidget_CCD.setHorizontalHeaderLabels(["action", "Format"])
        self.DCCui.tableWidget_CCD.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)    
        iii=0
        for ccc in self.CH.Actual_Interface_Formats:   
            self.DCCui.tableWidget_CCD.setItem(iii,0, QTableWidgetItem(ccc))
            self.DCCui.tableWidget_CCD.setItem(iii,1, QTableWidgetItem(self.CH.Actual_Interface_Formats[ccc]))
            if ccc in self.CH.Required_actions:
                color=QColor('yellow')
                self.setColortoRow(self.DCCui.tableWidget_CCD, iii, color)                
            iii=iii+1
        self.DCCui.tableWidget_CCD.resizeColumnsToContents()            
    
    def setColortoRow(self,table, rowIndex, color):
        for j in range(table.columnCount()):
            table.item(rowIndex, j).setBackground(color)

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
        allactions=self.CH.getListofActions(['interfaceId'])
        self.DCCui.comboBox_CCD_action.addItem('')
        for iii in allactions:           
            self.DCCui.comboBox_CCD_action.addItem(iii)          
        #index= self.DCCui.comboBox_CCD_action.findText('interfaceName',QtCore.Qt.MatchFixedString)
        index=0
        self.DCCui.comboBox_CCD_action.setCurrentIndex(index)    
        self.CH.Selected_action=self.DCCui.comboBox_CCD_action.currentText()

    def ComboBox_Select_action(self):
        self.Selected_action=self.DCCui.comboBox_CCD_action.currentText()         
        self.DCCui.lineEdit_CCD_action.setText(self.Selected_action)     
        aFormat=self.CH.getGformatforActionid(self.Selected_action,self.id)
        self.DCCui.lineEdit_CCD_action.setText(self.Selected_action)     
        self.DCCui.lineEdit_CCD_Format.setText(aFormat) 
        self.fill_actionParameters_Table(aFormat)
    
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
                    if param == Tpar and Tvalue is not '':
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
    
    def ComboBox_Select_interface(self):
        anid=self.DCCui.comboBox_CCD_interface.currentText()
        if str(anid)!=str(self.CH.id):            
            self.CH.Set_id(str(anid))
            aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.CH.id)
            self.DCCui.label_CCD_interfaceName.setText(aname)  
            self.CH.Setup_Command_Handler(False)   #Refresh info in CH    
            #self.Set_Config_info_To_TableWidget()                 
            self.id=self.CH.id  
            self.Refresh_after_config_File_change()

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
        #print(self.CH.get_action_from_gcode(Gcodeline))
        #Gcodeline='G0 X0.5 Z3 Y0.8'
        #print(self.CH.get_action_from_gcode(Gcodeline))
        #Gcodeline='G0 X0.5 Z0.8 Y3'
        #print(self.CH.get_action_from_gcode(Gcodeline))
        #Gcodeline='G0 Z8'
        #print(self.CH.get_action_from_gcode(Gcodeline))
        #Gcodeline='G92 X0.5'
        #print(self.CH.get_action_from_gcode(Gcodeline))
        Gcodeline='G91 G0 X0.5 Y0.8 Z3'
        print(self.CH.get_action_from_gcode(Gcodeline))
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



