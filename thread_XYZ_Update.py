
from PyQt5 import QtCore, QtGui, QtWidgets
import threading
import queue
import re
import logging
import time
from common import *

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s')
class XYZ_Update(threading.Thread):
    def __init__(self,xyz_thread,killer_event,label_XactPos,label_YactPos,label_ZactPos,button_hold_start_1,frame_hold_stop):
        threading.Thread.__init__(self, name="XYZ Update")
        logging.info("XYZ Update Started")
        self.xyz_thread=xyz_thread
        self.cycle_time=0.1
        self.label_XactPos=label_XactPos
        self.label_YactPos=label_YactPos
        self.label_ZactPos=label_ZactPos
        self.killer_event=killer_event
        self.button_hold_start_1=button_hold_start_1
        self.frame_hold_stop=frame_hold_stop
        self.state_xyz=0
        self.oldstate_xyz=0


    def run(self):                
        count=0
        while not self.killer_event.wait(self.cycle_time):   
            try:
                self.data = self.xyz_thread.read()
                self.Set_Actual_Position_Values(self.data['XPOS'],self.data['YPOS'],self.data['ZPOS']) 
                self.state_xyz=self.data['STATE_XYZ'] 
                self.Enable_Disable_Hold_Start()
                #time.sleep(self.cycle_time)
            except:
                if count==0:
                    logging.info("XYZ Update can't get data to update")                         
                else:
                   count=count+1
                if count>=2000:
                    count=0        
        logging.info("XYZ Update killed")          

    def read(self):
        return self.data

    def Enable_Disable_Hold_Start(self):
         #1=reset, 2=alarm, 3=idle, 4=end, 5=run, 6=hold, 7=probe, 8=cycling,  9=homing, 10 =jogging 11=error
        if self.state_xyz==1:
            self.button_hold_start_1.setEnabled(False) 
            self.frame_hold_stop.setEnabled(False) 
        elif self.state_xyz==2:
            self.button_hold_start_1.setEnabled(True)  
            self.frame_hold_stop.setEnabled(True)    
        elif self.state_xyz==3:
            self.button_hold_start_1.setEnabled(False)
            self.frame_hold_stop.setEnabled(False) 
        elif self.state_xyz==4:
            self.button_hold_start_1.setEnabled(False) 
            self.frame_hold_stop.setEnabled(False)  
        elif self.state_xyz==5:
            self.button_hold_start_1.setEnabled(True)
            self.frame_hold_stop.setEnabled(True)
        elif self.state_xyz==6:
            self.button_hold_start_1.setEnabled(True)
            self.frame_hold_stop.setEnabled(True)
        elif self.state_xyz==7:
            self.button_hold_start_1.setEnabled(True) 
            self.frame_hold_stop.setEnabled(True)
        elif self.state_xyz==8:
            self.button_hold_start_1.setEnabled(True) 
            self.frame_hold_stop.setEnabled(True)     
        elif self.state_xyz==9:
            self.button_hold_start_1.setEnabled(True)
            self.frame_hold_stop.setEnabled(True)  
        else:
            self.button_hold_start_1.setEnabled(False)
            self.frame_hold_stop.setEnabled(False)                      

    def Set_Actual_Position_Values(self,xxx,yyy,zzz):                            
        self.x_pos = xxx
        self.y_pos = yyy
        self.z_pos = zzz
        _translate = QtCore.QCoreApplication.translate
        self.label_XactPos.setText(_translate("MainWindow","X = "+str(xxx)))
        self.label_XactPos.adjustSize()
        self.label_YactPos.setText(_translate("MainWindow","Y = "+str(yyy)))
        self.label_YactPos.adjustSize()
        self.label_ZactPos.setText(_translate("MainWindow","Z = "+str(zzz)))
        self.label_ZactPos.adjustSize()    
