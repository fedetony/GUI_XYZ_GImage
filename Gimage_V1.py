from PIL import Image, ImageFilter  # imports the library
from PIL.ImageQt import ImageQt

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
            print(str(Process_Data.PImg_Size_mm))
            if self.im.width > 0 and self.im.height > 0:
                Process_Data.pix_per_mm_width=int(Process_Data.PImg_Size_mm[0]/self.im.width)
                Process_Data.pix_per_mm_height=int(Process_Data.PImg_Size_mm[1]/self.im.height)                        
            Process_Data.PImg_Size_px=[Process_Data.pix_per_mm_width*Process_Data.PImg_Size_mm[0],Process_Data.pix_per_mm_width*Process_Data.PImg_Size_mm[1]]

        return Process_Data

    def Process_Image(self):
        if self.Isimagetoprint==True:
            Process_Data=self.Get_Process_Data()
            self.Create_Processed_Image(Process_Data)
            self.appply_process_to_imp(Process_Data)
            logging.info('Image Process Done')
            print(str(self.IsProcessedimagetoprint))
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
            
    def Get_Pixel(self,x,y):
        [x,y]=self.Transform_pixel_coordinates_to_image_coordinates(x,y)
        self.imp.getpixel(x, y)
    
    def Transform_pixel_coordinates_to_image_coordinates(self,x,y):
        # (0,0) is the upper left corner
        y=self.imp.height-y
        return [x,y]

    def Image_to_gcode(self,Tool,Technique,Process_Data):
        if self.IsProcessedimagetoprint==True:
            self.Get_Pixel(0, 0)    
            #L = conv_imtoprint.getpixel((1, 1))

            #if Technique=='stipple':
            #if Technique=='circulism':
            #if Technique=='squares':
    
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
        CValue=float(210.0)        
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
        CValue=float(0.1)
        CInfo='Image Resolution in [mm/pixel]' #image is divided into pixels with this resolution each pixel represents an x,y coordinate
        self.Image_Config_Data=self.Set_ConfVar(self.Image_Config_Data,ConfVar,CValue,CUnit,CType,CInfo)

        #---------------------------------
        CUnit='mm'
        CType='vector'
        
        ConfVar='Robot_XYZ'
        CValue='1 2.1 3'
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

        #---------------------------------
        CUnit=''
        CType='int'
        
        ConfVar='Img_Num_Colors'
        CValue=8
        CInfo='Will reduce the number of colors used in the Process(<256)'
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
    def __init__(self,xyz_thread,killer_event,holding_event,stoping_event):
        threading.Thread.__init__(self, name="Image Gcode Stream")
        logging.info("Image Gcode Stream Started")
        self.xyz_thread=xyz_thread
        self.killer_event=killer_event
        self.holding_event=holding_event
        self.stoping_event=stoping_event        
        self.cycle_time=0.1               
        self.state_xyz=0
        self.prnt_height=0 #mm
        self.prnt_width=0  #mm
        self.im_width=0 # pixels
        self.im_height=0
        self.point_resolution=0.1 #
        self.Isimagetoprint=False
        self.istext2stream=False
        self.text_queue = queue.Queue()
        

    

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
    
    


    
    




