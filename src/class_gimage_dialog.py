#class_gmimage_dialog
from PIL import Image, ImageFilter  # imports the library
from PIL.ImageQt import ImageQt

from PyQt6 import QtCore, QtGui, QtWidgets, QtSvg, QtSvgWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtWidgets import  QWidget, QVBoxLayout, QApplication
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtGui import QStandardItemModel, QStandardItem

import logging
import threading
import os
import json
from copy import deepcopy
from pathlib import Path
import numpy as np
import resources_rc


import class_ST
import class_File_Dialogs
from class_LogHandler import get_appPath, LM
from class_treeview_functions import TypedItemDelegate, TreeviewFunctions, USER_ROLE
from class_struct_tracker import TreeStructTracker
from class_struct_conditioner import ConditionEngine
from class_LSTD import LayerSelectionToolDialog
from thread_gimage_plugin_handler import GImagePluginHandler
from class_CH import Command_Handler

ap=get_appPath()
img_path=os.path.join(ap,"img")
config_path=os.path.join(ap,"config")
temp_path=os.path.join(ap,"temp")
gimage_path=os.path.join(ap,"gimage")

# Set PIL logger not to interfere or chat
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("PIL.TiffImagePlugin").setLevel(logging.ERROR)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.ERROR)
logging.getLogger("PIL.JpegImagePlugin").setLevel(logging.ERROR)

log = LM.get_new_logger_propagating_to_root("Gimage","debug")

FIELDS_GIMAGE=[
    {"name": "ITEM",  "editable": False, "selectable": True,  "hidden": False},
    {"name": "VALUE", "editable": True,  "selectable": True,  "hidden": False},
    {"name": "TYPE",  "editable": False, "selectable": False, "hidden": False},
    {"name": "UNIT",  "editable": False, "selectable": True, "hidden": False},
    {"name": "INFO",  "editable": True, "selectable": True, "hidden": False},
]

class GimageGcodeGenerator(QtWidgets.QMainWindow):
    closed = QtCore.pyqtSignal()

    def __init__(self, parent=None, actual_interface_id=None):
        super().__init__(parent)
        log.info("... Started")
        self.setWindowTitle("Gimage G-Code Generator")
        self.setMinimumSize(1200, 800)
        # -------------------------
        #Initialize Variables
        # -------------------------
        if actual_interface_id is not None:
            self.actual_interface_id=actual_interface_id
        else:
            self.actual_interface_id="0"
        self.ch=Command_Handler(self.actual_interface_id)
        # create Signal Tracker
        self.st=class_ST.SignalTracker()  
        self.killer_event=threading.Event()
        self.tv=None
        self.cm=None
        self.color_selection_list=['Black&White','Red','Green','Blue','RGB','Not Red','Not Green','Not Blue']
        self.im = None
        self.im_width=0
        self.im_height=0
        self.is_original_image=False
        self.is_processed_image=False
        self.file_dialog=class_File_Dialogs.Dialogs()
        self.im_processor=ImageProcessor()
        self.all_icons_dict = {
                            "open_image": QtGui.QIcon(":/img/Ahmadhania-Spherical-Select-text.128.png"),
                            "save_process_image":QtGui.QIcon(":/img/Ahmadhania-Spherical-Save.128.png"),
                            "open_session_config":QtGui.QIcon(":/img/open-file-icon.png"),
                            "save_session_config":QtGui.QIcon(":/img/Save-as-icon.png"),
                            "refresh":QtGui.QIcon(":/img/Actions-view-refresh-icon.png"),
                            "position_helper":QtGui.QIcon(":/img/Ahmadhania-Spherical-Target.128.png"),
                            "layer_helper": QtGui.QIcon(":/img/Ahmadhania-Spherical-Restore.128.png"), 
                            "fit":QtGui.QIcon(":/img/move-icon.png"),
                            "machine_icon":QtGui.QIcon(":/img/Modify-icon.png"),
                            "tool_icon":QtGui.QIcon(":/img/Ahmadhania-Spherical-Paper-clip.128.png"),
                            "technique_icon":QtGui.QIcon(":/img/Ahmadhania-Spherical-Write.128.png"),
                            "color_icon":QtGui.QIcon(":/img/Ahmadhania-Spherical-Umbrella.128.png"),
                            "zoom_in": QtGui.QIcon(":/img/Plus-icon.png"),
                            "zoom_out": QtGui.QIcon(":/img/Minus-icon.png"),
                            "make_gcode":QtGui.QIcon(":/img/eye-in-a-sky-icon.png"),
                            "interface": QtGui.QIcon(":/img/Ahmadhania-Spherical-Top.128.png"),
                            }
        self._do_evaluation=False
        # -------------------------
        # Build GUI
        # -------------------------
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

        self.action_open_image = QtGui.QAction(self.all_icons_dict["open_image"], "Open Image", self)
        self.action_save_image = QtGui.QAction(self.all_icons_dict["save_process_image"], "Save Processed Image", self)
        self.gimage_image_toolbar.addAction(self.action_open_image)
        self.gimage_image_toolbar.addSeparator()
        self.gimage_image_toolbar.addAction(self.action_save_image)
        # Actual interface
        self.gimage_actual_interface_label=QtWidgets.QLabel("Actual Interface: ")
        # Config toolbar
        self.gimage_config_toolbar = QtWidgets.QToolBar()
        self.gimage_config_toolbar.setIconSize(QtCore.QSize(24, 24))

        self.action_open = QtGui.QAction(self.all_icons_dict["open_session_config"], "Open Session Config", self)
        self.action_save = QtGui.QAction(self.all_icons_dict["save_session_config"], "Save Session Config", self)
        self.action_refresh = QtGui.QAction(self.all_icons_dict["refresh"], "Refresh", self)
        self.action_position_helper = QtGui.QAction(self.all_icons_dict["position_helper"], "Position Helper", self)
        self.action_layer_helper = QtGui.QAction(self.all_icons_dict["layer_helper"], "Layer Helper", self)

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
        interface_layout, self.interface_combo = self._make_icon_label_combo_row(
            "Interface:", self.all_icons_dict["interface"])
        machine_layout, self.machine_combo = self._make_icon_label_combo_row(
            "Machine:", self.all_icons_dict["machine_icon"])
        tool_layout, self.tool_combo = self._make_icon_label_combo_row(
            "Tool:", self.all_icons_dict["tool_icon"])
        technique_layout, self.technique_combo = self._make_icon_label_combo_row(
            "Technique:", self.all_icons_dict["technique_icon"])
        color_layout, self.color_combo = self._make_icon_label_combo_row(
            "Color:", self.all_icons_dict["color_icon"])

        selector_layout.addLayout(interface_layout)
        selector_layout.addLayout(color_layout)
        selector_layout.addLayout(machine_layout)
        selector_layout.addLayout(tool_layout)
        selector_layout.addLayout(technique_layout)
        
        # -------------------------
        # TreeWidget
        # -------------------------
        self.tree = QtWidgets.QTreeView(self) # QTreeWidget(self)
        # -------------------------
        # Gcode output
        # -------------------------
        self.gcode_layout = QtWidgets.QHBoxLayout()
        # gcode toolbar
        self.gcode_toolbar = QtWidgets.QToolBar()
        self.gcode_toolbar.setIconSize(QtCore.QSize(36, 36))
        self.action_make_gcode = QtGui.QAction(self.all_icons_dict["make_gcode"], "Make Gcode", self)

        self.gcode_toolbar.addAction(self.action_make_gcode)

        # Progress_bar
        self.gimage_progressbar=QProgressBar()
        self.gimage_progressbar.setRange(0, 100)

        self.gcode_layout.addWidget(self.gcode_toolbar)
        self.gcode_layout.addWidget(self.gimage_progressbar)

        # -------------------------
        # Left layout
        # -------------------------
        left_layout.addWidget(self.gimage_image_toolbar)
        left_layout.addWidget(self.gimage_actual_interface_label)
        left_layout.addWidget(self.gimage_config_toolbar)
        left_layout.addLayout(selector_layout)
        left_layout.addWidget(self.tree)
        left_layout.addLayout(self.gcode_layout)
        # -------------------------
        # Splitter
        # -------------------------
        splitter.addWidget(left_panel)
        splitter.setStretchFactor(0, 0)
        #####################
        # --- RIGHT PANEL ---
        #####################

        # -------------------------
        # Image Toolbox
        # -------------------------
        self.image_toolbox = QtWidgets.QToolBar("Tools")
        self.image_toolbox.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.image_toolbox.setIconSize(QtCore.QSize(24, 24))
        self.image_toolbox.setMovable(False)

        self.action_zoom_in = QtGui.QAction(self.all_icons_dict["zoom_in"], "Zoom In", self)
        self.action_zoom_out = QtGui.QAction(self.all_icons_dict["zoom_out"], "Zoom Out", self)
        self.action_fit = QtGui.QAction(self.all_icons_dict["fit"], "Fit", self)

        self.image_toolbox.addAction(self.action_fit)
        self.image_toolbox.addSeparator()
        self.image_toolbox.addAction(self.action_zoom_in)
        self.image_toolbox.addAction(self.action_zoom_out)
        

        # -------------------------
        # Splitter with two views
        # -------------------------
        right_splitter = QtWidgets.QSplitter()
        right_splitter.setOrientation(QtCore.Qt.Orientation.Vertical)

        self.zoom_controller = SyncedZoomController()

        self.original_view = SyncedGraphicsView(self.zoom_controller)
        self.processed_view = SyncedGraphicsView(self.zoom_controller)
        self.original_view.set_has_image(False)
        self.processed_view.set_has_image(False)

        self.original_scene = QtWidgets.QGraphicsScene()
        self.original_view.setScene(self.original_scene)

        self.processed_scene = QtWidgets.QGraphicsScene()
        self.processed_view.setScene(self.processed_scene)

        right_splitter.addWidget(self.original_view)
        right_splitter.addWidget(self.processed_view)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 1)

        # -------------------------
        # Combine splitter + toolbox horizontally
        # -------------------------
        right_splitter_container = QtWidgets.QWidget()
        right_splitter_layout = QtWidgets.QHBoxLayout(right_splitter_container)
        right_splitter_layout.setContentsMargins(0, 0, 0, 0)
        right_splitter_layout.setSpacing(0)

        right_splitter_layout.addWidget(right_splitter, stretch=1)
        right_splitter_layout.addWidget(self.image_toolbox)

        splitter.addWidget(right_splitter_container)
        splitter.setStretchFactor(1, 1)
        # Set Configuration
        self.setup_configuration()
        self.fill_combos()
        self.connect_actions_to_gui()

    def _make_icon_label_combo_row(self, text, icon_obj:QtGui.QIcon):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        # Icon
        icon_label = QtWidgets.QLabel()
        icon_label.setPixmap(icon_obj.pixmap(24, 24))
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
        log.debug(self.cm.session)
        log.info("Success configuration set!")
        # QTreeWidget manager
        if self.cm.main_struct:
            self.main_struct=self.cm.main_struct
        else:
            self.main_struct={"No items":{"value":"Seems to be an issue with the configuration!","type":"str"}}
        print("+"*55)
        print("Loaded struct:")
        print(self.main_struct)
        print("+"*55)
        self.tv= TreeviewFunctions(self.tree,self.main_struct,FIELDS_GIMAGE)
        # attach delegate to VALUE column (1)
        delegate = TypedItemDelegate(self.tv)
        self.tree.setItemDelegateForColumn(1, delegate)
        self.tv.data_change[list,object,str,str].connect(self.on_tree_item_edited)
        self.tv.struct_data_change[list,object,str,str].connect(self.on_struct_item_edited)
        self.tv.expand_to_depth(1) #333) #Expand all
        # Condition Engine
        self.ce=ConditionEngine(self.tv.tracker)
        self._evaluate_conditions()
        
        # Add cache tooltip, icons, backgrounds, styles
        self.tv.set_icons_cache(self.all_icons_dict)
        self.tooltip_dict=self._get_tool_tip_dictionary()
        self.tv.set_tooltip_cache(self.tooltip_dict)
        #self.tv.set_style_cache(self.style_dict)

        # Right click Menu 
        self.tv.treeviewobj.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.tv.treeviewobj.customContextMenuRequested.connect(self.tv._on_context_menu)
        #self.tv.item_right_clicked.connect(self.on_item_right_clicked)
        
        self.tv.do_refresh()
    
    def _get_tool_tip_dictionary(self):
        """Generates tooltip dictionary from info in structure"""
        tooltip_dict={}
        root=self.tv.tracker.get_root()
        # set unique id for each tooltip, just in case child names are shared
        tt_id=0
        for key,item in root.items():
            node_valid=self.tv.tracker.validate_node([key])
            if node_valid.get("found"):
                track= node_valid.get("track")
                info=self.tv.tracker.get_value(track+["info"])
                if info is not None:
                    tooltip_dict[f"{tt_id}"] = info
                    # Set key in model
                    self.tv.tracker.set_or_create_property(track+["tooltip_key"],f"{tt_id}")
                    tt_id += 1
                if node_valid.get("has_children"):
                    for child_key in node_valid.get("children_keys"):
                        info=self.tv.tracker.get_value(track+[child_key,"info"])
                        if info is not None:
                            # Set key in model
                            self.tv.tracker.set_or_create_property(track+[child_key,"tooltip_key"],f"{tt_id}")
                            tooltip_dict[f"{tt_id}"] = info
                            tt_id += 1
        return tooltip_dict
    
    def on_item_right_clicked(self, src_index: QtCore.QModelIndex, stored):
        """Reserved for right click menu in the treeview"""
        # stored = src_index.data(USER_ROLE)
        menu = QtWidgets.QMenu(self)
        print(stored)
        # build actions based on stored / path / meta
        menu.addAction("Edit", lambda: self.menu_edit_item(src_index))
        menu.exec(QtGui.QCursor.pos())
    
    def menu_edit_item(self,index: QtCore.QModelIndex):
        """Example menu item"""
        stored = index.data(USER_ROLE)
        print(f'{stored.get("path")} @ row,col : {index.row()},{index.column()}')
    
    def fill_combos(self):
        id_list=self.ch.get_id_list()
        interface_name_list=[self.ch.get_name_from_id(an_id) for an_id in id_list]
        if interface_name_list:
            self.interface_combo.addItems(interface_name_list)
            if self.actual_interface_id in id_list:
                name=self.ch.get_name_from_id(self.actual_interface_id)
            else:
                name=interface_name_list[-1]
                self.actual_interface_id=id_list[-1]
            self.ch.set_id(self.actual_interface_id)
            self._set_combo_value(self.interface_combo,name) 
        if self.tv:
            self.machine_combo.addItems(self.cm.machine_list)
            self._setup_combo_obj(self.tool_combo,self.cm.tool_list)
            self._setup_combo_obj(self.technique_combo,self.cm.technique_list)
            #self.tool_combo.addItems(self.cm.tool_list)
            #self.technique_combo.addItems(self.cm.technique_list)
            self.color_combo.addItems(self.color_selection_list)
            # Set defaults
            m_t=self.tv.tracker.get_value(["machine","machine_type","value"])
            self._set_combo_value(self.machine_combo,m_t) 
            to_t=self.tv.tracker.get_value(["tool","tool_type","value"])
            self._set_combo_value(self.tool_combo,to_t)
            tq_t=self.tv.tracker.get_value(["technique","technique_type","value"])
            self._set_combo_value(self.technique_combo,tq_t) 
            c_t=self.tv.tracker.get_value(["image","color","value"])
            self._set_combo_value(self.color_combo,c_t) 
    
    def _setup_combo_obj(self,combo_obj,fill_list):
        model = QStandardItemModel(combo_obj)
        combo_obj.setModel(model)

        for itemdata in fill_list:
            item = QStandardItem(itemdata)
            model.appendRow(item)
    
    def _set_combo_value(self,combo:QComboBox,value:str):
        """Helper to set value to combo"""
        index = combo.findText(value) 
        if index >= 0: 
            combo.setCurrentIndex(index)

    @QtCore.pyqtSlot(list, object, object, str, str)
    def on_tree_item_edited_old_new(self, track, old_value, new_value, typestr, subtype):
        # Do not self._evaluate_conditions() here, is already done in on_tree_item_edited
        # Use this slot when you need old value and new value 
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

    @QtCore.pyqtSlot(list, object, str, str)
    def on_tree_item_edited(self, track, value, typestr, subtype):
        # Decide what to do with item value changed
        # self._evaluate_conditions()
        pass
    
    @QtCore.pyqtSlot(list, object, str, str)
    def on_struct_item_edited(self, track, value, typestr, subtype):
        # Decide what to do with item value changed
        if self._do_evaluation:
            self._evaluate_conditions()
            
    # def on_resolution_changed(self, value: float):
    #     self.cm.set_output_param("output", "resolution", value=float(value))

    def _evaluate_conditions(self):
        """Evaluate conditions if changes were applied refresh treeview"""
        do_eval=self._do_evaluation 
        self._do_evaluation = False
        evaluated = self.ce.evaluate_conditions_in_a_node(self.tv.tracker.get_root())
        if evaluated or do_eval:
            expanded = self.tv.get_expanded_paths()
            selected = self.tv.get_selected_paths()

            # Delay the refresh AND the restore
            def delayed_refresh():
                self.tv.do_refresh()
                self.tv.restore_expanded_paths(expanded)
                self.tv.restore_selected_paths(selected)
                self.tv.treeview_fit_to_contents(0)
                # Important Clear circular reference flag
                self.tv.tracker.remove_property_from_all_nodes(self.tv.tracker.get_root(),"__conditions__applied__")
            # Need to wait until all data changes are applied.
            QtCore.QTimer.singleShot(0, delayed_refresh)
    
    def connect_actions_to_gui(self):
        self.action_open.triggered.connect(self.load_gimage_config)
        self.action_save.triggered.connect(self.save_gimage_config)
        self.action_refresh.triggered.connect(self.refresh_gui_from_config)
        self.action_open_image.triggered.connect(self.load_original_image)

        self.action_fit.triggered.connect(self.on_fit_clicked)
        self.action_zoom_in.triggered.connect(self.on_zoom_in_clicked)
        self.action_zoom_out.triggered.connect(self.on_zoom_out_clicked)
        #Combos
        self.interface_combo.currentTextChanged.connect(self.on_interface_changed)
        self.color_combo.currentTextChanged.connect(self.on_color_changed)
        self.machine_combo.currentTextChanged.connect(self.on_machine_changed)
        self.tool_combo.currentTextChanged.connect(self.on_tool_changed)
        self.technique_combo.currentTextChanged.connect(self.on_technique_changed)

        self.action_layer_helper.triggered.connect(self.open_layer_helper)

        self.action_make_gcode.triggered.connect(self.make_gcode)
        # gimage signals
        self.st.gimage_progress.connect(self.on_gimage_progress)
        self.st.gimage_status.connect(self.on_gimage_status)
        self.st.gimage_finished.connect(self.on_gimage_finished)
        self.st.gimage_error.connect(self.on_gimage_error)
    
    def on_gimage_progress(self, percent, stat):
        self.gimage_progressbar.setValue(percent)
        # optional: update a label with stats
        # self.label_stats.setText(f"{stat.get('lines_done',0)} / {stat.get('lines_total',0)}")

    def on_gimage_status(self, msg):
        # self.label_status.setText(msg)
        pass

    def on_gimage_finished(self, filepath):
        # Load only on demand, or show a message
        QMessageBox.information(self, "G-code ready", f"G-code saved to:\n{filepath}")
        # Optionally: open in external editor

    def on_gimage_error(self, msg):
        QMessageBox.critical(self, "G-image Error", msg)
        log.error(f"Gimage Error detected: {msg}")
    
    def make_gcode(self):
        if self.is_processed_image:
            # Here emit signal to main with configuration dict or create       
            self.killer_event.clear()     
            gph=GImagePluginHandler(self.im_processed,
                                    self.main_struct.copy(),
                                    self.ch,
                                    self.killer_event,
                                    self.st)
            gph.start()

    def open_layer_helper(self):
        if not self.is_original_image:
            return
        process=self.tv.tracker.get_value(["image","process","value"])
        if process=="descrete" and self.is_processed_image:
            num_layers=self.tv.tracker.get_value(["image","number_of_colors","value"])
            color_selection=self.tv.tracker.get_value(["image","color","value"])
            selected_layers=self.tv.tracker.get_value(["image","selected_layers","value"])
            self.LSTDialog=LayerSelectionToolDialog(num_layers,selected_layers)
            self.LSTDialog.set_preview.connect(self.set_a_preview_image_to_view)
            self.LSTDialog.accepted.connect(self.set_layer_helper_values)
            self.LSTDialog.Fill_comboBox_LSTD_Image_Process(self.color_selection_list,color_selection) 
            self.LSTDialog.color_palette=self.im_processor.get_color_palette(self.im_processed,num_layers)
            self.LSTDialog.Assign_Colors_to_Labels(self.LSTDialog.color_palette)       

    def on_interface_changed(self, value):
        """Interface setting changed, if different apply ch change"""
        id_list=self.ch.get_id_list()
        interface_name_list=[self.ch.get_name_from_id(an_id) for an_id in id_list]
        
        for an_id,a_name in zip(id_list,interface_name_list):
            if value == a_name and an_id!=self.ch.id:
                self.actual_interface_id=an_id
                self.ch.set_id(an_id)
                return
        
    def on_color_changed(self, value):
        """Color setting changed, if different apply to config and processed image"""
        color_selection=self.tv.tracker.get_value(["image","color","value"])
        if color_selection != value:
            self._do_evaluation=True #triggers self._evaluate_conditions() # does refresh and changes according conditions
            was_set=self.tv.tracker.set_value(["image","color","value"],value)
            self._do_evaluation=False
            if was_set:
                def new_process_image():
                    self.im_processed=self.make_processed_image()
                    self.set_processed_image_to_view()
                if self.is_original_image:
                    QtCore.QTimer.singleShot(0, new_process_image)
    
    def on_technique_changed(self,value):
        """Technique setting changed, if different apply to config and refresh Treeview"""
        track=["technique","technique_type","value"]
        technique_selection=self.tv.tracker.get_value(track)
        compatible_techniques=self.cm.get_compatible_techniques(self.cm.tool_name)
        if value not in compatible_techniques:
            # restore previous valid value
            self.technique_combo.blockSignals(True)
            self._set_combo_value(self.technique_combo, technique_selection)
            self.technique_combo.blockSignals(False)
            return
        if technique_selection != value:
            if not self._change_setting_trigger_evaluate_conditions(track,value):
                log.warning(f"Unable to set {value} to {track}")

    def _get_actual_machine_tool_technique(self):
        """Get actual machine,tool,technique selections"""
        track=["tool","tool_type","value"]
        tool_selection=self.tv.tracker.get_value(track)
        machine_track=["machine","machine_type","value"]
        machine_selection=self.tv.tracker.get_value(machine_track)
        track=["technique","technique_type","value"]
        technique_selection=self.tv.tracker.get_value(track)
        return machine_selection,tool_selection,technique_selection

    def on_tool_changed(self,value):
        """Tool setting changed, if different apply to config and refresh Treeview"""
        track=["tool","tool_type","value"]
        tool_selection=self.tv.tracker.get_value(track)
        compatible_tools= self.cm.get_compatible_tools(self.cm.machine_name)
        if value not in compatible_tools:
            self.tool_combo.blockSignals(True)
            self._set_combo_value(self.tool_combo, tool_selection)
            self.tool_combo.blockSignals(False)
            return
        
        if tool_selection != value:
            compatible_techniques=self.cm.get_compatible_techniques(value)
            self.set_technique_compatibility(compatible_techniques)
            if len(compatible_techniques)==0:
                return
            if self.cm.technique_name in compatible_techniques:
                self.cm.set_tool(value)
            else:
                self.cm.set_machine_tool_technique(self.cm.machine_name,value,compatible_techniques[0])
                self.technique_combo.blockSignals(True)
                self._set_combo_value(self.technique_combo,compatible_techniques[0])
                self.technique_combo.blockSignals(False)
    
            self._do_evaluation=True #triggers self._evaluate_conditions() # does refresh and changes according conditions
            self._evaluate_conditions()
            self._do_evaluation=False
            
    def on_machine_changed(self,value):
        """Machine setting changed, if different apply to config and refresh Treeview"""
        machine_track=["machine","machine_type","value"]
        machine_selection=self.tv.tracker.get_value(machine_track)
        # print("*"*33)
        # print(self.cm.machine_dict) # this contains the dictionary of treeview (cm session)
        # print(self.cm.machine) # machine data ->dictionary
        # print("*"*33) 
        if machine_selection != value:
            compatible_tools= self.cm.get_compatible_tools(value)
            self.set_tool_compatibility(compatible_tools)
            if len(compatible_tools)==0:
                return
            if self.cm.tool_name in compatible_tools:
                # keep technique and tool selection
                self.cm.set_machine(value)
            else:
                compatible_techniques=self.cm.get_compatible_techniques(compatible_tools[0])
                self.set_technique_compatibility(compatible_techniques)
                if len(compatible_techniques)==0:
                    return
                self.cm.set_machine_tool_technique(value,compatible_tools[0],compatible_techniques[0])
                self.tool_combo.blockSignals(True)
                self.technique_combo.blockSignals(True)
                self._set_combo_value(self.tool_combo,compatible_tools[0])
                self._set_combo_value(self.technique_combo,compatible_techniques[0])
                self.tool_combo.blockSignals(False)
                self.technique_combo.blockSignals(False)
            
            self._do_evaluation=True #triggers self._evaluate_conditions() # does refresh and changes according conditions
            self._evaluate_conditions()
            self._do_evaluation=False
            
    def set_tool_compatibility(self, compatible_tools):
        model = self.tool_combo.model()
        if isinstance(model,QStandardItemModel):
            pass
        for row in range(model.rowCount()):
            item = model.item(row)
            tool_name = item.text()

            if tool_name in compatible_tools:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
            else:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)

    def set_technique_compatibility(self, compatible_techniques):
        model = self.technique_combo.model()
        if isinstance(model,QStandardItemModel):
            pass
        for row in range(model.rowCount()):
            item = model.item(row)
            tech_name = item.text()

            if tech_name in compatible_techniques:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
            else:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)

    
    def _change_setting_trigger_evaluate_conditions(self,track,value):
        was_set=self.tv.tracker.set_value(track,value)
        if was_set:
            self._do_evaluation=True #triggers self._evaluate_conditions() # does refresh and changes according conditions
            self._evaluate_conditions()
        self._do_evaluation=False
        return was_set
    
    def on_zoom_in_clicked(self):
        factor = 1.25
        new_zoom = self.zoom_controller.current_zoom * factor
        self.zoom_controller.set_zoom(new_zoom)

    def on_zoom_out_clicked(self):
        factor = 0.8
        new_zoom = self.zoom_controller.current_zoom * factor
        self.zoom_controller.set_zoom(new_zoom)

    @staticmethod
    def zoom_to_fit_height(view: QtWidgets.QGraphicsView, scene_rect: QtCore.QRectF) -> float:
        """Return the zoom factor needed so the image height matches the view height."""
        if scene_rect.height() == 0:
            return 1.0

        viewport_h = view.viewport().height()
        return viewport_h / scene_rect.height()

    @staticmethod
    def zoom_to_fit_width(view: QtWidgets.QGraphicsView, scene_rect: QtCore.QRectF) -> float:
        """Return the zoom factor needed so the image width matches the view width."""
        if scene_rect.width() == 0:
            return 1.0

        viewport_w = view.viewport().width()
        return viewport_w / scene_rect.width()

    def set_best_zoom_fit(self):
        """Fits the window to the height or width depending on window size"""
        scene_rect = self.original_scene.sceneRect()

        zoom_h = self.zoom_to_fit_height(self.original_view, scene_rect)
        zoom_w = self.zoom_to_fit_width(self.original_view, scene_rect)

        # Apply zoom through your controller
        self.zoom_controller.set_zoom(min(zoom_h,zoom_w))

    def on_fit_width_clicked(self):
        rect = self.original_scene.sceneRect()
        zoom = self.zoom_to_fit_width(self.original_view, rect)
        self.zoom_controller.set_zoom(zoom)

    def on_fit_height_clicked(self):
        rect = self.original_scene.sceneRect()
        zoom = self.zoom_to_fit_height(self.original_view, rect)
        self.zoom_controller.set_zoom(zoom)

    def on_fit_clicked(self):
        self.original_view.fitInView(
            self.original_scene.itemsBoundingRect(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio
        )
        self.processed_view.fitInView(
            self.processed_scene.itemsBoundingRect(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio
        )
        # Reset zoom controller to 1.0 so wheel zoom starts from neutral
        self.zoom_controller.set_zoom(1.0)
        self.set_best_zoom_fit()

    def open_image(self, imagefilename):
        """Opens image into the show supports jpeg,png,svg 
            and sets self.im as pillow 

        Args:
            imagefilename (str): filename

        Returns:
            bool: True if Image loaded correctly
        """
        if not os.path.exists(imagefilename):
            return False
        try:
            if imagefilename.lower().endswith(".svg"):
                # Render SVG → QPixmap
                pix = self.svg_to_qpixmap(imagefilename)
                # Convert QPixmap → Pillow Image
                self.im = self.qpixmap_to_pil(pix)
                self.im_width = self.im.width
                self.im_height = self.im.height
                # Display 
                self.show_original_image(pix)
            else:
                # Otherwise: normal raster image
                self.im = Image.open(imagefilename)
                self.im_width = self.im.width
                self.im_height = self.im.height
                qimg = self.pil_to_qimage(self.im)
                self.show_original_image(qimg)

            self.is_original_image = True
            self.image_filename = imagefilename
            self.original_view.set_has_image(self.is_original_image)
            self.clear_processed_view()
            self.im_processed=self.make_processed_image() # Image
            self.is_processed_image = True 
            self.set_processed_image_to_view()
            # set zoom
            # self.zoom_controller.set_zoom(1.0)
            self.on_fit_clicked()
            return True
        except Exception as e:
            log.error(f"Opening Image: {e}")
            self.im = None
            self.clear_original_view(include_processed=True)
        return False

    def set_processed_image_to_view(self):
        if self.is_processed_image: 
            self.processed_view.set_has_image(self.is_processed_image)
            pqimg = self.pil_to_qimage(self.im_processed)
            self.show_processed_image(pqimg)

    @QtCore.pyqtSlot(list, str, int, str)
    def set_layer_helper_values(self,selected_layers,process,num_colors,color_selection):
        if not self.is_original_image:
            return
        self._do_evaluation=True
        ok = self.tv.tracker.set_value(["image","process","value"],process) # descrete
        ok |= self.tv.tracker.set_value(["image","number_of_colors","value"],num_colors)
        ok |= self.tv.tracker.set_value(["image","color","value"],color_selection)    
        ok |= self.tv.tracker.set_value(["image","selected_layers","value"],selected_layers)
        self._do_evaluation=False
        self._set_combo_value(self.color_combo,color_selection)
        if ok:
            self.im_processed=self.make_processed_image()
            self.is_processed_image = True 
            self.set_processed_image_to_view()
        
        
    @QtCore.pyqtSlot(list, str, int, str)
    def set_a_preview_image_to_view(self,selected_layers,process,num_colors,color_selection):
        if not self.is_original_image:
            return
        print("got selected layers->",selected_layers)
        im_processed=self.im.copy()
        if process == "descrete":            
            im_processed = self.im_processor.apply_quant_color_process_to_image(im_processed,num_colors,color_selection)
            try:
                self.LSTDialog.color_palette=self.im_processor.get_color_palette(im_processed,num_colors)
                self.LSTDialog.Assign_Colors_to_Labels(self.LSTDialog.color_palette) 
            except:
                pass
            im_processed = self.im_processor.retain_selected_layers(im_processed,selected_layers,num_colors)
        elif process == "continuous":
            im_processed=self.im_processor.apply_quant_color_process_to_image(im_processed,None,color_selection)
        self.is_processed_image = True 
        self.processed_view.set_has_image(self.is_processed_image)
        pqimg = self.pil_to_qimage(im_processed)
        self.show_processed_image(pqimg)

    def clear_processed_view(self):
        self.is_processed_image=False
        self.processed_scene.clear()
        self.processed_view.set_has_image(False)
    
    def clear_original_view(self,include_processed=True):
        self.is_original_image=False
        self.original_scene.clear()
        self.original_view.set_has_image(False)
        if include_processed:
            self.clear_processed_view()

    def save_gimage_config(self):
        filepath=self.file_dialog.saveFileDialog(6,"Save Gimage Config") #json
        if filepath:
            self.cm.save_session(filepath)

    def load_gimage_config(self):
        filepath = self.file_dialog.openFileNameDialog(6,"Load Gimage Config") #json
        if filepath:
            self.cm.load_session(filepath)
            self.refresh_gui_from_config()

    def load_original_image(self):
        filepath = self.file_dialog.openFileNameDialog(1,"Load Gimage Image")
        if filepath:
            self.open_image(filepath)

    def refresh_gui_from_config(self):
        # placeholder for refresh
        pass

    def make_processed_image(self):
        """Makes color and quantization process to image.

        Returns:
            Image: processed image
        """
        if not self.is_original_image:
            return
        im_processed=self.im.copy()
        process=self.tv.tracker.get_value(["image","process","value"])
        num_colors=self.tv.tracker.get_value(["image","number_of_colors","value"])
        color_selection=self.tv.tracker.get_value(["image","color","value"])
        if process == "descrete":            
            im_processed=self.im_processor.apply_quant_color_process_to_image(im_processed,num_colors,color_selection)
            selected_layers=self.tv.tracker.get_value(["image","selected_layers","value"])
            im_processed=self.im_processor.retain_selected_layers(im_processed,selected_layers,num_colors)
        elif process == "continuous":
            im_processed=self.im_processor.apply_quant_color_process_to_image(im_processed,None,color_selection)
        return im_processed

    def show_original_image(self, image):
        self.original_scene.clear()
        if isinstance(image, QtGui.QPixmap):
            pix = image
        elif isinstance(image, QtGui.QImage):
            pix = QtGui.QPixmap.fromImage(image)
        elif isinstance(image, Image.Image):
            pix = self.pil_to_qpixmap(image)
        else:
            log.error(f"Unsupported image type: {type(image)}")
            return
        self.original_scene.addPixmap(pix)
        # IMPORTANT: force identical sceneRect
        self.original_scene.setSceneRect(QtCore.QRectF(pix.rect()))
        # Fit only once
        self.original_view.fitInView(
            self.original_scene.sceneRect(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio
        )
        # Sync controller zoom to the fitted zoom
        fitted_zoom = self.original_view.transform().m11()
        self.zoom_controller.set_zoom(fitted_zoom)
        self.original_view.set_has_image(True)

    def show_processed_image(self, image):
        self.processed_scene.clear()
        if isinstance(image, QtGui.QPixmap):
            pix = image
        elif isinstance(image, QtGui.QImage):
            pix = QtGui.QPixmap.fromImage(image)
        elif isinstance(image, Image.Image):
            pix = self.pil_to_qpixmap(image)
        else:
            log.error(f"Unsupported image type: {type(image)}")
            return
        self.processed_scene.addPixmap(pix)
        # IMPORTANT: force identical sceneRect
        self.processed_scene.setSceneRect(QtCore.QRectF(pix.rect()))
        self.processed_view.set_has_image(True)
        self.is_processed_image = True
        # Apply current zoom WITHOUT resetTransform
        current = self.processed_view.transform().m11()
        if current == 0:
            current = 0.0001
        scale_factor = self.zoom_controller.current_zoom / current
        self.processed_view.scale(scale_factor, scale_factor)

    @staticmethod
    def pil_to_qimage(pil_image:Image)->QImage:
        pil_image = pil_image.convert("RGBA")
        data = pil_image.tobytes("raw", "RGBA")
        qimage = QImage(
            data,
            pil_image.width,
            pil_image.height,
            QImage.Format.Format_RGBA8888
        )
        return qimage
    
    def pil_to_qpixmap(self,pil_image)->QPixmap:
        return QPixmap.fromImage(self.pil_to_qimage(pil_image))

    @staticmethod
    def qpixmap_to_pil(pixmap:QPixmap)->Image.Image:
        qimage = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        width = qimage.width()
        height = qimage.height()
        ptr = qimage.bits()
        ptr.setsize(qimage.sizeInBytes())
        arr = bytes(ptr)
        pil_img = Image.frombuffer("RGBA", (width, height), arr, "raw", "RGBA", 0, 1)
        return pil_img

    @staticmethod
    def svg_to_qpixmap(svg_path, width=None, height=None):
        renderer = QtSvg.QSvgRenderer(svg_path)

        # If no size given, use the SVG's default size
        default_size = renderer.defaultSize()
        w = width or default_size.width()
        h = height or default_size.height()

        pixmap = QPixmap(w, h)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return pixmap

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

class ImageProcessor:
    def __init__(self):
        super().__init__()
        self.color_palette=None
        self.rgb_to_pval = {}
        self.pval_to_rgb = {}
        self.imp=None

    def apply_quant_color_process_to_image(self,im:Image.Image,number_of_colors, color_selection)->Image.Image:
        """Set color selection and quantize image"""
        imp=im.copy()
        if color_selection == 'Black&White':
            imp = imp.convert('L')
        else:
            imp = imp.convert('RGB')
            if color_selection == 'Red':
                imp = self.get_one_channel_from_image(imp,'R')
            elif color_selection == 'Green':
                imp = self.get_one_channel_from_image(imp,'G')
            elif color_selection == 'Blue':
                imp =self.get_one_channel_from_image(imp,'B') 
            elif color_selection == 'Not Red':
                imp = self.remove_channel_from_image(imp,'R')
            elif color_selection == 'Not Green':
                imp = self.remove_channel_from_image(imp,'G')
            elif color_selection == 'Not Blue':
                imp =self.remove_channel_from_image(imp,'B')   
        if isinstance(number_of_colors,int) and 0<number_of_colors<=256:
            return imp.quantize(colors=number_of_colors)
        return imp

    @staticmethod
    def rgb_to_luminance_array(imp):
        """
        Convert an RGB Pillow image to a luminance (grayscale) NumPy array.

        Uses the standard Rec. 601 luma formula:
            L = 0.299*R + 0.587*G + 0.114*B

        Args:
            imp (PIL.Image): Input RGB image.

        Returns:
            numpy.ndarray: 2D array of uint8 luminance values.
        """
        arr = np.array(imp.convert("RGB"), dtype=np.float32)
        L = arr[:, :, 0] * 0.299 + arr[:, :, 1] * 0.587 + arr[:, :, 2] * 0.114
        return L.astype(np.uint8)

    def is_color_in_palette(self, color):
        """
        Return palette index for an RGB tuple.
        Returns -1 if not found.
        """
        return self.rgb_to_pval.get(color, -1)

    def get_color_from_palette(self, pval):
        """
        Return RGB tuple for a palette index.
        Returns white if not found.
        """
        return self.pval_to_rgb.get(pval, (255, 255, 255))

    def get_image_value_range(self):
        """
        Compute the minimum and maximum luminance values in the current image.

        Converts the image to luminance using rgb_to_luminance_array() and
        returns the min/max values found.

        Returns:
            list: [0, min_luminance, max_luminance]
        """
        L = self.rgb_to_luminance_array(self.imp)
        return [0, int(L.min()), int(L.max())]

    def build_palette_maps(self):
        """
        Build fast lookup dictionaries for palette operations.

        Creates:
            self.rgb_to_pval: {(r,g,b): pval}
            self.pval_to_rgb: {pval: (r,g,b)}
        """
        self.rgb_to_pval = {}
        self.pval_to_rgb = {}
        if self.color_palette is None:
            return
        for p, c, r, g, b in self.color_palette:
            self.rgb_to_pval[(r, g, b)] = p
            self.pval_to_rgb[p] = (r, g, b)

    def retain_selected_layers(self,imp:Image.Image, selected_layer_list:list,number_of_colors:int,unselected_fill_rgb:tuple=None):
        """
        Keep only pixels whose palette index is in selected_layer_list.
        All other pixels become white.

        Works for both RGB images and palette-indexed images.
        Uses NumPy for fast vectorized processing.
        """
        if not isinstance(selected_layer_list,list):
            selected_layer_list=[-1]
        if len(selected_layer_list) == 1 and selected_layer_list[0] == -1: #case [-1]
            selected_layer_list=list(range(number_of_colors))

        self.color_palette=self.get_color_palette(imp,number_of_colors)
        self.build_palette_maps()
        arr = np.array(imp)
        # Case 1: RGB image → convert to palette indices
        if arr.ndim == 3:
            h, w, _ = arr.shape
            flat = arr.reshape(-1, 3)
            rgb_tuples = [tuple(px) for px in flat]
            # Map RGB → palette index (default -1 for unknown)
            pvals = np.array([self.rgb_to_pval.get(rgb, -1) for rgb in rgb_tuples])
            pvals = pvals.reshape(h, w)
        # Case 2: indexed image (mode "P")
        else:
            pvals = arr
        # Build mask of selected layers
        mask = np.isin(pvals, selected_layer_list)
        # Output array (RGB)
        out = np.zeros((pvals.shape[0], pvals.shape[1], 3), dtype=np.uint8)
        if unselected_fill_rgb is None:
            unselected_fill_rgb=(255, 255, 255)  # default white

        out[:, :] = unselected_fill_rgb
        # Fill selected pixels with their palette RGB
        for p in selected_layer_list:
            rgb = self.pval_to_rgb.get(p, unselected_fill_rgb)
            out[pvals == p] = rgb
        # Convert back to Pillow image
        return Image.fromarray(out, "RGB")

    @staticmethod
    def get_one_channel_from_image(imp, channel):
        """
        Keep only one RGB channel from an image and zero out the others.

        Args:
            imp (PIL.Image): Input image.
            channel (str or int): 'R', 'G', 'B' or 0,1,2.

        Returns:
            PIL.Image: Image with only the selected channel preserved.
        """
        arr = np.array(imp.convert("RGB"))
        if channel in ('R', 0):
            arr[:, :, 1] = 0
            arr[:, :, 2] = 0
        elif channel in ('G', 1):
            arr[:, :, 0] = 0
            arr[:, :, 2] = 0
        elif channel in ('B', 2):
            arr[:, :, 0] = 0
            arr[:, :, 1] = 0
        return Image.fromarray(arr, "RGB")

    @staticmethod
    def remove_channel_from_image(imp, channel):
        """
        Remove (zero out) a single RGB channel while keeping the others intact.

        Args:
            imp (PIL.Image): Input image.
            channel (str or int): 'R', 'G', 'B' or 0,1,2.

        Returns:
            PIL.Image: Image with the selected channel removed.
        """
        arr = np.array(imp.convert("RGB"))
        if channel in ('R', 0):
            arr[:, :, 0] = 0
        elif channel in ('G', 1):
            arr[:, :, 1] = 0
        elif channel in ('B', 2):
            arr[:, :, 2] = 0
        return Image.fromarray(arr, "RGB")
    
    @staticmethod
    def get_color_palette(imp: Image.Image, number_of_colors: int = 256):
        """
        Extract the palette from a quantized Pillow image.

        Returns a list of tuples:
            (palette_index, count, r, g, b)

        Args:
            imp (PIL.Image.Image): A quantized image (mode 'P').
            number_of_colors (int): Maximum number of colors to retrieve.

        Returns:
            list[tuple[int, int, int, int, int]]:
                A list of (pval, count, r, g, b) entries.
        """
        # Ensure the image is palette-based
        number_of_colors=max(number_of_colors,1)
        number_of_colors=min(number_of_colors,256)
        if imp.mode != "P":
            #raise ValueError(f"get_color_palette() requires a quantized 'P' mode image, actual {imp.mode}")
            imp = imp.quantize(colors=number_of_colors)
            
        color_list = imp.getcolors(number_of_colors)  # [(count, pval), ...]
        palette_list = imp.getpalette()               # flat RGB list
        if palette_list is None: 
            return []
        if not color_list:
            return []

        color_palette = []

        for count, pval in color_list:
            base = 3 * pval
            r = palette_list[base + 0]
            g = palette_list[base + 1]
            b = palette_list[base + 2]
            color_palette.append((pval, count, r, g, b))

        return color_palette

class SyncedZoomController(QtCore.QObject):
    zoom_changed = QtCore.pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.current_zoom = 1.0
        self.max_zoom = 50.0
        self.min_zoom = 0.001
        self.views = []

    def register_view(self, view):
        self.views.append(view)

    def set_zoom(self, factor):
        factor = max(self.min_zoom, min(factor, self.max_zoom))
        self.current_zoom = factor
        self.zoom_changed.emit(factor)

    def zoom_by(self, multiplier: float):
        self.set_zoom(self.current_zoom * multiplier)
    
    def reset_zoom(self):
        self.set_zoom(1.0)


class SyncedGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, controller: SyncedZoomController, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.controller = controller
        self.controller.register_view(self)

        self._ignore_wheel = False
        self._ignore_scroll = False
        self._ignore_zoom = False
        self._has_image = False
        self.zoom_factor=1.01

        # Connect zoom sync
        self.controller.zoom_changed.connect(self.apply_zoom)

        # Connect scroll sync
        self.horizontalScrollBar().valueChanged.connect(self.sync_scroll_x)
        self.verticalScrollBar().valueChanged.connect(self.sync_scroll_y)

        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def set_has_image(self, value: bool):
        self._has_image = value

    # -------------------------
    # Wheel Zoom
    # -------------------------
    def wheelEvent(self, event):
        if not self._has_image or self._ignore_wheel:
            return

        zoom_in = self.zoom_factor
        zoom_out = 1/self.zoom_factor
        factor = zoom_in if event.angleDelta().y() > 0 else zoom_out

        new_zoom = self.controller.current_zoom * factor
        self.controller.set_zoom(new_zoom)

    # -------------------------
    # Apply Zoom (from controller)
    # -------------------------
    def apply_zoom(self, factor):
        if not self._has_image or self._ignore_zoom:
            return

        self._ignore_zoom = True

        # Compute relative scale factor
        current = self.transform().m11()
        if current == 0:
            current = 0.0001

        scale_factor = factor / current
        self.scale(scale_factor, scale_factor)

        self._ignore_zoom = False

    # -------------------------
    # Scroll Sync
    # -------------------------
    def sync_scroll_x(self, value):
        if self._ignore_scroll or not self._has_image:
            return

        for view in self.controller.views:
            if view is self or not view._has_image:
                continue

            view._ignore_scroll = True
            view.horizontalScrollBar().setValue(value)
            view._ignore_scroll = False

    def sync_scroll_y(self, value):
        if self._ignore_scroll or not self._has_image:
            return

        for view in self.controller.views:
            if view is self or not view._has_image:
                continue

            view._ignore_scroll = True
            view.verticalScrollBar().setValue(value)
            view._ignore_scroll = False

class ConfigManager:
    def __init__(self, base_folder=gimage_path,session_filepath=None):
        self.base_folder = Path(base_folder)
        self.is_machine_profile=False
        self.is_tool_profile=False
        self.is_teqnique_profile=False
        self.is_session_profile=False
        self.session_filepath=session_filepath
        self.main_struct=None
        # Load all profiles
        self.load_all_profiles()
        # Validate and merge
        self._validate_session()
        self._set_main_struct()

    def _set_main_struct(self):
        self.main_struct=self.session_dict
        self.tracker=TreeStructTracker(self.main_struct)
        self.tracker.data_changed.connect(self._tracker_data_change)

    def _tracker_data_change(self,track, value, a_type, subtype):
        print("ConfigManager tracker got: ",track, value, a_type, subtype)    

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
            raise ValueError("Missing one or more profiles!")
        try:
            machine = self.session["machine"]["machine_type"]["value"]
            tool = self.session["tool"]["tool_type"]["value"]
            workspace = self.session["workspace"]
            image = self.session["image"]
            output = self.session["output"]
            technique = self.session["technique"]["technique_type"]["value"]
        except (KeyError,TypeError,ValueError) as eee:
            raise ValueError(f"Missing configuration in file: '{eee}'")

        # --- 1. Validate existence ---
        if machine not in self.machine_profiles:
            raise ValueError(f"Unknown machine '{machine}'")

        if tool not in self.tool_profiles:
            raise ValueError(f"Unknown tool '{tool}'")

        if technique not in self.technique_profiles:
            raise ValueError(f"Unknown technique '{technique}'")

        machine_def = self.machine_profiles[machine]
        tool_def = self.tool_profiles[tool]
        tech_def = self.technique_profiles[technique]

        # --- 2. Tool must be compatible with machine ---
        if "compatible_machines" in tool_def:
            if machine not in tool_def["compatible_machines"]:
                raise ValueError(
                    f"Tool '{tool}' is not compatible with machine '{machine}'"
                )

        # --- 3. Technique must be compatible with tool ---
        if tool not in tech_def["compatible_tools"]:
            raise ValueError(
                f"Technique '{technique}' is not compatible with tool '{tool}'"
            )

        # --- 4. Technique requirements must be supported by machine/tool ---
        # Analog power requirement
        if tech_def.get("requires_analog_power", False):
            if not machine_def.get("supports_analog_power", False):
                raise ValueError(
                    f"Technique '{technique}' requires analog power, "
                    f"but machine '{machine}' does not support it."
                )

        # Grayscale requirement
        if tech_def.get("requires_grayscale", False):
            if not machine_def.get("supports_grayscale", True):
                raise ValueError(
                    f"Technique '{technique}' requires grayscale capability, "
                    f"but machine '{machine}' does not support it."
                )

        # Axis requirement (example: some techniques need Z)
        if tech_def.get("requires_z_axis", False):
            has_z = any(ax["name"] == "Z" for ax in machine_def["axes"])
            if not has_z:
                raise ValueError(
                    f"Technique '{technique}' requires a Z axis, "
                    f"but machine '{machine}' does not have one."
                )

        return True

    def update_value(self, section, key, new_value):
        target = None
        if section == "machine":
            target = self.machine_dict
        elif section == "tool":
            target = self.tool_dict
        elif section == "workspace":
            target = self.workspace_dict
        elif section == "technique":
            target = self.technique
        elif section == "image":
            target = self.image_dict
        elif section == "output":
            target = self.output_dict
        else:
            raise KeyError(f"Unknown section: {section}")
        entry = target[key]

        if isinstance(entry, dict) and "value" in entry:
            entry["value"] = new_value
        else:
            target[key] = new_value

    def _make_configuration_structure(self):
        s_dict = {
            "image": {
                "icon_key":"open_image",
                "children":[{key:value} for key,value in self.image_dict.items()]
                },
            "machine": {
                "icon_key":"machine_icon",
                "children":[{key:value} for key,value in self.machine_dict.items()]
                },
            "tool": {
                "icon_key":"tool_icon",
                "children":[{key:value} for key,value in self.tool_dict.items()]
                    },
            "workspace": {
                "icon_key":"position_helper",
                "children":[{key:value} for key,value in self.workspace_dict.items()]
                },
            "technique": {
                "icon_key":"technique_icon",
                "children":[{key:value} for key,value in self.technique_dict.items()]
                },
            "output": {
                "icon_key":"make_gcode",
                "children":[{key:value} for key,value in self.output_dict.items()]},
        }
        tr=TreeStructTracker(s_dict)
        ok = tr.set_or_create_value(["image","color","icon_key"],"color_icon")
        ok |= tr.set_or_create_value(["image","color","meta[editable]"],False)
        ok |= tr.set_or_create_value(["image","color","meta[selectable]"],False)
        # Here add icons and style
        return tr.get_root()

    # -------------------------
    # ACCESSORS
    # -------------------------
    @property
    def session_dict(self):
        return self._make_configuration_structure()

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
    def machine_name(self):
        return self.session["machine"]["machine_type"]["value"]

    @property
    def machine(self):
        return self.machine_profiles[self.machine_name]

    @property
    def tool_name(self):
        return self.session["tool"]["tool_type"]["value"]

    @property
    def tool(self):
        return self.tool_profiles[self.tool_name]

    @property
    def technique_name(self):
        return self.session["technique"]["technique_type"]["value"]

    @property
    def technique(self):
        return self.technique_profiles[self.technique_name]
    
    @property
    def machine_dict(self):
        return self.session.get("machine",None)
    
    @property
    def tool_dict(self):
        return self.session.get("tool",None)
    
    @property
    def workspace_dict(self):
        return self.session.get("workspace",None)

    @property
    def technique_dict(self):
        return self.session.get("technique",None)
    
    @property
    def image_dict(self):
        return self.session.get("image",None)

    @property
    def output_dict(self):
        return self.session.get("output",None)

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
        self.tracker.set_value(["machine","machine_type","value"],name)
        # self.session["machine"]["machine_type"]["value"] = name
        self._set_machine_profile(name)
        self._validate_session()

    def set_tool(self, name):
        if name not in self.tool_profiles:
            raise ValueError(f"Unknown tool '{name}'")
        self.tracker.set_value(["tool","tool_type","value"],name)
        #self.session["tool"]["tool_type"]["value"] = name
        self._validate_session()

    def set_technique(self, name):
        if name not in self.technique_profiles:
            raise ValueError(f"Unknown technique '{name}'")
        self.tracker.set_value(["technique","technique_type","value"],name)
        #self.session["technique"]["technique_type"]["value"] = name
        self._validate_session()
    
    def set_machine_tool_technique(self, machine_name,tool_name,technique_name):
        """Sets the tree values then triggers the validation"""
        if machine_name not in self.machine_profiles:
            raise ValueError(f"Unknown machine '{machine_name}'")
        #self.session["machine"]["machine_type"]["value"] = machine_name
        self.tracker.set_value(["machine","machine_type","value"],machine_name)
        self._set_machine_profile(machine_name)
        
        if tool_name not in self.tool_profiles:
            raise ValueError(f"Unknown tool '{tool_name}'")
        #self.session["tool"]["tool_type"]["value"] = tool_name
        self.tracker.set_value(["tool","tool_type","value"],tool_name)
        
        if technique_name not in self.technique_profiles:
            raise ValueError(f"Unknown technique '{technique_name}'")
        #self.session["technique"]["technique_type"]["value"] = technique_name
        self.tracker.set_value(["technique","technique_type","value"],technique_name)
        self._validate_session()

    def set_image_param(self, key, value):
        self.session["image"][key] = value

    def set_output_param(self, key, value):
        self.session["output"][key] = value
    
    def _set_machine_profile(self,machine_name):
        # --- 1. Validate existence ---
        if machine_name not in self.machine_profiles:
            return
        # Set axes
        machine=self.machine_profiles.get(machine_name)
        axes= machine.get("axes")
        machine_axes=[]
        for aaa in axes:
            if aaa.get("role") == "position" or aaa.get("role") == "rotation":
                machine_axes.append(aaa["name"])
        
        self.tracker.set_or_create_value(["machine","axes","value"],machine_axes)
        self.tracker.set_or_create_value(["machine","axes","meta[constraints[arity]]"],len(machine_axes))
        self.tracker.set_or_create_value(["machine","axis_count","value"],len(machine_axes))        
        # self.session["machine"]["axes"]["value"]=machine_axes
        # self.session["machine"]["axes"]["meta"]["constraints"]["arity"]=len(machine_axes)
        # self.session["machine"]["axis_count"]["value"]=len(machine_axes)
    
    def get_compatible_tools(self,machine_name):
        # --- 1. Validate existence ---
        if machine_name not in self.machine_profiles:
            return []

        compatible_tools=[]
        for tool,tool_def in self.tool_profiles.items():
            compatible_machines=tool_def.get("compatible_machines")
            if isinstance(compatible_machines,list) and machine_name in compatible_machines:
                compatible_tools.append(tool)
        return compatible_tools
    
    def get_compatible_techniques(self,tool_name):
        # --- 1. Validate existence ---
        if tool_name not in self.tool_profiles:
            return []

        compatible_techniques=[]
        for tech,tech_def in self.technique_profiles.items():
            compatible_tools=tech_def.get("compatible_tools")
            if isinstance(compatible_tools,list) and tool_name in compatible_tools:
                compatible_techniques.append(tech)
        return compatible_techniques
        

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
    