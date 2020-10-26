
import re
import logging
import fileinput
#from types import *

class Command_Handler:    
    def __init__(self,selected_interface_id,configfile=None,Required_actions={'interfaceId'}):            
        self.Set_id(selected_interface_id)
        self.Required_actions=Required_actions
        if self.Set_all_Filenames(configfile)==True:                    
            self.Setup_Command_Handler()
            self.Init_Read_Interface_Configurations()

    def Set_all_Filenames(self,configfilelist):
        try:
            self.filename=configfile[0]    
            self.Interfacefilename=configfile[1]
            self.Readfilename=configfile[2]
            return True
        except:    
            configfile=None 
            pass
        if configfile==None:
            self.filename='config/defaultConfig.cccfg'
            self.Interfacefilename='config/defaultConfig.iccfg'    
            self.Readfilename='config/defaultConfig.rccfg'   
            return True
        return False    
        


    def Set_Interfacefilename(self,filename):
        self.Interfacefilename=filename
    
    def Set_Readfilename(self,filename):
        self.Readfilename=filename

    def Set_id(self,selected_interface_id):
        self.id=str(selected_interface_id) #equivalent to is_tinyg

    def Setup_Command_Handler(self,log_check=True):        
        fileok=self.Check_command_config_file_Content(self.filename,self.Required_actions,logcheck=log_check)
        #open file .config
        if fileok==False:
            logging.error('Configuration File contains Errors! Configuration Will not be loaded!')
            self.Configdata={}
            self.Actual_Interface_Formats={}
            self.Num_interfaces=0
            return 
        self.Configdata=self.Load_command_config_from_file(Logopen=log_check)
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
    
    #def Set_new_Interface(self,interface_id):
    #    self.Set_id(interface_id)        

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

    def Load_command_config_from_file(self,filename=None,Logopen=False):       
        if filename is None: 
            filename=self.filename
        data={}
        if filename is not None:            
            if Logopen==True:
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
            regextxt=''
            isregex=False
            for achar in line:
                if achar=='#' and countnum==0:                    
                    break
                if achar=='r' and lastchar=='<':
                   regextxt=='r'
                if achar=="'" and lastchar=='r' and isregex==False:
                    isregex=True
                    regextxt=regextxt+achar
                elif achar=="'" and isregex==True:
                    isregex=False    
                
                if (achar =='<' or achar=='>') and isregex==True:
                    Nomismatch=True
                    #item=item+achar
                if achar =='<' and isregex==False:
                    #print(countnum)
                    item=''
                    countnum=countnum+1
                elif achar=='>' and isregex==False:
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
    
    def getGformatforReadactionid(self,action,id):
        ActionFormat=None
        try:       
            formatlist=self.ReadConfigallids[action]  
            if self.Check_id_in_Config(id)==True:   
                idcol=self.Get_interface_column_from_id(self.ReadConfigallids,id)
                if idcol!=None:
                    ActionFormat=formatlist[idcol]
        except:
            pass
        return ActionFormat

    def getListofActions(self,exceptlist=[]):        
        alist=[]
        for action in self.Actual_Interface_Formats:
            if action not in exceptlist:
                alist.append(action)
        return alist    

    def getListofReadactions(self,exceptlist=[]):        
        alist=[]
        for action in self.Read_Config:
            if action not in exceptlist:
                alist.append(action)
        return alist              
    
    def getListofInterfaceactions(self,exceptlist=[]):        
        alist=[]
        for action in self.Int_Config:
            if action not in exceptlist:
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
        aFormat=str(aFormat)     
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
        aFormat=str(aFormat)
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
    
    def Format_Get_optionlist_parameterlist(self,aFormat):
        aFormat=str(aFormat)
        minnumoptions=0
        optionslist,Numoptions=self.Format_which_Inside_Parenthesees(aFormat)
        for option in optionslist:
            if '&&' in option:
                minvaluelist,Numminval=self.Format_which_Inside_Parenthesees(option,r'\(',r'\)') #in [] 
                minop=option
                if Numminval>0:
                    minnumoptions=int(minvaluelist[0])
                else:
                    minnumoptions=1
        paramlist=[]            
        for option in optionslist:                
            varoptlist,Numspeciopt=self.Format_which_Inside_Parenthesees(option,r'\{',r'\}') #in [] 
            for jjj in varoptlist: 
                paramlist.append(jjj)    
        # remove &&(#) option
        oplist=[]
        for jjj in optionslist:
            if '&&' not in jjj:
                oplist.append(jjj)    
        optionslist=oplist                    
        return optionslist,paramlist,minnumoptions


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
    
    def Format_select_options_ored_parameters(self,aFormat,Parameters):
        aFormat=str(aFormat)
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
        aFormat=str(aFormat)
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
        paramok=False        
        if self.Is_action_in_Config(action)==True:
            aFormat=self.getGformatforAction(action)
            #print(aFormat)  
            paramok=self.Check_Parameters_for_Action(action,Parameters)
            #print('Paramok=',paramok)
            if paramok==True or Parammustok==False:
                Gcode=self.Get_code(aFormat,Parameters)
        else:
            logging.error('No action defined as '+action+' in configuration file!')    
        return Gcode,paramok    

    def Get_code(self,aFormat,Parameters):
        aFormat=str(aFormat)        
        try:
            countnumoptions=0
            Numvarleft=1   
            newFormat=aFormat         
            while Numvarleft>0:            
                newFormat=self.Format_replace_actions(newFormat)
                newFormat=self.Format_select_options_ored_parameters(newFormat,Parameters)        
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
        Params=self.Get_Parameters_Needed_for_Format(aFormat) 
        return Params

    def Get_Parameters_Needed_for_Format(self,aFormat):
        aFormat=str(aFormat)
        Params={}                
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
        opvarlist,atleast=self.Get_option_list(newFormat)

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

    def Check_Parameters_for_Action(self,action,Parameters):   
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
    
    def Check_Parameters_for_Format(self,aFormat,Parameters):     
        #print('Format checking...')      
        RequiredParams=self.Get_Parameters_Needed_for_Format(aFormat)     
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

    def Check_command_config_file_Content(self,filename,Reqactions,Checkstrickt=False,logcheck=True):
        #filename=self.filename        
        data={}
        if filename is not None:            
            if logcheck==True:
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
            if logcheck==True:    
                logging.info('\t-Minimum Amount Check Passed:'+str(achk))                      
            if achk==False:
                return False      
            
            achk=self.Check_id_in_Data(data,1)
            if logcheck==True:
                logging.info('\t-Id Check Passed:'+str(achk))    
            if achk==False:
                return False      
            
            
            achk=self.Check_number_Formats_in_Data(data)
            if logcheck==True:
                logging.info('\t-Amount of Formats Check Passed:'+str(achk))    
            if achk==False:
                return False      
            
            
            achk=self.Check_Req_actions_are_in_Data(Reqactions,data)
            if logcheck==True:
                logging.info('\t-Required actions Check Passed:'+str(achk))    
            if achk==False:
                return False                  

            achk=self.Check_Parenthesees_in_all_Formats(data)
            if logcheck==True:
                logging.info('\t-Parenthesees Check Passed:'+str(achk)) 
            if achk==False and Checkstrickt==True:
                return False   

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
        aFormat=str(aFormat)
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
                    #print('+1 depth')
                    if txt!=ppp1:
                        isok=self.Check_entangled_Parenthesees(ppp1,False)
                        
                    if isok == False:
                        return False
            elif Np2ini>0 and Np3ini>0:
                p2list,Nump2=self.Format_which_Inside_Parenthesees(txt,r'\[',r'\]') 
                for ppp2 in p2list:
                    #print('+2 depth')
                    if txt!=ppp2:
                        isok=self.Check_entangled_Parenthesees(ppp2,False)

                    if isok == False:
                        return False        
                return True    
            elif Np1ini>0 and Np3ini>0:
                p3list,Nump3=self.Format_which_Inside_Parenthesees(txt,r'\(',r'\)') 
                for ppp3 in p3list:
                    if txt!=ppp3:
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
    
    def Check_Parenthesees_in_one_Format(self,aFormat):
        allok=True
        aFor=str(aFormat)
        P1=self.Check_one_Parenthesees(aFor,IniP=r'\[',EndP=r'\]',logerr=False)
        if P1==False:
            logging.error('Parenthesees Mismatch "[ ]" in Format <'+ aFor+'>')
            allok=False
        P2=self.Check_one_Parenthesees(aFor,IniP=r'\(',EndP=r'\)',logerr=False)
        if P2==False:
            logging.error('Parenthesees Mismatch "( )" in Format <'+ aFor+'>')
            allok=False
        P3=self.Check_one_Parenthesees(aFor,IniP=r'\{',EndP=r'\}',logerr=False)
        if P3==False:
            logging.error('Parenthesees Mismatch "{ }" in Format <'+ aFor+'>')
            allok=False
        if allok==True:
            Pe=self.Check_entangled_Parenthesees(aFor,logerr=False)            
            if Pe==False:
                logging.error('Parenthesees Entangled {[( }]) in Format <'+ aFor+'>')
                allok=False

        return allok
    def Check_id_match_configs(self,data1,data2):
        isok=True
        try:
            d1list=data1['interfaceId']
            d2list=data2['interfaceId']
            if len(d1list)!=len(d2list):
                logging.error('interfaceId with different amount of items!')    
                return False
            for l1 in d1list:
                if l1 not in d2list:
                    logging.error('id '+str(l1) +' Not found in one interfaceId configurations!')    
                    return False    
        except:
            logging.error('No interfaceId found!')    
            isok=False
            pass
        return isok

    def fill_parameters(self,parnamelist,parvallist):
        numpar=len(parnamelist)
        numval=len(parvallist)
        if numpar!=numval:
            numpar=min(numpar,numval)
            numval=numpar            
        param={}    
        if numpar>0:
            parlist={}
            for iii in range(numpar):
                parlist.update({parnamelist[iii]:parvallist[iii]})
            allparams=self.Get_list_of_all_parameters_in_interface(self.id)            
            try:
                for par in parnamelist:
                    if par in allparams:
                        param.update({par:parlist[par]})
            except:
                pass
        return param    
    
    def Get_list_of_all_parameters_all_interfaces(self):
        allid=self.getGformatforAction('interfaceId')
        allparams=[]
        for ids in allid:
            aparams=self.Get_list_of_all_parameters_in_interface(ids)
            for ppp in aparams:
                if ppp not in allparams:
                    allparams.append(ppp)
        return allparams    

    def Get_option_list(self,aFormat):
        aFormat=str(aFormat)
        optionslist,Numoptions=self.Format_which_Inside_Parenthesees(aFormat) #in []
        opvarlist=[]        
        atleast=[]                
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
        return opvarlist,atleast  

    
    def get_regex_codes_to_find_parameters(self,aFormat):
        aFormat=str(aFormat)
        # ([XYZ][^\sXYZ]+) will match in any order parameters XYZ with or without spaces from gcode
        newFormat=self.Format_replace_actions(aFormat)        
        allparams=self.Get_list_of_all_parameters_all_interfaces() 
        opvarlist,atleast=self.Get_option_list(newFormat)                
        Parameters={}
        foundparameters=[]
        #Emptyreplace={}
        for param in allparams:            
            Parameters.update({param:'(.*)'})
            foundparameters.append(param)
            #Emptyreplace.update({param:''})
        justoptxt=''
        justoplist=[]
        for opiii in opvarlist:
            if '&&' not in opiii:
                aoptxt=self.Get_code(opiii,Parameters)
                aoptxt=aoptxt.replace('(.*)','')
                justoptxt=justoptxt+aoptxt
                justoplist.append(aoptxt.strip(' '))

        ch=chr(92)  # character \      
        justoptxt=justoptxt.replace(' ',ch+'s',1)        
        justoptxt=justoptxt.replace(' ','')          
        #print(justoptxt)
        #print(justoplist)
        varandval='(['+justoptxt+'][^'+ch+'s'+justoptxt+']+)'
        allval='['+justoptxt+']([^'+ch+'s'+justoptxt+']+)'
        allvar='(['+justoptxt+'])'
        P_opread={'all_var_txt':justoptxt,'var_list':justoplist,'num_var':len(justoplist),'all_var_val':varandval,'all_val':allval,'all_var':allvar,'paramslist':foundparameters}
        for optxtiii in justoplist:
            P_opread.update({optxtiii:'['+optxtiii+']([^'+ch+'s'+justoptxt+']+)'})
        '''        
        newFormat=newFormat.replace(ch,ch+ch)                               
        newFormat=newFormat.replace('||','?')         
        newFormat=newFormat.replace('.',ch+'.') 
        newFormat=newFormat.replace('^',ch+'^')                   
        newFormat=newFormat.replace('$',ch+'$')                       
        regexGcode=self.Get_code(newFormat,Parameters)        

        for iii in range(len(justoplist)):
            atxt='['+justoptxt+']'
            regexGcode=regexGcode.replace(justoplist[iii]+'(.*)',atxt+'(.*)')                                
        regexGcode=regexGcode.replace(' ',ch+'s?')
        return regexGcode
        '''    
        return P_opread    

    def get_main_code_from_gcode(self,Gcode,interface_id):
        '''
        Search all actions gcode format excluding optional parameters to match the gcode string
        '''
        allactions=self.getListofActions(exceptlist=['interfaceId','interfaceName'])
        if interface_id is None:
            interface_id=self.id
        foundcodeslist=[]  
        foundactionslist=[]  
        for action in allactions:
            aFormat=self.Get_action_format_from_id(self.Configdata,action,interface_id)
            aFormat=self.Format_replace_actions(aFormat)
            ParamsNeed=self.Get_Parameters_Needed_for_Format(aFormat)
            Maincmd=self.Format_Get_main_Command(aFormat)
            for ppp in ParamsNeed:
                if 'required' in ParamsNeed[ppp]:
                    Maincmd.replace('{'+ppp+'}','')            
            Maincmd_strip=Maincmd.strip()            
            if Maincmd_strip!='':                
                stripfound=False
                if Maincmd_strip in Gcode:
                    stripfound=True                
                if Maincmd in Gcode:
                    foundcodeslist.append(Maincmd)        
                    foundactionslist.append(action)
                elif Maincmd not in Gcode and stripfound==True:
                    foundcodeslist.append(Maincmd_strip)          
                    foundactionslist.append(action)    
        return foundcodeslist,foundactionslist
    
    def get_parameters_from_Gcode(self,Gcode,actionlist,interface_id,logerr=False):
        '''
        returns actions and parameters found in the Gcode
        '''
        actionparamsfound={}
        for action in actionlist:
            Params={}
            aFormat=self.Get_action_format_from_id(self.Configdata,action,interface_id)                        
            ParamsNeeded=self.Get_Parameters_Needed_for_action(action,interface_id)    
            P_opread=self.get_regex_codes_to_find_parameters(aFormat)
            if P_opread['num_var']==0:
                actionparamsfound.update({action:Params})
            if P_opread['num_var']>0:
                mg=re.search(P_opread['all_var_val'],Gcode)
                
                try:
                    numfound=len(mg.groups())                    
                    if numfound>0:                        
                        nmplist=P_opread['num_var']                              
                        mplist=P_opread['var_list']                           
                        for iii in range(nmplist):                            
                            var=mplist[iii]                                
                            #print(var)                  
                            par=re.search(P_opread[var],Gcode)
                            try:                                                        
                                Params.update({var : par.group(1)})   
                                #print(var,par.group(1))                                     
                            except:
                                pass                                                                
                    actionparamsfound.update({action:Params})                    
                except Exception as e:
                    if logerr==True:
                        logging.error(e)                     
                    pass
        return actionparamsfound        

    def get_action_from_gcode(self,Gcode,interface_id=None):        
        actionparamsfound={}
        if Gcode is not None or Gcode is not '':
            #allactions=self.getListofActions(exceptlist=['interfaceId','interfaceName'])
            if interface_id is None:
                interface_id=self.id            
            foundcodeslist,foundactionslist=self.get_main_code_from_gcode(Gcode,interface_id)
            #print('foundMain->',foundactionslist)
            if len(foundcodeslist)==0: #when no Main code but just parameters
                #already seached inside all parameters in get_main_code_from_gcode
                #actionparamsfound=self.get_parameters_from_Gcode(Gcode,allactions,interface_id)
                actionparamsfound={}                
            else:
                actionparamsfound=self.get_parameters_from_Gcode(Gcode,foundactionslist,interface_id)     
            actioncode=self.get_action_code(actionparamsfound,Gcode,interface_id)    
            actionparamsfound.update({'_action_code_':actioncode})
        return actionparamsfound                   

    def get_action_code(self,actionsparamsfound,Gcode,interface_id):
        modGcode=Gcode
        #print(actionsparamsfound)
        for actpar in actionsparamsfound:            
            aFormat=self.getGformatforActionid(actpar,interface_id)
            aFormat=self.Format_replace_actions(aFormat)
            #print('Here 1',modGcode,aFormat,actpar)
            if aFormat in Gcode:
                modGcode=modGcode.replace(aFormat,'{'+actpar+'}')
                #print('Here 2',modGcode,aFormat,actpar)
            else:                    
                #print('Here 3')
                MainComm=self.Format_Get_main_Command(aFormat)
                modGcode=modGcode.replace(MainComm,'{'+actpar+'}')
                Parneed=self.Get_Parameters_Needed_for_action(actpar,interface_id)
                P_get=self.get_regex_codes_to_find_parameters(aFormat)
                for sss in range(P_get['num_var']):
                    mp=re.search(P_get['all_var_val'],modGcode)
                    try:
                        nmp=len(mp.groups())
                        #print('Here 4')
                        for iii in range(nmp):
                            pareval=mp.group(iii+1)
                            modGcode=modGcode.replace(pareval,'')
                            #print('Here 5')
                    except:
                        pass        
        while '  ' in modGcode: #replace all double spaces to single spaces
            modGcode=modGcode.replace('  ',' ')                            
        return modGcode    

    def action_code_match_action(self,action_code,action,justin=False):
        atxt='{'+str(action)+'}'
        if  atxt in action_code:
            if action_code.strip() is atxt:
                return True
            return justin    
        else:
            return False         
    def Check_Format(self,aFormat,Parameters={}): 
        '''
        Checks parenthesees and if there is parameters the required parameters
        ''' 
        #print('check start')      
        isok= self.Check_Parenthesees_in_one_Format(aFormat)
        #print(isok,len(Parameters),Parameters)
        if isok==True and len(Parameters)>0 :
            #print('checking parameters')
            isok=self.Check_Parameters_for_Format(aFormat,Parameters)                 
        return isok

    def get_all_info_from_Format(self,aFormat):
        aFormat=str(aFormat)
        All_data={}
        
        All_data.update({'Format':aFormat})
        regexcmd='' 
        # if regex code
        isregex=False
        if "r'" in aFormat:
            #rlist=self.get_list_in_between_txt(aFormat,"'","'")
            #p2list,Nump2=self.Format_which_Inside_Parenthesees(p1,r"r\'",r'\]')
            rm=re.search("r'(.*)'",aFormat)
            try:                
                regexcmd=rm.group(1)
                isregex=True
            except:
                isregex=False
                pass    
        #print(regexcmd)        
            
        
        if isregex==True:
            MainComm=regexcmd
            newFormat=aFormat.replace(MainComm,'')
            optionslist,paramlist,minnumoptions=self.Format_Get_optionlist_parameterlist(newFormat)
            
        else:
            isok=self.Check_Format(aFormat)
            if isok==False:
                logging.error('Bad Format Entangled Parenthesees')
                return All_data
            MainComm=self.Format_Get_main_Command(aFormat)
            newFormat=self.Format_replace_actions(aFormat)
            optionslist,paramlist,minnumoptions=self.Format_Get_optionlist_parameterlist(newFormat)   
                
            #Parameters={}
            #for iii in paramlist:
            #    Parameters.update({iii})
            #newFormat=self.Format_select_options_ored_parameters(newFormat,Parameters)        
        
        isored=False        
        if '||' in newFormat:
            isored=True        
        ParamsNeed=self.Get_Parameters_Needed_for_Format(newFormat)           
        All_data.update({'ReqOpParamsdict':ParamsNeed})        
        All_data.update({'IsOred':isored})    
        All_data.update({'IsRegex':isregex})
        All_data.update({'MainCommand':MainComm})
        self.Get_only_the_Parameters_in_list
        All_data.update({'RegexCommand':regexcmd})  
        #if '<' in  regexcmd: 
        #    print(regexcmd)
        All_data.update({'processedFormat':newFormat})

        All_data.update({'Parameterlist':paramlist})
        All_data.update({'Optionlist':optionslist})
        All_data.update({'minRequiredOptions':minnumoptions})
        
        opttxtlist=self.Get_option_text(paramlist,optionslist)
        All_data.update({'Optiontxtlist':opttxtlist})

        P_regex=self.get_regex_codes_to_find_parameters(newFormat)         
        All_data.update({'AllOptiontxt':P_regex['all_var_txt']})
        All_data.update({'lenOptionlist':P_regex['num_var']}) 
        All_data.update({'AllParametersavailable':P_regex['paramslist']})         

        #print(optionslist)
        #print(paramlist)

        #print(P_regex['paramslist'])
        return All_data
    
    def Get_option_text(self,paramlist,optionlist):
        txtoplist=[]        
        for op in optionlist:
            for ppp in paramlist:            
                if '{'+ppp+'}' in op:
                    optiontxt=op.replace('{'+ppp+'}','')                    
                    txtoplist.append(optiontxt)   
        return txtoplist      

    def read_from_format(self,receivedline,aFormat,logerr=False):
        ParamRead={}
        aFormat=str(aFormat)
        All_data=self.get_all_info_from_Format(aFormat)
        success_=-1
        if All_data['IsRegex']==True:
            rgexcmd=All_data['RegexCommand']
            rmatch=re.search(rgexcmd,receivedline)
            success_=0
            try:
                num_match=len(rmatch.groups())
                paramlist=All_data['Parameterlist']
                optiontxtlist=All_data['Optiontxtlist']                
                nump=len(paramlist)
                numo=len(optiontxtlist)
                if numo==nump:
                    for iii in range(numo):
                        opttxt=optiontxtlist[iii]
                        ppp=paramlist[iii]
                        mmm=int(opttxt.strip())
                        ParamRead.update({ppp:rmatch.group(mmm)})
                        success_=success_+1
            except Exception as e:
                if logerr==True:
                    logging.error(e) 
                pass
        ParamRead.update({'__success__':success_})  #-1 No regex format, 0 No matches in format, # of matches found          
        return ParamRead

    def replace_action_format_in_file(self,filename,anaction,aFormat,anid,Logopen=False):
        replaced=False
        if filename is None: 
            filename=self.filename
        if anaction =='':
            return replaced            
        if filename is not None:  
            import fileinput
            # Does a list of files, and
            # redirects STDOUT to the file in question
            oldline, newline=self.get_new_line_old_line_for_action(anaction,aFormat,anid)
            #print(oldline, newline)
            if Logopen==True:
                logging.info('Opening:'+filename+'to change a format!')
            try:     
                for line in fileinput.input(filename, inplace = 1): 
                    if oldline in line:
                        line=line.replace(oldline,newline)
                    print(line, end='')                    #here prints inside file
                fileinput.close()                 
                replaced=True
            except Exception as e:
                logging.error(e)
                logging.info("Action could not be replaced on File!")
        if replaced==True and filename==self.filename:
            self.Setup_Command_Handler(False) #don't log checking
        return replaced

    def get_new_line_old_line_for_action(self,anaction,aFormat,anid):
        idlist=self.Configdata['interfaceId']
        #oldFormat=self.Get_action_format_from_id(self.Configdata,anaction,anid)
        newFormat=aFormat
        oldline='<'+anaction+'>'
        newline='<'+anaction+'>'
        for ids in idlist:        
            oldFormat=self.Get_action_format_from_id(self.Configdata,anaction,ids)   
            if oldFormat==None:
                oldFormat=''             
            if str(ids) == str(anid):
                oldline=oldline+'_<'+oldFormat+'>'
                newline=newline+'_<'+newFormat+'>'                
            else:
                oldline=oldline+'_<'+oldFormat+'>'
                newline=newline+'_<'+oldFormat+'>'
        return oldline, newline

    def create_empty_action_in_file(self,filename,anaction,Logopen=False):
        created=False
        if filename is None: 
            filename=self.filename
        if anaction =='':
            return created            
        if filename is not None:              
            # Does a list of files, and
            # redirects STDOUT to the file in question
            newline=self.get_new_line_for_action(anaction)    
            newline='\r\n'+newline
            if Logopen==True:
                logging.info('Opening:'+filename+' to create empty action!')
            try:     
                with open(filename, "a") as myfile:
                    myfile.write(newline)  
                myfile.close()              
                created=True
            except Exception as e:
                logging.error(e)
                logging.info("Action could not be append on File!")
        if created==True and filename==self.filename:
            self.Setup_Command_Handler(False) #don't log checking
        return created    

    def get_new_line_for_action(self,anaction):
        idlist=self.Configdata['interfaceId']        
        newFormat=''        
        newline='<'+anaction+'>'
        for ids in idlist:        
            newline=newline+'_<'+newFormat+'>'                
        return newline
    
    def delete_action_in_file(self,filename,anaction,Logopen=False):
        isdel=False
        if filename is None: 
            filename=self.filename
        if anaction =='':
            return isdel            
        if filename is not None:              
            oldline, newline=self.get_new_line_old_line_for_action(anaction,'',self.id)
            #print(oldline, newline)
            if Logopen==True:
                logging.info('Opening:'+filename+' to delete action!')
            try:     
                for line in fileinput.input(filename, inplace = 1): 
                    if oldline not in line:
                        print(line, end='')                    #here prints inside file
                fileinput.close()                 
                isdel=True
            except Exception as e:
                logging.error(e)
                logging.info("Action could not be deleted on File!")
        if isdel==True and filename==self.filename:
            self.Setup_Command_Handler(False) #don't log checking
        return isdel
        
    def Init_Read_Interface_Configurations(self,Reqactions_ic={},Reqactions_ir={},Logcheck=False): 
        self.Required_read=Reqactions_ir   
        self.Required_interface=Reqactions_ic
        try:            
            isok=self.Check_command_config_file_Content(self.Interfacefilename,Reqactions_ic,False,Logcheck)
            if isok==True:
                self.InterfaceConfigallids=self.Load_command_config_from_file(self.Interfacefilename)
                isok=self.Check_id_match_configs(self.Configdata,self.InterfaceConfigallids)
                if isok==True:
                    self.Int_Config=self.get_interface_config(self.InterfaceConfigallids,self.id)
            if isok==False:
                self.Int_Config={}
        except:
            self.InterfaceConfigallids={}  
            isok=False                               
            pass
        isokic=isok
        try:            
            isok=self.Check_command_config_file_Content(self.Readfilename,Reqactions_ir,False,Logcheck)
            if isok==True:
                self.ReadConfigallids=self.Load_command_config_from_file(self.Readfilename)
                isok=self.Check_id_match_configs(self.Configdata,self.ReadConfigallids)
                if isok==True:
                    self.Read_Config=self.get_interface_config(self.ReadConfigallids,self.id)
            if isok==False:
                self.Read_Config={}
        except:
            self.ReadConfigallids={}   
            isok=False         
            pass
        isokrc=isok
        return isokrc,isokic
    


            


            



   