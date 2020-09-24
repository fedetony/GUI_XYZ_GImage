from PIL import Image, ImageFilter  # imports the library
from PIL.ImageQt import ImageQt

import random
import numpy as np
import threading
import queue
import re
import logging
import time
from common import *
from dataclasses import dataclass, field
from typing import List

# install pySerial NOT serial!!!
import serial

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s')

@dataclass
class Struct_Process_Data:
    Isimagetoprint: bool = False
    Process: str = ''
    OImg_Size_px: List[int] = field(default_factory=list)             
    PImg_Proportional_Scale: bool = True
    PImg_Size_mm: List[float] = field(default_factory=list)                                     
    pix_per_mm_width: int = 1
    pix_per_mm_height: int = 1
    PImg_Size_px: List[int] = field(default_factory=list)    
    PImg_Resolution: float = 0.1
    PImg_Number_of_Colors: int = 256         
    C_Size_mm: List[float] = field(default_factory=list)      
    PImg_ini_pos_mm: List[float] = field(default_factory=list)      


@dataclass
class Struct_Stream_Data:
    Ispimagetoprint: bool = False
    Process: str = ''
    Tool: str = ''
    Technique: str = ''
    Resolution: float = 0.1
    Number_of_Colors: int = 8
    deltaZ: float =3 
    Zmove_pos: float =5
    Ztouch_pos: float =0
    Resolution: float =0.1
    Process_rate: float =2000
    Robot_XYZ: List[float] = field(default_factory=list)  
    Img_ini_pos: List[float] = field(default_factory=list)  
    Include_First_Layer: bool =False
    Frame_Image: int = 0
    Include_Last_Layer: bool =False
    Ini_Script: str = ''
    End_Script: str = ''

class GImage:
    def __init__(self):
        self.filename=''        
        self.prnt_height=0 # mm
        self.prnt_width=0  # mm
        self.im_width=0 # pixels
        self.im_height=0 # pixels
        self.point_resolution=0.1 # mm
        self.Isimagetoprint=False
        self.IsProcessedimagetoprint=False
        self.Set_Initial_Image_Config_Data()
        self.Set_Initial_Image_Tool_List()
        self.Set_Initial_Technique_List()
        self.Set_Initial_Image_Process()
        




    def open_image(self,imagefilename):
        self.imagefilename=imagefilename
        try:
            #logging.info('Trying to Open:'+self.filename)
            self.im = Image.open(imagefilename) # load an image from the hard drive
            self.im_width=self.im.width
            self.im_height=self.im.height   
            self.Isimagetoprint=True       
              
        except:
            self.Set_Image_end_size(0,0)
            self.im_width=0
            self.im_height=0
            self.Isimagetoprint=False
    
    def Get_image(self):
        if self.Isimagetoprint==True:
            return self.im    
        else:
            return 0
    def Get_Process_Data(self):
        Process_Data=Struct_Process_Data()
        Process_Data.Process=self.Selected_Image_Process
        if self.Isimagetoprint==True:            
            Process_Data.PImg_Number_of_Colors=self.Get_Variable_from_Image_Config_Data('Img_Num_Colors')
            Process_Data.Process=self.Selected_Image_Process
            Process_Data.OImg_Size_px=self.im.size
            Process_Data.PImg_Resolution=self.Get_Variable_from_Image_Config_Data('Img_Resolution')
            #Get new size
            Process_Data.PImg_Proportional_Scale=bool(self.Get_Variable_from_Image_Config_Data('Is_Proportional'))
            Process_Data.PImg_Size_mm=[self.Get_Variable_from_Image_Config_Data('Img_Width'),self.Get_Variable_from_Image_Config_Data('Img_Height')]
            
            Process_Data.PImg_ini_pos_mm=self.Get_Variable_from_Image_Config_Data('Img_ini_pos')
            Process_Data.C_Size_mm=[self.Get_Variable_from_Image_Config_Data('Canvas_Width'),self.Get_Variable_from_Image_Config_Data('Canvas_Height')]
            
            #print(str(Process_Data.PImg_Size_mm))
            if self.im.width > 0 and self.im.height > 0:
                Process_Data.pix_per_mm_width=int(Process_Data.PImg_Size_mm[0]/self.im.width)
                Process_Data.pix_per_mm_height=int(Process_Data.PImg_Size_mm[1]/self.im.height)                        
            Process_Data.PImg_Size_px=[Process_Data.pix_per_mm_width*Process_Data.PImg_Size_mm[0],Process_Data.pix_per_mm_width*Process_Data.PImg_Size_mm[1]]

        return Process_Data

    def Process_Image(self):
        if self.Isimagetoprint==True:
            Process_Data=self.Get_Process_Data()
            self.Create_Processed_Image(Process_Data)
            self.Crop_Image_to_Canvas_Size(Process_Data)
            self.appply_process_to_imp(Process_Data)
            logging.info('Image Process Applied')
            #print(str(self.IsProcessedimagetoprint))
            #Show image


    def show_image(self):
        if self.Isimagetoprint==True:
            self.im.show() # load an image from the hard drive    
        else:
            logging.info("NO IMAGE")      
    
    def Create_Processed_Image(self,P_Data):
        if self.Isimagetoprint==True:
            newsize=[]
            for aaa in P_Data.PImg_Size_mm:
                newsize.append(int(aaa/P_Data.PImg_Resolution))
            self.imp=self.im.resize(newsize)    #puts the image to the end size for value in each pixel            
            self.IsProcessedimagetoprint=True
    
    def appply_process_to_imp(self,P_Data):
        if self.IsProcessedimagetoprint==True:
            if P_Data.Process=='Black&White':
                self.imp = self.imp.convert('L')
            elif P_Data.Process=='Red':
                self.imp = self.imp.convert('RGB')
                self.imp = self.imp.getchannel(0)
            elif P_Data.Process=='Green':
                self.imp = self.imp.convert('RGB')
                self.imp = self.imp.getchannel(1)
            elif P_Data.Process=='Blue':
                self.imp = self.imp.convert('RGB')
                self.imp = self.imp.getchannel(2)
            elif P_Data.Process=='RGB':
                self.imp = self.imp.convert('RGB')
            
            self.imp = self.imp.quantize(colors=P_Data.PImg_Number_of_Colors)    
            logging.info('Created '+ P_Data.Process + ' Processed Image of size -->'+str(self.imp.size)+' Pixels')    
                        
    def Set_Initial_Image_Tool_List(self):
        self.Tool_List=[]
        self.Tool_List.append('Ball Pen')
        self.Tool_List.append('Fineliner Pen')
        self.Tool_List.append('Felp Pen')
        self.Tool_List.append('Brush')
        self.Tool_List.append('Needle')
        self.Tool_List.append('Cutter')
        self.Tool_List.append('Pencil')
        self.Tool_List.append('Mechanical Pencil')
        
        self.Selected_Tool=self.Tool_List[1]
        

    def Set_Initial_Technique_List(self):
        self.Technique_List=[]    
        self.Technique_List.append('Stipple')
        self.Technique_List.append('Lineing')
        self.Technique_List.append('Circulism')
        self.Technique_List.append('Delineation')


        self.Selected_Technique=self.Technique_List[1]

    def Set_Initial_Image_Process(self):
        self.Image_Process_List=[]    
        self.Image_Process_List.append('Black&White')
        self.Image_Process_List.append('Red')
        self.Image_Process_List.append('Green')
        self.Image_Process_List.append('Blue')
        self.Image_Process_List.append('RGB')

        self.Selected_Image_Process=self.Image_Process_List[1]
    
    def Set_Initial_Image_Config_Data(self):            
        #self.Image_Config_Data_names=['Img_Height','Img_Width']
        self.Image_Config_Data={}              
        #All with----------------
        CUnit='mm'
        CType='float'
        #----------------
        
        ConfVar='Canvas_Height'        
        CValue=float(297.0)        
        CInfo='Canvas or paper total Height (Y)'
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)
        
        ConfVar='Canvas_Width'        
        CValue=float(210.0)
        CInfo='Canvas or paper total Width (X)'
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        ConfVar='Img_Height'
        Cvalue=float(200.0)
        CInfo='Image Height (Y)'
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        ConfVar='Img_Width'
        CValue=float(200.0)
        CInfo='Image Width (X)'
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        ConfVar='Img_Resolution'
        CValue=float(0.5)
        CInfo='Image Resolution in [mm/pixel]' #image is divided into pixels with this resolution each pixel represents an x,y coordinate
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        ConfVar='Z_Retract'
        CValue=float(3.0)
        CInfo='Amount to retract from canvas to move in [mm]' #image is divided into pixels with this resolution each pixel represents an x,y coordinate
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)
    
        #---------------------------------
        CUnit='mm'
        CType='vector'
        
        ConfVar='Robot_XYZ'
        CValue='0 0 20'
        CInfo='(X,Y,Z) Origin point XYZ of Robot for canvas coordinate (0,0) tool touching the canvas.'
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        ConfVar='Img_ini_pos'
        CValue='10 10'
        CInfo='Origin point XY of Image wrt to canvas(0,0)'
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)
        
        #---------------------------------
        CUnit=''
        CType='bool'
        
        ConfVar='Is_Proportional'
        CValue='True'
        CInfo='When true will Scale the processed image as Original size'
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        ConfVar='Tool_Change'
        CValue='False'
        CInfo='When layer is build goes to Tool_Change_pos for tool to be changed'
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        ConfVar='Include_First_Layer'
        CValue='False'
        CInfo='Includes the white Layer in the process'
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        ConfVar='Include_Last_Layer'
        CValue='False'
        CInfo='Includes the Black Layer in the process'
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        #---------------------------------
        CUnit=''
        CType='int'
        
        ConfVar='Img_Num_Colors'
        CValue=8
        CInfo='The number of colors/Layers used in the Process(<256)'
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        ConfVar='Technique_Rate'
        CValue=2000
        CInfo='Technique rate speed to in [mm/m]' #image is divided into pixels with this resolution each pixel represents an x,y coordinate
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        ConfVar='Frame_Image'
        CValue=0
        CInfo='0=No Frame, 1=Single Line Frame' #image is divided into pixels with this resolution each pixel represents an x,y coordinate
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        #---------------------------------
        CUnit=''
        CType='string'
        
        ConfVar='Ini_Script'
        CValue='G28\nM117 Starting Gimage Code\nG0 X0 Y0\n'
        CInfo='Initial Gcode script for Gimage code'
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        ConfVar='End_Script'
        CValue='G0 Z80\nG0 X0 Y0\nM117 End of Gimage Code\n'
        CInfo='Initial Gcode script for Gimage code'
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        #Set Default values
        self.Default_Image_Config_Data={}
        self.Set_actualConfig_as_new_Defaults()

    def Set_actualConfig_as_new_Defaults(self):    
        for ccc in self.Image_Config_Data:
            self.Default_Image_Config_Data[ccc]=self.Image_Config_Data[ccc]
    
    def Set_To_Default_Conf_Var(self,ConfVar,Cval=1,Cunit=1,Ctype=1,Cinfo=1):
        if Cval==1:
            self.Image_Config_Data[ConfVar]=self.Default_Image_Config_Data[ConfVar]
        if Cunit==1:    
            self.Image_Config_Data[ConfVar+'_Unit']=self.Default_Image_Config_Data[ConfVar+'_Unit']
        if Ctype==1:    
            self.Image_Config_Data[ConfVar+'_Type']=self.Default_Image_Config_Data[ConfVar+'_Type']    
        if Cinfo==1:            
            self.Image_Config_Data[ConfVar+'_Info']=self.Default_Image_Config_Data[ConfVar+'_Info']     
    
    def Get_List_of_Image_Config_Names(self):
        ConfVarlist=[]
        for ccc in self.Image_Config_Data:
            if not '_Info' in ccc and not '_Type' in ccc and not '_Unit' in ccc:   
                ConfVarlist.append(ccc)
        return ConfVarlist

    def Check_Image_Config_Data(self):
        #This checks the formats and types are congruent
        ConfVarlist=self.Get_List_of_Image_Config_Names()        
        for ConfVar in ConfVarlist:        
            if self.Get_Variable_from_Image_Config_Data(ConfVar)==None:
                self.Set_To_Default_Conf_Var(ConfVar)
            #else:
            #   print(str(self.Get_Variable_from_Image_Config_Data(ConfVar))+', Stored:'+str(self.Image_Config_Data[ConfVar]))     
        
        #Length of Vectors are congruent
        ConfVar='Img_ini_pos'
        Varvect=list(self.Get_Variable_from_Image_Config_Data(ConfVar))
        #print(str(Varvect)+'-->'+str(len(Varvect)))
        if len(Varvect)!=2:
            self.Set_To_Default_Conf_Var(ConfVar)                
            #print("Default set:"+str(self.Image_Config_Data[ConfVar]))
        
        ConfVar='Robot_XYZ'
        Varvect=list(self.Get_Variable_from_Image_Config_Data(ConfVar))
        if len(Varvect)!=3:
            self.Set_To_Default_Conf_Var(ConfVar)    
        
        ConfVar='Is_Proportional'
        IsProp=bool(self.Get_Variable_from_Image_Config_Data(ConfVar))
        if IsProp==True:
            self.Set_Image_Proportional_Size()

        ConfVar='Img_Resolution'
        Imres=self.Get_Variable_from_Image_Config_Data(ConfVar)
        if Imres<=0.025:
            self.Set_To_Default_Conf_Var(ConfVar)

        ConfVar='Img_Num_Colors'    
        NC=self.Get_Variable_from_Image_Config_Data(ConfVar)
        if NC<2 or NC>256:
            self.Set_To_Default_Conf_Var(ConfVar)

        #set checked changes as new default
        self.Set_actualConfig_as_new_Defaults()

    def Set_Image_Proportional_Size(self):
        if self.Isimagetoprint==True:
            pW=self.im.width
            pH=self.im.height            
            I_H=self.Get_Variable_from_Image_Config_Data('Img_Height')            
            I_W=self.Get_Variable_from_Image_Config_Data('Img_Width')   
            I_Ho=I_H
            I_Wo=I_W     
            # get defaults
            I_Hd=self.Default_Image_Config_Data['Img_Height']
            I_Wd=self.Default_Image_Config_Data['Img_Width']
            if I_Hd!=I_H and I_Wd==I_W and pH!=0:
                I_W=I_H*pW/pH
                #logging.info('Here 1')
            elif I_Hd==I_H and I_Wd!=I_W and pW!=0:     
                I_H=I_W*pH/pW
                #logging.info('Here 2')
            else:    
                if I_H>I_W and pW!=0:
                    I_H=I_W*pH/pW
                elif I_H<=I_W and pH!=0:
                    I_W=I_H*pW/pH   
            self.Image_Config_Data['Img_Height']=I_H    
            self.Image_Config_Data['Img_Width']=I_W    
            if I_Ho!=I_H or I_Wo!=I_W:
                logging.info('Image Config Size Changed: Img_Width='+str(I_W)+' Img_Height='+str(I_H))            


    def Get_Variable_from_Image_Config_Data(self,Variable):
        if Variable in self.Image_Config_Data:
            if '_Info' in Variable:
                return self.Image_Config_Data[Variable]
            elif '_Unit' in Variable:
                return self.Image_Config_Data[Variable]    
            elif '_Type' in Variable:
                return self.Image_Config_Data[Variable]    
            else:
                try:
                    thetype=self.Image_Config_Data[Variable+'_Type']
                    if thetype=='int':
                        return int(self.Image_Config_Data[Variable])
                    if thetype=='float':
                        return float(self.Image_Config_Data[Variable])    
                    if thetype=='string':
                        return str(self.Image_Config_Data[Variable])    
                    if thetype=='bool':
                        aval=str(self.Image_Config_Data[Variable])
                        if 'True' in aval or 'true' in aval or aval is '1' or aval is 'T':
                            return True
                        elif 'False' in aval or 'false' in aval or aval is '0' or aval is 'F':
                            return False      
                        else:    
                            return ''    
                    if thetype=='vector':
                        alist=[]
                        try:                          
                            line=str(self.Image_Config_Data[Variable]) 
                            mf =re.split(r'\s',line)                               
                        except:
                            mf = None
                        try:
                            if mf is not None:   
                                numitems=len(mf)
                                for item in mf:                                   
                                    #print("Inside vector->"+str(item))
                                    alist.append(float(item))
                                  
                        except Exception as e:
                            logging.error('Bad vector format in '+ Variable)
                            logging.error(e)                        
                            alist=[]
                            pass
                        return alist    
                    #Other formats return string                
                    return str(self.Image_Config_Data[Variable])
                except:
                    logging.error('Bad format in '+Variable)
                    return None
        else:
            return None
    

    def Set_ConfVar(self,CData,ConfVar,CValue,CUnit,CType,CInfo):        
        CData[ConfVar]=CValue
        CData[ConfVar+'_Unit']=CUnit
        CData[ConfVar+'_Type']=CType
        CData[ConfVar+'_Info']=CInfo
        return CData

    def Get_Image_Config_Data(self):        
        return self.Image_Config_Data
    
    def Get_Gimage_Data_for_Stream(self):
        Gimage_Data=Struct_Stream_Data()
        #Here fill info with configuration
        Gimage_Data.Ispimagetoprint=self.IsProcessedimagetoprint
        Gimage_Data.Technique=self.Selected_Technique
        Gimage_Data.Tool=self.Selected_Tool
        Gimage_Data.Process =self.Selected_Image_Process
        Gimage_Data.Robot_XYZ=self.Get_Variable_from_Image_Config_Data('Robot_XYZ')
        Gimage_Data.Img_ini_pos=self.Get_Variable_from_Image_Config_Data('Img_ini_pos')
        Gimage_Data.deltaZ=self.Get_Variable_from_Image_Config_Data('Z_Retract') #mm here value from config
        Gimage_Data.Zmove_pos=Gimage_Data.Robot_XYZ[2]+Gimage_Data.deltaZ
        Gimage_Data.Ztouch_pos=Gimage_Data.Robot_XYZ[2]
        Gimage_Data.Resolution=self.Get_Variable_from_Image_Config_Data('Img_Resolution')
        Gimage_Data.Process_rate=self.Get_Variable_from_Image_Config_Data('Technique_Rate')        
        Gimage_Data.Include_First_Layer=self.Get_Variable_from_Image_Config_Data('Include_First_Layer')
        Gimage_Data.Frame_Image=self.Get_Variable_from_Image_Config_Data('Frame_Image')
        Gimage_Data.Include_Last_Layer=self.Get_Variable_from_Image_Config_Data('Include_Last_Layer')            
        Gimage_Data.Ini_Script=self.Get_Variable_from_Image_Config_Data('Ini_Script')
        Gimage_Data.End_Script=self.Get_Variable_from_Image_Config_Data('End_Script')
        return Gimage_Data           
    
    def Crop_Image_to_Canvas_Size(self,P_Data):        
        P_Data.PImg_ini_pos_mm
        C_Hmm=P_Data.C_Size_mm[1]
        C_Wmm=P_Data.C_Size_mm[0]
        I_Hmm=P_Data.PImg_Size_mm[1]
        I_Wmm=P_Data.PImg_Size_mm[0]
        I_ini_posmm=P_Data.PImg_ini_pos_mm
        I_Rmm=P_Data.PImg_Resolution
        if I_Rmm>0:
            C_H=int(C_Hmm/I_Rmm)
            C_W=int(C_Wmm/I_Rmm)
            I_H=int(I_Hmm/I_Rmm)
            I_W=int(I_Wmm/I_Rmm)
            I_ini_pos=[int(I_ini_posmm[0]/I_Rmm),int(I_ini_posmm[1]/I_Rmm)]

        #crop image if smaller than Canvas
        if C_H<I_ini_pos[1]+I_H:
            val=C_H-I_ini_pos[1]
            if val>0:
                self.imp = self.imp.crop((0, 0, val, C_W)) # crop image
        if C_W<I_ini_pos[0]+I_W:
            val=C_W-I_ini_pos[0]
            if val>0:    
                self.imp = self.imp.crop((0, 0, C_H, val)) # crop image
        
               




    def Test_Image(self):
        im = Image.open("Testimage.png") # load an image from the hard drive
        blurred = im.filter(ImageFilter.BLUR) # blur the image

        im.show() # display both images
        blurred.show()

        rotated = im.rotate(180) # rotates the image by 180 degrees
        #saved = rotated.save("file_rotated.jpg") #saves the rotated image

        im1 = im.crop((100, 100, 250, 250)) # crop image

        rgb_im = im.convert('RGB')
        r, g, b = rgb_im.getpixel((1, 1))
        L_im = im.convert('L')
        L = L_im.getpixel((1, 1))

        print(r, g, b, L)

        print(im.size)
        print('width: ', im.width) # pixels 
        print('height:', im.height)         
                


class Image_Gcode_Stream(threading.Thread):
    
    #def __init__(self,xyz_thread,killer_event,holding_event,stoping_event):        
    def __init__(self,killer_event,plaintextEdit_GcodeScript):        
        threading.Thread.__init__(self, name="Image Gcode Stream")
        logging.info("Image Gcode Stream Started")
        self.plaintextEdit_GcodeScript=plaintextEdit_GcodeScript        
        #self.xyz_thread=xyz_thread
        self.killer_event=killer_event
        #self.holding_event=holding_event
        #self.stoping_event=stoping_event                
        self.cycle_time=0.1               
        self.state_xyz=0

        self.Isimagetoprint=False
        self.istext2stream=False
        self.Isxyz_thread=False
        self.text_queue = queue.Queue()
    
    def Set_xyz_thread(self,xyz_thread,stoping_event):
        self.xyz_thread=xyz_thread  
        self.holding_event=self.xyz_thread.grbl_event_hold     
        self.stoping_event=stoping_event
        self.Isxyz_thread=True

    def wait_until_finished(self,a_count):
        count=0
        if self.state_xyz==3:
            while self.state_xyz==self.oldstate_xyz and count<a_count:
                self.data = self.xyz_thread.read()                
                self.get_state()
                time.sleep(self.cycle_time)
                count=count+1            
        self.oldstate_xyz=self.state_xyz
        while self.state_xyz==5:
            self.data = self.xyz_thread.read()                
            self.get_state()
            time.sleep(self.cycle_time)
     
    def get_state(self):        
        self.state_xyz=self.data['STATE_XYZ'] 

    def run(self):                
        count=0
        while not self.killer_event.wait(self.cycle_time):   
            if self.Isxyz_thread==True:
                try:
                    self.data = self.xyz_thread.read()                
                    self.get_state()
                    if self.stoping_event.is_set()==True:
                        self.Stop_Clear()
                    if self.holding_event.is_set()==False:                    
                        try:
                            #logging.info("Run entered 7")
                            line2stream= self.text_queue.get_nowait()
                            self.stream_one_line(line2stream)          
                            self.data = self.xyz_thread.read()                
                            self.get_state()
                            if self.state_xyz==11: # error
                                logging.info("Error in Gcode detected! (" + str(line2stream)+') ' )
                                self.Stop_Clear()
                            self.wait_until_finished(20000)    
                        except queue.Empty:                    
                            pass
                    
                    
                except:
                    if count==0:
                        logging.info("Image Gcode Stream can't get data to update")                         
                    else:
                        count=count+1
                    if count>=2000:
                        count=0        
        logging.info("Image Gcode Stream killed")          
    
    def Stop_Clear(self):
        if self.istext2stream==True:
            self.text_queue.empty()
            self.istext2stream=False
            logging.info("Image Gcode Stream Stopped!")
        self.stoping_event.clear()

    def read(self):
        return self.data
     
    def stream_one_line(self,line2stream):
        if self.istext2stream==True:
            self.xyz_thread.grbl_gcode_cmd(line2stream)
    
    def Get_Pixel(self,x,y,Resolution):
        [x,y]=self.Transform_pixel_coordinates_to_image_coordinates(x,y)
        self.imp.getpixel((x, y))
    
    def Transform_pixel_coordinates_to_image_coordinates(self,x,y,Resolution=1):
        # (0,0) is the upper left corner
        y=self.imp.height-y
        x=Resolution*x
        y=Resolution*y
        # Add robot image origin position
        y=y+self.Img_ini_pos[1]+self.Robot_XYZ[1]
        x=x+self.Img_ini_pos[0]+self.Robot_XYZ[0]
        return [x,y]

    def Generate_Gimage_Code(self,pimage,Gimage_Data,P_Bar_Update_Gimage):
        self.Gimage_Code=''            
        self.Gimage_Code_loop=''
        if Gimage_Data.Ispimagetoprint==True:            
            #pimg_arr=np.array(self.imp)    
            self.imp=pimage  
            self.Technique=Gimage_Data.Technique
            self.Tool=Gimage_Data.Tool
            self.Process=Gimage_Data.Process                         
            self.Robot_XYZ=Gimage_Data.Robot_XYZ
            self.Img_ini_pos=Gimage_Data.Img_ini_pos            
            Zinfo=[Gimage_Data.deltaZ,Gimage_Data.Zmove_pos,Gimage_Data.Ztouch_pos,Gimage_Data.Resolution,Gimage_Data.Process_rate]

            #get min max range
            pimg_val_range=[0,256,0]
            for xxx in range(0,self.imp.width):
                #print(str(xxx))
                for yyy in range(0,self.imp.height):
                    #print(str(yyy))    
                    avalue=self.imp.getpixel((xxx,yyy))
                    if avalue<pimg_val_range[1]:
                        pimg_val_range[1]=avalue
                    if avalue>pimg_val_range[2]:
                        pimg_val_range[2]=avalue   
            if Gimage_Data.Include_Last_Layer==True:
                pimg_val_range[2]=pimg_val_range[2]+1
            if Gimage_Data.Include_First_Layer==True:
                pimg_val_range[1]=pimg_val_range[1]-1                                            
            logging.info(self.Technique+' Process Started') 
            self.Gimage_Code='' 
            print('Ini script-> '+Gimage_Data.Ini_Script)
            if Gimage_Data.Ini_Script is not '':                 
                self.Gimage_Code=self.Gimage_Code+Gimage_Data.Ini_Script.replace('\\n','\n')
            if Gimage_Data.Frame_Image==1:
                inicoor=self.Transform_pixel_coordinates_to_image_coordinates(0,0,Gimage_Data.Resolution)                
                endcoor=self.Transform_pixel_coordinates_to_image_coordinates(self.imp.width,self.imp.height,Gimage_Data.Resolution)
                print(str([inicoor,endcoor]))
                self.Gimage_Code=self.Gimage_Code+self.Do_a_line_Frame(True,inicoor,endcoor,Zinfo)   
            if self.Technique=='Stipple':                
                self.Gimage_Code=self.Gimage_Code+self.Write_Gimage_Code_Stippling(pimg_val_range,Zinfo,P_Bar_Update_Gimage)                  
            if self.Technique=='Lineing':        
                self.Gimage_Code=self.Gimage_Code+self.Write_Gimage_Code_Lineing(pimg_val_range,Zinfo,P_Bar_Update_Gimage)
            if Gimage_Data.End_Script is not '':             
                self.Gimage_Code=self.Gimage_Code+Gimage_Data.End_Script.replace('\\n','\n')
            logging.info(self.Technique+' Process Finished')    
        return self.Gimage_Code    
    
    def Do_a_line_Frame(self,Isclockwise,Coordsinimm,Coordsendmm,Zinfo):
        [deltaZ,Zmove_pos,Ztouch_pos,Resolution,Process_rate]=Zinfo
        Lcode=''
        [Lcodeadd,is_up]=self.Lineing_UpDown(False,Zinfo)
        Lcode=Lcode+Lcodeadd
        Lcode=Lcode+self.Write_Goto_Code(0,xxx=Coordsinimm[0],yyy=Coordsinimm[1])
        ##Pull down
        [Lcodeadd,is_up]=self.Lineing_UpDown(is_up,Zinfo)
        Lcode=Lcode+Lcodeadd
        if Isclockwise==True:            
            Lcode=Lcode+self.Write_Goto_Code(1,xxx=Coordsinimm[0],yyy=Coordsendmm[1],fff=Process_rate)
            Lcode=Lcode+self.Write_Goto_Code(1,xxx=Coordsendmm[0],yyy=Coordsendmm[1],fff=Process_rate)
            Lcode=Lcode+self.Write_Goto_Code(1,xxx=Coordsendmm[0],yyy=Coordsinimm[1],fff=Process_rate)
            Lcode=Lcode+self.Write_Goto_Code(1,xxx=Coordsinimm[0],yyy=Coordsinimm[1],fff=Process_rate)
        else:            
            Lcode=Lcode+self.Write_Goto_Code(1,xxx=Coordsendmm[0],yyy=Coordsinimm[1],fff=Process_rate)
            Lcode=Lcode+self.Write_Goto_Code(1,xxx=Coordsendmm[0],yyy=Coordsendmm[1],fff=Process_rate)
            Lcode=Lcode+self.Write_Goto_Code(1,xxx=Coordsinimm[0],yyy=Coordsendmm[1],fff=Process_rate)    
            Lcode=Lcode+self.Write_Goto_Code(1,xxx=Coordsinimm[0],yyy=Coordsinimm[1],fff=Process_rate)
        ##Pull up
        [Lcodeadd,is_up]=self.Lineing_UpDown(False,Zinfo)
        Lcode=Lcode+Lcodeadd
        return Lcode

    def Write_Gimage_Code_Lineing(self,pimg_val_range,Zinfo,P_Bar_Update_Gimage):      
        [deltaZ,Zmove_pos,Ztouch_pos,Resolution,Process_rate]=Zinfo   
        last_avalue=0
        is_up=True
        Lcode=''
        for aaa in range(pimg_val_range[1],pimg_val_range[2]):
            P_Bar_Update_Gimage.SetStatus(aaa/pimg_val_range[2]*100)
            if aaa==pimg_val_range[1]:                 
                [pimg_X,pimg_Y]=self.Transform_pixel_coordinates_to_image_coordinates(0,0,Resolution)  
                Lcode=Lcode+self.Write_Goto_Code(0,xxx=pimg_X,yyy=pimg_Y,fff=Process_rate)
                [Lcodeadd,is_up]=self.Lineing_UpDown(False,Zinfo)
                Lcode=Lcode+Lcodeadd            
            else:       
                if aaa % 2 == 0:                            
                    for xxx in range(0,self.imp.width):                                                       
                        if xxx % 2 == 0:
                            for yyy in range(0,self.imp.height):   
                                [Lcode,is_up]=self.Write_Gimage_Process_Code_Lineing(Lcode,aaa,is_up,pimg_val_range,xxx,yyy,Zinfo)
                        else:        
                            for yyy in reversed(range(0,self.imp.height)):   
                                [Lcode,is_up]=self.Write_Gimage_Process_Code_Lineing(Lcode,aaa,is_up,pimg_val_range,xxx,yyy,Zinfo)
                else:                                                                           
                    for yyy in range(0,self.imp.height):   
                        if yyy % 2 == 0:
                            for xxx in range(0,self.imp.width):
                                [Lcode,is_up]=self.Write_Gimage_Process_Code_Lineing(Lcode,aaa,is_up,pimg_val_range,xxx,yyy,Zinfo)            
                        else:
                            for xxx in reversed(range(0,self.imp.width)):
                                [Lcode,is_up]=self.Write_Gimage_Process_Code_Lineing(Lcode,aaa,is_up,pimg_val_range,xxx,yyy,Zinfo)                    

        [Lcodeadd,is_up]=self.Lineing_UpDown(False,Zinfo)
        Lcode=Lcode+Lcodeadd   
        return Lcode            
                    
    def Write_Gimage_Process_Code_Lineing(self,Lcode,aaa,is_up,pimg_val_range,xxx,yyy,Zinfo):
        [deltaZ,Zmove_pos,Ztouch_pos,Resolution,Process_rate]=Zinfo                
        avalue=self.imp.getpixel((xxx, yyy)) 
        pimg_val_range[0]=avalue       
        [pimg_X,pimg_Y]=self.Transform_pixel_coordinates_to_image_coordinates(xxx,yyy,Resolution)                                          
        [pimg_Xend,pimg_Yend]=self.Transform_pixel_coordinates_to_image_coordinates(xxx,yyy,Resolution)                                                 
        if avalue==aaa:                                                   
            if is_up==True:
                [pimg_X,pimg_Y]=self.Transform_pixel_coordinates_to_image_coordinates(xxx,yyy,Resolution)                                          
                [pimg_Xend,pimg_Yend]=self.Transform_pixel_coordinates_to_image_coordinates(xxx,yyy,Resolution)
                #Put Down
                Lcode=Lcode+self.Write_Goto_Code(1,xxx=pimg_X,yyy=pimg_Y,fff=Process_rate)
                [Lcodeadd,is_up]=self.Lineing_UpDown(is_up,Zinfo)
                Lcode=Lcode+Lcodeadd
                is_up=False                                
            else:
                #update end coordinates
                [pimg_Xend,pimg_Yend]=self.Transform_pixel_coordinates_to_image_coordinates(xxx,yyy,Resolution)  
        elif avalue!=aaa:
            if is_up==False:
                Lcode=Lcode+self.Write_Goto_Code(1,xxx=pimg_Xend,yyy=pimg_Yend,fff=Process_rate)
                #Lift
                [Lcodeadd,is_up]=self.Lineing_UpDown(is_up,Zinfo)
                Lcode=Lcode+Lcodeadd
                is_up=True
        elif yyy>=self.imp.height-1 or xxx>=self.imp.width-1 or xxx==0 or yyy==0:                            
            if is_up==False:
                Lcode=Lcode+self.Write_Goto_Code(1,xxx=pimg_Xend,yyy=pimg_Yend,fff=Process_rate)
                #Lift
                [Lcodeadd,is_up]=self.Lineing_UpDown(is_up,Zinfo)
                Lcode=Lcode+Lcodeadd
                is_up=True
        return [Lcode,is_up]        

    def Lineing_UpDown(self,Is_up,Zinfo):
        [deltaZ,Zmove_pos,Ztouch_pos,Resolution,Process_rate]=Zinfo
        if Is_up==True:
            Lcode=self.Write_Goto_Code(0,zzz=Ztouch_pos)
            return [Lcode,False]
        else: 
            Lcode=self.Write_Goto_Code(0,zzz=Zmove_pos)
            return [Lcode,True]
        return 
    
    def Write_Gimage_Code_Stippling(self,pimg_val_range,Zinfo,P_Bar_Update_Gimage):  
        [deltaZ,Zmove_pos,Ztouch_pos,Resolution,Process_rate]=Zinfo          
        Gimage_Code=''
        for xxx in range(0,self.imp.width):
            #print(str(xxx/pimage.width*100)+'%')
            P_Bar_Update_Gimage.SetStatus(xxx/self.imp.width*100)
            for yyy in range(0,self.imp.height):
                avalue=self.imp.getpixel((xxx, yyy))
                [pimg_X,pimg_Y]=self.Transform_pixel_coordinates_to_image_coordinates(xxx,yyy,Resolution)  
                pimg_val_range[0]=avalue                                                        
                Gimage_Code_loop=self.Write_Gimage_Process_Code_Stippling(pimg_val_range,pimg_X,pimg_Y,Zinfo)
                Gimage_Code=Gimage_Code+Gimage_Code_loop 
        return Gimage_Code

    def Write_Gimage_Process_Code_Stippling(self,pimg_val_range,xxx,yyy,Zinfo):
        [deltaZ,Zmove_pos,Ztouch_pos,Resolution,Process_rate]=Zinfo
        iii=0
        randomlist = []
        randomlist.clear()       
        Lcode='' 
        for aaa in range(pimg_val_range[1],pimg_val_range[0]):
            iii=iii+1
            for bbb in range(0,2): #Generate 2 random numbers per item
                nnn = random.randint(0,12)
                randomlist.append((nnn-6)/6) #number beween -1 and 1 1/6 quantification
        sss=0   
        #print(str(randomlist))     
        if iii>1: #Only write if the value has color
            Lcode=self.Write_Goto_Code(0,zzz=Zmove_pos)
            Lcode=Lcode+self.Write_Goto_Code(0,xxx=xxx,yyy=yyy)            
            for aaa in range(pimg_val_range[1],pimg_val_range[0]):  
                if aaa>pimg_val_range[1]:                                               
                    newx=xxx+Resolution*randomlist[sss]
                    sss=sss+1    
                    newy=yyy+Resolution*randomlist[sss]
                    sss=sss+1
                    Lcode=Lcode+self.Write_Goto_Code(1,xxx=newx,yyy=newy,zzz=Ztouch_pos,fff=Process_rate)
                    Lcode=Lcode+self.Write_Goto_Code(1,xxx=xxx,yyy=yyy,zzz=Ztouch_pos+deltaZ,fff=Process_rate)                               
        return Lcode    

    def Write_Goto_Code(self,GX,xxx=None,yyy=None,zzz=None,fff=None,eee=None,aaachar='',aaa=None,e_o_l='\n'):
        Gimgcode='G'+str(GX)
        if xxx!=None:
            Gimgcode=Gimgcode+' X'+str("{0:.3f}".format(xxx))
        if yyy!=None:
            Gimgcode=Gimgcode+' Y'+str("{0:.3f}".format(yyy))    
        if zzz!=None:
            Gimgcode=Gimgcode+' Z'+str("{0:.3f}".format(zzz))
        if fff!=None:
            Gimgcode=Gimgcode+' F'+str(fff)
        if eee!=None:
            Gimgcode=Gimgcode+' E'+str(eee)   
        if aaachar is not '':
            Gimgcode=Gimgcode+' '+aaachar              
        if aaa!=None:
            Gimgcode=Gimgcode+str(aaa)     
        return Gimgcode+e_o_l 
    
    


    
    




