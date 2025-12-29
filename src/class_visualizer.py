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

class GCodeVisualizerDialog(QtWidgets.QDialog):
    closed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("G‑code Visualizer")
        self.resize(1100, 700)

        # Variables
        self.dynamic_items = []
        self.static_items = []

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
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_zoom_in)
        self.toolbar.addAction(self.action_zoom_out)
        self.toolbar.addAction(self.action_fit)

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
        # Main Layout
        # -------------------------
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(splitter)
        layout.addLayout(status_layout)   # <-- THIS is the correct call


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
        # -------------------------
        # Grid, axes, Rulers
        # -------------------------
        self.add_grid()
        self.add_axes()
        self.add_rulers()

        # Connect actions
        self.render_actions_connect()

    def load_motions(self, motions):
        self.motions = motions
        self.populate_table()
        self.render_svg()
    
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
        self.action_fit.triggered.connect(lambda: self.view.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio))
        self.view.mouseMoved.connect(self.update_cursor_status)

    def update_cursor_status(self, x, y):
        self.cursor_label.setText(f"Cursor: X={x:.2f}  Y={y:.2f}")

    def add_grid(self):
        self.grid = GridItem(spacing=1.0, bold_every=10)
        self.scene.addItem(self.grid)
        self.grid.setZValue(-1000)
        self.static_items.append(self.grid)

    def add_axes(self):
        self.axes = AxisItem()
        self.axes.setZValue(-900)
        self.scene.addItem(self.axes)
        self.static_items.append(self.axes)

    def add_rulers(self):
        self.ruler = RulerItem()
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


    def render_svg(self):
        self.clear_scene(False) # will not delete the grid

        # Placeholder: draw axes
        self.scene.addLine(0, 0, 100, 0, QtGui.QPen(QtCore.Qt.GlobalColor.red))
        self.scene.addLine(0, 0, 0, 100, QtGui.QPen(QtCore.Qt.GlobalColor.green))

        # Later: convert motions → SVG → QGraphicsSvgItem
    
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

        # Build SVG
        svg = f"""
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1">
            <path d="{' '.join(path_cmds)}"
                stroke="black"
                stroke-width="0.5"
                fill="none" />
        </svg>
        """

        return svg

    def render_svg(self):
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
    def __init__(self, spacing=1.0, bold_every=10):
        super().__init__()
        self.spacing = spacing
        self.bold_every = bold_every

        self.thin_pen = QtGui.QPen(QtGui.QColor(200, 200, 200))
        self.thin_pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        self.thin_pen.setWidthF(0)

        self.bold_pen = QtGui.QPen(QtGui.QColor(150, 150, 150))
        self.bold_pen.setWidthF(0.4)

    def boundingRect(self):
        return QtCore.QRectF(-5000, -5000, 10000, 10000)

    def paint(self, painter, option, widget):
        left, top, right, bottom = -5000, -5000, 5000, 5000

        # Vertical lines
        x = left
        while x <= right:
            pen = self.bold_pen if (abs(x) % (self.spacing * self.bold_every) < 0.001) else self.thin_pen
            painter.setPen(pen)
            painter.drawLine(QtCore.QPointF(x, top), QtCore.QPointF(x, bottom))
            x += self.spacing

        # Horizontal lines
        y = top
        while y <= bottom:
            pen = self.bold_pen if (abs(y) % (self.spacing * self.bold_every) < 0.001) else self.thin_pen
            painter.setPen(pen)
            painter.drawLine(QtCore.QPointF(left, y), QtCore.QPointF(right, y))
            y += self.spacing

class AxisItem(QtWidgets.QGraphicsItem):
    def boundingRect(self):
        return QtCore.QRectF(-5000, -5000, 10000, 10000)

    def paint(self, painter, option, widget):
        pen_x = QtGui.QPen(QtGui.QColor("red"))
        pen_x.setWidthF(0.5)
        pen_y = QtGui.QPen(QtGui.QColor("green"))
        pen_y.setWidthF(0.5)

        painter.setPen(pen_x)
        painter.drawLine(-5000, 0, 5000, 0)

        painter.setPen(pen_y)
        painter.drawLine(0, -5000, 0, 5000)

class RulerItem(QtWidgets.QGraphicsItem):
    def boundingRect(self):
        return QtCore.QRectF(-5000, -5000, 10000, 10000)

    def paint(self, painter, option, widget):
        painter.setPen(QtGui.QPen(QtGui.QColor(80, 80, 80), 0))

        # X-axis ruler (top)
        for x in range(-5000, 5001, 10):
            painter.drawLine(x, -5000, x, -4990)
            if x % 50 == 0:
                painter.drawText(QtCore.QPointF(x + 1, -4980), str(x))

        # Y-axis ruler (left)
        for y in range(-5000, 5001, 10):
            painter.drawLine(-5000, y, -4990, y)
            if y % 50 == 0:
                painter.drawText(QtCore.QPointF(-4980, y + 3), str(y))


    

