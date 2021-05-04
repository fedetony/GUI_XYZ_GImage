# -*- coding: utf-8 -*-
"""
Created on 12.10.2020
Python 3.7 pyQt5
@author: F.Garcia
"""
# Created by: PyQt5 UI code generator 5.13.0

from PyQt5 import QtCore, QtGui, QtWidgets


from PyQt5.QtWidgets import *
from PIL.ImageQt import ImageQt
import re
import io #TextIOWrapper
import logging
import os
import threading
import time
import ast #read dictionaries


import GuiXYZ_TTD 
import class_File_Dialogs
import class_CCD
import thread_queueStream

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
ahandler=logging.StreamHandler()
ahandler.setLevel(logging.INFO)
ahandler.setFormatter(formatter)
log.addHandler(ahandler)

class IdentifyID(threading.Thread):
    """
        A thread class to do the translation process
    """
    def __init__(self, CH, qstream, kill_event,File_Type_from,loglines=True):
        threading.Thread.__init__(self, name="Identify thread")        
        self.killer_event = kill_event
        self.CH=CH
        self.qstream=qstream
        self.File_Type_from=File_Type_from
        ids=self.CH.Configdata['interfaceId']
        if len(ids)>0:
            self.Ident_ID=ids[0]
        else:
            self.quit()
        self.loglines=loglines  
        self.cycle_time=0.001      
        
    def quit(self):
        self.qstream.quit()
        self.killer_event.set()   
        #log.info('Quit Identification!')          

    def run(self):  
        self.Do_Identification()  
        log.info('Identification finished, closing Thread!')     
        self.quit()

    def Do_Identification(self):                        
        ids=self.CH.Configdata['interfaceId']
        validId=[]
        errcountlist=[]
        self.errdict={}
        for anId in ids:
            self.errdict.update({anId:None})
        isok=True                
        errcount=0
        total=self.qstream.get_num_of_total_commands_onFile()
        linenum=0   
        anId=self.Ident_ID                                         
        while not self.killer_event.is_set() and linenum<total and self.qstream.is_alive()==True : 
            self.errdict[anId]=errcount   
            try:
                if total<self.qstream.get_num_of_total_commands_onFile():
                    total=self.qstream.get_num_of_total_commands_onFile()                
                line2check=self.qstream.Consume_buff(True)  
                             
                linenum=linenum+1
                isok,foundId=self.Recognize_Line(line2check,anId)    
                if self.loglines==True:
                    log.info(str(linenum)+' Found:'+str(isok)+' ID:'+str(foundId))                     
                    #print(self.errdict)
                if isok==False:                            
                    errcount=errcount+1                    
                    if errcount>3:
                        log.warning(str(errcount)+' lines unrecognized Encountered in File!')
                        break
                else:
                    errcount=self.errdict[anId]
                if foundId!=anId:
                    if self.errdict[anId]==0:
                        self.errdict[anId]=-1
                    errcount=0
                    if self.errdict[foundId] is None:                                                        
                        self.Ident_ID=foundId
                        self.errdict[foundId]=0                    
                    anId=self.Ident_ID
            except:
                self.qstream.quit()    
                pass
        #print('Exit while',anId)         
        
    def get_Identified_ID(self):
        return self.Ident_ID   
    
    def get_err_ID(self):
        return self.errdict     
                            
    def Recognize_ID_from_LineID(self,line2rec,actionparamsfound,startid):
        ids=self.CH.Configdata['interfaceId']
        try:
            apf=actionparamsfound['_action_code_']
        except:
            apf=line2rec
            pass
        if (line2rec==apf and line2rec!='' and line2rec is not None):
            # reorganize ids
            the_ids=[startid]
            for anId in ids:
                if anId!=startid:
                    the_ids.append(anId)                
            #print('Recognize_ID_from_LineID->',line2rec,actionparamsfound)
            for anId in the_ids:
                apfound=self.CH.get_action_from_gcode(line2rec,anId)  
                print(anId,line2rec,' Here Found->',apfound)
                if line2rec!=apfound['_action_code_']: 
                     return anId
            log.warning('Non Recognized-> '+line2rec)
            return None
        return startid

        
        
    def Recognize_Line(self,line2rec,anId):
        #isok=False       
        if self.File_Type_from=='.acode':
            actionparamsfound=ast.literal_eval(line2rec)            
        elif self.File_Type_from=='.gcode' or self.File_Type_from=='.ngc':
            actionparamsfound=self.CH.get_action_from_gcode(line2rec,anId)     
        foundId=self.Recognize_ID_from_LineID(line2rec,actionparamsfound,anId)       
        #aGcode,isok=self.CH.Get_Gcode_for_Actionparamsfound(actionparamsfound,anId,Parammustok=True)            
        if foundId==None:
            return False,anId    
        elif foundId==anId:
            return True,anId 
        return True,foundId        


class DoTranslation(threading.Thread):
    """
        A thread class to do the translation process
    """
    def __init__(self, CH, qstream, kill_event,File_info,loglines=True):
        threading.Thread.__init__(self, name="Translate thread")        
        self.killer_event = kill_event
        self.CH=CH
        self.qstream=qstream
        self.File_ID_to=File_info['File_ID_to']
        self.File_ID_from=File_info['File_ID_from']
        self.filename_to=File_info['filename_to']
        self.File_Type_from=File_info['File_Type_from']
        self.File_Type_to=File_info['File_Type_to']
        self.loglines=loglines
        #self.cycle_time=cycle_time
        
    def quit(self):
        self.killer_event.set()  
        #log.info('Quit Translation!')                

    def run(self):                        
        #while not self.killer_event.wait(self.cycle_time):
        self.Do_Translation()  
        log.info('Translation finished, closing Thread!')     
        self.quit()

    def Do_Translation(self):        
        log.info('Translating From:'+str(self.File_ID_from)+' To: '+str(self.File_ID_to))
        if self.filename_to is not None and self.qstream.is_alive()==True:            
            try:                
                with open(self.filename_to, 'w') as yourFile:            
                    log.info('Starting Translation!')         
                    linein=0
                    total=self.qstream.get_num_of_total_commands_onFile()  
                    while self.qstream.is_alive()==True and not self.killer_event.is_set() and linein<total:
                        if total<self.qstream.get_num_of_total_commands_onFile():
                            total=self.qstream.get_num_of_total_commands_onFile()  
                        line2translate=self.qstream.Consume_buff(True)                        
                        linein=linein+1
                        Translatedline,isok=self.Translate_Line(line2translate)
                        if self.loglines==True:
                            log.info(line2translate+'-->'+Translatedline.rstrip())
                        if Translatedline.rstrip()=='' and isok==True:
                            log.warning('Empty Gcode found on line '+str(linenum)+' for ID:'+str(self.File_ID_to))
                        if isok==False:
                            linenum=self.qstream.get_num_of_commands_consumed()
                            log.warning('Gcode Error in code Translation on line '+str(linenum))
                        yourFile.writelines(Translatedline)      
                yourFile.close()                
            except Exception as e:
                log.error(e)
                self.qstream.quit()                
                log.error("Not possible to read file fro Translation!")
        
    def Translate_Line(self,line2translate):
        isok=True
        Transgcode=''
        if self.File_Type_from=='.acode':
            actionparamsfound=ast.literal_eval(line2translate)
        elif self.File_Type_from=='.gcode' or self.File_Type_from=='.ngc':
            actionparamsfound=self.CH.get_action_from_gcode(line2translate,self.File_ID_from)
            if line2translate==actionparamsfound['_action_code_']:
                someid=self.Recognize_ID_from_Line(line2translate,actionparamsfound)
                if someid is not None:     
                    log.info('Other ID found:'+str(someid))           
                    actionparamsfound=self.CH.get_action_from_gcode(line2translate,someid)    
                    #print(actionparamsfound)        

        if self.File_Type_to=='.gcode' or self.File_Type_to=='.ngc':            
            #gather all parameters of the action
            #print(actionparamsfound)
            Transgcode,isok=self.CH.Get_Gcode_for_Actionparamsfound(actionparamsfound,self.File_ID_to,Parammustok=True)                        
            if isok==False:
                print('False result',actionparamsfound,'ID to',self.File_ID_to)
            
        elif self.File_Type_to=='.acode':
            Transgcode=str(actionparamsfound)
        Transgcode=Transgcode+'\n'
        return Transgcode,isok

    def Recognize_ID_from_Line(self,line2rec,actionparamsfound):
        ids=self.CH.Configdata['interfaceId']
        validId=[]
        errcountlist=[]
        #print('Entered Recognize_ID_from_Line')
        if line2rec==actionparamsfound['_action_code_'] and line2rec!='' and line2rec is not None:
            for anId in ids:
                apfound=self.CH.get_action_from_gcode(line2rec,anId)  
                if line2rec!=apfound['_action_code_']: 
                     return anId
            #print('Entered Recognize_ID_from_Line did not find ID')
        return None
     
class ProgressBar_Update_(QtCore.QThread):
    tick = QtCore.pyqtSignal(int, name="valchanged") #New style signal

    def __init__(self, parent):
        QtCore.QThread.__init__(self,parent)

    def SetStatus(self,x):
        self.tick.emit(x)                             
        #time.sleep(0.05)

    def info(self, message):
        self.logger.info("{}".format(message))

class TranslateToolDialog(QWidget,GuiXYZ_TTD.Ui_Dialog_TTD):    
    save_gcode_to_file=QtCore.pyqtSignal(str)
    #def __init__(self,NumLayers,Selected_Layers,parent=None):    
    #    super().__init__(parent)
    def __init__(self,Actual_Interface,filename_from,filename_to, *args, **kwargs):
        super(TranslateToolDialog, self).__init__(*args, **kwargs)    
        self.__name__="TTD"
        self.Is_Translating=False
        self.Is_Recognizing=False
        self.WasRecognized=False
        self.Actual_Interface=Actual_Interface    
        self.openTranslateToolDialog()             
        self.filename_from=filename_from               
        self.filename_to=filename_to                       
        self.aDialog=class_File_Dialogs.Dialogs()   
        self.CCDialog=class_CCD.CommandConfigurationDialog(self.Actual_Interface) 
        self.CH=self.CCDialog.CH   
        self.TTD_Connect_Actions() 
        self.set_defaults()
        self.set_from_info()
        self.set_to_info()                             
        self.Fill_combos()
        self.sqkill_ev = threading.Event()
        self.sqkill_ev.clear()  
        self.RecognizeIDkill_ev=threading.Event()
        self.RecognizeIDkill_ev.clear() 
        self.isqstream=False
        self.cyctime=0.005     
        

    
    def TTD_Connect_Actions(self):        
        self.DTTui.pushButton_TTD_Load_Code.clicked.connect(self.PB_Load_File)
        self.DTTui.pushButton_TTD_Save_Code.clicked.connect(self.PB_Save_File)
        self.DTTui.checkBox_TTD_FromGcodetxt.clicked.connect(self.set_from_info)
        self.DTTui.comboBox_TTD_ID_Code.activated.connect(self.ComboBox_Select_IDto)
        self.DTTui.comboBox_TTD_Type_Code.activated.connect(self.ComboBox_Select_File_Type)
        self.DTTui.pushButton_TTD_Translate.clicked.connect(self.Do_Translation)        
        
    def Status_Update(self,val):
        self.DTTui.progressBar_TTD_State.setValue(val)  
        if val==100:
            self.Is_Translating=False  
            self.Is_Recognizing=False     
            self.Enable_buttons()   
        #print('Emmitted->',val)

    def Buffer_Update(self,val):
        self.DTTui.progressBar_TTD_Buffer.setValue(val)    
        #print('Emmitted->',val)

    def quit(self):
        log.info('TTD Quit detected!!')
        self.Dialog_TTD.close()
        self.reject()       
        print('closed TTD')
        
           
    def openTranslateToolDialog(self):
        self.Dialog_TTD = QtWidgets.QDialog()
        self.DTTui = GuiXYZ_TTD.Ui_Dialog_TTD()
        self.DTTui.setupUi(self.Dialog_TTD)        
        self.Dialog_TTD.show()             

    def accept(self):
        #print('accepted')       
        self.RecognizeIDkill_ev.set()    
        try:
            self.Rec_thread.quit()
        except:
            pass
        if self.Trans_thread.is_alive()==False:
            self.sqkill_ev.set()     
        time.sleep(0.2)   
        #self.CCDialog.accept()
        return self.filename_to

    def reject(self):  
        self.RecognizeIDkill_ev.set()
        self.sqkill_ev.set()   
        try:
            self.Rec_thread.quit()
        except:
            pass
        try:
            self.Trans_thread.quit()
        except:
            pass
        try:
            self.qstream.quit()
        except:
            pass
        time.sleep(0.2)   
        self.CCDialog.quit()        
    
    def PB_Load_File(self):
        filename=self.aDialog.openFileNameDialog(4) #gcode and action
        if filename is not None:
            self.filename_from=filename    
            self.WasRecognized=False                       
        self.set_file_type()   
        self.set_file_IDs()          
        return filename
    
    def set_file_type(self):
        self.File_Type_from=self.get_file_ext(self.filename_from)      
        self.File_Type_to=self.get_file_ext(self.filename_to)      

    def set_file_IDs(self):
        #self.File_ID_from=#identify the Id of file or use actual id
        '''
        if self.Is_LoadfromGcode()==True:
            self.File_ID_from=self.CH.id
            #if self.WasRecognized==False:

        else:
        '''
        if self.WasRecognized==False:
            self.Recognize_ID_of_File(self.filename_from)                        
        self.File_ID_to=self.DTTui.comboBox_TTD_ID_Code.currentText()      
        
    def Recognize_ID_of_File(self,aFile,minlines=100):   
        self.File_ID_from=self.CH.id
        idini=self.File_ID_from
        self.Is_Recognizing=True
        self.Enable_buttons()
        if aFile is not None:          
            self.Open_queue(aFile)               
            #self.RecognizeIDkill_ev=threading.event()
            self.RecognizeIDkill_ev.clear()        
            if self.qstream.get_num_of_total_commands_onFile()>0 and self.qstream.is_alive()==True:
                self.Rec_thread=IdentifyID( self.CH, self.qstream, self.RecognizeIDkill_ev,self.File_Type_from,True)
                self.Rec_thread.start()  
                linenum=0                            
                total=min(minlines,self.qstream.get_num_of_total_commands_onFile())
                
                while not self.sqkill_ev.is_set() and linenum<total and self.qstream.is_alive()==True:                    
                    time.sleep(0.1)
                    linenum=self.qstream.get_num_of_commands_consumed() 
                    self.File_ID_from=self.Rec_thread.get_Identified_ID()
                    total=min(minlines,self.qstream.get_num_of_total_commands_onFile())                    
                    if idini!=self.File_ID_from:
                        self.Fill_Labels()
                        idini=self.File_ID_from
                    self.WasRecognized=True
                self.Rec_thread.quit()
        self.Is_Recognizing=False
        self.Enable_buttons()
        self.Fill_Labels()
        
    def get_file_ext(self,f_n):
        ext=''
        if f_n is not None:
            Filenx=self.CCDialog.extract_filename(f_n,withextension=False)
            Filewx=self.CCDialog.extract_filename(f_n,withextension=True)
            ext=Filewx.replace(Filenx,'')
        return ext

    def Fill_Type_FileType_combobox(self):
        self.DTTui.comboBox_TTD_Type_Code.clear()
        self.DTTui.comboBox_TTD_Type_Code.addItem(".gcode")
        self.DTTui.comboBox_TTD_Type_Code.addItem(".acode")        
        self.DTTui.comboBox_TTD_Type_Code.addItem(".ngc")        
        self.File_Type_to=".gcode"
        index= self.DTTui.comboBox_TTD_Type_Code.findText(self.File_Type_to,QtCore.Qt.MatchFixedString)
        self.DTTui.comboBox_TTD_Type_Code.setCurrentIndex(index)

    def Enable_buttons(self):                        
        if self.Is_Recognizing==True or self.Is_Translating==True:
            self.DTTui.comboBox_TTD_ID_Code.setEnabled(False)
            self.DTTui.comboBox_TTD_Type_Code.setEnabled(False)
            self.DTTui.pushButton_TTD_Translate.setEnabled(False)
            self.DTTui.pushButton_TTD_Save_Code.setEnabled(False)
            self.DTTui.pushButton_TTD_Load_Code.setEnabled(False)
            self.DTTui.checkBox_TTD_FromGcodetxt.setEnabled(False)
        else:
            self.DTTui.comboBox_TTD_ID_Code.setEnabled(True)
            self.DTTui.comboBox_TTD_Type_Code.setEnabled(True)
            self.DTTui.checkBox_TTD_FromGcodetxt.setEnabled(True)
            self.DTTui.pushButton_TTD_Translate.setEnabled(True)
            self.DTTui.pushButton_TTD_Save_Code.setEnabled(True)
            self.DTTui.pushButton_TTD_Load_Code.setEnabled(not self.Is_LoadfromGcode())
        self.Fill_Labels()
        
    def Fill_Labels(self):
        if self.File_Type_from is not None:
            self.DTTui.label_TTD_File_from_Type.setText(self.File_Type_from)
            aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.File_ID_from)
            self.DTTui.label_TTD_File_from_ID.setText('ID'+str(self.File_ID_from)+' '+aname)


    def ComboBox_Select_File_Type(self):
        Sel_type=self.DTTui.comboBox_TTD_Type_Code.currentText()        
        if Sel_type!=self.Defext:
            self.Defext=Sel_type
            if self.filename_to is not None:
                File=self.CCDialog.extract_filename(self.filename_to,withextension=False)
                Path=self.CCDialog.extract_path(self.filename_to)            
                self.filename_to=Path+File+Sel_type
        self.set_to_info()

    def Fill_interface_combobox(self):        
        self.DTTui.comboBox_TTD_ID_Code.clear()
        for iii in self.CH.Configdata['interfaceId']:           
            self.DTTui.comboBox_TTD_ID_Code.addItem(iii)                          
        index= self.DTTui.comboBox_TTD_ID_Code.findText(self.CH.id,QtCore.Qt.MatchFixedString)
        self.DTTui.comboBox_TTD_ID_Code.setCurrentIndex(index)    
        aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.CH.id)
        self.DTTui.label_TTD_ID_to_Name.setText(aname)
        self.Selected_ID_to=self.CH.id
        
    
    def ComboBox_Select_IDto(self):
        anid=self.DTTui.comboBox_TTD_ID_Code.currentText()
        if str(anid)!=str(self.CH.id):            
            self.CH.Set_id(str(anid))
            aname=self.CH.Get_action_format_from_id(self.CH.Configdata,'interfaceName',self.CH.id)
            self.DTTui.label_TTD_ID_to_Name.setText(aname)             
            self.Selected_ID_to=self.CH.id             

    def Fill_combos(self):
        self.Fill_interface_combobox()
        self.Fill_Type_FileType_combobox()

    def set_defaults(self):
        temppath=self.CCDialog.get_appPath()+os.sep+'temp'+os.sep
        try:
            os.mkdir(temppath)
        except:
            pass  
        self.Defext='.gcode'
        self.exchangefile=temppath+'__Translate__TTD__'+self.Defext
        self.temppath=temppath
        self.fileout_Default=temppath+'Translated'+self.Defext
        self.File_Type_from=self.Defext
        self.File_Type_to=self.Defext
        self.File_ID_from=self.CH.id
        self.File_ID_to=self.CH.id    
        

    def set_from_info(self):
        if self.filename_from is None:
            self.UseGcodeText=True   
            self.File_Type_from=self.Defext
        else:
            self.UseGcodeText=self.Is_LoadfromGcode()
        self.Enable_buttons()    
        if self.UseGcodeText==True:
            self.DTTui.label_TTD_File_Loaded.setText('Gcode text')
            self.DTTui.label_TTD_File_Loaded.adjustSize()
            self.Ask_Main_Save_File(self.exchangefile)
            self.filename_from=self.exchangefile
        else:  
            if self.filename_from is not None: 
                aFile=self.CCDialog.extract_filename(self.filename_from,withextension=True)         
                self.DTTui.label_TTD_File_Loaded.setText(aFile)     
                self.DTTui.label_TTD_File_Loaded.adjustSize()
                

    def Is_LoadfromGcode(self):
        return self.DTTui.checkBox_TTD_FromGcodetxt.isChecked()

    def set_to_info(self):        
        if self.filename_to is None:
            self.filename_to=self.fileout_Default              
        aFile=self.CCDialog.extract_filename(self.filename_to,withextension=True)         
        self.DTTui.label_TTD_Saved.setText(aFile)     
        self.DTTui.label_TTD_Saved.adjustSize()
        self.set_file_type()
        
                
    def Ask_Main_Save_File(self,filename):            
        self.save_gcode_to_file.emit(filename)
    
    def PB_Save_File(self):        
        filename=self.aDialog.saveFileDialog(4) #gcode and action
        if filename is not None:
            self.filename_to=filename 
        self.set_file_type()                 
        return filename
    
    def Open_queue(self,filefrom):
        self.sqkill_ev.clear()
        self.DTTui.P_Bar_Update_state=ProgressBar_Update_(self)
        self.DTTui.P_Bar_Update_state.tick.connect(self.Status_Update)
        self.DTTui.P_Bar_Update_buffer=ProgressBar_Update_(self)
        self.DTTui.P_Bar_Update_buffer.tick.connect(self.Buffer_Update)        
        text2stream=self.get_text_from_file(filefrom)        
        #self.qstream=thread_queueStream.queueStream(text2stream,self.cyctime,self.sqkill_ev,Refill_value=1,Buffer_size=20,Pbar_buffer=None,Pbar_Stream=None)
        self.qstream=thread_queueStream.queueStream(text2stream,self.cyctime,self.sqkill_ev,Refill_value=1,Buffer_size=20,Pbar_buffer=self.DTTui.P_Bar_Update_buffer,Pbar_Stream=self.DTTui.P_Bar_Update_state)
        self.qstream.start()        
        self.isqstream=True
    
    def get_text_from_file(self,filename):
        text2stream=''
        if filename is not None:            
            try:                
                with open(filename, 'r') as yourFile:                    
                    text2stream=yourFile.read()
                              
                yourFile.close()                
            except Exception as e:
                log.error(e)
                log.error("Not possible to read!")
        return text2stream
    
    def Do_Translation(self):
        self.set_file_IDs()
        while self.Is_Recognizing==True:
            time.sleep(0.1)        
            self.Enable_buttons() 

        self.set_from_info()
        time.sleep(2)
        self.sqkill_ev.clear()
        self.Open_queue(self.filename_from)
        File_info={}
        File_info['File_ID_to']=self.File_ID_to
        File_info['File_ID_from']=self.File_ID_from
        File_info['filename_to']=self.filename_to
        File_info['File_Type_from']=self.File_Type_from
        File_info['File_Type_to']=self.File_Type_to
        self.Is_Translating=True        
        self.Enable_buttons() 
        if self.qstream.get_num_of_total_commands_onFile()>0 and self.qstream.is_alive()==True:
            self.Trans_thread=DoTranslation( self.CH, self.qstream, self.sqkill_ev,File_info)
            self.Trans_thread.start()


    