from PyQt6.QtWidgets import *
from PyQt6 import QtWidgets, QtGui, QtCore

class Dialogs(QWidget):
    def __init__(self):
        super().__init__()
        # self.options = QFileDialog.options()
        # self.options |= QFileDialog.Option.DontUseNativeDialog
        self.options = QFileDialog.Option.DontUseNativeDialog
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
            self.filters="All Files (*);;Yaml Files (*.yml);;Json Files (*.json)"
            self.selected_filter = "Yaml Files (*.yml)" 
        elif filter==4:
            self.filters="All Files (*);;Gcode Files (*.gcode);;Linux Gcode Files (*.ngc);;Action Files (*.acode)"
            self.selected_filter = "Gcode Files (*.gcode)"   
        elif filter==5:
            self.filters="All Files (*);;Batton Configuration Files (*.btncfg)"
            self.selected_filter = "Batton Configuration Files (*.btncfg)"
        else:
            self.filters="All Files (*)"
            self.selected_filter = "All Files (*)"    

    def openFileNameDialog(self,filter=0):
        '''
        filters:
        0->Gcode Files (*.gcode *.ncg)
        1->Images (*.png *.xpm *.jpg *.bmp)
        2->Text Files (*.txt)
        3->Configuration Files (*.yml *.json)
        4->Gcode and Action Files (*.gcode *.ncg *.acode) 
        5->Batton Configuration files (*.btncfg)
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
        0->Gcode Files (*.gcode *.ncg)
        1->Images (*.png *.xpm *.jpg *.bmp)
        2->Text Files (*.txt)
        3->Configuration Files (*.yml *.json)
        4->Gcode and Action Files (*.gcode *.ncg *.acode) 
        5->Batton Configuration files (*.btncfg)
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
        0->Gcode Files (*.gcode *.ncg)
        1->Images (*.png *.xpm *.jpg *.bmp)
        2->Text Files (*.txt)
        3->Configuration Files (*.yml *.json)
        4->Gcode and Action Files (*.gcode *.ncg *.acode) 
        5->Batton Configuration files (*.btncfg)
        else all Files
        '''    
        self.get_filter(filter)         
        fileName, _ = QFileDialog.getSaveFileName(self, "Save File dialog ", self.dir, self.filters, self.selected_filter, options=self.options)
        if fileName:
            return fileName
        else:
            return None



class DeleteConfirmDialog(QtWidgets.QDialog):
    def __init__(self, name, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Delete Interface")
        self.setModal(True)

        # Main layout
        layout = QtWidgets.QVBoxLayout(self)

        # Horizontal layout for icon + text
        top_layout = QtWidgets.QHBoxLayout()

        # Warning icon (same as QMessageBox)
        icon_label = QtWidgets.QLabel()
        icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning)
        icon_label.setPixmap(icon.pixmap(48, 48))
        top_layout.addWidget(icon_label)

        # Message text
        text_label = QtWidgets.QLabel(
            f"To delete '<b>{name}</b>', type <b>DELETE</b> below:"
        )
        text_label.setWordWrap(True)
        top_layout.addWidget(text_label)

        layout.addLayout(top_layout)

        # Input field
        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setPlaceholderText("Type DELETE to confirm")
        self.line_edit.setMinimumWidth(300)
        self.line_edit.setMinimumHeight(28)
        layout.addWidget(self.line_edit)

        # OK / Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def confirmed(self):
        """Return True only if user typed DELETE."""
        return self.line_edit.text().strip().upper() == "DELETE"

