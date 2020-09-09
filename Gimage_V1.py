from PIL import Image, ImageFilter  # imports the library
import threading
import queue
import re
import logging
import time
from common import *

# install pySerial NOT serial!!!
import serial

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s')


class GImage:
    def __init__(self):
        self.filename=''        
        self.prnt_height=0 # mm
        self.prnt_width=0  # mm
        self.im_width=0 # pixels
        self.im_height=0 # pixels
        self.point_resolution=0.1 # mm
        self.Isimagetoprint=False
        self.Set_Initial_Image_Config_Data()

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


    def show_image(self):
        if self.Isimagetoprint==True:
            self.im.show() # load an image from the hard drive    
        else:
            logging.info("NO IMAGE")      

    def Set_Image_end_size(self,prnt_width,prnt_height):    
        self.prnt_height=prnt_height
        self.prnt_width=prnt_height
        if self.im_width > 0 and self.im_height > 0:
            self.pix_per_mm_width=int(self.prnt_width/self.im_width)
            self.pix_per_mm_height=int(self.prnt_height/self.im_height)            
        else:
            self.pix_per_mm_width=0
            self.pix_per_mm_height=0
            self.Isimagetoprint=False
    
    def Resize_to_print_size(self):
        if self.im_width > 0 and self.im_height > 0:
            newsize=(int(self.prnt_width/point_resolution),int(self.prnt_height/point_resolution))
            self.imtoprint=self.im.resize(newsize)    #puts the image to the end size for value in each pixel
            self.Isimagetoprint=True
    
    def Image_to_gcode(self,Tool,Technique,Type_Layer):
        if self.Isimagetoprint==True:
            if Type_Layer=='R' or Type_Layer=='G' or Type_Layer=='B':
                conv_imtoprint = self.imtoprint.convert('RGB')
            if Type_Layer=='L': #Gray scale
                conv_imtoprint = self.imtoprint.convert('L')    
                #L = conv_imtoprint.getpixel((1, 1))

            #if Technique=='stipple':
            #if Technique=='circulism':
            #if Technique=='squares':
    
    def Set_Initial_Image_Config_Data(self):            
        self.Image_Config_Data_names=['Img_Height','Img_Width']
        self.Image_Config_Data={}
        self.Image_Config_Data['Img_Height']=float(210.0)
        self.Image_Config_Data['Img_Height_Unit']='mm'
        self.Image_Config_Data['Img_Height_Type']='float'
        self.Image_Config_Data['Img_Height_Info']='Image Height'

        self.Image_Config_Data['Img_Width']=float(210.0)
        self.Image_Config_Data['Img_Width_Unit']='mm'
        self.Image_Config_Data['Img_Width_Type']='float'
        self.Image_Config_Data['Img_Width_Info']='Image Width'
    
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
    
    


    
    




