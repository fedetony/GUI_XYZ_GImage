
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import *
import logging

class SignalTracker(QWidget):
    '''
    Only incharged of signaling information when changes are present.
    signals for Enableing/disabling objects in GUI
    Or values to track positions,states etc..
    Signals then can be connected to GUI events.
    '''
    data_change=QtCore.pyqtSignal(dict)    
    pos_change= QtCore.pyqtSignal(list)    
    state_change= QtCore.pyqtSignal(int)
    timer_change= QtCore.pyqtSignal(str)
    stream_info_change=QtCore.pyqtSignal(list)    
    enable_bHOLD= QtCore.pyqtSignal(bool)
    enable_bSTOP= QtCore.pyqtSignal(bool)
    enable_isSTREAMING= QtCore.pyqtSignal(bool)
    is_hold_state= QtCore.pyqtSignal(bool)
    log_update=QtCore.pyqtSignal(bool)
    log_to_main = QtCore.pyqtSignal(object)

    # Gimage signals
    gimage_progress = QtCore.pyqtSignal(int, dict)   # percent, stats
    gimage_status = QtCore.pyqtSignal(str)
    gimage_finished = QtCore.pyqtSignal(str)         # final gcode or path
    gimage_error = QtCore.pyqtSignal(str)

    # status
    eta_change = QtCore.pyqtSignal(object)

    # Monitor data
    tx_raw = QtCore.pyqtSignal(float, str)
    rx_raw = QtCore.pyqtSignal(float, str)

    def __init__(self, *args, **kwargs):        
        super(SignalTracker, self).__init__(*args, **kwargs)    
        self.__name__="ST"
    
    def Log_to_Main(self, record: logging.LogRecord): 
        self.log_to_main.emit(record)

    def Log_Update(self):
        self.log_update.emit(True)

    def Signal_Data(self,datadict):
        self.data_change.emit(datadict)

    def Signal_Position(self,poslist):
        self.pos_change.emit(poslist)                     

    def Signal_Stream_Info(self,streaminfolist):
        self.stream_info_change.emit(streaminfolist)

    def Signal_State(self,newstate):
        self.state_change.emit(newstate)

    def Signal_Timer(self,timestr):
        self.timer_change.emit(timestr)                         
    
    def S_Enable_bHOLD(self,isEnable):
        self.enable_bHOLD.emit(isEnable)    

    def S_Enable_bSTOP(self,isEnable):
        self.enable_bSTOP.emit(isEnable)      

    def S_Enable_isSTREAMING(self,isEnable):
        self.enable_isSTREAMING.emit(isEnable)                      
    
    def S_isONHOLDSTREAM(self,isonhold):
        self.is_hold_state.emit(isonhold)

    def S_eta_change(self,eta):
        self.eta_change.emit(eta) 

    def GImage_Progress(self,percent:int,stat:dict=None):
        if not isinstance(stat,dict):
            stat={}
        self.gimage_progress.emit(percent,stat)   
    
    def GImage_Status(self,status:str):
        self.gimage_status.emit(status)

    def GImage_Finished(self,result:str):
        self.gimage_finished.emit(result) 

    def GImage_Error(self,result:str):
        self.gimage_error.emit(result) 

    def Monitor_tx_raw(self,timestamp:float,raw:str):
        self.tx_raw.emit(timestamp,raw)    
    
    def Monitor_rx_raw(self,timestamp:float,raw:str):
        self.rx_raw.emit(timestamp,raw)    
    


    