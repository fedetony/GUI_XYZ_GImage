import threading
import queue
import re
import logging
import time
from common import *

# install pySerial NOT serial!!!
import serial
import class_CH

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
ahandler=logging.StreamHandler()
ahandler.setLevel(logging.INFO)
ahandler.setFormatter(formatter)
log.addHandler(ahandler)

# ser reader thread (TINYG)
class SerialReaderWriterThread(threading.Thread):
    """
        A thread class to control XYZ read/write
    """

    def __init__(self, port, baudrate, rx_queue, kill_event,grbl_event_hold,grbl_event_start,grbl_event_status,grbl_event_softreset,grbl_event_stop,IsRunning_event):
        threading.Thread.__init__(self, name="XYZ thread")
        self.rx_queue = rx_queue
        self.IsRunning_event=IsRunning_event
        self.killer_event = kill_event
        self.grbl_event_hold=grbl_event_hold
        self.grbl_event_start=grbl_event_start
        self.grbl_event_status=grbl_event_status
        self.grbl_event_softreset=grbl_event_softreset
        self.grbl_event_stop=grbl_event_stop
        self.port = port
        self.baudrate=baudrate
        self.cycle_time = 0.1
        self.is_tinyg=1
        self.xyzsetupready=False
        self.wasrunningbeforepause=False
        self.linesexecuted=0
        self.linessenttoexec=0
        self.linesacknkowledged=0
        self.IscheckmodeOn=False
        self.Actualcmdneedstimetoexec=False
       
        log.info("Thread init XYZ")
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

        log.info("Thread Opening serial port")
        self.trytoopen_serial_port()
        # identify grbl
        try:
            count=1
            while count<100:
                grbl_out = str(self.ser_port.readline())
                if "Grbl" in grbl_out or "grbl" in grbl_out:
                    self.is_tinyg=0
                    log.info("Grbl identified")
                    count=count+100
                if "TinyG" in grbl_out or "tinyG" in grbl_out or "tinyg" in grbl_out:
                    self.is_tinyg=1
                    log.info("TinyG identified")
                    count=count+100
                if "Marlin" in grbl_out:
                    self.is_tinyg=2
                    log.info("Marlin identified")
                    count=count+100        
                time.sleep(0.1)
                count=count+1            
        except:
           pass
        
        #log.info("passed here 4 -> "+ str(self.is_tinyg))     
        
        if self.is_tinyg==1:
            log.info("setting up TinyG")
            self.cycle_time=0.1
            self.Initialize_Tinyg()
        if self.is_tinyg==2:
            log.info("setting up Marlin")
            self.cycle_time=0.2
            self.Initialize_Marlin()    
        else:
            log.info("setting up grbl")
            self.cycle_time=0.1    
            self.Initialize_Grbl()
    
    def trytoopen_serial_port(self):
        try:            
            #str(self.baudrate).encode('utf-8')
            self.ser_port = serial.Serial(self.port, self.baudrate, timeout=0)            
            self.ser_port.flushInput()  # Flush startup text in serial input
        except Exception as eee:
            log.error(eee)
            log.error("SerialReaderWriterThread: Failed to open serial port " + self.port)
            raise
    
    def run(self):        
        #log.info("Run entered")
        self.xyzsetupready=True
        #log.info("killer_event->"+ str(self.killer_event.wait(self.cycle_time)))
        #log.info("grbl_event_hold->"+ str(self.grbl_event_hold.wait(self.cycle_time)))
        while not self.killer_event.wait(self.cycle_time):            
            #log.info("Run entered 1")            
            if  self.grbl_event_hold.is_set():
                self.Send_grbl_Hold(1) #clears start flag
                log.info("Holding !!")
                while not self.grbl_event_start.is_set() and not self.killer_event.is_set() and not self.grbl_event_softreset.is_set():
                    self.Run_Read_Values()
                    time.sleep(self.cycle_time)
                    #log.info("Run entered 3")
                if self.grbl_event_start.is_set():
                    self.Send_grbl_Start(1) #clears hold flag   
                    log.info("Run Started!")
                    self.grbl_event_start.clear() #clear start flag

            if  self.grbl_event_softreset.is_set():
                log.info("Reseting!!")
                self.Send_grbl_SoftReset(1)
                time.sleep(1.5)   #Marlin blocks incoming data for 1 sec after M410 stop                     
                self.grbl_event_softreset.clear()
                #Clean queue
                with self.rx_queue.mutex:
                    self.rx_queue.queue.clear()            
            if  self.grbl_event_stop.is_set():
                log.info("Stopping!!")
                self.Send_Marlin_Stop(1)
                while self.grbl_event_stop.is_set() and not self.killer_event.is_set() and not self.grbl_event_softreset.is_set():
                    try:
                        #self.ser_port.xonxoff=False
                        time.sleep(5)
                        #self.ser_port.xonxoff=True
                        #self.ser_port.send_break(10) #send information after 10 secs
                        
                        log.info("Stopping try loop!!")
                        
                        if self.ser_port._checkClosed():
                            self.ser_port._close()
                            self.trytoopen_serial_port()
                        self.ser_port.write(str('M114'+'\n').encode())
                        #self.Run_Read_Values()
                        #time.sleep(self.cycle_time)
                        self.grbl_event_stop.clear()
                    except:                         
                        pass
                #Marlin blocks incoming data for 1 sec after M410 stop so makes error when comms try to reach                                   
                # Clean queue
                with self.rx_queue.mutex:
                    self.rx_queue.queue.clear()                 
            if self.killer_event.is_set():
                if self.is_tinyg==2:
                    self.Send_Marlin_Kill(1)
                else:    
                    self.Send_grbl_SoftReset(1)
                #log.info("Run entered 6")
            else:
                # check if there is something we should send to the serial
                try:
                    #log.info("Run entered 7")                    
                    new_cmd = self.rx_queue.get_nowait()
                    self.Actualcmdneedstimetoexec=self.Does_cmd_need_time_to_execute(new_cmd,self.Actualcmdneedstimetoexec)
                    
                    #log.info("Wait State :" + str(new_cmd)+'-->'+str(self.Actualcmdneedstimetoexec))
                    log.debug("Received :" + str(new_cmd))
                    self.ser_port.write(str(new_cmd).encode())
                    if self.is_tinyg!=1:
                        self.grbl_event_status.set()  
                    self.Do_line_Counting(new_cmd)      
                    
                except queue.Empty:
                    #self.grbl_event_status.clear()
                    pass
                # read the values
                self.Run_Read_Values()
        log.info(self.name + " killed")
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
                print('Not G0,G1,G2,G3')
                return Current_IswaitState                         
        except:    
            pass
        print('Is a G0,G1,G2,G3')
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

    def Run_Read_Values(self):
        if self.is_tinyg==1:
            grbl_out = str(self.ser_port.readline())  # Wait for grbl response with carriage return                    
            self.data=self.Process_Tinyg_data(grbl_out)
        elif self.is_tinyg==2:    
            self.Send_Marlin_Read(0,False)         # do not report ok-> False             
            grbl_out = self.readline_grbl()
            self.data=self.Process_Marlin_data(grbl_out)
        else:    
            #log.info("Run entered 9")
            self.Send_grbl_Read(0,False)         # do not report ok-> False             
            grbl_out = self.readline_grbl()
            self.data=self.Process_grbl_data(grbl_out)
        
        #self.Set_Last_Planned_Positionfromdata()    

    def Initialize_Tinyg(self):
        self.ser_port.write(str.encode("$sv=1\n"))
        self.ser_port.write(str.encode("$si=100\n"))
        time.sleep(0.1)
        self.ser_port.write(str.encode("$posz\n"))
        self.Read_Actual_Config()

    def Initialize_Marlin(self):
        self.ser_port.write(str.encode("M117 Marlin connected :)\n")) # Firmware info
        self.ser_port.write(str.encode("M115\n")) # Firmware info
        self.ser_port.write(str.encode("M114\n"))
        #self.ser_port.write(str.encode("M503\n")) # Report settings
        #self.Read_Actual_Config()

    def Initialize_Grbl(self):
        self.Read_Actual_Config()
    
    def Is_system_ready(self):
        return self.xyzsetupready

    def Read_Config_Parameter(self,Param,Showlog=True):
        valread=''
        try:
            for ccc in self.grbl_Config:
                #log.info('Found->'+ccc)
                if ccc=='$'+str(Param):                    
                    if Showlog==True:
                        log.info(ccc + '=' + str(self.grbl_Config[ccc]) + ' for ' + self.grbl_Config[ccc+'_Info'])                           
                    valread= self.grbl_Config[ccc]
        except:
            if Showlog==True:
                log.info('No Config $' + str(Param)) 
            pass
        return valread
           


    def Change_Config_Parameter(self,Param,Value):
        try:
            log.info('Sending configuration $' + str(Param)+ '=' + str(Value) + ' for ' + self.grbl_Config['$'+ str(Param)+'_Info'] )
            new_cmd = '$'+str(Param)+'='+str(Value)+'\n'   
            self.xyzsetupready=False                               
            self.ser_port.write(str(new_cmd).encode())
            line = self.readline_grbl() # Wait for grbl response with carriage return            
            self.xyzsetupready=True
            if "ok" in line:
                for ccc in self.grbl_Config:
                    if ccc == '$'+str(Param):
                        if self.grbl_Config[ccc+'_Type']=='int':
                            self.grbl_Config[ccc]=int(Value)
                        elif self.grbl_Config[ccc+'_Type']=='float':
                            self.grbl_Config[ccc]=float(Value)
                        else:
                            self.grbl_Config[ccc]=str(Value)    
                log.info("Parameter Accepted!")                
        except:
            log.info('Not Possible to configure ' + str(Param))    

    def Read_Actual_Config(self,showlog=1):
        #self.grbl_Config.clear()
        self.xyzsetupready=False
        new_cmd = '$$'+'\n'            
        self.ser_port.write(str(new_cmd).encode())

        line = ' '
        self.ser_port.reset_input_buffer()    
        linebuff=[]                
        while not "ok" in line:            
            line_r = self.ser_port.readline()  # Wait for grbl response with carriage return
            line_r = line_r.decode('utf-8')
            line_r=str(line_r)                        
            for ccc in line_r:
                if ccc != '\r' and ccc != '\n':
                    linebuff.append(ccc)
                if ccc == '\n':
                    line=''.join(linebuff)
                    if "Unknown command:" in line:
                        self.is_tinyg=2
                        log.info('Marlin identified! ')
                        showlog=0
                    if showlog==1:
                        log.info('Config Read: '+ line)                     
                    if (line):
                        if self.is_tinyg==0:  
                            try:           
                                #mf = re.search('.([0-9]*)=([+-]?[0-9]*[.][0-9]+)\s.(\w.*).',line)
                                mf = re.search('^\$(\d+)=([+-]?\d*[\.,]\d*)\s\((.*)\)',line)                               
                            except:
                                mf = None
                            try:
                                #mi = re.search('.([0-9]*)=([+-]?[0-9]*)\s.(\w.*).',line)
                                mi = re.search('^\$([+-]?\d+)=(\d+)\s\((.*)\)',line)
                            except:
                                mi = None
                        
                                
                            if mf is not None: #float type
                                #log.info('storing float')
                                #log.info('mf ->'+str(mf.groups()))
                                self.grbl_Config['$'+str(mf.group(1))]=float(mf.group(2))
                                self.grbl_Config['$'+str(mf.group(1))+'_Info']=str(mf.group(3))
                                self.grbl_Config['$'+str(mf.group(1))+'_Type']='float'
                                
                            if mi is not None: #int type
                                #log.info('storing int')
                                #log.info('mi ->'+str(mi.groups()))
                                if mi.group(2)!='':
                                    self.grbl_Config['$'+str(mi.group(1))]=int(mi.group(2))
                                    self.grbl_Config['$'+str(mi.group(1))+'_Info']=str(mi.group(3))
                                    self.grbl_Config['$'+str(mi.group(1))+'_Type']='int'                            
                        if self.is_tinyg==1:
                            try:           
                                mtg = re.search('^\[(\w+)\]\s(.*)[\s+]([+-]?\d+\S?\d*)\s*(.*)',line)
                            except:
                                mtg = None
                            if mtg is not None: #int type
                                #log.info('storing int')
                                #log.info('mtg ->'+str(mtg.groups()))                                
                                
                                text=str(mtg.group(2))
                                try:
                                    if str(mtg.group(4))!='':
                                        text=text+'('+str(mtg.group(4))+')'
                                except:
                                    pass    
                                self.grbl_Config['$'+str(mtg.group(1))+'_Info']=text
                                try:
                                    mtgfloat = re.search('([+-]?\d*[.,]\d+)',str(mtg.group(3)))
                                except:
                                    mtgfloat = None
                                try:
                                    if mtgfloat == None:
                                        mtgint = re.search('(^[+-]?\d*$)',str(mtg.group(3)))
                                except:
                                    mtgint = None   
                                     
                                if mtgfloat is not None:
                                    self.grbl_Config['$'+str(mtg.group(1))]=float(mtg.group(3))
                                    self.grbl_Config['$'+str(mtg.group(1))+'_Type']='float'
                                elif mtgint is not None:
                                    self.grbl_Config['$'+str(mtg.group(1))]=int(mtg.group(3))
                                    self.grbl_Config['$'+str(mtg.group(1))+'_Type']='int'    
                                else:
                                    self.grbl_Config['$'+str(mtg.group(1))]=str(mtg.group(3))
                                    self.grbl_Config['$'+str(mtg.group(1))+'_Type']='string'        
                    linebuff=[]         
        self.xyzsetupready=True

    def Process_Tinyg_data(self,grbl_out):
        if (grbl_out):
            #print( grbl_out.strip() )
            self.Set_Status_from_StateXYZ()
            any=0
            if "stat" in grbl_out:
                # read the values
                #print("ENTERED --------------------------------------")
                m = re.search('stat:([0-9])', grbl_out)
                #print(grbl_out)
                try:
                    self.data['STATE_XYZ'] = int(m.group(1))
                except AttributeError:
                    self.data['STATE_XYZ'] = 0
                #log.info('STATE ' + str(self.data['STATE_XYZ']))
                self.Set_Status_from_StateXYZ()
                if self.olddata['STATE_XYZ']>=5 and self.data['STATE_XYZ']<=4 or self.data['STATE_XYZ']==11: # state X-> 3
                    self.IsRunning_event.clear()  
                    self.linesexecuted=self.linesexecuted+1  
                else:
                    self.IsRunning_event.set()    
                
                any=1
                # print grbl_out

            if "posz" in grbl_out:
                # read the values
                m = re.search('posz:([+-]?[0-9]*[.][0-9]+)', grbl_out)
                self.data['ZPOS'] = float(m.group(1))
                #log.info('ZPOS ' + str(self.data['ZPOS']))
                any=1
                # print grbl_out

            if 'posx' in grbl_out:
                # print grbl_out.strip()
                m = re.search('posx:([+-]?[0-9]*[.][0-9]+)', grbl_out)
                self.data['XPOS'] = float(m.group(1))
                #log.info('XPOS ' + str(self.data['XPOS']))
                any=1
                # print grbl_out
            
            if 'posy' in grbl_out:
                # print grbl_out.strip()
                m = re.search('posy:([+-]?[0-9]*[.][0-9]+)', grbl_out)
                self.data['YPOS'] = float(m.group(1))
                #log.info('YPOS ' + str(self.data['YPOS']))
                any=1
                # print grbl_out
            if  any==1:   
                log.info('<' + str(self.data['STATUS'])+', POS:'+"\t"+str(self.data['XPOS'])+",\t" + str(self.data['YPOS'])+",\t" + str(self.data['ZPOS'])+'> ' +str(self.data['STATE_XYZ']))                                            
                for aaa in self.data:         
                    self.olddata[aaa]=self.data[aaa]
            else:
                text=grbl_out.replace("b'",'')
                text=text.replace("'",'')
                text=text.replace('\n','')
                text=text.replace("\n",'')
                if text!='':
                    log.info(text)    
        return self.data        

    def Send_grbl_Hold(self,sendcmd):
        #if not self.grbl_event_hold.is_set():
        self.grbl_event_hold.set()
        self.grbl_event_start.clear()
        if sendcmd==1:
            if self.is_tinyg==2:
                if self.data['STATE_XYZ']==3:
                    self.wasrunningbeforepause=False
                    self.ser_port.write(str('M0 Hold event Set'+'\n').encode())
                else:
                    self.wasrunningbeforepause=True
                    self.ser_port.write(str('P000'+'\n').encode())        
                log.info("Marlin on Hold!")
            elif self.is_tinyg==1:
                self.ser_port.write(str('!'+'\n').encode())
                log.info("TinyG on hold!")                    
            else:
                self.ser_port.write(str('!'+'\n').encode())
                log.info("grbl on hold!")
            time.sleep(0.2) # wait after command    

    def Send_Marlin_Kill(self,sendcmd):
        if not self.grbl_event_softreset.is_set():
            self.grbl_event_softreset.set()
        if sendcmd==1:
            self.ser_port.write(str('M112'+'\n').encode())
            log.info("Marlin Kill sent!")
            time.sleep(0.2) # wait after command
    
    def Send_Marlin_Stop(self,sendcmd):
        if not self.grbl_event_stop.is_set():
            self.grbl_event_stop.set()
        if sendcmd==1:
            if self.is_tinyg==2:
                self.ser_port.write(str('M410'+'\n').encode())
                log.info("Marlin Stop sent!")
            elif self.is_tinyg==0:
                self.Send_grbl_Hold(1)    
                self.Send_grbl_SoftReset(1)
                log.info("grbl hold->reset sent!") #should keep the position while halted then reset
            else:
                self.Send_grbl_Hold(1)    
                self.ser_port.write(str('M0'+'\n').encode()) #M1 should work too
                log.info("TinyG Stop sent!")                

    def Send_grbl_SoftReset(self,sendcmd):
        if not self.grbl_event_softreset.is_set():
            self.grbl_event_softreset.set()
        if sendcmd==1:
            if self.is_tinyg==2:
                self.ser_port.write(str('M999'+'\n').encode())    
                log.info("Marlin Reset!")
            else:    
                self.ser_port.write(str('^X'+'\n').encode())
                log.info("grbl softreset sent!")

    def Send_grbl_Start(self,sendcmd):         
        self.grbl_event_start.set()
        self.grbl_event_hold.clear()
        if sendcmd==1:    
            if self.is_tinyg==2:
                if self.wasrunningbeforepause==False:
                    self.ser_port.write(str('M108'+'\n').encode())
                else:    
                    self.ser_port.write(str('R000'+'\n').encode())    
                log.info("Marlin start!")
            else:    
                self.ser_port.write(str('~'+'\n').encode())
                log.info("grbl start!")
        time.sleep(0.2) # wait after command        
    
    def readline_grbl(self):
        line=''
        count=1
        linebuff=[]
        while True:
            line_r = self.ser_port.readline()  # Wait for grbl response with carriage return
            line_r = line_r.decode('utf-8')
            line_r=str(line_r)                       
            for ccc in line_r:
                if ccc != '\r' and ccc != '\n':
                    linebuff.append(ccc)
                if ccc == '\n':
                    line=''.join(linebuff)
                    return str(line)
            count=count+1        
            if count>128:
                return line
                          
    def Send_grbl_Read(self,waittime,showlog=True):    
        if self.is_tinyg==2:
           self.Send_Marlin_Read(waittime,showlog)
        else:       
            if  self.grbl_event_status.is_set(): 
                self.ser_port.write(str('?'+'\n').encode())
                grbl_out = self.readline_grbl()                
                self.data=self.Process_grbl_data(grbl_out,showlog)
                time.sleep(waittime)                        
        return self.data
    
    def Send_Marlin_Read(self,waittime,showlog=True):       
        if  self.grbl_event_status.is_set() and not self.grbl_event_softreset.is_set(): 
            #self.ser_port.write(str('S000'+'\n').encode())
            #if not self.grbl_event_softreset.is_set():
            #    self.ser_port.write(str(''+'\n').encode())
            grbl_out = self.readline_grbl()                
            self.data=self.Process_Marlin_data(grbl_out,showlog)
            time.sleep(waittime)                        
        return self.data    
        
    def Process_Marlin_data(self,grbl_out,showok=False):
        #X:0.00 Y:0.00 Z:0.00 E:0.00 Count X:0 Y:0 Z:12000
        if (grbl_out):
            #log.info("-----Received ->>>>"+grbl_out)
            #print( grbl_out.strip() )
            if "ok" in grbl_out:
                self.data['STATUS']='ok'
                if self.IsRunning_event.is_set():
                    self.IsRunning_event.clear()   
                    self.linesexecuted=self.linesexecuted+1
                    showok=True
                if showok==True:
                    log.info(self.data['STATUS'])
            if "error" in grbl_out:                
                self.data['STATUS']=grbl_out
                log.info(self.data['STATUS'])
                if self.Actualcmdneedstimetoexec==True or self.IsRunning_event.is_set():
                    self.IsRunning_event.clear()    
                    self.linesexecuted=self.linesexecuted+1
            if "ALARM" in grbl_out:
                self.data['STATUS']=grbl_out
            if "echo:" in grbl_out:
                if "busy: processing" not in grbl_out:
                    self.data['STATUS']=grbl_out    
                    log.info(self.data['STATUS'])
            if "action" in grbl_out:
                self.data['STATUS']=grbl_out    
                log.info(self.data['STATUS'])    
                    
            if "[" in grbl_out and "]" in grbl_out:
                self.data['STATUS']=grbl_out     
                log.info(self.data['STATUS'])
            if  "S_XYZ:" in grbl_out: 
                self.data['STATUS']=grbl_out   
                try:                                
                    m = re.search('S_XYZ:([0-9]+)', grbl_out)
                    self.data['STATE_XYZ']= int(m.group(1))
                    
                    if self.Compare_Hasdatachanged(self.olddata)==True:
                        if self.olddata['STATE_XYZ']!=self.data['STATE_XYZ']:
                            log.info('S_XYZ from '+ str(self.olddata['STATE_XYZ']) + ' to ' + str(self.data['STATE_XYZ']))                                      
                            if self.IsRunning_event.is_set() and self.olddata['STATE_XYZ']>=5 and self.data['STATE_XYZ']<=4 or self.data['STATE_XYZ']==11: # state X-> 3
                                self.IsRunning_event.clear()   
                                self.linesexecuted=self.linesexecuted+1 
                            else:
                                self.IsRunning_event.set()  
                            self.olddata['STATE_XYZ']=self.data['STATE_XYZ']              
                            self.Set_Status_from_StateXYZ()
                            self.olddata['STATUS']=self.data['STATUS']

                except:                        
                    log.info("No read State: " + grbl_out)    
            if  "X:" in grbl_out:  
                try:
                    isotherformat=False                                
                    m = re.search('X:([+-]?[0-9]*[.][0-9]+)\sY:([+-]?[0-9]*[.][0-9]+)\sZ:([+-]?[0-9]*[.][0-9]+)\sE:([+-]?[0-9]*[.][0-9]+)\sCount\sX:([+-]?[0-9]*)\sY:([+-]?[0-9]*)\sZ:([+-]?[0-9]*)', grbl_out)

                    #self.data['STATUS'] = 'S_XYZ:'+str(m.group(1))
                    self.data['MXPOS'] = int(m.group(5))
                    self.data['MYPOS'] = int(m.group(6))                
                    self.data['MZPOS'] = int(m.group(7))
                    self.data['XPOS'] = float(m.group(1))
                    self.data['YPOS'] = float(m.group(2))                
                    self.data['ZPOS'] = float(m.group(3))
                    self.data['EPOS'] = float(m.group(4))

                except:
                    isotherformat=True
                    pass
                if isotherformat==True:
                    try:                                
                        m = re.search('<(\w*),MPos:([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),WPos:([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),Ctl:(\d{8})>', grbl_out)

                        self.data['STATUS'] = 'S_XYZ:'+str(m.group(1))
                        self.data['MXPOS'] = float(m.group(2))
                        self.data['MYPOS'] = float(m.group(3))                
                        self.data['MZPOS'] = float(m.group(4))
                        self.data['MAPOS'] = float(m.group(5))
                        self.data['XPOS'] = float(m.group(6))
                        self.data['YPOS'] = float(m.group(7))                
                        self.data['ZPOS'] = float(m.group(8))
                        self.data['APOS'] = float(m.group(9))
                        self.data['CTL'] = float(m.group(10))
                    except:                        
                        log.info("No read: "+grbl_out)
                
                #self.data['STATE_XYZ']=0
                self.Set_StateXYZ_from_Status() 
                #if self.grbl_event_status.is_set():
                if self.Compare_Hasdatachanged(self.olddata)==True:
                    log.info(grbl_out + ' ' + str(self.data['STATE_XYZ'])) 
                
                   
                
                for aaa in self.data:         
                    self.olddata[aaa]=self.data[aaa]              
                #log.info('XPOS=' + str(self.data['XPOS'])+',YPOS=' + str(self.data['YPOS'])+',ZPOS=' + str(self.data['ZPOS'])+' '+ str(self.data['STATUS']) )
                #log.info('WXPOS=' + str(self.data['WXPOS'])+',WYPOS=' + str(self.data['WYPOS'])+',WZPOS=' + str(self.data['WZPOS'])+' '+ str(self.data['STATE_XYZ']) )
            self.Set_StateXYZ_from_Status()    
        return self.data     

    def Process_grbl_data(self,grbl_out,showok=False):
        #<Idle,MPos:0.000,0.000,0.000,WPos:0.000,0.000,0.000> if (grbl_out):
        if (grbl_out):
            #print( grbl_out.strip() )
            if "ok" in grbl_out:
                self.data['STATUS']='ok'
                if showok==True:
                    log.info(self.data['STATUS'])
            if "error" in grbl_out:                
                self.data['STATUS']=grbl_out
                log.info(self.data['STATUS'])
                if self.Actualcmdneedstimetoexec==True:
                    self.IsRunning_event.clear()    
                    self.linesexecuted=self.linesexecuted+1
            if "ALARM" in grbl_out:
                self.data['STATUS']=grbl_out
                log.info(self.data['STATUS'])
            if "[" in grbl_out and "]" in grbl_out:
                self.data['STATUS']=grbl_out     
                log.info(self.data['STATUS'])
            if  "<" in grbl_out and ">" in grbl_out:  
                try:
                    isotherformat=False                                
                    m = re.search('<(\w*),MPos:([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),WPos:([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+)>', grbl_out)

                    self.data['STATUS'] = 'S_XYZ:'+str(m.group(1))
                    self.data['MXPOS'] = float(m.group(2))
                    self.data['MYPOS'] = float(m.group(3))                
                    self.data['MZPOS'] = float(m.group(4))
                    self.data['XPOS'] = float(m.group(5))
                    self.data['YPOS'] = float(m.group(6))                
                    self.data['ZPOS'] = float(m.group(7))
                except:
                    isotherformat=True
                    pass
                if isotherformat==True:
                    try:                                
                        m = re.search('<(\w*),MPos:([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),WPos:([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),([+-]?[0-9]*[.][0-9]+),Ctl:(\d{8})>', grbl_out)

                        self.data['STATUS'] = 'S_XYZ:'+str(m.group(1))
                        self.data['MXPOS'] = float(m.group(2))
                        self.data['MYPOS'] = float(m.group(3))                
                        self.data['MZPOS'] = float(m.group(4))
                        self.data['MAPOS'] = float(m.group(5))
                        self.data['XPOS'] = float(m.group(6))
                        self.data['YPOS'] = float(m.group(7))                
                        self.data['ZPOS'] = float(m.group(8))
                        self.data['APOS'] = float(m.group(9))
                        self.data['CTL'] = float(m.group(10))
                    except:                        
                        log.info("No read: "+grbl_out)
                
                #self.data['STATE_XYZ']=0
                self.Set_StateXYZ_from_Status() 
                #if self.grbl_event_status.is_set():                
                if self.Compare_Hasdatachanged(self.olddata)==True:
                    log.info(grbl_out + ' ' + str(self.data['STATE_XYZ'])) 
                    # if state changed                
                    if self.olddata['STATE_XYZ']!=self.data['STATE_XYZ']:
                        if (self.data['STATE_XYZ']<=4 or self.data['STATE_XYZ']==11): # state X-> 3
                            self.IsRunning_event.clear()    
                            self.linesexecuted=self.linesexecuted+1
                        else:
                            self.IsRunning_event.set()   

                for aaa in self.data:         
                    self.olddata[aaa]=self.data[aaa]              
                #log.info('XPOS=' + str(self.data['XPOS'])+',YPOS=' + str(self.data['YPOS'])+',ZPOS=' + str(self.data['ZPOS'])+' '+ str(self.data['STATUS']) )
                #log.info('WXPOS=' + str(self.data['WXPOS'])+',WYPOS=' + str(self.data['WYPOS'])+',WZPOS=' + str(self.data['WZPOS'])+' '+ str(self.data['STATE_XYZ']) )
            self.Set_StateXYZ_from_Status()    
        return self.data     
    
    def Compare_Hasdatachanged(self,olddata):
        is_different=False
        for aaa in self.data:
            #log.info(str(olddata[aaa])+' vs ' + str(self.data[aaa]))
            if olddata[aaa]!=self.data[aaa]:
                is_different= True
                break        
        return is_different

    def Set_StateXYZ_from_Status(self):
        status=self.data['STATUS']
         #1=reset, 2=alarm, 3=idle, 4=end, 5=run, 6=hold, 7=probe, 8=cycling,  9=homing, 10 =jogging 11=error
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
        if self.is_tinyg==1:  
            cmd="G28.2 X0 Y0 Z0"+'\n' # tiny g code for homing   
        if self.is_tinyg==2:
            cmd="G28"+'\n'             
        else:
            cmd="$H"+'\n'
        self.rx_queue.put(cmd)    
        log.info("Homing Command set in queue")



    def read(self):
        return self.data


class XYZGrbl:

    def __init__(self, grbl_port,grbl_baudrate, killer_event,IsRunning_event):
        self.IsRunning_event=IsRunning_event
        self.srl_cmd_queue = queue.Queue()
        self.grbl_event_hold= threading.Event()
        self.grbl_event_start= threading.Event()
        self.grbl_event_status= threading.Event()
        self.grbl_event_softreset= threading.Event()
        self.grbl_event_stop= threading.Event()  
        self.grbl_event_hold.clear()
        self.grbl_event_start.clear()
        self.grbl_event_status.clear()
        self.grbl_event_softreset.clear()     
        self.grbl_event_stop.clear()
        self.ser_read_thread = SerialReaderWriterThread(grbl_port,grbl_baudrate, self.srl_cmd_queue, killer_event,self.grbl_event_hold,self.grbl_event_start,self.grbl_event_status,self.grbl_event_softreset,self.grbl_event_stop,self.IsRunning_event)
        #self.G_H=class_CCD.Command_Handler()

    def join(self):
        self.ser_read_thread.join()

    def start(self):
        self.ser_read_thread.start()

    def home_offset(self, x, z):
        self.srl_cmd_queue.put('G92 X' + str(x) + ' Y' + str(z) + '\n')
        
    def home_offset_xyz(self, x, y, z):
        self.srl_cmd_queue.put('G92 X' + str(x) + ' Y' + str(y)+ ' Z' + str(z) + '\n')

    def goto_xz(self, x, z):
        self.srl_cmd_queue.put('G0 X' + str(x) + ' Z' + str(z) + '\n')
    
    def goto_xy(self, x, y):
        self.srl_cmd_queue.put('G0 X' + str(x) + ' Y' + str(y) + '\n')
        
    def goto_yz(self, y, z):
        self.srl_cmd_queue.put('G0 Z' + str(z) + ' Y' + str(y) + '\n')
    
    def goto_xyz(self, x,y,z):
        self.srl_cmd_queue.put('G0 X' + str(x) + ' Y' + str(y)+' Z' + str(z) + '\n')
    
    def goto_xyzf(self, x,y,z,f):
        self.srl_cmd_queue.put('G1 X' + str(x) + ' Y' + str(y)+' Z' + str(z) +' F' + str(f) + '\n')

    def goto_x(self, x):
        self.srl_cmd_queue.put('G0 X' + str(x) + '\n')

    def goto_z(self, z):
        self.srl_cmd_queue.put('G0 Z' + str(z) + '\n')	
    
    def goto_y(self, y):
        self.srl_cmd_queue.put('G0 Y' + str(y) + '\n')	
    
    def clear_state(self):   
        if self.ser_read_thread.is_tinyg==1:
            self.srl_cmd_queue.put( chr(24) + '\n') #reset signal
        else:   
            self.srl_cmd_queue.put( '$X' + '\n') #reset signal
            self.srl_cmd_queue.put( chr(24) + '\n') #reset signal 
        
        
                
    def read_grbl_config(self,Refresh=False,Showlog=0):
        if Refresh==True:
            self.ser_read_thread.Read_Actual_Config(Showlog)
        return self.ser_read_thread.grbl_Config

    def change_grbl_config_parameter(self,Param,Value):
        Showlog=0
        self.ser_read_thread.Change_Config_Parameter(Param,Value)
        self.ser_read_thread.Read_Actual_Config(Showlog)

    def read(self):
        return self.ser_read_thread.read()

    def grbl_gcode_cmd(self,gcode_cmd):
        if self.ser_read_thread.is_tinyg==2 and gcode_cmd=='M410':
            self.grbl_stop()     
        elif self.ser_read_thread.is_tinyg==0 and gcode_cmd=='!':
            self.grbl_feed_hold()         
        elif self.ser_read_thread.is_tinyg==0 and gcode_cmd=='~':
            self.grbl_event_start.set()
        elif self.ser_read_thread.is_tinyg==0 and gcode_cmd=='^X':                
            self.grbl_event_softreset.set()               
        else:
            self.srl_cmd_queue.put( str(gcode_cmd) + '\n') #send command
    
    def grbl_feed_hold(self):
        self.grbl_event_hold.set()

    def grbl_feed_start(self):
        self.grbl_event_start.set()

    def grbl_softreset(self):
        self.grbl_event_softreset.set()    
    
    def grbl_stop(self):
        self.grbl_event_stop.set() # grbl makes hold -> soft reset 
    
    def grbl_status(self):
        self.grbl_event_status.set()
        return self.ser_read_thread.Send_grbl_Read(0)
    
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



