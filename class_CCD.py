from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
import re
import logging
import GuiXYZ_CCD

class CommandConfigurationDialog(QWidget,GuiXYZ_CCD.Ui_Dialog_CCD):
    set_clicked= QtCore.pyqtSignal(list)
    #def __init__(self,NumLayers,Selected_Layers,parent=None):    
    #    super().__init__(parent)
    def __init__(self,selected_interface_id, *args, **kwargs):                
        super(CommandConfigurationDialog, self).__init__(*args, **kwargs)       
        self.id=selected_interface_id #equivalent to is_tinyg
        self.Is_Dialog_Open=False     
        #self.openCommandConfigDialog()   #to be called when you want the dialog
        self.Setup_Command_Config()
    
    def Setup_Command_Config(self):
        #open file .config
        self.Configdata=self.Load_command_config_from_file()
        #read configurations
        #get number of configurations from interfaceId
        self.Num_interfaces=self.get_number_of_interfaces(self.Configdata)
        #get action dictionary of selected Id {'action'=stringformat}
        self.Actual_Interface_Formats=self.get_interface_config(self.Configdata,self.id)

    def get_number_of_interfaces(self,data):
        try:
            idlist=data['interfaceId']
        except Exception as e:
            logging.error(e)
            idlist=[]
            pass
        sss=0    
        for ddd in idlist:            
            sss=sss+1
        return sss    
    
    def Set_new_Interface(self,interface_id):
        self.id=interface_id
        self.Setup_Command_Config()

    def Get_interface_column_from_id(self,data,interface_id):
        try:
            idlist=data['interfaceId']
        except Exception as e:
            logging.error(e)
            idlist=[]
            pass
        ccc=0
        for iii in idlist:
            if iii==str(interface_id):
                return ccc
            ccc=ccc+1
        return None

    def get_interface_config(self,data,interface_id):
        alist=[]
        dataint={}    
        Colnum=self.Get_interface_column_from_id(data,interface_id) 
        Numinter=self.get_number_of_interfaces(data)
        if Colnum!=None and  Colnum<=Numinter:  
            for ddd in data:
                alist=data[ddd]        
                dataint[ddd]=alist[Colnum]
        return dataint       

    def quit(self):
        self.Dialog_CCD.close()
        self.Is_Dialog_Open=False
           
    def openCommandConfigDialog(self):
        self.Dialog_CCD = QtWidgets.QDialog()
        self.DCCui = GuiXYZ_CCD.Ui_Dialog_CCD()
        self.DCCui.setupUi(self.Dialog_CCD)        
        self.Dialog_CCD.show()    
        self.Is_Dialog_Open=True         
        #Connect buttons
        self.DCCui.pushButton_CCD_set_commands.clicked.connect(self.PB_CCD_set_commands)

    def PB_CCD_set_commands(self):
        self.Set_Config_info_To_TableWidget()

    def Set_Config_info_To_TableWidget(self):
        self.DCCui.tableWidget_CCD.clear()
        for iii in self.Actual_Interface_Formats:
            print(iii)
            print(self.Actual_Interface_Formats[iii])



    def PB_CCD_Set_Preview(self):            
        #print('clicked')
        self.aList=[]
        self.set_clicked.emit(self.aList)

    def accept(self):
        #print('accepted')        
        return self.Selected_Layers   

    def getGformatforAction(self,action):
        ActionFormat=None
        try:
            ActionFormat=self.Actual_Interface_Formats[action]
        except:
            pass
        return ActionFormat

    def Get_Gcode_for_Action(action,Parameters=None):
        Gcode=''
        return Gcode    

    def Load_command_config_from_file(self):
        #filename=aDialog.openFileNameDialog(2) #0 gcode, 1 Images 2 txt else all 
        filename='config/MachineCommandConfig.config'
        data={}
        if filename is not None:            
            logging.info('Opening:'+filename)
            try:                
                with open(filename, 'r') as yourFile:
                    #self.plaintextEdit_GcodeScript.setText(yourFile.read())        #textedit
                    linelist=yourFile.readlines() #makes list of lines  
                data=self.Get_Command_Config_Data_From_List(linelist)                                                
                yourFile.close()                
            except Exception as e:
                logging.error(e)
                logging.info("Command Configuration File could not be read!")
        return data        
    
    def Get_Command_Config_Data_From_List(self,linelist):
        data={}
        for line in linelist:
            #logging.info(line)            
            lastchar=''
            actionname=''
            item=''
            lineinfolist=[]
            countnum=0
            for achar in line:
                if achar=='#' and countnum==0:                    
                    break
                if achar =='<':
                    #print(countnum)
                    item=''
                    countnum=countnum+1
                elif achar=='>':
                    lastchar=achar    
                    if countnum==1:
                        actionname=item
                    else:
                        lineinfolist.append(item)
                elif achar=='_' and lastchar=='>':
                    lastchar=achar 
                else:    
                    item=item+achar
                lastchar=achar            
            if actionname!='': 
                #logging.info('action:'+actionname)   
                #print(lineinfolist)
                data[actionname]=lineinfolist                             
        return data    

