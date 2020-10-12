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

import GuiXYZ_RTD 

class ResizeToolDialog(QWidget,GuiXYZ_RTD.Ui_Dialog_RTD):
    set_clicked= QtCore.pyqtSignal(list)
    #def __init__(self,NumLayers,Selected_Layers,parent=None):    
    #    super().__init__(parent)
    def __init__(self,Resize_Data_List, *args, **kwargs):
        super(ResizeToolDialog, self).__init__(*args, **kwargs)    
        self.IsRTDim=False
        self.Scale=1
        self.Resize_Data_List=Resize_Data_List    
        self.openResizeToolDialog()
        [self.Machine_Size,self.Machine_pos,self.Canvas_pos,self.Canvas_Size,self.Image_pos,self.Image_Size,self.Frame]=self.Resize_Data_List
        self.Set_Data_List(self.Resize_Data_List)
        self.Actualize_labels_positions()
        self.RTD_Connect_Actions()
    
    def quit(self):
        self.Dialog_RTD.close()
           
    def openResizeToolDialog(self):
        self.Dialog_RTD = QtWidgets.QDialog()
        self.DRui = GuiXYZ_RTD.Ui_Dialog_RTD()
        self.DRui.setupUi(self.Dialog_RTD)
        #self.set_objects_fromNum_layers(self.Number_of_Layers)        
        self.Dialog_RTD.show()             
        self.DRui.pushButton_RTD_Set_Resized.clicked.connect(self.PB_RTD_Set_Preview)
            
    def PB_RTD_Set_Preview(self):            
        #print('clicked')
        self.Update_Resize_Data_List()
        self.set_clicked.emit(self.Resize_Data_List)

    def Update_Resize_Data_List(self):
        self.Resize_Data_List=[self.Machine_Size,self.Machine_pos,self.Canvas_pos,self.Canvas_Size,self.Image_pos,self.Image_Size,self.Frame]
    
    def accept(self):
        #print('accepted')
        #self.Get_Selected_Layers_From_checkbox()
        self.Update_Resize_Data_List()
        return self.Resize_Data_List  
    
    def Set_Data_List(self,Data_List):
        #print(Data_List)
        [Machine_Size,Machine_pos,Canvas_pos,Canvas_Size,Image_pos,Image_Size,Frame]=Data_List
        self.Set_Machine_Size(Machine_Size)
        self.Set_Machine_pos(Machine_pos)
        self.Set_Canvas_pos(Canvas_pos)    
        self.Set_Canvas_Size(Canvas_Size)   
        self.Set_Image_pos(Image_pos)   
        self.Set_Image_Size(Image_Size)     
        self.Set_Frame(Frame)                 

    def RTD_Connect_Actions(self):
        #self.DRui.groupBox_RTD_Resize.

        self.DRui.lineEdit_RTD_Machine_Size_x.editingFinished.connect(self.Put_Machine_Size)
        self.DRui.lineEdit_RTD_Machine_Size_y.editingFinished.connect(self.Put_Machine_Size)
        self.DRui.lineEdit_RTD_Machine_Size_z.editingFinished.connect(self.Put_Machine_Size)
        
        self.DRui.lineEdit_RTD_Machine_pos_x.editingFinished.connect(self.Put_Machine_pos)
        self.DRui.lineEdit_RTD_Machine_pos_y.editingFinished.connect(self.Put_Machine_pos)
        self.DRui.lineEdit_RTD_Machine_pos_z.editingFinished.connect(self.Put_Machine_pos) 

        self.DRui.lineEdit_RTD_Canvas_pos_x.editingFinished.connect(self.Put_Canvas_pos)
        self.DRui.lineEdit_RTD_Canvas_pos_y.editingFinished.connect(self.Put_Canvas_pos)

        self.DRui.lineEdit_RTD_Canvas_Size_W.editingFinished.connect(self.Put_Canvas_Size)
        self.DRui.lineEdit_RTD_Canvas_Size_H.editingFinished.connect(self.Put_Canvas_Size)  

        self.DRui.lineEdit_RTD_Image_pos_x.editingFinished.connect(self.Put_Image_pos)
        self.DRui.lineEdit_RTD_Image_pos_y.editingFinished.connect(self.Put_Image_pos)

        self.DRui.lineEdit_RTD_Image_Size_W.editingFinished.connect(self.Put_Image_Size)
        self.DRui.lineEdit_RTD_Image_Size_H.editingFinished.connect(self.Put_Image_Size)

        self.DRui.spinBox_RTD_Frame.valueChanged.connect(self.Put_Frame)
    
    def Put_All(self):
        self.Put_Machine_Size()
        self.Put_Machine_pos()
        self.Put_Canvas_pos()
        self.Put_Canvas_Size()
        self.Put_Image_pos()
        self.Put_Image_Size()
        self.Put_Frame()

    def Put_Machine_Size(self):
        Machine_Size=self.Get_Machine_Size()
        #print('Got '+str(Machine_Size)+' had '+str(self.Machine_Size))
        self.Set_Machine_Size(Machine_Size) #if accepted
        self.Machine_Size=self.Get_Machine_Size()        
        self.Actualize_labels_positions()

    def Put_Machine_pos(self):
        Machine_pos=self.Get_Machine_pos()        
        #print('Got '+str(Machine_pos)+' had '+str(self.Machine_pos))
        self.Set_Machine_pos(Machine_pos) #if accepted
        self.Machine_pos=self.Get_Machine_pos()        
        #print('Got after '+str(Machine_pos)+' had '+str(self.Machine_pos))
        self.Actualize_labels_positions() 

    def Put_Canvas_pos(self):
        Canvas_pos=self.Get_Canvas_pos()        
        self.Set_Canvas_pos(Canvas_pos) #if accepted
        self.Canvas_pos=self.Get_Canvas_pos()        
        self.Actualize_labels_positions() 

    def Put_Canvas_Size(self):
        Canvas_Size=self.Get_Canvas_Size()        
        self.Set_Canvas_Size(Canvas_Size) #if accepted
        self.Canvas_Size=self.Get_Canvas_Size()        
        self.Actualize_labels_positions()     

    def Put_Image_Size(self):
        Image_Size=self.Get_Image_Size()        
        self.Set_Image_Size(Image_Size) #if accepted
        self.Image_Size=self.Get_Image_Size()        
        self.Actualize_labels_positions() 

    def Put_Image_pos(self):
        Image_pos=self.Get_Image_pos()        
        self.Set_Image_pos(Image_pos) #if accepted
        self.Image_pos=self.Get_Image_pos()        
        self.Actualize_labels_positions()     

    def Put_Frame(self):
        self.Frame=self.Get_Frame()
        if self.Frame==0:
           self.DRui.label_RTD_Image.setStyleSheet("border: No border;") 
        else:
           self.DRui.label_RTD_Image.setStyleSheet("border: 2px solid black;")  
           #self.DRui.label_RTD_Image.setStyleSheet("border: 2px solid blue;") 
    
    def Get_Machine_Size(self):
        Data=self.Machine_Size
        try:
            Data[0]=float(self.DRui.lineEdit_RTD_Machine_Size_x.text())
            Data[1]=float(self.DRui.lineEdit_RTD_Machine_Size_y.text())
            Data[2]=float(self.DRui.lineEdit_RTD_Machine_Size_z.text())
        except Exception as e:
            logging.error(e)
            self.Set_Machine_Size(self.Machine_Size)
            Data=self.Machine_Size
        return Data    

    def Set_Machine_Size(self,Machine_Size):
        if Machine_Size is not None:
            
            self.DRui.lineEdit_RTD_Machine_Size_x.setText(str("{0:.2f}".format(Machine_Size[0])))
            self.DRui.lineEdit_RTD_Machine_Size_y.setText(str("{0:.2f}".format(Machine_Size[1])))
            self.DRui.lineEdit_RTD_Machine_Size_z.setText(str("{0:.2f}".format(Machine_Size[2])))        

    def Get_Machine_pos(self):
        Data=self.Machine_pos
        try:
            Data[0]=float(self.DRui.lineEdit_RTD_Machine_pos_x.text())
            Data[1]=float(self.DRui.lineEdit_RTD_Machine_pos_y.text())
            Data[2]=float(self.DRui.lineEdit_RTD_Machine_pos_z.text())
        except Exception as e:
            logging.error(e)
            self.Set_Machine_pos(self.Machine_pos)
            Data=self.Machine_pos
        return Data   
        

    def Set_Machine_pos(self,Machine_pos):
        if Machine_pos is not None:
            self.DRui.lineEdit_RTD_Machine_pos_x.setText(str("{0:.2f}".format(Machine_pos[0])))
            self.DRui.lineEdit_RTD_Machine_pos_y.setText(str("{0:.2f}".format(Machine_pos[1])))
            self.DRui.lineEdit_RTD_Machine_pos_z.setText(str("{0:.2f}".format(Machine_pos[2])))

    def Get_Canvas_pos(self):
        Data=self.Canvas_pos
        try:
            Data[0]=float(self.DRui.lineEdit_RTD_Canvas_pos_x.text())
            Data[1]=float(self.DRui.lineEdit_RTD_Canvas_pos_y.text())            
        except:
            self.Set_Canvas_pos(self.Canvas_pos)
            Data=self.Canvas_pos
        return Data           

    def Set_Canvas_pos(self,Canvas_pos):
        if Canvas_pos is not None:
            self.DRui.lineEdit_RTD_Canvas_pos_x.setText(str("{0:.2f}".format(Canvas_pos[0])))
            self.DRui.lineEdit_RTD_Canvas_pos_y.setText(str("{0:.2f}".format(Canvas_pos[1])))

    def Get_Canvas_Size(self):
        Data=self.Canvas_Size
        try:
            Data[0]=float(self.DRui.lineEdit_RTD_Canvas_Size_W.text())
            Data[1]=float(self.DRui.lineEdit_RTD_Canvas_Size_H.text())            
        except:
            self.Set_Canvas_Size(self.Canvas_Size)
            Data=self.Canvas_Size
        return Data  
        
    def Set_Canvas_Size(self,Canvas_Size):
        if Canvas_Size is not None:
            self.DRui.lineEdit_RTD_Canvas_Size_W.setText(str("{0:.2f}".format(Canvas_Size[0])))
            self.DRui.lineEdit_RTD_Canvas_Size_H.setText(str("{0:.2f}".format(Canvas_Size[1])))    

    def Get_Image_pos(self):
        Data=self.Image_pos
        try:
            Data[0]=float(self.DRui.lineEdit_RTD_Image_pos_x.text())
            Data[1]=float(self.DRui.lineEdit_RTD_Image_pos_y.text())            
        except:
            self.Set_Image_pos(self.Image_pos)
            Data=self.Image_pos
        return Data          

    def Set_Image_pos(self,Image_pos):
        if Image_pos is not None:
            self.DRui.lineEdit_RTD_Image_pos_x.setText(str("{0:.2f}".format(Image_pos[0])))
            self.DRui.lineEdit_RTD_Image_pos_y.setText(str("{0:.2f}".format(Image_pos[1])))

    def Get_Image_Size(self):
        Data=self.Image_Size
        try:
            Data[0]=float(self.DRui.lineEdit_RTD_Image_Size_W.text())
            Data[1]=float(self.DRui.lineEdit_RTD_Image_Size_H.text())            
        except:
            self.Set_Image_Size(self.Image_Size)
            Data=self.Image_Size
        return Data             

    def Set_Image_Size(self,Image_Size):
        if Image_Size is not None:
            self.DRui.lineEdit_RTD_Image_Size_W.setText(str("{0:.2f}".format(Image_Size[0])))
            self.DRui.lineEdit_RTD_Image_Size_H.setText(str("{0:.2f}".format(Image_Size[1])))

    def Get_Frame(self):
        Data=self.Frame
        try:
            Data=int(self.DRui.spinBox_RTD_Frame.value())            
        except:
            self.Set_Frame(self.Frame)
        return Data             
                
    def Set_Frame(self,Frame):
        if Frame >= 0:
            self.DRui.spinBox_RTD_Frame.setValue(int(Frame))

    def Get_Data_List(self):        
        Machine_Size=self.Get_Machine_Size()
        Machine_pos=self.Get_Machine_pos()
        Canvas_pos=self.Get_Canvas_pos()    
        Canvas_Size=self.Get_Canvas_Size()   
        Image_pos=self.Get_Image_pos()   
        Image_Size=self.Get_Image_Size()     
        Frame=self.Get_Frame()    
        Data_List=[Machine_Size,Machine_pos,Canvas_pos,Canvas_Size,Image_pos,Image_Size,Frame]
        
    def Set_Unit_tooltip_info(self,RTD_dict):
        self.DRui.label_RTD_Machine_Size_unit.setText(RTD_dict['RSize'+'_Unit'])
        self.DRui.label_RTD_Machine_pos_unit.setText(RTD_dict['Rpos'+'_Unit'])
        self.DRui.label_RTD_Canvas_pos_unit.setText(RTD_dict['Cpos'+'_Unit'])
        self.DRui.label_RTD_Canvas_Size_unit.setText(RTD_dict['CSize'+'_Unit'])
        self.DRui.label_RTD_Image_pos_unit.setText(RTD_dict['Ipos'+'_Unit'])
        self.DRui.label_RTD_Image_Size_unit.setText(RTD_dict['ISize'+'_Unit'])
        #RTD_dict['Frame'+'_Unit'])

        self.DRui.label_RTD_Machine_Size_unit.setToolTip(RTD_dict['RSize'+'_Info'])
        self.DRui.label_RTD_Machine_pos_unit.setToolTip(RTD_dict['Rpos'+'_Info'])
        self.DRui.label_RTD_Canvas_pos_unit.setToolTip(RTD_dict['Cpos'+'_Info'])
        self.DRui.label_RTD_Canvas_Size_unit.setToolTip(RTD_dict['CSize'+'_Info'])
        self.DRui.label_RTD_Image_pos_unit.setToolTip(RTD_dict['Ipos'+'_Info'])
        self.DRui.label_RTD_Image_Size_unit.setToolTip(RTD_dict['ISize'+'_Info'])
        self.DRui.spinBox_RTD_Frame.setToolTip(RTD_dict['Frame'+'_Info'])

    def Actualize_labels_positions(self):        
        self.Set_Scale()
        self.Set_Machine_label()
        self.Set_Canvas_label()    
        self.Set_Image_label()  
        self.Set_Machine_Point_label()  

    def Set_Scale(self):
        self.Scale=1
        if self.Machine_Size[0]>0 and self.Machine_Size[1]>0:
            FRect=self.DRui.frame_RTD_Images.frameRect()
            FH=FRect.height()
            FW=FRect.width()
            S1=(FW/self.Machine_Size[0])
            S2=(FH/self.Machine_Size[1])
            self.Scale=min(S1,S2)
            #print('Scale->'+str(self.Scale))

    def Set_Machine_label(self):
        try:
            Geo=self.DRui.frame_RTD_Images.geometry()
            MGeo=self.DRui.label_RTD_Machine.geometry()
            x_F,y_F,W_F,H_F=Geo.getRect()            
            MGeo.setRect(0, 0, int(self.Machine_Size[0]*self.Scale), int(self.Machine_Size[1]*self.Scale))
            self.DRui.label_RTD_Machine.setGeometry(MGeo)
        except:
            pass
    
    def TL_to_BL(self,xtl,ytl,W,H,Htlbl):
        return xtl,Htlbl-ytl,W,H

    def BL_to_TL(self,xbl,ybl,W,H,Htlbl):
        return xbl,Htlbl+ybl,W,H    

    def Set_Canvas_label(self):        
        try:
            MGeo=self.DRui.label_RTD_Machine.geometry()
            CGeo=self.DRui.label_RTD_Canvas.geometry()
            x_M,y_M,W_M,H_M=MGeo.getRect() # top, left
            x_MO=int(self.Canvas_pos[0]*self.Scale)
            y_MO=int(self.Canvas_pos[1]*self.Scale)
            W_C=int(self.Canvas_Size[0]*self.Scale)
            H_C=int(self.Canvas_Size[1]*self.Scale)                
            pos=[x_M+x_MO,y_M+(H_M-(y_MO+H_C)),W_C,H_C]        
            CGeo.setRect(pos[0],pos[1],pos[2],pos[3])        
            self.DRui.label_RTD_Canvas.setGeometry(CGeo)    
        except:
            pass    

    def Set_Image_label(self):        
        try:
            #MGeo=self.DRui.label_RTD_Machine.geometry()
            CGeo=self.DRui.label_RTD_Canvas.geometry()
            IGeo=self.DRui.label_RTD_Image.geometry()
            x_C,y_C,W_C,H_C=CGeo.getRect() # top, left
            x_IO=int(self.Image_pos[0]*self.Scale)
            y_IO=int(self.Image_pos[1]*self.Scale)
            W_I=int(self.Image_Size[0]*self.Scale)
            H_I=int(self.Image_Size[1]*self.Scale)         
            pos=[x_C+x_IO,y_C+(H_C-(y_IO+H_I)),W_I,H_I]        
            IGeo.setRect(pos[0],pos[1],pos[2],pos[3])        
            self.DRui.label_RTD_Image.setGeometry(IGeo) 
        except:
            pass     

    def Set_Image_to_Image_label(self,im):
        self.im=im
        qim = ImageQt(im)
        self.the_pixmap=QtGui.QPixmap.fromImage(qim)        
        self.DRui.label_RTD_Image.setPixmap(self.the_pixmap.scaled(
                    self.DRui.label_RTD_Image.size(), QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation))       
        self.IsRTDim=True      
        self.Put_Frame()
    def Set_Machine_Point_label(self):         
        try:
            MGeo=self.DRui.label_RTD_Machine.geometry()
            MPGeo=self.DRui.label_RTD_Machine_Point.geometry()
            x_,y_,W_MP,H_MP=MPGeo.getRect() # top, left
            x_M,y_M,W_M,H_M=MGeo.getRect() # top, left
            x_MPO=int(self.Machine_pos[0]*self.Scale)
            y_MPO=int(self.Machine_pos[1]*self.Scale)            
            W_M=int(self.Machine_Size[0]*self.Scale)
            H_M=int(self.Machine_Size[1]*self.Scale)         
            pos=[x_M+x_MPO-int(W_MP/2),y_M+(H_M-(y_MPO+H_MP-int(H_MP/2))),W_MP,H_MP]        
            MPGeo.setRect(pos[0],pos[1],pos[2],pos[3])        
            self.DRui.label_RTD_Machine_Point.setGeometry(MPGeo) 
        except:
            pass  

