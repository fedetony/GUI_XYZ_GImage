'''
F.Garcia
05.11.2020
Streaming Handle thread.
Is alive meanwhile there is text to stream.
'''
import threading
import queue
import logging
import time
import re
import io
import sys
import os
from common import *


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
ahandler=logging.StreamHandler()
ahandler.setLevel(logging.INFO)
ahandler.setFormatter(formatter)
log.addHandler(ahandler)


 
class queueStream(threading.Thread):
    """
        A thread class to buffer and deliver the Gcode for streaming
    """                  
    def __init__(self, text2stream,cycle_time,kill_event,Refill_value=0,Buffer_size=5,Pbar_buffer=None,Pbar_Stream=None):
        threading.Thread.__init__(self, name="Stream Queue thread")        
        self.cycle_time=cycle_time
        self.killer_event = kill_event        
        self.text_queue = queue.Queue()
        self.output_queue = queue.Queue()   
        self.textqsize=self.text_queue.qsize()
        self.outqsize=self.output_queue.qsize()                    
        self.Pbar_buffer=Pbar_buffer
        self.Pbar_Stream=Pbar_Stream
        self.Pbarini=0
        self.Pbarend=100
        self.Pbar_Set_Status(self.Pbar_buffer,0)        
        self.Pbar_Set_Status(self.Pbar_Stream,0) 
        #event handled       
        self.Add1tobuffer_event=threading.Event()        
        self.Add1tobuffer_event.clear() 
        self.itemsinbuffer_event=threading.Event()
        self.itemsinbuffer_event.clear() 
        self.Is_textintoqueue_Finished=False
        self.Stream_Finished=False
        self.Streamsize=0
        self.filename=self.get_temppathFilename()
        self.Max_Buffer_size=1024        
        self.set_Buffer(Refill_value,Buffer_size)
        self.Filelength=0
        self.Set_Streamtext_to_text_queue(text2stream)
        
        
    def Are_items_in_buffer(self):
        return self.itemsinbuffer_event.is_set()

    def add_one_line_to_buffer_ev(self):
        self.Add1tobuffer_event.set()

    def set_Buffer(self,Refill_value=0,Buffer_size=5):
        '''
        Sets values for filling the buffer when reaching refill value. 
        Refill_value=0 -> when empty
        Refill_value>= Buff_size-> never
        '''
        if Buffer_size<=0:
            Buffer_size=5
        if Buffer_size>int(self.Max_Buffer_size/2):
            Buffer_size=int(self.Max_Buffer_size/2)
        self.Buff_size=Buffer_size
        self.Buff_fill=Refill_value
        
    def Fill_buffer(self,whencountis=0,untilcountis=5):        
        if whencountis<0:
            whencountis=0
        if self.outqsize<=whencountis and self.textqsize>0:            
            while self.textqsize>0 and self.outqsize<untilcountis:
                self.Add_to_output_queue()    
            self.itemsinbuffer_event.set()                
        self.Set_qsizes()    

    def Pbar_Set_Status(self,Pbar,val):
        if  Pbar!=None and int(val)>=0 and int(val)<=100:      
            Pbar.SetStatus(int(val))
    
    def quit(self):
        self.killer_event.set()        
        #self.join()

    def Get_Progress_Percentage(self,sss,Numsss,Perini=0,Perend=100):
        if sss>Numsss:            
            return Perend
        if sss<0 or Numsss<=0:            
            return Perini
        if (Perend-Perini)<=0:
            Per=min(abs(Perini),abs(Perend))              
            return Per 
        Per=round(Perini+(sss/Numsss)*(Perend-Perini),2)        
        return Per   
    
    def get_number_lines_in_file(self,aFile):
        numlines=0
        try:
            with open(aFile) as my_file:
                numlines= sum(1 for _ in my_file)
            my_file.close()
        except Exception as e:
            log.error(e)
            numlines=None
            pass
        return numlines
    
    def refresh_Pbars(self):
        sstatb=self.Get_Progress_Percentage(self.get_num_of_commands_buff(),self.Buff_size,Perini=0,Perend=100)
        self.Pbar_Set_Status(self.Pbar_buffer,sstatb)
        sstat=self.Get_Progress_Percentage(self.get_num_of_commands_left(),self.get_num_of_total_commands_onFile(),Perini=0,Perend=100)        
        self.Pbar_Set_Status(self.Pbar_Stream,sstat)

    def run(self):                
        
        #print('Entered Run------------------------------------')
        if self.Filelength is not None:
            if self.Filelength>0:
                try:
                    sfile=open(self.filename, 'r')
                    #print('Opened file------------------------------------')
                except:
                    sfile=None
                    self.killer_event.set()
                    log.error('Error with file opening '+self.filename)
                    pass
                # fill some text to the text queue before entering loop
                if self.Filelength<=2*self.Buff_size:
                    qqq=self.Filelength
                else:
                    qqq=2*self.Buff_size
                for iii in range(qqq):
                    self.Add_to_text_queue_from_file(sfile)                
                self.Set_qsizes()
            else:
                log.error('Filesize is '+str(self.Filelength))
                self.quit()
        else:
            log.error('File empty '+self.filename)            
            self.quit()
        count=0
        #print('is file:',sfile)
        while not self.killer_event.wait(self.cycle_time):   
            try:
                # Read from the file until end and close it and set Pbar                
                self.Add_to_text_queue_from_file(sfile)
                self.Set_qsizes()
                
                self.Fill_buffer(self.Buff_fill,self.Buff_size)    
                if self.Add1tobuffer_event.is_set()==True:                    
                    self.Add_to_output_queue() 
                    self.itemsinbuffer_event.set()                     
                    self.Add1tobuffer_event.clear()   
                if count==3:
                    self.refresh_Pbars()
                    count=0
                count=count+1
                #if self.Stream_Finished==True:
                #    self.killer_event.set()
                #    break           
            except Exception as e:
                self.killer_event.set()
                log.error(e)
                log.error("Stream Queue fatal error! exiting thread!")                                         
                raise  
        if self.killer_event.is_set():
            log.info("Stream Queue Killing event Detected!")                        
        log.info("Stream Queue Ended!")  
        try: 
            sfile.close()
        except:
            pass        
        self.Pbar_Set_Status(self.Pbar_buffer,0)        
        self.Pbar_Set_Status(self.Pbar_Stream,100)        
        #self.quit() 
    
    def Add_to_text_queue_from_file(self,sfile):        
        if self.Is_textintoqueue_Finished==False:
            if sfile is not None:
                if self.get_num_of_commands_txt()<=self.Max_Buffer_size:
                    try:
                        line=sfile.readline()                
                        if line=='':
                            line=None                    
                        line=line.rstrip()
                        if line!='':                    
                            self.text_queue.put(line)
                            self.Streamsize=self.Streamsize+1
                            self.Set_qsizes()
                            #print('In text queue->',line)
                    except Exception as e:
                        #log.error(e)
                        log.info('Finished queueing text! Lines in queue:'+str(self.Streamsize))
                        sfile.close()
                        sfile=None
                        #print('Finish text into queue -------------------------------------------------------')
                        self.Is_textintoqueue_Finished=True
                        pass
        sstat=self.Get_Progress_Percentage(self.get_num_of_commands_left(),self.get_num_of_total_commands_onFile(),Perini=0,Perend=100)        
        self.Pbar_Set_Status(self.Pbar_Stream,sstat)
        


    def Set_qsizes(self):
        self.textqsize=self.text_queue.qsize()
        self.outqsize=self.output_queue.qsize()
        if self.outqsize==0:
            self.itemsinbuffer_event.clear()
        # Finished when both queues are empty
        [buff,txt,consumed,left,tot,totfile]=self.get_all_nums(False)
        if left==0 and consumed==tot and consumed>0:
            self.Stream_Finished=True

    def get_all_nums(self,logprint=False):
        buff=self.get_num_of_commands_buff()
        txt=self.get_num_of_commands_txt()
        left=self.get_num_of_commands_left()
        consumed=self.get_num_of_commands_consumed()
        tot=self.get_num_of_total_commands()
        totfile=self.get_num_of_total_commands_onFile()
        if logprint==True:
            log.info('Stream Queue Thread Exit Report:')
            log.info('Lines in Buffer-----: '+str(buff))
            log.info('Lines to be Buffered: '+str(txt))
            log.info('Lines to be Consumed: '+str(left))
            log.info('Lines Consumed------: '+str(consumed))
            log.info('Lines in Memory-----: '+str(tot))
            log.info('Lines in Total------: '+str(totfile))
        return [buff,txt,consumed,left,tot,totfile]

    def get_num_of_commands_consumed(self):
        return self.Streamsize-(self.textqsize+self.outqsize)

    def get_num_of_commands_left(self):
        if self.Stream_Finished==False:
            return self.textqsize+self.outqsize
        else:
            return -1    

    def get_num_of_commands_txt(self):
        return self.textqsize

    def get_num_of_commands_buff(self):
        return self.outqsize

    def get_num_of_total_commands(self):
        return self.Streamsize     
    
    def get_num_of_total_commands_onFile(self):
        return self.Filelength

    def Add_to_output_queue(self):        
        try:        
            line=self.text_queue.get_nowait()
            self.output_queue.put(line)
        except queue.Empty:                    
            pass     
        self.Set_qsizes()
        sstat=self.Get_Progress_Percentage(self.get_num_of_commands_buff(),self.Buff_size,Perini=0,Perend=100)
        self.Pbar_Set_Status(self.Pbar_buffer,sstat)                        
    
    def Consume_buff(self,doblock=False):
        '''
        returns the text in Buffer. Returns None if buffer empty.
        '''
        txt=None
        #if self.Are_items_in_buffer==True:
        try:
            #txt=self.output_queue.get_nowait()
            txt=self.output_queue.get(block=doblock)
        except queue.Empty:                    
            pass 
        return txt

    def Set_Streamtext_to_text_queue(self,text2stream):
        if text2stream is None or text2stream=='':
            log.error('No text to stream!')
            self.quit()
        self.Pbar_Set_Status(self.Pbar_buffer,0)        
        self.Pbar_Set_Status(self.Pbar_Stream,0)            
        self.SavetempGcode(self.filename,text2stream)                
        self.Pbar_Set_Status(self.Pbar_Stream,10)
        self.Filelength=self.get_number_lines_in_file(self.filename) 
        #print('Found ->',self.Filelength)       
                       
    ## Save to file -> open read -> fill buffer
    def SavetempGcode(self,filename,text2stream):                
        if filename is not None:       
            mfile=re.search('(\.gcode$)',filename)
            try:
                if mfile.group(1)!='.gcode': 
                    filename=filename+'.gcode'
            except:
                filename=filename+'.gcode' 
                pass       
            log.info('Saving temporary file to stream:'+filename) 
            try:
                with open(filename, 'w') as yourFile:
                    yourFile.write(text2stream)                
                yourFile.close()                
            except Exception as e:
                log.error(e)
                log.info("Temporary File was not Written!")
                self.quit()
                pass
    
    def Get_linelist_from_file(self,filename):        
        linelist=[]
        if filename is not None:            
            log.info('Opening:'+filename)
            try:
                self.plaintextEdit_GcodeScript.clear()
                with open(filename, 'r') as yourFile:                    
                    linelist=yourFile.readlines() #makes list of lines                  
                yourFile.close()                
            except Exception as e:
                log.error(e)
                log.info("File was not read!")
        return linelist    

    def get_appPath(self):
        # determine if application is a script file or frozen exe
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(__file__)
        return application_path      

    def get_temppathFilename(self):
        temppath=self.get_appPath()+os.sep+'temp'+os.sep
        try:
            os.mkdir(temppath)
        except:
            pass
        return temppath+'__TempStream__.gcode'


def main():
    
    kill_ev = threading.Event()
    kill_ev.clear()
    text2stream=';Test1\n'
    for iii in range(25):
        text2stream=text2stream+'G0 X'+str(iii)+'\n'
        text2stream=text2stream+'G0 X'+str(-iii)+'\n'    
    cycle_time=0.1
    qstream=queueStream(text2stream,cycle_time,kill_ev,Refill_value=15,Buffer_size=20)
    qstream.start()
    print('inbuff:',qstream.get_num_of_commands_buff(),'Executed:',qstream.get_num_of_commands_consumed(),'Total:',qstream.get_num_of_total_commands())
    #while not kill_ev.is_set():    
    try:
        while qstream.is_alive()==True:                
            txt=qstream.Consume_buff(True)
            print('inbuff:',qstream.get_num_of_commands_buff(),'Executed:',qstream.get_num_of_commands_consumed(),'Total:',qstream.get_num_of_total_commands())
            if txt != None:
                print(txt)
            time.sleep(0.1)
            if qstream.get_num_of_commands_left()==20:
                qstream.get_all_nums(True)
                kill_ev.set()
                #qstream.join()
            print(qstream.is_alive())    
    except:
        pass

    

    

if __name__ == '__main__':
    main()
