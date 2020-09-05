import threading
import queue
import re
import logging
import time
from common import *

# install pySerial NOT serial!!!
import serial

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s')

# ser reader thread (TINYG)
class SerialReaderWriterThread(threading.Thread):
    """
        A thread class to control XYZ read/write
    """

    def __init__(self, port, baudrate, rx_queue, kill_event,grbl_event_hold,grbl_event_start,grbl_event_status,grbl_event_softreset):
        threading.Thread.__init__(self, name="XYZ thread")
        self.rx_queue = rx_queue
        self.killer_event = kill_event
        self.grbl_event_hold=grbl_event_hold
        self.grbl_event_start=grbl_event_start
        self.grbl_event_status=grbl_event_status
        self.grbl_event_softreset=grbl_event_softreset
        self.port = port
        self.baudrate=baudrate
        self.cycle_time = 0.1
        self.is_tinyg=1
        self.xyzsetupready=False

        logging.info("Thread init XYZ")
        self.data = {}
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
        for aaa in self.data:         
            self.olddata[aaa]=self.data[aaa]              

        logging.info("Thread Opening serial port")
        try:            
            #str(self.baudrate).encode('utf-8')
            self.ser_port = serial.Serial(self.port, self.baudrate, timeout=0)            
            self.ser_port.flushInput()  # Flush startup text in serial input
        except Exception as eee:
            logging.error(eee)
            logging.error("SerialReaderWriterThread: Failed to open serial port " + self.port)
            raise
        # identify grbl
        try:
            count=1
            while count<100:
                grbl_out = str(self.ser_port.readline())
                if "Grbl" in grbl_out or "grbl" in grbl_out:
                    self.is_tinyg=0
                    logging.info("Grbl identified")
                    count=count+100
                if "TinyG" in grbl_out or "tinyG" in grbl_out or "tinyg" in grbl_out:
                    self.is_tinyg=1
                    logging.info("TinyG identified")
                    count=count+100    
                time.sleep(0.1)
                count=count+1            
        except:
           pass
        
        #logging.info("passed here 4 -> "+ str(self.is_tinyg))     
        
        if self.is_tinyg==1:
            logging.info("setting up TinyG")
            self.Initialize_Tinyg()
        else:
            logging.info("setting up grbl")
            self.cycle_time=0.1    
            self.Initialize_Grbl()

    def run(self):        
        #logging.info("Run entered")
        self.xyzsetupready=True
        #logging.info("killer_event->"+ str(self.killer_event.wait(self.cycle_time)))
        #logging.info("grbl_event_hold->"+ str(self.grbl_event_hold.wait(self.cycle_time)))
        while not self.killer_event.wait(self.cycle_time):            
            #logging.info("Run entered 1")
            
            if  self.grbl_event_hold.is_set():
                self.Send_grbl_Hold(1)
                logging.info("Holding !!")
                while not self.grbl_event_start.is_set() and not self.killer_event.is_set() and not self.grbl_event_softreset.is_set():
                    self.Run_Read_Values()
                    time.sleep(self.cycle_time)
                    #logging.info("Run entered 3")
                if self.grbl_event_start.is_set():
                    self.Send_grbl_Start(1) #clears hold flag   
                    logging.info("Run Started!")
            if  self.grbl_event_softreset.is_set():
                logging.info("Reseting!!")
                self.Send_grbl_SoftReset(1)                        
                self.grbl_event_softreset.clear()
                #Clean queue
                with self.rx_queue.mutex:
                    self.rx_queue.queue.clear()
                

            
            if self.killer_event.is_set():
                self.Send_grbl_SoftReset(1)
                #logging.info("Run entered 6")
            else:
                
                # check if there is something we should send to the serial
                try:
                    #logging.info("Run entered 7")
                    new_cmd = self.rx_queue.get_nowait()
                    logging.debug("Received :" + str(new_cmd))
                    self.ser_port.write(str(new_cmd).encode())
                    if self.is_tinyg!=1:
                        self.grbl_event_status.set()                        
                except queue.Empty:
                    #self.grbl_event_status.clear()
                    pass

                # read the values
                self.Run_Read_Values()
                
 
        logging.info(self.name + " killed")
        self.ser_port.close()
    
    def Run_Read_Values(self):
        if self.is_tinyg==1:
            grbl_out = str(self.ser_port.readline())  # Wait for grbl response with carriage return                    
            self.data=self.Process_Tinyg_data(grbl_out)
        else:    
            #logging.info("Run entered 9")
            self.Send_grbl_Read(0,False)         # do not report ok-> False             
            grbl_out = self.readline_grbl()
            self.data=self.Process_grbl_data(grbl_out)

    def Initialize_Tinyg(self):
        self.ser_port.write(str.encode("$sv=1\n"))
        self.ser_port.write(str.encode("$si=100\n"))
        time.sleep(0.1)
        self.ser_port.write(str.encode("$posz\n"))
        self.Read_Actual_Config()


    def Initialize_Grbl(self):
        self.Read_Actual_Config()
    
    def Is_system_ready(self):
        return self.xyzsetupready

    def Read_Config_Parameter(self,Param,Showlog=True):
        valread=''
        try:
            for ccc in self.grbl_Config:
                #logging.info('Found->'+ccc)
                if ccc=='$'+str(Param):                    
                    if Showlog==True:
                        logging.info(ccc + '=' + str(self.grbl_Config[ccc]) + ' for ' + self.grbl_Config[ccc+'_Info'])                           
                    valread= self.grbl_Config[ccc]
        except:
            if Showlog==True:
                logging.info('No Config $' + str(Param)) 
            pass
        return valread
           


    def Change_Config_Parameter(self,Param,Value):
        try:
            logging.info('Sending configuration $' + str(Param)+ '=' + str(Value) + ' for ' + self.grbl_Config['$'+ str(Param)+'_Info'] )
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
                logging.info("Parameter Accepted!")                
        except:
            logging.info('Not Possible to configure ' + str(Param))    

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
                    
                    if showlog==1:
                        logging.info('Config Read: '+ line)                     
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
                                #logging.info('storing float')
                                #logging.info('mf ->'+str(mf.groups()))
                                self.grbl_Config['$'+str(mf.group(1))]=float(mf.group(2))
                                self.grbl_Config['$'+str(mf.group(1))+'_Info']=str(mf.group(3))
                                self.grbl_Config['$'+str(mf.group(1))+'_Type']='float'
                                
                            if mi is not None: #int type
                                #logging.info('storing int')
                                #logging.info('mi ->'+str(mi.groups()))
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
                                #logging.info('storing int')
                                #logging.info('mtg ->'+str(mtg.groups()))                                
                                
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
                #logging.info('STATE ' + str(self.data['STATE_XYZ']))
                self.Set_Status_from_StateXYZ()
                any=1
                # print grbl_out

            if "posz" in grbl_out:
                # read the values
                m = re.search('posz:([+-]?[0-9]*[.][0-9]+)', grbl_out)
                self.data['ZPOS'] = float(m.group(1))
                #logging.info('ZPOS ' + str(self.data['ZPOS']))
                any=1
                # print grbl_out

            if 'posx' in grbl_out:
                # print grbl_out.strip()
                m = re.search('posx:([+-]?[0-9]*[.][0-9]+)', grbl_out)
                self.data['XPOS'] = float(m.group(1))
                #logging.info('XPOS ' + str(self.data['XPOS']))
                any=1
                # print grbl_out
            
            if 'posy' in grbl_out:
                # print grbl_out.strip()
                m = re.search('posy:([+-]?[0-9]*[.][0-9]+)', grbl_out)
                self.data['YPOS'] = float(m.group(1))
                #logging.info('YPOS ' + str(self.data['YPOS']))
                any=1
                # print grbl_out
            if  any==1:   
                logging.info('<' + str(self.data['STATUS'])+', POS:'+"\t"+str(self.data['XPOS'])+",\t" + str(self.data['YPOS'])+",\t" + str(self.data['ZPOS'])+'> ' +str(self.data['STATE_XYZ']))
            else:
                text=grbl_out.replace("b'",'')
                text=text.replace("'",'')
                text=text.replace('\n','')
                text=text.replace("\n",'')
                if text!='':
                    logging.info(text)    
        return self.data        

    def Send_grbl_Hold(self,sendcmd):
        if not self.grbl_event_hold.is_set():
            self.grbl_event_hold.set()
        if sendcmd==1:
            self.ser_port.write(str('!'+'\n').encode())
            logging.info("grbl on hold!")

    def Send_grbl_SoftReset(self,sendcmd):
        if not self.grbl_event_softreset.is_set():
            self.grbl_event_softreset.set()
        if sendcmd==1:
            self.ser_port.write(str('^X'+'\n').encode())
            logging.info("grbl softreset sent!")

    def Send_grbl_Start(self,sendcmd):  
        if not self.grbl_event_start.is_set():  
            self.grbl_event_start.set()
        if sendcmd==1:    
            self.ser_port.write(str('~'+'\n').encode())
            logging.info("grbl start!")
        if self.grbl_event_hold.is_set():
            self.grbl_event_hold.clear()
            logging.info("grbl hold flag clear!")
    
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
        if  self.grbl_event_status.is_set(): 
            self.ser_port.write(str('?'+'\n').encode())
            grbl_out = self.readline_grbl()                
            self.data=self.Process_grbl_data(grbl_out,showlog)
            time.sleep(waittime)                        
        return self.data
        
    def Process_grbl_data(self,grbl_out,showok=False):
        #<Idle,MPos:0.000,0.000,0.000,WPos:0.000,0.000,0.000> if (grbl_out):
        if (grbl_out):
            #print( grbl_out.strip() )
            if "ok" in grbl_out:
                self.data['STATUS']='ok'
                if showok==True:
                    logging.info(self.data['STATUS'])
            if "error" in grbl_out:                
                self.data['STATUS']=grbl_out
                logging.info(self.data['STATUS'])
            if "ALARM" in grbl_out:
                self.data['STATUS']=grbl_out
                logging.info(self.data['STATUS'])
            if "[" in grbl_out and "]" in grbl_out:
                self.data['STATUS']=grbl_out     
                logging.info(self.data['STATUS'])
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
                        logging.info("No read: "+grbl_out)
                
                #self.data['STATE_XYZ']=0
                self.Set_StateXYZ_from_Status() 
                #if self.grbl_event_status.is_set():
                if self.Compare_Hasdatachanged(self.olddata)==True:
                    logging.info(grbl_out + ' ' + str(self.data['STATE_XYZ'])) 
                for aaa in self.data:         
                    self.olddata[aaa]=self.data[aaa]              
                #logging.info('XPOS=' + str(self.data['XPOS'])+',YPOS=' + str(self.data['YPOS'])+',ZPOS=' + str(self.data['ZPOS'])+' '+ str(self.data['STATUS']) )
                #logging.info('WXPOS=' + str(self.data['WXPOS'])+',WYPOS=' + str(self.data['WYPOS'])+',WZPOS=' + str(self.data['WZPOS'])+' '+ str(self.data['STATE_XYZ']) )
            self.Set_StateXYZ_from_Status()    
        return self.data     
    
    def Compare_Hasdatachanged(self,olddata):
        is_different=False
        for aaa in self.data:
            #logging.info(str(olddata[aaa])+' vs ' + str(self.data[aaa]))
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
        else:
            cmd="$H"+'\n'
        self.rx_queue.put(cmd)    
        logging.info("Homing Command set in queue")



    def read(self):
        return self.data


class XYZGrbl:

    def __init__(self, grbl_port,grbl_baudrate, killer_event):
        self.srl_cmd_queue = queue.Queue()
        self.grbl_event_hold= threading.Event()
        self.grbl_event_start= threading.Event()
        self.grbl_event_status= threading.Event()
        self.grbl_event_softreset= threading.Event()  
        self.grbl_event_hold.clear()
        self.grbl_event_start.clear()
        self.grbl_event_status.clear()
        self.grbl_event_softreset.clear()     
        self.ser_read_thread = SerialReaderWriterThread(grbl_port,grbl_baudrate, self.srl_cmd_queue, killer_event,self.grbl_event_hold,self.grbl_event_start,self.grbl_event_status,self.grbl_event_softreset)

    def join(self):
        self.ser_read_thread.join()

    def start(self):
        self.ser_read_thread.start()

    def home_offset(self, x, z):
        self.srl_cmd_queue.put('g92 x' + str(x) + ' z' + str(z) + '\n')
        
    def home_offset_xyz(self, x, y, z):
        self.srl_cmd_queue.put('g92 x' + str(x) + ' y' + str(y)+ ' z' + str(z) + '\n')

    def goto_xz(self, x, z):
        self.srl_cmd_queue.put('g0 x' + str(x) + ' z' + str(z) + '\n')
    
    def goto_xy(self, x, y):
        self.srl_cmd_queue.put('g0 x' + str(x) + ' y' + str(y) + '\n')
        
    def goto_yz(self, y, z):
        self.srl_cmd_queue.put('g0 z' + str(z) + ' y' + str(y) + '\n')
    
    def goto_xyz(self, x,y,z):
        self.srl_cmd_queue.put('g0 x' + str(x) + ' y' + str(y)+' z' + str(z) + '\n')

    def goto_x(self, x):
        self.srl_cmd_queue.put('g0 x' + str(x) + '\n')

    def goto_z(self, z):
        self.srl_cmd_queue.put('g0 z' + str(z) + '\n')	
    
    def goto_y(self, y):
        self.srl_cmd_queue.put('g0 y' + str(y) + '\n')	
    
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
        self.srl_cmd_queue.put( str(gcode_cmd) + '\n') #send command
    
    def grbl_feed_hold(self):
        self.grbl_event_hold.set()

    def grbl_feed_start(self):
        self.grbl_event_start.set()

    def grbl_softreset(self):
        self.grbl_event_softreset.set()    
    
    def grbl_status(self):
        self.grbl_event_status.set()
        return self.ser_read_thread.Send_grbl_Read(0)
    
    def Is_system_ready(self):
        return self.ser_read_thread.Is_system_ready()
    
    def Read_Config_Parameter(self,Param,Showlog=False):
        return self.ser_read_thread.Read_Config_Parameter(Param,Showlog)    

    def Send_Homing(self):        
        self.ser_read_thread.Send_Homing()




