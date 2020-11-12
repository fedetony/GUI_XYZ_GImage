from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
#from PIL.ImageQt import ImageQt
import re
import io #TextIOWrapper
import logging
import GuiXYZ_LSTD

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
ahandler=logging.StreamHandler()
ahandler.setLevel(logging.INFO)
ahandler.setFormatter(formatter)
log.addHandler(ahandler)

class LayerSelectionToolDialog(QWidget,GuiXYZ_LSTD.Ui_Dialog_LSTD):
    set_clicked= QtCore.pyqtSignal(list)
    #def __init__(self,NumLayers,Selected_Layers,parent=None):    
    #    super().__init__(parent)
    def __init__(self,NumLayers,Selected_Layers, *args, **kwargs):        
        super(LayerSelectionToolDialog, self).__init__(*args, **kwargs)    
        self.__name__="LSTD"
        self.Number_of_Layers=NumLayers
        if self.Number_of_Layers<1:
            self.Number_of_Layers=1
        self.Selected_Layers=Selected_Layers        
        if self.Selected_Layers is None or len(self.Selected_Layers)<=0:
            self.Selected_Layers=[-1]
        self.Layer_range=[0,0,self.Number_of_Layers]    
        self.openLayerSelectToolDialog()
        self.Set_Checkboxeswith_Selected_Layers(self.Selected_Layers)   
    
    def quit(self):
        self.Dialog_LSTD.close()

    def Assign_Colors_to_Labels(self,Color_Palette):

        for iii in range(self.Number_of_Layers): 
            #CBname="checkBox_LSTD"+'_CB_L'+str(iii)
            Color=(255,255,255)
            Lname="label_LSTD"+'_L_L'+str(iii)                         
            try:
                label = self.Dialog_LSTD.findChild(QtWidgets.QLabel, Lname)                  
                txt="("+str(255)+","+str(255)+","+str(255)+")"    
                label.setText(txt)    
                label.setStyleSheet("background-color:rgb"+txt+"; border: 1px solid black;")
                label.adjustSize()
                if Color_Palette is not None:
                    for ttt in Color_Palette:# (p,c,r,g,b)) palette,count,rgb tuple
                        (p,c,r,g,b)=ttt
                        if p==iii:
                            Color=(r,g,b)
                            txt="("+str(r)+","+str(g)+","+str(b)+")"    
                            label.setText(txt)    
                            label.setStyleSheet("background-color:rgb"+txt+"; border: 1px solid black;")                        
                            break
               

            except Exception as e:
                log.error(e)
                log.info("Label Error!"+Lname)
                pass    


    def Clear_allcheckbox(self,val=False):
        for iii in range(self.Number_of_Layers): 
            CBname="checkBox_LSTD"+'_CB_L'+str(iii)
            #Lname="label_LSTD"+'_L_L'+str(iii)                         
            try:
                checkbox = self.Dialog_LSTD.findChild(QtWidgets.QCheckBox, CBname)                  
                checkbox.setChecked(val)
            except Exception as e:
                log.error(e)
                log.info("Check Box Error!"+CBname)
                pass    
    
    def Get_Selected_Layers_From_checkbox(self):
        S_L=[]
        sss=0
        for iii in range(self.Number_of_Layers): 
            CBname="checkBox_LSTD"+'_CB_L'+str(iii)
            #Lname="label_LSTD"+'_L_L'+str(iii)                         
            try:
                checkbox = self.Dialog_LSTD.findChild(QtWidgets.QCheckBox, CBname)                  
                if checkbox.isChecked()==True:
                    S_L.append(iii)
                    sss=sss+1
            except Exception as e:
                log.error(e)
                log.info("Check Box Error!"+CBname)
                pass    
        if sss==self.Number_of_Layers:
            S_L=[-1]    
        self.Selected_Layers = S_L    

    def Set_Checkboxeswith_Selected_Layers(self,S_L):
        Isall=False
        self.Clear_allcheckbox()
        for iii in S_L:
            CBname="checkBox_LSTD"+'_CB_L'+str(iii)
            #Lname="label_LSTD"+'_L_L'+str(iii)
            if iii==-1:
                Isall=True
                break                       
            checkbox = self.Dialog_LSTD.findChild(QtWidgets.QCheckBox, CBname)
            checkbox.setChecked(True)
        if Isall==True:
            self.Clear_allcheckbox(True)


    def set_objects_fromNum_layers(self,Num_Layers):
        
        Obj_Names=[]
        for iii in range(Num_Layers):
            Obj_Names.append('_CB_L'+str(iii))
            Obj_Names.append('_L_L'+str(iii))
        Obj_Text=[]
        for iii in range(Num_Layers):
            Obj_Text.append('Layer'+str(iii))
            Obj_Text.append(str(iii))
        
        obj_positions = [(iii, jjj) for iii in range(Num_Layers) for jjj in range(2)]

        L_N=0
        for position, name, txt in zip(obj_positions, Obj_Names, Obj_Text):
            if name == '':
                continue
            if '_CB_L' in name:                
                checkbox=QtWidgets.QCheckBox(self.DSLui.frame)
                checkbox.setObjectName("checkBox_LSTD"+name)  
                checkbox.setText(txt)                
                checkbox.clicked.connect(self.Get_Selected_Layers_From_checkbox)
                self.DSLui.gridLayout.addWidget(checkbox, *position)              


            else:
                label=QtWidgets.QLabel(self.DSLui.frame)
                label.setObjectName("label_LSTD"+name)
                label.setText(txt)
                self.DSLui.gridLayout.addWidget(label, *position)
                L_N=L_N+1    
           
    def openLayerSelectToolDialog(self):
        self.Dialog_LSTD = QtWidgets.QDialog()
        self.DSLui = GuiXYZ_LSTD.Ui_Dialog_LSTD()
        self.DSLui.setupUi(self.Dialog_LSTD)
        self.set_objects_fromNum_layers(self.Number_of_Layers)        
        self.Dialog_LSTD.show()             
        self.DSLui.pushButton_LSTD_Set_Preview.clicked.connect(self.PB_LSTD_Set_Preview)
            
    def PB_LSTD_Set_Preview(self):            
        #print('clicked')
        self.set_clicked.emit(self.Selected_Layers)

    def accept(self):
        #print('accepted')
        self.Get_Selected_Layers_From_checkbox()
        return self.Selected_Layers   

    def Get_list_of_Selected_Layers(self,Selected_Layers,pimg_val_range):
        listofSellay=[]
        for sss in Selected_Layers:
            if sss==-1:
                listofSellay=[]
                for iii in range(pimg_val_range[1],pimg_val_range[2]+1):
                    listofSellay.append(iii)
                break
            if sss<=pimg_val_range[2] and sss>=pimg_val_range[1]:
                listofSellay.append(sss)
        if len(Selected_Layers)==0:    
            listofSellay=[]
            for iii in range(pimg_val_range[1],pimg_val_range[2]+1):
                listofSellay.append(iii)
        return listofSellay

