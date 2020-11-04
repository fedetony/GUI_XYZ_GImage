import threading
import queue
import re
import logging
import time
import io
from common import *


logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s')

class XYZ_Gcode_Stream(threading.Thread):
    def __init__(self,xyz_thread,killer_event,holding_event,stoping_event,IsRunning_event):
        threading.Thread.__init__(self, name="XYZ Gcode Stream")
        logging.info("XYZ Gcode Stream Started")        
        self.IsRunning_event=IsRunning_event 
        self.xyz_thread=xyz_thread
        self.killer_event=killer_event
        self.holding_event=holding_event
        self.stoping_event=stoping_event        
        self.cycle_time=0.1                       
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
                    logging.error(e)
                    logging.info("XYZ Gcode Stream can't get data to update")                         
                else:
                   count=count+1
                if count>=2000:
                    count=0        
        logging.info("XYZ Gcode Stream killed")         

    def Do_the_streaming(self,typeofstream=0):
        # typeofstream=0 Wait until each Command returns finish singl to send next one.(Slow)
        # typeofstream=1 Send all to machine and dont wait for response. 
        # typeofstream=2 Send a number of lines and count the returns.
        if typeofstream==0:
            try:                                        
                if not self.IsRunning_event.is_set():      
                    if self.text_queue.qsize()>0:
                        self.Do_line_count()
                        self.istext2stream=True
                    line2stream= self.text_queue.get_nowait()                            
                    logging.info("Sending command->("+str(self.line_count)+") "+line2stream)
                    self.stream_one_line(line2stream)                                      
                    self.data = self.xyz_thread.read()                
                    self.get_state()
                    if self.state_xyz==11: # error
                        logging.info("Error in Gcode detected! (" + str(line2stream)+') ' )
                        self.Stop_Clear()                                
                    self.wait_until_finished(typeofstream)    #Clears Running_event
            except queue.Empty:                    
                pass   
        elif typeofstream==1:
            try:                      
                if not self.IsRunning_event.is_set() or self.text_queue.qsize()>0:      
                    #logging.info(' type 1 stream Is running event->'+str(self.IsRunning_event.is_set()))                                  
                    if self.text_queue.qsize()>0:
                        self.Do_line_count()
                        self.istext2stream=True
                    line2stream= self.text_queue.get_nowait()                            
                    logging.info("Sending command->("+str(self.line_count)+") "+line2stream)
                    self.stream_one_line(line2stream)                                      
                    self.data = self.xyz_thread.read()                
                    self.get_state()
                    if self.state_xyz==11: # error
                        logging.info("Error in Gcode detected! (" + str(line2stream)+') ' )
                        self.Stop_Clear()   
                    #self.IsRunning_event.clear()                                 
            except queue.Empty:                    
                pass    
        elif typeofstream==2:
            try:                        
                
                if self.bufflines<self.bufflinesize:                        
                    if self.text_queue.qsize()>0:                        
                        self.Do_buffline_count()
                        self.Do_line_count()
                        self.istext2stream=True                    
                    line2stream= self.text_queue.get_nowait()                            
                    logging.info("Sending command->("+str(self.line_count)+") "+line2stream)
                    #logging.info("Buffline->"+str(self.bufflines))
                    self.stream_one_line(line2stream)                                      
                    self.data = self.xyz_thread.read()                
                    self.get_state()
                    if self.state_xyz==11: # error
                        logging.info("Error in Gcode detected! (" + str(line2stream)+') ' )
                        self.Stop_Clear()                       
                    self.wait_until_finished(typeofstream)    #Clears Running_event                                    
                else:
                    self.wait_until_finished(typeofstream)    
            except queue.Empty:                    
                pass            

    def wait_until_finished(self,typeofstream):  
        if typeofstream==1:
            time.sleep(self.cycle_time)
            self.data = self.xyz_thread.read()                
            self.get_state()        
            if self.oldstate_xyz!=self.state_xyz:
                self.oldstate_xyz=self.state_xyz                 
            self.IfEnd_of_Stream()

        if typeofstream==0:            
            while self.IsRunning_event.wait(self.cycle_time): 
                time.sleep(self.cycle_time)
                if self.stoping_event.is_set()==True:
                    self.Stop_Clear()
                if self.killer_event.is_set()==True:
                    break    
                self.data = self.xyz_thread.read()                
                self.get_state()        
                if self.oldstate_xyz!=self.state_xyz:
                    self.oldstate_xyz=self.state_xyz
                self.IfEnd_of_Stream()
            self.linesfinalized_count=self.xyz_thread.Get_linesexecutedCount()  
            linesacknowledged_count=self.xyz_thread.Get_linesacknowledgedCount()
            num_events=self.linesfinalized_count-self.lastlinesfinalized_count+1
            logging.info("Type 0 Number Lines Finished->"+str(self.linesfinalized_count))    
            logging.info("Type 0 Number Lines Acknowledged->"+str(linesacknowledged_count))    

            logging.info("Type 0 Number events Finished->"+str(num_events))    

        if typeofstream==2:              
            #logging.info("Debug Buffline->"+str(self.bufflines))                 
            self.linesfinalized_count=self.xyz_thread.Get_linesexecutedCount()  
            linesacknowledged_count=self.xyz_thread.Get_linesacknowledgedCount()
            num_events=self.linesfinalized_count-self.lastlinesfinalized_count+1
            logging.info("Number events Finished->"+str(num_events))
            if num_events>=self.bufflinesize:    
                self.bufflines=0
                self.lastlinesfinalized_count=self.linesfinalized_count            
            self.IfEnd_of_Stream()
    
    def IfEnd_of_Stream(self):                
        if self.text_queue.qsize()==0:   #Nothing in queue             
            self.istext2stream=False
            self.line_count=0
            #self.streamsize=0  
            self.bufflines=0     
            #1=reset, 2=alarm, 3=idle, 4=end, 5=run, 6=hold, 7=probe, 8=cycling,  9=homing, 10 =jogging 11=error                         
            if self.state_xyz<5 or self.state_xyz==11:     # is not running    
                logging.info("End of Gcode Stream :)")       
                self.IsRunning_event.clear() #Event is cleared in INIT state only here else in XYZ thread        
    
    def Do_buffline_count(self):
        if self.line_count==0:
            self.bufflines=0            
        elif self.line_count>self.streamsize:
            self.line_count=0
            self.bufflines=0                
        elif self.line_count<=self.streamsize and self.streamsize>0 and self.line_count>0:            
            if self.bufflines<=self.bufflinesize:       
                self.bufflines=self.bufflines+1  
        else:
            self.bufflines=self.bufflinesize

        

    def Do_line_count(self):
        if self.line_count==0:
            self.bufflines=0
            self.streamsize=self.text_queue.qsize()
            self.line_count=1
            self.xyz_thread.Reset_linesexecutedCount()            
            self.linesfinalized_count=self.xyz_thread.Get_linesexecutedCount()
            self.lastlinesfinalized_count=self.linesfinalized_count
            self.lastRunningstate=self.IsRunning_event.is_set()
            #logging.info('A reset Here')
        elif self.line_count>self.streamsize:
            self.line_count=0
            self.bufflines=0                
        elif self.line_count<=self.streamsize and self.streamsize>0 and self.line_count>0:
            self.line_count=self.line_count+1                        
        try:
            if self.streamsize>0:
                self.Pbarupdate.SetStatus(self.line_count/self.streamsize*100)  
        except:
            pass      
        self.linesfinalized_count=self.xyz_thread.Get_linesexecutedCount()
        

    def Stop_Clear(self):
        if self.istext2stream==True:
            self.text_queue.empty()
            self.istext2stream=False
            logging.info("Gcode Stream Stopped!")
        self.stoping_event.clear()

    def read(self):
        return self.data

    def Stream(self,text2stream,Pbar):
        self.Pbarupdate=Pbar
        self.Pbarupdate.SetStatus(0)
        self.istext2stream=True        
        line=''
        linecount=1
        for lll in text2stream:            
            if lll=='\n':
                if self.killer_event.is_set():
                    break
                if self.stoping_event.is_set():
                    logging.info("Queueing Stopped! ("+str(linecount)+') '+ line )
                    self.Stop_Clear()
                    return                                       
                logging.info("Queueing Line-> ("+str(linecount)+") "+ line)                                            
                self.text_queue.put(line)                    
                self.data = self.xyz_thread.read()                
                self.get_state()                              
                if self.state_xyz==11: # error
                    logging.info("Error in Gcode! ("+str(linecount)+') '+ line )
                    self.Stop_Clear()
                    break                       
                linecount=linecount+1
                line=''
            else:
                line=line+lll   
        logging.info("Queueing Line-> ("+str(linecount)+") "+ line)                                            
        self.text_queue.put(line)                     
        self.istext2stream=False    
        logging.info("End of Queue to Stream!")  
        #Initialize count
        self.line_count=0
        self.Do_line_count()  

    def Islinecontent_ok(self,line):
        contents=line.strip(' ')
        contents=contents.strip('\n')        
        if line=='' or contents=='':
            return False
        return True    

    def stream_one_line(self,line2stream):
        if self.istext2stream==True:                    
            self.xyz_thread.grbl_gcode_cmd(line2stream)
            #logging.info("Sent->"+line2stream)             



