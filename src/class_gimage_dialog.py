#class_gmimage_dialog

from PyQt6 import QtCore, QtGui, QtWidgets, QtSvg, QtSvgWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtWidgets import  QWidget, QVBoxLayout, QApplication
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter

import logging
import os
import json
from copy import deepcopy
from pathlib import Path


import class_ST
import class_LogHandler
ap=class_LogHandler.get_appPath()
img_path=os.path.join(ap,"img")
config_path=os.path.join(ap,"config")
temp_path=os.path.join(ap,"temp")
gimage_path=os.path.join(ap,"gimage")

log = logging.getLogger("Gimage")
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(levelname)s] (%(name)s) %(message)s')
ahandler=logging.StreamHandler()
ahandler.setLevel(logging.INFO)
ahandler.setFormatter(formatter)
log.addHandler(ahandler)
    
class GimageGcodeGenerator(QtWidgets.QMainWindow):
    closed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        log.info("... Started")
        self.setWindowTitle("Gimage G-Code Generator")
        self.setMinimumSize(1200, 800)

        #Initialize Variables
        self.tm=None
        self.cm=None
        self.color_selection_list=['Black&White','Red','Green','Blue','RGB']

        # Main splitter
        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        # --- LEFT PANEL ---
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)

        # -------------------------
        # Toolbars
        # -------------------------

        self.gimage_image_toolbar = QtWidgets.QToolBar()
        self.gimage_image_toolbar.setIconSize(QtCore.QSize(36, 36))

        self.action_open_image = QtGui.QAction(QtGui.QIcon(":/img/Ahmadhania-Spherical-Select-text.128.png"), "Open Image", self)
        self.action_save_image = QtGui.QAction(QtGui.QIcon(":/img/Ahmadhania-Spherical-Save.128.png"), "Save Processed Image", self)
        self.gimage_image_toolbar.addAction(self.action_open_image)
        self.gimage_image_toolbar.addSeparator()
        self.gimage_image_toolbar.addAction(self.action_save_image)

        self.gimage_actual_interface_label=QtWidgets.QLabel("Actual Interface: ")
        
        self.gimage_config_toolbar = QtWidgets.QToolBar()
        self.gimage_config_toolbar.setIconSize(QtCore.QSize(24, 24))

        self.action_open = QtGui.QAction(QtGui.QIcon(":/img/open-file-icon.png"), "Open Session Config", self)
        self.action_save = QtGui.QAction(QtGui.QIcon(":/img/Save-as-icon.png"), "Save Session Config", self)
        self.action_refresh = QtGui.QAction(QtGui.QIcon(":/img/Actions-view-refresh-icon.png"), "Refresh", self)
        self.action_position_helper = QtGui.QAction(QtGui.QIcon(":/img/Ahmadhania-Spherical-Target.128.png"), "Position Helper", self)
        self.action_layer_helper = QtGui.QAction(QtGui.QIcon(":/img/Ahmadhania-Spherical-Restore.128.png"), "Layer Helper", self)
        
        self.action_fit = QtGui.QAction(QtGui.QIcon(":/img/move-icon.png"), "Fit", self)

        self.gimage_config_toolbar.addAction(self.action_open)
        self.gimage_config_toolbar.addAction(self.action_save)
        self.gimage_config_toolbar.addSeparator()
        self.gimage_config_toolbar.addAction(self.action_refresh)
        self.gimage_config_toolbar.addAction(self.action_position_helper)
        self.gimage_config_toolbar.addAction(self.action_layer_helper)
        # -------------------------
        # Selectors
        # -------------------------
        selector_layout = QtWidgets.QVBoxLayout()
        
        machine_layout, self.machine_combo = self._make_icon_label_combo_row(
            "Machine:", ":/img/Modify-icon.png"
        )

        tool_layout, self.tool_combo = self._make_icon_label_combo_row(
            "Tool:", ":/img/Ahmadhania-Spherical-Paper-clip.128.png"
        )

        technique_layout, self.technique_combo = self._make_icon_label_combo_row(
            "Technique:", ":/img/Ahmadhania-Spherical-Write.128.png"
        )

        color_layout, self.color_combo = self._make_icon_label_combo_row(
            "Color:", ":/img/Ahmadhania-Spherical-Umbrella.128.png"
        )

        selector_layout.addLayout(machine_layout)
        selector_layout.addLayout(tool_layout)
        selector_layout.addLayout(technique_layout)
        selector_layout.addLayout(color_layout)
        # -------------------------
        # TreeWidget
        # -------------------------
        self.tree =QTreeWidget(self)
        # Progress_bar
        self.gimage_progressbar=QProgressBar()
        self.gimage_progressbar.setRange(0, 100)
        # -------------------------
        # Left layout
        # -------------------------
        left_layout.addWidget(self.gimage_image_toolbar)
        left_layout.addWidget(self.gimage_actual_interface_label)
        left_layout.addWidget(self.gimage_config_toolbar)
        left_layout.addLayout(selector_layout)
        left_layout.addWidget(self.tree)
        left_layout.addWidget(self.gimage_progressbar)
        # -------------------------
        # Splitter
        # -------------------------
        splitter.addWidget(left_panel)
        splitter.setStretchFactor(0, 0)

        # --- RIGHT PANEL ---
        right_splitter = QtWidgets.QSplitter()
        right_splitter.setOrientation(QtCore.Qt.Orientation.Vertical)

        # Original image preview
        self.original_view = QtWidgets.QGraphicsView()
        self.original_scene = QtWidgets.QGraphicsScene()
        self.original_view.setScene(self.original_scene)

        # Processed image preview
        self.processed_view = QtWidgets.QGraphicsView()
        self.processed_scene = QtWidgets.QGraphicsScene()
        self.processed_view.setScene(self.processed_scene)

        right_splitter.addWidget(self.original_view)
        right_splitter.addWidget(self.processed_view)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 1)

        splitter.addWidget(right_splitter)
        splitter.setStretchFactor(1, 1)
        # Set Configuration
        self.setup_configuration()
        self.fill_combos()

    def _make_icon_label_combo_row(self, text, icon_path):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        # Icon
        icon_label = QtWidgets.QLabel()
        icon_label.setPixmap(QtGui.QIcon(icon_path).pixmap(24, 24))
        # Text label
        text_label = QtWidgets.QLabel(text)
        # Combo
        combo = QtWidgets.QComboBox()
        combo.setMinimumWidth(120)
        # Group icon + label so they stay together
        left_group = QtWidgets.QWidget()
        left_layout = QtWidgets.QHBoxLayout(left_group)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        left_layout.addWidget(icon_label)
        left_layout.addWidget(text_label)
        # Add to main row
        layout.addWidget(left_group, 0)   # fixed
        layout.addWidget(combo, 1)        # expands
        return layout, combo

    def setup_configuration(self):
        try:
            self.cm = ConfigManager(gimage_path)
        except ValueError as eee:
            log.error(eee)
            return
        log.debug(self.cm.machine) 
        log.debug(self.cm.tool) 
        log.debug(self.cm.technique) 
        log.debug(self.cm.image)
        log.info("Success machine, tools, technique and session configuration set!")
        self.tm=TreeManager(self.tree,self.cm)
        self.tm.item_edited.connect(self.on_tree_item_edited)
        self.tm.refresh()
    
    def fill_combos(self):
        if self.tm:
            self.machine_combo.addItems(self.cm.machine_list)
            self.tool_combo.addItems(self.cm.tool_list)
            self.technique_combo.addItems(self.cm.technique_list)
            self.color_combo.addItems(self.color_selection_list)

    @QtCore.pyqtSlot(str, str, str, str)
    def on_tree_item_edited(self, section, key, old_value, new_value):
        # Decide which dialog to open
        # if key == "layers":
        #     self._open_layer_dialog(section, key, old_value)

        # elif key in ("position", "size", "offset"):
        #     self._open_coordinate_dialog(section, key, old_value)

        # elif key == "color":
        #     self._open_color_dialog(section, key, old_value)

        # else:
        #     # default: accept new_value directly
        #     self.config_manager.session[section][key] = new_value
        pass

    # def on_resolution_changed(self, value: float):
    #     self.cm.set_output_param("output", "resolution", value=float(value))
    
    def save_gimage_config(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Gimage Config", "", "JSON Files (*.json)"
        )
        if path:
            self.cm.save_session(path)

    def load_gimage_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Gimage Config", "", "JSON Files (*.json)"
        )
        if path:
            self.cm.load_session(path)
            self.refresh_gui_from_config()

    def refresh_gui_from_config(self):
        # placeholder for refresh
        pass

    def show_original_image(self, qimage):
        self.original_scene.clear()
        pix = QtGui.QPixmap.fromImage(qimage)
        self.original_scene.addPixmap(pix)
        self.original_view.fitInView(self.original_scene.itemsBoundingRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
    
    def draw_vector_paths(self, shapes):
        self.processed_scene.clear()

        pen = QtGui.QPen(QtGui.QColor("red"))
        pen.setWidth(1)

        for shape in shapes:
            for sub in shape:
                path = QtGui.QPainterPath()
                first = True
                for edge in sub:
                    (x, y) = edge[0]
                    if first:
                        path.moveTo(x, y)
                        first = False
                    else:
                        path.lineTo(x, y)
                self.processed_scene.addPath(path, pen)
    
    def write_svg(self, filename, color_joined_pieces, width, height):
        with open(filename, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" '
                    f'width="{width}" height="{height}" '
                    f'viewBox="0 0 {width} {height}">\n')

            for color, shapes in color_joined_pieces.items():
                r, g, b, a = color
                fill = f"rgb({r},{g},{b})"
                opacity = a / 255.0

                for shape in shapes:
                    for sub in shape:
                        if not sub:
                            continue

                        # Build path
                        parts = []
                        x0, y0 = sub[0][0]
                        parts.append(f"M {x0} {y0}")
                        for edge in sub:
                            x, y = edge[1]
                            parts.append(f"L {x} {y}")
                        parts.append("Z")

                        d = " ".join(parts)

                        f.write(f'  <path d="{d}" fill="{fill}" fill-opacity="{opacity}" '
                                f'stroke="none"/>\n')

            f.write('</svg>\n')
        
    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class ConfigManager:
    def __init__(self, base_folder=gimage_path,session_filepath=None):
        self.base_folder = Path(base_folder)
        self.is_machine_profile=False
        self.is_tool_profile=False
        self.is_teqnique_profile=False
        self.is_session_profile=False
        self.session_filepath=session_filepath
        # Load all profiles
        self.load_all_profiles()
        # Validate and merge
        self._validate_session()

    def load_all_profiles(self):
        # Load all profiles
        try:
            self.machine_profiles = self._load_json("machine_profiles.json")
            self.is_machine_profile=True
        except FileNotFoundError as eee:
            log.error(eee)
        try:
            self.tool_profiles = self._load_json("tool_profiles.json")
            self.is_tool_profile=True
        except FileNotFoundError as eee:
            log.error(eee)
        try:    
            self.technique_profiles = self._load_json("technique_profiles.json")
            self.is_teqnique_profile=True
        except FileNotFoundError as eee:
            log.error(eee)
        # Load default session config
        try:
            if self.session_filepath is None:
                self.session = self._load_json("default_session_config.json")
            else:
                self.session = self._load_json(None,self.session_filepath)
            self.is_session_profile=True
        except FileNotFoundError as eee:
            log.error(eee)

    # -------------------------
    # JSON LOADING
    # -------------------------

    def _load_json(self, filename, filepath=None):
        if filepath is None:
            fnpath = Path(os.path.join(self.base_folder,filename))
        else:
            fnpath = Path(filepath)
        if not os.path.exists(fnpath):
            raise FileNotFoundError(f"Missing config file: {fnpath}")
        with fnpath.open("r", encoding="utf-8") as f:
            return json.load(f)

    # -------------------------
    # SESSION VALIDATION
    # -------------------------
    def _are_all_profiles(self):
        return self.is_machine_profile and self.is_session_profile and self.is_teqnique_profile and self.is_tool_profile
    
    def _validate_session(self):
        if not self._are_all_profiles():
            raise ValueError(f"Missing one or more profiles!")  
        
        machine = self.session["machine"]
        tool = self.session["tool"]
        technique = self.session["technique"]

        if machine not in self.machine_profiles:
            raise ValueError(f"Unknown machine '{machine}'")

        if tool not in self.tool_profiles:
            raise ValueError(f"Unknown tool '{tool}'")

        if technique not in self.technique_profiles:
            raise ValueError(f"Unknown technique '{technique}'")

        # Check tool compatibility
        compatible = self.technique_profiles[technique]["compatible_tools"]
        if tool not in compatible:
            raise ValueError(
                f"Technique '{technique}' is not compatible with tool '{tool}'"
            )

    def update_value(self, section, key, new_value):
        target = None
        if section == "machine":
            target = self.machine
        elif section == "tool":
            target = self.tool
        elif section == "technique":
            target = self.technique
        elif section == "image":
            target = self.image
        elif section == "output":
            target = self.session
        else:
            raise KeyError(f"Unknown section: {section}")

        entry = target[key]

        if isinstance(entry, dict) and "value" in entry:
            entry["value"] = new_value
        else:
            target[key] = new_value

    # -------------------------
    # ACCESSORS
    # -------------------------
    @property
    def session_dict(self):
        return {
            "machine": self.machine,
            "tool": self.tool,
            "technique": self.technique,
            "image": self.image,
            "output": self.session
        }

    @property
    def machine_list(self):
        return list(self.machine_profiles.keys())
    
    @property
    def tool_list(self):
        return list(self.tool_profiles.keys())
    
    @property
    def technique_list(self):
        return list(self.technique_profiles.keys())

    @property
    def machine(self):
        return self.machine_profiles[self.session["machine"]]

    @property
    def tool(self):
        return self.tool_profiles[self.session["tool"]]

    @property
    def technique(self):
        return self.technique_profiles[self.session["technique"]]

    @property
    def image(self):
        return self.session["image"]

    @property
    def output(self):
        return self.session["output"]

    # -------------------------
    # SESSION SAVE/LOAD
    # -------------------------

    def save_session(self, filepath):
        path = Path(filepath)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.session, f, indent=4, ensure_ascii=False)
        self.session_filepath=path

    def load_session(self, filepath):
        path = Path(filepath)
        old_session=self.session_filepath
        try:
            with path.open("r", encoding="utf-8") as f:
                self.session = json.load(f)
                self.session_filepath=path
                self._validate_session()
        except Exception as eee:
            log.error(f"Invalid session: {eee}")
            self.session_filepath=old_session

    # -------------------------
    # MODIFY SESSION
    # -------------------------

    def set_machine(self, name):
        if name not in self.machine_profiles:
            raise ValueError(f"Unknown machine '{name}'")
        self.session["machine"] = name
        self._validate_session()

    def set_tool(self, name):
        if name not in self.tool_profiles:
            raise ValueError(f"Unknown tool '{name}'")
        self.session["tool"] = name
        self._validate_session()

    def set_technique(self, name):
        if name not in self.technique_profiles:
            raise ValueError(f"Unknown technique '{name}'")
        self.session["technique"] = name
        self._validate_session()

    def set_image_param(self, key, value):
        self.session["image"][key] = value

    def set_output_param(self, key, value):
        self.session["output"][key] = value


class SvgViewer(QWidget):
    def __init__(self):
        """Usage viewer = SvgViewer()
            viewer.load_svg("output.svg")
            viewer.show()
            """
        super().__init__()
        layout = QVBoxLayout(self)
        self.svg = QSvgWidget()
        layout.addWidget(self.svg)

    def load_svg(self, filename):
        self.svg.load(filename)



class SvgGraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHints(self.renderHints() | 
                            QPainter.RenderHint.Antialiasing |
                            QPainter.RenderHint.SmoothPixmapTransform)

    def load_svg(self, filename):
        self.scene.clear()
        item = QGraphicsSvgItem(filename)
        self.scene.addItem(item)
        self.fitInView(item.boundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    
class TreeManager(QWidget):
    item_edited = QtCore.pyqtSignal(str,str,str,str)
    def __init__(self, tree:QTreeWidget,config_manager:ConfigManager):
        super().__init__() 
        self.tree=tree
        self.config_manager=config_manager
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Key", "Value", "Unit", "Info"])
        self._read_only_keys=[]
        self._hidden_keys=[]
        self._disabled_keys=[]

        header = self.tree.header()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)  # Key
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)  # Value
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)  # Unit
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)           # Info


    def set_read_only(self,read_only_key_list):
        if isinstance(read_only_key_list,list):
            self._read_only_keys=[]
        else:
            log.error("Read only items must be a list!")
    
    def set_hidden(self,hide_key_list):
        if isinstance(hide_key_list,list):
            self._hidden_keys=[]
        else:
            log.error("Hide items must be a list!")
    
    def set_disabled(self,disabled_key_list):
        if isinstance(disabled_key_list,list):
            self._disabled_keys=[]
        else:
            log.error("Hide items must be a list!")
    

    def item_changed(self,section_name,section_item,old_section_data,new_section_data):
        self.item_edited.emit(section_name,section_item,str(old_section_data),str(new_section_data))

    def refresh(self):
        """Rebuild the tree from the current config."""
        self.session_dict=self.config_manager.session_dict
        self.build_config_tree(self.session_dict)
        
    def build_config_tree(self, config_dict:dict):
        """Build the configuration tree from a dictionary."""
        self.tree.clear()
        for section_name, section_data in config_dict.items():
            section_item = QTreeWidgetItem([section_name])
            section_item.setFlags(section_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tree.addTopLevelItem(section_item)
            if isinstance(section_data,dict):
                for key, value in section_data.items():
                    # 1. Skip hidden keys
                    if key in self._hidden_keys:
                        continue
                    child = QTreeWidgetItem([key, "", "", ""])
                    section_item.addChild(child)
                    # 2. Gray out read-only keys
                    if key in self._read_only_keys:
                        child.setFlags(child.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                    # 3. Add editor widget
                    if isinstance(value, dict):
                        if "value" in value:
                            self._add_editor_widget(child, value["value"])
                        if "unit" in value:
                            self._add_editor_unit(child, value["unit"])
                        if "info" in value:
                            self._add_editor_info(child, value["info"])
                    else:
                        self._add_editor_widget(child, value)
                    # 4. Disable editor widget if needed
                    if key in self._disabled_keys:
                        editor = self.tree.itemWidget(child, 1)
                        if editor:
                            editor.setDisabled(True)

    def _add_editor_unit(self, item, value):
        w = QLabel(str(value))  
        self.tree.setItemWidget(item, 2, w)
    
    def _add_editor_info(self, item, value):
        w = QLabel(str(value))  
        self.tree.setItemWidget(item, 3, w)

    def _add_editor_widget(self, item, value):
        if isinstance(value, bool):
            w = QCheckBox()
            w.setChecked(value)
            w.stateChanged.connect(lambda _: self._update_value(item, w.isChecked()))

        elif isinstance(value, int):
            w = QSpinBox()
            w.setRange(-999999, 999999)
            w.setValue(value)
            w.valueChanged.connect(lambda v: self._update_value(item, v))
        elif isinstance(value, float):
            w = QDoubleSpinBox()
            w.setRange(-999999.0, 999999.0)
            w.setDecimals(4)
            w.setValue(value)
            w.valueChanged.connect(lambda v: self._update_value(item, v))
        elif isinstance(value, str):
            w = QLineEdit(value)
            w.textChanged.connect(lambda v: self._update_value(item, v))
        elif isinstance(value, list):
            # vector editor
            try:
                w = self._make_vector_editor(item, value)
            except (ValueError,TypeError):
                new_value="["+' '.join(value)+"]"
                w = QLineEdit(new_value)
                w.textChanged.connect(lambda v: self._update_value(item, v))
        else:
            w = QLabel(str(value))  # fallback
        # key = item.text(0)  
        # if key in self._disabled_keys: 
        #     w.setDisabled(True)
        # Add to column 1 -> Value
        self.tree.setItemWidget(item, 1, w)
        
    def _make_vector_editor(self, item, values):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0,0,0,0)

        spinboxes = []
        for v in values:
            sb = QDoubleSpinBox()
            sb.setRange(-999999, 999999)
            sb.setValue(float(v))
            sb.valueChanged.connect(lambda _: self._update_vector(item, spinboxes))
            layout.addWidget(sb)
            spinboxes.append(sb)

        return widget

    def _update_value(self, item, new_value):
        section = item.parent().text(0)
        key = item.text(0)

        # read old value
        entry = self.config_manager.session_dict[section][key]
        old_value = entry["value"] if isinstance(entry, dict) else entry

        # update real config
        self.config_manager.update_value(section, key, new_value)

        # notify
        self.item_changed(section, key, old_value, new_value)

    def _update_vector(self, item, spinboxes):
        section = item.parent().text(0)
        key = item.text(0)

        values = [sb.value() for sb in spinboxes]

        entry = self.config_manager.session_dict[section][key]
        old_value = entry["value"] if isinstance(entry, dict) else entry

        self.config_manager.update_value(section, key, values)

        self.item_changed(section, key, old_value, values)

    def _disable_key(self):
        child = QTreeWidgetItem([key, "", "", ""])
        if key in self._read_only_keys:
            child.setFlags(child.flags() & ~Qt.ItemFlag.ItemIsEnabled)




    
    # def _set_validators():
    #     validator = Qt.QRegExpValidator(QRegExp("[A-Za-z0-9_]+"))
    #     lineedit.setValidator(validator)



