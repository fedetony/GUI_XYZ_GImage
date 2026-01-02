from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import *

import GuiXYZ_LSTD

from class_LogHandler import LM
log = LM.get_logger("LSTD")

class LayerSelectionToolDialog(QWidget, GuiXYZ_LSTD.Ui_Dialog_LSTD):
    set_clicked = QtCore.pyqtSignal(list)

    def __init__(self, num_layers, selected_layers, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.Number_of_Layers = max(1, num_layers)
        self.Selected_Layers = selected_layers or [-1]

        self.Dialog_LSTD = QtWidgets.QDialog()
        self.DSLui = GuiXYZ_LSTD.Ui_Dialog_LSTD()
        self.DSLui.setupUi(self.Dialog_LSTD)

        # Store widgets instead of searching by name
        self.checkboxes = []
        self.labels = []

        self._build_layer_widgets()
        self.Set_Checkboxeswith_Selected_Layers(self.Selected_Layers)

        self.DSLui.pushButton_LSTD_Set_Preview.clicked.connect(self.PB_LSTD_Set_Preview)
        self.Dialog_LSTD.show()

    # ---------------------------------------------------------
    # Build UI
    # ---------------------------------------------------------
    def _build_layer_widgets(self):
        layout = self.DSLui.gridLayout

        for i in range(self.Number_of_Layers):
            # Checkbox
            cb = QtWidgets.QCheckBox(f"Layer {i}")
            cb.clicked.connect(self.Get_Selected_Layers_From_checkbox)
            layout.addWidget(cb, i, 0)
            self.checkboxes.append(cb)

            # Label
            lbl = QtWidgets.QLabel(str(i))
            lbl.setStyleSheet("border: 1px solid black;")
            layout.addWidget(lbl, i, 1)
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
    def Clear_allcheckbox(self, val=False):
        for cb in self.checkboxes:
            cb.setChecked(val)

    def Get_Selected_Layers_From_checkbox(self):
        selected = [i for i, cb in enumerate(self.checkboxes) if cb.isChecked()]

        if len(selected) == self.Number_of_Layers:
            selected = [-1]

        self.Selected_Layers = selected

    def Set_Checkboxeswith_Selected_Layers(self, S_L):
        if -1 in S_L:
            self.Clear_allcheckbox(True)
            return

        self.Clear_allcheckbox(False)
        for i in S_L:
            if 0 <= i < self.Number_of_Layers:
                self.checkboxes[i].setChecked(True)

    # ---------------------------------------------------------
    # Dialog actions
    # ---------------------------------------------------------
    def PB_LSTD_Set_Preview(self):
        self.set_clicked.emit(self.Selected_Layers)

    def accept(self):
        self.Get_Selected_Layers_From_checkbox()
        return self.Selected_Layers

    # ---------------------------------------------------------
    # Layer range filtering
    # ---------------------------------------------------------
    @staticmethod
    def Get_list_of_Selected_Layers(selected_layers, pimg_val_range):
        minv, maxv = pimg_val_range[1], pimg_val_range[2]

        if not selected_layers or -1 in selected_layers:
            return list(range(minv, maxv + 1))

        return [s for s in selected_layers if minv <= s <= maxv]

