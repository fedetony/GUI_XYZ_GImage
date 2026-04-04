from PyQt6 import QtCore, QtGui, QtWidgets, QtSvg, QtSvgWidgets
from PyQt6.QtWidgets import *
import resources_rc
import class_treeview_functions
import class_struct_tracker
import class_struct_conditioner
from class_simulation_slider import TripleSlider,DualSliderWidget

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
                        {"Pen": {"value": "#888888", "type": "color", "meta": {"hidden":False, "editable":True, "conditions": conditions["rapid"]}}},
                        {"Pen Width": {"value": 0.3, "type": "float",  "unit":"[0.1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0.1, "max": 5}, "conditions": conditions["rapid"]}}},
                        {"Line Transparency": {"value": 60, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}, "conditions": conditions["rapid"]}}},
                        ]}},
            ]},
        "linear": {"children":[                  
                {"Show": {"value": True, "type": "bool", "unit":"", "meta": {}}},
                {"Style": {"meta": {"hidden":False, "conditions": conditions["linear"]}, 
                           "children":[
                        {"Color Mapping Mode": {"value": "none", "type": "str", "meta": {"hidden":False, "editable":True, "options":["none","feedrate","power","z heights"], "conditions": conditions["linear"]}}},                                                
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"], "conditions": conditions["linear"]}}},
                        {"Pen": {"value": "#4d0404", "type": "color", "meta": {"hidden":False, "editable":True, "conditions": conditions["linear"]}}},
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
        self.layer_overlay={"grid":maxlevel-3,"frame":maxlevel-2,"rulers":maxlevel-1,"axes":maxlevel-1,"render_svg":-3333,"toolhead":maxlevel}
        self.sim_running = False
        self.sim_timer = QtCore.QTimer()
        self.sim_timer.setInterval(30)  # 30ms per step (~33 FPS)
        self.sim_timer.timeout.connect(self.sim_step_forward)
        self.stream_running=False
        self.executed_count=0
        self.last_modal=None
        self.show_status={}
        # ------------------------
        self.axes=None
        self.job_box=None
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
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Line", "Command", "Params", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
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

    def _build_style_configuration_tree(self):
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
        """Builds the model from objects in the structure"""
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
        """Returns a dictionary with the Style-defined values."""

        def get(path, default):
            val = self.s_ce.tracker.get_value(path)
            return default if val in (None, "", []) else val

        base = track + ["Style"]

        return {
            "Line Type":          get(base + ["Line Type", "value"], "solid"),
            "Fill Color":         get(base + ["Fill Color", "value"], "#1570D8"),
            "Fill Transparency":  get(base + ["Fill Transparency", "value"], 77),
            "Pen":                get(base + ["Pen", "value"], "#000000"),
            "Pen Width":          float(get(base + ["Pen Width", "value"], 0.3)),
            "Line Transparency":  get(base + ["Line Transparency", "value"], 77),
        }

    def make_pen_from_style(self, style: dict, m=None) -> QtGui.QPen:
        pen = QtGui.QPen()

        # -----------------------------
        # Pen width
        # -----------------------------
        pen.setWidthF(style["Pen Width"])
        # -----------------------------
        # Base color (fixed mode)
        # -----------------------------
        color = QtGui.QColor(style["Pen"])
        color.setAlpha(style["Line Transparency"])
        # -----------------------------
        # Color Mapping Mode
        # -----------------------------
        mode = style.get("Color Mapping Mode", "fixed")
        if m is not None:
            if mode == "power" and hasattr(m, "s") and m.s is not None:
                power = max(0, min(255, int(m.s)))
                hue = int((1 - power / 255) * 240)
                color = QtGui.QColor.fromHsv(hue, 255, 255)
                color.setAlpha(style["Line Transparency"])

            elif mode == "feedrate" and hasattr(m, "f") and m.f:
                f = float(m.f)
                # Map feedrate to hue (blue→red)
                hue = int((1 - min(1, f / 3000)) * 240)
                color = QtGui.QColor.fromHsv(hue, 255, 255)
                color.setAlpha(style["Line Transparency"])

            elif mode == "layerheight" and hasattr(m, "z") and m.z:
                z = float(m.z)
                # Map Z to hue
                hue = int((1 - min(1, z / 10)) * 240)
                color = QtGui.QColor.fromHsv(hue, 255, 255)
                color.setAlpha(style["Line Transparency"])

            elif mode == "none":
                pen.setStyle(QtCore.Qt.PenStyle.NoPen)
                return pen  # No need to set color or style further

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
            #self._changing_from_code=True
            # update values in structure
            # self.s_tv.tracker.set_value(track,value,subtype)
            self._build_style_dict()

            self.apply_style_changes(name)
    
    def on_checkbox_changed(self,child,value):
        """Checkbox to change treview value, if different apply to config and refresh Treeview"""
        return
        track_show=[child,"Show","value"]
        child_dict=self.style_dict.get(child)
        if not isinstance(child_dict,dict):
            return
        old_show=self.s_tv.tracker.get_value(track_show) #child_dict.get("Show") 
        if old_show != value:
            was_set=self.s_tv.tracker.set_value(track_show,value)
            # if not was_set:
            #     log.warning(f"Unable to set {value} to {track_show}")
            # else:
            #     child_dict["Show"]=value
            #     self._evaluate_conditions()
        
    def on_show_fill_changed(self,child):
        """Show orfill setting changed, if different apply to config and refresh Treeview"""
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
    
    def _change_setting_trigger_evaluate_conditions(self,track,value):
        #self._do_evaluation=True #triggers self._evaluate_conditions() # does refresh and changes according conditions
        self._do_evaluation=False
        was_set=self.s_tv.tracker.set_value(track,value)
        if was_set:
            self._evaluate_conditions()
        # self._do_evaluation=False
        return was_set

    def _get_obj_from_track(self,track):
        for name,obj in self.style_dict.items():
            if name == track[0]:
                return obj
        return None   
    
    def _evaluate_conditions(self):
        """Evaluate conditions if changes were applied refresh treeview"""
        evaluated = self.s_ce.evaluate_conditions_in_a_node(self.s_tv.tracker.get_root())
        if evaluated or self._do_evaluation:
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
        self.last_x = 0
        self.last_y = 0
        self.motions = motions
        # Clear dynamic items only
        # Clear EVERYTHING (static + dynamic) 
        self.clear_scene(clear_all=True)
        # -------------------------
        # Job Box, Grid, axes, Rulers
        # -------------------------
        self.add_toolhead()
        self.add_job_box()
        self.add_work_box()
        self.add_grid()
        self.add_axes()
        self.add_rulers()
        # Set visibility
        self.set_showing()
        self.apply_all_styles()
        # Draw full static toolpath
        self.render_svg()
        # Set scene borders after generating the items
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        # Build table
        self.populate_table()
        # Build layers (IMPORTANT)
        self.build_layers()
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
        self.sim_slider.setStart(self.sim_start_spin.value())
        self.sim_slider.setEnd(self.sim_end_spin.value())
        self.sim_slider.setPosition(self.sim_pos_spin.value())


    def compute_bounds(self):
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
        self.table.setRowCount(len(self.motions))

        for i, m in enumerate(self.motions):
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(i+1)))
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(m.type or ""))
            params = []
            for axis in ["x", "y", "z", "i", "j", "k", "r", "f", "s", "e"]:
                val = getattr(m, axis)
                if val is not None:
                    params.append(f"{axis.upper()}{val}")
            self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(" ".join(params)))
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(""))  # status column

    def render_actions_connect(self):
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
        self.sim_action_next.triggered.connect(self.sim_step_forward)
        self.sim_action_previous.triggered.connect(self.sim_step_backward)
        self.sim_action_ini.triggered.connect(self.sim_jump_start)
        self.sim_action_end.triggered.connect(self.sim_jump_end)

        self.speed_slider.valueChanged.connect(lambda v: self.sim_timer.setInterval(v))
        self.sim_pos_spin.valueChanged.connect(self.sim_jump_to)

        self.table.itemSelectionChanged.connect(self.on_table_selection)
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
        self.sim_slider.posChanged.connect(self.sim_pos_spin.setValue)

        # Sync spinboxes → slider
        self.sim_start_spin.valueChanged.connect(self.sim_slider.setStart)
        self.sim_end_spin.valueChanged.connect(self.sim_slider.setEnd)
        self.sim_pos_spin.valueChanged.connect(self.sim_slider.setPosition)


    def fit_view(self):
        pxmin, pymin, pxmax, pymax = self.bounds_padded(0.2)
        self.view.fitInView(QtCore.QRectF(pxmin, pymin, pxmax - pxmin, pymax - pymin),
                            QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        # self.view.fitInView(self.job_box, QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def on_color_mapping_mode_changed(self, index):
        mode = self.color_mapping_mode_combo.itemData(index)
        if self._syncing_ui:
            return
        for motion in ("rapid", "linear", "arc_cw", "arc_ccw"):
            self.sync_ui(lambda m=motion: self._change_setting_trigger_evaluate_conditions(
                [m, "Style", "Color Mapping Mode", "value"], mode
            ))
        # Trigger redraw
        self.redraw_scene()

    def redraw_scene(self):
        # Clear ONLY dynamic items (toolpath)
        return
        self.clear_scene(clear_all=False)
        #self.redraw_sim_position()
        
        # Reset last position
        self.last_x = 0
        self.last_y = 0

        # Redraw all motion segments
        for i in range(1, len(self.motions)):
            prev = self.motions[i - 1]
            m = self.motions[i]
            self.draw_motion_segment(prev, m)

        # Move toolhead to last motion
        if self.motions:
            last = self.motions[-1]
            x = last.x if last.x is not None else self.last_x
            y = last.y if last.y is not None else self.last_y
            self.tool_dot.setRect(x - 1, y - 1, 2, 2)
            self.tool_label.setText(f"Tool: X={x:.2f} Y={y:.2f}")

    def on_table_selection(self):
        if self.sim_running:
            return  # ignore clicks during simulation

        selected = self.table.selectedIndexes()
        if not selected:
            return

        row = selected[0].row()

        # Update spinbox without triggering jump twice
        self.sim_pos_spin.blockSignals(True)
        self.sim_pos_spin.setValue(row)
        self.sim_pos_spin.blockSignals(False)
        self.sim_slider.setPosition(row)

        self.sim_index = row
        self.redraw_sim_position()
    
    def set_style_controls_enabled(self, enabled: bool):
        self.color_mapping_mode_combo.setEnabled(enabled)
        if enabled:
            self.style_tree.show()
        else:
            self.style_tree.hide()

    def set_canvas_enabled(self, enabled):
        if enabled:
            self.view.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
            self.view.setInteractive(True)
        else:
            self.view.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
            self.view.setInteractive(False)
    
    def play_pressed(self):
        self.stream_play.emit()
    
    def pause_pressed(self):
        self.stream_pause.emit()
    
    def stop_pressed(self):
        self.stream_stop.emit()

    def update_cursor_status(self, x, y):
        self.cursor_label.setText(f"Cursor: X={x:.2f}  Y={y:.2f}")
    
    def bounds_padded(self,padding_per=0.2):
        xmin, ymin, xmax, ymax = self.get_job_bounds()    
        # Expand by padding_per%
        w = xmax - xmin
        h = ymax - ymin
        pad_x = w * padding_per
        pad_y = h * padding_per
        return xmin - pad_x, ymin - pad_y, xmax + pad_x, ymax + pad_y
    
    def get_job_bounds(self):
        """Returns job's xmin, ymin, xmax, ymax"""
        return self.job_xmin, self.job_ymin, self.job_xmax, self.job_ymax
    
    def add_toolhead(self):
        self.tool_dot = self.scene.addEllipse(-1, -1, 2, 2,
                                      QtGui.QPen(QtCore.Qt.GlobalColor.black),
                                      QtGui.QBrush(QtCore.Qt.GlobalColor.red))
        self.tool_dot.setZValue(self.layer_overlay["toolhead"])

    def add_job_box(self):
        xmin, ymin, xmax, ymax = self.compute_bounds()
        self.job_box = QtWidgets.QGraphicsRectItem(QtCore.QRectF(xmin, ymin, xmax - xmin, ymax - ymin))
        self.job_box.setPen(QtGui.QPen(QtGui.QColor(120, 120, 120)))  # or any color
        self.job_box.setBrush(QtGui.QBrush(QtCore.Qt.BrushStyle.NoBrush))
        self.scene.addItem(self.job_box)
        self.static_items.append(self.job_box)
        self.job_box.setZValue(self.layer_overlay["frame"])
        self.job_xmin=xmin
        self.job_xmax=xmax
        self.job_ymin=ymin
        self.job_ymax=ymax
        self.svg_height=ymax - ymin
    
    def apply_frame_style(self):
        if not self.job_box:
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
        pen = self.job_box.pen()
        pen.setColor(color)
        pen.setWidthF(pen_width)
        pen.setStyle(qt_style)
        self.job_box.setPen(pen)

        # Apply fill only if enabled
        if self.style_dict["frame"]["Fill"]:
            self.job_box.setBrush(QtGui.QBrush(fill))
        else:
            self.job_box.setBrush(QtGui.QBrush(QtCore.Qt.BrushStyle.NoBrush))

        # Apply visibility
        self.job_box.setVisible(self.style_dict["frame"]["Show"])

        # Redraw
        self.job_box.update()
    
    def apply_render_style(self):
        if not self.motions:
            return

        # Remove old SVG item
        if self.svg_item is not None:
            self.scene.removeItem(self.svg_item)
            self.svg_item = None

        # Visibility check using your tested logic
        if not self.is_motion_type_visible("render"):
            return

        # Re-render SVG with updated style
        self.render_svg()


    def render_svg(self):
        if not self.motions:
            return

        # Remove old SVG item
        if self.svg_item is not None:
            self.scene.removeItem(self.svg_item)
            self.svg_item = None

        # Visibility check
        if not self.is_motion_type_visible("render"):
            return

        # Build SVG with style
        svg = self.motions_to_svg(self.motions)
        svg_bytes = svg.encode("utf-8")

        renderer = QtSvg.QSvgRenderer(svg_bytes)
        item = QtSvgWidgets.QGraphicsSvgItem()
        item.setSharedRenderer(renderer)
        item.setZValue(self.layer_overlay["render_svg"])

        # Add new SVG item
        self.scene.addItem(item)

        # # Fit view (optional)
        # self.view.fitInView(
        #     self.scene.itemsBoundingRect(),
        #     QtCore.Qt.AspectRatioMode.KeepAspectRatio
        # )

        # Store reference
        self.svg_item = item

    def add_work_box(self):
        xmin, ymin, xmax, ymax = self.bounds_padded(padding_per=0.2)
        self.work_box = QtWidgets.QGraphicsRectItem(QtCore.QRectF(xmin, ymin, xmax - xmin, ymax - ymin))
        self.work_box.setPen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen))  
        self.work_box.setBrush(QtGui.QBrush(QtCore.Qt.BrushStyle.NoBrush))
        self.scene.addItem(self.work_box)
        self.static_items.append(self.work_box)
        self.work_box.setZValue(self.layer_overlay["frame"])

    def add_grid(self):
        # Expand by 20%
        pxmin,pymin,pxmax,pymax=self.bounds_padded(padding_per=0.0)

        self.grid = GridItem(
            pxmin,pymin,pxmax,pymax,
            spacing=1.0,
            bold_every=5
        )
        self.scene.addItem(self.grid)
        self.grid.setZValue(self.layer_overlay["grid"])
        self.static_items.append(self.grid)
    
    def apply_grid_style(self):
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
        # Expand by 20% Same grid size
        pxmin,pymin,pxmax,pymax=self.bounds_padded(padding_per=0.2)
        self.axes = AxisItem(pxmin,pymin,pxmax,pymax)
        self.axes.setZValue(self.layer_overlay["axes"])
        self.scene.addItem(self.axes)
        self.static_items.append(self.axes)
    
    def apply_axes_style(self):
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
        # Rulers against the job box
        pxmin,pymin,pxmax,pymax=self.bounds_padded(padding_per=0.0)
        self.ruler = RulerItem(pxmin,pymin,pxmax,pymax)
        self.ruler.setZValue(self.layer_overlay["rulers"])
        self.scene.addItem(self.ruler)
        self.static_items.append(self.ruler)

    def apply_ruler_style(self):
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
        if not clear_all:
            # Clear ONLY dynamic items (toolpath, live cursor, etc.)
            for item in self.dynamic_items:
                self.scene.removeItem(item)
            self.dynamic_items.clear()
        else:
            # Clear EVERYTHING
            self.scene.clear()
            self.static_items.clear()
            self.dynamic_items.clear()
            self.svg_item = None

    
    # --------------------------- Parser ---------------------------------
    
    def parse_to_motions(self, lines):
        motions = []
        for line in lines:
            m = self.parse_gcode_line(line)
            if m:
                motions.append(m)
        return motions

    def motions_to_svg(self, motions):
        # -----------------------------------------
        # 1. Visibility check (use your tested logic)
        # -----------------------------------------
        if not self.is_motion_type_visible("render"):
            # Return an empty SVG container
            xmin, ymin, xmax, ymax = self.get_job_bounds()
            width  = xmax - xmin
            height = ymax - ymin
            return f"""
            <svg xmlns="http://www.w3.org/2000/svg"
                version="1.1"
                viewBox="{xmin} {ymin} {width} {height}">
            </svg>
            """

        # -----------------------------------------
        # 2. Get style dict and build QPen
        # -----------------------------------------
        style = self._get_style_dict_from_track(["render"])
        pen = self.make_pen_from_style(style)

        # If style says "none", produce empty SVG
        if pen.style() == QtCore.Qt.PenStyle.NoPen:
            xmin, ymin, xmax, ymax = self.get_job_bounds()
            width  = xmax - xmin
            height = ymax - ymin
            return f"""
            <svg xmlns="http://www.w3.org/2000/svg"
                version="1.1"
                viewBox="{xmin} {ymin} {width} {height}">
            </svg>
            """

        # -----------------------------------------
        # 3. Convert QPen → SVG attributes
        # -----------------------------------------
        svg_style = self.pen_to_svg_attributes(pen)

        # -----------------------------------------
        # 4. Build SVG path commands
        # -----------------------------------------
        path_cmds = []
        last_x = last_y = 0
        xmin, ymin, xmax, ymax = self.get_job_bounds()
        width  = xmax - xmin
        height = ymax - ymin

        for m in motions:
            if m.type not in ("rapid", "linear", "arc_cw", "arc_ccw"):
                continue

            x = m.x if m.x is not None else last_x
            y = m.y if m.y is not None else last_y

            if m.type == "rapid":
                path_cmds.append(f"M {x} {y}")

            elif m.type == "linear":
                path_cmds.append(f"L {x} {y}")

            elif m.type in ("arc_cw", "arc_ccw"):
                if m.r is not None:
                    r = m.r
                else:
                    dx = m.i if m.i is not None else 0
                    dy = m.j if m.j is not None else 0
                    r = (dx*dx + dy*dy)**0.5

                sweep = 1 if m.type == "arc_cw" else 0
                path_cmds.append(f"A {r} {r} 0 0 {sweep} {x} {y}")

            last_x, last_y = x, y

        # -----------------------------------------
        # 5. Build final SVG
        # -----------------------------------------
        dash_attr = (
            f'stroke-dasharray="{svg_style["dasharray"]}"'
            if svg_style["dasharray"] else ""
        )

        svg = f"""
        <svg xmlns="http://www.w3.org/2000/svg"
            version="1.1"
            viewBox="{xmin} {ymin} {width} {height}">
            <path d="{' '.join(path_cmds)}"
                stroke="{svg_style['stroke']}"
                stroke-width="{svg_style['stroke_width']}"
                stroke-opacity="{svg_style['stroke_opacity']}"
                {dash_attr}
                fill="none" />
        </svg>
        """

        return svg


    def pen_to_svg_attributes(self, pen: QtGui.QPen):
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

    def parse_gcode_line(self,line):

        raw = line.rstrip("\n")
        clean = raw.strip()
        def _extract_float(token):
            try:
                return float(token[1:])
            except:
                return None
        if not clean:
            return None

        # Remove comments
        comment = None
        if ";" in clean:
            clean, comment = clean.split(";", 1)
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

            if t.startswith("X"): m.x = _extract_float(t)
            elif t.startswith("Y"): m.y = _extract_float(t)
            elif t.startswith("Z"): m.z = _extract_float(t)
            elif t.startswith("I"): m.i = _extract_float(t)
            elif t.startswith("J"): m.j = _extract_float(t)
            elif t.startswith("K"): m.k = _extract_float(t)
            elif t.startswith("R"): m.r = _extract_float(t)
            elif t.startswith("F"): m.f = _extract_float(t)
            elif t.startswith("S"): m.s = _extract_float(t)

            # Extra axes (rotary/extruder)
            elif t.startswith("A"): m.a = _extract_float(t)
            elif t.startswith("B"): m.b = _extract_float(t)
            elif t.startswith("C"): m.c = _extract_float(t)
            elif t.startswith("E"): m.e = _extract_float(t)

        m.comment = comment
        return m
    
    # ---------------------------- Live update -----------------------------    
    def add_gcode_line(self, line):
        # 1. Parse
        m = self.parse_gcode_line(line)
        if not m:
            return

        # 2. Store
        self.motions.append(m)

        # 3. Update table
        self.add_table_row(m)

        # 4. Draw the new segment
        self.draw_motion(m)

        # 5. Update status bar
        self.update_status(m)

    def add_table_row(self, m):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(row + 1)))
        self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(m.type or ""))

        params = []
        for axis in ["x", "y", "z", "i", "j", "k", "r", "f", "s", "e"]:
            val = getattr(m, axis)
            if val is not None:
                params.append(f"{axis.upper()}{val}")

        self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(" ".join(params)))
        self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(""))  # status

        # Auto-scroll to bottom
        self.table.scrollToBottom()
    
    def draw_motion(self, m, code_by_power=True):
        if m.type not in ("rapid", "linear", "arc_cw", "arc_ccw"):
            return

        # Track last position
        if not hasattr(self, "last_x"):
            self.last_x = 0
            self.last_y = 0

        x = m.x if m.x is not None else self.last_x
        y = m.y if m.y is not None else self.last_y

        # Style-driven pen
        if self.is_motion_type_visible(m.type):
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
        self.view.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def draw_arc_segment(self, x0, y0, x1, y1, m, pen):
        # Approximate arc with 40 segments
        import math

        if m.r is not None:
            r = m.r
        else:
            dx = m.i if m.i is not None else 0
            dy = m.j if m.j is not None else 0
            r = math.sqrt(dx*dx + dy*dy)

        # Compute center
        cx = x0 + (m.i or 0)
        cy = y0 + (m.j or 0)

        # Compute angles
        a0 = math.atan2(y0 - cy, x0 - cx)
        a1 = math.atan2(y1 - cy, x1 - cx)

        # Direction
        cw = (m.type == "arc_cw")

        # Normalize
        if cw and a1 > a0:
            a1 -= 2 * math.pi
        if not cw and a1 < a0:
            a1 += 2 * math.pi

        steps = 40
        for i in range(steps):
            t0 = a0 + (a1 - a0) * (i / steps)
            t1 = a0 + (a1 - a0) * ((i + 1) / steps)

            x_start = cx + r * math.cos(t0)
            y_start = cy + r * math.sin(t0)
            x_end   = cx + r * math.cos(t1)
            y_end   = cy + r * math.sin(t1)

            self.scene.addLine(x_start, y_start, x_end, y_end, pen)
    
    def update_status(self, m):
        x = m.x if m.x is not None else self.last_x
        y = m.y if m.y is not None else self.last_y
        z = m.z if m.z is not None else 0
        s = m.s if m.s is not None else 0

        self.status.setText(f"X:{x:.2f}  Y:{y:.2f}  Z:{z:.2f}  Power:{s}  State:Streaming")

    # ------------------------ Simulation -------------------------
    def sim_jump_to(self, index):
        self.sim_pause()
        self.sim_index = index
        self.redraw_sim_position()

    def draw_motion_segment(self, prev, m):
        # Determine start and end points
        x0 = prev.x if prev.x is not None else getattr(self, "last_x", 0)
        y0 = prev.y if prev.y is not None else getattr(self, "last_y", 0)

        x1 = m.x if m.x is not None else x0
        y1 = m.y if m.y is not None else y0

        # -----------------------------
        # Style-driven pen selection
        # -----------------------------
        if m.type in ("rapid", "linear", "arc_cw", "arc_ccw"):
            style = self._get_style_dict_from_track([m.type])
            # Visibility override
            if not self.is_motion_type_visible(m.type):
                style["Line Type"] = "none"
            pen = self.make_pen_from_style(style, m)
        else:
            # Non-motion fallback
            pen = QtGui.QPen(QtGui.QColor("#ff0000"))
            pen.setWidthF(0.3)

        # -----------------------------
        # Draw only if line type is not "none"
        # -----------------------------
        if pen.style() != QtCore.Qt.PenStyle.NoPen:
            if m.type in ("rapid", "linear"):
                line = self.scene.addLine(QtCore.QLineF(x0, y0, x1, y1), pen)
                self.dynamic_items.append(line)

            elif m.type in ("arc_cw", "arc_ccw"):
                self.draw_arc_segment(x0, y0, x1, y1, m, pen)

        # -----------------------------
        # Always update last position
        # -----------------------------
        self.last_x = x1
        self.last_y = y1

    
    def is_motion_type_visible(self, motion_type: str) -> bool:
        return bool(self.s_ce.tracker.get_value([motion_type, "Show", "value"]))

    def sim_play(self):
        if not self.motions:
            return
        start = self.sim_start_spin.value()

        # If starting fresh or after stop, clear and redraw up to start
        if self.sim_index <= start:
            self.clear_scene(clear_all=False)
            for i in range(1, start + 1):
                prev = self.motions[i - 1]
                m = self.motions[i]
                self.draw_motion_segment(prev, m)
            self.sim_index = start

        self.sim_running = True
        self.sim_timer.start()
        self.set_canvas_enabled(False)
        self.set_style_controls_enabled(False)

    def sim_pause(self):
        self.set_canvas_enabled(True)
        self.set_style_controls_enabled(True)
        self.sim_running = False
        self.sim_timer.stop()

    def sim_stop(self):
        self.set_canvas_enabled(True)
        self.set_style_controls_enabled(True)
        self.sim_pause()
        self.sim_index = 0
        self.redraw_sim_position()

    def sim_jump_start(self):
        self.sim_pause()
        self.clear_scene(clear_all=False)  # clear dynamic items only

        start = self.sim_start_spin.value()

        # Redraw up to start
        for i in range(1, start + 1):
            prev = self.motions[i - 1]
            m = self.motions[i]
            self.draw_motion_segment(prev, m)

        self.sim_index = start

        self.update_sim_position(self.sim_index)


    def sim_jump_end(self):
        self.sim_pause()
        self.clear_scene(clear_all=False)  # clear dynamic items only

        # Redraw everything up to end
        end = self.sim_end_spin.value()
        for i in range(1, end + 1):
            prev = self.motions[i - 1]
            m = self.motions[i]
            self.draw_motion_segment(prev, m)

        self.sim_index = end

        # Update spinbox
        self.update_sim_position(self.sim_index)
        
    def sim_step_forward(self):
        if not self.motions:
            return

        end = self.sim_end_spin.value()
        max_index = len(self.motions) - 1

        if self.sim_index < end and self.sim_index < max_index:
            self.sim_index += 1
            self.update_sim_position(self.sim_index)
        else:
            self.sim_pause()

    def sim_step_backward(self):
        if not self.motions:
            return

        start = self.sim_start_spin.value()

        if self.sim_index > start and self.sim_index > 0:
            self.sim_index -= 1
            # Update spinbox without triggering jump
            self.update_sim_position(self.sim_index)

    def redraw_sim_position(self):
        m = self.motions[self.sim_index]

        # Draw segment if not at first line
        if self.sim_index > 0:
            prev = self.motions[self.sim_index - 1]
            self.draw_motion_segment(prev, m)

        # Move toolhead dot
        x = m.x if m.x is not None else self.last_x
        y = m.y if m.y is not None else self.last_y
        # y_flipped = self.svg_height - y

        # self.tool_dot.setRect(x - 1, y_flipped - 1, 2, 2)
        self.tool_dot.setRect(x - 1, y - 1, 2, 2)

        # Update labels
        # self.tool_label.setText(f"Tool: X={x:.2f} Y={y_flipped:.2f}")
        self.tool_label.setText(f"Tool: X={x:.2f} Y={y:.2f}")

        # Highlight table row
        self.table.selectRow(self.sim_index)
        self.table.scrollToItem(self.table.item(self.sim_index, 0))

        # Optionally center view on toolhead
        if self.center_check.isChecked():
            # self.view.centerOn(x, y_flipped)
            self.view.centerOn(x, y)

        # Update progress bar
        self.update_job_progressbar(self.sim_index,end=self.sim_end_spin.value(),start=self.sim_start_spin.value())    

    def update_job_progressbar(self, position, end, start=0):
        total = max(0, end - start)
        progress = max(0, position - start)

        self.job_progress.setRange(0, total)
        self.job_progress.setValue(progress)

    #------------------------ Layers -------------------

    def build_layers(self):
        self.layers = {}  # layer_id -> list of indices

        for i, m in enumerate(self.motions):
            layer_id = self.get_layer_id(m)
            self.layers.setdefault(layer_id, []).append(i)

        # Populate combo box
        self.layer_combo.blockSignals(True)
        self.layer_combo.clear()
        for layer_id in sorted(self.layers.keys()):
            self.layer_combo.addItem(str(layer_id), layer_id)
        self.layer_combo.blockSignals(False)
    
    def layer_only_changed(self, state):
        if state:  # checked
            self.layer_changed()  # enforce layer range
        else:
            # Restore full range
            max_index = len(self.motions) - 1
            self.sim_start_spin.setValue(0)
            self.sim_end_spin.setValue(max_index)

    def update_sim_position(self, index):
        """Sets position to index"""
        self.sim_index = index

        # Update spinbox
        self.sim_pos_spin.blockSignals(True)
        self.sim_pos_spin.setValue(index)
        self.sim_pos_spin.blockSignals(False)

        # Update slider
        self.sim_slider.setPosition(index)

        # Redraw
        self.redraw_sim_position()


    def layer_changed(self):
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
        idx = self.layer_combo.currentIndex()
        if idx < self.layer_combo.count() - 1:
            self.layer_combo.setCurrentIndex(idx + 1)

    def prev_layer(self):
        idx = self.layer_combo.currentIndex()
        if idx > 0:
            self.layer_combo.setCurrentIndex(idx - 1)

    def get_layer_id(self, m):
        # 3D printing / CNC
        if m.z is not None:
            return round(m.z, 3)

        # Laser grayscale grouping
        if m.s is not None:
            return int(m.s / 10)

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
        for child in ("grid","rulers","axes","frame"):
            self.apply_style_changes(child)

    def sync_ui(self, func):
        self._syncing_ui = True
        func()
        self._syncing_ui = False

    def toggle_grid(self, state):
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
        if self.grid:
            self.grid.density = 1 + (value * 0.1)
            self.grid.update()

    def toggle_frame(self, state):
        if self._syncing_ui:
            return
        stateb = bool(state)
        if self.job_box:
            self.job_box.setVisible(stateb)
        self.show_status["frame"] = stateb
        if self.frame_toggle.isChecked() != stateb:
            self.sync_ui(lambda: self.frame_toggle.setChecked(stateb))
        self.sync_ui(lambda: self.s_tv.tracker.set_value(
            ["frame", "Show", "value"], stateb, "bool"
        ))
        self.apply_frame_style()
    
    def on_frame_toggle_clicked(self, state):
        checked = (state == QtCore.Qt.CheckState.Checked.value)
        if self._syncing_ui:
            return
        self.sync_ui(lambda: self._change_setting_trigger_evaluate_conditions(
            ["frame", "Show", "value"], checked
        ))
        self.show_status["frame"] = checked
        if self.job_box:
            self.job_box.setVisible(checked)
        self.apply_frame_style()
    
    def on_grid_toggle_clicked(self, state):
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
        self.closed.emit()
        super().closeEvent(event)

class GraphicsView(QtWidgets.QGraphicsView):
    mouseMoved = QtCore.pyqtSignal(float, float)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)

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


