from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
import re
import logging
import GuiXYZ_CCD
import class_CH
from types import *

class CommandConfigurationDialog(QWidget,GuiXYZ_CCD.Ui_Dialog_CCD):
    set_clicked= QtCore.pyqtSignal(list)
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
        self.Num_interfaces=self.CH.Num_interfaces

    def quit(self):
        self.Dialog_CCD.close()
        self.Is_Dialog_Open=False
           
    def openCommandConfigDialog(self):
        self.Dialog_CCD = QtWidgets.QDialog()
        self.DCCui = GuiXYZ_CCD.Ui_Dialog_CCD()
        self.DCCui.setupUi(self.Dialog_CCD)        
        self.Dialog_CCD.show()    
        self.Is_Dialog_Open=True    
        self.PB_CCD_set_commands()    
        #Connect buttons
        self.DCCui.pushButton_CCD_set_commands.clicked.connect(self.PB_CCD_set_commands)
        self.DCCui.comboBox_CCD_interface.currentIndexChanged.connect(self.ComboBox_Select_interface)
        self.DCCui.comboBox_CCD_action.currentIndexChanged.connect(self.ComboBox_Select_action)
        self.DCCui.pushButton_test.clicked.connect(self.PB_test)

    def PB_CCD_set_commands(self):
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
            iii=iii+1
        self.DCCui.tableWidget_CCD.resizeColumnsToContents()            

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
        for iii in self.CH.Configdata:           
            self.DCCui.comboBox_CCD_action.addItem(iii)          
        #index= self.DCCui.comboBox_CCD_action.findText('interfaceName',QtCore.Qt.MatchFixedString)
        index=1
        self.DCCui.comboBox_CCD_action.setCurrentIndex(index)    
        self.CH.Selected_action=self.DCCui.comboBox_CCD_action.currentText()

    def ComboBox_Select_action(self):
        self.CH.Selected_action=self.DCCui.comboBox_CCD_action.currentText()       

    def ComboBox_Select_interface(self):
        anid=self.DCCui.comboBox_CCD_interface.currentText()
        if anid!=self.CH.id:            
            self.CH.Set_new_Interface(anid)
            aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.CH.id)
            self.DCCui.label_CCD_interfaceName.setText(aname)         
            self.Set_Config_info_To_TableWidget()       

    def PB_CCD_Set_Preview(self):            
        #print('clicked')
        self.aList=[]
        self.set_clicked.emit(self.aList)

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
    
    def PB_test(self):
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



