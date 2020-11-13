
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *

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
    
    def __init__(self, *args, **kwargs):        
        super(SignalTracker, self).__init__(*args, **kwargs)    
        self.__name__="ST"

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
    