from PyQt5.QtWidgets import *

class Dialogs(QWidget):
    def __init__(self):
        super().__init__()
        self.options = QFileDialog.Options()
        self.options |= QFileDialog.DontUseNativeDialog
        self.dir=""
    def get_filter(self,filter):
        if filter==0:
            self.filters="All Files (*);;Gcode Files (*.gcode);;Linux Gcode Files (*.ngc)"
            self.selected_filter = "Gcode Files (*.gcode)"
        elif filter==1:
            self.filters="All Files (*);;Images (*.png *.xpm *.jpg *.bmp)"
            self.selected_filter = "Images (*.png *.xpm *.jpg *.bmp)"
        elif filter==2:
            self.filters="All Files (*);;Text Files (*.txt)"
            self.selected_filter = "Text Files (*.txt)"
        elif filter==3:
            self.filters="All Files (*);;Configuration Files (*.cccfg *.iccfg *.rccfg);;Interface Files (*.iccfg);;Read Files (*.rccfg);;Command Files (*.cccfg)"
            self.selected_filter = "Configuration Files (*.cccfg *.iccfg *.rccfg)"    
        else:
            self.filters="All Files (*)"
            self.selected_filter = "All Files (*)"    

    def openFileNameDialog(self,filter=0):
        '''
        filters:
        0->Gcode Files (*.gcode)
        1->Images (*.png *.xpm *.jpg *.bmp)
        2->Text Files (*.txt)
        3->Configuration Files (*.config)
        else all Files
        '''        
        #dir = self.sourceDir
        self.get_filter(filter)        
        
        fileObj = QFileDialog.getOpenFileName(self, "Open File dialog ", self.dir, self.filters, self.selected_filter, options=self.options)
        fileName, _ = fileObj
        if fileName:
            return fileName
        else:
            return None    
    
    def openFileNamesDialog(self,filter=0):
        '''
        filters:
        0->Gcode Files (*.gcode)
        1->Images (*.png *.xpm *.jpg *.bmp)
        2->Text Files (*.txt)
        3->Configuration Files (*.config)
        else all Files
        '''
        self.get_filter(filter) 
        files, _ = QFileDialog.getOpenFileNames(self, "Open File Names Dialog", self.dir, self.filters, self.selected_filter, options=self.options)
        if files:
            return files
        else:
            return None    
    
    def saveFileDialog(self,filter=0): 
        '''
        filters:
        0->Gcode Files (*.gcode)
        1->Images (*.png *.xpm *.jpg *.bmp)
        2->Text Files (*.txt)
        3->Configuration Files (*.config)
        else all Files
        '''    
        self.get_filter(filter)         
        fileName, _ = QFileDialog.getSaveFileName(self, "Save File dialog ", self.dir, self.filters, self.selected_filter, options=self.options)
        if fileName:
            return fileName
        else:
            return None
