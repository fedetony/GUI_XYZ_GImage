from PyQt6 import QtCore, QtGui, QtWidgets, QtSvg, QtSvgWidgets
from PyQt6.QtWidgets import *

class Motion:
    def __init__(self, raw):
        self.raw = raw          # original line
        self.type = None        # "rapid", "linear", "arc_cw", "arc_ccw", "other"
        self.x = None
        self.y = None
        self.z = None
        self.i = None
        self.j = None
        self.k = None
        self.r = None
        self.f = None
        self.s = None
        self.comment = None

class GCodeVisualizerDialog(QtWidgets.QMainWindow):
    closed = QtCore.pyqtSignal()
    stream_play = QtCore.pyqtSignal()
    stream_pause = QtCore.pyqtSignal()
    stream_stop = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("G‑code Visualizer")
        self.resize(1100, 700)

        # Variables
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
        self.sim_running = False
        self.sim_timer = QtCore.QTimer()
        self.sim_timer.setInterval(30)  # 30ms per step (~33 FPS)
        self.sim_timer.timeout.connect(self.sim_step_forward)


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
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Line", "Command", "Params", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

        # -------------------------
        # Right: Canvas (QGraphicsView)
        # -------------------------
        self.scene = QtWidgets.QGraphicsScene()
        # self.view = QtWidgets.QGraphicsView(self.scene)
        self.view = GraphicsView(self.scene)

        self.view.setRenderHints(QtGui.QPainter.RenderHint.Antialiasing | QtGui.QPainter.RenderHint.SmoothPixmapTransform)

        # -------------------------
        # Splitter
        # -------------------------
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.table)
        splitter.addWidget(self.view)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        splitter_layout = QtWidgets.QVBoxLayout()
        splitter_layout.addWidget(splitter)
        splitter_layout.setStretch(0, 1) # the splitter gets stretch

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

        self.grid_toggle = QtWidgets.QCheckBox("Grid")
        self.grid_toggle.setChecked(True)
        
        self.grid_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.grid_slider.setRange(1, 50)   # 1mm to 50mm
        self.grid_slider.setValue(10)
        
        self.frame_toggle = QtWidgets.QCheckBox("Frame")
        self.frame_toggle.setChecked(True)
        
        self.ruler_toggle = QtWidgets.QCheckBox("Rulers")
        self.ruler_toggle.setChecked(True)
        
        # Add to toolbar
        self.grid_toolbar.addWidget(self.grid_toggle)
        self.grid_toolbar.addWidget(self.grid_slider)
        self.grid_toolbar.addWidget(self.frame_toggle)
        self.grid_toolbar.addWidget(self.ruler_toggle)
        #Add to top layout
        top_toolbar_layout.addWidget(self.grid_toolbar)


        # -------------------------
        # Main Layout
        # -------------------------
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        layout = QtWidgets.QVBoxLayout(central)
        layout.addLayout(top_toolbar_layout)
        layout.addLayout(splitter_layout)
        layout.addWidget(self.sim_toolbar)
        layout.addLayout(status_layout)   
        


        # -------------------------
        # Internal data
        # -------------------------
        self.motions = []   # list of Motion objects
        self.svg_item = None

        # -------------------------
        # Toolhead object
        # -------------------------
        self.tool_dot = self.scene.addEllipse(-1, -1, 2, 2,
                                      QtGui.QPen(QtCore.Qt.GlobalColor.black),
                                      QtGui.QBrush(QtCore.Qt.GlobalColor.red))
        self.tool_dot.setZValue(1000)
        

        # Connect actions
        self.render_actions_connect()

    def load_motions(self, motions):
        self.last_x = 0
        self.last_y = 0
        self.motions = motions
        # Clear dynamic items only
        self.clear_scene(clear_all=False)
        # -------------------------
        # Job Box, Grid, axes, Rulers
        # -------------------------
        self.add_job_box()
        self.add_grid()
        self.add_axes()
        self.add_rulers()
        # Draw full static toolpath
        self.render_svg()
        # Build table
        self.populate_table()
        # Build layers (IMPORTANT)
        self.build_layers()
        # Reset simulation ranges
        max_index = len(motions) - 1
        self.sim_start_spin.setRange(0, max_index)
        self.sim_end_spin.setRange(0, max_index)
        self.sim_end_spin.setValue(max_index)
        self.sim_pos_spin.setRange(0, max_index)

        # Reset simulation index
        self.sim_index = 0
        self.redraw_sim_position()
    
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
            for axis in ["x", "y", "z", "i", "j", "k", "r", "f", "s"]:
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
        self.grid_toggle.stateChanged.connect(self.toggle_grid)
        self.grid_slider.valueChanged.connect(self.update_grid_spacing)
        self.frame_toggle.stateChanged.connect(self.toggle_frame)
        self.ruler_toggle.stateChanged.connect(self.toggle_rulers)

    def fit_view(self):
        self.view.fitInView(self.job_box, QtCore.Qt.AspectRatioMode.KeepAspectRatio)


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

        self.sim_index = row
        self.redraw_sim_position()
    
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

    def add_job_box(self):
        xmin, ymin, xmax, ymax = self.compute_bounds()
        self.job_box = QtWidgets.QGraphicsRectItem(QtCore.QRectF(xmin, ymin, xmax - xmin, ymax - ymin))
        self.job_box.setPen(QtGui.QPen(QtGui.QColor(120, 120, 120)))  # or any color
        self.job_box.setBrush(QtGui.QBrush(QtCore.Qt.BrushStyle.NoBrush))
        self.scene.addItem(self.job_box)
        self.static_items.append(self.job_box)
        self.job_box.setZValue(-3333)
        self.job_xmin=xmin
        self.job_xmax=xmax
        self.job_ymin=ymin
        self.job_ymax=ymax

    def add_grid(self):
        # Expand by 20%
        pxmin,pymin,pxmax,pymax=self.bounds_padded(padding_per=0.2)

        self.grid = GridItem(
            pxmin,pymin,pxmax,pymax,
            spacing=1.0,
            bold_every=10
        )
        self.scene.addItem(self.grid)
        self.grid.setZValue(-1000)
        self.static_items.append(self.grid)

    def add_axes(self):
        # Expand by 20% Same grid size
        pxmin,pymin,pxmax,pymax=self.bounds_padded(padding_per=0.2)

        self.axes = AxisItem(pxmin,pymin,pxmax,pymax)
        self.axes.setZValue(-900)
        self.scene.addItem(self.axes)
        self.static_items.append(self.axes)

    def add_rulers(self):
        # Expand by 20% Same grid size
        pxmin,pymin,pxmax,pymax=self.bounds_padded(padding_per=0.2)
        self.ruler = RulerItem(pxmin,pymin,pxmax,pymax)
        self.ruler.setZValue(-800)
        self.scene.addItem(self.ruler)
        self.static_items.append(self.ruler)


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

    
    # --------------------------- Parser ---------------------------------
    
    def parse_to_motions(self, lines):
        motions = []
        for line in lines:
            m = self.parse_gcode_line(line)
            if m:
                motions.append(m)
        return motions

    def motions_to_svg(self, motions):
        path_cmds = []
        last_x = last_y = 0
        xmin, ymin, xmax, ymax = self.get_job_bounds()
        width  = xmax - xmin
        height = ymax - ymin

        for m in motions:
            # Skip non-motion commands
            if m.type not in ("rapid", "linear", "arc_cw", "arc_ccw"):
                continue

            x = m.x if m.x is not None else last_x
            y = m.y if m.y is not None else last_y

            # Rapid move (G0)
            if m.type == "rapid":
                path_cmds.append(f"M {x} {y}")

            # Linear move (G1)
            elif m.type == "linear":
                path_cmds.append(f"L {x} {y}")

            # Arc moves (G2/G3)
            elif m.type in ("arc_cw", "arc_ccw"):
                # SVG arc uses: A rx ry x-axis-rotation large-arc-flag sweep-flag x y
                # We approximate radius from I/J or R
                if m.r is not None:
                    r = m.r
                else:
                    # Compute radius from I/J offsets
                    dx = m.i if m.i is not None else 0
                    dy = m.j if m.j is not None else 0
                    r = (dx**2 + dy**2) ** 0.5

                sweep = 1 if m.type == "arc_cw" else 0
                path_cmds.append(f"A {r} {r} 0 0 {sweep} {x} {y}")

            last_x, last_y = x, y

        # FINAL SVG WITH CORRECT VIEWBOX 
        svg = f""" <svg xmlns="http://www.w3.org/2000/svg" 
                    version="1.1" 
                    viewBox="{xmin} {ymin} {width} {height}"> 
                    <path d="{' '.join(path_cmds)}" 
                        stroke="black" 
                        stroke-width="0.5" 
                        fill="none" /> 
                </svg> """
        return svg

    def render_svg(self):

        # Later: convert motions → SVG → QGraphicsSvgItem
        if not self.motions:
            return

        svg = self.motions_to_svg(self.motions)
        svg_bytes = svg.encode("utf-8")

        self.clear_scene(False)

        renderer = QtSvg.QSvgRenderer(svg_bytes)
        item = QtSvgWidgets.QGraphicsSvgItem()
        
        item.setSharedRenderer(renderer)

        self.scene.addItem(item)
        self.view.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)


    @staticmethod
    def parse_gcode_line(line):

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

        m = Motion(raw)

        # Command (G0, G1, G2, G3, M3, M5, etc.)
        m.cmd = parts[0].upper()

        # Determine motion type
        if m.cmd in ("G0", "G00"):
            m.type = "rapid"
        elif m.cmd in ("G1", "G01"):
            m.type = "linear"
        elif m.cmd in ("G2", "G02"):
            m.type = "arc_cw"
        elif m.cmd in ("G3", "G03"):
            m.type = "arc_ccw"
        else:
            m.type = "other"

        # Parse parameters
        for token in parts[1:]:
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
        for axis in ["x", "y", "z", "i", "j", "k", "r", "f", "s"]:
            val = getattr(m, axis)
            if val is not None:
                params.append(f"{axis.upper()}{val}")

        self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(" ".join(params)))
        self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(""))  # status

        # Auto-scroll to bottom
        self.table.scrollToBottom()
    
    def draw_motion(self, m, code_by_power=True):
        """Draw incrementally"""
        # Skip non-motion commands
        if m.type not in ("rapid", "linear", "arc_cw", "arc_ccw"):
            return

        # Track last position
        if not hasattr(self, "last_x"):
            self.last_x = 0
            self.last_y = 0

        x = m.x if m.x is not None else self.last_x
        y = m.y if m.y is not None else self.last_y

        pen = QtGui.QPen()
        pen.setWidthF(0.3)

        # Color by type
        if m.type == "rapid":
            pen.setColor(QtGui.QColor("gray"))
        else:
            if not code_by_power:
                pen.setColor(QtGui.QColor("red"))
            else:
                power = m.s or 0 
                # Map 0–255 → blue→red 
                color = QtGui.QColor.fromHsv( int((1 - power / 255) * 240), # hue 
                                            255, 255 ) 
                pen.setColor(color)

        # Linear move
        if m.type in ("rapid", "linear"):
            self.scene.addLine(self.last_x, self.last_y, x, y, pen)

        # Arc move
        elif m.type in ("arc_cw", "arc_ccw"):
            # Approximate arc with polyline (simple and fast)
            self.draw_arc_segment(self.last_x, self.last_y, x, y, m, pen)

        self.last_x = x
        self.last_y = y

        #Update toolhead
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

        # Pen selection
        pen = QtGui.QPen()
        pen.setWidthF(0.3)

        if m.type == "rapid":
            pen.setColor(QtGui.QColor("#888888"))
        elif m.s is not None:
            # Power heatmap
            power = max(0, min(255, int(m.s)))
            hue = int((1 - power / 255) * 240)
            pen.setColor(QtGui.QColor.fromHsv(hue, 255, 255))
        else:
            pen.setColor(QtGui.QColor("#ff0000"))

        # Linear moves
        if m.type in ("rapid", "linear"):
            line = self.scene.addLine(QtCore.QLineF(x0, y0, x1, y1), pen)
            self.dynamic_items.append(line)

        # Arc moves
        elif m.type in ("arc_cw", "arc_ccw"):
            self.draw_arc_segment(x0, y0, x1, y1, m, pen)

        # Update last position for simulation
        self.last_x = x1
        self.last_y = y1

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

    def sim_pause(self):
        self.set_canvas_enabled(True)
        self.sim_running = False
        self.sim_timer.stop()

    def sim_stop(self):
        self.set_canvas_enabled(True)
        self.sim_pause()
        self.sim_index = 0
        self.redraw_sim_position()

    def sim_jump_start(self):
        self.sim_pause()
        self.clear_scene(clear_all=False)

        start = self.sim_start_spin.value()

        # Redraw up to start
        for i in range(1, start + 1):
            prev = self.motions[i - 1]
            m = self.motions[i]
            self.draw_motion_segment(prev, m)

        self.sim_index = start

        self.sim_pos_spin.blockSignals(True)
        self.sim_pos_spin.setValue(start)
        self.sim_pos_spin.blockSignals(False)

        self.redraw_sim_position()


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
        self.sim_pos_spin.blockSignals(True)
        self.sim_pos_spin.setValue(end)
        self.sim_pos_spin.blockSignals(False)

        self.redraw_sim_position()
        
    def sim_step_forward(self):
        if not self.motions:
            return

        end = self.sim_end_spin.value()
        max_index = len(self.motions) - 1

        if self.sim_index < end and self.sim_index < max_index:
            self.sim_index += 1

            self.sim_pos_spin.blockSignals(True)
            self.sim_pos_spin.setValue(self.sim_index)
            self.sim_pos_spin.blockSignals(False)

            self.redraw_sim_position()
        else:
            self.sim_pause()

    def sim_step_backward(self):
        if not self.motions:
            return

        start = self.sim_start_spin.value()

        if self.sim_index > start and self.sim_index > 0:
            self.sim_index -= 1

            # Update spinbox without triggering jump
            self.sim_pos_spin.blockSignals(True)
            self.sim_pos_spin.setValue(self.sim_index)
            self.sim_pos_spin.blockSignals(False)

            self.redraw_sim_position()

    def redraw_sim_position(self):
        m = self.motions[self.sim_index]

        # Draw segment if not at first line
        if self.sim_index > 0:
            prev = self.motions[self.sim_index - 1]
            self.draw_motion_segment(prev, m)

        # Move toolhead dot
        x = m.x if m.x is not None else self.last_x
        y = m.y if m.y is not None else self.last_y
        self.tool_dot.setRect(x - 1, y - 1, 2, 2)

        # Update labels
        self.tool_label.setText(f"Tool: X={x:.2f} Y={y:.2f}")

        # Highlight table row
        self.table.selectRow(self.sim_index)
        self.table.scrollToItem(self.table.item(self.sim_index, 0))

        # Optionally center view on toolhead
        if self.center_check.isChecked():
            self.view.centerOn(x, y)

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
    def toggle_grid(self, state):
        if self.grid:
            self.grid.setVisible(bool(state))

    def update_grid_spacing(self, value):
        if self.grid:
            self.grid.spacing = value
            self.grid.update()

    def toggle_frame(self, state):
        if self.job_box:
            self.job_box.setVisible(bool(state))

    def toggle_rulers(self, state):
        if self.ruler:
            self.ruler.setVisible(bool(state))


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

        # Normalize bounds
        if left > right:
            left, right = right, left
        if top > bottom:
            top, bottom = bottom, top

        # Vertical lines
        x = left
        while x <= right:
            idx = int((x - left) / self.spacing)
            pen = self.bold_pen if (idx % self.bold_every == 0) else self.thin_pen
            painter.setPen(pen)
            painter.drawLine(QtCore.QPointF(x, top), QtCore.QPointF(x, bottom))
            x += self.spacing

        # Horizontal lines
        y = top
        while y <= bottom:
            idx = int((y - top) / self.spacing)
            pen = self.bold_pen if (idx % self.bold_every == 0) else self.thin_pen
            painter.setPen(pen)
            painter.drawLine(QtCore.QPointF(left, y), QtCore.QPointF(right, y))
            y += self.spacing


class AxisItem(QtWidgets.QGraphicsItem):
    def __init__(self, xmin, ymin, xmax, ymax):
        super().__init__()
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

    def boundingRect(self):
        return QtCore.QRectF(self.xmin, self.ymin,
                             self.xmax - self.xmin,
                             self.ymax - self.ymin)

    def paint(self, painter, option, widget):
        pen_x = QtGui.QPen(QtGui.QColor("red"))
        pen_x.setWidthF(0.5)
        pen_y = QtGui.QPen(QtGui.QColor("green"))
        pen_y.setWidthF(0.5)

        painter.setPen(pen_x)
        painter.drawLine(QtCore.QPointF(self.xmin, 0), QtCore.QPointF(self.xmax, 0))

        painter.setPen(pen_y)
        painter.drawLine(QtCore.QPointF(0, self.ymin), QtCore.QPointF(0, self.ymax))

class RulerItem(QtWidgets.QGraphicsItem):
    def __init__(self, xmin, ymin, xmax, ymax):
        super().__init__()
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

    def boundingRect(self):
        return QtCore.QRectF(self.xmin, self.ymin,
                             self.xmax - self.xmin,
                             self.ymax - self.ymin)

    def paint(self, painter, option, widget):
        painter.setPen(QtGui.QPen(QtGui.QColor(80, 80, 80), 0))
        tick = 10

        # -------------------------
        # X-axis ruler (top edge)
        # -------------------------
        y_top = self.ymin
        for x in range(int(self.xmin), int(self.xmax) + 1, 10):
            # small tick
            painter.drawLine(QtCore.QPointF(x, y_top),
                             QtCore.QPointF(x, y_top + tick))

            # label every 50 units
            if x % 50 == 0:
                painter.drawText(QtCore.QPointF(x + 2, y_top + 3 * tick), str(x))

        # -------------------------
        # Y-axis ruler (left edge)
        # -------------------------
        x_left = self.xmin
        for y in range(int(self.ymin), int(self.ymax) + 1, 10):
            # small tick
            painter.drawLine(QtCore.QPointF(x_left, y),
                             QtCore.QPointF(x_left + tick, y))

            # label every 50 units
            if y % 50 == 0:
                painter.drawText(QtCore.QPointF(x_left + 2 * tick, y + 3), str(y))



    

