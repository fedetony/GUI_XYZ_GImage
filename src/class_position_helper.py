import sys
from PyQt6 import QtWidgets, QtGui, QtCore

import math
import logging

MAIN_STRUCT_EXAMPLE={
        "Machine": [  
                {"Axes": {"value": ['X','Y','Z'], "type": "list", "subtype": "str", "meta": {"editable": False }}},
                {"Mapping": [
                    {"X": {"value": "X", "type": "str", "meta": {"options": ["X", "Y", "Z", "A", "B", "C","E","F","S"]}}},
                    {"Y": {"value": "Y", "type": "str", "meta": {"options": ["X", "Y", "Z", "A", "B", "C","E","F","S"]}}},
                    {"Z": {"value": "Z", "type": "str", "meta": {"options": ["X", "Y", "Z", "A", "B", "C","E","F","S"]}}},
                ]},
                {"Size": {"value": [700, 800, 200], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [0.01,0.01,0.01], "max": [10**6,10**6,10**6]}, "decimals": 2}}},
                {"Anchor": {"value": [0.5, 0.5, 0.5], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": {"arity": 3, "min": [0.0,0.0,0.0], "max": [1,1,1]}, "decimals": 2}}},
                {"Position": {"value": [0.0, 0.0, 0.0], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [-10**6,-10**6,-10**6], "max": [10**6,10**6,10**6]}, "decimals": 3}}},
            ],
        "Workspace": [                  
                {"Size": {"value": [650, 700, 100], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [0.01,0.01,0.01], "max": [10**6,10**6,10**6]}, "decimals": 2}}},
                {"Anchor": {"value": [0.5, 0.5, 0.5], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": {"arity": 3, "min": [0.0,0.0,0.0], "max": [1,1,1]}, "decimals": 2}}},
                {"Position": {"value": [10.0, 10.0, 10.0], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [-10**6,-10**6,-10**6], "max": [10**6,10**6,10**6]}, "decimals": 3}}},
            ],
        "Material": [                  
                {"Size": {"value": [270, 210, 3], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [0.01,0.01,0.01], "max": [10**6,10**6,10**6]}, "decimals": 2}}},
                {"Anchor": {"value": [0.5, 0.5, 0.5], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": {"arity": 3, "min": [0.0,0.0,0.0], "max": [1,1,1]}, "decimals": 2}}},
                {"Position": {"value": [10.0, 10.0, 10.0], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [-10**6,-10**6,-10**6], "max": [10**6,10**6,10**6]}, "decimals": 3}}},
            ],
        "Head": [                  
                {"Size": {"value": [40, 40, 30], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [0.01,0.01,0.01], "max": [10**6,10**6,10**6]}, "decimals": 2}}},
                {"Anchor": {"value": [0.5, 0.5, 1], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": {"arity": 3, "min": [0.0,0.0,0.0], "max": [1,1,1]}, "decimals": 2}}},
                {"Position": {"value": [10.0, 10.0, 80.0], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [-10**6,-10**6,-10**6], "max": [10**6,10**6,10**6]}, "decimals": 3}}},
            ],
        "Tool": [                  
                {"Tool Type": {"value": "pencil", "type": "str", "meta": {"options": ["pen","pencil","laser"]}}},
                {"Size": {"value": [5, 5, 100], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [0.01,0.01,0.01], "max": [10**6,10**6,10**6]}, "decimals": 2}}},
                {"Anchor": {"value": [0.5, 0.5, 1], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": {"arity": 3, "min": [0.0,0.0,0.0], "max": [1,1,1]}, "decimals": 2}}},
                {"Position": {"value": [10.0, 10.0, 40.0], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [-10**6,-10**6,-10**6], "max": [10**6,10**6,10**6]}, "decimals": 3}}},
            ]
        }

FIELDS_POSITION=[
    {"name": "ITEM",  "editable": False, "selectable": True,  "hidden": False},
    {"name": "VALUE", "editable": True,  "selectable": True,  "hidden": False},
    {"name": "TYPE",  "editable": False, "selectable": False, "hidden": True},
    {"name": "UNIT",  "editable": False, "selectable": True, "hidden": False},
    {"name": "INFO",  "editable": True, "selectable": True, "hidden": False},
]

# Add logger
ph_fun_name="PositionHelper"
from class_LogHandler import get_appPath, LM ,init_logger_manager
try:
    log = LM.get_logger_with_handler(ph_fun_name,
                                     "debug",
                                     True,
                                     "%(asctime)s [%(levelname)s] (%(name)s) %(message)s")
    log.info(f"{ph_fun_name} Logger started")
except (AttributeError, ImportError):
    LM = init_logger_manager(None)
    log = LM.get_logger(__name__)
    log.info("Application starting...")

import class_treeview_functions
import class_struct_tracker
import class_struct_conditioner
# ----------------- 3D model -----------------
class CNCObject3D:
    """
    Represents a 3D object in the CNC scene graph.

    Coordinate System
    -----------------
    All objects store their position in *world coordinates*:

        x → world X position
        y → world Y position
        z → world Z position

    These values always represent the absolute position of the object
    in the global 3D space, regardless of parenting.

    Parenting
    ---------
    When an object has a parent, its relative position is stored in:

        local_dx = x - parent.x
        local_dy = y - parent.y
        local_dz = z - parent.z

    These local offsets are updated only when the user (or code)
    moves the child directly. When the parent moves, the child’s
    world coordinates are recomputed from the stored local offsets.

    Views
    -----
    Each 2D projection uses the appropriate world axes:

        XY view → (x, y)
        XZ view → (x, z)
        YZ view → (y, z)

    Shapes in each view are scaled using the corresponding dimensions:

        XY → (w, h)
        XZ → (w, d)
        YZ → (h, d)

    Summary
    -------
    - x, y, z are ALWAYS world coordinates.
    - local_dx/dy/dz store the child’s offset relative to its parent.
    - Moving a child updates both world and local coordinates.
    - Moving a parent updates only world coordinates (children follow).
    - Views and shapes derive directly from world coordinates.
    """

    def __init__(self, name):
        self.name = name
        self.parent = None
        self.children = []

        # 3D position
        self.x = 0
        self.y = 0
        self.z = 0

        # Size
        self.w = 50
        self.h = 50
        self.d = 50

        # Anchor (fractions)
        self.anchor_x = 0.5
        self.anchor_y = 0.5
        self.anchor_z = 0.5

        # References to projected items
        self.item_xy = None
        self.item_xz = None
        self.item_yz = None

        # Local offsets (relative to parent)
        self.local_dx = 0
        self.local_dy = 0
        self.local_dz = 0

    def move_to(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def resize_to(self, w, h, d):
        self.w = w
        self.h = h
        self.d = d

    def attach_child(self, child):
        """Attach a child object and compute its local offsets once."""
        child.parent = self
        self.children.append(child)

        # Compute local offsets ONCE
        child.local_dx = child.x - self.x
        child.local_dy = child.y - self.y
        child.local_dz = child.z - self.z

    def update_children_recursive(self, obj):
        for child in obj.children:
            # update child world position from parent
            child.x = obj.x + child.local_dx
            child.y = obj.y + child.local_dy
            child.z = obj.z + child.local_dz

            # update child graphics
            child.item_xy.update_from_model()
            child.item_xz.update_from_model()
            child.item_yz.update_from_model()

            # recurse
            self.update_children_recursive(child)

    def anchor_world(self):
        ax = self.x + self.w * self.anchor_x
        ay = self.y + self.h * self.anchor_y
        az = self.z + self.d * self.anchor_z
        return ax, ay, az

    def anchor_xy(self):
        # projected anchor in XY (top view)
        ax = self.x + self.w * self.anchor_x
        ay = self.y + self.h * self.anchor_y
        return QtCore.QPointF(ax, ay)

    def anchor_xz(self):
        # projected anchor in XZ (side view)
        ax = self.x + self.w * self.anchor_x
        az = self.z + self.d * self.anchor_z
        return QtCore.QPointF(ax, az)

    def anchor_yz(self):
        # projected anchor in YZ (side view)
        ay = self.y + self.h * self.anchor_y
        az = self.z + self.d * self.anchor_z
        return QtCore.QPointF(ay, az)


# ----------------- Base projected item -----------------
class ProjectedItem(QtWidgets.QGraphicsRectItem):
    """
    A 2D projection of a CNCObject3D into one of the planes:
    - XY: (x, y)
    - XZ: (x, z)
    - YZ: (y, z)
    """

    PlaneXY = 0
    PlaneXZ = 1
    PlaneYZ = 2

    def __init__(self, obj: CNCObject3D, plane, on_model_changed, color, parent=None):
        super().__init__(parent)
        self.obj = obj
        self.plane = plane
        self.on_model_changed = on_model_changed  # callback to notify dialog
        self.allow_user_resize=(True,True)
        # default rectangle 
        self.base_polygon = None # normalized polygon (0..1) 
        self.anchor = (0.5, 0.5) # normalized anchor 
        self.shape_item = QtWidgets.QGraphicsPolygonItem(self)

        self.setBrush(QtGui.QColor(color).lighter(160))
        self.setPen(QtGui.QPen(QtGui.QColor(color), 2))
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

        self.anchor_item = None
        self._build_geometry()
        self._create_anchor_item()
        self.update_from_model()
        self.handles = []
        self._create_resize_handles()
        self._update_shape()

    def set_shape(self, polygon_points, anchor=(0.5, 0.5)):
        """
        polygon_points: list of (x,y) in normalized 0..1 space
        anchor: (ax, ay) also in 0..1 space
        """
        self.base_polygon = polygon_points
        self.anchor = anchor
        self._update_shape()

    def _update_shape(self):
        if self.base_polygon is None:
            return  # no custom shape yet
        w = getattr(self, "_plane_w", self.obj.w) 
        h = getattr(self, "_plane_h", self.obj.h)
        poly = QtGui.QPolygonF()
        for x, y in self.base_polygon:
            px = x * w
            py = y * h
            poly.append(QtCore.QPointF(px, py))
        self.shape_item.setPolygon(poly)

    def reset_handles(self ,allow_x=True, allow_y=True):
        """Resets permissions for user resizing, and sets the handles accordingly"""
        self.allow_user_resize=(allow_x,allow_y)
        #clear handles
        self.handles = []
        self._create_resize_handles()

    def _create_resize_handles(self):
        # Right-side handle (controls width or height depending on plane)
        if self.plane == self.PlaneXY:
            if self.allow_user_resize[0]:
                axis = "x"   # width
                handle = ResizeHandle(self, axis, self._on_resize)
                handle.setPos(self.rect().width(), self.rect().height() / 2)
                self.handles.append(handle)
            if self.allow_user_resize[1]:
                axis = "y"   # height
                handle = ResizeHandle(self, axis, self._on_resize)
                handle.setPos(self.rect().width() / 2, self.rect().height())
                self.handles.append(handle)

        elif self.plane == self.PlaneXZ:
            if self.allow_user_resize[0]:
                axis = "x"   # width
                handle = ResizeHandle(self, axis, self._on_resize)
                handle.setPos(self.rect().width(), self.rect().height() / 2)
                self.handles.append(handle)
            
            if self.allow_user_resize[1]:
                axis = "z"   # depth
                handle = ResizeHandle(self, axis, self._on_resize)
                handle.setPos(self.rect().width() / 2, self.rect().height())
                self.handles.append(handle)

        elif self.plane == self.PlaneYZ:
            if self.allow_user_resize[0]:
                axis = "y"   # height
                handle = ResizeHandle(self, axis, self._on_resize)
                handle.setPos(self.rect().width(), self.rect().height() / 2)
                self.handles.append(handle)
            if self.allow_user_resize[1]:
                axis = "z"   # depth
                handle = ResizeHandle(self, axis, self._on_resize)
                handle.setPos(self.rect().width() / 2, self.rect().height())
                self.handles.append(handle)

    def _on_resize(self, axis, dx, dy):
        if axis == "x":
            self.obj.w = max(3, self.obj.w + dx)
        elif axis == "y":
            self.obj.h = max(3, self.obj.h + dy)
        elif axis == "z":
            self.obj.d = max(3, self.obj.d + dy)

        # Notify controller
        if self.on_model_changed:
            self.on_model_changed(self.obj)


    def _build_geometry(self):
        if self.plane == self.PlaneXY:
            self.setRect(0, 0, self.obj.w, self.obj.h)
        elif self.plane == self.PlaneXZ:
            self.setRect(0, 0, self.obj.w, self.obj.d)
        elif self.plane == self.PlaneYZ:
            self.setRect(0, 0, self.obj.h, self.obj.d)

    def _create_anchor_item(self):
        # small crosshair
        self.anchor_item = QtWidgets.QGraphicsLineItem(self)
        pen = QtGui.QPen(QtGui.QColor("red"), 1)
        self.anchor_item.setPen(pen)

    def update_anchor_visual(self):
        r = self.rect()

        if self.plane == self.PlaneXY:
            ax = r.width() * self.obj.anchor_x
            ay = r.height() * self.obj.anchor_y
        elif self.plane == self.PlaneXZ:
            ax = r.width() * self.obj.anchor_x
            ay = r.height() * self.obj.anchor_z
        else:  # YZ
            ax = r.width() * self.obj.anchor_y
            ay = r.height() * self.obj.anchor_z

        size = 3
        # Horizontal line
        self.anchor_item.setLine(ax - size, ay, ax + size, ay)
        # Vertical line
        if not hasattr(self, "_anchor_v"):
            self._anchor_v = QtWidgets.QGraphicsLineItem(self)
            self._anchor_v.setPen(self.anchor_item.pen())

        self._anchor_v.setLine(ax, ay - size, ax, ay + size)

    def update_from_model(self):
        # Update rect size
        if self.plane == self.PlaneXY:
            self.setRect(0, 0, self.obj.w, self.obj.h)
            w = self.obj.w 
            h = self.obj.h
        elif self.plane == self.PlaneXZ:
            self.setRect(0, 0, self.obj.w, self.obj.d)
            w = self.obj.w 
            h = self.obj.d
        elif self.plane == self.PlaneYZ:
            self.setRect(0, 0, self.obj.h, self.obj.d)
            w = self.obj.h 
            h = self.obj.d

        # Update position
        if self.plane == self.PlaneXY:
            self.setPos(self.obj.x, self.obj.y)
        elif self.plane == self.PlaneXZ:
            self.setPos(self.obj.x, self.obj.z)
        elif self.plane == self.PlaneYZ:
            self.setPos(self.obj.y, self.obj.z)

        # Update anchor and handles
        self.update_anchor_visual()

        if not hasattr(self,"handles"):
            return
        # for h in self.handles:
        #     h.setPos(h.pos())  # force reposition
        self._update_handle_positions()
        # store for shape update 
        self._plane_w = w 
        self._plane_h = h
        # Update shape
        self._update_shape()


    def _update_handle_positions(self):
        r = self.rect()

        for h in self.handles:
            if h.axis == "x":
                # right side
                h.setPos(r.width(), r.height() / 2)
            elif h.axis == "y":
                # bottom side (XY or YZ)
                h.setPos(r.width() / 2, r.height())
            elif h.axis == "z":
                # bottom side (XZ or YZ)
                h.setPos(r.width() / 2, r.height())

    def hoverMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        if self.plane == self.PlaneXY:
            self.setToolTip(f"{self.obj.name}\nX: {scene_pos.x():.2f}, Y: {scene_pos.y():.2f}")
        elif self.plane == self.PlaneXZ:
            self.setToolTip(f"{self.obj.name}\nX: {scene_pos.x():.2f}, Z: {scene_pos.y():.2f}")
        else:
            self.setToolTip(f"{self.obj.name}\nY: {scene_pos.x():.2f}, Z: {scene_pos.y():.2f}")
        super().hoverMoveEvent(event)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            new_pos = QtCore.QPointF(value)

            # Update model based on plane
            if self.plane == self.PlaneXY:
                # XY view controls X and Y
                self.obj.x = new_pos.x()
                self.obj.y = new_pos.y()
            elif self.plane == self.PlaneXZ:
                # XZ view controls X and Z
                self.obj.x = new_pos.x()
                self.obj.z = new_pos.y()
            elif self.plane == self.PlaneYZ:
                # YZ view controls Y and Z
                self.obj.y = new_pos.x()
                self.obj.z = new_pos.y()

            # Update local offsets 
            parent = self.obj.parent 
            if parent is not None:
                self.obj.local_dx = self.obj.x - parent.x 
                self.obj.local_dy = self.obj.y - parent.y 
                self.obj.local_dz = self.obj.z - parent.z

            # Notify controller so other views can update
            if self.on_model_changed:
                self.on_model_changed(self.obj)

            return new_pos

        return super().itemChange(change, value)


# ----------------- Main dialog with 3 views -----------------
class PositionHelper(QtWidgets.QMainWindow): #QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Positioning Helper: Size & Coordinate Editor (XY, XZ, YZ) ")
        self.resize(1200, 800)

        self.objects = []
        self.items_xy = {}
        self.items_xz = {}
        self.items_yz = {}
        self.world_sizes=[1,1,1]
        self.zoom = 1.0
        self._changing_from_code=False

        self._build_ui()
        self._build_configutation()
        self._build_model()
        self._build_views()
        self._apply_shapes()
        self._sync_view_sizes(self.world_sizes[0],self.world_sizes[1],self.world_sizes[2])
        self._fit_all()

    def _build_configutation(self):
        self._do_evaluation=False
        self.positions_struct=MAIN_STRUCT_EXAMPLE
        self.phtv=class_treeview_functions.TreeviewFunctions(self.positions_tree,self.positions_struct,FIELDS_POSITION)
        # attach delegate to VALUE column (1)
        delegate = class_treeview_functions.TypedItemDelegate(self.phtv)
        self.positions_tree.setItemDelegateForColumn(1, delegate)
        self.phtv.data_change[list,object,str,str].connect(self.on_tree_item_edited)
        self.phtv.struct_data_change[list,object,str,str].connect(self.on_struct_item_edited)
        self.phtv.expand_to_depth(1) #333) #Expand all
        # Condition Engine
        self.phce=class_struct_conditioner.ConditionEngine(self.phtv.tracker)
        self._evaluate_conditions()
        
        # Add cache tooltip, icons, backgrounds, styles
        # self.tv.set_icons_cache(self.all_icons_dict)
        # self.tv.set_style_cache(self.style_dict)

        # Right click Menu 
        self.phtv.treeviewobj.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.phtv.treeviewobj.customContextMenuRequested.connect(self.phtv._on_context_menu)
        #self.phtv.item_right_clicked.connect(self.on_item_right_clicked)
        
        self.phtv.do_refresh()
        
    @QtCore.pyqtSlot(list, object, object, str, str)
    def on_tree_item_edited_old_new(self, track, old_value, new_value, typestr, subtype):
        # Decide what to do with item value changed from user with old value
        pass

    @QtCore.pyqtSlot(list, object, str, str)
    def on_tree_item_edited(self, track, value, typestr, subtype):
        # Decide what to do with item value changed from user
        pass

    @QtCore.pyqtSlot(list, object, str, str)
    def on_struct_item_edited(self, track, value, typestr, subtype):
        # Decide what to do with item value changed from code
        if self._do_evaluation:
            self._evaluate_conditions()

    def _evaluate_conditions(self):
        """Evaluate conditions if changes were applied refresh treeview"""
        evaluated = self.phce.evaluate_conditions_in_a_node(self.phtv.tracker.get_root())
        if evaluated or self._do_evaluation:
            expanded = self.phtv.get_expanded_paths()
            selected = self.phtv.get_selected_paths()

            # Delay the refresh AND the restore
            def delayed_refresh():
                self.phtv.do_refresh()
                self.phtv.restore_expanded_paths(expanded)
                self.phtv.restore_selected_paths(selected)
                self.phtv.treeview_fit_to_contents(0)
                # Important Clear circular reference flag
                self.phtv.tracker.remove_property_from_all_nodes(self.phtv.tracker.get_root(),"__conditions__applied__")
            # Need to wait until all data changes are applied.
            QtCore.QTimer.singleShot(0, delayed_refresh)

    def _build_ui(self):
        # Main splitter
        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)
        # LEFT PANEL 
        left_panel = QtWidgets.QWidget() 
        left_layout = QtWidgets.QVBoxLayout(left_panel) 
        # RIGHT PANEL 
        right_panel = QtWidgets.QWidget() 
        right_layout = QtWidgets.QGridLayout(right_panel) 
        # Add panels to splitter
        splitter.addWidget(left_panel) 
        splitter.addWidget(right_panel)
        # -------------------------
        # TreeWidget
        # -------------------------
        self.positions_tree = QtWidgets.QTreeView(self) # QTreeWidget(self)
        left_layout.addWidget(self.positions_tree)
        # -------------------------
        # Views
        # -------------------------
        flip_v = QtGui.QTransform()
        flip_v.scale(1, -1)   # flip vertically
        flip_h = QtGui.QTransform() 
        flip_h.scale(-1, 1) # flip horizontally

        self.view_xy = OrthoView(self, self._wheel_zoom)
        self.view_xz = OrthoView(self, self._wheel_zoom)
        self.view_yz = OrthoView(self, self._wheel_zoom)

        # XY view 
        #self.view_xy = QtWidgets.QGraphicsView()
        self.scene_xy = QtWidgets.QGraphicsScene(self)
        self.view_xy.setScene(self.scene_xy)
        self.view_xy.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.view_xy.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
        self.view_xy.setTransform(flip_v)
        right_layout.addWidget(self._wrap_with_label(self.view_xy, "XY (Top View)"), 1, 0)

        # XZ view 
        #self.view_xz = QtWidgets.QGraphicsView()
        self.scene_xz = QtWidgets.QGraphicsScene(self)
        self.view_xz.setScene(self.scene_xz)
        self.view_xz.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.view_xz.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
        self.view_xz.setTransform(flip_v)
        right_layout.addWidget(self._wrap_with_label(self.view_xz, "XZ (Side View)"), 0, 0)

        # YZ view 
        #self.view_yz = QtWidgets.QGraphicsView()
        self.scene_yz = QtWidgets.QGraphicsScene(self)
        self.view_yz.setScene(self.scene_yz)
        self.view_yz.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.view_yz.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
        # self.view_yz.setTransform(flip_v)
        # self.view_yz.setTransform(flip_h)
        self.view_yz.rotate(270)
        right_layout.addWidget(self._wrap_with_label(self.view_yz, "YZ (Side View)"), 1, 1)

        #properties panel
        self.props = QtWidgets.QTextEdit()
        self.props.setReadOnly(True)
        self.props.setPlainText("Properties / debug output will go here.")
        right_layout.addWidget(self._wrap_with_label(self.props, "Properties"), 0, 1)

    def _wrap_with_label(self, widget, text):
        box = QtWidgets.QVBoxLayout()
        container = QtWidgets.QWidget()
        container.setLayout(box)
        label = QtWidgets.QLabel(text)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        box.addWidget(label)
        box.addWidget(widget)
        return container
    
    def _sync_view_sizes(self, world_x, world_y, world_z):
        self.scene_xy.setSceneRect(0, 0, world_x, world_y)
        self.scene_xz.setSceneRect(0, 0, world_x, world_z)
        self.scene_yz.setSceneRect(0, 0, world_y, world_z)


    #############
    # Zoom
    #############

    def _wheel_zoom(self, direction):
        if direction > 0:
            self.zoom *= 1.01
        else:
            self.zoom /= 1.01

        self._apply_zoom()

    def _apply_zoom(self):
        # XY
        t = QtGui.QTransform(self.trans_base_xy)
        t.scale(self.zoom, self.zoom)
        self.view_xy.setTransform(t)

        # XZ
        t = QtGui.QTransform(self.trans_base_xz)
        t.scale(self.zoom, self.zoom)
        self.view_xz.setTransform(t)

        # YZ (already rotated/flipped in base_yz)
        t = QtGui.QTransform(self.trans_base_yz)
        t.scale(self.zoom, self.zoom)
        self.view_yz.setTransform(t)
    
    def zoom_in(self):
        self.zoom *= 1.01
        self._apply_zoom()

    def zoom_out(self):
        self.zoom /= 1.01
        self._apply_zoom()
    
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

    def fit_xy_view(self):
        scene_rect = self.scene_xy.sceneRect()

        zoom_h = self.zoom_to_fit_height(self.view_xy, scene_rect)
        zoom_w = self.zoom_to_fit_width(self.view_xy, scene_rect)

        self.zoom = min(zoom_h, zoom_w)
        self._apply_zoom()


    #--------------------- Some shapes ----------------
    @staticmethod
    def make_hexagon():
        pts = []
        for i in range(6):
            a = 2 * math.pi * i / 6
            pts.append((0.5 + 0.5 * math.cos(a),
                        0.5 + 0.5 * math.sin(a)))
        return pts
    
    @staticmethod
    def make_square_with_point():
        return [
            (0.0, 0.0),   # top-left
            (1.0, 0.0),   # top-right
            (1.0, 0.8),   # bottom-right
            (0.5, 1.0),   # point
            (0.0, 0.8)    # bottom-left
        ]
    
    @staticmethod
    def make_triangle_polygon():
        return [
            (0.5, 0.0),   # top center
            (1.0, 1.0),   # bottom right
            (0.0, 1.0)    # bottom left
        ]
    
    @staticmethod
    def make_circle_polygon(segments=24):
        pts = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            pts.append((0.5 + 0.5*math.cos(a),
                        0.5 + 0.5*math.sin(a)))
        return pts


    def _build_model(self):
        # Simple demo model: machine, workspace, material, head, tool
        self.machine = CNCObject3D("Machine")
        m_size=self.phce.tracker.get_value(["Machine","Size","value"])
        m_pos=self.phce.tracker.get_value(["Machine","Position","value"])
        m_anchor=self.phce.tracker.get_value(["Machine","Anchor","value"])
        self.set_obj_size_position_anchor(self.machine,m_size,m_pos,m_anchor)
        # Set world sizes as 110% machine size
        self.world_sizes=[1.0*sss for sss in m_size]

        self.workspace = CNCObject3D("Workspace")
        w_size=self.phce.tracker.get_value(["Workspace","Size","value"])
        w_pos=self.phce.tracker.get_value(["Workspace","Position","value"])
        w_anchor=self.phce.tracker.get_value(["Workspace","Anchor","value"])
        self.set_obj_size_position_anchor(self.workspace,w_size,w_pos,w_anchor)
        # Attach to parent after having coordinates
        self.machine.attach_child(self.workspace)

        self.material = CNCObject3D("Material")
        ma_size=self.phce.tracker.get_value(["Material","Size","value"])
        ma_pos=self.phce.tracker.get_value(["Material","Position","value"])
        ma_anchor=self.phce.tracker.get_value(["Material","Anchor","value"])
        self.set_obj_size_position_anchor(self.material,ma_size,ma_pos,ma_anchor)
        self.workspace.attach_child(self.material)

        self.head = CNCObject3D("Head")
        h_size=self.phce.tracker.get_value(["Head","Size","value"])
        h_pos=self.phce.tracker.get_value(["Head","Position","value"])
        h_anchor=self.phce.tracker.get_value(["Head","Anchor","value"])
        self.set_obj_size_position_anchor(self.head,h_size,h_pos,h_anchor)
        self.machine.attach_child(self.head)

        self.tool = CNCObject3D("Tool")
        t_size=self.phce.tracker.get_value(["Tool","Size","value"])
        t_pos=self.phce.tracker.get_value(["Tool","Position","value"])
        t_anchor=self.phce.tracker.get_value(["Tool","Anchor","value"])
        self.set_obj_size_position_anchor(self.tool,t_size,t_pos,t_anchor)
        self.head.attach_child(self.tool)

        self.objects = [self.machine, self.workspace, self.material, self.head, self.tool]

        self._updating=False
    
    def set_obj_size_position_anchor(self,obj:CNCObject3D,size_list,pos_list,anchor_list):
        if isinstance(size_list,list) and len(size_list)==3:
            obj.w = size_list[0]
            obj.h = size_list[1]
            obj.d = size_list[2]
        if isinstance(pos_list,list) and len(pos_list)==3:
            obj.x = pos_list[0]
            obj.y = pos_list[1]
            obj.z = pos_list[2]
        if isinstance(anchor_list,list) and len(anchor_list)==3:
            obj.anchor_x = anchor_list[0]
            obj.anchor_y = anchor_list[1]
            obj.anchor_z = anchor_list[2]
    
    def _apply_shapes(self):
        # pencil shape
        circle = self.make_circle_polygon()
        triangle = self.make_square_with_point()
        triangle2 = self.make_square_with_point()

        self.tool.item_xy.set_shape(circle, anchor=(0.5, 0.5))
        self.tool.item_xz.set_shape(triangle, anchor=(0.5, 1.0))
        self.tool.item_yz.set_shape(triangle2, anchor=(0.5, 1.0))


    def _build_views(self):
        # colors = {
        #     "Machine": "lightGray",
        #     "Workspace": "lightGreen",
        #     "Material": "sandyBrown",
        #     "Head": "lightBlue",
        #     "Tool": "orange",
        # }
        colors = {
            "Machine": "#d0d0d0",
            "Workspace": "#a8e6a3",
            "Material": "#d2a679",
            "Head": "#8ec6ff",
            "Tool": "#ffb347",
        }


        for obj in self.objects:
            color = colors.get(obj.name, "white")

            obj.item_xy = ProjectedItem(
                obj, ProjectedItem.PlaneXY,
                on_model_changed=self.on_model_changed,
                color=color
            )
            self.scene_xy.addItem(obj.item_xy)
            #self.items_xy[obj] = obj.item_xy

            obj.item_xz = ProjectedItem(
                obj, ProjectedItem.PlaneXZ,
                on_model_changed=self.on_model_changed,
                color=color
            )
            self.scene_xz.addItem(obj.item_xz)
            #self.items_xz[obj] = obj.item_xz

            obj.item_yz = ProjectedItem(
                obj, ProjectedItem.PlaneYZ,
                on_model_changed=self.on_model_changed,
                color=color
            )
            self.scene_yz.addItem(obj.item_yz)
            #self.items_yz[obj] = obj.item_yz

        # --- Z reference lines (dashed) ---
        pen_z = QtGui.QPen(QtGui.QColor("darkGray"), 1, QtCore.Qt.PenStyle.DashLine)

        # XZ Z-axis reference
        self.zline_xz = QtWidgets.QGraphicsLineItem(0, 0, 400, 0)
        self.zline_xz.setPen(pen_z)
        self.scene_xz.addItem(self.zline_xz)

        # YZ Z-axis reference
        self.zline_yz = QtWidgets.QGraphicsLineItem(0, 0, 400, 0)
        self.zline_yz.setPen(pen_z)
        self.scene_yz.addItem(self.zline_yz)

        self.trans_base_xy = self.view_xy.transform()   # after flip
        self.trans_base_xz = self.view_xz.transform()   # after flip
        self.trans_base_yz = self.view_yz.transform()   # after rotate/flip


    def move_obj_to(self, obj, x, y, z):
        self._changing_from_code=True
        obj.move_to(x, y, z)

        if obj.parent:
            obj.local_dx = obj.x - obj.parent.x
            obj.local_dy = obj.y - obj.parent.y
            obj.local_dz = obj.z - obj.parent.z

        self.on_model_changed(obj)
        self._changing_from_code=False


    def resize_obj_to(self,obj: CNCObject3D, w, h, d):
        self._changing_from_code=True
        obj.resize_to(w, h, d)
        self.on_model_changed(obj)
        self._changing_from_code=False

    def on_model_changed(self, obj: CNCObject3D):
        # Update all projections of this object
        if self._updating:
            return
        if None in [obj.item_xy,obj.item_xz,obj.item_yz]:
            return
        self._updating=True
        obj.item_xy.update_from_model()
        obj.item_xz.update_from_model()
        obj.item_yz.update_from_model()

        # updates local_XY coords
        obj.update_children_recursive(obj)

        # Debug info
        msg=self._get_obj_children_message(obj)
        self.props.setPlainText(msg)
        if not self._changing_from_code:
            self.update_tree(obj)
        self._updating=False
    
    def update_tree(self,obj: CNCObject3D):
        name=obj.name
        self._do_evaluation=True
        self.phce.tracker.set_value([name,"Size","value"],[obj.w,obj.h,obj.d],"float")
        self.phce.tracker.set_value([name,"Position","value"],[obj.x,obj.y,obj.z],"float")
        self.phce.tracker.set_value([name,"Anchor","value"],[obj.anchor_x,obj.anchor_y,obj.anchor_z],"float")
        self._do_evaluation=False


    def _get_obj_children_message(self,obj: CNCObject3D):
        msg=""
        msg += self._get_obj_message(obj)    
        for child in obj.children:
            msg += self._get_obj_message(child)    
        return msg

    def _get_obj_message(self,obj: CNCObject3D):
        msg=""
        try:
            msg += f"Updated: {obj.name}: Size: W: {obj.w:.2f}, H: {obj.h:.2f}, D: {obj.d:.2f}\n" 
            msg += f"\t+ World X: {obj.x:.2f}, Y: {obj.y:.2f}, Z: {obj.z:.2f}\n"
            msg += f"\tLocal dX: {obj.local_dx:.2f}, dY: {obj.local_dy:.2f}, dZ: {obj.local_dz:.2f}\n"
            msg += f"\tAnchor X: {obj.anchor_x:.2f}, Y: {obj.anchor_y:.2f}, Z: {obj.anchor_z:.2f}\n"
        except:
            pass
        return msg 
    
    def _fit_all(self):
        for view, scene in [
            (self.view_xy, self.scene_xy),
            (self.view_xz, self.scene_xz),
            (self.view_yz, self.scene_yz),
        ]:
            # scene.setSceneRect(scene.itemsBoundingRect())
            view.fitInView(scene.sceneRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)

        # Position Z reference lines at Z=0
        self.zline_xz.setPos(0, 0)
        self.zline_yz.setPos(0, 0)
        # self.fit_xy_view()
        self.zoom=1
        self._apply_zoom()

class OrthoView(QtWidgets.QGraphicsView):
    def __init__(self, parent, zoom_callback):
        super().__init__(parent)
        self.zoom_callback = zoom_callback

    def wheelEvent(self, event):
        delta = event.angleDelta().y()

        if delta > 0:
            self.zoom_callback(+1)
        else:
            self.zoom_callback(-1)


class ResizeHandle(QtWidgets.QGraphicsRectItem):
    def __init__(self, parent_item, axis, on_resize):
        super().__init__(-4, -4, 8, 8, parent_item)
        self.axis = axis
        self.on_resize = on_resize
        self.parent_item = parent_item

        self.setBrush(QtGui.QColor("yellow"))
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setZValue(10)

        self._dragging = False
        self._last_scene_pos = None

    def mousePressEvent(self, event):
        self._dragging = True
        self._last_scene_pos = self.mapToScene(event.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._dragging:
            return super().mouseMoveEvent(event)

        new_scene_pos = self.mapToScene(event.pos())
        delta_scene = new_scene_pos - self._last_scene_pos

        # convert delta to parent local coordinates
        p0 = self.parent_item.mapFromScene(self._last_scene_pos)
        p1 = self.parent_item.mapFromScene(new_scene_pos)
        delta_local = p1 - p0

        dx = delta_local.x()
        dy = delta_local.y()

        # apply resize
        self.on_resize(self.axis, dx, dy)

        # update last position
        self._last_scene_pos = new_scene_pos

        # snap handle back to its corner
        self.setPos(self.pos())

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._last_scene_pos = None
        super().mouseReleaseEvent(event)




def main():
    app = QtWidgets.QApplication(sys.argv)
    dlg = PositionHelper()
    dlg.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
