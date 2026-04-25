from PyQt6 import QtCore, QtGui, QtWidgets, QtSvg, QtSvgWidgets
from PyQt6.QtWidgets import *
import resources_rc
import class_treeview_functions
import class_struct_tracker
import class_struct_conditioner
from class_simulation_slider import TripleSlider,DualSliderWidget
import math
import tempfile
import os
import colorsys
import bisect
from collections import defaultdict

conditions={"rapid": "me_set('meta[hidden]',False) if node_get('rapid[Show[value]]') else me_set('meta[hidden]',True)",
            "linear": "me_set('meta[hidden]',False) if node_get('linear[Show[value]]') else me_set('meta[hidden]',True)",
            "arc_cw": "me_set('meta[hidden]',False) if node_get('arc_cw[Show[value]]') else me_set('meta[hidden]',True)",
            "arc_ccw": "me_set('meta[hidden]',False) if node_get('arc_ccw[Show[value]]') else me_set('meta[hidden]',True)",
            "frame": "me_set('meta[hidden]', not node_get('frame[Show[value]]'))",
            "frame_fill": "me_set('meta[hidden]', not node_get('frame[Fill[value]]'))",
            "grid": "me_set('meta[hidden]',False) if node_get('grid[Show[value]]') else me_set('meta[hidden]',True)",
            "axes": "me_set('meta[hidden]',False) if node_get('axes[Show[value]]') else me_set('meta[hidden]',True)",
            "rulers": "me_set('meta[hidden]',False) if node_get('rulers[Show[value]]') else me_set('meta[hidden]',True)",
            "render": "me_set('meta[hidden]',False) if node_get('render[Show[value]]') else me_set('meta[hidden]',True)",
            }
STYLE_STRUCT_EXAMPLE={
        "rapid": {"children":[                  
                {"Show": {"value": True, "type": "bool", "unit":"", "meta": {}}},
                {"Style": {"meta": {"hidden":False, "conditions": conditions["rapid"]}, 
                           "children":[
                        {"Color Mapping Mode": {"value": "none", "type": "str", "meta": {"hidden":False, "editable":True, "options":["none","feedrate","power","z heights"], "conditions": conditions["rapid"]}}},                        
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"], "conditions": conditions["rapid"]}}},
                        {"Pen": {"value": "#35F565", "type": "color", "meta": {"hidden":False, "editable":True, "conditions": conditions["rapid"]}}},
                        {"Pen Width": {"value": 0.3, "type": "float",  "unit":"[0.1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0.1, "max": 5}, "conditions": conditions["rapid"]}}},
                        {"Line Transparency": {"value": 180, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}, "conditions": conditions["rapid"]}}},
                        ]}},
            ]},
        "linear": {"children":[                  
                {"Show": {"value": True, "type": "bool", "unit":"", "meta": {}}},
                {"Style": {"meta": {"hidden":False, "conditions": conditions["linear"]}, 
                           "children":[
                        {"Color Mapping Mode": {"value": "none", "type": "str", "meta": {"hidden":False, "editable":True, "options":["none","feedrate","power","z heights"], "conditions": conditions["linear"]}}},                                                
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"], "conditions": conditions["linear"]}}},
                        {"Pen": {"value": "#c5301c", "type": "color", "meta": {"hidden":False, "editable":True, "conditions": conditions["linear"]}}},
                        {"Pen Width": {"value": 0.3, "type": "float",  "unit":"[0.1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0.1, "max": 5}, "conditions": conditions["linear"]}}},
                        {"Line Transparency": {"value": 180, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}, "conditions": conditions["linear"]}}},
                        ]}},
            ]},    
        "arc_cw": {"children":[                  
                {"Show": {"value": True, "type": "bool", "unit":"", "meta": {}}},
                {"Style": {"meta": {"hidden":False, "conditions": conditions["arc_cw"]}, 
                           "children":[
                        {"Color Mapping Mode": {"value": "none", "type": "str", "meta": {"hidden":False, "editable":True, "options":["none","feedrate","power","z heights"], "conditions": conditions["arc_cw"]}}},                                                
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"], "conditions": conditions["arc_cw"]}}},
                        {"Pen": {"value": "#4d0404", "type": "color", "meta": {"hidden":False, "editable":True, "conditions": conditions["arc_cw"]}}},
                        {"Pen Width": {"value": 0.3, "type": "float",  "unit":"[0.1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0.1, "max": 5}, "conditions": conditions["arc_cw"]}}},
                        {"Line Transparency": {"value": 180, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}, "conditions": conditions["arc_cw"]}}},
                        ]}},
            ]},
        "arc_ccw": {"children":[                  
                {"Show": {"value": True, "type": "bool", "unit":"", "meta": {}}},
                {"Style": {"meta": {"hidden":False, "conditions": conditions["arc_ccw"]}, 
                           "children":[    
                        {"Color Mapping Mode": {"value": "none", "type": "str", "meta": {"hidden":False, "editable":True, "options":["none","feedrate","power","z heights"], "conditions": conditions["arc_ccw"]}}},                    
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"], "conditions": conditions["arc_ccw"]}}},
                        {"Pen": {"value": "#4d0404", "type": "color", "meta": {"hidden":False, "editable":True, "conditions": conditions["arc_ccw"]}}},
                        {"Pen Width": {"value": 0.3, "type": "float",  "unit":"[0.1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0.1, "max": 5}, "conditions": conditions["arc_ccw"]}}},
                        {"Line Transparency": {"value": 180, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}, "conditions": conditions["arc_ccw"]}}},
                        ]}},
            ]},   
        "frame": {"children":[                  
                {"Show": {"value": True, "type": "bool", "unit":"", "meta": {}}},
                {"Fill": {"value": False, "type": "bool", "unit":"", "meta": {}}},
                {"Style": {"meta": {"hidden":False, "conditions": conditions["frame"]}, 
                           "children":[                        
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"], "conditions": conditions["frame"]}}},
                        {"Pen": {"value": "#a8e6a3", "type": "color", "meta": {"hidden":False, "editable":True, "conditions": conditions["frame"]}}},
                        {"Pen Width": {"value": 0.3, "type": "float",  "unit":"[0.1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0.1, "max": 5}, "conditions": conditions["frame"]}}},
                        {"Line Transparency": {"value": 60, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}, "conditions": conditions["frame"]}}},
                        {"Fill Color": {"value": "#a8e6a3", "type": "color", "meta": {"hidden":False, "editable":True, "conditions": conditions["frame_fill"]}}},
                        {"Fill Transparency": {"value": 120, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}, "conditions": conditions["frame_fill"]}}}
                        ]}},
            ]},
        "grid": {"children":[                  
                {"Show": {"value": True, "type": "bool", "unit":"", "meta": {}}},
                {"Style": {"meta": {"hidden":False, "conditions": conditions["grid"]}, 
                           "children":[                        
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"], "conditions": conditions["grid"]}}},
                        {"Pen": {"value": "#818181", "type": "color", "meta": {"hidden":False, "editable":True, "conditions": conditions["grid"]}}},
                        {"Pen Width": {"value": 0.4, "type": "float",  "unit":"[0.1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0.1, "max": 5}, "conditions": conditions["grid"]}}},
                        {"Line Transparency": {"value": 60, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}, "conditions": conditions["grid"]}}},
                        ]}},
            ]},
        "axes": {"children":[                  
                {"Show": {"value": True, "type": "bool", "unit":"", "meta": {}}},                
                {"Style": {"meta": {"hidden":False, "conditions": conditions["axes"]}, 
                           "children":[                        
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"], "conditions": conditions["axes"]}}},
                        {"Pen": {"value": "#127bb8", "type": "color", "meta": {"hidden":False, "editable":True, "conditions": conditions["axes"]}}},
                        {"Pen Width": {"value": 0.3, "type": "float",  "unit":"[0.1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0.1, "max": 5}, "conditions": conditions["axes"]}}},
                        {"Line Transparency": {"value": 233, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}, "conditions": conditions["axes"]}}},
                        ]}},
            ]},
        "rulers": {"children":[                  
                {"Show": {"value": True, "type": "bool", "unit":"", "meta": {}}},
                {"Style": {"meta": {"hidden":False, "conditions": conditions["rulers"]}, 
                           "children":[                        
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"], "conditions": conditions["rulers"]}}},
                        {"Pen": {"value": "#777777", "type": "color", "meta": {"hidden":False, "editable":True, "conditions": conditions["rulers"]}}},
                        {"Pen Width": {"value": 0.3, "type": "float",  "unit":"[0.1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0.1, "max": 5}, "conditions": conditions["rulers"]}}},
                        {"Line Transparency": {"value": 120, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}, "conditions": conditions["rulers"]}}},
                        ]}},
            ]}, 
        "render": {"children":[                  
                {"Show": {"value": True, "type": "bool", "unit":"", "meta": {}}},
                {"Show Rapid": {"value": False, "type": "bool", "unit":"", "meta": {}}},
                {"Show Linear": {"value": True, "type": "bool", "unit":"", "meta": {}}},
                {"Show ArcCW": {"value": True, "type": "bool", "unit":"", "meta": {}}},
                {"Show ArcCCW": {"value": True, "type": "bool", "unit":"", "meta": {}}},
                {"Style": {"meta": {"hidden":False, "conditions": conditions["render"]}, 
                           "children":[                        
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"], "conditions": conditions["render"]}}},
                        {"Pen": {"value": "#BBBBBB", "type": "color", "meta": {"hidden":False, "editable":True, "conditions": conditions["render"]}}},
                        {"Pen Width": {"value": 0.3, "type": "float",  "unit":"[0.1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0.1, "max": 5}, "conditions": conditions["render"]}}},
                        {"Line Transparency": {"value": 120, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}, "conditions": conditions["render"]}}},
                        ]}},
            ]},            
        }

FIELDS_POSITION=[
    {"name": "ITEM",  "editable": False, "selectable": True,  "hidden": False},
    {"name": "VALUE", "editable": True,  "selectable": True,  "hidden": False},
    {"name": "TYPE",  "editable": False, "selectable": False, "hidden": True},
    {"name": "UNIT",  "editable": False, "selectable": True, "hidden": True},
    {"name": "INFO",  "editable": True, "selectable": True, "hidden": True},
]

LINE_MAP = {
            "none": QtCore.Qt.PenStyle.NoPen,
            "solid": QtCore.Qt.PenStyle.SolidLine,
            "dash": QtCore.Qt.PenStyle.DashLine,
            "dot": QtCore.Qt.PenStyle.DotLine,
            "dashdot": QtCore.Qt.PenStyle.DashDotLine,
            "dashdotdot": QtCore.Qt.PenStyle.DashDotDotLine,
        }

# Add logger
vis_fun_name="Visualizer"
from class_LogHandler import get_appPath, LM ,init_logger_manager
try:
    log = LM.get_logger_with_handler(vis_fun_name,
                                     "debug",
                                     True,
                                     "%(asctime)s [%(levelname)s] (%(name)s) %(message)s")
    log.info(f"{vis_fun_name} Logger started")
except (AttributeError, ImportError):
    LM = init_logger_manager(None)
    log = LM.get_logger(__name__)
    log.info("Application starting...")

from dataclasses import dataclass

@dataclass(slots=True)
class Motion:
    raw: str = ""  # original line
    type: str = "other" # "rapid", "linear", "arc_cw", "arc_ccw", "other"
    x: float | None = None  # linear
    y: float | None = None  # linear
    z: float | None = None  # linear
    a: float | None = None  # rotary
    b: float | None = None  # rotary
    c: float | None = None  # rotary
    i: float | None = None  # arcs
    j: float | None = None  # arcs
    k: float | None = None  # arcs
    h: float | None = None  # helical
    r: float | None = None  # arcs radii
    f: float | None = None  # feedrate
    s: float | None = None  # Power
    e: float | None = None  # Extruder
    cmd: str = ""
    comment: str = ""
    layer_id: int | None = None  # internal layer assignment

@dataclass(slots=True)
class Position:
    type: str = "other" # "rapid", "linear", "arc_cw", "arc_ccw", "other"
    x: float | None = None  # linear
    y: float | None = None  # linear
    z: float | None = None  # linear
    f: float | None = None  # feedrate
    s: float | None = None  # Power
    e: float | None = None  # Extruder
    layer_id: int | None = None  # internal layer assignment
    m_index: int | None = None  # motions index for position

class GCodeVisualizerDialog(QtWidgets.QMainWindow):
    closed = QtCore.pyqtSignal()
    stream_play = QtCore.pyqtSignal()
    stream_pause = QtCore.pyqtSignal()
    stream_stop = QtCore.pyqtSignal()

    def __init__(self, parent=None, style_struct=None):
        super().__init__(parent)

        self.setWindowTitle("G‑code Visualizer")
        self.resize(1100, 700)

        # Define main structure or use example
        if isinstance(style_struct,dict):
            self.style_struct=style_struct
        else:
            self.style_struct=STYLE_STRUCT_EXAMPLE
        self._do_evaluation=False
        # -------------------------
        # Internal data
        # -------------------------
        self.motions = []   # list of Motion objects
        self.positions = [] # lsit of Position objects
        self.svg_item = None
        self.dynamic_items = []
        self.static_items = []
        # Simulation
        self.last_x = 0
        self.last_y = 0
        self.sim_index = 0
        self.job_xmin=-333
        self.job_xmax=333
        self.job_ymin=-333
        self.job_ymax=333
        self.svg_height = 666
        maxlevel=9999
        maxlevel = 1000
        self.layer_overlay = {
            "work_box":       maxlevel - 1000,
            "grid":        maxlevel - 900,
            "frame":       maxlevel - 800,
            "rulers":      maxlevel - 700,
            "axes":        maxlevel - 700,
            "render_svg":  maxlevel - 500,
            "simulation":  maxlevel - 200,
            "stream":      maxlevel - 200,
            "toolhead":    maxlevel,
        }
        self.fixed_layer_mapping={
            "rapid":1, 
            "linear":2, 
            "arc_cw":3, 
            "arc_ccw":4,
            "other":0
        }
        self.motion_limits={}
        self._persistant_values={}
        self.sim_running = False
        self.sim_timer = QtCore.QTimer()
        self.sim_timer.setInterval(30)  # 30ms per step (~33 FPS)
        self.sim_timer.timeout.connect(self.sim_step_forward)
        self.stream_running=False
        self.executed_count=0
        self.last_modal=None
        self.show_status={}
        self.simulation_status={
            "is_stop":True,
            "is_play":False,
            "is_pause":False,
            "is_sliding":False,
            }
        self.motion_item = None
        self.batch_size = 3000
        self.svg_batches = {}  # batch_index → QGraphicsSvgItem
        self.batch_ranges = [] # list of (start_index, end_index)
        self.batch_manager = {}
        self.movement_index = 0
        self.movement_batches = []
        # ------------------------
        self.axes=None
        self.frame=None
        self.ruler=None
        self.grid=None
        self._syncing_ui=False
        # -------------------------
        # Toolbar
        # -------------------------
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(24, 24))

        self.action_open = QtGui.QAction(QtGui.QIcon(":/img/open-file-icon.png"), "Open", self)
        self.action_play = QtGui.QAction(QtGui.QIcon(":/img/Button-Play-icon.png"), "Play", self)
        self.action_pause = QtGui.QAction(QtGui.QIcon(":/img/Button-Pause-icon.png"), "Pause", self)
        self.action_stop = QtGui.QAction(QtGui.QIcon(":/img/Actions-process-stop-icon.png"), "Stop", self)
        self.action_zoom_in = QtGui.QAction(QtGui.QIcon(":/img/Plus-icon.png"), "Zoom In", self)
        self.action_zoom_out = QtGui.QAction(QtGui.QIcon(":/img/Minus-icon.png"), "Zoom Out", self)
        self.action_fit = QtGui.QAction(QtGui.QIcon(":/img/move-icon.png"), "Fit", self)

        self.toolbar.addAction(self.action_open)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_play)
        self.toolbar.addAction(self.action_pause)
        self.toolbar.addAction(self.action_stop)

        self.zoom_toolbar = QtWidgets.QToolBar("Zoom")
        self.zoom_toolbar.setIconSize(QtCore.QSize(24, 24))
        self.zoom_toolbar.addAction(self.action_zoom_in)
        self.zoom_toolbar.addAction(self.action_zoom_out)
        self.zoom_toolbar.addAction(self.action_fit)

        top_toolbar_layout = QtWidgets.QHBoxLayout()
        top_toolbar_layout.addWidget(self.toolbar)
        top_toolbar_layout.addStretch()
        top_toolbar_layout.addWidget(self.zoom_toolbar)

        # -------------------------
        # Left: G‑code table
        # -------------------------
        table_tree_layout = QtWidgets.QVBoxLayout()
        self.table = QtWidgets.QTableView()
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)

        # self.table = QtWidgets.QTableWidget()
        # self.table.setColumnCount(4)
        # self.table.setHorizontalHeaderLabels(["Line", "Command", "Params", "Status"])
        # self.table.horizontalHeader().setStretchLastSection(True)
        # self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        # -------------------------
        # Left: Style Treeview
        # -------------------------
        self.style_tree = QtWidgets.QTreeView(self)
        self.style_tree.setMinimumHeight(120) 
        # -------------------------
        # Left side: table + style tree in a vertical splitter
        # -------------------------
        left_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        left_splitter.addWidget(self.table)
        left_splitter.addWidget(self.style_tree)

        # Hide the style tree by default
        
        left_splitter.setStretchFactor(0, 1)
        left_splitter.setStretchFactor(1, 0)

        # optional hide
        # self.style_tree.setVisible(False)
        # self.style_tree.hide()

        # -------------------------
        # Right: Canvas (QGraphicsView)
        # -------------------------
        self.scene = QtWidgets.QGraphicsScene()
        # self.view = QtWidgets.QGraphicsView(self.scene)
        self.view = GraphicsView(self.scene)
        # Set Y axis towards up
        self.view.setTransform(QtGui.QTransform(1, 0, 0, -1, 0, 0))

        self.view.setRenderHints(QtGui.QPainter.RenderHint.Antialiasing | QtGui.QPainter.RenderHint.SmoothPixmapTransform)
        self.view.mouseMoved.connect(self.update_cursor_status)

        # -------------------------
        # Main horizontal splitter
        # -------------------------
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(self.view)

        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)

        splitter_layout = QtWidgets.QVBoxLayout()
        splitter_layout.addWidget(main_splitter)
        splitter_layout.setStretch(0, 1)

        # -------------------------
        # Status bar
        # -------------------------
        status_layout = QtWidgets.QHBoxLayout()
        self.status = QtWidgets.QLabel("X:0  Y:0  Z:0  Power:0  State:Idle")
        self.tool_label = QtWidgets.QLabel("Tool: X=0 Y=0")
        self.machine_label = QtWidgets.QLabel("Machine X:0  Y:0  Z:0")
        self.cursor_label = QtWidgets.QLabel("Cursor: X:0  Y:0")

        status_layout.addWidget(self.status)
        status_layout.addStretch()
        status_layout.addWidget(self.machine_label)
        status_layout.addStretch()
        status_layout.addWidget(self.tool_label)
        status_layout.addStretch()
        status_layout.addWidget(self.cursor_label)
        
        # -------------------------
        # Simulation toolbar
        # -------------------------
        self.sim_toolbar = QtWidgets.QToolBar()
        self.sim_toolbar.setIconSize(QtCore.QSize(24, 24))

        self.sim_action_ini = QtGui.QAction(QtGui.QIcon(":/img/Ahmadhania-Spherical-Fast-backward.128.png"), "Fast Backward", self)
        self.sim_action_previous = QtGui.QAction(QtGui.QIcon(":/img/Ahmadhania-Spherical-Previous-track.128.png"), "Previous", self)
        self.sim_action_play = QtGui.QAction(QtGui.QIcon(":/img/Ahmadhania-Spherical-Play.128.png"), "Play", self)
        self.sim_action_pause = QtGui.QAction(QtGui.QIcon(":/img/Ahmadhania-Spherical-Pause.128.png"), "Pause", self)
        self.sim_action_stop = QtGui.QAction(QtGui.QIcon(":/img/Ahmadhania-Spherical-Stop.128.png"), "Stop", self)
        self.sim_action_next = QtGui.QAction(QtGui.QIcon(":/img/Ahmadhania-Spherical-Next-track.128.png"), "Next", self)
        self.sim_action_end = QtGui.QAction(QtGui.QIcon(":/img/Ahmadhania-Spherical-Fast-forward.128.png"), "Fast Forward", self)
        self.sim_action_next_layer = QtGui.QAction(QtGui.QIcon(":/img/Ahmadhania-Spherical-Scroll-up.128.png"), "Next Layer", self)
        self.sim_action_prev_layer = QtGui.QAction(QtGui.QIcon(":/img/Ahmadhania-Spherical-Scroll-down.128.png"), "Previous Layer", self)
        self.sim_action_clean_paths = QtGui.QAction(QtGui.QIcon(":/img/Ahmadhania-Spherical-Write.128.png"), "Clean Paths", self)
        # Slider
        self.speed_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 200)
        self.speed_slider.setValue(30)
        # Spinboxes
        self.sim_start_spin = QtWidgets.QSpinBox()
        self.sim_start_spin.setRange(0, 0)
        self.sim_start_spin.setPrefix("Start: ")

        self.sim_end_spin = QtWidgets.QSpinBox()
        self.sim_end_spin.setRange(0, 0)
        self.sim_end_spin.setPrefix("End: ")

        self.sim_pos_spin = QtWidgets.QSpinBox()
        self.sim_pos_spin.setRange(0, 0)
        self.sim_pos_spin.setPrefix("Line: ")

        # Layer selector
        self.layer_combo = QtWidgets.QComboBox()
        self.layer_combo.setMinimumWidth(80)

        # Simulate only this layer
        self.layer_only_check = QtWidgets.QCheckBox("Layer Only")
        self.center_check = QtWidgets.QCheckBox("Center")

        # Add to toolbar
        self.sim_toolbar.addAction(self.sim_action_ini)
        self.sim_toolbar.addAction(self.sim_action_previous)
        self.sim_toolbar.addAction(self.sim_action_next)
        self.sim_toolbar.addAction(self.sim_action_end)
        self.sim_toolbar.addSeparator()
        self.sim_toolbar.addAction(self.sim_action_play)
        self.sim_toolbar.addAction(self.sim_action_pause)
        self.sim_toolbar.addAction(self.sim_action_stop)
        self.sim_toolbar.addSeparator()
        self.sim_toolbar.addAction(self.sim_action_clean_paths)
        self.sim_toolbar.addSeparator()
        self.sim_toolbar.addWidget(self.speed_slider)
        self.sim_toolbar.addSeparator()
        self.sim_toolbar.addWidget(QtWidgets.QLabel("Layer:"))
        self.sim_toolbar.addWidget(self.layer_combo)
        self.sim_toolbar.addAction(self.sim_action_prev_layer)
        self.sim_toolbar.addAction(self.sim_action_next_layer)
        self.sim_toolbar.addWidget(self.layer_only_check)
        self.sim_toolbar.addSeparator()
        self.sim_toolbar.addWidget(self.sim_start_spin)
        self.sim_toolbar.addWidget(self.sim_end_spin)
        self.sim_toolbar.addWidget(self.sim_pos_spin)
        self.sim_toolbar.addSeparator()
        self.sim_toolbar.addWidget(self.center_check)
        # -------------------------
        # Grid toolbar
        # -------------------------
        self.grid_toolbar = QtWidgets.QToolBar("Grid")
        self.addToolBar(self.grid_toolbar)
        self.grid_toolbar.setIconSize(QtCore.QSize(24, 24))

        self.color_mapping_mode_combo = QtWidgets.QComboBox()
        self.color_mapping_mode_combo.setMinimumWidth(80)
        self.color_mapping_mode_combo.addItem("Fixed", "fixed")
        self.color_mapping_mode_combo.addItem("Power", "power")
        self.color_mapping_mode_combo.addItem("Feedrate", "feedrate")
        self.color_mapping_mode_combo.addItem("Z heights", "layerheight")
        self.color_mapping_mode_combo.addItem("None", "none")
        index = self.color_mapping_mode_combo.currentIndex()
        mode = self.color_mapping_mode_combo.itemData(index)
        self.color_mapping_mode=mode

        self.grid_toggle = QtWidgets.QCheckBox("Grid")
        self.grid_toggle.setChecked(True)
        
        self.grid_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.grid_slider.setRange(1, 50)   # 1mm to 50mm
        self.grid_slider.setValue(10)
        
        self.frame_toggle = QtWidgets.QCheckBox("Frame")
        self.frame_toggle.setChecked(True)
        
        self.ruler_toggle = QtWidgets.QCheckBox("Rulers")
        self.ruler_toggle.setChecked(True)

        self.axes_toggle = QtWidgets.QCheckBox("Axes")
        self.axes_toggle.setChecked(True)
        
        # Add to toolbar
        self.grid_toolbar.addWidget(self.color_mapping_mode_combo)
        self.grid_toolbar.addWidget(self.grid_toggle)
        self.grid_toolbar.addWidget(self.grid_slider)
        self.grid_toolbar.addWidget(self.frame_toggle)
        self.grid_toolbar.addWidget(self.ruler_toggle)
        self.grid_toolbar.addWidget(self.axes_toggle)
        #Add to top layout
        top_toolbar_layout.addWidget(self.grid_toolbar)

        # -------------------------
        # Progress bars
        # -------------------------
        # When connecting to stream
        # self.buffer_progress = QProgressBar()
        # self.buffer_progress.setRange(0, len(self.motions))
        # self.buffer_progress.setValue(0)
        self.job_progress = QProgressBar()
        self.job_progress.setRange(0, len(self.motions))
        
        progressbar_layout = QtWidgets.QVBoxLayout()
        progressbar_layout.addWidget(self.job_progress)
        # -------------------------
        # Triple slider
        # -------------------------
        # self.sim_slider = TripleSlider()
        self.sim_slider =DualSliderWidget() #<- nicer
        progressbar_layout.addWidget(self.sim_slider)

        # -------------------------
        # Main Layout
        # -------------------------
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        layout = QtWidgets.QVBoxLayout(central)
        layout.addLayout(top_toolbar_layout)
        layout.addLayout(splitter_layout)
        layout.addWidget(self.sim_toolbar)
        layout.addLayout(progressbar_layout) 
        layout.addLayout(status_layout)   
        
        # Connect actions
        self.render_actions_connect()
        # style tree setup
        self._build_style_configuration_tree()
        self._build_style_dict()
        # set color mode
        index = self.color_mapping_mode_combo.currentIndex()
        self.on_color_mapping_mode_changed(index)

    def _build_style_configuration_tree(self):
        """Initialize and configure the style tree, delegates, condition engine, and context menu.

        Sets up treeview behavior, connects edit signals, evaluates conditions, and refreshes the UI.
        """
        self._do_evaluation=False
        self.s_tv=class_treeview_functions.TreeviewFunctions(self.style_tree,self.style_struct,FIELDS_POSITION)
        # attach delegate to VALUE column (1)
        delegate = class_treeview_functions.TypedItemDelegate(self.s_tv)
        self.style_tree.setItemDelegateForColumn(1, delegate)
        self.s_tv.data_change[list,object,str,str].connect(self.on_tree_item_edited)
        self.s_tv.struct_data_change[list,object,str,str].connect(self.on_struct_item_edited)
        #self.s_tv.expand_to_depth(1) #333) #Expand all
        # Condition Engine
        self.s_ce=class_struct_conditioner.ConditionEngine(self.s_tv.tracker)
        self._evaluate_conditions()
        
        # Add cache tooltip, icons, backgrounds, styles
        # self.s_tv.set_icons_cache(self.all_icons_dict)
        # self.s_tv.set_style_cache(style_dict)

        # Right click Menu 
        self.s_tv.treeviewobj.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.s_tv.treeviewobj.customContextMenuRequested.connect(self.s_tv._on_context_menu)
        #self.s_tv.item_right_clicked.connect(self.on_item_right_clicked)
        
        self.s_tv.do_refresh()
    
    def _build_style_dict(self):
        """Build the style dictionary from the validated structure tree.

        Populates style entries for each child node and updates visibility states.
        """

        val_dict=self.s_ce.tracker.validate_node([])
        self.style_dict = {}
        if val_dict["found"] and val_dict["is_root"]:
            if val_dict["has_children"]:
                for child in val_dict["children_keys"]:
                    # Build object
                    m_show=self.s_ce.tracker.get_value([child,"Show","value"])
                    m_fill=self.s_ce.tracker.get_value([child,"Fill","value"])
                    ostyle_dict=self._get_style_dict_from_track([child])
                    self.style_dict.update({child:{"Show":m_show,"Fill":m_fill,"Style":ostyle_dict}})  
                    self.show_status[child]=m_show
                self.set_showing() # sets checkboxes according to self.show_status 
    
    def apply_style_changes(self, child):
        """Apply the appropriate style update based on the given child key.

        Dispatches to the specific style‑application method for the selected element.
        """
        if child == "grid":
            self.apply_grid_style()
        elif child == "rulers":
            self.apply_ruler_style()
        elif child == "axes":
            self.apply_axes_style()
        elif child == "frame":
            self.apply_frame_style()
        elif child == "render":
            self.apply_render_style()

    def _get_style_dict_from_track(self, track: list[str]) -> dict:
        """Return a style dictionary by reading tracked values with defaults applied.

        Extracts style-related fields from the tracker and normalizes missing entries.
        """
        def get(path, default):
            val = self.s_ce.tracker.get_value(path)
            return default if val in (None, "", []) else val

        base = track + ["Style"]

        return {
            "Color Mapping Mode": get(base + ["Color Mapping Mode", "value"], self.color_mapping_mode),
            "Line Type":          get(base + ["Line Type", "value"], "solid"),
            "Fill Color":         get(base + ["Fill Color", "value"], "#1570D8"),
            "Fill Transparency":  get(base + ["Fill Transparency", "value"], 77),
            "Pen":                get(base + ["Pen", "value"], "#000000"),
            "Pen Width":          float(get(base + ["Pen Width", "value"], 0.3)),
            "Line Transparency":  get(base + ["Line Transparency", "value"], 77),
        }

    def _normalize_motion_parameter(self, key, value):
        """Normalize a motion parameter to a 0–1 range based on configured limits.

        Returns 0 if the key is unknown or the range is invalid.
        """
        if key not in self.motion_limits:
            return 0.0
        min_v, max_v = self.motion_limits[key]
        if max_v == min_v:
            return 0.0
        return (value - min_v) / (max_v - min_v)
    
    def _get_norm_color(self, key, value, base_color, use_hue):
        """Compute a normalized QColor based on motion value and mapping mode.

        Maps the parameter to either hue or brightness using the normalized range.
        """
        norm = self._normalize_motion_parameter(key, value)

        if use_hue:
            # Hue mapping (blue → red)
            hue = int((1 - norm) * 240)
            return QtGui.QColor.fromHsv(hue, 255, 255)

        else:
            # Brightness mapping (value channel)
            h = base_color.hue()
            s = base_color.saturation()
            v = int(norm * 255)
            return QtGui.QColor.fromHsv(h, s, v)

    def make_pen_from_style(self, style: dict, m: Motion=None, use_hue=False) -> QtGui.QPen:
        """Create a QPen using the new hue/brightness mapping model."""
        pen = QtGui.QPen()
        pen.setWidthF(style["Pen Width"])
        # Base color chosen by the user
        base_color = QtGui.QColor(style["Pen"])
        # Default color before mapping
        color = QtGui.QColor(base_color)
        # Determine mapping mode
        mode = style.get("Color Mapping Mode", self.color_mapping_mode)
        if m is not None:
            # If movement type is unknown → no mapping
            if m.type not in ("rapid", "linear", "arc_cw", "arc_ccw") or style["Line Type"] == "none":
                mode = "none"
            movement_hue = base_color.hue()
            # -----------------------------
            # FIXED MODE
            # -----------------------------
            if mode == "fixed":
                # Start with full brightness
                norm_total = 1.0
                # Layer contribution
                if hasattr(m, "layer_id") and m.layer_id is not None:
                    norm_layer = m.layer_id / max(1, len(self.layers))
                    norm_total *= norm_layer
                # Power contribution
                if hasattr(m, "s") and m.s is not None:
                    norm_s = self._normalize_motion_parameter("S", m.s)
                    norm_total *= norm_s
                # Feedrate contribution
                if hasattr(m, "f") and m.f is not None:
                    norm_f = self._normalize_motion_parameter("F", m.f)
                    norm_total *= norm_f
                # Final mapped color
                color = self.map_color(base_color, norm_total, movement_hue)

            # -----------------------------
            # POWER MODE
            # -----------------------------
            elif mode == "power" and hasattr(m, "s") and m.s is not None:
                norm = self._normalize_motion_parameter("S", m.s)
                color = self.map_color(base_color, norm, movement_hue if use_hue else None)

            # -----------------------------
            # FEEDRATE MODE
            # -----------------------------
            elif mode == "feedrate" and hasattr(m, "f") and m.f is not None:
                norm = self._normalize_motion_parameter("F", m.f)
                color = self.map_color(base_color, norm, movement_hue if use_hue else None)

            # -----------------------------
            # LAYER HEIGHT MODE
            # -----------------------------
            elif mode == "layerheight" and hasattr(m, "z") and m.z is not None:
                norm = self._normalize_motion_parameter("Z", m.z)
                color = self.map_color(base_color, norm, movement_hue if use_hue else None)

            # -----------------------------
            # NONE MODE (hide pen)
            # -----------------------------
            elif mode == "none":
                pen.setStyle(QtCore.Qt.PenStyle.NoPen)
                return pen

        # Apply transparency
        color.setAlpha(style["Line Transparency"])
        pen.setColor(color)

        # -----------------------------
        # Line type
        # -----------------------------
        lt = style["Line Type"]
        if lt == "dash":
            pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        elif lt == "dot":
            pen.setStyle(QtCore.Qt.PenStyle.DotLine)
        elif lt == "dashdot":
            pen.setStyle(QtCore.Qt.PenStyle.DashDotLine)
        elif lt == "dashdotdot":
            pen.setStyle(QtCore.Qt.PenStyle.DashDotDotLine)
        elif lt == "none":
            pen.setStyle(QtCore.Qt.PenStyle.NoPen)
        else:
            pen.setStyle(QtCore.Qt.PenStyle.SolidLine)

        return pen


    # when streaming for buffer
    # def send_next_line(self):
    #     line = self.gcode_lines[self.send_index]
    #     self.serial.write(line.encode() + b"\n")

    #     self.send_index += 1
    #     self.buffer_progress.setValue(self.send_index)

    @QtCore.pyqtSlot(list, object, str, str)
    def on_struct_item_edited(self, track, value, typestr, subtype):
        # Decide what to do with item value changed from code
        if self._do_evaluation:
            self._evaluate_conditions()

    @QtCore.pyqtSlot(list, object, object, str, str)
    def on_tree_item_edited_old_new(self, track, old_value, new_value, typestr, subtype):
        # Decide what to do with item value changed from user with old value
        pass

    @QtCore.pyqtSlot(list, object, str, str)
    def on_tree_item_edited(self, track, value, typestr, subtype):
        # Decide what to do with item value changed
        self._evaluate_conditions()
        name=track[0]
        obj=self._get_obj_from_track(track)
        if obj:            
            self._build_style_dict()
            self.apply_style_changes(name)
        
    def on_show_fill_changed(self, child):
        """Handle changes to a child's Show/Fill settings and update config if values differ.

        Compares new tracker values with stored ones and triggers condition evaluation when updated.
        """
        # Values changed evaluate the conditions
        track_show=[child,"Show","value"]
        track_fill=[child,"Fill","value"]
        child_dict=self.style_dict.get(child)
        if not isinstance(child_dict,dict):
            return
        m_show=self.s_ce.tracker.get_value(track_show)
        m_fill=self.s_ce.tracker.get_value(track_fill)
        old_show=child_dict.get("Show") 
        old_fill=child_dict.get("Fill")
        if old_show != m_show:
            if not self._change_setting_trigger_evaluate_conditions(track_show,m_show):
                log.warning(f"Unable to set {m_show} to {track_show}")
        if old_fill!=m_fill:
            if not self._change_setting_trigger_evaluate_conditions(track_fill,m_fill):
                log.warning(f"Unable to set {m_fill} to {track_fill}")
    
    def _change_setting_trigger_evaluate_conditions(self, track, value):
        """Set a tracked value and re-evaluate conditions if the update succeeds.

        Returns True if the value was applied to the tracker.
        """
        self._do_evaluation=False
        was_set=self.s_tv.tracker.set_value(track,value)
        if was_set:
            self._evaluate_conditions()
        # self._do_evaluation=False
        return was_set

    def _get_obj_from_track(self, track):
        """Return the style‑dictionary entry matching the given track's root key.

        Searches style_dict for the object whose name matches track[0].
        """
        for name,obj in self.style_dict.items():
            if name == track[0]:
                return obj
        return None   
    
    def _evaluate_conditions(self):
        """Evaluate condition rules and refresh the treeview when changes occur.

        Rebuilds UI state, restoring expansion and selection after condition updates.
        """
        do_eval=self._do_evaluation
        self._do_evaluation=False
        evaluated = self.s_ce.evaluate_conditions_in_a_node(self.s_tv.tracker.get_root())
        if evaluated or do_eval:
            expanded = self.s_tv.get_expanded_paths()
            selected = self.s_tv.get_selected_paths()
            # Delay the refresh AND the restore
            def delayed_refresh():
                self.s_tv.do_refresh()
                self.s_tv.restore_expanded_paths(expanded)
                self.s_tv.restore_selected_paths(selected)
                self.s_tv.treeview_fit_to_contents(0)
                # Important Clear circular reference flag
                self.s_tv.tracker.remove_property_from_all_nodes(self.s_tv.tracker.get_root(),"__conditions__applied__")
            # Need to wait until all data changes are applied.
            QtCore.QTimer.singleShot(0, delayed_refresh)

    def load_motions(self, motions):
        """Load a new motion list into the viewer and rebuild all scene elements.

        Resets state, regenerates static items (grid, axes, rulers, frame), rebuilds layers and batches,
        redraws the full toolpath, updates simulation ranges and UI controls, and fits the view to the
        newly computed scene bounds.
        """
        self.last_x = 0
        self.last_y = 0
        self.motions = motions
        self._motion_index_=None
        # Clear dynamic items only
        # Clear EVERYTHING (static + dynamic) 
        self.clear_scene(clear_all=True)
        # -------------------------
        # Job Box, Grid, axes, Rulers
        # -------------------------
        self.add_toolhead()
        self.add_frame()
        self.add_work_box()
        self.add_grid()
        self.add_axes()
        self.add_rulers()
        # Set visibility
        self.set_showing()
        self.apply_all_styles()
        # Set scene borders after generating the items
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        # Build table
        self.populate_table()
        # Build layers (IMPORTANT)
        self.build_layers()
        # Draw full static toolpath
        self.render_svg(do_positions=True)
        # build_batches
        self.build_batches()
        # Reset simulation ranges
        max_index = len(motions) - 1
        self.sim_start_spin.setRange(0, max_index)
        self.sim_end_spin.setRange(0, max_index)
        self.sim_pos_spin.setRange(0, max_index)
        self.sim_slider.setRange(0,max_index)
        self.sim_end_spin.setValue(max_index)

        # Reset simulation index
        self.sim_index = 0
        self.redraw_sim_position()
        # Set progress bar
        self.update_job_progressbar(self.sim_index,end=self.sim_end_spin.value(),start=self.sim_start_spin.value())
        #Wait other objects to load
        self.setup_triple_slider()
        #Fit view
        self.fit_view()

    def setup_triple_slider(self):
        """Sync the triple‑slider widget with the current simulation start, end, and position values."""
        self.sim_slider.setStart(self.sim_start_spin.value())
        self.sim_slider.setEnd(self.sim_end_spin.value())
        self.sim_slider.setPosition(self.sim_pos_spin.value())

    def compute_bounds(self):
        """Compute the min/max XY bounds of all motions.

        Returns a fallback bounding box if no valid coordinates exist.
        """
        xs = []
        ys = []
        for m in self.motions:
            if m.x is not None:
                xs.append(m.x)
            if m.y is not None:
                ys.append(m.y)

        if not xs or not ys:
            return (-100, -100, 100, 100)  # fallback

        return (min(xs), min(ys), max(xs), max(ys))

    def populate_table(self):
        """Populate the G‑code table with a new model and connect selection events."""
        # Attach Treeview model
        self.model = GCodeTableModel(self.motions)
        self.table.setModel(self.model)
        # connect selection
        self.table.selectionModel().selectionChanged.connect(self.on_table_selection)
    
    def select_table_position(self, row):
        """Select and center the given table row in the view.

        Highlights the row and scrolls it into the middle of the table.
        """
        # row is an int
        index = self.model.index(row, 0)
        # Select the row
        self.table.selectRow(row)
        # Scroll to the index
        self.table.scrollTo(index, QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter)


    def render_actions_connect(self):
        """Connect all UI actions, toolbar controls, simulation commands, and slider/spinbox sync events.

        Wires up file actions, zoom controls, simulation playback, layer navigation, grid/frame toggles,
        color‑mapping options, and triple‑slider synchronization.
        """
        self.action_open.triggered.connect(self.open_file)
        self.action_zoom_in.triggered.connect(lambda: self.view.scale(1.2, 1.2))
        self.action_zoom_out.triggered.connect(lambda: self.view.scale(0.8, 0.8))
        self.action_fit.triggered.connect(self.fit_view)        
        self.view.mouseMoved.connect(self.update_cursor_status)
        self.action_play.triggered.connect(self.play_pressed)
        self.action_stop.triggered.connect(self.stop_pressed)
        self.action_pause.triggered.connect(self.pause_pressed)
        # Simulation
        self.sim_action_play.triggered.connect(self.sim_play)
        self.sim_action_pause.triggered.connect(self.sim_pause)
        self.sim_action_stop.triggered.connect(self.sim_stop)
        self.sim_action_next.triggered.connect(self.sim_1_step_forward)
        self.sim_action_previous.triggered.connect(self.sim_step_backward)
        self.sim_action_ini.triggered.connect(self.sim_jump_start)
        self.sim_action_end.triggered.connect(self.sim_jump_end)
        self.sim_action_clean_paths.triggered.connect(self.clean_paths)

        self.speed_slider.valueChanged.connect(lambda v: self.sim_timer.setInterval(v))
        self.sim_pos_spin.valueChanged.connect(self.sim_jump_to)

        # Table Connection when model is created

        # layers 
        self.sim_action_next_layer.triggered.connect(self.next_layer)
        self.sim_action_prev_layer.triggered.connect(self.prev_layer)
        self.layer_combo.currentIndexChanged.connect(self.layer_changed)
        self.layer_only_check.stateChanged.connect(self.layer_only_changed)
        # grid toolbar
        self.color_mapping_mode_combo.currentIndexChanged.connect(self.on_color_mapping_mode_changed)
        self.grid_toggle.stateChanged.connect(self.on_grid_toggle_clicked)
        self.grid_slider.valueChanged.connect(self.update_grid_spacing)
        self.frame_toggle.stateChanged.connect(self.on_frame_toggle_clicked)
        self.ruler_toggle.stateChanged.connect(self.on_rulers_toggle_clicked)
        self.axes_toggle.stateChanged.connect(self.on_axes_toggle_clicked)
        #Triple slider
        # Sync slider → spinboxes
        self.sim_slider.startChanged.connect(self.sim_start_spin.setValue)
        self.sim_slider.endChanged.connect(self.sim_end_spin.setValue)
        self.sim_slider.posChanged.connect(self.on_pos_slider_position_changed)

        # Sync spinboxes → slider
        self.sim_start_spin.valueChanged.connect(self.sim_slider.setStart)
        self.sim_end_spin.valueChanged.connect(self.sim_slider.setEnd)
        self.sim_pos_spin.valueChanged.connect(self.sim_slider.setPosition)

    def on_pos_slider_position_changed(self, value: int):
        """Update the simulation position while suppressing redraw triggers.

        Syncs the position spinbox with the slider without firing simulation updates.
        """ 
        self.simulation_status["is_sliding"]=True
        self.blockSignals(True)
        self.sim_pos_spin.setValue(value)
        self.blockSignals(False)
        self.simulation_status["is_sliding"]=False

    def fit_view(self):
        """Fit the scene into the viewport using padded motion bounds.

        Computes padded XY limits and adjusts the view to maintain aspect ratio.
        """
        pxmin, pymin, pxmax, pymax = self.bounds_padded(0.2)
        self.view.fitInView(QtCore.QRectF(pxmin, pymin, pxmax - pxmin, pymax - pymin),
                            QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        # self.view.fitInView(self.frame, QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def on_color_mapping_mode_changed(self, index):
        """Update the global color‑mapping mode and reapply layer and SVG rendering.

        Sets the new mode in all motion styles, rebuilds layers, redraws the SVG, and refreshes the simulation view.
        """
        mode = self.color_mapping_mode_combo.itemData(index)
        self.color_mapping_mode=mode
        if self._syncing_ui:
            return
        self._do_evaluation=True
        
        was_set=True
        for motion in ("rapid", "linear", "arc_cw", "arc_ccw"):
            was_set = was_set and self.s_tv.tracker.set_value([motion, "Style", "Color Mapping Mode[value]"], mode)

        self.build_layers()
        # Render svg with new layer structure
        self.render_svg() 
        # Trigger redraw
        self.redraw_sim_position()

    def on_table_selection(self, selected, deselected):
        """Handle table row selection and sync simulation position.

        Updates spinbox, slider, and simulation index, then redraws the current simulation state.
        """
        if self.sim_running:
            return  # ignore clicks during simulation

        indexes = self.table.selectionModel().selectedIndexes()
        if not indexes:
            return

        row = indexes[0].row()

        # Update spinbox without triggering jump twice
        self.sim_pos_spin.blockSignals(True)
        self.sim_pos_spin.setValue(row)
        self.sim_pos_spin.blockSignals(False)

        self.sim_slider.blockSignals(True)
        self.sim_slider.setPosition(row)
        self.sim_slider.blockSignals(False)

        self.sim_index = row
        self.redraw_sim_position()
    
    def set_style_controls_enabled(self, enabled: bool):
        """Enable or disable style‑related UI controls.

        Toggles the color‑mapping combo and shows or hides the style tree accordingly.
        """
        self.color_mapping_mode_combo.setEnabled(enabled)
        if enabled:
            self.style_tree.show()
        else:
            self.style_tree.hide()

    def set_canvas_enabled(self, enabled):
        """Enable or disable canvas interaction, toggling drag mode and interactivity."""
        if enabled:
            self.view.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
            self.view.setInteractive(True)
        else:
            self.view.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
            self.view.setInteractive(False)
    
    def play_pressed(self):
        """Emit the play signal for starting the stream."""
        self.stream_play.emit()
    
    def pause_pressed(self):
        """Emit the pause signal to temporarily halt the stream."""
        self.stream_pause.emit()
    
    def stop_pressed(self):
        """Emit the stop signal to terminate the stream."""
        self.stream_stop.emit()

    def update_cursor_status(self, x, y):
        """Update the status label with the current cursor coordinates."""
        self.cursor_label.setText(f"Cursor: X={x:.2f}  Y={y:.2f}")
    
    def bounds_padded(self, padding_per=0.2):
        """Return job bounds expanded by a percentage-based padding."""
        xmin, ymin, xmax, ymax = self.get_job_bounds()    
        # Expand by padding_per%
        w = xmax - xmin
        h = ymax - ymin
        pad_x = w * padding_per
        pad_y = h * padding_per
        return xmin - pad_x, ymin - pad_y, xmax + pad_x, ymax + pad_y
    
    def get_job_bounds(self):
        """Return the job’s raw bounding box as (xmin, ymin, xmax, ymax)."""
        return self.job_xmin, self.job_ymin, self.job_xmax, self.job_ymax
    
    def add_toolhead(self):
        """Add the toolhead marker to the scene and set its Z‑order."""
        self.tool_dot = self.scene.addEllipse(-1, -1, 2, 2,
                                      QtGui.QPen(QtCore.Qt.GlobalColor.black),
                                      QtGui.QBrush(QtCore.Qt.GlobalColor.red))
        self.tool_dot.setZValue(self.layer_overlay["toolhead"])

    def add_frame(self):
        """Create and add the job frame rectangle based on computed motion bounds.

        Builds the frame item, updates job boundary values, applies visibility, and registers it as a static scene element.
        """
        xmin, ymin, xmax, ymax = self.compute_bounds()
        self.frame = QtWidgets.QGraphicsRectItem(QtCore.QRectF(xmin, ymin, xmax - xmin, ymax - ymin))
        self.frame.setPen(QtGui.QPen(QtGui.QColor(120, 120, 120)))  # or any color
        self.frame.setBrush(QtGui.QBrush(QtCore.Qt.BrushStyle.NoBrush))
        self.frame.setZValue(self.layer_overlay["frame"])
        self.scene.addItem(self.frame)
        self.static_items.append(self.frame)
        self.job_xmin=xmin
        self.job_xmax=xmax
        self.job_ymin=ymin
        self.job_ymax=ymax
        self.svg_height=ymax - ymin
        self.frame.setVisible(self.is_item_type_visible("frame"))
    
    def apply_frame_style(self):
        """Apply the configured frame style, including pen, fill, transparency, and visibility.

        Reads style settings, updates pen and brush properties, and refreshes the frame item.
        """
        if not self.frame:
            return
        style = self.style_dict["frame"]["Style"]

        # Extract values
        line_type = style.get("Line Type", "solid")
        pen_color = style.get("Pen", "#787878")
        pen_width = style.get("Pen Width", 0.8)
        transparency = style.get("Line Transparency", 255)

        fill_color = style.get("Fill Color", "#000000")
        fill_transparency = style.get("Fill Transparency", 0)

        # Convert pen color
        color = QtGui.QColor(pen_color)
        color.setAlpha(transparency)

        # Convert fill color
        fill = QtGui.QColor(fill_color)
        fill.setAlpha(fill_transparency)

        qt_style = LINE_MAP.get(line_type, LINE_MAP["solid"])

        # Apply pen
        pen = self.frame.pen()
        pen.setColor(color)
        pen.setWidthF(pen_width)
        pen.setStyle(qt_style)
        self.frame.setPen(pen)

        # Apply fill only if enabled
        if self.style_dict["frame"]["Fill"]:
            self.frame.setBrush(QtGui.QBrush(fill))
        else:
            self.frame.setBrush(QtGui.QBrush(QtCore.Qt.BrushStyle.NoBrush))

        # Apply visibility
        self.frame.setVisible(self.style_dict["frame"]["Show"])

        # Redraw
        self.frame.update()
    
    def apply_render_style(self):
        """Reapply the render layer using the current style settings.

        Removes any existing SVG item, checks visibility, and regenerates the SVG with updated styling.
        """
        if not self.motions:
            return
        # Remove old SVG item
        if self.svg_item is not None:
            self.scene.removeItem(self.svg_item)
            del self.svg_item
            self.svg_item = None

        # Visibility check using your tested logic
        if not self.is_item_type_visible("render"):
            return
        # Re-render SVG with updated style
        self.render_svg()

    def adjust_brightness_for_layer(self, base_rgb_hex, layer_id, max_layer):
        """
        Take the original pen color (hex), convert to HSV,
        and scale only the brightness (value) based on layer.
        Layer 0 = brightest, max_layer = darkest.
        """
        # Parse hex → RGB 0–1
        base_rgb_hex = base_rgb_hex.lstrip("#")
        r = int(base_rgb_hex[0:2], 16) / 255.0
        g = int(base_rgb_hex[2:4], 16) / 255.0
        b = int(base_rgb_hex[4:6], 16) / 255.0

        # Convert to HSV
        h, s, v = colorsys.rgb_to_hsv(r, g, b)

        # Compute brightness scaling
        if max_layer <= 0:
            scale = 1.0
        else:
            t = layer_id / max_layer
            # 1.0 → 0.3 brightness range
            scale = 1.0 - 0.7 * t

        v = max(0.0, min(1.0, v * scale))

        # Convert back to RGB
        r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)

        return f"#{int(r2*255):02x}{int(g2*255):02x}{int(b2*255):02x}"

    def map_color(self, base_color, norm, movement_hue=None):
        """
        base_color: QColor chosen by the user
        norm: 0..1 normalized strength (S, F, Z, etc.)
        movement_hue: override hue for movement type (0..359) or None to use base hue
        """
        # Hue: movement identity
        if movement_hue is None:
            h = base_color.hue()
        else:
            h = movement_hue

        # Saturation: keep user's color feel
        s = base_color.saturation()

        # Value: strength (never collapse to black)
        v = int(50 + norm * 205)  # 50..255

        return QtGui.QColor.fromHsv(h, s, v)


    def layer_to_color(self, layer_id, max_layer, mapping=None):
        """
        Convert a layer index into an RGB hex color string.

        Parameters
        ----------
        layer_id : int
            The current layer number (0..max_layer).
        max_layer : int
            The highest layer number. Used to normalize the color mapping.
        mapping : str or None
            Selects the color mapping style:
                - "heatmap"     : Blue → Cyan → Green → Yellow → Red
                - "thermal"     : Black → Red → Yellow → White
                - "rainbow"     : Purple → Blue → Green → Yellow → Red
                - "mono"        : Dark blue → Bright cyan
                - None/default  : Fixed hue (yellow) with decreasing brightness

        Returns
        -------
        str
            Hex color string, e.g. "#ffaa33".
        """
        # Normalize t in 0..1
        if max_layer <= 0:
            t = 0.0
        else:
            t = layer_id / max_layer
        # ------------------------------------------------------------
        # Heatmap: Blue → Cyan → Green → Yellow → Red
        # ------------------------------------------------------------
        if mapping == "heatmap":
            hue = (240 * (1 - t)) / 360.0   # 240° → 0°
            sat = 1.0
            val = 1.0
        # ------------------------------------------------------------
        # Thermal: Black → Red → Yellow → White
        # ------------------------------------------------------------
        elif mapping == "thermal":
            hue = (60 * t) / 360.0          # 0° → 60°
            sat = 1.0
            val = 0.3 + 0.7 * t             # darker → brighter
        # ------------------------------------------------------------
        # Rainbow: Purple → Blue → Green → Yellow → Red
        # ------------------------------------------------------------
        elif mapping == "rainbow":
            hue = (270 * (1 - t)) / 360.0   # 270° → 0°
            sat = 1.0
            val = 1.0
        # ------------------------------------------------------------
        # Monochrome heatmap: Dark blue → Bright cyan
        # ------------------------------------------------------------
        elif mapping == "mono":
            hue = 200 / 360.0               # blue/cyan
            sat = 1.0
            val = 0.3 + 0.7 * t
        # ------------------------------------------------------------
        # Default: fixed yellow hue, decreasing brightness
        # ------------------------------------------------------------
        else:
            hue = 55 / 360.0                # yellow
            sat = 1.0
            val = 1.0 - 0.7 * t             # 1.0 → 0.3
        # Convert HSV → RGB
        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def render_svg(self, do_positions=False):
        """Render the full toolpath as an SVG and add it to the scene.

        Removes any existing SVG item, checks visibility, regenerates the SVG
        from the current motions (optionally including position markers), and
        inserts the new SVG item at the appropriate Z‑layer.
        """
        if not self.motions:
            return

        # Remove old SVG item
        if self.svg_item is not None:
            self.scene.removeItem(self.svg_item)
            del self.svg_item
            self.svg_item = None

        # Visibility check
        if not self.is_item_type_visible("render"):
            return

        # Build SVG with style
        svg = self.motions_to_svg(self.motions,True,do_positions)
        svg_bytes = svg.encode("utf-8")

        renderer = QtSvg.QSvgRenderer(svg_bytes)
        item = QtSvgWidgets.QGraphicsSvgItem()
        item.setSharedRenderer(renderer)
        item.setZValue(self.layer_overlay["render_svg"])

        # Add new SVG item
        self.scene.addItem(item)

        # Store reference
        self.svg_item = item

    def add_work_box(self):
        """Add the padded work‑area rectangle to the scene.

        Creates a non‑interactive bounding box around the job area, registers it as
        a static item, and assigns the appropriate Z‑layer.
        """
        xmin, ymin, xmax, ymax = self.bounds_padded(padding_per=0.2)
        self.work_box = QtWidgets.QGraphicsRectItem(QtCore.QRectF(xmin, ymin, xmax - xmin, ymax - ymin))
        self.work_box.setPen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen))  
        self.work_box.setBrush(QtGui.QBrush(QtCore.Qt.BrushStyle.NoBrush))
        self.work_box.setZValue(self.layer_overlay["work_box"])
        self.scene.addItem(self.work_box)
        self.static_items.append(self.work_box)

    def add_grid(self):
        """Add the background grid item to the scene.

        Builds a GridItem spanning the padded job bounds, applies default spacing,
        registers it as a static element, and sets visibility based on style rules.
        """
        # Expand by 20%
        pxmin,pymin,pxmax,pymax=self.bounds_padded(padding_per=0.0)

        self.grid = GridItem(
            pxmin,pymin,pxmax,pymax,
            spacing=1.0,
            bold_every=5
        )
        self.grid.setZValue(self.layer_overlay["grid"])
        self.scene.addItem(self.grid)
        self.static_items.append(self.grid)
        self.grid.setVisible(self.is_item_type_visible("grid"))
    
    def apply_grid_style(self):
        """Apply the configured grid style to both thin and bold grid lines.

        Reads line type, color, width, and transparency from the style dictionary,
        updates both pens accordingly, and triggers a redraw of the grid item.
        """
        if not self.grid:
            return
        if "grid" not in self.style_dict:
            return

        style = self.style_dict["grid"]["Style"]

        # Extract values
        line_type = style.get("Line Type", "solid")
        pen_color = style.get("Pen", "#818181")
        pen_width = style.get("Pen Width", 0.4)
        transparency = style.get("Line Transparency", 255)

        # Convert color + transparency
        color = QtGui.QColor(pen_color)
        color.setAlpha(transparency)

        # Map line type to Qt style
        qt_line_style = LINE_MAP.get(line_type, LINE_MAP["solid"])

        # Apply to thin pen
        self.grid.thin_pen.setColor(color)
        self.grid.thin_pen.setWidthF(pen_width)
        self.grid.thin_pen.setStyle(qt_line_style)

        # Apply to bold pen (same style but thicker)
        bold_color = QtGui.QColor(pen_color)
        bold_color.setAlpha(transparency)
        self.grid.bold_pen.setColor(bold_color)
        self.grid.bold_pen.setWidthF(pen_width * 2)

        # Trigger redraw
        self.grid.update()


    def add_axes(self):
        """Add the XY axes item to the scene using padded job bounds.

        Creates an AxisItem spanning the padded region, registers it as a static
        element, assigns its Z‑layer, and applies visibility rules.
        """
        # Expand by 20% Same grid size
        pxmin,pymin,pxmax,pymax=self.bounds_padded(padding_per=0.2)
        self.axes = AxisItem(pxmin,pymin,pxmax,pymax)
        self.axes.setZValue(self.layer_overlay["axes"])
        self.scene.addItem(self.axes)
        self.static_items.append(self.axes)
        self.axes.setVisible(self.is_item_type_visible("axes"))
    
    def apply_axes_style(self):
        """Apply the configured style to the X and Y axes.

        Updates both axis pens using the style dictionary—line type, color,
        width, and transparency—and triggers a redraw of the axes item.
        """
        if not self.axes:
            return
        style = self.style_dict["axes"]["Style"]

        # Extract values
        line_type = style.get("Line Type", "solid")
        pen_color = style.get("Pen", "#ff0000")
        pen_width = style.get("Pen Width", 0.5)
        transparency = style.get("Line Transparency", 255)

        # Convert color
        color = QtGui.QColor(pen_color)
        color.setAlpha(transparency)

        # Map line type
        qt_style = LINE_MAP.get(line_type, LINE_MAP["solid"])

        # Apply to both axis pens
        self.axes.pen_x.setColor(color)
        self.axes.pen_x.setWidthF(pen_width)
        self.axes.pen_x.setStyle(qt_style)

        self.axes.pen_y.setColor(color)
        self.axes.pen_y.setWidthF(pen_width)
        self.axes.pen_y.setStyle(qt_style)

        # Redraw
        self.axes.update()


    def add_rulers(self):
        """Add ruler items aligned to the job bounds.

        Creates a RulerItem spanning the job area, registers it as a static
        scene element, assigns its Z‑layer, and applies visibility rules.
        """
        # Rulers against the job box
        pxmin,pymin,pxmax,pymax=self.bounds_padded(padding_per=0.0)
        self.ruler = RulerItem(pxmin,pymin,pxmax,pymax)
        self.ruler.setZValue(self.layer_overlay["rulers"])
        self.scene.addItem(self.ruler)
        self.static_items.append(self.ruler)
        self.ruler.setVisible(self.is_item_type_visible("rulers"))

    def apply_ruler_style(self):
        """Apply the configured style to the rulers.

        Updates major and minor tick pens using line type, color, width, and
        transparency from the style dictionary, sets the text color, and triggers
        a redraw of the ruler item.
        """
        if not self.ruler:
            return
        style = self.style_dict["rulers"]["Style"]

        line_type = style.get("Line Type", "solid")
        pen_color = style.get("Pen", "#505050")
        pen_width = style.get("Pen Width", 0.4)
        transparency = style.get("Line Transparency", 255)

        # Convert color
        color = QtGui.QColor(pen_color)
        color.setAlpha(transparency)

        # Map line type
        qt_style = LINE_MAP.get(line_type, LINE_MAP["solid"])

        # Apply to pens
        self.ruler.pen_major.setColor(color)
        self.ruler.pen_major.setWidthF(pen_width)
        self.ruler.pen_major.setStyle(qt_style)

        self.ruler.pen_minor.setColor(color)
        self.ruler.pen_minor.setWidthF(max(0.1, pen_width * 0.5))
        self.ruler.pen_minor.setStyle(qt_style)

        # Text color matches major pen
        self.ruler.text_color = QtGui.QColor(color)

        # Redraw
        self.ruler.update()

    def open_file(self):
        """Open a G‑code file, parse it into motion objects, and load it into the viewer.

        Prompts the user for a file, reads its contents, converts the lines into
        motion data, and rebuilds the full scene via load_motions().
        """
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open G‑code", "", "G‑code (*.gcode *.nc *.txt)"
        )
        if not path:
            return

        with open(path, "r") as f:
            lines = f.readlines()
        motions = self.parse_to_motions(lines)
        self.load_motions(motions)

    def clear_scene(self, clear_all=False):
        """Clear scene items and reset rendering/simulation state.

        Removes the live motion item, deletes cached SVG batches, clears dynamic
        items (or all items when clear_all=True), resets simulation flags, batch
        counters, and last‑known tool position. Static and dynamic item lists are
        also reset when performing a full clear.
        """
        # Remove live MotionItem
        if getattr(self, "motion_item", None):
            if self.motion_item.scene() is self.scene:
                self.scene.removeItem(self.motion_item)
            del self.motion_item
            self.motion_item = None

        # Remove all cached SVG batches
        if hasattr(self, "svg_batches"):
            for key, item in list(self.svg_batches.items()):
                if item.scene() is self.scene:
                    self.scene.removeItem(item)
                del item
            self.svg_batches.clear()

        # Clear dynamic items
        if not clear_all:
            for item in self.dynamic_items:
                if item.scene() is self.scene:
                    self.scene.removeItem(item)
                del item
            self.dynamic_items.clear()
        else:
            self.scene.clear()
            self.static_items.clear()
            self.dynamic_items.clear()
            self.svg_item = None

        # Reset simulation state
        self.simulation_status["is_clear"] = True

        # Reset batch state
        self.current_batch = 0

        # Reset last known position
        self.last_x = 0
        self.last_y = 0

    
    # --------------------------- Parser ---------------------------------
    
    def parse_to_motions(self, lines):
        """Parse G-code lines into a list of motion objects.

        Args:
            lines: Iterable of raw G‑code strings.

        Returns:
            List of parsed motion objects.
        """
        motions = []
        for line in lines:
            m = self.parse_gcode_line(line)
            if m:
                motions.append(m)
        return motions

    def build_batches(self, start_index: int = 0):
        """Build batch ranges for segmented SVG rendering.

        Determines contiguous motion ranges based on batch_size, aligning each
        batch to the nearest defined position object. Produces a list of
        (start_index, end_index) tuples stored in batch_ranges.
        """
        self.batch_ranges = []
        last = len(self.motions) - 1
        
        ini_pos_obj=self._get_position_object(start_index)
        if start_index>0:
            start_index=ini_pos_obj.m_index # last known defined position
        for start in range(start_index, len(self.motions), self.batch_size):
            s_index=ini_pos_obj.m_index
            end = min(s_index + self.batch_size - 1, last)
            # match batch end to last defined movement position
            end_pos_obj=self._get_position_object(end)
            e_index= end_pos_obj.m_index
            self.batch_ranges.append((s_index, e_index))
            ini_pos_obj=end_pos_obj
    
    def _build_motion_index(self):
        """Build and cache a mapping from motion indices to position-list indices.

        Creates a list mapping each Position.m_index to its index in
        self.positions. Returns the cached mapping on subsequent calls.
        """
        # positions is already sorted by m_index
        keys = [pos.m_index for pos in self.positions]   # sorted list of motion indices
        return keys


    def _get_position_object(self, motions_index):
        """Return the Position object corresponding to a motion index.

        Resolves the nearest defined position at or before the given index.
        Falls back to the last known position for out‑of‑range indices, or
        returns a default Position() if no match is found.
        """
        keys = self._build_motion_index()
        # No positions at all → return empty Position()
        if not keys:
            return Position()
        # rightmost key <= motions_index
        iii = bisect.bisect_right(keys, motions_index) - 1
        # If i >= 0 → we found a valid previous position
        if iii >= 0:
            return self.positions[iii]
        # i == -1 → motions_index is BEFORE the first movement
        # Return the FIRST known position
        return self.positions[0]
    
    def _get_next_position_object(self, motions_index):
        """Return the next defined Position object after the given motion index.

        Finds the nearest future position whose m_index is greater than the
        provided motions_index. Falls back to the last known position or a
        default Position() if no suitable match exists.
        """ 
        keys = self._build_motion_index()
        if not keys:
            return Position()
        # leftmost key > motions_index
        iii = bisect.bisect_right(keys, motions_index)

        # If i is inside the list, we found a future movement
        if iii < len(keys):
            return self.positions[iii]

        # Otherwise: no future movement → return last known position
        return self.positions[-1]

    
    def _get_prev_position_object(self, motions_index):
        """Return the previous defined Position object before the given motion index.

        Resolves the current position, then finds the nearest earlier position
        whose m_index is less than the current one. Returns the first position
        for index 0, the last known position for out‑of‑range indices, or a
        default Position() if no match is found.
        """
        # curr_obj=self._get_position_object(motions_index)
        # m_i=self._build_motion_index()
        # if curr_obj.m_index <= 0: 
        #     # first position
        #     return curr_obj
        # if motions_index >= len(self.motions): 
        #     # end position return last known position
        #     return self.positions[-1]
        # last_i=0
        # for index in m_i.keys():
        #     if index>=curr_obj.m_index and last_i<curr_obj.m_index:
        #         return self.positions[m_i[last_i]]
        #     last_i=index
        # return Position() 
        curr = self._get_position_object(motions_index)
        curr_index = curr.m_index
        keys = self._build_motion_index()
        if not keys:
            return Position()
        # rightmost key < curr_index
        iii = bisect.bisect_left(keys, curr_index) - 1
        if iii >= 0:
            return self.positions[iii]
        return curr  # already at first position
    
    def activate_svg_batch(self, batch_index):
        """Activate a specific SVG batch and update scene state accordingly.

        This method prepares the viewer to display a given batch of pre‑rendered
        SVG segments. It performs several coordinated tasks:

        • Restores the last known tool position for the start of the batch by
        resolving the previous defined Position object and updating both the
        simulation state and batch manager.

        • Removes any live MotionItem currently displayed, ensuring that only
        batch‑based SVG rendering is visible.

        • Updates simulation flags and sets the current batch index.

        • Ensures that all *previous* batches (0 → batch_index‑1) are built and
        visible in the scene. Missing batches are generated on demand via
        build_svg_batch() and cached in svg_batches.

        • Hides all *future* batches (batch_index+1 → end), removing them from
        the scene and clearing their cached entries to reduce memory usage.

        This function effectively switches the viewer into a consistent state
        where the selected batch and all earlier batches are visible, while later
        batches remain hidden until activated.
        """
        # get last motion position
        sb,eb=self.batch_ranges[batch_index] 
        s_obj=self._get_prev_position_object(sb)
        self.last_x = self.batch_manager["last_x"] = s_obj.x 
        self.last_y = self.batch_manager["last_y"] = s_obj.y
        self.batch_manager["last_obj"] = s_obj
        
        # Remove live MotionItem
        if getattr(self, "motion_item", None):
            if self.motion_item.scene() is self.scene:
                self.scene.removeItem(self.motion_item)
            del self.motion_item
            self.motion_item = None

        # Reset simulation state
        self.simulation_status["is_clear"] = False
        # Reset batch state
        self.current_batch = batch_index

        # Ensure all PREVIOUS batches exist and are visible
        for iii in range(batch_index):
            item=self.svg_batches.get(iii)
            if not item:
                item=self.build_svg_batch(iii)
                self.svg_batches[iii]=item
            if item not in self.scene.items():
                # print(f"Added {iii}")
                item.setZValue(self.layer_overlay["simulation"])
                self.scene.addItem(item)

        # Hide all FUTURE batches
        for i in range(batch_index + 1, len(self.batch_ranges)):
            if i in self.svg_batches:
                if self.svg_batches[i].scene() is self.scene:
                    self.scene.removeItem(self.svg_batches[i])
                del self.svg_batches[i]

    def build_svg_batch(self, batch_index):
        """Build and return the SVG batch for the given batch index.

        Looks up the (start, end) motion range for the batch and delegates
        rendering to build_svg_batch_start_end().
        """
        start, end = self.batch_ranges[batch_index]
        return self.build_svg_batch_start_end(start, end)
    
    def build_svg_batch_start_end(self, start, end):
        """Render a motion slice as an SVG batch and return it as a QGraphicsSvgItem.

        Converts the specified motion range into an SVG fragment, creates a shared
        QSvgRenderer, wraps it in a QGraphicsSvgItem, assigns the "simulation" Z‑layer,
        and returns the ready‑to‑insert scene item.
        """
        # Ensure last position is set correctly
        s_obj=self._get_prev_position_object(start)
        self.last_x = self.batch_manager["last_x"] = s_obj.x 
        self.last_y = self.batch_manager["last_y"] = s_obj.y
        self.batch_manager["last_obj"] = s_obj
        svg = self.motions_to_svg_batch(self.motions[start:end+1])
        renderer = QtSvg.QSvgRenderer(svg.encode("utf-8"))
        item = QtSvgWidgets.QGraphicsSvgItem()
        item.setSharedRenderer(renderer)
        item.setZValue(self.layer_overlay["simulation"])
        # Ensure last position is set correctly
        s_obj=self._get_position_object(end)
        self.last_x = self.batch_manager["last_x"] = s_obj.x 
        self.last_y = self.batch_manager["last_y"] = s_obj.y
        self.batch_manager["last_obj"] = s_obj
        return item

    def motions_to_svg_batch(self, motions_slice):
        """Convert a slice of motion commands into an SVG fragment for batch rendering.

        This method generates a standalone SVG representing only the given range of
        motions. It uses the job’s global bounds for the <svg> viewBox, then walks
        through the motion slice pairwise to emit individual <path> elements with
        their own stroke styles.

        Key behaviors:
        • Maintains continuity by tracking the last known (x, y) position from the
        batch manager, ensuring that batches connect seamlessly even when the
        slice begins mid‑path.

        • Skips non‑motion commands while still updating the last known position so
        subsequent paths start correctly.

        • For each motion, resolves the appropriate style dictionary, applies
        visibility rules, constructs a QPen, and converts that pen into SVG
        stroke attributes.

        • Supports rapid, linear, and arc motions. Arc commands are emitted as SVG
        elliptical‑arc paths using either explicit radius (R) or center‑offset
        (I/J) parameters.

        • Emits each motion as its own <path> element with stroke, width, opacity,
        and optional dash patterns. Fill is always “none”.

        The resulting SVG string contains only the geometry for this batch and is
        suitable for rendering via QSvgRenderer as part of the batched display
        system.
        """

        # 1. Bounds (same for all batches)
        xmin, ymin, xmax, ymax = self.get_job_bounds()
        width  = xmax - xmin
        height = ymax - ymin

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
            f'viewBox="{xmin} {ymin} {width} {height}">'
        ]
        last_x = self.batch_manager.get("last_x",0)
        last_y = self.batch_manager.get("last_y",0)
        last_obj = self.batch_manager.get("last_obj")
        

        # 2. Loop through motions in the slice
        for prev, m in zip(motions_slice, motions_slice[1:]):
            is_not_visible=False
            # Skip non-motion types
            if m.type not in ("rapid", "linear", "arc_cw", "arc_ccw"):
                x = m.x if m.x is not None else last_x
                y = m.y if m.y is not None else last_y
                last_x, last_y = x, y
                continue

            # Compute pen for THIS motion
            style = self._get_style_dict_from_track([m.type])
            if not self.is_item_type_visible(m.type):
                style["Line Type"] = "none"

            pen = self.make_pen_from_style(style, m)
            if pen.style() == QtCore.Qt.PenStyle.NoPen:
                x = m.x if m.x is not None else last_x
                y = m.y if m.y is not None else last_y
                last_x, last_y = x, y
                is_not_visible=True

            svg_style = self.pen_to_svg_attributes(pen)

            # Coordinates
            x0 = prev.x if prev.x is not None else last_x
            y0 = prev.y if prev.y is not None else last_y
            x1 = m.x if m.x is not None else x0
            y1 = m.y if m.y is not None else y0

            # Build path command
            # always emit an independent mini-path for this segment
            # so nothing ever "connects" accidentally
            
            if is_not_visible:
                d = f"M {x0} {y0} M {x1} {y1}"
            else:
                if m.type in ("rapid", "linear") and not is_not_visible:
                    d = f"M {x0} {y0} L {x1} {y1}"

                elif m.type in ("arc_cw", "arc_ccw"):
                    if m.r is not None:
                        r = abs(m.r)
                    else:
                        dx = m.i if m.i is not None else 0
                        dy = m.j if m.j is not None else 0
                        r = (dx*dx + dy*dy)**0.5

                    if r == 0:
                        d = f"M {x0} {y0} L {x1} {y1}"
                    else:
                        sweep = 1 if m.type == "arc_cw" else 0
                        d = f"M {x0} {y0} A {r} {r} 0 0 {sweep} {x1} {y1}"
            # Emit <path> with its own stroke
            dash_attr = (
                f'stroke-dasharray="{svg_style["dasharray"]}"'
                if svg_style["dasharray"] else ""
            )

            svg_parts.append(
                f'<path d="{d}" '
                f'stroke="{svg_style["stroke"]}" '
                f'stroke-width="{svg_style["stroke_width"]}" '
                f'stroke-opacity="{svg_style["stroke_opacity"]}" '
                f'{dash_attr} fill="none" />'
            )

            last_x, last_y = x1, y1

        svg_parts.append("</svg>")
        return "\n".join(svg_parts)

    def motions_to_svg(self, motions, do_debug_save=False, do_positions=False):
        """Render the full motion list into a layered SVG and optionally build Position objects.

        This is the primary high‑level renderer for converting an entire sequence of
        motion commands into a complete SVG representation. It also optionally
        constructs the chronological list of Position objects used for simulation,
        scrubbing, and batch rendering.

        Rendering pipeline overview:

        1. Visibility and bounds
        • Retrieves the global job bounds and constructs the <svg> viewBox.
        • If the “render” item type is hidden or the pen style resolves to NoPen,
            returns an empty SVG shell.

        2. Style resolution
        • Fetches the style dictionary for the “render” track.
        • Converts the style into a QPen and then into SVG stroke attributes
            (color, width, opacity, dash pattern).

        3. Motion iteration and path extraction
        • Iterates through motions pairwise (prev, m), mirroring simulation logic.
        • Skips non‑motion commands but still updates last known coordinates.
        • Skips invisible motion types (rapid/linear/arc) based on style rules.
        • Computes start/end coordinates for each segment, falling back to the
            last known position when needed.
        • Emits each segment as an independent mini‑path (“M … L …” or “M … A …”)
            so paths never accidentally connect across discontinuities.
        • Groups all emitted path commands by their motion layer (m.layer_id).

        4. Optional Position object creation
        • When do_positions=True, constructs a Position object for each motion
            segment, storing x/y/z/e, feedrate, motion type, layer_id, and the
            motion index.
        • These Position objects populate self.positions and are later used for
            simulation, scrubbing, and batch alignment.

        5. Chunking for large layers
        • Each layer’s path list is split into chunks of up to 2000 commands.
        • Each chunk is prefixed with a correct “M x y” to ensure SVG path
            continuity regardless of chunk boundaries.
        • Produces a list of (layer, path_string) tuples.

        6. Layered SVG assembly
        • Determines the maximum layer index for brightness scaling.
        • Groups chunks by layer and emits each layer as a <g> element with
            Inkscape‑compatible metadata.
        • Each layer’s stroke color is brightness‑adjusted based on its depth
            (layer 0 brightest, max_layer darkest).
        • Emits each chunk as a <path> with stroke, width, opacity, and optional
            dash pattern.

        7. Optional debug output
        • When do_debug_save=True, writes the final SVG to a temporary file
            (“debug_render.svg”) for inspection.

        Returns:
            str: A complete SVG document containing all rendered motion geometry,
                grouped by layer and ready for QSvgRenderer or external tools.
        """
        # -----------------------------------------
        # 1. Visibility check
        # -----------------------------------------
        xmin, ymin, xmax, ymax = self.get_job_bounds()
        width  = xmax - xmin
        height = ymax - ymin

        if not self.is_item_type_visible("render"):
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
                f'viewBox="{xmin} {ymin} {width} {height}"></svg>'
            )

        # -----------------------------------------
        # 2. Style → QPen
        # -----------------------------------------
        style = self._get_style_dict_from_track(["render"])
        pen = self.make_pen_from_style(style)

        if pen.style() == QtCore.Qt.PenStyle.NoPen:
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
                f'viewBox="{xmin} {ymin} {width} {height}"></svg>'
            )

        # -----------------------------------------
        # 3. Convert QPen → SVG attributes
        # -----------------------------------------
        svg_style = self.pen_to_svg_attributes(pen)

        # -----------------------------------------
        # 4. Build path commands grouped by layer
        # -----------------------------------------
        paths_by_layer = defaultdict(list)

        motion_types = ("rapid", "linear", "arc_cw", "arc_ccw")
        visible = {t: self.are_motions_render_visible(t) for t in motion_types}

        last_x = last_y = 0
        last_z = last_e = 0
        if do_positions:
            # initiate positions with default position
            pos_obj=self._define_position_object(do_positions,None,
                                            x=last_x,y=last_y,z=last_z,
                                            type="other",s=0,f=0,
                                            layer_id=0,e=last_e,
                                            m_index=0)
            self.positions=[pos_obj]
        # iterate in chronological pairs, like the simulation
        for count,(prev, m) in enumerate(zip(motions, motions[1:])):

            # skip non-motion types
            if m.type not in motion_types:
                # still update last position
                x = m.x if m.x is not None else last_x
                y = m.y if m.y is not None else last_y
                last_x, last_y = x, y
                continue

            # skip invisible motion types
            if not visible[m.type]:
                x = m.x if m.x is not None else last_x
                y = m.y if m.y is not None else last_y
                last_x, last_y = x, y
                continue

            layer = m.layer_id if m.layer_id is not None else 0

            # start/end like simulation
            x0 = prev.x if prev.x is not None else last_x
            y0 = prev.y if prev.y is not None else last_y
            x1 = m.x if m.x is not None else x0
            y1 = m.y if m.y is not None else y0

            if do_positions:
                z1 = m.z if m.z is not None else last_z
                e1 = m.e if m.e is not None else last_e
                pos_obj=self._define_position_object(do_positions,None,
                                               x=x1,y=y1,z=z1,
                                               type=m.type,s=m.s,f=m.f,
                                               layer_id=m.layer_id,e=e1,
                                               m_index=count)
                self.positions.append(pos_obj)

            # always emit an independent mini-path for this segment
            # so nothing ever "connects" accidentally
            if m.type == "rapid":
                paths_by_layer[layer].append(f"M {x0} {y0} M {x1} {y1}")

            elif m.type == "linear":
                paths_by_layer[layer].append(f"M {x0} {y0} L {x1} {y1}")

            elif m.type in ("arc_cw", "arc_ccw"):
                if m.r is not None:
                    r = abs(m.r)
                else:
                    dx = m.i if m.i is not None else 0
                    dy = m.j if m.j is not None else 0
                    r = (dx*dx + dy*dy)**0.5

                if r == 0:
                    paths_by_layer[layer].append(f"M {x0} {y0} L {x1} {y1}")
                else:
                    sweep = 1 if m.type == "arc_cw" else 0
                    paths_by_layer[layer].append(
                        f"M {x0} {y0} A {r} {r} 0 0 {sweep} {x1} {y1}"
                    )

            last_x, last_y = x1, y1
        # -----------------------------------------
        # 5. Split each layer into chunks of 2000 commands
        # -----------------------------------------
        MAX_CMDS = 2000
        chunked_paths = []  # list of (layer, path_string)

        for layer, cmds in paths_by_layer.items():
            for i in range(0, len(cmds), MAX_CMDS):
                chunk = cmds[i:i + MAX_CMDS]

                # Extract the REAL first coordinate of the chunk
                first_cmd = chunk[0]
                parts = first_cmd.split()

                # Determine the coordinate of the first command
                if parts[0] == "M":
                    mx, my = parts[1], parts[2]
                elif parts[0] == "L":
                    mx, my = parts[1], parts[2]
                elif parts[0] == "A":
                    mx, my = parts[-2], parts[-1]  # arc endpoint
                else:
                    # fallback (should never happen)
                    mx, my = "0", "0"

                # Always prepend a correct M x y
                chunk = [f"M {mx} {my}"] + chunk

                path_str = " ".join(chunk)
                chunked_paths.append((layer, path_str))
        # -----------------------------------------
        # 6. Build final SVG with <g> groups per layer
        # -----------------------------------------
        # Find max layer value (unique layers only)
        if chunked_paths:
            max_layer = max(layer for layer, _ in chunked_paths)
        else:
            max_layer = 0

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
            f'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
            f'viewBox="{xmin} {ymin} {width} {height}">'
        ]

        # Group chunks by layer for <g> grouping
        groups = defaultdict(list)
        for layer, path_str in chunked_paths:
            groups[layer].append(path_str)

        # Build <g> groups
        for layer in sorted(groups.keys()):
            stroke_color = self.adjust_brightness_for_layer(
                svg_style["stroke"], layer, max_layer
            )
            svg_parts.append(
                f'<g inkscape:groupmode="layer" inkscape:label="Layer {layer}">'
            )
            dash_attr = (
                f'stroke-dasharray="{svg_style["dasharray"]}"'
                if svg_style["dasharray"] else ""
            )
            for path_str in groups[layer]:
                svg_parts.append(
                    f'<path d="{path_str}" '
                    f'stroke="{stroke_color}" '
                    f'stroke-width="{svg_style["stroke_width"]}" '
                    f'stroke-opacity="{svg_style["stroke_opacity"]}" '
                    f'{dash_attr} fill="none" />'
                )
            svg_parts.append("</g>")
        svg_parts.append("</svg>")
        svg = "\n".join(svg_parts)

        # -----------------------------------------
        # 7. Save debug SVG to temp folder
        # -----------------------------------------
        if do_debug_save:
            debug_svg = os.path.join(tempfile.gettempdir(), "debug_render.svg")
            with open(debug_svg, "w", encoding="utf-8") as f:
                f.write(svg)
            print("Debug SVG saved to:", debug_svg)

        return svg

    def _define_position_object(self, do_positions, position_object: Position = None, **kwargs) -> Position:
        """Create or update a Position object during motion processing.

        This helper is used by the rendering and simulation pipeline to build the
        chronological list of Position objects (when do_positions=True). It either
        instantiates a new Position or updates an existing one, then applies any
        provided keyword attributes (x, y, z, e, feedrate, motion type, layer_id,
        m_index, etc.) that match fields on the Position class.

        Returns:
            Position: The newly created or updated Position object, or None when
            do_positions=False.
        """
        if not do_positions:
            return
        if not position_object:
            pos_obj=Position()
        else:
            pos_obj=position_object
        params = {k: v for k, v in kwargs.items() if v is not None}
        for par,value in params.items():
            if hasattr(pos_obj,par):
                setattr(pos_obj,par,value)
        return pos_obj

    def pen_to_svg_attributes(self, pen: QtGui.QPen):
        """Convert a QPen into a dictionary of SVG stroke attributes.

        Handles color, width, opacity, and dash patterns, including the special
        case where the pen style is NoPen (stroke disabled). The returned mapping
        is suitable for direct insertion into <path> elements.
        """
        # Handle "none"
        if pen.style() == QtCore.Qt.PenStyle.NoPen:
            return {
                "stroke": "none",
                "stroke_width": "0",
                "stroke_opacity": "0",
                "dasharray": ""
            }
        color = pen.color()
        width = pen.widthF()
        stroke = color.name()  # "#RRGGBB"
        opacity = color.alpha() / 255.0
        # Dash patterns
        dasharray = ""
        if pen.style() == QtCore.Qt.PenStyle.DashLine:
            dasharray = "5,5"
        elif pen.style() == QtCore.Qt.PenStyle.DotLine:
            dasharray = "1,4"
        elif pen.style() == QtCore.Qt.PenStyle.DashDotLine:
            dasharray = "5,5,1,5"
        elif pen.style() == QtCore.Qt.PenStyle.DashDotDotLine:
            dasharray = "5,5,1,5,1,5"

        return {
            "stroke": stroke,
            "stroke_width": str(width),
            "stroke_opacity": str(opacity),
            "dasharray": dasharray
        }

    def parse_gcode_line(self, line):
        """Parse a single line of G‑code into a Motion object.

        This method processes one raw G‑code line and extracts all relevant
        information needed for motion simulation, rendering, and analysis.
        It handles comments, modal behavior, persistent parameters, coordinate
        extraction, and movement classification.

        Parsing behavior:

        • Preprocessing
        - Strips whitespace and removes trailing newline characters.
        - Ignores empty lines.
        - Removes comments in both ';' and '( ... )' formats.
        - Removes optional line numbers (e.g., N123).

        • Motion object creation
        - Instantiates a Motion() and stores the raw line.
        - Extracts the command token (G0, G1, G2, M3, etc.).
        - Special‑cases M5 → “M3 S0” to normalize spindle‑off behavior.

        • Motion type resolution
        - Maps G0/G1/G2/G3 to motion types: rapid, linear, arc_cw, arc_ccw.
        - Tracks modal motion type (e.g., X10 Y10 without a G‑code repeats
            the last modal motion).
        - Non‑movement commands become type="other".

        • Parameter extraction
        - Parses X/Y/Z/I/J/K/R/A/B/C/E coordinates.
        - Parses feedrate (F) and spindle speed (S), with persistence:
            missing F/S values reuse the last known value.
        - Stores comments separately.

        • Modal non‑movement detection
        - If a modal command (e.g., G1) appears with no coordinates or arc
            parameters, it is reclassified as type="other" since it does not
            represent actual movement.

        • Min/max tracking
        - Updates global min/max values for S, F, X, Y, Z for later use in
            bounds computation and UI scaling.

        Returns:
            Motion | None:
                A fully populated Motion object, or None if the line contains
                no actionable content.
        """
        raw = line.rstrip("\n")
        clean = raw.strip()
        if not clean:
            return None
        
        def _persistant(new,key):
            per_val=self._persistant_values.get(key)
            if new is not None:
                self._persistant_values[key]=new
                return new
            return per_val
        
        def _extract_float(token):
            try:
                return float(token[1:])
            except:
                return None
        
        # Remove comments/messages
        comment = None
        if ";" in clean:
            clean, comment = clean.split(";", 1)
            clean = clean.strip()
        if "(" in clean:
            clean, comment = clean.split("(", 1)
            clean = clean.strip()

        # Remove line numbers (N123)
        parts = clean.split()
        if not parts:
            return None

        if parts[0].upper().startswith("N"):
            parts = parts[1:]
            if not parts:
                return None

        m = Motion()
        m.raw = raw

        # Command (G0, G1, G2, G3, M3, M5, etc.)
        m.cmd = parts[0].upper()
        if m.cmd=="M5":
            m.cmd="M3 S0" # Special case 
        # Determine motion type
        pos = 1
        if m.cmd in ("G0", "G00"):
            m.type = "rapid"
            self.last_modal= m.type
        elif m.cmd in ("G1", "G01"):
            m.type = "linear"
            self.last_modal= m.type
        elif m.cmd in ("G2", "G02"):
            m.type = "arc_cw"
            self.last_modal= m.type
        elif m.cmd in ("G3", "G03"):
            m.type = "arc_ccw"
            self.last_modal= m.type
        else:
            if str(m.cmd).startswith(("X","Y","Z","S","E","P","F","R","I","J","K","R","A","B","C")):
                m.type=self.last_modal
                pos=0 # count all part variables
            else: 
                m.type = "other"

        # Parse parameters
        for token in parts[pos:]:
            t = token.upper()
            if t.startswith(";") or t.startswith("("): break # is a comment or message
            if t.startswith("X"): m.x = _extract_float(t)
            elif t.startswith("Y"): m.y = _extract_float(t)
            elif t.startswith("Z"): m.z = _extract_float(t)
            elif t.startswith("I"): m.i = _extract_float(t)
            elif t.startswith("J"): m.j = _extract_float(t)
            elif t.startswith("K"): m.k = _extract_float(t)
            elif t.startswith("R"): m.r = _extract_float(t)
            elif t.startswith("F"): m.f = _persistant(_extract_float(t),"F")
            elif t.startswith("S"): m.s = _persistant(_extract_float(t),"S")

            # Extra axes (rotary/extruder)
            elif t.startswith("A"): m.a = _extract_float(t)
            elif t.startswith("B"): m.b = _extract_float(t)
            elif t.startswith("C"): m.c = _extract_float(t)
            elif t.startswith("E"): m.e = _extract_float(t)
        m.f=self._persistant_values.get("F")
        m.s=self._persistant_values.get("S")
        m.comment = comment
        # Detect modal commands that do NOT move
        if m.type in ("linear", "rapid", "arc_cw", "arc_ccw"):
            if (m.x is None and m.y is None and m.z is None 
            and m.i is None and m.j is None and m.k is None
            and m.a is None and m.b is None and m.c is None 
            and m.r is None and m.e is None):
                # This is NOT a movement, it's a modal update (e.g., S, F, etc.)
                m.type = "other"
        # collect limits
        self._collect_min_max("S",m)
        self._collect_min_max("F",m)
        self._collect_min_max("X",m)
        self._collect_min_max("Y",m)
        self._collect_min_max("Z",m)
        return m
    
    def _collect_min_max(self, txt, m: Motion):
        """Update the global min/max limits for a given motion attribute.

        Looks up the attribute (e.g., X, Y, Z, F, S) on the Motion object and,
        if present and non‑None, updates self.motion_limits[txt] with the new
        minimum and maximum values observed so far. Handles first‑time values,
        missing attributes, and previously invalid stored ranges.
        """
        att = str(txt).lower()
        # If motion has no such attribute → skip
        if not hasattr(m, att):
            return
        val = getattr(m, att)
        # Ignore None values entirely
        if val is None:
            return
        # Retrieve existing min/max
        min_max = self.motion_limits.get(txt)
        # First time seeing this parameter
        if not isinstance(min_max, tuple):
            self.motion_limits[txt] = (val, val)
            return
        # Update min/max safely
        current_min, current_max = min_max
        if current_min is None or current_max is None:
            # Replace invalid stored values
            self.motion_limits[txt] = (val, val)
        else:
            self.motion_limits[txt] = (min(val, current_min), max(val, current_max))
    
    # ---------------------------- Live update -----------------------------    
    def add_gcode_line(self, line):
        """Live update: Parse, append, render, and display a single incoming G‑code line.

        Converts the raw line into a Motion object, appends it to the model,
        draws the resulting motion segment in the scene, updates the status bar,
        and scrolls the table view to keep the newest line visible.
        """
        # 1. Parse
        m = self.parse_gcode_line(line)
        if not m:
            return
        # 2. Append to motions + model
        self.model.appendMotion(m)
        # 3. Draw the new segment
        self.draw_motion(m)
        # 4. Update status bar
        self.update_status(m)
        # 5. Auto-scroll to bottom (FAST)
        last_index = self.model.index(len(self.motions) - 1, 0)
        self.table.scrollTo(last_index, QtWidgets.QAbstractItemView.ScrollHint.PositionAtBottom)

    def draw_motion(self, m, code_by_power=True):
        """Render a single Motion object directly into the scene.

        Handles real‑time drawing of rapid, linear, and arc motions as they are
        appended to the model. The method:

        • Tracks the last known tool position, falling back to previous values
        when coordinates are omitted (modal behavior).

        • Resolves the correct style for the motion type, applying visibility
        rules and converting the style into a QPen.

        • Draws the segment:
            – Rapid/linear moves become simple line segments.
            – Arc moves are delegated to draw_arc_segment() for proper geometry.

        • Updates the live toolhead indicator (dot + label) to reflect the new
        position.

        • Re‑centers the view on the full scene bounds to keep the toolhead in
        view during streaming input.

        This function is the fast, incremental counterpart to the full SVG
        renderer, used for live G‑code streaming or manual line‑by‑line input.
        """
        if m.type not in ("rapid", "linear", "arc_cw", "arc_ccw"):
            return
        # Track last position
        if not hasattr(self, "last_x"):
            self.last_x = 0
            self.last_y = 0
        x = m.x if m.x is not None else self.last_x
        y = m.y if m.y is not None else self.last_y
        # Style-driven pen
        if self.is_item_type_visible(m.type):
            style = self._get_style_dict_from_track([m.type])
        else:
            style = self._get_style_dict_from_track([m.type])
            style["Line Type"] = "none"
        pen = self.make_pen_from_style(style, m)
        # Draw
        if m.type in ("rapid", "linear"):
            self.scene.addLine(self.last_x, self.last_y, x, y, pen)
        else:
            self.draw_arc_segment(self.last_x, self.last_y, x, y, m, pen)

        # Update toolhead
        self.last_x = x
        self.last_y = y
        self.tool_dot.setRect(x - 1, y - 1, 2, 2)
        self.tool_label.setText(f"Tool: X={x:.2f} Y={y:.2f}")

        # Keep view centered
        # self.view.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def draw_arc_segment(self, x0, y0, x1, y1, m: Motion, pen):
        """Approximate a G‑code arc (G2/G3) with line segments and append them to the live MotionItem.

        This method performs a real‑time geometric approximation of circular arcs
        during streaming rendering. It:

        • Computes the arc radius using either R or I/J offsets.
        • Determines the arc center (cx, cy) from the start point and I/J values.
        • Converts start/end points into angular coordinates (a0 → a1).
        • Normalizes the sweep direction based on clockwise/counter‑clockwise mode.
        • Subdivides the arc into a fixed number of straight segments (40 steps).
        • For each segment:
            – Computes the start/end coordinates on the circle.
            – Appends the segment to motion_item.segments for incremental drawing.
            – Expands the MotionItem’s bounding rect to include the new segment.

        After all segments are added, the method updates the last tool position and
        triggers a redraw of the MotionItem.

        This is the live‑rendering counterpart to the SVG arc generator used in
        batch and full‑render modes.
        """
        # Determine radius
        if m.r is not None:
            r = abs(m.r)
        else:
            dx = m.i if m.i is not None else 0
            dy = m.j if m.j is not None else 0
            r = math.sqrt(dx*dx + dy*dy)
        # Center
        cx = x0 + (m.i or 0)
        cy = y0 + (m.j or 0)
        # Angles
        a0 = math.atan2(y0 - cy, x0 - cx)
        a1 = math.atan2(y1 - cy, x1 - cx)
        cw = (m.type == "arc_cw")
        # Normalize sweep direction
        if cw and a1 > a0:
            a1 -= 2 * math.pi
        if not cw and a1 < a0:
            a1 += 2 * math.pi
        # Number of line segments to approximate arc
        steps = 40
        for i in range(steps):
            t0 = a0 + (a1 - a0) * (i / steps)
            t1 = a0 + (a1 - a0) * ((i + 1) / steps)

            sx = cx + r * math.cos(t0)
            sy = cy + r * math.sin(t0)
            ex = cx + r * math.cos(t1)
            ey = cy + r * math.sin(t1)

            # Append to live MotionItem tail
            self.motion_item.segments.append((sx, sy, ex, ey, pen))

            # Update bounding rect
            new_rect = QtCore.QRectF(min(sx, ex), min(sy, ey),
                                    abs(ex - sx), abs(ey - sy))

            self.motion_item.prepareGeometryChange()
            self.motion_item._bounding_rect = self.motion_item._bounding_rect.united(new_rect)

        # Update last position
        self.last_x = x1
        self.last_y = y1
        # Update MotionItem after arc
        self.motion_item.update()
    
    def update_status(self, m):
        """Update the status bar with the latest tool position and power state.

        Resolves modal coordinates (X/Y/Z/S), falling back to the last known values,
        and updates the status bar text to reflect the current tool position and
        streaming state.
        """
        x = m.x if m.x is not None else self.last_x
        y = m.y if m.y is not None else self.last_y
        z = m.z if m.z is not None else 0
        s = m.s if m.s is not None else 0

        self.status.setText(f"X:{x:.2f}  Y:{y:.2f}  Z:{z:.2f}  Power:{s}  State:Streaming")

    # ------------------------ Simulation -------------------------
    def sim_jump_to(self, index):
        """Jump the simulator to a specific motion index.

        Pauses the simulation, updates the current simulation index, and redraws
        the tool position so the view reflects the new point in the motion list.
        """
        self.sim_pause()
        self.sim_index = index
        self.redraw_sim_position()

    def adjust_brightness_for_power(base_rgb_hex, s_value, max_s=1000):
        """Scale an RGB color’s brightness based on spindle/laser power.

        Converts the base color from RGB → HSV, scales the value (V) component
        proportionally to the given power level (s_value / max_s), clamps the
        result to [0, 1], and converts back to RGB. Returns a new hex color
        string representing the brightness‑adjusted color.

        Useful for visually encoding power levels in rendered paths.
        """
        base_rgb_hex = base_rgb_hex.lstrip("#")
        r = int(base_rgb_hex[0:2], 16) / 255.0
        g = int(base_rgb_hex[2:4], 16) / 255.0
        b = int(base_rgb_hex[4:6], 16) / 255.0

        h, s, v = colorsys.rgb_to_hsv(r, g, b)

        scale = s_value / max_s
        v = max(0.0, min(1.0, v * scale))

        r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
        return f"#{int(r2*255):02x}{int(g2*255):02x}{int(b2*255):02x}"

    def draw_motion_segment(self, prev: Motion, m: Motion):
        """Draw a single simulated motion segment into the live MotionItem.

        This method is used by the simulation engine to incrementally render
        motion segments as the simulator advances. It mirrors the logic of the
        full renderer but produces lightweight, real‑time geometry:

        • Determines start/end coordinates using modal behavior:
            – Falls back to last_x/last_y when coordinates are omitted.
            – Ensures continuity even when G‑code omits X/Y values.

        • Selects a pen based on the motion type:
            – Rapid, linear, and arc motions use style‑driven pens.
            – Invisible types force “Line Type = none”.
            – Non‑motion types fall back to a small red diagnostic pen.

        • Skips drawing entirely when the resolved pen style is NoPen.

        • Appends the segment (x0, y0 → x1, y1) to motion_item.segments,
        which stores all geometry for the live simulation overlay.

        • Expands the MotionItem’s bounding rectangle to include the new
        segment, using prepareGeometryChange() for safe updates.

        • Updates last_x / last_y so subsequent segments start correctly.

        This function is the simulation‑time counterpart to draw_arc_segment()
        and the full SVG renderer, optimized for fast incremental updates.
        """
        # Determine start and end points
        x0 = prev.x if prev.x is not None else getattr(self, "last_x", 0)
        y0 = prev.y if prev.y is not None else getattr(self, "last_y", 0)

        x1 = m.x if m.x is not None else x0
        y1 = m.y if m.y is not None else y0

        # Style-driven pen selection
        if m.type in ("rapid", "linear", "arc_cw", "arc_ccw"):
            style = self._get_style_dict_from_track([m.type])
            if not self.is_item_type_visible(m.type):
                style["Line Type"] = "none"
            pen = self.make_pen_from_style(style, m)
        else:
            pen = QtGui.QPen(QtGui.QColor("#ff0000"))
            pen.setWidthF(0.3)

        # Skip invisible segments
        if pen.style() == QtCore.Qt.PenStyle.NoPen:
            self.last_x = x1
            self.last_y = y1
            return

        # Append to live MotionItem tail
        self.motion_item.segments.append((x0, y0, x1, y1, pen))

        # Update bounding rect
        new_rect = QtCore.QRectF(min(x0, x1), min(y0, y1),
                                abs(x1 - x0), abs(y1 - y0))

        self.motion_item.prepareGeometryChange()
        self.motion_item._bounding_rect = self.motion_item._bounding_rect.united(new_rect)
        self.motion_item.update()

        # Update last position
        self.last_x = x1
        self.last_y = y1

    def is_item_type_visible(self, motion_type: str) -> bool:
        """Return whether a given motion type is currently visible.

        Queries the settings tracker for the generic visibility flag associated
        with the motion type (e.g., 'rapid', 'linear', 'arc_cw', etc.). Used by
        both live rendering and SVG generation to suppress drawing when a type
        is disabled in the UI.
        """
        return bool(self.s_ce.tracker.get_value([motion_type, "Show", "value"]))
    
    def are_motions_render_visible(self, mtype):
        """Return whether a motion type should be included in full SVG rendering.

        Checks the dedicated 'render' visibility settings for each motion type:
        Rapid, Linear, ArcCW, and ArcCCW. These settings are separate from the
        generic visibility flags and control whether the full renderer emits
        geometry for that motion type.

        Returns:
            bool | None: True/False for known motion types, or None for unknown types.
        """
        if mtype == "rapid":
            return bool(self.s_ce.tracker.get_value(["render", "Show Rapid", "value"]))
        if mtype == "linear":
            return bool(self.s_ce.tracker.get_value(["render", "Show Linear", "value"]))
        if mtype == "arc_cw":
            return bool(self.s_ce.tracker.get_value(["render", "Show ArcCW", "value"]))
        if mtype == "arc_ccw":
            return bool(self.s_ce.tracker.get_value(["render", "Show ArcCCW", "value"]))
        return None

    def sim_play(self):
        """Start or resume the motion simulation.

        This method drives the simulation state machine and handles three cases:

        • Fresh start (after a full stop):
            – Clears previously drawn simulation paths.
            – Resets the MotionItem used for live drawing.
            – Resets the simulation index to the user‑selected start value.
            – Rebuilds batch ranges beginning at the new index.

        • Resume from pause:
            – Freezes the current drawn geometry so new segments append cleanly.

        • Already playing:
            – Returns immediately to avoid restarting the engine.

        After resolving the correct entry state, the method:
            – Updates simulation flags (play/pause/stop).
            – Starts the simulation timer.
            – Disables canvas and style controls to prevent UI interference.
            – Records the simulation start index in the batch manager.

        This function is the main entry point for beginning continuous playback.
        """
        if not self.motions:
            return
        start = self.sim_start_spin.value()
        end = self.sim_end_spin.value()
        # Already playing
        if self.simulation_status.get("is_play"):
            return
        # Starting fresh after stop
        if self.simulation_status.get("is_stop"):
            self.clean_paths()

            # Reset MotionItem
            self._reset_motion_item()

            # Reset simulation index
            self.sim_index = start
            self.build_batches(self.sim_index)

        # If paused → resume
        elif self.simulation_status.get("is_pause"):
            # remove all drawings if index is before last drawing
            if self.batch_manager.get("sim_start",0)>=self.sim_index:
                self.clean_paths()
                # Reset MotionItem
                self._reset_motion_item()
            # Only freeze if there are batches.
            if len(self.svg_batches)>0:     
                self._freeze_current_motions()

        # Update state
        self.simulation_status["is_pause"] = False
        self.simulation_status["is_play"] = True
        self.simulation_status["is_stop"] = False
        self.sim_running = True
        self.batch_manager["sim_start"]=self.sim_index
        # Start timer
        self.sim_timer.start()

        # Disable UI while playing
        self.set_canvas_enabled(False)
        self.set_style_controls_enabled(False)
    
    def sim_pause(self):
        """Pause the simulation without resetting state.

        Stops the simulation timer, updates play/pause/stop flags, and re‑enables
        canvas and style controls so the user can inspect or modify the view.
        The simulation index and drawn geometry remain intact for later resuming.
        """
        self.set_canvas_enabled(True)
        self.set_style_controls_enabled(True)

        self.simulation_status["is_pause"] = True
        self.simulation_status["is_play"] = False
        self.simulation_status["is_stop"] = False

        self.sim_running = False
        self.sim_timer.stop()

    def sim_stop(self):
        """Stop the simulation and optionally reset it to the beginning.

        Behavior depends on the current simulation state:

        • If playing or paused:
            – First pauses the simulation.
            – Then marks the state as fully stopped.

        • If already stopped:
            – Resets the simulation index to zero.
            – Clears all drawn simulation paths.
            – Resets the MotionItem.
            – Rebuilds batch ranges from index 0.
            – Updates the displayed simulation position.

        Canvas and style controls are always re‑enabled when stopping.
        """
        self.set_canvas_enabled(True)
        self.set_style_controls_enabled(True)

        is_stopped = self.simulation_status.get("is_stop")
        is_playing = self.simulation_status.get("is_play")
        is_paused = self.simulation_status.get("is_pause")

        if is_playing or is_paused:
            self.sim_pause()
            self.simulation_status["is_pause"] = False
            self.simulation_status["is_play"] = False
            self.simulation_status["is_stop"] = True

        if is_stopped:
            self.sim_index = 0
            self.batch_manager["sim_start"]=self.sim_index
            self.clean_paths()
            # Reset MotionItem
            self._reset_motion_item()
            self.build_batches(self.sim_index)
            self.update_sim_position(self.sim_index)
            
    def sim_jump_start(self):
        """Jump the simulation to the configured start index.

        Pauses the simulation, clears any previously drawn simulation paths,
        resets the MotionItem, and sets the simulation index to the user‑selected
        start value. The tool position is then updated so the view reflects the
        new starting point.

        This is the fast, clean way to reposition the simulator at the beginning
        of a selected range without running through intermediate motions.
        """
        self.sim_pause()
        self.clean_paths()
        start = self.sim_start_spin.value()
        # Reset MotionItem
        self._reset_motion_item()

        self.sim_index = start
        self.batch_manager["sim_start"]=self.sim_index
        self.update_sim_position(self.sim_index)

    def sim_jump_end(self):
        """Jump the simulation to the configured end index, drawing all segments in between.

        Pauses the simulation and determines how much geometry must be drawn to
        reach the user‑selected end index:

        • If already at or beyond the end index:
            – Simply update the displayed tool position.

        • If before the start index:
            – Clears all paths and begins drawing from the start index.

        • Otherwise:
            – Continues drawing from the current simulation index.

        Missing MotionItem instances are recreated automatically. All segments
        between the chosen start and end indices are appended to the MotionItem,
        and the simulation index is updated to the final position.
        """
        self.sim_pause()
        end = self.sim_end_spin.value()
        
        if self.sim_index>=end:
            self.sim_index = end
            self.update_sim_position(self.sim_index)
            return
        elif self.sim_index<=self.sim_start_spin.value():
            self.clean_paths()
            start = self.sim_start_spin.value()
        else:
            start = self.sim_index
            
        if not self.motion_item:
            # Reset MotionItem
            self._reset_motion_item()
        this_obj =self._get_position_object(start)
        self.last_x = self.batch_manager["last_x"] = this_obj.x 
        self.last_y = self.batch_manager["last_y"] = this_obj.y
        self.batch_manager["last_obj"] = this_obj
        for iii in range(start, end + 1):
            prev = self.motions[iii - 1]
            m = self.motions[iii]
            self._append_segment_to_motion_item(prev, m, iii)
            self.update_job_progressbar(iii,end,start)

        self.sim_index = end
        self.update_sim_position(self.sim_index)
    
    def sim_1_step_forward(self):
        """Advance the simulation forward in 1 step increment, drawing geometry as needed."""
        # Ensure batch is selected correctly
        self.current_batch=self._get_batch_index()
        self.sim_step_forward(steps_per_tick = 1)

    def sim_step_forward(self,steps_per_tick = 10):
        """Advance the simulation forward in small increments, drawing geometry as needed.

        This method performs a controlled, incremental simulation step. It:

        • Ensures the simulation index is not before the configured start index.
        • Restores the correct last_x/last_y position using the previous Position object.
        • Advances the simulation in fixed increments (10 segments per tick).
        • Uses Position objects to determine the next motion boundary so that
        grouped motions (e.g., arcs or modal sequences) advance cleanly.
        • For each step:
            – Draws all motion segments between the current and next Position index.
            – Updates the simulation index to the end of that group.

        If the simulation reaches the end index or the end of the motion list,
        playback is paused automatically. The tool position is updated after
        each tick to keep the UI synchronized with the simulation state.
        """
        if not self.motions:
            return
        start = self.sim_start_spin.value()
        curr_pos_obj=self._get_position_object(self.sim_index)
        start_pos_obj=self._get_position_object(start)
        end = self.sim_end_spin.value()
        max_index = len(self.motions) - 1
        the_last_position_obj=self._get_position_object(max_index)
        if curr_pos_obj.m_index<start_pos_obj.m_index:
            self.sim_index=start_pos_obj.m_index
        # Ensure last position is set correctly
        s_obj=self._get_prev_position_object(self.sim_index)
        self.last_x = self.batch_manager["last_x"] = s_obj.x 
        self.last_y = self.batch_manager["last_y"] = s_obj.y
        self.batch_manager["last_obj"] = s_obj
        # Draw 10 segments per tick
        for _ in range(steps_per_tick):
            if self.sim_index >= end or self.sim_index > max_index or self.sim_index >= the_last_position_obj.m_index:
                self.sim_pause()
                self.sim_index = end
                break
            if not curr_pos_obj:
                curr_pos_obj=self._get_position_object(self.sim_index)
            next_pos_obj=self._get_next_position_object(self.sim_index)
            if not next_pos_obj or not next_pos_obj.m_index:
                continue
            delta_steps=next_pos_obj.m_index-curr_pos_obj.m_index
            # Evaluate motions for 1 step
            start_step=self.sim_index
            end_step=next_pos_obj.m_index
            self.last_x = self.batch_manager["last_x"] = curr_pos_obj.x 
            self.last_y = self.batch_manager["last_y"] = curr_pos_obj.y
            self.batch_manager["last_obj"] = curr_pos_obj
            for iii in range(start_step, end_step + 0):
                prev = self.motions[iii - 1]
                m = self.motions[iii]
                self._append_segment_to_motion_item(prev, m, iii)
            self.sim_index = end_step
            curr_pos_obj=next_pos_obj

        # Ensure last position is set correctly
        self.last_x = self.batch_manager["last_x"] = curr_pos_obj.x 
        self.last_y = self.batch_manager["last_y"] = curr_pos_obj.y
        self.batch_manager["last_obj"] = curr_pos_obj

        self.update_sim_position(self.sim_index)
    
    def sim_step_backward(self):
        """Step the simulation backward by one Position‑level group of motions.

        This method rewinds the simulation in a controlled way, undoing the most
        recently drawn geometry and restoring the simulator to the previous
        Position object. It handles two major cases:

        • Simple rewind (within the same batch):
            – Uses the current and previous Position objects to determine how many
            motion steps belong to the current segment group.
            – Removes exactly that many segments from motion_item.segments.
            – Recomputes the MotionItem bounding rectangle.
            – Updates sim_index to the previous Position’s motion index.

        • Cross‑batch rewind:
            – If the number of segments to remove is unavailable (e.g., due to
            batch boundaries or missing geometry), the method:
                • Detects whether the batch index changed.
                • Activates the correct SVG batch if needed.
                • Resets the MotionItem.
                • Rebuilds all live geometry from the start of the batch up to
                    the new simulation index.

        After rewinding, the method updates the displayed tool position so the UI
        reflects the new simulation state.

        This is the backward counterpart to sim_step_forward(), using Position
        objects to ensure that stepping aligns with logical motion boundaries
        rather than raw G‑code lines.
        """
        if not self.motions:
            return
        self.sim_pause()
        start = self.sim_start_spin.value()

        if self.sim_index > start:
            # Remove last segment
            curr_pos_obj=self._get_position_object(self.sim_index)
            prev_pos_obj=self._get_prev_position_object(self.sim_index)
            # motion steps taken since last position
            delta_steps=curr_pos_obj.m_index-prev_pos_obj.m_index
            if (self.motion_item and self.motion_item.segments 
                    and len(self.motion_item.segments)>=delta_steps):
                self.motion_item.segments.pop()
                self._recompute_motion_item_bounds()
                self.motion_item.update()
                self.sim_index = prev_pos_obj.m_index
            else:
                before_batch=self._get_batch_index()
                self.sim_index = prev_pos_obj.m_index
                current_batch=self._get_batch_index()
                if before_batch!=current_batch:
                    self.activate_svg_batch(current_batch)
                self._reset_motion_item()
                bstart,bend=self.batch_ranges[current_batch]
                for index in range(bstart,self.sim_index):
                    prev = self.motions[index]
                    m = self.motions[index + 1]
                    self._append_segment_to_motion_item(prev, m, index + 1)

            self.update_sim_position(self.sim_index)

    def _get_batch_index(self,index = None):
        """Return the index of the batch that contains the current simulation index.

        Iterates through self.batch_ranges (each a tuple of (start, end) motion
        indices) and finds the batch whose range includes self.sim_index.
        Returns -1 if the simulation index does not fall within any batch.

        Used throughout the simulation engine to determine which SVG batch is
        active, which batch needs to be frozen, and when batch boundaries are
        crossed during stepping.
        """
        if index is None:
            index = self.sim_index
        batch_index=-1
        for iii, abatch in enumerate(self.batch_ranges):
            if index >= abatch[0] and index <= abatch[1]:
                batch_index = iii 
                break
        return batch_index

    def _freeze_current_motions(self):
        """Convert the currently drawn live MotionItem tail into a permanent SVG batch.

        This method is called when resuming simulation after a pause. It freezes
        all geometry drawn so far into a static SVG batch and rebuilds the batch
        structure so that future simulation steps append cleanly.

        Detailed behavior:

        1. Validate state
        • Returns immediately if no motions or no MotionItem exist.
        • Ensures sim_index is valid and determines the current batch.

        2. Freeze the live‑drawn geometry
        • Determines the batch start index and the current Position object.
        • Adjusts sim_index to the last movement index.
        • Restores last_x/last_y from the last Position respect to batch start.
        • Builds a new SVG batch for the range [start, end].
        • Stores this frozen batch in svg_batches[current_batch].

        3. Remove future batches
        • Deletes all batches after the current one from both the scene and
            the cache.
        • Preserves earlier batches and the truncated current batch.

        4. Rebuild batch ranges
        • Recomputes batch_ranges starting from sim_index.
        • Prepends the preserved ranges so the batch structure remains valid.

        5. Reset SVG batch cache
        • Clears svg_batches and keeps only the newly frozen batch.

        6. Activate the correct batch
        • Determines the new batch index and displays the corresponding SVG.

        7. Reset MotionItem
        • Clears the live‑drawing tail so new segments append cleanly.

        8. Force a visual refresh
        • Updates the scene and viewport to reflect the new batch layout.

        This function is essential for seamless pause/resume behavior: it ensures
        that previously drawn geometry becomes static, efficient SVG, while new
        simulation steps continue drawing only the incremental tail.
        """

        if not self.motions or not self.motion_item:
            return

        if self.sim_index <= 0:
            self.sim_index = 0
            return

        # 1. Determine current batch
        current_batch = self._get_batch_index()
        if current_batch < 0:
            return

        # 2. Freeze MotionItem tail into an SVG batch
        start, _ = self.batch_ranges[current_batch]
        e_obj=self._get_position_object(self.sim_index)
        end = e_obj.m_index
        # move index to last movement motion
        self.sim_index=e_obj.m_index
        # Get last position done inside        
        frozen_item = self.build_svg_batch_start_end(start, end)
        # last position is set (end) as last_obj
        self.svg_batches[current_batch] = frozen_item

        # Store old ranges
        until_ranges=[]
        for i in range(0,current_batch):
            until_ranges.append(self.batch_ranges[i])
        until_ranges.append((start,end-1))
        # 3. Remove All batches from scene 
        # will be added inside activate_svg_batch in the scene
        for i in range(0, len(self.batch_ranges)):
            if i in self.svg_batches:
                if self.svg_batches[i].scene() is self.scene:
                    self.scene.removeItem(self.svg_batches[i])
                del self.svg_batches[i]

        # 4. Rebuild batch ranges starting from sim_index
        self.build_batches(self.sim_index)
        self.batch_ranges = until_ranges + self.batch_ranges
        # 5. Add current SVG batch cache (IMPORTANT)
        self.svg_batches = {current_batch: frozen_item}

        # 6. Activate the correct batch
        new_batch = self._get_batch_index()
        self.activate_svg_batch(new_batch)

        # 7. Reset MotionItem tail
        self._reset_motion_item()

        # 8. Force refresh
        self.scene.update()
        self.view.viewport().update()
        QtWidgets.QApplication.processEvents()

    def _append_segment_to_motion_item(self, prev: Motion, m: Motion, index: int):
        """Append a single simulated motion segment to the live MotionItem, with full batch awareness.

        This method is the simulation engine’s incremental drawing primitive. It
        appends exactly one segment (prev → m) to the MotionItem, but also handles
        all the logic required when crossing batch boundaries.

        Behavior overview:

        1. Determine the active batch
        • Uses _get_batch_index() to find which batch the current sim_index belongs to.
        • If no batch applies, nothing is drawn.

        2. Ensure a MotionItem exists
        • Creates or resets the MotionItem if needed.

        3. Handle batch switching
        • If the simulation index has moved into a new batch OR the simulation
            has reached the configured end index:
                – Activates the correct SVG batch (possibly batch_index + 1).
                – Resets the MotionItem so new segments append cleanly.
                – Restores last_x/last_y from the last frozen Position object.
                – Recomputes `prev` so the new segment begins exactly where the
                frozen batch ended.

        4. Compute segment geometry
        • Resolves modal coordinates for start/end points.
        • Ensures continuity even when X/Y are omitted in the G‑code.

        5. Style resolution
        • Retrieves the correct style for the motion type.
        • Converts it into a QPen for live drawing.

        6. Append the segment
        • Adds (x0, y0, x1, y1, pen) to motion_item.segments.
        • Expands the MotionItem’s bounding rectangle.
        • Triggers a redraw.

        7. Update last position
        • Stores x1/y1 so the next segment begins correctly.

        This function is the simulation‑time equivalent of the SVG renderer’s
        segment builder, but with additional logic to maintain perfect continuity
        across batch boundaries.
        """
        # 1. Determine batch index
        batch_index=self._get_batch_index(index)
        if batch_index<0:
            return
        if not self.motion_item:
            # Reset MotionItem
            self._reset_motion_item()
        sim_end = (index == self.sim_end_spin.value())
        last_obj=self.batch_manager.get("last_obj")
        if not last_obj:
            return
        # 2. Switch batch if needed
        if batch_index != getattr(self, "current_batch", -1) or sim_end: # and new_move:
            if sim_end:
                self.activate_svg_batch(batch_index+1)
            else:
                self.activate_svg_batch(batch_index)

            # Reset MotionItem
            self._reset_motion_item()

            # IMPORTANT: continue from the LAST frozen motion
            if isinstance(last_obj,Position):
                last_frozen = self.motions[last_obj.m_index]
                self.last_x = last_obj.x
                self.last_y = last_obj.y    
            else:
                last_frozen = self.motions[index]
                # self.last_x = last_frozen.x or 0
                # self.last_y = last_frozen.y or 0
            prev = last_frozen
        motion_types = ("rapid", "linear", "arc_cw", "arc_ccw")
        visible = {t: self.is_item_type_visible(t) for t in motion_types}

        # 3. Compute start/end
        x0 = prev.x if prev.x is not None else self.last_x
        y0 = prev.y if prev.y is not None else self.last_y
        x1 = m.x if m.x is not None else x0
        y1 = m.y if m.y is not None else y0
        z1 = m.z if m.z is not None else last_obj.z
        e1 = m.e if m.e is not None else last_obj.e

        # 4. Pen for this motion        
        this_obj=self._define_position_object(True,None,x=x1,y=y1,z=z1,
                                               type=m.type,s=m.s,f=m.f,
                                               layer_id=m.layer_id,e=e1,
                                               m_index=index)

        # skip non-motion types
        if m.type not in motion_types:
            # still update last position
            self.last_x = self.batch_manager["last_x"] = this_obj.x 
            self.last_y = self.batch_manager["last_y"] = this_obj.y
            self.batch_manager["last_obj"] = this_obj
            return

        # # skip invisible motion types
        # if not visible[m.type]:
        #     self.last_x = self.batch_manager["last_x"] = this_obj.x 
        #     self.last_y = self.batch_manager["last_y"] = this_obj.y
        #     self.batch_manager["last_obj"] = this_obj
        #     return

        # layer = m.layer_id if m.layer_id is not None else 0
        
        # Style-driven pen selection
        style = self._get_style_dict_from_track([this_obj.type])
        if not visible[this_obj.type]:
            style["Line Type"] = "none"
        pen = self.make_pen_from_style(style, m)    

        # 5. Append to MotionItem (Only if change in position or style)
        if m.type in ("rapid", "linear"):
            # Append to live MotionItem tail
            self.motion_item.segments.append((x0, y0, x1, y1, pen))

            # Update bounding rect
            new_rect = QtCore.QRectF(min(x0, x1), min(y0, y1),
                                    abs(x1 - x0), abs(y1 - y0))

            self.motion_item.prepareGeometryChange()
            self.motion_item._bounding_rect = self.motion_item._bounding_rect.united(new_rect)
            self.motion_item.update()
        elif m.type in ("arc_cw", "arc_ccw"):
            self.draw_arc_segment(x0,y0,x1,y1,m,pen)

        # # 7. Update last position (is step by step, not obj to obj)
        self.last_x = self.batch_manager["last_x"] = this_obj.x 
        self.last_y = self.batch_manager["last_y"] = this_obj.y
        self.batch_manager["last_obj"] = this_obj

    def _reset_motion_item(self):
        """Reset or recreate the live MotionItem used for simulation drawing.

        The MotionItem represents the *current simulation tail* — the geometry
        drawn after the last frozen SVG batch. This method clears that tail so
        new segments can be appended cleanly.

        Behavior:
        • If no MotionItem exists:
            – Creates a new MotionItem with an empty segment list and a zero‑sized
            bounding rectangle.
            – Adds it to the scene.

        • If a MotionItem already exists:
            – Clears all stored segments.
            – Resets the bounding rectangle to an empty QRectF.
            – Triggers an update so the scene reflects the cleared state.

        This function is called whenever:
            – A batch boundary is crossed,
            – The simulation is restarted,
            – The simulation tail must be rebuilt from scratch.
        """
        # Reset MotionItem
        if not self.motion_item:
            # Create new MotionItem
            self.motion_item = MotionItem([], QtCore.QRectF(0, 0, 0, 0))
            self.motion_item.setZValue(self.layer_overlay["simulation"])
            self.scene.addItem(self.motion_item)
        else:
            self.motion_item.segments.clear()
            self.motion_item._bounding_rect = QtCore.QRectF(0, 0, 0, 0)
            self.motion_item.update()

    def _recompute_motion_item_bounds(self):
        """Recalculate the MotionItem bounding rectangle from its stored segments.

        Used primarily when stepping *backward* in the simulation, where segments
        may be removed and the bounding box must be recomputed from scratch.

        Behavior:
        • If no MotionItem exists → nothing to do.
        • If the MotionItem has no segments → bounding rect becomes empty.
        • Otherwise:
            – Collects all x/y coordinates from every segment.
            – Computes min/max extents.
            – Updates the MotionItem’s bounding rectangle using
            prepareGeometryChange() for safe scene updates.

        This ensures that the MotionItem always reports accurate geometry to the
        scene, even after partial rewinds or manual segment removal.
        """
        if not self.motion_item:
            return
        if not self.motion_item.segments:
            self.motion_item._bounding_rect = QtCore.QRectF(0, 0, 0, 0)
            return

        xs = []
        ys = []
        for (x0, y0, x1, y1, _) in self.motion_item.segments:
            xs.extend([x0, x1])
            ys.extend([y0, y1])

        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)
        max_y = max(ys)

        self.motion_item.prepareGeometryChange()
        self.motion_item._bounding_rect = QtCore.QRectF(
            min_x, min_y, max_x - min_x, max_y - min_y
        )

    def redraw_sim_position(self):
        """Refresh toolhead position, table highlight, and progress bar for the current sim index."""
        if not self.motions:
            return
        pos_obj=self._get_position_object(self.sim_index)

        # Move toolhead dot
        x = pos_obj.x 
        y = pos_obj.y
        
        z = pos_obj.z
        s = pos_obj.s
        f = pos_obj.f
        
        self.tool_dot.setRect(x - 1, y - 1, 2, 2)

        # Update labels
        parts = []
        if x is not None:
            parts.append(f"X={x:.2f}")
        if y is not None:
            parts.append(f"Y={y:.2f}")
        if z is not None:
            parts.append(f"Z={z:.2f}")
        if s is not None:
            parts.append(f"S={int(s)}")
        if f is not None:
            parts.append(f"F={int(f)}")
        self.tool_label.setText("Tool: " + " ".join(parts))


        # Highlight table row
        self.select_table_position(self.sim_index)

        if self.center_check.isChecked():
            view_rect = self.view.viewport().rect()
            pt = self.view.mapFromScene(x, y)

            if not view_rect.contains(pt):
                self.view.centerOn(x, y)
                # Recalculate cursor scene position after recentering
                cursor_pos = self.view.mapFromGlobal(QtGui.QCursor.pos())
                scene_pos = self.view.mapToScene(cursor_pos)
                self.update_cursor_status(scene_pos.x(), scene_pos.y())

        # Update progress bar
        self.update_job_progressbar(self.sim_index,end=self.sim_end_spin.value(),start=self.sim_start_spin.value())   

        # Force scene refresh
        self.scene.update()
        self.view.viewport().update()
        if not self.simulation_status.get("is_sliding"):
            QtWidgets.QApplication.processEvents() 

    def update_job_progressbar(self, position, end, start=0):
        """Update the job progress bar using 0.1% resolution based on the current sim position."""
        total = max(1, end - start)
        progress = max(0, position - start)

        # Compute percentage with 0.1% resolution (max 1000 updates)
        per = int(progress / total * 1000)

        # Initialize range once
        if not hasattr(self, "_last_percentage_value"):
            self.job_progress.setRange(0, 1000)

        # Only update when crossing a 0.1% boundary
        last = getattr(self, "_last_percentage_value", None)
        if last is None or per != last:
            self.job_progress.setValue(per)

        self._last_percentage_value = int(per)



    #------------------------ Layers -------------------

    def build_layers(self):
        """Rebuild layer groups and refresh the layer selector."""
        self.layers = {}  # layer_id -> list of indices
        index = self.color_mapping_mode_combo.currentIndex()
        mode = self.color_mapping_mode_combo.itemData(index)
        self.color_mapping_mode=mode
        for i, m in enumerate(self.motions):
            layer_id = self.get_layer_id(m,mode)
            m.layer_id = layer_id
            self.layers.setdefault(layer_id, []).append(i)

        # Populate combo box
        self.layer_combo.blockSignals(True)
        self.layer_combo.clear()
        for layer_id in sorted(self.layers.keys()):
            self.layer_combo.addItem(str(layer_id), layer_id)
        self.layer_combo.blockSignals(False)
    
    def layer_only_changed(self, state):
        """Toggle between full‑range simulation and layer‑only mode."""
        if state:  # checked
            self.layer_changed()  # enforce layer range
        else:
            # Restore full range
            max_index = len(self.motions) - 1
            self.sim_start_spin.setValue(0)
            self.sim_end_spin.setValue(max_index)

    def update_sim_position(self, index):
        """Set the simulation index and refresh UI controls + tool position."""
        self.sim_index = index

        # Update spinbox
        self.sim_pos_spin.blockSignals(True)
        self.sim_pos_spin.setValue(index)
        self.sim_pos_spin.blockSignals(False)

        # Update slider
        self.sim_slider.blockSignals(True)
        self.sim_slider.setPosition(index)
        self.sim_slider.blockSignals(False)

        # Redraw
        self.redraw_sim_position()

    def layer_changed(self):
        """Update the sim range to match the selected layer and jump to its start."""
        if not self.layers:
            return

        layer_id = self.layer_combo.currentData()
        indices = self.layers[layer_id]

        start = indices[0]
        end = indices[-1]

        # Update simulation range
        self.sim_start_spin.blockSignals(True)
        self.sim_end_spin.blockSignals(True)
        self.sim_start_spin.setValue(start)
        self.sim_end_spin.setValue(end)
        self.sim_start_spin.blockSignals(False)
        self.sim_end_spin.blockSignals(False)
        self.sim_slider.setStart(start)
        self.sim_slider.setEnd(end)

        # Jump to start of layer
        self.sim_index = start
        self.sim_pos_spin.setValue(start)
        self.redraw_sim_position()

    def next_layer(self):
        """Select the next layer in the layer list."""
        idx = self.layer_combo.currentIndex()
        if idx < self.layer_combo.count() - 1:
            self.layer_combo.setCurrentIndex(idx + 1)

    def prev_layer(self):
        """Select the previous layer in the layer list."""
        idx = self.layer_combo.currentIndex()
        if idx > 0:
            self.layer_combo.setCurrentIndex(idx - 1)
    
    def clean_paths(self):
        """Clear all dynamic rendered paths from the scene."""
        self.clear_scene(False)

    def get_layer_id(self, m: Motion, mode: str):
        """Return the layer ID for a motion based on the selected mapping mode."""
        if mode in ("Fixed", "fixed"):
            fixed=self.fixed_layer_mapping.get(m.type)
            if not fixed:
                return 0
            return fixed
        elif mode in ("Power", "power"):
            # Laser grayscale grouping
            if m.s is not None:
                return int(m.s / 10) * 10
        elif mode in("Feedrate", "feedrate"):
            # Feedrate values
            if m.z is not None:
                return int(m.f / 10) * 10
        elif mode in ("Z heights", "layerheight"):
            # 3D printing / CNC
            if m.z is not None:
                return round(m.z, 3)
        #else:    #("None", "none")
        # Default single layer
        return 0
    
    # ---------------- Grid axes,Rulers, toggle -----------------
    def set_showing(self):
        """Sync toolbar checkboxes with show_status without triggering recursion."""
        self._syncing_ui = True
        # Axes
        self.axes_toggle.setChecked(self.show_status.get("axes") in (True, None))
        # Frame
        self.frame_toggle.setChecked(self.show_status.get("frame") in (True, None))
        # Rulers
        self.ruler_toggle.setChecked(self.show_status.get("rulers") in (True, None))
        # Grid
        self.grid_toggle.setChecked(self.show_status.get("grid") in (True, None))
        self._syncing_ui = False
    
    def apply_all_styles(self):
        """Apply style updates to all scene elements."""
        for child in ("grid","rulers","axes","frame"):
            self.apply_style_changes(child)

    def sync_ui(self, func):
        """Run a UI update while suppressing signal feedback."""
        self._syncing_ui = True
        func()
        self._syncing_ui = False

    def toggle_grid(self, state):
        """Show or hide the grid and sync all related UI controls."""
        if self._syncing_ui:
            return
        stateb = bool(state)
        # Update scene item
        if self.grid:
            self.grid.setVisible(stateb)
        # Update internal state
        self.show_status["grid"] = stateb
        # Sync toolbar checkbox
        if self.grid_toggle.isChecked() != stateb:
            self.sync_ui(lambda: self.grid_toggle.setChecked(stateb))
        # Sync treeview model
        self.sync_ui(lambda: self.s_tv.tracker.set_value(
            ["grid", "Show", "value"], stateb, "bool"
        ))
        # Apply style (optional)
        self.apply_grid_style()

    def update_grid_spacing(self, value):
        """Adjust grid spacing based on the slider value."""
        if self.grid:
            self.grid.density = 1 + (value * 0.1)
            self.grid.update()

    def toggle_frame(self, state):
        """Show or hide the frame and sync related UI controls."""
        if self._syncing_ui:
            return
        stateb = bool(state)
        if self.frame:
            self.frame.setVisible(stateb)
        self.show_status["frame"] = stateb
        if self.frame_toggle.isChecked() != stateb:
            self.sync_ui(lambda: self.frame_toggle.setChecked(stateb))
        self.sync_ui(lambda: self.s_tv.tracker.set_value(
            ["frame", "Show", "value"], stateb, "bool"
        ))
        self.apply_frame_style()
    
    def on_frame_toggle_clicked(self, state):
        """Handle frame checkbox clicks and update settings + visibility."""
        checked = (state == QtCore.Qt.CheckState.Checked.value)
        if self._syncing_ui:
            return
        self.sync_ui(lambda: self._change_setting_trigger_evaluate_conditions(
            ["frame", "Show", "value"], checked
        ))
        self.show_status["frame"] = checked
        if self.frame:
            self.frame.setVisible(checked)
        self.apply_frame_style()
    
    def on_grid_toggle_clicked(self, state):
        """Handle grid checkbox clicks and update settings + visibility."""
        checked = (state == QtCore.Qt.CheckState.Checked.value)
        if self._syncing_ui:
            return
        # Update TreeView model WITH condition evaluation
        self.sync_ui(lambda: self._change_setting_trigger_evaluate_conditions(
            ["grid", "Show", "value"], checked
        ))
        self.show_status["grid"] = checked
        if self.grid:
            self.grid.setVisible(checked)
        self.apply_grid_style()

    def toggle_rulers(self, state):
        """Show or hide rulers and sync related UI controls."""
        if self._syncing_ui:
            return
        stateb = bool(state)
        if self.ruler:
            self.ruler.setVisible(stateb)
        self.show_status["rulers"] = stateb
        if self.ruler_toggle.isChecked() != stateb:
            self.sync_ui(lambda: self.ruler_toggle.setChecked(stateb))
        self.sync_ui(lambda: self.s_tv.tracker.set_value(
            ["rulers", "Show", "value"], stateb, "bool"
        ))
        self.apply_ruler_style()
    
    def on_rulers_toggle_clicked(self, state):
        """Handle ruler checkbox clicks and update settings + visibility."""
        checked = (state == QtCore.Qt.CheckState.Checked.value)
        if self._syncing_ui:
            return
        self.sync_ui(lambda: self._change_setting_trigger_evaluate_conditions(
            ["rulers", "Show", "value"], checked
        ))
        self.show_status["rulers"] = checked
        if self.ruler:
            self.ruler.setVisible(checked)
        self.apply_ruler_style()

    def toggle_axes(self, state):
        """Show or hide axes and sync related UI controls."""
        if self._syncing_ui:
            return
        stateb = bool(state)
        if self.axes:
            self.axes.setVisible(stateb)
        self.show_status["axes"] = stateb
        if self.axes_toggle.isChecked() != stateb:
            self.sync_ui(lambda: self.axes_toggle.setChecked(stateb))
        self.sync_ui(lambda: self.s_tv.tracker.set_value(
            ["axes", "Show", "value"], stateb, "bool"
        ))
        self.apply_axes_style()

    def on_axes_toggle_clicked(self, state):
        """Handle axes checkbox clicks and update settings + visibility."""
        checked = (state == QtCore.Qt.CheckState.Checked.value)
        if self._syncing_ui:
            return
        self.sync_ui(lambda: self._change_setting_trigger_evaluate_conditions(
            ["axes", "Show", "value"], checked
        ))
        self.show_status["axes"] = checked
        if self.axes:
            self.axes.setVisible(checked)
        self.apply_axes_style()

    def closeEvent(self, event):
        """Emit and Close"""
        # stop simulation if running
        self.sim_stop()
        self.closed.emit()
        super().closeEvent(event)

class GraphicsView(QtWidgets.QGraphicsView):
    mouseMoved = QtCore.pyqtSignal(float, float)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)

    def wheelEvent(self, event):
        zoom_in = 1.25
        zoom_out = 0.8
        if event.angleDelta().y() > 0:
            self.scale(zoom_in, zoom_in)
        else:
            self.scale(zoom_out, zoom_out)

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        self.mouseMoved.emit(pos.x(), pos.y())
        super().mouseMoveEvent(event)

class GridItem(QtWidgets.QGraphicsItem):
    def __init__(self, xmin, ymin, xmax, ymax, spacing=1.0, bold_every=10):
        super().__init__()
        self.density = 1.0   # default (no change)
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.spacing = spacing
        self.bold_every = bold_every

        self.thin_pen = QtGui.QPen(QtGui.QColor(200, 200, 200))
        self.thin_pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        self.thin_pen.setWidthF(0)

        self.bold_pen = QtGui.QPen(QtGui.QColor(150, 150, 150))
        self.bold_pen.setWidthF(0.4)

    def boundingRect(self):
        return QtCore.QRectF(self.xmin, self.ymin,
                             self.xmax - self.xmin,
                             self.ymax - self.ymin)

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        left   = rect.left()
        right  = rect.right()
        top    = rect.top()
        bottom = rect.bottom()

        scale = painter.worldTransform().m11()
        # Adaptive base spacing
        if scale < 0.2:
            base_minor = 50
        elif scale < 0.5:
            base_minor = 10
        else:
            base_minor = 5

        # Apply density
        minor = base_minor * self.density
        major = minor * self.bold_every

        # Normalize bounds
        if left > right:
            left, right = right, left
        if top > bottom:
            top, bottom = bottom, top

        # -------------------------
        # Vertical grid lines
        # -------------------------
        x = int(self.xmin - (self.xmin % minor))
        while x <= self.xmax:
            if x % major == 0:
                painter.setPen(self.bold_pen)
            else:
                painter.setPen(self.thin_pen)

            painter.drawLine(QtCore.QPointF(x, top), QtCore.QPointF(x, bottom))
            x += minor

        # -------------------------
        # Horizontal grid lines
        # -------------------------
        y = int(self.ymin - (self.ymin % minor))
        while y <= self.ymax:
            if y % major == 0:
                painter.setPen(self.bold_pen)
            else:
                painter.setPen(self.thin_pen)

            painter.drawLine(QtCore.QPointF(left, y), QtCore.QPointF(right, y))
            y += minor

class AxisItem(QtWidgets.QGraphicsItem):
    def __init__(self, xmin, ymin, xmax, ymax):
        super().__init__()
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

        # Pens that can be updated
        self.pen_x = QtGui.QPen(QtGui.QColor("red"))
        self.pen_x.setWidthF(0.5)

        self.pen_y = QtGui.QPen(QtGui.QColor("green"))
        self.pen_y.setWidthF(0.5)

    def boundingRect(self):
        return QtCore.QRectF(self.xmin, self.ymin,
                             self.xmax - self.xmin,
                             self.ymax - self.ymin)

    def paint(self, painter, option, widget):
        painter.setPen(self.pen_x)
        painter.drawLine(QtCore.QPointF(self.xmin, 0), QtCore.QPointF(self.xmax, 0))

        painter.setPen(self.pen_y)
        painter.drawLine(QtCore.QPointF(0, self.ymin), QtCore.QPointF(0, self.ymax))

class RulerItem(QtWidgets.QGraphicsItem):
    def __init__(self, xmin, ymin, xmax, ymax):
        super().__init__()
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

        # Pens that can be styled
        self.pen_major = QtGui.QPen(QtGui.QColor(80, 80, 80))
        self.pen_major.setWidthF(0.4)

        self.pen_minor = QtGui.QPen(QtGui.QColor(120, 120, 120))
        self.pen_minor.setWidthF(0.2)

        # Text color (optional)
        self.text_color = QtGui.QColor(80, 80, 80)

    def boundingRect(self):
        xmin = min(self.xmin, self.xmax)
        xmax = max(self.xmin, self.xmax)
        ymin = min(self.ymin, self.ymax)
        ymax = max(self.ymin, self.ymax)

        pad = 200  # generous padding so ticks + text are never clipped
        return QtCore.QRectF(
            xmin - pad,
            ymin - pad,
            (xmax - xmin) + 2*pad,
            (ymax - ymin) + 2*pad
        )

    def paint(self, painter, option, widget):
        scale = painter.worldTransform().m11()

        # Adaptive tick spacing
        if scale < 0.2:
            major = 100
            minor = 50
        elif scale < 0.5:
            major = 50
            minor = 10
        else:
            major = 10
            minor = 5

        tick_small = 8
        tick_big = 15

        painter.setPen(self.pen_major)

        # -------------------------
        # X-axis ruler (top edge)
        # -------------------------
        y_top = self.ymin

        # X-axis ruler
        x = int(self.xmin)
        while x <= self.xmax:
            if x % major == 0:
                painter.setPen(self.pen_major)
                painter.drawLine(QtCore.QPointF(x, y_top),
                                QtCore.QPointF(x, y_top + tick_big))
                self.transform_matrix(painter, x, y_top, str(x))
            elif x % minor == 0:
                painter.setPen(self.pen_minor)
                painter.drawLine(QtCore.QPointF(x, y_top),
                                QtCore.QPointF(x, y_top + tick_small))
            x += minor


        # -------------------------
        # Y-axis ruler (left edge)
        # -------------------------
        x_left = self.xmin

        y = int(self.ymin)
        while y <= self.ymax:
            if y % major == 0:
                painter.setPen(self.pen_major)
                painter.drawLine(QtCore.QPointF(x_left, y),
                                QtCore.QPointF(x_left + tick_big, y))
                self.transform_matrix(painter,x_left, y, str(y))

            elif y % minor == 0:
                painter.setPen(self.pen_minor)
                painter.drawLine(QtCore.QPointF(x_left, y),
                                QtCore.QPointF(x_left + tick_small, y))

            y += minor
    
    def transform_matrix(self, painter, x, y, label):
        # 1. Compute screen coords BEFORE disabling world matrix
        screen_pt = painter.worldTransform().map(QtCore.QPointF(x, y))

        # 2. Draw text in screen space
        painter.save()
        painter.setWorldMatrixEnabled(False)
        painter.drawText(QtCore.QPointF(screen_pt.x() + 4, screen_pt.y() - 4), label)
        painter.restore()


class MotionItem(QtWidgets.QGraphicsItem):
    def __init__(self, segments, bounding_rect):
        super().__init__()
        self.segments = segments          # list of (x0,y0,x1,y1,pen)
        self._bounding_rect = bounding_rect

        # This item never changes → huge performance boost
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption, False)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton)

    def boundingRect(self):
        return self._bounding_rect

    def paint(self, painter, option, widget):
        for (x0, y0, x1, y1, pen) in self.segments:
            painter.setPen(pen)
            painter.drawLine(QtCore.QPointF(x0, y0), QtCore.QPointF(x1, y1))

class GCodeTableModel(QtCore.QAbstractTableModel):
    def __init__(self, motions, parent=None):
        super().__init__(parent)
        self.motions = motions
        self.headers = ["Line", "Command", "Params", "Status"]

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.motions)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 4

    def data(self, index, role):
        if not index.isValid() or role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None

        m = self.motions[index.row()]
        col = index.column()

        if col == 0:
            return str(index.row() + 1)
        elif col == 1:
            return m.type
        elif col == 2:
            params = []
            for axis in ["x", "y", "z", "i", "j", "k", "r", "f", "s", "e"]:
                val = getattr(m, axis)
                if val is not None:
                    params.append(f"{axis.upper()}{val}")
            return " ".join(params)
        elif col == 3:
            return getattr(m, "status", "")

        return None

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == QtCore.Qt.Orientation.Horizontal:
            return self.headers[section]
        return str(section)

    # NEW: append support
    def appendMotion(self, m):
        row = len(self.motions)
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.motions.append(m)
        self.endInsertRows()

    # NEW: update a single row (e.g., status)
    def updateRow(self, row):
        top = self.index(row, 0)
        bottom = self.index(row, 3)
        self.dataChanged.emit(top, bottom)


