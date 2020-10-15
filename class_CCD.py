from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
import re
import logging
import GuiXYZ_CCD
from types import *

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
        self.Actual_Interface_Formats={}
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

    def Get_action_format_from_id(self,data,action,interface_id):
        try:
            aclist=data[action]
            idcol=self.Get_interface_column_from_id(data,interface_id)
            if idcol!=None:
                return aclist[idcol]
        except Exception as e:
            logging.error(e)            
            pass        
        return None

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
                #print(dataint[ddd])
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
        self.DCCui.comboBox_CCD_interface.currentIndexChanged.connect(self.ComboBox_Select_interface)
        self.DCCui.pushButton_test.clicked.connect(self.PB_test)

    def PB_CCD_set_commands(self):
        self.Set_Config_info_To_TableWidget()
        self.Fill_interface_combobox()

    def Set_Config_info_To_TableWidget(self):
        self.DCCui.tableWidget_CCD.clear()
        #Table_NumCols=self.Num_interfaces+1
        Table_NumCols=2
        self.DCCui.tableWidget_CCD.setColumnCount(Table_NumCols)
        
        Table_NumRows=self.Get_Number_of_Actual_Interface_Formats()
        self.DCCui.tableWidget_CCD.setRowCount(Table_NumRows)
        self.DCCui.tableWidget_CCD.setHorizontalHeaderLabels(["action", "Format"])
        self.DCCui.tableWidget_CCD.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)    
        iii=0
        for ccc in self.Actual_Interface_Formats:   
            self.DCCui.tableWidget_CCD.setItem(iii,0, QTableWidgetItem(ccc))
            self.DCCui.tableWidget_CCD.setItem(iii,1, QTableWidgetItem(self.Actual_Interface_Formats[ccc]))
            iii=iii+1
        self.DCCui.tableWidget_CCD.resizeColumnsToContents()        
    
    def get_number_of_actions(self):
        return self.Get_Number_of_Actual_Interface_Formats()

    def Get_Number_of_Actual_Interface_Formats(self):
        Num=0
        for jjj in self.Actual_Interface_Formats:
            #print(jjj)
            Num=Num+1
        return Num    

    def Fill_interface_combobox(self):
        self.DCCui.comboBox_CCD_interface.clear()
        for iii in self.Configdata['interfaceId']:           
            self.DCCui.comboBox_CCD_interface.addItem(iii)          
        index= self.DCCui.comboBox_CCD_interface.findText(self.id,QtCore.Qt.MatchFixedString)
        self.DCCui.comboBox_CCD_interface.setCurrentIndex(index)    
        aname=self.Get_action_format_from_id(self.Configdata,'interfaceName',self.id)
        self.DCCui.label_CCD_interfaceName.setText(aname)    

    def ComboBox_Select_interface(self):
        anid=self.DCCui.comboBox_CCD_interface.currentText()
        if anid!=self.id:            
            self.Set_new_Interface(anid)
            aname=self.Get_action_format_from_id(self.Configdata,'interfaceName',self.id)
            self.DCCui.label_CCD_interfaceName.setText(aname)         
            self.Set_Config_info_To_TableWidget()
        

    def PB_CCD_Set_Preview(self):            
        #print('clicked')
        self.aList=[]
        self.set_clicked.emit(self.aList)

    def accept(self):
        #print('accepted')        
        return self.Selected_Layers   

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

    def getGformatforAction(self,action):
        ActionFormat=None
        try:            
            ActionFormat=self.Actual_Interface_Formats[action]
        except:
            pass
        return ActionFormat
    
    def getListofActions(self):        
        alist=[]
        for action in self.Actual_Interface_Formats:
            alist.append(action)
        return alist

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
    
    def Split_text(self,separator,line):
        alist=[]
        count=0
        try:                                      
            mf =re.split(separator,line)                               
            x=re.findall(separator,line)
        except:
            mf = None
            
        try:
            if mf is not None:                  
                for item in mf:                                   
                    #print("Inside vector->"+str(item))
                    alist.append(item)
                    #count=count+1
                if x is not None:
                    count=len(x)     
            else:
                alist.append(line)
        except Exception as e:            
            logging.error(e)                        
            alist=[]
            pass
        return alist,count                   

    def Get_Gcode_for_Action(self,action,Parameters={}):
        Gcode=''
        
        aFormat=self.getGformatforActionfromTable(action)
        #print(aFormat)  
        Gcode=self.Get_code(aFormat,Parameters)
        return Gcode    

    def PB_test(self):
        action='test'    
        Parameters={'X':15,'Y':20.1,'Z':'8','str_var':'X'}    
        Gcode=self.Get_Gcode_for_Action(action,Parameters)
        print(Gcode)        
        self.DCCui.label_test.setText(Gcode)

    def num_groups(self,match):
        if match is not None:
            return len(match.groups())
        else:
            return 0 

    def Format_Number_of_formatspecifiers(self,aFormat):        
        NS=0
        NSC=0
        txtlist,NSC=self.Split_text(r'\%\%',aFormat)        
        txtlist,NS=self.Split_text(r'\%',aFormat)

        amounts=[NS-NSC,NSC]
        return amounts


    def Format_which_Inside_Parenthesees(self,aFormat,IniP=r'\[',EndP=r'\]'):
        try:
            alist=[]
            txtlist,Nopini=self.Split_text(IniP,aFormat) 
            txtlist,Nopend=self.Split_text(EndP,aFormat) 
            if Nopini!=Nopend:
                #logging.error('Bad Format [] in '+aFormat)
                Nopini=0
            else:    
                if Nopini>0:    
                    txt=str(aFormat)            
                    for jjj in range(Nopini):
                        ppp=re.findall(IniP,'[({<>})]')
                        if len(ppp)>0:
                            sTxtlist = txt.split(ppp[0],1) #separate first
                        else:
                            sTxtlist = txt.split(IniP,1) #separate first
                        stxt=sTxtlist[1]
                        ppp=re.findall(EndP,'[({<>})]')
                        if len(ppp)>0:
                            ilist=stxt.split(ppp[0])    
                        else:
                            ilist=stxt.split(EndP)                        
                        item=ilist[0]
                        if len(ilist)>1:
                            txt=ilist[1]
                        alist.append(item)                    
        except Exception as e:            
            logging.error(e)                        
            alist=[]
            Nopini=0
            pass            
        return alist,Nopini
    
    def Format_Get_main_Command(self,aFormat,Numoptions=None):
        if Numoptions==None:
            optionslist,Numoptions=self.Format_which_Inside_Parenthesees(aFormat)
        if Numoptions==0:
            return aFormat
        else:
            txt=str(aFormat)  
            sTxtlist = txt.split('[',1) #separate first
            stxt=sTxtlist[0]
            return stxt
    
    def Format_Get_options(self,aFormat,Parameters):
        orsplit,Norsplit=self.Split_text(r'\]\|\|\[',aFormat)
        if Norsplit>0:
            newFormat=aFormat            
            for iii in range(len(orsplit)):
                #print(str(iii)+'-->'+newFormat)                
                split1=newFormat.split(']||[',1)
                #print(split1)
                if len(split1)>1:
                    before=split1[0]+']'
                    after='['+split1[1]
                else:
                    break                        
                beflistop,Numbefopt=self.Format_which_Inside_Parenthesees(before)
                aftlistop,Numaftopt=self.Format_which_Inside_Parenthesees(after)
                varlistb,Numspecimain=self.Format_which_Inside_Parenthesees(beflistop[Numbefopt-1],r'\{',r'\}')
                Isonlistb=self.Check_all_Parameters_are_in_list(varlistb,Parameters)
                varlista,Numspecimain=self.Format_which_Inside_Parenthesees(aftlistop[0],r'\{',r'\}')
                Isonlista=self.Check_all_Parameters_are_in_list(varlista,Parameters) 
                if Isonlistb==False and Isonlista==False:
                    if '&&' not in beflistop[Numbefopt-1]:
                        before=before.replace('['+beflistop[Numbefopt-1]+']','')
                    else:    
                        if '&&' not in aftlistop[0]:
                            after=after.replace('['+aftlistop[0]+']','')    
                elif Isonlistb==True and Isonlista==False:                    
                    after=after.replace('['+aftlistop[0]+']','')                         
                elif Isonlistb==False and Isonlista==True:                                            
                    before=before.replace('['+beflistop[Numbefopt-1]+']','')           
                elif Isonlistb==True and Isonlista==True:
                    if '&&' not in aftlistop[0]:
                        after=after.replace('['+aftlistop[0]+']','')    
                newFormat=before+after                            
                    
            return newFormat                
        else:
            return aFormat
    
    def Format_replace_actions(self,aFormat):
        varlist,Numvars=self.Format_which_Inside_Parenthesees(aFormat,r'\{',r'\}') 
        action_list=self.getListofActions()
        newFormat=aFormat
        try:
            for var in varlist:
                if 'char(' in var:
                    vlist,Numv=self.Format_which_Inside_Parenthesees(var,r'\(',r'\)')                     
                    try:
                        if Numv>0:
                            valstr=vlist[0]
                            if '0x' in valstr:                                
                                hex_str=valstr                                
                                hex_int = int(hex_str, base=16)                                  
                                int_int=int(hex_int)
                                fff=chr(int_int)                                                          
                            else:                                
                                fff=chr(int(valstr))
                    except Exception as e:            
                        logging.error(e)                        
                        fff=''
                        pass
                    if fff is not None:    
                        newFormat=newFormat.replace('{'+var+'}',fff)    
                for action in action_list:
                    if action in var:
                        vlist,Numv=self.Format_which_Inside_Parenthesees(var,r'\(',r'\)') 
                        if Numv>0:                        
                            fff=self.Get_action_format_from_id(self.Configdata,action,vlist[0])
                            #print('here1:'+str(fff))
                        else:
                            #print(action)
                            fff=self.Get_action_format_from_id(self.Configdata,action,self.id)    
                            #print('here2:'+str(fff))
                        if fff is not None:    
                            if 'char(' in fff:
                                fff='{'+fff+'}'
                            newFormat=newFormat.replace('{'+var+'}',fff)
        except Exception as e:            
            logging.error(e)                        
            newFormat=aFormat
            pass                     
        return newFormat
    
    def Get_code(self,aFormat,Parameters):
        try:
            countnumoptions=0
            Numvarleft=1   
            newFormat=aFormat         
            while Numvarleft>0:            
                newFormat=self.Format_replace_actions(newFormat)
                newFormat=self.Format_Get_options(newFormat,Parameters)        
                optionslist,Numoptions=self.Format_which_Inside_Parenthesees(newFormat)
                The_code=''
                MCommand=self.Format_Get_main_Command(newFormat,Numoptions)
                varlist,Numspecimain=self.Format_which_Inside_Parenthesees(MCommand,r'\{',r'\}') #in []                        
                astr=MCommand
                #areallparams=self.Check_all_Parameters_are_in_list(varlist,Parameters,True)   #Log when missing parameter in main
                areallparams=self.Check_all_Parameters_are_in_list(varlist,Parameters)   
                if areallparams==True:
                    params=self.Get_only_the_Parameters_in_list(varlist,Parameters)
                    if Numspecimain>0:
                        astr=MCommand.format(**params)
                        #print(astr)
                    else:
                        astr=MCommand
                The_code=newFormat.replace(MCommand,astr)        
                minnumoptions=0        
                minop=None
                for option in optionslist:
                    if '&&' in option:
                        minvaluelist,Numminval=self.Format_which_Inside_Parenthesees(option,r'\(',r'\)') #in [] 
                        minop=option
                        if Numminval>0:
                            minnumoptions=int(minvaluelist[0])
                        else:
                            minnumoptions=1
                for option in optionslist:                
                    varoptlist,Numspeciopt=self.Format_which_Inside_Parenthesees(option,r'\{',r'\}') #in [] 
                    isoptparam=self.Check_all_Parameters_are_in_list(varoptlist,Parameters)
                    optstr=''
                    if isoptparam==True:                
                        params=self.Get_only_the_Parameters_in_list(varoptlist,Parameters)                
                        if Numspeciopt>0:
                            optstr=option.format(**params)
                            astr=astr+optstr                    
                            countnumoptions=countnumoptions+1
                    if minop is option:
                        if countnumoptions>=minnumoptions:
                            The_code=The_code.replace('['+minop+']','')                                    
                    The_code=The_code.replace('['+option+']',optstr)            
                varcode,Numvarleft=self.Format_which_Inside_Parenthesees(The_code,r'\{',r'\}')            
                #logging.info('Required '+ str(minnumoptions)+' Option parameters, '+str(countnumoptions)+' found!')  
                #self.countnumoptions=countnumoptions      
                #if Numvarleft>0:            
                #    The_code=self.Get_code(The_code,Parameters,countnumoptions)
                newFormat=The_code    
                #params={}
                #for iii in range(Numspecimain):
                #        params.update({varlist[iii]: iii*10})            
                #countnumoptions=self.countnumoptions
            if countnumoptions<minnumoptions:
                logging.error('Minimum '+ str(minnumoptions)+' Option parameters are Required: '+str(countnumoptions)+' found! '+str(minnumoptions-countnumoptions)+' missing!')        
        
        except Exception as e:            
            logging.error(e)                        
            #The_code=''
            pass        
        return The_code    

    def Check_all_Parameters_are_in_list(self,varlist,Parameters,elog=False):
        isinparams=True
        for var in varlist:
            isinparams=False                
            for param in Parameters:            
                if var==param:
                    isinparams=True
                    break   
            if isinparams==False:
                if elog==True:
                    logging.error('Missing parameter:'+var)
                break                                  
        return isinparams

    def Get_only_the_Parameters_in_list(self,varlist,Parameters):        
        Pardict={}
        #print(Parameters)
        for var in varlist:            
            for param in Parameters:            
                if var==param:
                    Pardict.update({var: Parameters[param]})           
                    break        
        #print(Pardict)                                                 
        return  Pardict    
               



        
                
                    

        

