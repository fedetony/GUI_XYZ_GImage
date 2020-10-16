
import re
import logging
#from types import *

class Command_Handler:    
    def __init__(self,selected_interface_id,configfile=None,Required_actions={'interfaceId'}):            
        self.Set_id(selected_interface_id)
        self.Required_actions=Required_actions
        if configfile==None:
            self.filename='config/MachineCommandConfig.config'
        else:
            self.filename=configfile    
        self.Setup_Command_Handler()
            
    def Set_id(self,selected_interface_id):
        self.id=str(selected_interface_id) #equivalent to is_tinyg

    def Setup_Command_Handler(self):        
        fileok=self.Check_command_config_file_Content(self.filename,self.Required_actions)
        #open file .config
        if fileok==False:
            logging.error('Configuration File contains Errors! Configuration Will not be loaded!')
            self.Configdata={}
            self.Actual_Interface_Formats={}
            self.Num_interfaces=0
            return
        self.Configdata=self.Load_command_config_from_file()
        #read configurations
        #get number of configurations from interfaceId
        self.Num_interfaces=self.get_number_of_interfaces(self.Configdata)
        #get action dictionary of selected Id {'action'=stringformat}                
        self.Actual_Interface_Formats={}
        if self.Check_id_in_Config(self.id)==True:
            self.Actual_Interface_Formats=self.get_interface_config(self.Configdata,self.id)
    
    def Check_id_in_Config(self,id):
        try:
            isok=False
            newid=str(id)
            idlist=self.Configdata['interfaceId']
            #print(idlist,' Desired id->',newid)
            if newid in idlist:
                isok=True
            if newid==self.id and isok==False:
                self.Set_id(idlist[0])
                logging.error('None existing Id changed to ', self.id)
                isok=True
        except Exception as e:
            logging.error(e)
            logging.error('Invalid Machine Id!!!!!')
            isok=False
            pass    
        return isok

    

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
        self.Set_id(interface_id)        

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
        
    def get_number_of_actions(self):
        return self.Get_Number_of_Actual_Interface_Formats()

    def get_number_of_actions_in_Data(self,data):
        Num=0
        for jjj in data:
            #print(jjj)
            Num=Num+1
        return Num    

    def Get_Number_of_Actual_Interface_Formats(self):
        Num=0
        for jjj in self.Actual_Interface_Formats:
            #print(jjj)
            Num=Num+1
        return Num    

    def Load_command_config_from_file(self):        
        filename=self.filename
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
            Nomismatch=self.Check_one_Parenthesees(line,IniP='<',EndP='>')  
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
                if Nomismatch==False:
                    logging.info('Parenthesees <> Mismatch in:'+actionname)
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

    def getGformatforActionid(self,action,id):
        ActionFormat=None
        try:       
            formatlist=self.Configdata[action]  
            if self.Check_id_in_Config(id)==True:   
                idcol=self.Get_interface_column_from_id(self.Configdata,id)
                if idcol!=None:
                    ActionFormat=formatlist[idcol]
        except:
            pass
        return ActionFormat

    def getListofActions(self):        
        alist=[]
        for action in self.Actual_Interface_Formats:
            alist.append(action)
        return alist              
    
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

    def get_text_split_separatorfromregex(self,regex_sep):
        ppp=re.findall(regex_sep,'[({<>})]')
        if len(ppp)>0:
            return ppp[0] #separate first
        else:
            return regex_sep
    
    def get_list_in_between_txt(self,txt,inis,ends):
        alist=[]
        astr=''
        doappend=False
        count=0
        for achar in txt:
            if achar==ends and inis!=ends:
                doappend=False
            if achar==inis and inis!=ends:
                doappend=True
                count=count+1
            if inis==ends and achar==ends:
                doappend= not doappend   
            if doappend==True:
                if achar!=inis and achar!=ends:
                    astr=astr+achar    
            if  doappend==False and count>=1:
                alist.append(astr)
                astr=''
                count=0

        return alist        

    def Format_which_Inside_Parenthesees(self,aFormat,IniP=r'\[',EndP=r'\]'):
        try:
            alist=[]
            Inisep=self.get_text_split_separatorfromregex(IniP)
            Endsep=self.get_text_split_separatorfromregex(EndP)
            #print(Inisep+'hola'+Endsep)
            txtlist,Nopini=self.Split_text(IniP,aFormat) 
            txtlist,Nopend=self.Split_text(EndP,aFormat) 
            #print(Nopini,Nopend)
            if Nopini!=Nopend:
                logging.error('Bad Format '+Inisep+' '+Endsep+' in <'+aFormat+'>')
                #Nopini=0
            #else:    
            #    if Nopini>0:    
            txt=str(aFormat)                             
            alist=self.get_list_in_between_txt(txt,Inisep,Endsep)    
            Nopini=len(alist)              
        except Exception as e:            
            logging.error(e)     
            logging.error('Inside Parentheses')                        
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

    def Get_Gcode_for_Action(self,action,Parameters={},Parammustok=True):
        Gcode=''
        if self.Is_action_in_Config(action)==True:
            aFormat=self.getGformatforAction(action)
            print(aFormat)  
            paramok=self.Are_Parameters_ok(action,Parameters)
            print('Paramok=',paramok)
            if paramok==True or Parammustok==False:
                Gcode=self.Get_code(aFormat,Parameters)
        else:
            logging.error('No action defined as '+action+' in configuration file!')    
        return Gcode    

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

    def Get_list_of_all_parameters_in_interface(self,interface_id):
        action_list=self.getListofActions()
        allParams=[]
        for action in action_list:
            ParamsReca=self.Get_Parameters_Needed_for_action(action,interface_id)
            for ParaR in ParamsReca:
                if ParaR not in allParams:
                    allParams.append(ParaR) 
        return allParams           
    
    def Get_Parameters_Needed_for_action(self,action,interface_id):
        Params={}
        if self.Is_action_in_Config(action)==False:
            logging.error('action missing to get needed Parameters!')
            return Params
        aFormat=self.Get_action_format_from_id(self.Configdata,action,interface_id)
        newFormat=''
        count=0
        while aFormat!=newFormat:
            if count>0:
                aFormat=newFormat
            newFormat=self.Format_replace_actions(aFormat)        
            count=count+1            
            if count>20:
                aFormat=newFormat
        #print(newFormat)
        allvarlist,Numallvar=self.Format_which_Inside_Parenthesees(newFormat,r'\{',r'\}')  
        optionslist,Numoptions=self.Format_which_Inside_Parenthesees(newFormat) #in []
        opvarlist=[]        
        atleast=[]        
        #print(allvarlist,Numallvar)
        #print(optionslist,Numoptions)
        addatleast=False
        for option in optionslist:  
            if '&&' in option:
                addatleast=True   
                optxt=option
            varoptlist,Numspeciopt=self.Format_which_Inside_Parenthesees(option,r'\{',r'\}') #in []             
            for opjjj in varoptlist:                
                if addatleast==True:       
                    atleast.append([opjjj,optxt])                   
                opvarlist.append(opjjj)
        #print('OP:',opvarlist,'-AND-All:',allvarlist)    
        for avar in allvarlist:
            if avar in opvarlist:
                Params.update({avar: 'optional' })
                for aaa in atleast:
                    if avar in aaa:
                        Params.update({avar: 'optional'+aaa[1] })
                        break
            else:
                Params.update({avar: 'required' })    
        return Params

    def Is_action_in_Config(self,action):
        alist=self.getListofActions()
        if action in alist:
            return True
        else:
            return False    

    def Are_Parameters_ok(self,action,Parameters):   
        if self.Is_action_in_Config(action)==False:
            return False
        RequiredParams=self.Get_Parameters_Needed_for_action(action,self.id)     
        minimum_required=0
        minimum_oprequired=0
        for reqParam in RequiredParams:
            if '&&' in RequiredParams[reqParam]:
                oplistmin,Numopmin=self.Format_which_Inside_Parenthesees(RequiredParams[reqParam],r'\(',r'\)') 
                for opjjj in oplistmin:
                        minimum_oprequired=int(opjjj)             
            if 'required' in RequiredParams[reqParam]:           
                minimum_required=minimum_required+1
        minimum_req_total=minimum_required+minimum_oprequired            
        if minimum_req_total==0:
            return True
        required_found=0
        optional_found=0    
        for reqParam in RequiredParams:
            if 'required' in RequiredParams[reqParam]: 
                if reqParam in Parameters:
                    required_found=required_found+1
                else:
                    return False    
            if 'optional' in RequiredParams[reqParam]: 
                if reqParam in Parameters:
                    optional_found=optional_found+1
        if required_found==minimum_required and optional_found>=minimum_oprequired:
            return True
        return False
    
    def Check_command_config_file_Content(self,filename,Reqactions,Checkstrickt=False):
        #filename=self.filename        
        data={}
        if filename is not None:            
            
            logging.info('Checking configuration in:'+filename)
            try:                
                with open(filename, 'r') as yourFile:
                    #self.plaintextEdit_GcodeScript.setText(yourFile.read())        #textedit
                    linelist=yourFile.readlines() #makes list of lines  
                data=self.Get_Command_Config_Data_From_List(linelist)                                                
                yourFile.close()
            except Exception as e:
                logging.error(e)
                logging.info("File"+filename+" could not be Checked!")
                pass        
            achk=self.Check_num_actions_in_Data(data)
            if achk==False:
                return False      
            logging.info('\t-Minimum Amount Check Passed:'+str(achk))                      

            achk=self.Check_id_in_Data(data,1)
            if achk==False:
                return False      
            logging.info('\t-Id Check Passed:'+str(achk))    
            
            achk=self.Check_number_Formats_in_Data(data)
            if achk==False:
                return False      
            logging.info('\t-Amount of Formats Check Passed:'+str(achk))    
            
            achk=self.Check_Req_actions_are_in_Data(Reqactions,data)
            if achk==False:
                return False      
            logging.info('\t-Required actions Check Passed:'+str(achk))    

            achk=self.Check_Parenthesees_in_all_Formats(data)
            if achk==False and Checkstrickt==True:
                return False   
            logging.info('\t-Parenthesees Check Passed:'+str(achk)) 

            return True
                
        logging.error('No file to Check')    
        return False

    def Check_id_in_Data(self,data,min_interfaces=1):                    
        try:
            idlist=data['interfaceId']
            idlistfound=True            
        except Exception as e:
            #logging.error(e)
            logging.error("No 'interfaceId' defined in configuration File!")
            idlistfound=False            
            pass
        if idlistfound==True:
            Numinter=self.get_number_of_interfaces(data)
            if Numinter<min_interfaces or Numinter==None:
                logging.error('At least '+str(min_interfaces)+ " interfaces must be defined in 'interfaceId' ")
                return False  
            compidlist=[]      
            for ids in idlist:
                if ids in compidlist:
                    logging.error('Repeated id '+str(ids)+ " in 'interfaceId'. Unique id is required!")
                    return False  
                else:
                    compidlist.append(ids)                         
        return True

    def Check_num_actions_in_Data(self,data):                    
        numactions=self.get_number_of_actions_in_Data(data)
        if numactions<1:
            logging.error('No actions found in File!')
            return False
        return True    

    def Check_Req_actions_are_in_Data(self,Reqactions,data):
        allok=True
        for reqa in Reqactions:
            if reqa not in data:
                logging.error('Missing required action:' + str(reqa))
                allok=False
        return allok        
   
    def Check_number_Formats_in_Data(self,data):                
        Numinter=self.get_number_of_interfaces(data)
        allok=True
        if Numinter!=None and Numinter>0:  
            for ddd in data:
                alist=data[ddd]
                intfound=len(alist)        
                if Numinter>intfound:
                    logging.error('Missing ' +str(Numinter-intfound) +' interface(s) on action: '+ddd)
                    allok=False
        return allok            
    def Nums_Parenthesees(self,txt,IniP,EndP):
        
        txtlist,Nopini=self.Split_text(IniP,txt) 
        txtlist,Nopend=self.Split_text(EndP,txt) 
        #print(Nopini,Nopend)
        return [Nopini,Nopend]

    def Check_one_Parenthesees(self,aFormat,IniP=r'\[',EndP=r'\]',logerr=True):
        try:            
            Inisep=self.get_text_split_separatorfromregex(IniP)
            Endsep=self.get_text_split_separatorfromregex(EndP)
            
            [Nopini,Nopend]=self.Nums_Parenthesees(aFormat,IniP,EndP)
            
            if Nopini!=Nopend:
                if logerr==True:
                    logging.error('Bad Format '+Inisep+' '+Endsep+' in <'+aFormat+'>')
                return False
            return True
        except:
            logging.error('Bad Parenthesees Format '+Inisep+' '+Endsep+' in <'+aFormat+'>')
            pass
        return False
    
    def Check_entangled_Parenthesees(self,txt,logerr=False):
        p1list,Nump1=self.Format_which_Inside_Parenthesees(txt,r'\{',r'\}')  
        [Np1ini,Np1end]=self.Nums_Parenthesees(txt,r'\{',r'\}')
        [Np2ini,Np2end]=self.Nums_Parenthesees(txt,r'\[',r'\]')
        [Np3ini,Np3end]=self.Nums_Parenthesees(txt,r'\(',r'\)')
        if Np1ini==Np1end and Np2ini==Np2end and Np3ini==Np3end:
            if Np1ini==0 and Np2ini==0 and Np3ini==0:
                return True
            elif Np1ini>0 and Np2ini==0 and Np3ini==0:
                return True    
            elif Np1ini==0 and Np2ini>0 and Np3ini==0:
                return True
            elif Np1ini==0 and Np2ini==0 and Np3ini>0:
                return True    
            elif Np1ini>0 and Np2ini>0:
                p1list,Nump1=self.Format_which_Inside_Parenthesees(txt,r'\{',r'\}') 
                for ppp1 in p1list:
                    isok=self.Check_entangled_Parenthesees(ppp1,False)
                    if isok == False:
                        return False
            elif Np2ini>0 and Np3ini>0:
                p2list,Nump2=self.Format_which_Inside_Parenthesees(txt,r'\[',r'\]') 
                for ppp2 in p2list:
                    isok=self.Check_entangled_Parenthesees(ppp2,False)
                    if isok == False:
                        return False        
                return True    
            elif Np1ini>0 and Np3ini>0:
                p3list,Nump3=self.Format_which_Inside_Parenthesees(txt,r'\(',r'\)') 
                for ppp3 in p3list:
                    isok=self.Check_entangled_Parenthesees(ppp3,False)
                    if isok == False:
                        return False        
                return True        
            

        else:
            if logerr==True:
                logging.error('Different amounts of opening and closing Parenthesees')
            return False

        for p1 in p1list:
            p2list,Nump2=self.Format_which_Inside_Parenthesees(p1,r'\[',r'\]') 
            p3list,Nump3=self.Format_which_Inside_Parenthesees(p1,r'\(',r'\)') 
            for p2 in p2list:
                p2check=Check_one_Parenthesees(p2,IniP=r'\(',EndP=r'\)',logerr=False)
            for p3 in p3list:
                p3check=Check_one_Parenthesees(p2,IniP=r'\(',EndP=r'\)',logerr=False)    
        

    def Check_Parenthesees_in_all_Formats(self,data):
        allok=True
        for ddd in data:
            alist=data[ddd]
            for aFor in alist:
                P1=self.Check_one_Parenthesees(aFor,IniP=r'\[',EndP=r'\]',logerr=False)
                if P1==False:
                    logging.error('Parenthesees Mismatch "[ ]" in action: '+ddd+ ' Format <'+ aFor+'>')
                    allok=False
                P2=self.Check_one_Parenthesees(aFor,IniP=r'\(',EndP=r'\)',logerr=False)
                if P2==False:
                    logging.error('Parenthesees Mismatch "( )" in action: '+ddd+ ' Format <'+ aFor+'>')
                    allok=False
                P3=self.Check_one_Parenthesees(aFor,IniP=r'\{',EndP=r'\}',logerr=False)
                if P3==False:
                    logging.error('Parenthesees Mismatch "{ }" in action: '+ddd+ ' Format <'+ aFor+'>')
                    allok=False
        if allok==True:
            for ddd in data:
                alist=data[ddd]
                for aFor in alist:
                    Pe=self.Check_entangled_Parenthesees(aFor,logerr=False)            
                    if Pe==False:
                        logging.error('Parenthesees Entangled {[( }]) in action: '+ddd+ ' Format <'+ aFor+'>')
                        allok=False

        return allok

                


            



   