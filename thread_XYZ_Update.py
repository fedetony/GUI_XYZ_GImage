
from PyQt5 import QtCore, QtGui, QtWidgets
import threading
import queue
import re
import logging
import time
from common import *
import datetime

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
ahandler=logging.StreamHandler()
ahandler.setLevel(logging.INFO)
ahandler.setFormatter(formatter)
log.addHandler(ahandler)

class XYZ_Update(threading.Thread):

    def __init__(self,ST,xyz_thread,xyz_gcodestream_thread,killer_event):
        threading.Thread.__init__(self, name="XYZ Update")
        log.info("XYZ Update Started")
        self.killer_event=killer_event
        self.ST=ST
        self.xyz_thread=xyz_thread  
        self.xyz_gcodestream_thread=xyz_gcodestream_thread      
        self.cycle_time=self.xyz_thread.ser_read_thread.cycle_time
        self.CH=self.xyz_thread.ser_read_thread.CH        
        self.Actualizeposstate=True
        self.state_xyz=0
        self.oldstate_xyz=0
        self.TimerON=False
        self.IsStreaming=False
        self.timertxt=''
        self.Lasttimertxt=''
        self.Initialize_Tracking_events()
        self.data={}
        self.olddata={}
        self.Stream_info_list=[0,0,0,0,0,0]
        self.LastStream_info_list=[0,0,0,0,0,0]
        self.Stream_info_changed=False
        self.sim_params=self.get_sim_parameters()


    def Initialize_Tracking_events(self):
        self.Is_Streaming_Track=threading.Event()
        self.Is_Streaming_Track.clear()
        self.Is_Position_Changed_Track=threading.Event()
        self.Is_Position_Changed_Track.clear()
        self.Is_State_Changed_Track=threading.Event()
        self.Is_State_Changed_Track.clear()
        self.Is_On_Hold_Track=threading.Event()
        self.Is_On_Hold_Track.clear()
        self.Is_Robot_Responding_Track=threading.Event()
        self.Is_Robot_Responding_Track.clear()
        self.Is_Connected_Track=threading.Event()
        self.Is_Connected_Track.clear()
        
        self.Is_bSTOP_Enabled=threading.Event()
        self.Is_bSTOP_Enabled.set()
        self.Is_bHOLD_Enabled=threading.Event()
        self.Is_bHOLD_Enabled.clear()

    def Clear_Timer(self):
        self.Set_timer_start()
        timetxt=self.elapsed_time(self.Start_Time,False)        
        self.Lasttimertxt=self.timertxt
        self.timertxt=timetxt

    def Start_Timer(self):
        self.Clear_Timer()
        self.TimerON=True
        self.IsStreaming=True
        self.Is_Streaming_Track.set()

    
    def Stop_Timer(self):
        self.TimerON=False
        self.IsStreaming=False
        self.Is_Streaming_Track.clear()

    def Set_timer_start(self):
        now = datetime.datetime.now()
        self.Start_Time=now 
    
    def Show_elapsed_Time(self):
        if self.TimerON==True:
            timetxt=self.elapsed_time(self.Start_Time,False)
            self.Lasttimertxt=self.timertxt
            self.timertxt=timetxt

    def elapsed_time(self,tstart,dolog=False): 
        now = datetime.datetime.now()
        timepassed=now-tstart    
        txttime=str(datetime.timedelta(seconds=timepassed.seconds))    
        if dolog==True:
            log.info('Time elapsed: '+ txttime)    
        return txttime

    def run(self):                
        count=0
        timer_count=0
        while not self.killer_event.wait(self.cycle_time):   
            #self.ST.Log_Update()
            try:
                self.set_olddata()
                self.data = self.xyz_thread.read()
                self.Actualizeposstate=self.Compare_Hasdatachanged(self.olddata,['CTL'])
                self.Set_Actual_Position_Values(self.data['XPOS'],self.data['YPOS'],self.data['ZPOS']) 
                self.state_xyz=self.data['STATE_XYZ'] 
                self.Status=self.data['STATUS'] #self.xyz_thread.ser_read_thread.Set_Status_from_StateXYZ
                self.Set_Actual_State_Value(self.state_xyz,self.Status)
                self.Enable_Disable_with_state()                
                if self.TimerON==True:
                    timer_count=timer_count+self.cycle_time
                if timer_count>=1: #Update value once per second
                    self.Show_elapsed_Time()
                    timer_count=0        
                self.Get_Streaming_Info()
                self.Signal_ALL()            
            except Exception as e:
                if count==0:
                    log.error(e)
                    log.info("XYZ Update can't get data to update")                         
                else:
                    count=count+1
                if count>=20000:
                    count=0        
                       
        log.info("XYZ Update killed")          
    
    def Get_Streaming_Info(self):   
        if self.IsStreaming==True:     
            self.linesacknowledged_count=self.xyz_thread.Get_linesacknowledgedCount()
            self.linesfinalized_count=self.xyz_gcodestream_thread.linesfinalized_count
            lastlinesfinalized_count=self.xyz_gcodestream_thread.lastlinesfinalized_count
            self.num_events=self.linesfinalized_count-lastlinesfinalized_count+1
            try:
                qstream=self.xyz_gcodestream_thread.qstream
                self.buff=qstream.get_num_of_commands_buff()
                self.consumed=qstream.get_num_of_commands_consumed() #actual line
                self.onFile=qstream.get_num_of_total_commands_onFile()
                self.Stream_info_list=[self.buff,self.consumed,self.onFile,self.linesacknowledged_count,self.linesfinalized_count,self.num_events]

                self.Stream_info_changed=self.Compare_hasStream_info_Changed(self.LastStream_info_list)
            except Exception as e:
                log.error(e)                
                pass


    def Signal_ALL(self):
        #self.ST.Log_Update()
        self.ST.S_Enable_bHOLD(self.Is_bHOLD_Enabled.is_set())
        self.ST.S_Enable_bSTOP(self.Is_bSTOP_Enabled.is_set())
        if self.Lasttimertxt!=self.timertxt:
            self.ST.Signal_Timer(self.timertxt)
        self.ST.S_Enable_isSTREAMING(self.Is_Streaming_Track.is_set())                
        #if self.Actualizeposstate==True:
        self.ST.Signal_Data(self.data)
        self.ST.S_isONHOLDSTREAM(self.Is_On_Hold_Track.is_set())
        if self.IsStreaming==True:
            if self.Stream_info_changed==True:
                self.ST.Signal_Stream_Info(self.Stream_info_list)
        


    def Compare_Hasdatachanged(self,olddata,exceptlist=[]):
        is_different=False
        self.Is_Position_Changed_Track.clear()
        for aaa in self.data:
            #log.info(str(olddata[aaa])+' vs ' + str(self.data[aaa]))
            if aaa not in exceptlist:
                if aaa in olddata:
                    if olddata[aaa]!=self.data[aaa]:
                        is_different= True
                        if 'POS' in aaa:
                            self.Is_Position_Changed_Track.set()                        
                        break        
        return is_different

    def read(self):
        return self.data

    def Enable_Disable_with_state(self):
         #1=reset, 2=alarm, 3=idle, 4=end, 5=run, 6=hold, 7=probe, 8=cycling,  9=homing, 10 =jogging 11=error
        if self.state_xyz in [1,2,3,4,11]:
            self.Is_bSTOP_Enabled.clear()
        elif self.state_xyz in [5,6,7,8,9,10]:            
            self.Is_bSTOP_Enabled.set()
        else:
           self.Is_bSTOP_Enabled.set()

        if self.state_xyz in [1,2,3,4,11]:
            self.Is_bHOLD_Enabled.clear()
        elif self.state_xyz in [5,6,7,8,9,10]:            
            self.Is_bHOLD_Enabled.set()
        else:
           self.Is_bHOLD_Enabled.clear()  
        
        if self.IsStreaming==True:      
            # Allow hold and Stop always available on streaming            
            self.Is_bSTOP_Enabled.set()      
            # signal only when state changes to hold
            if self.state_xyz==6 and self.oldstate_xyz!=6:        
                self.Is_On_Hold_Track.set()   
                log.info('------------------------Stream Hold Detected-----------------------------')
                cmd=self.xyz_thread.CH.getGformatforAction('userResume')
                log.info('Waiting for userResume Command: '+str(cmd))
            else:
                self.Is_On_Hold_Track.clear() 
        else:
            self.Is_On_Hold_Track.clear() 
        
    
    def Set_Actual_Position_Values(self,xxx,yyy,zzz):                            
        self.x_pos = xxx
        self.y_pos = yyy
        self.z_pos = zzz
    
    def set_olddata(self):
        self.oldstate_xyz=self.state_xyz
        for aaa in self.data:
            self.olddata.update({aaa:self.data[aaa]})
        self.LastStream_info_list=[]
        for bbb in self.Stream_info_list:
            self.LastStream_info_list.append(bbb)
    
    def Compare_hasStream_info_Changed(self,laststreaminfo):
        Stream_info_changed=False
        for jjj in range(len(self.Stream_info_list)):
            if self.Stream_info_list[jjj]!=laststreaminfo[jjj]:
                Stream_info_changed=True
                break
        return Stream_info_changed
    

        
    def Set_Actual_State_Value(self,StateXYZ,Status=''):  
        self.Is_State_Changed_Track.clear()                                          
        self.state_xyz=StateXYZ
        if self.state_xyz!=self.oldstate_xyz:
            self.Is_State_Changed_Track.set()                                  
        self.status=Status

    def get_sim_parameters(self):
        sim_params={}
        #to read from config later
        steppernames={'X','Y','Z','E'}
        posmin={'X':0,'Y':0,'Z':-5,'E':None}
        posmax={'X':234.00,'Y':235.00,'Z':245.00,'E':None}
        stepsperunit={'X':80.00,'Y':80.00,'Z':400.00,'E':93.00}
        feedratemax={'X':500,'Y':500,'Z':5,'E':25} #(units/s)
        accelerationmax={'X':500,'Y':500,'Z':100,'E':5000} #(units/s2)
        feedratedependancy={'X':1,'Y':1,'Z':1,'E':None} #if 1 will use the minfeedrate in case of a dependant axis movement
        sim_params.update({'steppernames':steppernames})
        sim_params.update({'posmin':posmin})
        sim_params.update({'posmax':posmax})
        sim_params.update({'stepsperunit':stepsperunit})
        sim_params.update({'feedratemax':feedratemax})
        sim_params.update({'feedratedependancy':feedratedependancy})
        sim_params.update({'accelerationmax':accelerationmax})        
        return sim_params
    
    def get_min_max_in_dict(self,adict,ismin=True):
        result=None
        for item in adict:
            val=adict[item]
            if ismin==True:                
                if val<=result or result is None:
                    result=val
            else:
                if val>=result or result is None:
                    result=val
        return result

    def get_sim_time(self,posini,posend,vini,vend):        
        evlist=[]
        allFR=self.sim_params['feedratemax']
        allAcc=self.sim_params['accelerationmax']
        FR={}
        Acc={}
        #only use the ones that have a different end position
        dep=self.sim_params('feedratedependancy')
        for xyze in self.sim_params('steppernames'):            
            try:
                if posini[xyze]!=posend[xyze] or vini[xyze]!=vend[xyze] and dep[xyze]==1:
                    evlist.append(xyze)
                    FR.update({xyze:allFR[xyze]})
                    Acc.update({xyze:allAcc[xyze]})
            except:
                pass
        #Find minimum Feedrate and acceleration on changing variables (will be used in moving)
        minFR=self.get_min_max_in_dict(FR,True)
        minAcc=self.get_min_max_in_dict(Acc,True)
        for xyze in posini:
            if dep[xyze]==1:
                FR.update({xyze:minFR})
                Acc.update({xyze:minAcc})
            else:
                FR.update({xyze:minFR})
                Acc.update({xyze:allAcc[xyze]})
        vel={}
        times={}
        for xyze in posini:
            ttt=self.get_cyn_time_block(posini[xyze],posend[xyze],vini[xyze],vend[xyze],Acc[xyze],FR[xyze])            
            times.update({vxyze:ttt})
        return times
    
    def get_cyn_time_to_accelerate(self,Vi,Vf,Acc,Vmax):        
        if Vf>Vmax:
            Vf=Vmax        
        vvv=abs(Vf-Vi)
        if Acc==0 or Acc is None:
            return 0,Vf
        ttt= abs(vvv/Acc)
        return ttt,Vf
    
    def get_cyn_distance_to_accelerate(self,Vi,Vf,Acc,Vmax):        
        ttt,Vf=self.get_cyn_time_to_accelerate(Vi,Vf,Acc,Vmax)
        dX=Vi*ttt+0.5*Acc*ttt**2
        return abs(dX),ttt,Vf
    
    def get_cyn_time_block(self,Xi,Xf,Vi,Vf,Acc,Vmax):  
        dX=abs(Xf-Xi)
        if Vf>Vmax:
            Vf=Vmax                
        if Vi<Vf and Vf>0:            
            rqdX,rqttt,rqVf=self.get_cyn_distance_to_accelerate(Vi,Vf,Acc,Vmax)
            if dX>rqdX:
                ttt=rqttt+(dX-rqdX)/Vf
            else:
                ttt=self.get_cyn_time_position(self,0,dX,Vi,Acc)
        elif Vi>Vf and Vf>=0:
            rqdX,rqttt,rqVf=self.get_cyn_distance_to_accelerate(Vf,Vi,Acc,Vmax)
            if dX>rqdX:
                ttt=rqttt+(dX-rqdX)/Vf
            else:
                ttt=self.get_cyn_time_position(self,0,dX,Vi,Acc)
        elif Vi==Vf and Vf==0:
            rqdX,rqttt,rqVf=self.get_cyn_distance_to_accelerate(0,Vmax,Acc,Vmax)
            if dX>2*rqdX:
                ttt=2*rqttt+(dX-2*rqdX)/rqVf            
            else:
                ttt=2*self.get_cyn_time_position(self,0,dX/2,Vi,Acc)
        elif Vi==Vf and Vf!=0:            
            ttt=(dX)/Vf                        
        else:            
            ttt=0
        return ttt        

    def get_cyn_time_position(self,Xi,Xf,Vi,Acc):             
        dX=Xf-Xi
        aaa=1
        if Acc!=0:            
            bbb=Vi*2/Acc 
            ccc=-2*dX/Acc     
            insqr=bbb**2-4*aaa*ccc
        else:            
            insqr=-1        
        if insqr>=0:
            sol1=(-bbb+insqr**0.5)/(2*aaa)
            sol2=(-bbb-insqr**0.5)/(2*aaa)
            if sol1>=0 and sol2<0:
                ttt=sol1
            elif sol2>=0 and sol1<0: 
                ttt=sol2
            else:
                ttt=min(sol1,sol2)

        else:
            return 0
        
        return ttt
    
    #def get_sim_Position_at_dt(self,posini,posend,dt):



        

        
 