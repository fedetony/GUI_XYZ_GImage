import threading
import queue
import re
import logging
import time
import io
from common import *
import thread_queueStream

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
ahandler=logging.StreamHandler()
ahandler.setLevel(logging.INFO)
ahandler.setFormatter(formatter)
log.addHandler(ahandler)

class XYZ_Gcode_Stream(threading.Thread):
    def __init__(self,xyz_thread,killer_event,holding_event,stoping_event,IsRunning_event):
        threading.Thread.__init__(self, name="Gcode thread")
        log.info("XYZ Gcode Stream Started")        
        self.IsRunning_event=IsRunning_event 
        self.xyz_thread=xyz_thread
        self.killer_event=killer_event
        self.holding_event=holding_event
        self.stoping_event=stoping_event        
        self.cycle_time=self.xyz_thread.ser_read_thread.cycle_time                       
        # typeofstream=0 Wait until each Command returns finish signal to send next one.(Slow) 
        # typeofstream=1 Send all to machine and dont wait for response. 
        # typeofstream=2 Send a number of lines and count the returns.
        self.type_of_stream=0 
        self.state_xyz=0
        self.oldstate_xyz=0
        self.istext2stream=False
        self.text_queue = queue.Queue()
        self.streamsize=0
        self.line_count=0
        self.bufflines=0
        self.bufflinesize=5   
        self.linesfinalized_count=0
        self.lastlinesfinalized_count=0
        self.lastRunningstate=self.IsRunning_event.is_set()        
        self.sqkill_ev = threading.Event()
        self.sqkill_ev.clear()  
        self.isqstream=False

        
    '''    
        #self.linesfin_count=Running_Event_Count_Update(self.IsRunning_event) 
        #self.linesfin_count.bind_to(self.Update_RunningCount)   
             
                
    #def Update_RunningCount(self):
    #    self.linesfinalized_count=self.linesfin_count.Count_events()

    def Count_Running_Events(self):
        if not self.IsRunning_event.is_set() and self.lastRunningstate==True:        
            self.linesfinalized_count=self.linesfinalized_count+1  
        self.lastRunningstate=self.IsRunning_event.is_set() 
    '''
    def get_state(self):        
        self.state_xyz=self.data['STATE_XYZ'] 

    def run(self):                
        count=0
        while not self.killer_event.wait(self.cycle_time):   
            try:
                self.data = self.xyz_thread.read()                
                self.get_state()
                if self.stoping_event.is_set()==True:
                    self.Stop_Clear()
                if self.holding_event.is_set()==False:                    
                    self.Do_the_streaming(self.type_of_stream)            
            except Exception as e:
                if count==0:
                    log.error(e)
                    log.info("XYZ Gcode Stream can't get data to update")                         
                else:
                    count=count+1
                if count>=2000:
                    count=0        
        self.sqkill_ev.set()
        log.info("XYZ Gcode Stream killed")         

    def Do_the_streaming(self,typeofstream=0):
        # typeofstream=0 Wait until each Command returns finish signal to send next one.(Slow)
        # typeofstream=1 Send all to machine and dont wait for response. 
        # typeofstream=2 Send a number of lines and count the returns.        
        
        self.IfEnd_of_Stream()
        if self.istext2stream==False or self.isqstream==False:
            return                    
        if typeofstream==0:  
            #print('Running event',self.IsRunning_event.is_set())                                                  
            if not self.IsRunning_event.is_set():                  
                try:
                    if self.qstream.get_num_of_commands_left()>0:                        
                        [buff,txt,consumed,left,tot,totfile]=self.qstream.get_all_nums(False)                          
                        if buff>0:    
                            self.xyz_thread.ser_read_thread.Streamwriting=True                                                                          
                            line2stream=self.qstream.Consume_buff(True)
                            self.line_count=consumed
                            self.bufflines=buff
                            log.info("Sending command->("+str(self.line_count)+") "+line2stream)
                            self.Isneededtimeforcommand=False
                            self.stream_one_line(line2stream,False)   #send through command recognition                              
                            [is_ack,is_ackcexecuted,is_ackcreceived,is_error,is_alarm]=self.xyz_thread.Get_reads_bools()                                            
                            
                            if is_error==True or is_alarm==True:
                                log.info("Error in Stream detected! (" + str(line2stream)+') ' )
                                self.xyz_thread.ser_read_thread.Streamwriting=False                                                                          
                                self.Stop_Clear()                                                                              
                            self.xyz_thread.ser_read_thread.Streamwriting=False                                                                              
                            self.wait_until_finished(typeofstream)    #Clears Running_event                           
                except Exception as e:                
                    log.error(e)
                    log.error('On Do the streaming -> typeofstream==0')                                                            
                    pass
        elif typeofstream==1:  
            #print('Running event',self.IsRunning_event.is_set())                                                  
            if not self.IsRunning_event.is_set():                  
                try:
                    if self.qstream.get_num_of_commands_left()>0:                        
                        [buff,txt,consumed,left,tot,totfile]=self.qstream.get_all_nums(False)                          
                        if buff>0:    
                            self.xyz_thread.ser_read_thread.Streamwriting=True                                                                          
                            line2stream=self.qstream.Consume_buff(True)
                            self.line_count=consumed
                            self.bufflines=buff
                            log.info("Sending command->("+str(self.line_count)+") "+line2stream)
                            self.Isneededtimeforcommand=False
                            self.stream_one_line(line2stream,False)   #send through command recognition                                                          
                            is_ack=False
                            errorcount=0
                            is_error=False 
                            is_alarm=False
                            while is_ack==False and is_error==False and is_alarm==False:
                                if self.stoping_event.is_set()==True:
                                    self.Stop_Clear()
                                if self.killer_event.is_set()==True:
                                    self.isqstream=False
                                    self.sqkill_ev.set()                     
                                    break  
                                grbl_out=self.xyz_thread.ser_read_thread.Wait_for_serial_response(self.cycle_time,exitcount=20,loginfo=False,teaseini=26)                             
                                self.xyz_thread.ser_read_thread.Process_Read_Data(grbl_out,showok=False)
                                [is_ack,is_ackcexecuted,is_ackcreceived,is_error,is_alarm]=self.xyz_thread.Get_reads_bools()                                                                   
                                self.data = self.xyz_thread.read()                
                                self.get_state()                                              
                                if is_error==True or is_alarm==True: 
                                    while self.xyz_thread.Is_command_running()==True:                                   
                                        time.sleep(self.cycle_time)
                                        if self.stoping_event.is_set()==True or self.killer_event.is_set()==True or self.sqkill_ev.is_set():                     
                                            break 
                                    if errorcount==0:
                                        self.stream_one_line(line2stream,False)   #send through command recognition                                                          
                                    else:        
                                        self.stream_one_line(line2stream,True)   #send directly as gcode                              
                                    errorcount=errorcount+1
                                if errorcount>10:
                                    log.info("Error or alarm in Stream detected! (" + str(line2stream)+') ' )
                                    self.xyz_thread.ser_read_thread.Streamwriting=False                                                                          
                                    self.Stop_Clear()       
                                #self.log_Counts()
                            self.xyz_thread.ser_read_thread.Streamwriting=False                                                                                                              
                except Exception as e:                
                    log.error(e)
                    log.error('On Do the streaming -> typeofstream==1')                                                            
                    pass        
        '''               
        elif typeofstream==2:
            try:                        
                
                if self.bufflines<self.bufflinesize:                        
                    if self.text_queue.qsize()>0:                        
                        self.Do_buffline_count()
                        self.Do_line_count()
                        self.istext2stream=True                    
                    line2stream= self.text_queue.get_nowait()                            
                    log.info("Sending command->("+str(self.line_count)+") "+line2stream)
                    #log.info("Buffline->"+str(self.bufflines))
                    self.stream_one_line(line2stream)                                      
                    self.data = self.xyz_thread.read()                
                    self.get_state()
                    if self.state_xyz==11: # error
                        log.info("Error in Gcode detected! (" + str(line2stream)+') ' )
                        self.Stop_Clear()                       
                    self.wait_until_finished(typeofstream)    #Clears Running_event                                    
                else:
                    self.wait_until_finished(typeofstream)    
            except queue.Empty:                    
                pass            
        '''
     
        
        
        #else jus closes the msgbox
    def wait_until_finished(self,typeofstream):          
        if typeofstream==0:  
            
            while self.IsRunning_event.wait(self.cycle_time): 
                
                if self.xyz_thread.Is_command_running()==False:               
                    break
                if self.Isneededtimeforcommand==False:
                    break
                if self.stoping_event.is_set()==True:
                    self.Stop_Clear()
                if self.killer_event.is_set()==True:
                    self.isqstream=False
                    self.sqkill_ev.set()                     
                    break    
                self.data = self.xyz_thread.read()                
                self.get_state()        
                if self.oldstate_xyz!=self.state_xyz:
                    self.oldstate_xyz=self.state_xyz
            
                # ask reports while waiting    
                #if self.washasautoReport==False:
                #self.xyz_thread.grbl_event_status.clear()
                #cmd='statusReport'            
                #Gcode,isok=self.xyz_thread.ser_read_thread.CH.Get_Gcode_for_Action(cmd,{},True)
                #self.xyz_thread.ser_read_thread.port_write(Gcode,isok)  
                    
                self.IfEnd_of_Stream()
            

            self.linesfinalized_count=self.xyz_thread.Get_linesexecutedCount()              
            #self.log_Counts()
        '''

        if typeofstream==2:              
            #log.info("Debug Buffline->"+str(self.bufflines))                 
            self.linesfinalized_count=self.xyz_thread.Get_linesexecutedCount()  
            linesacknowledged_count=self.xyz_thread.Get_linesacknowledgedCount()
            num_events=self.linesfinalized_count-self.lastlinesfinalized_count+1
            log.info("Number events Finished->"+str(num_events))
            if num_events>=self.bufflinesize:    
                self.bufflines=0
                self.lastlinesfinalized_count=self.linesfinalized_count            
            self.IfEnd_of_Stream()
        '''
    
    def log_Counts(self):
        linesacknowledged_count=self.xyz_thread.Get_linesacknowledgedCount()
        num_events=self.linesfinalized_count-self.lastlinesfinalized_count+1
        log.info('In Buffer:'+str(self.qstream.get_num_of_commands_buff())+' Consumed:'+str(self.qstream.get_num_of_commands_consumed())+' Total:'+str(self.qstream.get_num_of_total_commands_onFile()))
        log.info('Finished:'+str(self.linesfinalized_count)+' Acknowledged:'+str(linesacknowledged_count)+' Num events'+str(num_events))

    def IfEnd_of_Stream(self):                        
        try:
            self.isqstream=self.qstream.is_alive()
            if self.isqstream==True:
                if self.qstream.Stream_Finished==True:       
                    log.info("Stream Finished:")
                    [buff,txt,consumed,left,tot,totfile]=self.qstream.get_all_nums(True)
                    self.istext2stream=False
                    self.line_count=0
                    #self.streamsize=0  
                    self.bufflines=0                    
                    #Wait to terminate the thread
                    self.sqkill_ev.set()
                    while self.qstream.is_alive()==True:                    
                        time.sleep(self.cycle_time)
                    #self.xyz_thread.ser_read_thread.hasautoReport=self.washasautoReport
                    #self.IsRunning_event.clear()                
                    self.xyz_thread.ser_read_thread.set_selfconfigvalues()
        except:
            self.isqstream=False
            pass    

    def Stop_Clear(self):
        if self.istext2stream==True:
            self.text_queue.empty()
            self.istext2stream=False
            log.info("Gcode Stream Stopped!")
        if self.isqstream==True:
            self.isqstream=False                    
        self.sqkill_ev.set()     
        self.xyz_thread.ser_read_thread.set_selfconfigvalues()   #Restore configuration               
        self.stoping_event.clear()

    def read(self):
        return self.data

    def Stream_queue(self,text2stream,Pbarstream=None,Pbarbuffer=None):  
        #self.washasautoReport=self.xyz_thread.ser_read_thread.hasautoReport
        #Setting autoreport to True for the send read commands at same time of stream commands
        #self.xyz_thread.ser_read_thread.hasautoReport=True 
        self.xyz_thread.ser_read_thread.logPosition=False
        self.xyz_thread.ser_read_thread.logStateChange=True 
        self.sqkill_ev.clear()
        self.istext2stream=True 
        cyctime=self.cycle_time/2 #Thread can be much faster
        self.qstream=thread_queueStream.queueStream(text2stream,cyctime,self.sqkill_ev,Refill_value=5,Buffer_size=20,Pbar_buffer=Pbarbuffer,Pbar_Stream=Pbarstream)
        self.qstream.start()        
        self.isqstream=True                     
        self.xyz_thread.Reset_linesexecutedCount()    

    def Islinecontent_ok(self,line):
        contents=line.strip(' ')
        contents=contents.strip('\n')        
        if line=='' or contents=='':
            return False
        return True    

    def stream_one_line(self,line2stream,Fast=True):
        if self.istext2stream==True:     
            if Fast==True:
                #Command recognition routine
                self.xyz_thread.send_queue_gcode(line2stream) 
                self.Isneededtimeforcommand=self.xyz_thread.Is_time_needed_for_command()
            else:                   
                #This analizes which action is
                self.xyz_thread.grbl_gcode_cmd(line2stream)
                self.Isneededtimeforcommand=None
            



