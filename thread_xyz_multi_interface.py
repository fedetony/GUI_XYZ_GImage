import threading
import queue
import re
import logging
import time
from common import *

# install pySerial NOT serial!!!
import serial
import class_CH

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s')

# ser reader thread (TINYG)
class InterfaceSerialReaderWriterThread(threading.Thread):
    """
        A thread class to control XYZ machine read/write
    """    
    def __init__(self, port, baudrate, rx_queue, kill_event,grbl_event_hold,grbl_event_resume,grbl_event_status,grbl_event_softreset,grbl_event_stop,IsRunning_event,CH):
        threading.Thread.__init__(self, name="XYZ thread")
        self.CH=CH
        self.rx_queue = rx_queue
        self.IsRunning_event=IsRunning_event
        self.killer_event = kill_event
        self.grbl_event_hold=grbl_event_hold
        self.grbl_event_resume=grbl_event_resume
        self.grbl_event_status=grbl_event_status
        self.grbl_event_softreset=grbl_event_softreset
        self.grbl_event_stop=grbl_event_stop
        self.port = port
        self.baudrate=baudrate           
        self.Init_Configurations()    
        self.Init_Values() 
        if self.canIuseCH==True: 
            self.Connect_Serial_and_identify_Interface()            
        else:
            self.join() #end thread   
        
    def Init_Configurations(self,Logcheck=False):  
        self.canIuseCH=False  
        self.Set_Required_actions_to_CH(None,None,None)
        try:            
            isok=self.CH.Check_command_config_file_Content(self.CH.Interfacefilename,self.CH.Required_interface,False,Logcheck)
            if isok==True:
                self.InterfaceConfigallids=self.CH.Load_command_config_from_file(self.CH.Interfacefilename)
                isok=self.CH.Check_id_match_configs(self.CH.Configdata,self.InterfaceConfigallids)
                if isok==True:                    
                    self.Int_Config=self.CH.get_interface_config(self.InterfaceConfigallids,self.CH.id)
                    self.canIuseCH=True
                    logging.info("Successfully Loaded command handler form config Files!")
            if isok==False:
                logging.info("Errors in configuration files, Loading hard programed limited interface!")
                self.canIuseCH=False
                self.Int_Config=self.Default_Interface_Config()
        except:
            self.InterfaceConfigallids={}
            self.canIuseCH=False
            logging.error("Fatal Errors in configuration files!")
            raise
            
        
        try:            
            isok=self.CH.Check_command_config_file_Content(self.CH.Readfilename,self.CH.Required_read,False,Logcheck)
            if isok==True:
                self.ReadConfigallids=self.CH.Load_command_config_from_file(self.CH.Readfilename)
                isok=self.CH.Check_id_match_configs(self.CH.Configdata,self.ReadConfigallids)
                if isok==True:
                    self.Read_Config=self.CH.get_interface_config(self.ReadConfigallids,self.CH.id)
            if isok==False:
                logging.info("Errors in read configuration file, Loading hard programed limited interface!")
                self.canIuseCH=False
                self.Read_Config=self.Default_Read_Config()
        except:
            self.ReadConfigallids={}
            logging.error("Fatal Errors in configuration files!")
            self.canIuseCH=False
            raise
    
    def set_showok(self):
        '''
        Read ShowOK configuration
        '''
        showok=self.get_config_value('showOK',self.CH.id)
        if showok is None:
            showok=False           
        self.show_ok=showok    

    def Set_Required_actions_to_CH(self,Reqcc,Reqic,Reqrc):
        if Reqcc is None or Reqcc is {}:
            Reqcc={'interfaceId','interfaceName'}
        if Reqic is None or Reqic is {}:
            Reqic={'logpositionoutputFormat','logPosition','logAllReadData','logStateChange','timeforMachineStartup','showOK','timetowaitafterresume','interfaceidentifyer','interfaceId','cycletime','defaultInterface','beforestartupSequence','afterstartupSequence','hasautoReport'}         
        if Reqrc is None or Reqrc is {}:
            Reqrc={'interfaceId','acknowledgecommandreceivedRead','acknowledgecommandexecutedRead','errorRead','alarmRead','infoRead','configRead','stateRead','positionResponseRead'}
        self.CH.Required_read=Reqrc           
        self.CH.Required_actions=Reqcc    
        self.CH.Required_interface=Reqic

    def Init_Values(self):                       
        self.cycle_time = float(self.Int_Config['cycletime'])
        self.is_tinyg=self.Int_Config['interfaceId']
        self.xyzsetupready=False
        self.wasrunningbeforepause=False
        self.linesexecuted=0
        self.linessenttoexec=0
        self.linesacknkowledged=0
        self.IscheckmodeOn=False
        self.Actualcmdneedstimetoexec=False
        # data       
        logging.info("Thread init XYZ ini values set")
        self.AllReadData= {}
        self.data = {}
        self.data['EPOS'] = float(0)
        self.data['ZPOS'] = float(0)
        self.data['YPOS'] = float(0)
        self.data['XPOS'] = float(0)
        self.data['MZPOS'] = float(0)
        self.data['MYPOS'] = float(0)
        self.data['MXPOS'] = float(0)
        self.data['STATE_XYZ'] = int(0)
        self.data['STATUS'] = str('')
        self.grbl_Config={}
        self.olddata={}
        self.LastPlannedPos={}
        self.LastPlannedPos['ZPOS'] = float(0)
        self.LastPlannedPos['YPOS'] = float(0)
        self.LastPlannedPos['XPOS'] = float(0)
        for aaa in self.data:         
            self.olddata[aaa]=self.data[aaa]              

    def Default_Interface_Config(self):
        DefaultInt_Config={'interfaceidentifyer':'','interfaceId':0,'cycletime':0.2,'defaultInterface':'0','beforestartupSequence':'','afterstartupSequence':'','hasautoReport':False}        
        return DefaultInt_Config

    def Default_Read_Config(self):
        DefaultRead_Config={
            'interfaceId':0 ,
            'acknowledgeRead': "r'([oO][kK])'[1{ACK}]" ,
            'errorRead':"r'[Ee]rror(.*)'[1{ERROR}]",
            'alarmRead':"r'[Aa]larm(.*)'[1{ALARM}]",
            'infoRead':"r'\\[(.*)\\]'[1{INFO}]",
            'configRead':"r'^(\\$.*)=([^\\s]+)(.*)'[1{ConfCMD}][2{ConfValue}][3{ConfInfo}]",
            'stateRead':"",
            'positionResponseRead':"r'[<](\\w*),MPos:([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),WPos:([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),Ctl:(\\d{8})[>]'[1{STATUS}][2{MXPOS}][3{MYPOS}][4{MZPOS}][5{MAPOS}][6{XPOS}][7{YPOS}][8{ZPOS}][9{APOS}][10{CTL}]"
            }        
        return DefaultRead_Config        

    def Connect_Serial_and_identify_Interface(self):
        logging.info("Thread Opening serial port")
        self.trytoopen_serial_port()
        # identify Interface
        grbl_out=''
        try:
            count=1
            selid=0
            interfaceidentified=False
            while count<100:
                grbl_out = self.Wait_for_serial_response(0.1,exitcount=1000,loginfo=True,teaseini=20)                                
                identifierlist=self.CH.InterfaceConfigallids['interfaceidentifyer']
                namelist=self.CH.Configdata['interfaceName']
                idlist=self.CH.Configdata['interfaceId']                                
                for iii in range(len(identifierlist)):
                    if identifierlist[iii] in grbl_out and grbl_out is not '':
                        #print(grbl_out,iii,identifierlist[iii],idlist[iii],namelist[iii])
                        selid=idlist[iii]
                        logging.info('Success: '+str(namelist[iii])+' interface identified! ID'+str(selid))
                        interfaceidentified=True
                        self.is_tinyg=selid
                        count=count+100
                        break
                if interfaceidentified==True:                        
                    break
                                 
                count=count+1            
        except Exception as eee:
            logging.error(eee)
            pass
        
        if interfaceidentified==False:
            logging.info("Fail: Device Not identified. Check your identifyer <interfaceidentifyer> in InterfaceConfig.config File")             
            selectedid=self.get_config_value('defaultInterface',selid)
            if selectedid is not None:
                selid=selectedid
                self.is_tinyg=selid
                logging.info("Selecting Default interface from file Configuration! ID:"+str(selid))         
        
        self.CH.Set_new_Interface(self.is_tinyg)

        InterfaceName=self.CH.getGformatforAction('interfaceName')
        logging.info("Changed Interface to id "+ str(self.CH.id)+' ->'+InterfaceName)  
        
        self.Initialize_Interface()
        
        
    def Wait_for_serial_response(self,waittime,exitcount=1000000,loginfo=True,teaseini=20):
        wake=threading.Event()
        wake.clear()
        count=0
        grbl_out=''        
        if loginfo==True:
            logging.info('Waiting for any response...')
        while not wake.wait(waittime) and not self.grbl_event_stop.is_set() and not self.killer_event.is_set() and not self.grbl_event_softreset.is_set():
            #logging.info('wait')
            theread=self.ser_port.readline()            
            grbl_out =self.serialread_to_str(theread)            
                        
            if count<teaseini and count>=teaseini-5:
               self.port_write('\n',True,logcmd=True) 
            if count>=teaseini and count<=teaseini+self.CH.Num_interfaces:
                self.tease_serial(count)
            if len(grbl_out)>0:
                if loginfo==True:
                    logging.info("Machine response detected: "+grbl_out)
                wake.set()
            if count>exitcount:
               grbl_out=None 
               wake.set()     
            count=count+1   
        if count>=exitcount:
            logging.error('Wait Timeout exit...')    
        if self.grbl_event_stop.is_set() or self.killer_event.is_set() or self.grbl_event_softreset.is_set():
            logging.error('Wait exit by event...')        
        return grbl_out
    
    def serialread_to_str(self,theread,coding=None):
        if type(theread)==bytes:
            if coding!= None:
                return str(theread.decode(coding))    
            return str(theread.decode())
        else:    
            return str(therad)

    def get_config_value(self,configaction,anid):
        aFormat=self.CH.Get_action_format_from_id(self.CH.InterfaceConfigallids,configaction,anid)
        atype=self.CH.Get_action_format_from_id(self.CH.InterfaceConfigallids_type,configaction,anid)
        isok,avalue=self.get_Format_type_to_value(atype,aFormat)
        if isok==True:
            return avalue
        else:
            return None    
    def set_correct_type(self,txt,returntypetxt=False):
        txt=str(txt)
        mf=re.search('([+-]?[0-9]*[.][0-9]+)',txt) 
        try:
            if len(mf.groups())>0:
                if returntypetxt==True:
                    return 'float'
                return float(txt)
        except:
            pass 
        mb=re.search('([01]{8})',txt) 
        try:
            if len(mb.groups())>0:
                if returntypetxt==True:
                    return 'byte'
                return str.encode(txt)
        except:
            pass        

        mi=re.search('([+-]?\d+)',txt) 
        try:
            if len(mi.groups())>0:
                if returntypetxt==True:
                    return 'int'
                return int(txt)
        except:
            pass     
        if returntypetxt==True:
            return 'string'  
        return str(txt) 

    def get_Format_type_to_value(self,atype,aFormat,showlog=False):
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
                    logging.error(e)     
                val=None   
                isok=False                
                pass        
                
        elif atype=='str' or atype=='string':
            try:
                val=str(aFormat)
                isok=True
            except Exception as e:
                if showlog==True:
                    logging.error(e)     
                val=None 
                isok=False                   
                pass                    
        elif atype=='int':
            try:
                val=int(aFormat)
                isok=True    
            except Exception as e:
                if showlog==True:
                    logging.error(e)     
                val=None
                isok=False    
                pass
        elif atype=='float':
            try:
                val=float(aFormat)
                isok=True    
            except Exception as e:
                if showlog==True:
                    logging.error(e)     
                val=None
                isok=False    
                pass    
        elif atype=='byte':
            try:
                val=bytes(aFormat.encode())
                isok=True    
            except Exception as e:
                if showlog==True:
                    logging.error(e)     
                val=None
                isok=False    
                pass    
        elif atype=='char':
            try:
                val=chr(int(aFormat))
                isok=True    
            except Exception as e:
                if showlog==True:
                    logging.error(e)     
                val=None
                isok=False    
                pass                         
        elif atype=='read' or atype=='regex' or atype=='action':
            try:    
                P_Allinfo=self.CH.get_all_info_from_Format(aFormat)            
                val=P_Allinfo
                isok=True
            except Exception as e:
                if showlog==True:
                    logging.error(e)
                P_Allinfo={}    
                isok=False   
                pass
            if P_Allinfo is {}:
                isok=False   
            val=P_Allinfo     
        else:
            isok=True
            val=aFormat    
        if showlog==True:
            if isok == False:
                msgtxt="Bad format of type "+atype
                logging.error(msgtxt)                
            else:                
                msgtxt="Format of type "+atype+" accepted"                
                logging.info(msgtxt)                
        return isok,val    

    def tease_serial(self,nnn):
        col=nnn % self.CH.Num_interfaces
        idlist=self.CH.Configdata['interfaceId']
        aFormat=self.CH.Get_action_format_from_id(self.CH.Configdata,'reportBuildInfo',idlist[col])
        Gcode=self.CH.Get_code(aFormat,{})
        #Gcode,isok=self.CH.Get_Gcode_for_Action('reportBuildInfo('+str(idlist[col])+')',{},True)
        logging.info('Teasing...'+Gcode)
        self.port_write(Gcode,True,logcmd=True)

    def trytoopen_serial_port(self):
        try:            
            #str(self.baudrate).encode('utf-8')
            self.ser_port = serial.Serial(self.port, self.baudrate, timeout=0)            
            self.ser_port.flushInput()  # Flush startup text in serial input
        except Exception as eee:
            logging.error(eee)
            logging.error("InterfaceSerialReaderWriterThread: Failed to open serial port " + self.port)
            raise
    
    def run(self):               
        self.xyzsetupready=True
        # start cyclic Run
        while not self.killer_event.wait(self.cycle_time):                         
            if self.xyzsetupready==False:
                logging.info('Holding Run while setup or EEPROM read...')
                countsetup=0
                while self.xyzsetupready==False and countsetup<=1000 and not self.killer_event.is_set() and not self.grbl_event_softreset.is_set():
                    time.sleep(self.cycle_time)
                    countsetup=countsetup+1
                self.xyzsetupready=True   
                logging.info('Releasing Run after EEPROM read...') 

            if  self.grbl_event_hold.is_set():
                self.Send_Hold(1) #clears start flag
                logging.info("Holding !!")
                while not self.grbl_event_resume.is_set() and not self.killer_event.is_set() and not self.grbl_event_softreset.is_set():
                    self.Run_Read_Values()
                    time.sleep(self.cycle_time)
                    
                if self.grbl_event_resume.is_set():
                    self.Send_Resume(1) #clears hold flag   
                    logging.info("Run Started!")
                    self.grbl_event_resume.clear() #clear start flag

            if  self.grbl_event_softreset.is_set():
                logging.info("Reseting!!")
                self.Send_SoftReset(1)
                time.sleep(1.5)   #Marlin blocks incoming data for 1 sec after M410 stop                     
                self.grbl_event_softreset.clear()
                #Clean queue
                with self.rx_queue.mutex:
                    self.rx_queue.queue.clear()            
            
            if  self.grbl_event_stop.is_set():
                logging.info("Stopping!!")
                self.Send_Stop(1)
                #Clean queue
                with self.rx_queue.mutex:
                    self.rx_queue.queue.clear() 
                self.grbl_event_stop.clear()    
                  
            if self.killer_event.is_set():
                self.Send_Kill(1)
                
                
            else:
                # check if there is something we should send to the serial
                try:
                                       
                    new_cmd = self.rx_queue.get_nowait()
                    self.Actualcmdneedstimetoexec=self.Does_cmd_need_time_to_execute(new_cmd,self.Actualcmdneedstimetoexec)                    
                    #logging.info("Wait State :" + str(new_cmd)+'-->'+str(self.Actualcmdneedstimetoexec))                   
                    self.ser_port.write(str(new_cmd).encode())                    
                    self.grbl_event_status.set()  #Set flag to read the values
                    self.Do_line_Counting(new_cmd)      
                    
                except queue.Empty:
                    #self.grbl_event_status.clear()
                    pass
                # read the values
                self.Run_Read_Values()
        logging.info(self.name + " killed")
        self.ser_port.close()
    
    def Do_line_Counting(self,new_cmd):      
        self.linesacknkowledged=self.linesacknkowledged+1                        
        if self.Actualcmdneedstimetoexec==False: #Count No waiting lines as executed. Example G92 or G80 or M114
            self.linesexecuted=self.linesexecuted+1                            
        else:
            self.Actualcmdneedstimetoexec=self.Track_position_for_Gcode(new_cmd,self.Actualcmdneedstimetoexec)   
            if self.Actualcmdneedstimetoexec==False: #Count No waiting lines as executed. Example G92 or G80 or M114
                self.linesexecuted=self.linesexecuted+1 
        Is_G0G1G2G3=self.Set_Last_Planned_Position(new_cmd)        

    def queue_count(self):
        return self.rx_queue.qsize()

    def Reset_linesexecutedCount(self):
        self.linesexecuted=0
        self.linessenttoexec=0
        self.linesacknkowledged=0
    
    def Set_Last_Planned_Positionfromdata(self):
        self.LastPlannedPos['XPOS']=self.data['XPOS']
        self.LastPlannedPos['YPOS']=self.data['YPOS']
        self.LastPlannedPos['ZPOS']=self.data['ZPOS']

        
    def Initialize_Interface(self):
        
        timefMS=self.get_config_value('timeforMachineStartup',self.CH.id)
        try:    
            if float(timefMS)>20:
                timefMS=20
            if float(timefMS)<=0:
                timefMS=0.1    
            logging.info('Waiting for '+str(timefMS)+'[s] before Startup!')    
            time.sleep(float(timefMS))
        except:
            logging.info('Waiting for 1(s) before Startup!')
            time.sleep(1)    
            pass
        self.set_showok()
        aFormat=self.CH.Get_action_format_from_id(self.CH.InterfaceConfigallids,'beforestartupSequence',self.CH.id)
        Gcode=self.CH.Get_code(aFormat,{})
        self.port_write(Gcode,True)
        if Gcode!='':
            line_r = self.Wait_for_serial_response(0.1,exitcount=100,loginfo=True,teaseini=95)                       
        InterfaceName=self.CH.getGformatforAction('interfaceName')
        logging.info("setting up "+str(InterfaceName))
        cmd='Message'
        amsg={'msg':'Inteface id '+ str(self.CH.id)+ ' Connected'}
        Gcode,isok=self.CH.Get_Gcode_for_Action(cmd,amsg,True)
        self.port_write(Gcode,isok)
        if isok==True and Gcode!='':
            line_r = self.Wait_for_serial_response(0.1,exitcount=100,loginfo=True,teaseini=95)               
        cmd='automaticstatusReports-Filtered'
        Gcode,isok=self.CH.Get_Gcode_for_Action(cmd,{},True)
        self.port_write(Gcode,isok)
        if isok==True and Gcode!='':
            line_r = self.Wait_for_serial_response(0.1,exitcount=100,loginfo=True,teaseini=95)               
        cmd='automaticstatusReports-Moving'        
        Gcode,isok=self.CH.Get_Gcode_for_Action(cmd,{'timems':200},True)        
        self.port_write(Gcode,isok)
        if isok==True and Gcode!='':
            line_r = self.Wait_for_serial_response(0.1,exitcount=100,loginfo=True,teaseini=95)               
        cmd='reportBuildInfo'
        Gcode,isok=self.CH.Get_Gcode_for_Action(cmd,{},True)
        self.port_write(Gcode,isok)
        if isok==True and Gcode!='':
            line_r = self.Wait_for_serial_response(0.1,exitcount=100,loginfo=True,teaseini=95)               
        cmd='statusReport'
        Gcode,isok=self.CH.Get_Gcode_for_Action(cmd,{},True)
        self.port_write(Gcode,isok)
        if isok==True and Gcode!='':
            line_r = self.Wait_for_serial_response(0.1,exitcount=100,loginfo=True,teaseini=95)               
        aFormat=self.CH.Get_action_format_from_id(self.CH.InterfaceConfigallids,'afterstartupSequence',self.CH.id)
        Gcode=self.CH.Get_code(aFormat,{})
        self.port_write(Gcode,True)
        if Gcode!='':
            line_r = self.Wait_for_serial_response(0.1,exitcount=100,loginfo=True,teaseini=95)               

        

    def queue_write(self,cmd,isok,ending='\n',logcmd=False):
        if isok==True:
            if cmd is not '' and cmd is not None:
                if ending is not None:
                    self.rx_queue.put(cmd+ending)                    
                else:
                    self.rx_queue.put(cmd) 
                if logcmd==True:
                    logging.info('Queued')      


    def port_write(self,cmd,isok,ending='\n',logcmd=False):
        if isok==True:
            if cmd is not '' and cmd is not None:
                if ending is not None:
                    self.ser_port.write(str.encode(cmd+ending))
                else:
                    self.ser_port.write(str.encode(cmd))    
            
    def Is_system_ready(self):
        return self.xyzsetupready

    def Send_Hold(self,sendcmd):
        #if not self.grbl_event_hold.is_set():
        self.grbl_event_hold.set()
        self.grbl_event_resume.clear()
        if sendcmd==1:
            
            if self.data['STATE_XYZ']==3:
                cmd='userPause'        
            else:
                cmd='quickPause'            
            Gcode,isok=self.CH.Get_Gcode_for_Action(cmd,{},True)
            self.port_write(Gcode,isok) 
            interfacename=self.CH.getGformatforAction('interfaceName')
            logging.info(str(interfacename)+" on hold!")                   

    def Send_Kill(self,sendcmd):        
        if not self.grbl_event_softreset.is_set():
            self.grbl_event_softreset.set()

        if sendcmd==1:
            interfacename=self.CH.getGformatforAction('interfaceName')
            logging.info(str(interfacename)+" Kill send!")
            cmd='emergencyKill'
            Gcode,isok=self.CH.Get_Gcode_for_Action(cmd,{},True)
            self.port_write(Gcode,isok) 
            time.sleep(0.2) # wait after command
           
    
    def Send_Stop(self,sendcmd):
        if not self.grbl_event_stop.is_set():
            self.grbl_event_stop.set()
        if sendcmd==1:
            cmd='quickStop'
            Gcode,isok=self.CH.Get_Gcode_for_Action(cmd,{},True)
            self.port_write(Gcode,isok) 
            interfacename=self.CH.getGformatforAction('interfaceName')
            logging.info(str(interfacename)+" Stop send!") 

    def Send_SoftReset(self,sendcmd):
        if not self.grbl_event_softreset.is_set():
            self.grbl_event_softreset.set()
        if sendcmd==1:
            cmd='softReset'
            Gcode,isok=self.CH.Get_Gcode_for_Action(cmd,{},True)
            self.port_write(Gcode,isok) 
            interfacename=self.CH.getGformatforAction('interfaceName')
            logging.info(str(interfacename)+" SoftReset send!") 

    def Send_Resume(self,sendcmd):         
        self.grbl_event_resume.set()
        self.grbl_event_hold.clear()
        if sendcmd==1:    
            if self.wasrunningbeforepause==False:
                cmd='userResume'        
            else:
                cmd='quickResume'            
            Gcode,isok=self.CH.Get_Gcode_for_Action(cmd,{},True)
            self.port_write(Gcode,isok) 
            interfacename=self.CH.getGformatforAction('interfaceName')
            logging.info(str(interfacename)+" Resume!")            
        timeresume=self.get_config_value('timetowaitafterresume',self.is_tinyg)    
        if timeresume<0 or timeresume>2 or timeresume is None:
            time.sleep(0.2) # wait after command        
        else:
            time.sleep(timeresume) # wait after command        
    
    def readline_fromserial(self,buff=128):
        line=''
        count=1
        linebuff=[]
        while True:
            line_r = self.ser_port.readline()  # Wait for machine response with carriage return
            line_r = self.serialread_to_str(line_r,'utf-8')
            line_r=str(line_r)                       
            for ccc in line_r:
                if ccc != '\r' and ccc != '\n':
                    linebuff.append(ccc)
                if ccc == '\n':
                    line=''.join(linebuff)
                    return str(line)
            count=count+1        
            if count>buff:
                return line
    
    def Read_key_Status(self,PRdata,akey,showlog):
        '''
        Reads PRdata and cleans it if a value is found.
        returns: PRdata,astatus
        astatus has the value if found or None
        PRdata[akey] is cleaned '' if value found.
        '''
        astatus=None
        try:
            astatus=PRdata[akey]     
            if astatus is not '' or astatus is not None:
                if showlog==True:
                    logging.info(astatus)                   
                PRdata.update({akey:''})
        except:
            pass 
        return PRdata,astatus
    
    def Read_one_data(self,grbl_out,Readaction):
        PRdata={}     
        foundmatch=False           
        if Readaction in self.Read_Config:
            aFormat=self.Read_Config[Readaction]                                
            #print(aFormat)    
            PRead=self.CH.read_from_format(grbl_out,aFormat,logerr=False)
            if PRead['__success__']>0:
                for PR in PRead:
                    if PR is not '__success__':
                        PRdata.update({PR:PRead[PR]})
                    foundmatch=True        
                    break
        #print(foundmatch,PRdata)
        return  PRdata,foundmatch  


    def Read_all_data(self,grbl_out):
        PRdata={}
        foundmatch=False
        for aitem in self.data:
            PRdata.update({aitem:self.data[aitem]})
        for RC in self.Read_Config:
            aFormat=self.Read_Config[RC]                                
            #print(aFormat)    
            PRead=self.CH.read_from_format(grbl_out,aFormat,logerr=False)
            if PRead['__success__']>0:
                for PR in PRead:
                    if PR is not '__success__':
                        PRdata.update({PR:PRead[PR]})
                foundmatch=True        
                break
        #print(foundmatch,PRdata)
        return  PRdata,foundmatch       

    def Process_Read_Data(self,grbl_out,showok=False):
        if (grbl_out):
            logalldata=self.get_config_value('logAllReadData',self.is_tinyg)
            if logalldata==True:
                logging.info(grbl_out)
            PRdata,foundmatch=self.Read_all_data(grbl_out)
            if foundmatch==False and len(grbl_out):
                logNoread=self.get_config_value('logNoread',self.is_tinyg)
                if logNoread==True or logNoread is None:
                    logging.info("No read: "+ grbl_out)
            else:
                self.AllReadData=PRdata
                PRdata,astatus=self.Read_key_Status(PRdata,'ACK',showok)
                if astatus is not None:
                    self.data['STATUS']=astatus
                PRdata,astatus=self.Read_key_Status(PRdata,'ACKCMD',showok)
                if astatus is not None:
                    self.data['STATUS']=astatus    
                PRdata,astatus=self.Read_key_Status(PRdata,'ERROR',True)
                if astatus is not None:
                    self.data['STATUS']=astatus                
                PRdata,astatus=self.Read_key_Status(PRdata,'ALARM',True)
                if astatus is not None:
                    self.data['STATUS']=astatus             
                PRdata,astatus=self.Read_key_Status(PRdata,'INFO',True)
                if astatus is not None:
                    self.data['STATUS']=astatus                       
                for iii in self.data:
                    PRdata,astatus=self.Read_key_Status(PRdata,iii,False)
                    if astatus is not None:
                        self.data.update({iii:self.set_correct_type(astatus)})
                        if iii is 'STATUS':                            
                            self.Set_StateXYZ_from_Status()                        
                        if iii is 'STATE_XYZ':
                            self.Set_Status_from_StateXYZ()   

                if self.Compare_Hasdatachanged(self.olddata,['CTL'])==True:
                    logPosition=self.get_config_value('logPosition',self.is_tinyg)
                    if logPosition!=False:
                        logpositionoutputFormat=self.get_config_value('logpositionoutputFormat',self.is_tinyg)
                        if logpositionoutputFormat is not None and logpositionoutputFormat!='':
                            Gcode=self.CH.Get_code(logpositionoutputFormat,self.data)
                            if Gcode=='' or Gcode is None:
                                logging.info(grbl_out + ' ' + str(self.data['STATE_XYZ']))     
                            else:
                                logging.info(Gcode)     
                            
                                
                        else:                            
                            logging.info(grbl_out + ' ' + str(self.data['STATE_XYZ'])) 
                    # if state changed                
                    if self.olddata['STATE_XYZ']!=self.data['STATE_XYZ']:
                        logStateChange=self.get_config_value('logStateChange',self.is_tinyg)
                        if logStateChange==True:
                            logging.info('State change from: '+str(self.olddata['STATUS'])+' '+str(self.olddata['STATE_XYZ']) + ' to ' + str(self.data['STATUS']) + ' ' + str(self.data['STATE_XYZ'])) 

                        if (self.data['STATE_XYZ']<=4 or self.data['STATE_XYZ']==11): # state X-> 3
                            self.IsRunning_event.clear()    
                            self.linesexecuted=self.linesexecuted+1
                        else:
                            self.IsRunning_event.set()   

                for aaa in self.data:         
                    self.olddata[aaa]=self.data[aaa]                
        return self.data
 
    
    
    def Compare_Hasdatachanged(self,olddata,exceptlist=[]):
        is_different=False
        for aaa in self.data:
            #logging.info(str(olddata[aaa])+' vs ' + str(self.data[aaa]))
            if aaa not in exceptlist:
                if aaa in olddata:
                    if olddata[aaa]!=self.data[aaa]:
                        is_different= True
                        break        
        return is_different

    def Set_StateXYZ_from_Status(self):
        '''
        1=reset, 2=alarm, 3=idle, 4=end, 5=run, 6=hold, 7=probe, 8=cycling,  9=homing, 10 =jogging 11=error
        '''
        status=self.data['STATUS']         
        if 'Init' in status or 'init' in status:
            self.data['STATE_XYZ']=0 
        if 'Reset' in status or 'reset' in status:
            self.data['STATE_XYZ']=1
        if 'Alarm' in status or 'alarm' in status:
            self.data['STATE_XYZ']=2
        if 'Idle' in status or 'idle' in status:
            self.data['STATE_XYZ']=3
        if 'End' in status or 'end' in status:
            self.data['STATE_XYZ']=4    
        if 'Run' in status or 'run' in status:
            self.data['STATE_XYZ']=5   
        if 'Hold' in status or 'hold' in status:
            self.data['STATE_XYZ']=6
        if 'Probe' in status or 'probe' in status:
            self.data['STATE_XYZ']=7
        if 'Cycling' in status or 'cycling' in status:
            self.data['STATE_XYZ']=8                    
        if 'Homing' in status or 'homing' in status:
            self.data['STATE_XYZ']=9
        if 'Jogging' in status or 'jogging' in status:
            self.data['STATE_XYZ']=10
        if 'Error' in status or 'error' in status:            
            self.data['STATE_XYZ']=11    
    
    def Set_Status_from_StateXYZ(self):
        """
        0	machine is initializing	
        1	machine is ready for use	
        2	machine is in alarm state (soft shut down)	
        3	program stop or no more blocks (M0, M1, M60)	
        4	program end via M2, M30	
        5	motion is running	
        6	motion is holding	
        7	probe cycle active	
        8	machine is running (cycling)	
        9	machine is homing	
        10	machine is jogging	
        11	machine is in hard alarm state (shut down)
        """
        #1=reset, 2=alarm, 3=idle, 4=end, 5=run, 6=hold, 7=probe, 8=cycling,  9=homing, 10 =jogging 11=error
        state=self.data['STATE_XYZ']
        self.data['STATUS']='N/A'
        if state ==1:
            self.data['STATUS']='ready'   
        if state ==2:
            self.data['STATUS']='alarm' #soft alarm
        if state ==3:
            self.data['STATUS']='idle' #stop'
        if state ==4:
            self.data['STATUS']='end'       
        if state ==5:
            self.data['STATUS']='run'
        if state ==6:
            self.data['STATUS']='hold'           
        if state ==7:
            self.data['STATUS']='probe'
        if state ==8:
            self.data['STATUS']='cycling'    
        if state ==9:
            self.data['STATUS']='homing'
        if state ==10:
            self.data['STATUS']='jogging'    
        if state ==0:
            self.data['STATUS']='init'            
        if state ==11:
            self.data['STATUS']='error' #hard alarm                

    def Send_Homing(self):
        '''
        Homing command for Homing
        '''
        cmd='Home'
        Gcode,isok=self.CH.Get_Gcode_for_Action(cmd,{},True)
        self.queue_write(Gcode,isok)         
        logging.info("Homing Command set in queue")

    def read(self):
        '''
        Predetermined and processed information required for positioning and update.
        '''
        return self.data
    
    def read_all(self):
        '''
        Raw information as read from read config file
        '''
        return self.AllReadData   

    def Send_Multi_Read(self,waittime,showlog=True): 
        '''
        Asks for a report in case no autoreport. Reads all info and process it.
        Returns position data only. All other info unprocessed in AllReaddata dict.
        ''' 
        hasautoReport=self.get_config_value('hasautoReport',self.is_tinyg) 
        if hasautoReport is None:
            hasautoReport=False
        if hasautoReport == False:
            if  self.grbl_event_status.is_set(): 
                cmd='statusReport'            
                Gcode,isok=self.CH.Get_Gcode_for_Action(cmd,{},True)
                self.port_write(Gcode,isok)                 
        
        if  self.grbl_event_status.is_set() and not self.grbl_event_softreset.is_set() and not self.grbl_event_stop.is_set():             
            grbl_out = self.readline_fromserial(buff=4*256)     
                    
            self.data=self.Process_Read_Data(grbl_out,self.show_ok)                
            time.sleep(waittime)  
            #self.grbl_event_status.clear()              
        return self.data
    

    def Run_Read_Values(self):
        '''
        Reads serial and Process the information, stores received info in self.data
        '''        
        self.Send_Multi_Read(0,self.show_ok)         # do not report ok-> False             
        grbl_out = self.readline_fromserial()
        self.data=self.Process_Read_Data(grbl_out,self.show_ok) 
    
    def Read_Config_Parameter(self,Param,Showlog=True):
        '''
        Reads Machine EEPROM configuration for Param information from the grbl_Config dictionary.
        '''
        valread=''
        try:
            for ccc in self.grbl_Config:
                #logging.info('Found->'+ccc)
                if ccc==str(Param):                    
                    if Showlog==True:
                        logging.info(ccc + '=' + str(self.grbl_Config[ccc]) + ' for ' + self.grbl_Config[ccc+'_Info'])                           
                    valread= self.grbl_Config[ccc]
                    break
        except:
            if Showlog==True:
                logging.info('No Config ' + str(Param)+ ' found!') 
            pass
        return valread
    

    #------------------------------------------------------------------------
    # #######################################################################
    # Need to be transformed to multi
    # #######################################################################
    # -----------------------------------------------------------------------
    # to be refurbished
                   
    def Change_Config_Parameter(self,Param,Value):
        isaccepted=False
        try:            
            self.xyzsetupready=False                               
            cmd='modifySetting'
            Params={'setting':Param,'value':Value}            
            Gcode,isok=self.CH.Get_Gcode_for_Action(cmd,Params,True)
            self.port_write(Gcode,isok)
            if isok==True:
                logging.info('Sent setting ' + Gcode )
            else:
                logging.info('Setting Not sent! ' + Gcode )                          
            line = self.Wait_for_serial_response(0.1,exitcount=1000,loginfo=False,teaseini=2000)   
            
            data=self.Process_Read_Data(line,showok=True)      
            isack, iscr, isce=self.is_received_acknowledge(line)          
            
            self.xyzsetupready=True
            # update configuration
            if isack==True: #"ok" in line:
                for ccc in self.grbl_Config:
                    if ccc == str(Param):
                        #atype=self.grbl_Config[ccc+'_Type']
                        atype=self.set_correct_type(Value,returntypetxt=True)
                        isok,avalue=self.get_Format_type_to_value(atype,Value)
                        if isok==True:
                            self.grbl_Config[ccc]=avalue
                            logging.info(str(Param)+" Parameter Accepted!")
                            isaccepted=True
                        else:
                            self.grbl_Config[ccc]=str(Value)        
                            logging.info(str(Param)+" not congruent type set as string!")
                            isaccepted=False
                        break
                #logging.info(str(Param)+" Parameter Accepted!")                

        except:
            logging.info('Not Possible to configure ' + str(Param))    
            isaccepted=False
        return isaccepted

    def is_received_acknowledge(self,grbl_out):
        '''
        Returns isack True if either command executed or command received are True
        Returns CE and CR responses if match found can be False or None
        False-> command exist, but not found
        None-> command does not exist
        '''
        isack=False 
        PRdata,foundmatchce=self.Read_one_data(grbl_out,'acknowledgecommandexecutedRead')
        if foundmatchce==True:
            isack=True        
        PRdata,foundmatchcr=self.Read_one_data(grbl_out,'acknowledgecommandreceivedRead')
        if foundmatchcr==True:
            isack=True        
        return isack, foundmatchcr, foundmatchce   



    def Read_Actual_Config(self,showlog=True):
        '''
        Reads the configuration of device following the configRead Format.
        Reads all parameters that contain conf in their name
        '''
        #self.grbl_Config.clear()
        self.xyzsetupready=False
        
        cmd='reportSettings'
        Gcode,isok=self.CH.Get_Gcode_for_Action(cmd,{},True)
        if isok==True:
            logging.info('Asking for settings ' + Gcode )
        else:
            logging.info("Can't gather settings please check action reportSetting! for ID:" + self.is_tinyg )    
            return
        self.ser_port.reset_input_buffer()  
        self.port_write(Gcode,isok)
        line = ' '          
        linebuff=[]
        okrcv=None        
        confdict={}             
        alllines='' 
        # catch all info first
        while okrcv is None:       
            line_r=self.readline_fromserial(buff=4*256)                                                         
            #line_r = self.Wait_for_serial_response(0.1,exitcount=1000,loginfo=False,teaseini=2000) 
            isack, iscr, isce=self.is_received_acknowledge(line_r)              
            if isack==True:
                okrcv=isack
            alllines=alllines+line_r + '\n'   
            linebuff.append(line_r)
        # Process the data    
        confignum=0
        for line in linebuff:
            PRdata,foundmatch=self.Read_all_data(line)    
            oneconf={}        
            if foundmatch==True:
                prlist=[]
                for jjj in PRdata:
                    prlist.append(jjj)
                ConfValue=''
                ConfCMD=''    
                ConfInfo=''
                ConfType=''
                ConfUnit=''
                for iii in prlist:                    
                    PRdata,avalue=self.Read_key_Status(PRdata,iii,False)
                    
                    if avalue is not None:  
                        lowiii=str(iii).lower() 
                        if 'Conf'.lower() in str(iii).lower():                     
                            oneconf.update({iii:avalue})
                        if lowiii=='ConfValue'.lower():
                            ConfValue=avalue
                            ConfType=self.set_correct_type(str(avalue),True)
                        if lowiii=='ConfUnit'.lower():
                            ConfUnit=str(avalue)
                        if lowiii=='ConfInfo'.lower():        
                            ConfInfo=str(avalue)
                        if lowiii=='ConfCMD'.lower():    
                            ConfCMD=str(avalue)
                        if 'Conf'.lower() in lowiii:
                            #put all other information in info
                            if 'cmd' not in lowiii and 'info' not in lowiii and 'value' not in lowiii:
                                 ConfInfo=ConfInfo+' ('+str(avalue)+')'
                
                if  ConfCMD!='':           
                    self.grbl_Config.update({ConfCMD : ConfValue})
                    self.grbl_Config.update({ConfCMD+'_Type' : ConfType})
                    self.grbl_Config.update({ConfCMD+'_Info' : ConfInfo})                        
                        
                confignum=confignum+1
            else:
                logging.info('No Read match for:'+line)    
            if oneconf is not {}:    
                confdict.update({'Config_'+str(confignum):oneconf})

        self.xyzsetupready=True  
        #print(confdict)    
        #print('Alllines:\n', alllines)  

    # to be transformed
    def Set_Last_Planned_Position(self,txtgcmd):
        try:
            mg = re.search('.*?([Gg][0-3 9]{1})(\d*[\.,]?\d*)?.*?([X,x,Y,y,Z,z,F,f,I,i,J,j,K,k])([+-]?\d*[\.,]?\d*)',txtgcmd)
            if '9' in str(mg.group(1)):
                if '2' != str(mg.group(2)):
                    #Not G92
                    return False
            else:        
                if float(mg.group(2)) is not None:
                    #print('Not G0,G1,G2,G3')
                    return False                         
        except:    
            pass
        try:
            mgx = re.search('.*?([Gg][0-3]{1}).*([X,x])([+-]?\d*[\.,]?\d*)',txtgcmd)
            self.LastPlannedPos['XPOS'] = float(mgx.group(3))            
        except:    
            pass
        try:
            mgy = re.search('.*?([Gg][0-3]{1}).*([Y,y])([+-]?\d*[\.,]?\d*)',txtgcmd)            
            self.LastPlannedPos['YPOS'] = float(mgx.group(3))
        except:    
            pass
        try:
            mgz = re.search('.*?([Gg][0-3]{1}).*([Z,z])([+-]?\d*[\.,]?\d*)',txtgcmd)            
            self.LastPlannedPos['ZPOS'] = float(mgx.group(3))
        except:    
            pass
        return True


    def Track_position_for_Gcode(self,txtgcmd,Current_IswaitState):
        samex=True
        samey=True
        samez=True
        try:
            mg = re.search('.*?([Gg][0-3]{1})(\d*[\.,]?\d*)?.*?([X,x,Y,y,Z,z,F,f,I,i,J,j,K,k])([+-]?\d*[\.,]?\d*)',txtgcmd)
            if float(mg.group(2)) is not None:
                #print('Not G0,G1,G2,G3')
                return Current_IswaitState                         
        except:    
            pass
        #print('Is a G0,G1,G2,G3')
        try:
            mgx = re.search('.*?([Gg][0-3]{1}).*([X,x])([+-]?\d*[\.,]?\d*)',txtgcmd)
            if self.LastPlannedPos['XPOS'] == float(mgx.group(3)):
                samex=True
            else:
                samex=False                
        except:    
            pass
        try:
            mgy = re.search('.*?([Gg][0-3]{1}).*([Y,y])([+-]?\d*[\.,]?\d*)',txtgcmd)            
            if self.LastPlannedPos['YPOS'] == float(mgy.group(3)):
                samey=True
            else:
                samey=False                            
        except:    
            pass
        try:
            mgz = re.search('.*?([Gg][0-3]{1}).*([Z,z])([+-]?\d*[\.,]?\d*)',txtgcmd)            
            if self.LastPlannedPos['ZPOS'] == float(mgz.group(3)):
                samez=True
            else:
                samez=False    
        except:    
            pass
        if (samex and samey and samez)==True: #when all coordinates are the same -> no movement
            return False
        return Current_IswaitState

    def Does_cmd_need_time_to_execute(self,txtgcmd,Current_IswaitState=False):
        coords=['X','x','Y','y','Z','z','I','i','J','j','K','k','R','r']
        GRBL_Wait_for_state_Cmds=['G0','g0','G1','g1','G2','g2','G3','g3','$H','G29','g29','G30','g30', 'G38.2', 'G38.3', 'G38.4', 'G38.5']        
        gnums=[0,1,2,3,4,28,28.1,28.2,28.3,30,30.1,30.2,30.3]
        mnums=[]
        TinyG_Wait_for_state_Cmds=[]
        for iii in gnums:
            TinyG_Wait_for_state_Cmds.append('G'+str(iii))
            TinyG_Wait_for_state_Cmds.append('g'+str(iii))
        for iii in mnums:
            TinyG_Wait_for_state_Cmds.append('M'+str(iii))
            TinyG_Wait_for_state_Cmds.append('m'+str(iii))
        #TinyG_Wait_for_state_Cmds=['G0','g0','G1','g1','G2','g2','G3','g3','G4','g4','G28','g28','G28.1','g28.1','G28.2','g28.2','G28.3','g28.3','G29','g29','G30','g30']
        
        gnums=[0,1,2,3,4,5,10,11,12,27,28,29,30,38.2,38.3,38.4,38.5,42,61,425]
        mnums=[48,125,190,191,192,226,360,361,362,363,364,400]
        #Marlin_Wait_for_state_Cmds=['S000','P000','R000']
        Marlin_Wait_for_state_Cmds=[]
        for iii in gnums:
            Marlin_Wait_for_state_Cmds.append('G'+str(iii))
            Marlin_Wait_for_state_Cmds.append('g'+str(iii))
        for iii in mnums:
            Marlin_Wait_for_state_Cmds.append('M'+str(iii))
            Marlin_Wait_for_state_Cmds.append('m'+str(iii))

        if self.is_tinyg==0: #Grbl            
            try:
                mg = re.search('^([\!,~,\?,\$])',txtgcmd)   # override string
                if str(mg.group(1)) in ['!','~','?']:
                    return Current_IswaitState
                if str(mg.group(1))=='$':
                    if '$H' in txtgcmd or '$h' in txtgcmd: #Homing
                        return True            
                    elif '$J' in txtgcmd or '$j' in txtgcmd: #Jogging                          
                        return True             
                    elif '$C' in txtgcmd:
                        if self.IscheckmodeOn==True:
                            self.IscheckmodeOn=False
                            return False
                        else:     
                            self.IscheckmodeOn=True
                            return False                  
                    else:
                        return Current_IswaitState
                return False        
            except:    
                pass
            if self.IscheckmodeOn==True:
                return False   
            try:                            
                mg = re.search('^([M,m,G,g,X,x,Y,y,Z,z])([+-]?\d*[\.,]?\d*)',txtgcmd)   
                thecmd=str(mg.group(1))+str(mg.group(2))   
                if str(mg.group(1)) in coords: # case modal on -> X100
                    return True
                for cmd in GRBL_Wait_for_state_Cmds: 
                    if cmd in thecmd: #case G0 X100
                        return True 
                    if cmd in txtgcmd: #case G53 G0 X0
                        return True       
            except:
                pass  

            
        if self.is_tinyg==1: #TinyG
            try:                           
                mg = re.search('^([N,n,M,m,G,g,S,s,P,p,R,r,X,x,Y,y,Z,z])([+-]?\d*[\.,]?\d*)',txtgcmd)   
                thecmd=str(mg.group(1))+str(mg.group(2)) 
                if str(mg.group(1)) in coords: # case modal on -> X100
                    return True         
                if str(mg.group(1)) == 'N' or str(mg.group(1)) == 'n': #if starts with line number search after it the command
                    mg = re.search('^([N,n])([+-]?\d*[\.,]?\d*)\s?([M,m,G,g,S,s,P,p,R,r,X,x,Y,y,Z,z])([+-]?\d*[\.,]?\d*)',txtgcmd)   
                    thecmd=str(mg.group(3))+str(mg.group(4))              
                    if str(mg.group(3)) in coords: # case modal on -> X100
                        return True         
                for cmd in TinyG_Wait_for_state_Cmds:          
                    if cmd in thecmd: #case G0 X100
                        return True 
                    if cmd in txtgcmd: #case G53 G0 X0
                        return True       
            except:
                pass             
        if self.is_tinyg==2:
            try:                           
                mg = re.search('^([N,n,M,m,G,g,S,s,P,p,R,r,X,x,Y,y,Z,z])([+-]?\d*[\.,]?\d*)',txtgcmd)   
                thecmd=str(mg.group(1))+str(mg.group(2)) 
                if str(mg.group(1)) in ['R','r','P','p','S','s']:
                    if 'R000' in txtgcmd or 'S000' in txtgcmd or 'P000' in txtgcmd:
                        return Current_IswaitState  
                if str(mg.group(1)) in coords: # case modal on -> X100
                    return True         
                if str(mg.group(1)) == 'N' or str(mg.group(1)) == 'n': #if starts with line number search after it the command
                    mg = re.search('^([N,n])([+-]?\d*[\.,]?\d*)\s?([M,m,G,g,S,s,P,p,R,r,X,x,Y,y,Z,z])([+-]?\d*[\.,]?\d*)',txtgcmd)   
                    thecmd=str(mg.group(3))+str(mg.group(4))                                
                    if str(mg.group(3)) in coords: # case modal on -> X100
                        return True         
                for cmd in Marlin_Wait_for_state_Cmds:
                    if cmd in thecmd: #case G0 X100
                        return True 
                    if cmd in txtgcmd: #case G53 G0 X0
                        return True       
            except:
                pass             
            
            
        return False    

    


class XYZMulti:
    def __init__(self, grbl_port,grbl_baudrate,killer_event,IsRunning_event,selected_interface_id=0):
        self.IsRunning_event=IsRunning_event
        self.srl_cmd_queue = queue.Queue()
        self.grbl_event_hold= threading.Event()
        self.grbl_event_resume= threading.Event()
        self.grbl_event_status= threading.Event()
        self.grbl_event_softreset= threading.Event()
        self.grbl_event_stop= threading.Event()  
        self.grbl_event_hold.clear()
        self.grbl_event_resume.clear()
        self.grbl_event_status.clear()
        self.grbl_event_softreset.clear()     
        self.grbl_event_stop.clear()
        Required_actions=self.define_required_actions()
        self.CH=class_CH.Command_Handler(selected_interface_id,Required_actions=Required_actions)
        self.ser_read_thread = InterfaceSerialReaderWriterThread(grbl_port,grbl_baudrate, self.srl_cmd_queue, killer_event,self.grbl_event_hold,self.grbl_event_resume,self.grbl_event_status,self.grbl_event_softreset,self.grbl_event_stop,self.IsRunning_event,self.CH)
        

    def join(self):
        self.ser_read_thread.join()

    def start(self):
        self.ser_read_thread.start()   

    def home_offset(self, x, z):
        #self.srl_cmd_queue.put('G92 X' + str(x) + ' Y' + str(z) + '\n')
        cmd='setPosition'
        parnamelist=['X','Z']
        parvallist=[x,z]
        params=self.CH.fill_parameters(parnamelist,parvallist)        
        self.send_queue_command(cmd,params,True)
    
        
    def home_offset_xyz(self, x, y, z):  
        #self.srl_cmd_queue.put('G92 X' + str(x) + ' Y' + str(y)+ ' Z' + str(z) + '\n')        
        cmd='setPosition'
        parnamelist=['X','Y','Z']
        parvallist=[x,y,z]
        params=self.CH.fill_parameters(parnamelist,parvallist)  
        #print(params)      
        self.send_queue_command(cmd,params,True)

    def send_immediate_command(self,cmd,Parameters,Parammustok=True):            
        Gcode,isok=self.CH.Get_Gcode_for_Action(action,Parameters,Parammustok)
        if isok==True or Parammustok==False:
            self.srl_cmd_queue.self.ser_port.write(str(Gcode+'\n').encode())
        else:
            logging.error('Command not sent to serial!')  

    def send_queue_command(self,action,Parameters,Parammustok=True):            
        Gcode,isok=self.CH.Get_Gcode_for_Action(action,Parameters,Parammustok)
        if isok==True or Parammustok==False:
            self.srl_cmd_queue.put(Gcode+'\n')
        else:
            logging.error('Command not Added to queue!')    

    def goto_(self,x=None,y=None,z=None,f=None,atype=0):
        if atype==0:
            cmd='rapidMove'
        elif atype==1:     
            cmd='linearMove'
        parnamelist=[]
        parvallist=[]
        if x!=None:
            parnamelist.append('X')
            parvallist.append(x)
        if y!=None:
            parnamelist.append('Y')
            parvallist.append(y)
        if z!=None:
            parnamelist.append('Z')
            parvallist.append(z)        
        if f!=None:
            parnamelist.append('F')
            parvallist.append(f)        
            cmd='linearMove'
        params=self.CH.fill_parameters(parnamelist,parvallist)        
        self.send_queue_command(cmd,params,True)

    def goto_xz(self, x, z):
        #self.srl_cmd_queue.put('G0 X' + str(x) + ' Z' + str(z) + '\n')
        self.goto_(x,None,z,None,0)
    
    def goto_xy(self, x, y):
        #self.srl_cmd_queue.put('G0 X' + str(x) + ' Y' + str(y) + '\n')
        self.goto_(x,y,None,None,0)
        
    def goto_yz(self, y, z):
        #self.srl_cmd_queue.put('G0 Z' + str(z) + ' Y' + str(y) + '\n')
        self.goto_(None,y,z,None,0)
    
    def goto_xyz(self, x,y,z):
        #self.srl_cmd_queue.put('G0 X' + str(x) + ' Y' + str(y)+' Z' + str(z) + '\n')
        self.goto_(x,y,z,None,0)
    
    def goto_xyzf(self, x,y,z,f):
        #self.srl_cmd_queue.put('G1 X' + str(x) + ' Y' + str(y)+' Z' + str(z) +' F' + str(f) + '\n')
        self.goto_(x,y,z,f,1)

    def goto_x(self, x):
        #self.srl_cmd_queue.put('G0 X' + str(x) + '\n')
        self.goto_(x,None,None,None,0)

    def goto_z(self, z):
        #self.srl_cmd_queue.put('G0 Z' + str(z) + '\n')	
        self.goto_(None,None,z,None,0)
    
    def goto_y(self, y):
        #self.srl_cmd_queue.put('G0 Y' + str(y) + '\n')	
        self.goto_(None,y,None,None,0)
    
    def clear_state(self):   
        '''
        if self.ser_read_thread.is_tinyg==1:
            self.srl_cmd_queue.put( chr(24) + '\n') #reset signal
        else:   
            self.srl_cmd_queue.put( '$X' + '\n') #reset signal
            self.srl_cmd_queue.put( chr(24) + '\n') #reset signal 
        '''
        cmd='clearAlarm'        
        params={}
        self.send_queue_command(cmd,params,True)

        
        
                
    def read_grbl_config(self,Refresh=False,Showlog=False):
        if Refresh==True:
            self.ser_read_thread.Read_Actual_Config(Showlog)
        return self.ser_read_thread.grbl_Config

    def change_grbl_config_parameter(self,Param,Value):
        Showlog=False
        isaccepted=self.ser_read_thread.Change_Config_Parameter(Param,Value)
        return isaccepted
        #if isaccepted==False: # only needs to read if rejected
        #    self.ser_read_thread.Read_Actual_Config(Showlog)

    def read(self):
        return self.ser_read_thread.read()

    def grbl_gcode_cmd(self,gcode_cmd,toqueue=True):
        '''
        if self.ser_read_thread.is_tinyg==2 and gcode_cmd=='M410':
            self.grbl_stop()     
        elif self.ser_read_thread.is_tinyg==0 and gcode_cmd=='!':
            self.grbl_feed_hold()         
        elif self.ser_read_thread.is_tinyg==0 and gcode_cmd=='~':
            self.grbl_event_resume.set()
        elif self.ser_read_thread.is_tinyg==0 and gcode_cmd=='^X':                
            self.grbl_event_softreset.set()               
        else:
            self.srl_cmd_queue.put( str(gcode_cmd) + '\n') #send command
        '''
        Glist=[]
        aclist=['quickPause','quickResume','quickStop','queueFlush','clearAlarm','unlockAlarm','softReset','emergencyKill']
        actionparamsfound=self.CH.get_action_from_gcode(gcode_cmd,self.CH.id)
        immediate=False
        
        for action in actionparamsfound:
            if action in aclist and action is not '_action_code_':
                # if is exactly the immediate command
                immediate=self.CH.action_code_match_action(actionparamsfound['_action_code_'],action)    
                if immediate==True:
                    immediate=self.Do_immediate_command(action) #will set events and return True if it set the event
                    toqueue=False
                break            
        if immediate==False:            
            if toqueue==False:    
                self.send_immediate_command(gcode_cmd,{},True)
            else:
                self.srl_cmd_queue.put( str(gcode_cmd) + '\n') #send command

    
    def grbl_feed_hold(self):
        self.grbl_event_hold.set()

    def grbl_feed_start(self):
        self.grbl_event_resume.set()

    def grbl_softreset(self):
        self.grbl_event_softreset.set()    
    
    def grbl_stop(self):
        self.grbl_event_stop.set() # grbl makes hold -> soft reset 
    
    def grbl_status(self):
        self.grbl_event_status.set()
        return self.ser_read_thread.Send_Multi_Read(0)
    
    def Is_system_ready(self):
        return self.ser_read_thread.Is_system_ready()
    
    def Read_Config_Parameter(self,Param,Showlog=False):
        return self.ser_read_thread.Read_Config_Parameter(Param,Showlog)    

    def Send_Homing(self):        
        self.ser_read_thread.Send_Homing()
    
    def Reset_linesexecutedCount(self):
        self.ser_read_thread.Reset_linesexecutedCount()
    
    def Get_linesexecutedCount(self):
        return self.ser_read_thread.linesexecuted  

    def Get_linesacknowledgedCount(self):
        return self.ser_read_thread.linesacknkowledged      
    
    def Get_Queue_Count(self):    
        return self.ser_read_thread.queue_count()

    def Is_TinyG(self):
        return self.ser_read_thread.is_tinyg

    def Do_immediate_command(self,action):
        #aclist=['quickPause','quickResume','quickStop','queueFlush','clearAlarm','unlockAlarm','softReset','emergencyKill']
        if action is 'quickPause':
            self.grbl_event_hold.set()
            immediate=True
        elif action is 'quickResume':
            self.grbl_event_resume.set()
            immediate=True
        elif action is 'quickStop':
            self.grbl_event_stop.set()            
            immediate=True
        elif action is 'softReset':
            self.grbl_event_softreset.set()
            immediate=True
        elif action is 'emergencyKill':
            self.kill_event.set()
            immediate=True
        else:    
            immediate=False
        return immediate

    def get_Format_type_to_value(self,atype,aFormat,showlog=False):
        return self.ser_read_thread.get_Format_type_to_value(atype,aFormat,showlog)    
    
    def set_correct_type(self,txt,returntypetxt=False):
        return self.ser_read_thread.set_correct_type(txt,returntypetxt)

    def define_required_actions(self):
        return {'setPosition','interfaceId','interfaceName','rapidMove','linearMove','quickPause','reportBuildInfo',
                'userPause','userResume','statusReport','automaticstatusReports-Filtered','automaticstatusReports-Moving', 
               'quickResume','quickStop','queueFlush','clearAlarm','unlockAlarm','softReset','emergencyKill'}


