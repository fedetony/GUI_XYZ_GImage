from PyQt6 import QtWidgets, QtCore, QtGui

class DualSliderWidget(QtWidgets.QWidget):
    startChanged = QtCore.pyqtSignal(int)
    endChanged = QtCore.pyqtSignal(int)
    posChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pos_slider = PositionSlider()
        self.range_slider = RangeSlider()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.pos_slider)
        layout.addWidget(self.range_slider)

        # Connect signals
        self.pos_slider.valueChanged.connect(self.posChanged)
        self.range_slider.startChanged.connect(self.startChanged)
        self.range_slider.endChanged.connect(self.endChanged)

    # Unified API
    def setRange(self, mn, mx):
        self.pos_slider.setRange(mn, mx)
        self.range_slider.setRange(mn, mx)

    def setStart(self, v):
        self.range_slider.setStart(v)

    def setEnd(self, v):
        self.range_slider.setEnd(v)

    def setPosition(self, v):
        self.pos_slider.setValue(v)

class RangeSlider(QtWidgets.QWidget):
    startChanged = QtCore.pyqtSignal(int)
    endChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._min = 0
        self._max = 100
        self._start = 0
        self._end = 100
        self._dragging = None
        self.setMinimumHeight(30)

    def setRange(self, mn, mx):
        self._min, self._max = mn, mx
        self._start = max(mn, min(self._start, mx))
        self._end = max(self._start, min(self._end, mx))
        self.update()

    def setStart(self, v):
        self._start = max(self._min, min(v, self._end))
        self.startChanged.emit(self._start)
        self.update()

    def setEnd(self, v):
        self._end = min(self._max, max(v, self._start))
        self.endChanged.emit(self._end)
        self.update()

    def _value_to_x(self, v):
        w = self.width() - 20
        return 10 + (v - self._min) / (self._max - self._min) * w

    def _x_to_value(self, x):
        w = self.width() - 20
        x = max(10, min(x, self.width() - 10))
        return int(self._min + (x - 10) / w * (self._max - self._min))

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Track
        p.setPen(QtGui.QPen(QtGui.QColor("#888"), 3))
        p.drawLine(QtCore.QPointF(10, 15), QtCore.QPointF(self.width() - 10, 15))

        # Range highlight
        p.setPen(QtGui.QPen(QtGui.QColor("#4a8"), 4))
        p.drawLine(
            QtCore.QPointF(self._value_to_x(self._start), 15),
            QtCore.QPointF(self._value_to_x(self._end), 15)
        )

        size = 8

        # Start ▲
        sx = self._value_to_x(self._start)
        p.setBrush(QtGui.QColor("#3c3"))
        p.setPen(QtGui.QPen(QtGui.QColor("black"), 1))
        p.drawPolygon(QtGui.QPolygonF([
            QtCore.QPointF(sx, 15 - size),
            QtCore.QPointF(sx - size, 15 + size),
            QtCore.QPointF(sx + size, 15 + size)
        ]))

        # End ▲
        ex = self._value_to_x(self._end)
        p.setBrush(QtGui.QColor("#c33"))
        p.drawPolygon(QtGui.QPolygonF([
            QtCore.QPointF(ex, 15 - size),
            QtCore.QPointF(ex - size, 15 + size),
            QtCore.QPointF(ex + size, 15 + size)
        ]))

    def mousePressEvent(self, event):
        x = event.position().x()
        sx = self._value_to_x(self._start)
        ex = self._value_to_x(self._end)
        hit = 12

        if abs(x - sx) < hit:
            self._dragging = "start"
        elif abs(x - ex) < hit:
            self._dragging = "end"

    def mouseMoveEvent(self, event):
        if not self._dragging:
            return
        v = self._x_to_value(event.position().x())
        if self._dragging == "start":
            self.setStart(v)
        elif self._dragging == "end":
            self.setEnd(v)

    def mouseReleaseEvent(self, event):
        self._dragging = None

class PositionSlider(QtWidgets.QWidget):
    valueChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._min = 0
        self._max = 100
        self._value = 0
        self._dragging = False
        self.setMinimumHeight(30)

    def setRange(self, mn, mx):
        self._min, self._max = mn, mx
        self._value = max(mn, min(self._value, mx))
        self.update()

    def setValue(self, v):
        self._value = max(self._min, min(v, self._max))
        self.valueChanged.emit(self._value)
        self.update()

    def _value_to_x(self, v):
        w = self.width() - 20
        return 10 + (v - self._min) / (self._max - self._min) * w

    def _x_to_value(self, x):
        w = self.width() - 20
        x = max(10, min(x, self.width() - 10))
        return int(self._min + (x - 10) / w * (self._max - self._min))

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Track
        p.setPen(QtGui.QPen(QtGui.QColor("#888"), 3))
        p.drawLine(QtCore.QPointF(10, 15), QtCore.QPointF(self.width() - 10, 15))

        # Handle ▼
        x = self._value_to_x(self._value)
        size = 8
        p.setBrush(QtGui.QColor("#39f"))
        p.setPen(QtGui.QPen(QtGui.QColor("black"), 1))
        points = [
            QtCore.QPointF(x, 15 + size),
            QtCore.QPointF(x - size, 15 - size),
            QtCore.QPointF(x + size, 15 - size)
        ]
        p.drawPolygon(QtGui.QPolygonF(points))

    def mousePressEvent(self, event):
        x = event.position().x()
        if abs(x - self._value_to_x(self._value)) < 12:
            self._dragging = True

    def mouseMoveEvent(self, event):
        if self._dragging:
            self.setValue(self._x_to_value(event.position().x()))

    def mouseReleaseEvent(self, event):
        self._dragging = False

class TripleSliderTriangles(QtWidgets.QWidget):
    startChanged = QtCore.pyqtSignal(int)
    endChanged = QtCore.pyqtSignal(int)
    posChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._min = 0
        self._max = 100
        self._start = 0
        self._end = 100
        self._pos = 0

        self._dragging = None
        self.setMinimumHeight(40)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def setRange(self, minimum, maximum):
        self._min = minimum
        self._max = maximum

        self._start = max(minimum, min(self._start, maximum))
        self._end   = max(self._start, min(self._end, maximum))
        self._pos   = max(self._start, min(self._pos, self._end))

        self.update()

    def setStart(self, value):
        self._start = max(self._min, min(value, self._end))
        self.startChanged.emit(self._start)
        if self._pos < self._start:
            self.setPosition(self._start)
        self.update()

    def setEnd(self, value):
        self._end = min(self._max, max(value, self._start))
        self.endChanged.emit(self._end)
        if self._pos > self._end:
            self.setPosition(self._end)
        self.update()

    def setPosition(self, value):
        self._pos = max(self._start, min(value, self._end))
        self.posChanged.emit(self._pos)
        self.update()

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _value_to_x(self, v):
        w = self.width() - 20
        return 10 + (v - self._min) / (self._max - self._min) * w

    def _x_to_value(self, x):
        w = self.width() - 20
        x = max(10, min(x, self.width() - 10))
        return int(self._min + (x - 10) / w * (self._max - self._min))

    # ---------------------------------------------------------
    # Painting
    # ---------------------------------------------------------

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Track
        p.setPen(QtGui.QPen(QtGui.QColor("#888"), 3))
        p.drawLine(QtCore.QPointF(10, 20), QtCore.QPointF(self.width() - 10, 20))

        # Range highlight
        p.setPen(QtGui.QPen(QtGui.QColor("#4a8"), 4))
        p.drawLine(
            QtCore.QPointF(self._value_to_x(self._start), 20),
            QtCore.QPointF(self._value_to_x(self._end), 20)
        )

        # Start handle (UP triangle)
        self._draw_triangle_up(
            p,
            self._value_to_x(self._start),
            20,
            8,
            QtGui.QColor("#3c3")
        )

        # End handle (DOWN triangle)
        self._draw_triangle_down(
            p,
            self._value_to_x(self._end),
            20,
            8,
            QtGui.QColor("#c33")
        )

        # Position handle (DOWN triangle, blue)
        self._draw_triangle_up(
            p,
            self._value_to_x(self._pos),
            20,
            8,
            QtGui.QColor("#39f")
        )

    def _draw_triangle_up(self, p, x, y, size, color):
        p.setBrush(color)
        p.setPen(QtGui.QPen(QtGui.QColor("black"), 1))
        points = [
            QtCore.QPointF(x, y - size),
            QtCore.QPointF(x - size, y + size),
            QtCore.QPointF(x + size, y + size)
        ]
        p.drawPolygon(QtGui.QPolygonF(points))

    def _draw_triangle_down(self, p, x, y, size, color):
        p.setBrush(color)
        p.setPen(QtGui.QPen(QtGui.QColor("black"), 1))
        points = [
            QtCore.QPointF(x, y + size),
            QtCore.QPointF(x - size, y - size),
            QtCore.QPointF(x + size, y - size)
        ]
        p.drawPolygon(QtGui.QPolygonF(points))

    # ---------------------------------------------------------
    # Mouse interaction
    # ---------------------------------------------------------

    def mousePressEvent(self, event):
        x = event.position().x()
        sx = self._value_to_x(self._start)
        ex = self._value_to_x(self._end)
        px = self._value_to_x(self._pos)

        hit = 12

        if abs(x - sx) < hit:
            self._dragging = "start"
        elif abs(x - ex) < hit:
            self._dragging = "end"
        elif abs(x - px) < hit:
            self._dragging = "pos"

    def mouseMoveEvent(self, event):
        if not self._dragging:
            return

        v = self._x_to_value(event.position().x())

        if self._dragging == "start":
            self.setStart(v)
        elif self._dragging == "end":
            self.setEnd(v)
        elif self._dragging == "pos":
            self.setPosition(v)

    def mouseReleaseEvent(self, event):
        self._dragging = None


class TripleSlider(QtWidgets.QWidget):
    startChanged = QtCore.pyqtSignal(int)
    endChanged = QtCore.pyqtSignal(int)
    posChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._min = 0
        self._max = 100
        self._start = 0
        self._end = 100
        self._pos = 0

        self.setMinimumHeight(40)

        self._dragging = None  # "start", "end", "pos"

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def setRange(self, minimum, maximum):
        self._min = minimum
        self._max = maximum
        self.update()
    
    def setMaximum(self, value: int):
        self.setRange(self._min, value)
    
    def setMinimum(self, value: int):
        self.setRange(value,self._max)

    def setStart(self, value):
        self._start = max(self._min, min(value, self._end))
        self.startChanged.emit(self._start)
        self.update()

    def setEnd(self, value):
        self._end = min(self._max, max(value, self._start))
        self.endChanged.emit(self._end)
        self.update()

    def setPosition(self, value):
        self._pos = max(self._start, min(value, self._end))
        self.posChanged.emit(self._pos)
        self.update()

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _value_to_x(self, v):
        w = self.width() - 20
        return 10 + (v - self._min) / (self._max - self._min) * w

    def _x_to_value(self, x):
        w = self.width() - 20
        x = max(10, min(x, self.width() - 10))
        return int(self._min + (x - 10) / w * (self._max - self._min))

    # ---------------------------------------------------------
    # Painting
    # ---------------------------------------------------------

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Track
        p.setPen(QtGui.QPen(QtGui.QColor("#888"), 3))
        p.drawLine(
            QtCore.QPointF(10.0, 20.0),
            QtCore.QPointF(float(self.width() - 10), 20.0)
        )

        # Range highlight
        p.setPen(QtGui.QPen(QtGui.QColor("#4a8"), 4))
        p.drawLine(
            QtCore.QPointF(float(self._value_to_x(self._start)), 20.0),
            QtCore.QPointF(float(self._value_to_x(self._end)), 20.0)
        )

        # # Start handle
        # self._draw_handle(p, float(self._value_to_x(self._start)), QtGui.QColor("#3c3"))

        # # End handle
        # self._draw_handle(p, float(self._value_to_x(self._end)), QtGui.QColor("#c33"))

        # # Position handle
        # self._draw_handle(p, float(self._value_to_x(self._pos)), QtGui.QColor("#39f"))
        # Start handle (UP triangle)
        self._draw_triangle_up(
            p,
            float(self._value_to_x(self._start)),
            20.0,
            8,
            QtGui.QColor("#2D41FA")
        )

        # End handle (DOWN triangle)
        self._draw_triangle_down(
            p,
            float(self._value_to_x(self._end)),
            20.0,
            8,
            QtGui.QColor("#c33")
        )

        # Position handle (DOWN triangle, blue)
        self._draw_triangle_down(
            p,
            float(self._value_to_x(self._pos)),
            20.0,
            8,
            QtGui.QColor("#F3F3F3")#"#39f")
        )




    def _draw_handle(self, p, x, color):
        p.setBrush(color)
        p.setPen(QtGui.QPen(QtGui.QColor("black"), 1))

        size = 8  # triangle size

        points = [
            QtCore.QPointF(x, 20 - size),      # top
            QtCore.QPointF(x - size, 20 + size),
            QtCore.QPointF(x + size, 20 + size)
        ]

        polygon = QtGui.QPolygonF(points)
        p.drawPolygon(polygon)

    def _draw_triangle_up(self, p, x, y, size, color):
        p.setBrush(color)
        p.setPen(QtGui.QPen(QtGui.QColor("black"), 1))

        points = [
            QtCore.QPointF(x, y - size),
            QtCore.QPointF(x - size, y + size),
            QtCore.QPointF(x + size, y + size)
        ]
        p.drawPolygon(QtGui.QPolygonF(points))


    def _draw_triangle_down(self, p, x, y, size, color):
        p.setBrush(color)
        p.setPen(QtGui.QPen(QtGui.QColor("black"), 1))

        points = [
            QtCore.QPointF(x, y + size),
            QtCore.QPointF(x - size, y - size),
            QtCore.QPointF(x + size, y - size)
        ]
        p.drawPolygon(QtGui.QPolygonF(points))




    # ---------------------------------------------------------
    # Mouse interaction
    # ---------------------------------------------------------

    def mousePressEvent(self, event):
        x = event.position().x()
        sx = self._value_to_x(self._start)
        ex = self._value_to_x(self._end)
        px = self._value_to_x(self._pos)

        if abs(x - sx) < 10:
            self._dragging = "start"
        elif abs(x - ex) < 10:
            self._dragging = "end"
        elif abs(x - px) < 10:
            self._dragging = "pos"

    def mouseMoveEvent(self, event):
        if not self._dragging:
            return

        v = self._x_to_value(event.position().x())

        if self._dragging == "start":
            self.setStart(v)
        elif self._dragging == "end":
            self.setEnd(v)
        elif self._dragging == "pos":
            self.setPosition(v)

    def mouseReleaseEvent(self, event):
        self._dragging = None



# from PyQt6 import QtWidgets, QtCore
# import pyqtgraph as pg


# class SimTripleSlider(QtWidgets.QWidget):
#     startChanged = QtCore.pyqtSignal(int)
#     endChanged = QtCore.pyqtSignal(int)
#     posChanged = QtCore.pyqtSignal(int)

#     def __init__(self, parent=None):
#         super().__init__(parent)
        
#         self.range_slider = pg.widgets.RangeSlider.RangeSlider(orientation='horizontal')
#         self.range_slider.setMouseEnabled(True)

#         self.pos_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
#         self.pos_slider.setSingleStep(1)
#         self.pos_slider.setPageStep(10)
#         self.pos_slider.setTracking(True)

#         # Stack them visually
#         layout = QtWidgets.QVBoxLayout(self)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.setSpacing(0)
#         layout.addWidget(self.range_slider)
#         layout.addWidget(self.pos_slider)

#         # Connect signals
#         self.range_slider.sigRegionChanged.connect(self._on_range_changed)
#         self.pos_slider.valueChanged.connect(self._on_pos_changed)

#         # Internal state
#         self._max = 0

#     # ------------------------------
#     # Public API
#     # ------------------------------

#     def setMaximum(self, max_value: int):
#         self._max = max_value
#         self.range_slider.setLimits(0, max_value)
#         self.range_slider.setRegion((0, max_value))
#         self.pos_slider.setRange(0, max_value)

#     def setStart(self, value: int):
#         lo, hi = self.range_slider.getRegion()
#         self.range_slider.setRegion((value, hi))

#     def setEnd(self, value: int):
#         lo, hi = self.range_slider.getRegion()
#         self.range_slider.setRegion((lo, value))

#     def setPosition(self, value: int):
#         self.pos_slider.setValue(value)

#     # ------------------------------
#     # Internal signal handlers
#     # ------------------------------

#     def _on_range_changed(self):
#         lo, hi = self.range_slider.getRegion()

#         # Enforce: start ≤ pos ≤ end
#         if self.pos_slider.value() < lo:
#             self.pos_slider.setValue(lo)
#         if self.pos_slider.value() > hi:
#             self.pos_slider.setValue(hi)

#         self.startChanged.emit(int(lo))
#         self.endChanged.emit(int(hi))

#     def _on_pos_changed(self, value):
#         lo, hi = self.range_slider.getRegion()

#         # Clamp inside range
#         if value < lo:
#             self.pos_slider.setValue(lo)
#             return
#         if value > hi:
#             self.pos_slider.setValue(hi)
#             return

#         self.posChanged.emit(value)
