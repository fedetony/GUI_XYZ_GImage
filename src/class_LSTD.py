from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import *

import GuiXYZ_LSTD

from class_LogHandler import LM
log = LM.get_logger("LSTD")

class LayerSelectionToolDialog(QWidget, GuiXYZ_LSTD.Ui_Dialog_LSTD):
    # process,num_colors,color_selection
    set_preview = QtCore.pyqtSignal(list,str,int,str)
    accepted = QtCore.pyqtSignal(list,str,int,str)
    # canceled = QtCore.pyqtSignal(list)
    
    set_color = QtCore.pyqtSignal(str)

    def __init__(self, num_layers, selected_layers, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actual_color_process='RGB'
        self.color_palette=None
        self.number_of_layers = max(1, num_layers)
        self.selected_layers = selected_layers or [-1]
        self.original_selected_layers=self.selected_layers

        self.Dialog_LSTD = QtWidgets.QDialog()
        self.DSLui = GuiXYZ_LSTD.Ui_Dialog_LSTD()
        self.DSLui.setupUi(self.Dialog_LSTD)

        # Store widgets instead of searching by name
        self.checkboxes = []
        self.labels = []

        self._build_layer_widgets()
        self.set_checkboxes_with_selected_layers(self.selected_layers)

        self.DSLui.pushButton_LSTD_Set_Preview.clicked.connect(self.PB_LSTD_Set_Preview)
        self.DSLui.checkBox_LSTD_checkall.clicked.connect(self.check_all_checkboxes)
        self.Dialog_LSTD.show()

    # ---------------------------------------------------------
    # Build UI
    # ---------------------------------------------------------
    def _build_layer_widgets(self):
        layout = self.DSLui.gridLayout

        for iii in range(self.number_of_layers):
            # Checkbox
            cb = QtWidgets.QCheckBox(f"Layer {iii}")
            cb.clicked.connect(self.get_selected_layers_from_checkbox)
            layout.addWidget(cb, iii, 0)
            self.checkboxes.append(cb)

            # Label
            lbl = QtWidgets.QLabel(str(iii))
            lbl.setStyleSheet("border: 1px solid black;")
            layout.addWidget(lbl, iii, 1)
            self.labels.append(lbl)

    # ---------------------------------------------------------
    # Color assignment
    # ---------------------------------------------------------
    def Assign_Colors_to_Labels(self, color_palette):
        if not color_palette:
            # No palette → set all labels to white
            for lbl in self.labels:
                lbl.setStyleSheet("background-color: rgb(255,255,255); border: 1px solid black;")
            return

        pval_to_rgb = {p: (r, g, b) for p, c, r, g, b in color_palette}

        for i, lbl in enumerate(self.labels):
            rgb = pval_to_rgb.get(i, (255, 255, 255))
            txt = f"({rgb[0]},{rgb[1]},{rgb[2]})"
            lbl.setText(txt)
            lbl.setStyleSheet(f"background-color: rgb{txt}; border: 1px solid black;")

    # ---------------------------------------------------------
    # Checkbox handling
    # ---------------------------------------------------------
    def check_all_checkboxes(self):
        val=self.DSLui.checkBox_LSTD_checkall.isChecked()
        self.clear_all_checkboxes(val)

    def clear_all_checkboxes(self, val=False):
        for cb in self.checkboxes:
            cb.setChecked(val)

    def get_selected_layers_from_checkbox(self):
        selected = [i for i, cb in enumerate(self.checkboxes) if cb.isChecked()]

        if len(selected) == self.number_of_layers:
            selected = [-1]

        self.selected_layers = selected

    def set_checkboxes_with_selected_layers(self, S_L):
        if -1 in S_L:
            self.clear_all_checkboxes(True)
            return

        self.clear_all_checkboxes(False)
        for i in S_L:
            if 0 <= i < self.number_of_layers:
                self.checkboxes[i].setChecked(True)

    # ---------------------------------------------------------
    # Combobox
    # ---------------------------------------------------------
    def Fill_comboBox_LSTD_Image_Process(self,color_selection_list,actual_color):
        self.DSLui.comboBox_LSTD_Image_Process.clear()
        self.DSLui.comboBox_LSTD_Image_Process.addItems(color_selection_list)
        self._set_combo_value(self.DSLui.comboBox_LSTD_Image_Process,actual_color)
        self.DSLui.comboBox_LSTD_Image_Process.currentIndexChanged.connect(self.color_process_changed)    

    def color_process_changed(self, value:str):
        self.actual_color_process=self.DSLui.comboBox_LSTD_Image_Process.currentText()

    def _set_combo_value(self,combo:QComboBox,value:str):
        """Helper to set value to combo"""
        index = combo.findText(value) 
        if index >= 0: 
            combo.setCurrentIndex(index)
    # ---------------------------------------------------------
    # Dialog actions
    # ---------------------------------------------------------
    def PB_LSTD_Set_Preview(self):
        # layers, process,num_colors,color_selection
        self.set_preview.emit(self.selected_layers,"descrete",self.number_of_layers,self.actual_color_process)

    def accept(self):
        self.get_selected_layers_from_checkbox()
        self.accepted.emit(self.selected_layers,"descrete",self.number_of_layers,self.actual_color_process)
        self.original_selected_layers=self.selected_layers
        return self.selected_layers

    # ---------------------------------------------------------
    # Layer range filtering
    # ---------------------------------------------------------
    @staticmethod
    def Get_list_of_selected_layers(selected_layers, pimg_val_range):
        minv, maxv = pimg_val_range[1], pimg_val_range[2]

        if not selected_layers or -1 in selected_layers:
            return list(range(minv, maxv + 1))

        return [s for s in selected_layers if minv <= s <= maxv]

