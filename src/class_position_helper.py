import sys
from PyQt6 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg

import math
import logging
from class_shape_factory import ShapeFactory
SF=ShapeFactory()
pencil=SF.make("pencil","down")

style_dict = {            
            "Machine": {
                "bg":"#d0d0d0",
                "fg": "#ff0000"       # red text
            },
            "Workspace": {
                "bg":"#a8e6a3",
                "fg": "#ff0000"       # red text
            },
            "Material": {
                "bg":"#d2a679",
                "fg": "#ff0000"       # red text
            },
            "Head": {
                "bg":"#8ec6ff",
                "fg": "#ff0000"       # red text
            },
            "Tool":{
                "bg": "#ffb347",
                "fg": "#ff0000"       # red text
            },
        }

MAIN_STRUCT_EXAMPLE={
        "Machine": {"children":[  
                {"Axes": {"value": ['X','Y','Z'], "type": "list", "subtype": "str", "meta": {"editable": False }}},
                {"Mapping": [
                    {"X": {"value": "X", "type": "str", "meta": {"options": ["X", "Y", "Z", "A", "B", "C","E","F","S"]}}},
                    {"Y": {"value": "Y", "type": "str", "meta": {"options": ["X", "Y", "Z", "A", "B", "C","E","F","S"]}}},
                    {"Z": {"value": "Z", "type": "str", "meta": {"options": ["X", "Y", "Z", "A", "B", "C","E","F","S"]}}},
                ]},
                {"Size": {"value": [700, 800, 200], "type": "list", "subtype": "float", "unit":"mm", "meta": { "constraints": {"arity": 3, "min": [0.01,0.01,0.01], "max": [10**6,10**6,10**6]}, "decimals": 2}}},
                {"Anchor": {"value": [0.5, 0.5, 0.5], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": { "arity": 3, "min": [0.0,0.0,0.0], "max": [1,1,1]}, "decimals": 2}}},
                {"Position": {"value": [0.0, 0.0, 0.0], "type": "list", "subtype": "float", "unit":"mm", "meta": {"editable":False,"constraints": { "arity": 3, "min": [-10**6,-10**6,-10**6], "max": [10**6,10**6,10**6]}, "decimals": 3}}},
                {"Parent": {"value": '', "type": "str",  "meta": {"hidden":False, "editable":False}}},
                {"Style": [                        
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"]}}},
                        {"Pen": {"value": "#d0d0d0", "type": "color", "meta": {"hidden":False, "editable":True}}},
                        {"Pen Width": {"value": 2, "type": "int",  "unit":"[1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 1, "max": 5}}}},
                        {"Fill": {"value": "#d0d0d0", "type": "color", "meta": {"hidden":False, "editable":True}}},
                        {"Fill Transparency": {"value": 60, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}}}}
                        ]},
                ]},
        "TestLine": {"Color":"#a8e6a3","children":[                  
                {"Size": {"value": [0, 400, 0], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [0.01,0.01,0.01], "max": [10**6,10**6,10**6]}, "decimals": 2}}},
                #{"Anchor": {"value": [0.5, 0.5, 0.5], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": {"arity": 3, "min": [0.0,0.0,0.0], "max": [1,1,1]}, "decimals": 2}}},
                {"Position": {"value": [350.0, 400.0, 100.0], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [-10**6,-10**6,-10**6], "max": [10**6,10**6,10**6]}, "decimals": 3}}},
                {"Parent": {"value": 'Machine', "type": "str",  "meta": {"hidden":False, "editable":False}}},
                {"Lock Size": {"value": [True, False, True], "type": "list", "subtype": "bool", "meta": {"subtype": "bool","constraints": {"arity": 3}, "hidden":False, "editable":False}}},                
                {"Lock Position": {"value": [False, False, False], "type": "list", "subtype": "bool", "meta": {"subtype": "bool","constraints": {"arity": 3}, "hidden":False, "editable":False}}},                
            ]},
        "Workspace": {"children":[                  
                {"Size": {"value": [650, 700, 100], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [0.01,0.01,0.01], "max": [10**6,10**6,10**6]}, "decimals": 2}}},
                {"Anchor": {"value": [0.5, 0.5, 0.5], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": {"arity": 3, "min": [0.0,0.0,0.0], "max": [1,1,1]}, "decimals": 2}}},
                {"Position": {"value": [10.0, 10.0, 10.0], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [-10**6,-10**6,-10**6], "max": [10**6,10**6,10**6]}, "decimals": 3}}},
                {"Parent": {"value": 'Machine', "type": "str",  "meta": {"hidden":False, "editable":False}}},
                {"Style": [                        
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"]}}},
                        {"Pen": {"value": "#a8e6a3", "type": "color", "meta": {"hidden":False, "editable":True}}},
                        {"Pen Width": {"value": 2, "type": "int",  "unit":"[1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 1, "max": 5}}}},
                        {"Fill": {"value": "#a8e6a3", "type": "color", "meta": {"hidden":False, "editable":True}}},
                        {"Fill Transparency": {"value": 60, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}}}}
                        ]},
            ]},
        "Home": {"children":[                  
                {"Size": {"value": [5, 5, 5], "type": "list", "subtype": "float", "unit":"mm", "meta": {"editable":False,"constraints": {"arity": 3, "min": [0.01,0.01,0.01], "max": [10**6,10**6,10**6]}, "decimals": 2}}},
                {"Anchor": {"value": [0.5, 0.5, 0.5], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": {"arity": 3, "min": [0.0,0.0,0.0], "max": [1,1,1]}, "decimals": 2}}},
                {"Position": {"value": [10.0, 10.0, 10.0], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [-10**6,-10**6,-10**6], "max": [10**6,10**6,10**6]}, "decimals": 3}}},
                {"Parent": {"value": 'Workspace', "type": "str",  "meta": {"hidden":False, "editable":False}}},
                {"Lock Size": {"value": [True, True, True], "type": "list", "subtype": "bool", "meta": {"subtype": "bool","constraints": {"arity": 3}, "hidden":False, "editable":False}}},                
                {"Lock Position": {"value": [False, False, False], "type": "list", "subtype": "bool", "meta": {"subtype": "bool","constraints": {"arity": 3}, "hidden":False, "editable":False}}},                
                {"View Z": {"value":[80, 80, 80], "type": "list", "subtype": "int", "info":"Height in view, order of objects in view","meta": {"constraints": {"arity": 3}, "hidden":True, "editable":False}}},                
                {"Style": [                        
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"]}}},
                        {"Pen": {"value": "#000000", "type": "color", "meta": {"hidden":False, "editable":True}}},
                        {"Pen Width": {"value": 2, "type": "int",  "unit":"[1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 1, "max": 5}}}},
                        {"Fill": {"value": "#043ba1", "type": "color", "meta": {"hidden":False, "editable":True}}},
                        {"Fill Transparency": {"value": 0, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}}}}
                        ]},
            ]},
        "Material": {"Color":"#d2a679","children":[                  
                {"Size": {"value": [270, 210, 3], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [0.01,0.01,0.01], "max": [10**6,10**6,10**6]}, "decimals": 2}}},
                {"Anchor": {"value": [0.5, 0.5, 0.5], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": {"arity": 3, "min": [0.0,0.0,0.0], "max": [1,1,1]}, "decimals": 2}}},
                {"Position": {"value": [10.0, 10.0, 10.0], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [-10**6,-10**6,-10**6], "max": [10**6,10**6,10**6]}, "decimals": 3}}},
                {"Parent": {"value": 'Workspace', "type": "str",  "meta": {"hidden":False, "editable":False}}},
                {"Style": [                        
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"]}}},
                        {"Pen": {"value": "#d2a679", "type": "color", "meta": {"hidden":False, "editable":True}}},
                        {"Pen Width": {"value": 2, "type": "int",  "unit":"[1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 1, "max": 5}}}},
                        {"Fill": {"value": "#f3f3f3", "type": "color", "meta": {"hidden":False, "editable":True}}},
                        {"Fill Transparency": {"value": 0, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}}}}
                        ]},
            ]},
        "Head": {"children":[                  
                {"Size": {"value": [40, 40, 30], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [0.01,0.01,0.01], "max": [10**6,10**6,10**6]}, "decimals": 2}}},
                {"Anchor": {"value": [0.5, 0.5, 1], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": {"arity": 3, "min": [0.0,0.0,0.0], "max": [1,1,1]}, "decimals": 2}}},
                {"Position": {"value": [10.0, 10.0, 80.0], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [-10**6,-10**6,-10**6], "max": [10**6,10**6,10**6]}, "decimals": 3}}},
                {"Parent": {"value": 'Machine', "type": "str",  "meta": {"hidden":False, "editable":False}}},
                {"Style": [                        
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"]}}},
                        {"Pen": {"value": "#8ec6ff", "type": "color", "meta": {"hidden":False, "editable":True}}},
                        {"Pen Width": {"value": 2, "type": "int",  "unit":"[1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 1, "max": 5}}}},
                        {"Fill": {"value": "#8ec6ff", "type": "color", "meta": {"hidden":False, "editable":True}}},
                        {"Fill Transparency": {"value": 60, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}}}}
                        ]},
            ]},
        "Tool": {"Color":"#ffb347","children":[                  
                {"Tool Type": {"value": "pencil", "type": "str", "meta": {"options": ["pen","pencil","laser"]}}},
                {"Size": {"value": [5, 5, 100], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [0.01,0.01,0.01], "max": [10**6,10**6,10**6]}, "decimals": 2}}},
                {"Anchor": {"value": [0.5, 0.5, 1], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": {"arity": 3, "min": [0.0,0.0,0.0], "max": [1,1,1]}, "decimals": 2}}},
                {"Position": {"value": [10.0, 10.0, 40.0], "type": "list", "subtype": "float", "unit":"mm", "meta": {"constraints": {"arity": 3, "min": [-10**6,-10**6,-10**6], "max": [10**6,10**6,10**6]}, "decimals": 3}}},
                {"Parent": {"value": 'Head', "type": "str",  "meta": {"hidden":False, "editable":False}}},
                {"Style": [                        
                        {"Line Type": {"value": "solid", "type": "str", "meta": {"hidden":False, "editable":True, "options":["solid","dash","dot","dashdot","dashdotdot"]}}},
                        {"Pen": {"value": "#4508ee", "type": "color", "meta": {"hidden":False, "editable":True}}},
                        {"Pen Width": {"value": 1, "type": "int",  "unit":"[1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 1, "max": 5}}}},
                        {"Fill": {"value": "#4508ee", "type": "color", "meta": {"hidden":False, "editable":True}}},
                        {"Fill Transparency": {"value": 128, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}}}}
                        ]},
                {"Shape":   [{"XY":[
                           {"Shape Points": {"value": [((0.5 + 0.5 * math.cos(2 * math.pi * i / 6), 0.5 + 0.5 * math.sin(2 * math.pi * i / 6))) for i in range(6)],"type": "list","subtype": "tuple","meta": {"hidden":False, "editable":False}}},
                            {"Anchor": {"value": [0.5, 0.5], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": {"arity": 2, "min": [0.0,0.0], "max": [1,1]}, "decimals": 2}}},
                            {"Style": [
                                {"Pen": {"value": "brown", "type": "color", "meta": {"hidden":False, "editable":True}}},
                                {"Pen Width": {"value": 1, "type": "int",  "unit":"[1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 1, "max": 5}}}},
                                {"Fill": {"value": "#ee8e08", "type": "color", "meta": {"hidden":False, "editable":True}}},
                                {"Fill Transparency": {"value": 128, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}}}}
                                ]},
                            ]},
                            {"XZ":[
                           {"Shape Points": {"value": pencil,"type": "list","subtype": "tuple","meta": {"hidden":False, "editable":False}}},
                            {"Anchor": {"value": [0, 0], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": {"arity": 2, "min": [0.0,0.0], "max": [1,1]}, "decimals": 2}}},
                            {"Style": [
                                {"Pen": {"value": "brown", "type": "color", "meta": {"hidden":False, "editable":True}}},
                                {"Pen Width": {"value": 1, "type": "int",  "unit":"[1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 1, "max": 5}}}},
                                {"Fill": {"value": "#ee8e08", "type": "color", "meta": {"hidden":False, "editable":True}}},
                                {"Fill Transparency": {"value": 128, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}}}}
                                ]},
                           ]},
                            {"YZ":[
                           {"Shape Points": {"value": pencil,"type": "list","subtype": "tuple","meta": {"hidden":False, "editable":False}}},
                            {"Anchor": {"value": [0.5, 0.5], "type": "list", "subtype": "float", "unit":"[0-1]", "meta": {"constraints": {"arity": 2, "min": [0.0,0.0], "max": [1,1]}, "decimals": 2}}},
                             {"Style": [
                                {"Pen": {"value": "brown", "type": "color", "meta": {"hidden":False, "editable":True}}},
                                {"Pen Width": {"value": 1, "type": "int",  "unit":"[1-5]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 1, "max": 5}}}},
                                {"Fill": {"value": "#ee8e08", "type": "color", "meta": {"hidden":False, "editable":True}}},
                                {"Fill Transparency": {"value": 128, "type": "int",  "unit":"[1-255]", "meta": {"hidden":False, "editable":True,"constraints": { "min": 0, "max": 255}}}}
                                ]},
                           ]},
                            ]            
                },
                {"Tracker": [
                    {"Speed": {"value": 333, "unit":"mm/s" ,"type": "int", "meta": {"hidden":False, "editable":True}}},
                    {"Extruder": {"value": 333,"step":0, "type": "float", "meta": {"hidden":False, "editable":False}}},
                    {"Power": {"value": 333,"step":0, "type": "int", "meta": {"hidden":False, "editable":False}}},
                    ]},
            ]}
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

import resources_rc
import class_treeview_functions
import class_struct_tracker
import class_struct_conditioner
from class_sync_zoom_scroll import SyncedScrollZoomController
from class_tracker_plot import TrackerPlot, TrackerPlotsContainer, TrackerPlotsContainerControls, TrackerWindow

#######################################################
# ----------------- 3D model -----------------
#######################################################
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

        # 3D position locks
        self.lock_x = False
        self.lock_y = False
        self.lock_z = False

        # Size locks
        self.lock_w = False
        self.lock_h = False
        self.lock_d = False

        self.allow_user_resize = True
        self.allow_user_repos = True

        # View self position        
        self.view_z_pos = {"xy":0,"xz":0,"yz":0}
        
        # Style
        self.style_dict={"Line Type":"solid","Fill":"#FFFFFF","Fill Transparency":77,"Pen":"#000000","Pen Width":2}
        # Shapes
        self._has_shape=False

    def move_to(self, x, y, z):
        if not self.lock_x:
            self.x = x
        if not self.lock_y:
            self.y = y
        if not self.lock_z:
            self.z = z

    def resize_to(self, w, h, d):
        if not self.lock_w:
            self.w = w
        if not self.lock_h:
            self.h = h
        if not self.lock_d:
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

#########################################################
# ----------------- Base projected item -----------------
#########################################################
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

    PLANE_MAP = {
    PlaneXY: {
        "move_axes": ("x", "y"),
        "size_axes": ("w", "h"),
    },
    PlaneXZ: {
        "move_axes": ("x", "z"),
        "size_axes": ("w", "d"),
    },
    PlaneYZ: {
        "move_axes": ("y", "z"),
        "size_axes": ("h", "d"),
    },
    }


    def __init__(self, obj: CNCObject3D, plane, on_model_changed, color, parent=None):
        super().__init__(parent)
        self.obj = obj
        self.plane = plane
        self.on_model_changed = on_model_changed  # callback to notify dialog        
        self.allow_user_resize=(True,True)
        self.allow_axis_movement=(True,True)
        self.shape_style=None
        self._last_resize_permissions = None
        self._is_new_style=True
        if isinstance(color,dict):
            self.general_style=color
        else:
            self.general_style=None
            self.color=color
        # default rectangle 
        self.base_polygon = None # normalized polygon (0..1) 
        self.anchor = (0.5, 0.5) # normalized anchor 
        self.shape_item = QtWidgets.QGraphicsPolygonItem(self)
        if not self.general_style:
            self.setBrush(QtGui.QColor(color).lighter(160))
            self.setPen(QtGui.QPen(QtGui.QColor(color), 2))
        else:
            self.apply_style_dict(self.general_style)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

        self.anchor_item = None
        self._build_geometry()
        self._create_anchor_item()
        # self.update_from_model()
        self.handles = []
        self._create_resize_handles()
        self._update_shape()
        self.shape_item.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton)        
        if hasattr(self, "_anchor_v"):
            self._anchor_v.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton)
        self.update_from_model()


    def set_shape(self, polygon_points, anchor=(0.5, 0.5), style=None):
        """
        polygon_points: list of (x,y) in normalized 0..1 space
        anchor: (ax, ay) also in 0..1 space
        """
        self.base_polygon = polygon_points
        self.anchor = anchor
        if style:
            self.shape_style=style
        self._update_shape()
    
    def update_movement_permissions(self):
        axes = self.PLANE_MAP[self.plane]["move_axes"]
        allowed = []

        for axis in axes:
            lock_flag = getattr(self.obj, f"lock_{axis}")
            allowed.append(not lock_flag)

        self.allow_axis_movement = tuple(allowed)

    def _update_resize_permissions(self):
        axes = self.PLANE_MAP[self.plane]["size_axes"]
        allowed = []

        for axis in axes:
            lock_flag = getattr(self.obj, f"lock_{axis}")
            allowed.append(not lock_flag)

        self.allow_user_resize = tuple(allowed)

    def _update_shape(self):
        if self.base_polygon is None:
            return

        w = getattr(self, "_plane_w", self.obj.w)
        h = getattr(self, "_plane_h", self.obj.h)

        poly = QtGui.QPolygonF()
        for x, y in self.base_polygon:
            poly.append(QtCore.QPointF(x * w, y * h))

        # Tell Qt the geometry is about to change
        self.shape_item.prepareGeometryChange()

        self.shape_item.setPolygon(poly)
        if not self.shape_style:
            self.shape_style=self.obj.style_dict
        self.set_style(self.shape_item, self.shape_style)
        # Hide parent pen/brush 
        try:
            self.setPen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen))
            self.setBrush(QtGui.QBrush(QtCore.Qt.BrushStyle.NoBrush))
        except Exception as eee:
            pass
        # Force repaint
        self.shape_item.update()
        self.update()  # force parent to repaint
        if self.scene():
            self.scene().update()  # force scene to repaint
    
    def _update_style(self):
        if not self._is_new_style:
            return
        self.apply_style_dict(self.obj.style_dict)
        self._is_new_style=False
    
    def set_style(self,shape_item,shape_style):
        if shape_style:
            pen=shape_style.get("Pen","black")
            width=min(max(int(shape_style.get("Pen Width",1)),1),5)
            fill=shape_style.get("Fill","white")
            lighter=shape_style.get("Fill Transparency",100)
            if fill:
                color = QtGui.QColor(fill) 
                if lighter: 
                    color.setAlpha(lighter) # modifies the color object 
                shape_item.setBrush(color)
            if pen and width:
                shape_item.setPen(QtGui.QPen(QtGui.QColor(pen), width))
        return shape_item
    
    def apply_style_dict(self,ostyle_dict:dict):        
        pen=ostyle_dict.get("Pen","black")
        width=min(max(int(ostyle_dict.get("Pen Width",1)),1),5)
        fill=ostyle_dict.get("Fill","white")
        trans=ostyle_dict.get("Fill Transparency",100)
        if fill:
            color = QtGui.QColor(fill) 
            if trans: 
                color.setAlpha(trans) # modifies the color object 
            self.setBrush(color)
        if pen and width:
            self.setPen(QtGui.QPen(QtGui.QColor(pen), width))
        
    def _delete_resize_handles(self):
        """Deletes the resize handles"""
        for h in self.handles:
            if h.scene():
                h.scene().removeItem(h)
            h.setParentItem(None)

        self.handles.clear()

    def _create_resize_handles(self):
        """Creates resizing handles"""
        if not self.obj.allow_user_resize:
            return
        
        size_axes = self.PLANE_MAP[self.plane]["size_axes"]
        r = self.rect()

        for axis_name, allowed in zip(size_axes, self.allow_user_resize):
            if not allowed:
                continue

            # Convert size axis to logical axis for handle
            # w → x, h → y, d → z
            logical_axis = {
                "w": "x",
                "h": "y",
                "d": "z",
            }[axis_name]

            h = ResizeHandle(self, logical_axis, self._on_resize)
            if logical_axis == "x":
                h.setPos(r.width(), r.height() / 2)
            else:
                h.setPos(r.width() / 2, r.height())
            self.handles.append(h)


    def _on_resize(self, axis, dx, dy):
        if axis == "x" and not self.obj.lock_w:
            self.obj.w = max(3, self.obj.w + dx)
        elif axis == "y" and not self.obj.lock_h:
            self.obj.h = max(3, self.obj.h + dy)
        elif axis == "z" and not self.obj.lock_d:
            self.obj.d = max(3, self.obj.d + dy)

        # Notify controller
        if self.on_model_changed:
            self.on_model_changed(self.obj)

    def _build_geometry(self):
        if self.plane == self.PlaneXY:
            self.setRect(0, 0, self.obj.w, self.obj.h)
            self.setZValue(self.obj.view_z_pos.get("xy",0))
        elif self.plane == self.PlaneXZ:
            self.setRect(0, 0, self.obj.w, self.obj.d)
            self.setZValue(self.obj.view_z_pos.get("xz",0))
        elif self.plane == self.PlaneYZ:
            self.setRect(0, 0, self.obj.h, self.obj.d)
            self.setZValue(self.obj.view_z_pos.get("yz",0))

    def update_view_z_pos(self):        
        if self.plane == self.PlaneXY:
            self.setZValue(self.obj.view_z_pos.get("xy",0))
        elif self.plane == self.PlaneXZ:
            self.setZValue(self.obj.view_z_pos.get("xz",0))
        elif self.plane == self.PlaneYZ:
            self.setZValue(self.obj.view_z_pos.get("yz",0))

    def _create_anchor_item(self):
        # small crosshair
        self.anchor_item = QtWidgets.QGraphicsLineItem(self)
        pen = QtGui.QPen(QtGui.QColor("red"), 1)
        self.anchor_item.setPen(pen)
        self.anchor_item.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton)

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
        self._update_resize_permissions()
        if self.allow_user_resize != self._last_resize_permissions:
            self._delete_resize_handles()
            self._create_resize_handles()
            self._last_resize_permissions = self.allow_user_resize
        else:
            self._update_handle_positions()

        # store for shape update 
        self._plane_w = w 
        self._plane_h = h
        # Update shape
        self._update_style()
        self._update_shape()
        self.update_view_z_pos()

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

    def contextMenuEvent(self, event):
        # Sizes
        if not self.obj.allow_user_repos and not self.obj.allow_user_resize:
            return
        menu = QtWidgets.QMenu()
        lock_icon = QtGui.QIcon(":/img/Action-lock-silver-icon.png")
        unlock_icon = QtGui.QIcon(":/img/Action-lock-pink-icon.png")
        if self.obj.allow_user_resize:
            if any(self.allow_user_resize):
                menu.addAction(lock_icon, "Lock Size", self.lock_size)
            else:                
                menu.addAction(unlock_icon,"Unlock Size", self.lock_size)
        # Positions
        if self.obj.allow_user_repos:
            if any(self.allow_axis_movement):
                menu.addAction(lock_icon,"Lock Position", self.lock_position)
                if self.obj.parent is not None:
                    menu.addSeparator()
                    menu.addAction("Center in Parent", self.align_center)
                    menu.addSeparator()
                    menu.addAction("Align Left", self.align_left)
                    menu.addAction("Align Right", self.align_right)
                    menu.addAction("Align Top", self.align_top)
                    menu.addAction("Align Bottom", self.align_bottom)
            else:
                menu.addAction(unlock_icon,"Unlock Position", self.lock_position)            
        menu.exec(event.screenPos())

    def lock_position(self):
        lock=any(self.allow_axis_movement)
        self.allow_axis_movement=(not lock, not lock)
        if self.plane == self.PlaneXY:
            self.obj.lock_x=lock
            self.obj.lock_y=lock
        elif self.plane == self.PlaneXZ:
            self.obj.lock_x=lock
            self.obj.lock_z=lock
        elif self.plane == self.PlaneYZ: 
            self.obj.lock_y=lock
            self.obj.lock_z=lock
        # Update to apply locks in all views
        self.obj.item_xy.update_movement_permissions()
        self.obj.item_xz.update_movement_permissions()
        self.obj.item_yz.update_movement_permissions()

    def lock_size(self):
        lock=any(self.allow_user_resize)
        self.allow_user_resize=(not lock, not lock)
        if self.plane == self.PlaneXY:
            self.obj.lock_w=lock
            self.obj.lock_h=lock
        elif self.plane == self.PlaneXZ:
            self.obj.lock_w=lock
            self.obj.lock_d=lock
        elif self.plane == self.PlaneYZ: 
            self.obj.lock_h=lock
            self.obj.lock_d=lock
        # Update to apply locks in all views and show/hide handles
        self.obj.item_xy.update_from_model()
        self.obj.item_xz.update_from_model()
        self.obj.item_yz.update_from_model()

    def align_center(self):
        p = self.obj.parent
        value=None
        if self.plane == self.PlaneXY:
            x = p.x + (p.w - self.obj.w) / 2
            y = p.y + (p.h - self.obj.h) / 2
            value=QtCore.QPointF(x, y)
        elif self.plane == self.PlaneXZ:
            x = p.x + (p.w - self.obj.w) / 2
            z = p.z + (p.d - self.obj.d) / 2
            value=QtCore.QPointF(x, z)
        elif self.plane == self.PlaneYZ:  # YZ
            y = p.y + (p.h - self.obj.h) / 2
            z = p.z + (p.d - self.obj.d) / 2
            value=QtCore.QPointF(y, z)
        if value:
            self.itemChange(QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange,value)

    def align_left(self):
        p = self.obj.parent
        value=None
        if self.plane == self.PlaneXY:
            x = p.x
            y = self.obj.y
            value=QtCore.QPointF(x, y)
        elif self.plane == self.PlaneXZ:
            x = p.x
            z = self.obj.z
            value=QtCore.QPointF(x, z)
        elif self.plane == self.PlaneYZ:  # YZ
            y = p.y 
            z = self.obj.z
            value=QtCore.QPointF(y, z)
        if value:
            self.itemChange(QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange,value)

    def align_right(self):
        p = self.obj.parent
        value=None
        if self.plane == self.PlaneXY:
            x = p.x + p.w - self.obj.w
            y = self.obj.y
            value = QtCore.QPointF(x, y)
        elif self.plane == self.PlaneXZ:
            x = p.x + p.w - self.obj.w
            z = self.obj.z
            value = QtCore.QPointF(x, z)
        elif self.plane == self.PlaneYZ:  # YZ
            y = p.y + p.h - self.obj.h
            z = self.obj.z
            value = QtCore.QPointF(y, z)
        if value:
            self.itemChange(QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange, value)

    def align_top(self):
        p = self.obj.parent
        value=None
        if self.plane == self.PlaneXY:
            x = self.obj.x
            y = p.y + p.h - self.obj.h
            value = QtCore.QPointF(x, y)
        elif self.plane == self.PlaneXZ:
            x = self.obj.x
            z = p.z + p.d - self.obj.d
            value = QtCore.QPointF(x, z)
        elif self.plane == self.PlaneYZ:  # YZ
            y = p.y + p.h - self.obj.h
            z = self.obj.z
            value = QtCore.QPointF(y, z)
        if value:
            self.itemChange(QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange, value)

    def align_bottom(self):
        p = self.obj.parent
        value=None
        if self.plane == self.PlaneXY:
            x = self.obj.x
            y = p.y
            value = QtCore.QPointF(x, y)
        elif self.plane == self.PlaneXZ:
            x = self.obj.x
            z = p.z
            value = QtCore.QPointF(x, z)
        elif self.plane == self.PlaneYZ:  # YZ
            y = p.y
            z = self.obj.z
            value = QtCore.QPointF(y, z)
        if value:
            self.itemChange(QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange, value)


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
            allow_x=False
            allow_y=False
            allow_z=False
            if not self.obj.allow_user_repos:
                return
            # Update model based on plane
            if self.plane == self.PlaneXY:
                # XY view controls X and Y
                if self.allow_axis_movement[0]:
                    self.obj.x = new_pos.x()
                    allow_x=True
                if self.allow_axis_movement[1]:
                    self.obj.y = new_pos.y()
                    allow_y=True
                nx,ny=self.obj.x,self.obj.y
            elif self.plane == self.PlaneXZ:
                # XZ view controls X and Z
                if self.allow_axis_movement[0]:
                    self.obj.x = new_pos.x()
                    allow_x=True
                if self.allow_axis_movement[1]:                    
                    self.obj.z = new_pos.y()
                    allow_z=True
                nx,ny=self.obj.x,self.obj.z
            elif self.plane == self.PlaneYZ:
                # YZ view controls Y and Z
                if self.allow_axis_movement[0]:
                    self.obj.y = new_pos.x()
                    allow_y=True
                if self.allow_axis_movement[1]:    
                    self.obj.z = new_pos.y()
                    allow_z=True
                nx,ny=self.obj.y,self.obj.z

            # Update local offsets 
            parent = self.obj.parent 
            if parent is not None:
                if allow_x:
                    self.obj.local_dx = self.obj.x - parent.x 
                if allow_y:
                    self.obj.local_dy = self.obj.y - parent.y 
                if allow_z:
                    self.obj.local_dz = self.obj.z - parent.z

            # Notify controller so other views can update
            if self.on_model_changed:
                self.on_model_changed(self.obj)

            return QtCore.QPointF(nx,ny)

        return super().itemChange(change, value)

class TexturedMaterialItem(CNCObject3D):
    def __init__(self, model: CNCObject3D, texture_path: str, parent_item=None):
        super().__init__(model, color="brown", parent_item=parent_item)
        self.texture = QtGui.QPixmap(texture_path)

    def paint(self, painter: QtGui.QPainter, option, widget=None):
        r = self.rect()
        if not self.texture.isNull():
            # Stretch texture to fill material
            painter.drawPixmap(r, self.texture, self.texture.rect())
        # Draw border on top
        painter.setPen(self.pen())
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawRect(r)

###############################################################
# ----------------------- Main dialog -------------------------
###############################################################

class PositionHelper(QtWidgets.QMainWindow): #QtWidgets.QDialog):
    def __init__(self,positions_struct=None,mode=None):
        super().__init__()
        self.setWindowTitle("Positioning Helper: Size & Coordinate Editor (XY, XZ, YZ) ")
        self.resize(1200, 800)
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
                            }
        # Define main structure or use example
        if isinstance(positions_struct,dict):
            self.positions_struct=positions_struct
        else:
            self.positions_struct=MAIN_STRUCT_EXAMPLE
        if mode and mode=="Tracker":
            self.tracking_mode=True
            self.positioning_mode=False
        elif mode and mode=="Position":
            self.tracking_mode=False
            self.positioning_mode=True
        else:
            self.tracking_mode=True
            self.positioning_mode=True
            
        self.objects = []
        self.items_xy = {}
        self.items_xz = {}
        self.items_yz = {}
        self.world_sizes=[1,1,1]
        self.zoom = 1.0
        self._changing_from_code=False

        self._build_ui()
        self._build_configuration()
        self._build_model()
        self._build_views()
        self._apply_shapes()
        self._build_plot_trackers()
        self._sync_view_sizes(self.world_sizes[0],self.world_sizes[1],self.world_sizes[2])
        self._fit_all()

    def _build_configuration(self):
        self._do_evaluation=False
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
        self.phtv.set_icons_cache(self.all_icons_dict)
        self.phtv.set_style_cache(style_dict)

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
        name=track[0]
        obj=self._get_obj_from_track(track)
        if obj:            
            self._changing_from_code=True
            # update values in structure
            self.phtv.tracker.set_value(track,value,subtype)
            # update values inside object
            m_size=self.phce.tracker.get_value([name,"Size","value"])
            m_pos=self.phce.tracker.get_value([name,"Position","value"])
            m_anchor=self.phce.tracker.get_value([name,"Anchor","value"])
            self.set_obj_size_position_anchor(obj,m_size,m_pos,m_anchor)
            # m_parent=self.phce.tracker.get_value([name,"Parent","value"])
            m_lock_size=self.phce.tracker.get_value([name,"Lock Size","value"])
            allow_user_resize=self.phce.tracker.get_value([name,"Size","meta[editable]"])
            m_lock_position=self.phce.tracker.get_value([name,"Lock Position","value"])
            allow_user_repos=self.phce.tracker.get_value([name,"Position","meta[editable]"])
            view_z_pos_list=self.phce.tracker.get_value([name,"View Z","value"])
            ostyle_dict=self._get_style_dict_from_track([name])
            for key,value in obj.style_dict.items():
                if ostyle_dict.get(key) != value:
                    self.set_obj_style(obj,ostyle_dict)
                    # On next update apply the style
                    obj.item_xy._is_new_style=True
                    obj.item_xz._is_new_style=True
                    obj.item_yz._is_new_style=True
                    break
            self.set_obj_view_position(obj,view_z_pos_list)
            self.set_obj_size_position_locks(obj,m_lock_size,m_lock_position,allow_user_resize,allow_user_repos)
            self.on_model_changed(obj)
            self._changing_from_code=False
            # update values in views
            self.update_tree(obj)
            # after updating object and tree
            self.update_plot_tracker(obj,track)
    
    def update_plot_tracker(self,obj,track):
        name=track[0]
        if "Tracker" not in track:
            return
        prop_track=track[:-1]
        prop=prop_track[-1]
        plot_tracker=self.plot_trackers.get(prop)
        if isinstance(plot_tracker,TrackerPlot):
            val_dict=self.phce.tracker.validate_node(prop_track)
            yyy=self.phce.tracker.get_value(prop_track+["value"])
            # plot tracker the pt_obj_id is the property(Speed, power ...) the prop is the tool
            pt_obj_id = prop
            pt_prop = name
            last_x=plot_tracker.get_last_x(pt_obj_id,pt_prop)
            last_y=plot_tracker.get_last_y(pt_obj_id,pt_prop)
            step=self.phce.tracker.get_value(track+["step"])
            if step and step !=last_x:
                xxx=step
            else:
                xxx=step or last_x+1
            if yyy and (last_x != xxx or last_y !=yyy):
                plot_tracker.add_point(pt_obj_id,pt_prop,xxx,yyy)

    @QtCore.pyqtSlot(list, object, str, str)
    def on_struct_item_edited(self, track, value, typestr, subtype):
        # Decide what to do with item value changed from code
        if self._do_evaluation:
            self._evaluate_conditions()
    
    def _get_obj_from_track(self,track):
        for name,obj in self.objects.items():
            if name == track[0]:
                return obj
        return None

    def _evaluate_conditions(self):
        """Evaluate conditions if changes were applied refresh treeview"""
        do_eval=self._do_evaluation
        self._do_evaluation=False
        evaluated = self.phce.evaluate_conditions_in_a_node(self.phtv.tracker.get_root())
        if evaluated or do_eval:
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
        self.left_layout = QtWidgets.QVBoxLayout(left_panel) 
        # RIGHT PANEL 
        right_panel = QtWidgets.QWidget() 
        self.right_layout = QtWidgets.QVBoxLayout(right_panel)
        # Add panels to splitter
        splitter.addWidget(left_panel) 
        splitter.addWidget(right_panel)
        # -------------------------
        # TreeWidget
        # -------------------------
        tree_splitter = QtWidgets.QSplitter()
        tree_splitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        tree_top_panel = QtWidgets.QWidget() 
        self.tree_top_layout = QtWidgets.QVBoxLayout(tree_top_panel) 
        tree_bottom_panel = QtWidgets.QWidget() 
        self.tree_bottom_layout = QtWidgets.QVBoxLayout(tree_bottom_panel) 
        tree_splitter.addWidget(tree_top_panel)
        tree_splitter.addWidget(tree_bottom_panel)      
        tree_splitter.setSizes([400, 80])  # tree big, bottom small

        self.positions_tree = QtWidgets.QTreeView(self) # QTreeWidget(self)
        
        self.tree_top_layout.addWidget(self.positions_tree)
        self.left_layout.addWidget(tree_splitter)
        # -------------------------
        # Views
        # -------------------------
        flip_v = QtGui.QTransform()
        flip_v.scale(1, -1)   # flip vertically
        flip_h = QtGui.QTransform() 
        flip_h.scale(-1, 1) # flip horizontally

        # Create controller
        self.zoomscroll = SyncedScrollZoomController()
        self.axis_sizes={}

        # Create views
        self.view_xy = SyncedView(self.zoomscroll,"XY")
        self.view_xz = SyncedView(self.zoomscroll,"XZ")
        self.view_yz = SyncedView(self.zoomscroll,"YZ")

        # Create scenes
        self.scene_xy = QtWidgets.QGraphicsScene(self)
        self.scene_xz = QtWidgets.QGraphicsScene(self)
        self.scene_yz = QtWidgets.QGraphicsScene(self)

        # Assign scenes to views
        self.view_xy.setScene(self.scene_xy)
        self.view_xz.setScene(self.scene_xz)
        self.view_yz.setScene(self.scene_yz)

        # Set hints and drag modes
        self.view_xy.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.view_xy.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
        self.view_xz.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.view_xz.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
        self.view_yz.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.view_yz.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)

        # Apply transforms
        self.view_xy.setTransform(flip_v)
        self.view_xz.setTransform(flip_v)
        self.view_yz.rotate(270)

        # IMPORTANT: store base transforms 
        self.view_xy.base_transform = self.view_xy.transform() 
        self.view_xz.base_transform = self.view_xz.transform() 
        self.view_yz.base_transform = self.view_yz.transform()

        # Register mappings
        self.zoomscroll.register_view(self.view_xy, {"h": ("X", +1), "v": ("Y", -1)})
        self.zoomscroll.register_view(self.view_yz, {"h": ("Z", -1), "v": ("Y", -1)})
        self.zoomscroll.register_view(self.view_xz, {"h": ("X", +1), "v": ("Z", -1)})
        
        # toolbar
        self.views_toolbox = QtWidgets.QToolBar("Tools")
        self.views_toolbox.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.views_toolbox.setIconSize(QtCore.QSize(36, 36))
        self.views_toolbox.setMovable(False)

        self.action_zoom_in = QtGui.QAction(self.all_icons_dict["zoom_in"], "Zoom In", self)
        self.action_zoom_out = QtGui.QAction(self.all_icons_dict["zoom_out"], "Zoom Out", self)
        self.action_fit = QtGui.QAction(self.all_icons_dict["fit"], "Fit", self)

        self.views_toolbox.addAction(self.action_fit)
        self.views_toolbox.addSeparator()
        self.views_toolbox.addAction(self.action_zoom_in)
        self.views_toolbox.addAction(self.action_zoom_out)
        
        # Add to layout
        frame = QtWidgets.QFrame()
        frame_layout = QtWidgets.QHBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)
        #Toolbox in frame
        self.views_toolbox.setFixedWidth(40)  # important
        frame_layout.addWidget(self.views_toolbox)

        # Put frame in square widget
        self.reserved_widget = SquareWidget()
        square_layout = QtWidgets.QVBoxLayout(self.reserved_widget)
        square_layout.setContentsMargins(0, 0, 0, 0)
        square_layout.setSpacing(0)
        square_layout.addWidget(frame)
   
        self.top_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.top_splitter.addWidget(ViewWithLabel(self.view_xz, "XZ (Side View)"))
        self.top_splitter.addWidget(ViewWithLabel(self.reserved_widget, "Position Helper"))
        self.top_splitter.setStretchFactor(0, 1)
        self.top_splitter.setStretchFactor(1, 0)

        self.bottom_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.bottom_splitter.addWidget(ViewWithLabel(self.view_xy, "XY (Top View)"))
        self.bottom_splitter.addWidget(ViewWithLabel(self.view_yz, "YZ (Side View)"))
        self.bottom_splitter.setStretchFactor(0, 1)
        self.bottom_splitter.setStretchFactor(1, 1)

        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        main_splitter.addWidget(self.top_splitter)
        main_splitter.addWidget(self.bottom_splitter)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 1)

        self.right_layout.addWidget(main_splitter)
        # top and bottom splitter sync
        self._syncing = False
        self.top_splitter.splitterMoved.connect(
            lambda pos, index: self.sync_splitters(self.top_splitter, self.bottom_splitter)
        )

        self.bottom_splitter.splitterMoved.connect(
            lambda pos, index: self.sync_splitters(self.bottom_splitter, self.top_splitter)
        )
        # Sets same size of XZ (height) and YZ (width)
        # XZ height = YZ width
        self.view_yz.resized.connect(lambda: self.view_xz.setFixedHeight(self.view_yz.width()))
        # XY height = YZ height
        self.view_yz.resized.connect(lambda: self.view_xy.setFixedHeight(self.view_yz.height()))
        # XZ width = XY width
        self.view_xy.resized.connect(lambda: self.view_xz.setFixedWidth(self.view_xy.width()))        
        
        # Add Plot tracker container
        self.tracker_controls = TrackerPlotsContainerControls() 
        self.tree_bottom_layout.addWidget(self.tracker_controls)
        self.plot_trackers={}
        self.tracker_window = TrackerWindow()
        self.tracker_controls.showTrackerWindowRequested.connect(
            lambda: self._show_tracker_window()
        )

        self.tracker_controls.hideTrackerWindowRequested.connect(
            lambda: self._hide_tracker_window()
        )

        #properties panel
        self.props = QtWidgets.QTextEdit()
        self.props.setReadOnly(True)
        self.props.setPlainText("Properties / debug output will go here.")
        self.tree_bottom_layout.addWidget(self._wrap_with_label(self.props, "Properties"))

        # Connect toolbar actions
        self.action_fit.triggered.connect(lambda: self.zoomscroll.set_best_fit(self.view_xy,self.view_xy.scene()))
        self.action_zoom_in.triggered.connect(lambda: self.zoomscroll.zoom_by(1.01))
        self.action_zoom_out.triggered.connect(lambda: self.zoomscroll.zoom_by(1/1.01))
        
        # Sync splitters
        def _sync_refresh():
            self.zoomscroll.set_best_fit(self.view_xy,self.view_xy.scene())
            self.sync_splitters(self.top_splitter,self.bottom_splitter)            
        QtCore.QTimer.singleShot(0, _sync_refresh)

    def _show_tracker_window(self):
        self.tracker_window.show()
        self.tracker_window.raise_()
        self.tracker_window.activateWindow()
        self.tracker_controls.on_toggle(True)

    def _hide_tracker_window(self):
        self.tracker_window.hide()
        self.tracker_controls.on_toggle(False)

    def sync_splitters(self, source, target):
        """Syncs the splitters"""
        if self._syncing:
            return

        self._syncing = True
        target.setSizes(source.sizes())
        self._syncing = False

    def resizeEvent(self, event):
        super().resizeEvent(event)

        # Keep splitters synced during window resize
        if not self._syncing:
            self._syncing = True
            self.bottom_splitter.setSizes(self.top_splitter.sizes())
            self._syncing = False

    def _sync_axis_sizes(self,set_sizes=True):
        self._sync_x_axis_size(set_sizes)
        self._sync_y_axis_size(set_sizes)
        self._sync_z_axis_size(set_sizes)
        # self.set_transformed_scene_rect(self.view_xy,self.axis_sizes["X"],self.axis_sizes["Y"])
        # self.set_transformed_scene_rect(self.view_xz,self.axis_sizes["X"],self.axis_sizes["Z"])
        # self.set_transformed_scene_rect(self.view_yz,self.axis_sizes["Y"],self.axis_sizes["Z"])
        # self.zoomscroll.update_extents(self.axis_sizes)

    def _sync_z_axis_size(self,set_sizes):
        z = self.view_yz.width()   
        if set_sizes:
            self.view_xz.setFixedHeight(z)
            # self.zoomscroll._update_scrollbar_ranges(self.view_xz)
            # self.zoomscroll._update_scrollbar_ranges(self.view_yz)
        self.axis_sizes.update({"Z":z})
    
    def _sync_y_axis_size(self,set_sizes):
        y = self.view_xy.height()   
        if set_sizes:
            self.view_yz.setFixedHeight(y)
            # self.zoomscroll._update_scrollbar_ranges(self.view_xy)
            # self.zoomscroll._update_scrollbar_ranges(self.view_yz)
        self.axis_sizes.update({"Y":y})
    
    def _sync_x_axis_size(self,set_sizes):
        x = self.view_xy.width()   
        if set_sizes:
            self.view_xz.setFixedWidth(x)
            # self.zoomscroll._update_scrollbar_ranges(self.view_xy)
            # self.zoomscroll._update_scrollbar_ranges(self.view_xz)
        self.axis_sizes.update({"X":x})

    def set_transformed_scene_rect(self,view:QtWidgets.QGraphicsView,w,h):    
        T = view.base_transform

        p1 = T.map(0, 0)
        p2 = T.map(w, 0)
        p3 = T.map(0, h)
        p4 = T.map(w, h)

        xs = [p1[0], p2[0], p3[0], p4[0]]
        ys = [p1[1], p2[1], p3[1], p4[1]]

        origin_x = min(xs)
        origin_y = min(ys)

        transformed_width  = max(xs) - min(xs)
        transformed_height = max(ys) - min(ys)

        view.scene().setSceneRect(origin_x, origin_y, transformed_width, transformed_height)

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

    def _build_model(self):
        """Builds the model from objects in the structure"""
        val_dict=self.phce.tracker.validate_node([])
        self.objects = {}
        if val_dict["found"] and val_dict["is_root"]:
            if val_dict["has_children"]:
                for child in val_dict["children_keys"]:
                    # Build object
                    child_obj = CNCObject3D(child)
                    m_size=self.phce.tracker.get_value([child,"Size","value"])
                    m_pos=self.phce.tracker.get_value([child,"Position","value"])
                    m_anchor=self.phce.tracker.get_value([child,"Anchor","value"])
                    self.set_obj_size_position_anchor(child_obj,m_size,m_pos,m_anchor)
                    m_parent=self.phce.tracker.get_value([child,"Parent","value"])
                    m_lock_size=self.phce.tracker.get_value([child,"Lock Size","value"])
                    allow_user_resize=self.phce.tracker.get_value([child,"Size","meta[editable]"])
                    m_lock_position=self.phce.tracker.get_value([child,"Lock Position","value"])
                    allow_user_repos=self.phce.tracker.get_value([child,"Position","meta[editable]"])
                    view_z_pos_list=self.phce.tracker.get_value([child,"View Z","value"])
                    ostyle_dict=self._get_style_dict_from_track([child])
                    self.set_obj_style(child_obj,ostyle_dict)
                    self.set_obj_view_position(child_obj,view_z_pos_list)
                    self.set_obj_size_position_locks(child_obj,m_lock_size,m_lock_position,allow_user_resize,allow_user_repos)
                    if m_parent in [None,'','None']:                        
                        # Set world sizes as 110% machine size
                        self.world_sizes=[max(1.0*sss,size) for sss,size in zip(m_size,self.world_sizes)]    
                    else:
                        if m_parent in self.objects.keys():
                            parent_obj=self.objects[m_parent]
                            parent_obj.attach_child(child_obj)
                    self.objects.update({child:child_obj})
                    # Add plot tracker
                    self._plot_tracker_of_obj(child_obj)

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
    
    def set_obj_view_position(self,obj:CNCObject3D,view_z_pos_list):        
        if isinstance(view_z_pos_list,list) and len(view_z_pos_list)==3:
            obj.view_z_pos.update({"xy":view_z_pos_list[0]})
            obj.view_z_pos.update({"xz":view_z_pos_list[1]})
            obj.view_z_pos.update({"yz":view_z_pos_list[2]})
    
    def set_obj_style(self,obj:CNCObject3D,ostyle_dict):    
        for key,value in ostyle_dict.items():    
            obj.style_dict.update({key:value})
        
    def set_obj_size_position_locks(self,obj:CNCObject3D,lock_size_list,lock_position_list,allow_user_resize,allow_user_repos):
        if allow_user_resize == False:
            obj.allow_user_resize=False
        else:
            obj.allow_user_resize=True

        if allow_user_repos == False:
            obj.allow_user_repos=False
        else:
            obj.allow_user_repos=True
        if isinstance(lock_size_list,list) and len(lock_size_list)==3:            
            obj.lock_w = lock_size_list[0]
            obj.lock_h = lock_size_list[1]
            obj.lock_d = lock_size_list[2]            
        if isinstance(lock_position_list,list) and len(lock_position_list)==3:
            obj.lock_x = lock_position_list[0]
            obj.lock_y = lock_position_list[1]
            obj.lock_z = lock_position_list[2]
        
    def _apply_shapes(self):
        # Apply shapes from structure
        for name,obj in self.objects.items():
            self._apply_gen_style_to_obj(name,obj)
            self._apply_shapes_to_obj(name,obj)
            # force scene to repaint
            obj.item_xy.scene().update()  
            obj.item_xz.scene().update()  
            obj.item_yz.scene().update()  

    def _get_style_dict_from_track(self,track:list[str])->dict:
        """Returns a dictionary with the Style defined values"""
        style_fill=self.phce.tracker.get_value(track+["Style","Fill","value"]) 
        if not style_fill:
            style_fill="#1570D8"
        style_pen=self.phce.tracker.get_value(track+["Style","Pen","value"]) 
        if not style_pen:
            style_pen="#000000" 
        style_fill_transparency=self.phce.tracker.get_value(track+["Style","Fill Transparency","value"]) 
        if not style_fill_transparency:
            style_fill_transparency=77
        style_pen_width=self.phce.tracker.get_value(track+["Style","Pen Width","value"]) 
        if not style_pen_width:
            style_pen_width=2
        style_line_type=self.phce.tracker.get_value(track+["Style","Line Type","value"]) 
        if not style_line_type:
            style_line_type="solid"
        return {"Line Type":style_line_type,"Fill":style_fill,"Fill Transparency":style_fill_transparency,"Pen":style_pen,"Pen Width":style_pen_width}

    def _apply_shapes_to_obj(self,name,obj:CNCObject3D):
        val_dict=self.phce.tracker.validate_node([name,"Shape"])
        has_edit_shape=False
        if val_dict["found"]:
            for child in val_dict["children_keys"]:
                track=val_dict["track"]+[child]
                points=self.phce.tracker.get_value(track+["Shape Points","value"])
                anchor=self.phce.tracker.get_value(track+["Anchor","value"]) or [0.5,0.5]
                # Styles
                ostyle_dict=self._get_style_dict_from_track(track)
                if child=="XY" and points:
                    obj.item_xy.set_shape(points, anchor=(anchor[0], anchor[1]),style=ostyle_dict)
                    has_edit_shape=True                    
                if child=="XZ" and points:
                    obj.item_xz.set_shape(points, anchor=(anchor[0], anchor[1]),style=ostyle_dict)
                    has_edit_shape=True                    
                if child=="YZ" and points:
                    obj.item_yz.set_shape(points, anchor=(anchor[0], anchor[1]),style=ostyle_dict)
                    has_edit_shape=True
                    
        if isinstance(obj,CNCObject3D):
            obj._has_shape=has_edit_shape
    
    def _apply_gen_style_to_obj(self,name,obj):
        val_dict=self.phce.tracker.validate_node([name,"Style"])
        has_edit_style=False
        if val_dict["found"]:
                track=val_dict["track"]
                # Styles
                ostyle_dict=self._get_style_dict_from_track([name])
                # On next update apply the style
                obj.item_xy._is_new_style=True
                obj.item_xz._is_new_style=True
                obj.item_yz._is_new_style=True

                obj.item_xy.set_style(obj.item_xy,ostyle_dict)
                obj.item_xz.set_style(obj.item_xz,ostyle_dict)
                obj.item_yz.set_style(obj.item_yz,ostyle_dict)
                has_edit_style=True

    def _build_plot_trackers(self):
        for name, plot_tracker in self.plot_trackers.items():
            self.tracker_window.container.add_plot(plot_tracker)

    def _plot_tracker_of_obj(self,obj:CNCObject3D):
        name=obj.name
        val_dict=self.phce.tracker.validate_node([name,"Tracker"])
        has_plot_tracker=False
        if val_dict["found"]:
            for child in val_dict["children_keys"]:
                track=val_dict["track"]+[child]
                # val_child=self.phce.tracker.validate_node(track)
                plot_tracker_value=self.phce.tracker.get_value(track+["value"])
                plot_tracker_unit=self.phce.tracker.get_value(track+["unit"]) or ""
                plot_tracker_x_label=self.phce.tracker.get_value(track+["xlabel"]) or ""
                plot_tracker_x_unit=self.phce.tracker.get_value(track+["xunit"]) or "step"
                style_pen_color=self.phce.tracker.get_value([name,"Style","Pen","value"]) or "#000000" 
                style_pen_width=self.phce.tracker.get_value([name,"Style","Pen Width","value"]) or 2
                style_line_type=self.phce.tracker.get_value([name,"Style","Line Type","value"]) or "solid"
                plot_tracker=self.plot_trackers.get(child)
                if not isinstance(plot_tracker,TrackerPlot):
                    plot_tracker=TrackerPlot()  
                # on plot_tracker: obj_id -> (speed, power...) prop is (tool)    
                pt_obj_id=child
                pt_prop=name                
                last_x=plot_tracker.get_last_x(pt_obj_id,pt_prop)
                plot_tracker.set_title(pt_obj_id)
                plot_tracker.set_y_label(pt_obj_id,plot_tracker_unit)
                plot_tracker.set_x_label(plot_tracker_x_label,plot_tracker_x_unit)
                plot_tracker.ensure_curve(pt_obj_id,pt_prop,style_pen_color,style_pen_width,style_line_type)
                step=self.phce.tracker.get_value(track+["step"])
                xxx=step or last_x
                if plot_tracker_value:
                    plot_tracker.add_point(pt_obj_id,pt_prop,xxx,plot_tracker_value)          
                self.plot_trackers.update({pt_obj_id:plot_tracker})           

    def _build_views(self):
        """Builds The views Populating the items"""
        for name,obj in self.objects.items():
            obj_style_dict=obj.style_dict

            obj.item_xy = ProjectedItem(
                obj, ProjectedItem.PlaneXY,
                on_model_changed=self.on_model_changed,
                color=obj_style_dict
            )
            self.scene_xy.addItem(obj.item_xy)
            #self.items_xy[obj] = obj.item_xy

            obj.item_xz = ProjectedItem(
                obj, ProjectedItem.PlaneXZ,
                on_model_changed=self.on_model_changed,
                color=obj_style_dict
            )
            self.scene_xz.addItem(obj.item_xz)
            #self.items_xz[obj] = obj.item_xz

            obj.item_yz = ProjectedItem(
                obj, ProjectedItem.PlaneYZ,
                on_model_changed=self.on_model_changed,
                color=obj_style_dict
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
        self._apply_shapes_to_obj(obj.name,obj)
        # force scene to repaint
        obj.item_xy.update()  
        obj.item_xz.update()  
        obj.item_yz.update()
        obj.item_xy.scene().update()  
        obj.item_xz.scene().update()  
        obj.item_yz.scene().update()
    
    def update_tree(self,obj: CNCObject3D):
        name=obj.name
        self._do_evaluation=True
        decimals=self.phce.tracker.get_value([name,"Size","meta[constraints[decimals]]"]) or 2
        sizes=[round(obj.w,decimals),round(obj.h,decimals),round(obj.d,decimals)]
        self.phce.tracker.set_value([name,"Size","value"],sizes,"float")

        decimals=self.phce.tracker.get_value([name,"Position","meta[constraints[decimals]]"]) or 2
        positions=[round(obj.x,decimals),round(obj.y,decimals),round(obj.z,decimals)]
        self.phce.tracker.set_value([name,"Position","value"],positions,"float")

        decimals=self.phce.tracker.get_value([name,"Anchor","meta[constraints[decimals]]"]) or 2
        anchors=[round(obj.anchor_x,decimals),round(obj.anchor_y,decimals),round(obj.anchor_z,decimals)]
        self.phce.tracker.set_value([name,"Anchor","value"],anchors,"float")   
        self.phtv.treeview_fit_to_contents(1)     
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
        self.zoomscroll.fit_all()


class SquareWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumSize(40, 40)  # toolbar width = minimum square size

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return width

    def sizeHint(self):
        return QtCore.QSize(200, 200)
    

class ResizeHandle(QtWidgets.QGraphicsRectItem):
    def __init__(self, parent_item, axis, on_resize):
        super().__init__(-4, -4, 8, 8, parent_item)
        self.axis = axis
        self.on_resize = on_resize
        self.parent_item = parent_item

        self.setBrush(QtGui.QColor("yellow"))
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setZValue(333)

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


class SyncedView(QtWidgets.QGraphicsView):
    resized = QtCore.pyqtSignal()   

    def __init__(self, controller:SyncedScrollZoomController,name:str="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name=name
        self.controller = controller
        self._ignore_scroll = False
        self._ignore_zoom = False
        self.current_zoom = 1
        #global axis extents 
        self.extents = {"X": 1000, "Y": 1000, "Z": 1000}

        # Save base transform (flip, rotate, etc.)
        self.base_transform = QtGui.QTransform()

        # Connect scrollbars
        self.horizontalScrollBar().valueChanged.connect(self._on_scroll)
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)

        # Connect zoom sync
        controller.zoom_changed.connect(self.apply_zoom)

    # Wheel zoom
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.controller.zoom_by(1.01)
        else:
            self.controller.zoom_by(1/1.01)

    # Scroll → controller
    def _on_scroll(self):
        if self._ignore_scroll:
            return
        h = self.horizontalScrollBar().value()
        v = self.verticalScrollBar().value()
        self.controller.update_global_scroll(self, h, v)

    # Controller → scroll
    def apply_global_scroll(self, global_scroll, mapping):
        self._ignore_scroll = True
        z = self.current_zoom
        msg=''
        msg+=f"{self.name}"
        if "h" in mapping:
            axis, sign = mapping["h"]
            px = int(global_scroll[axis] * z * sign)
            self.horizontalScrollBar().setValue(px)
            msg+=f" {axis} h->{px} "

        if "v" in mapping:
            axis, sign = mapping["v"]
            px = int(global_scroll[axis] * z * sign)
            self.verticalScrollBar().setValue(px)
            msg+=f" {axis} v->{px} "
        # print(msg)

        self._ignore_scroll = False

    # Controller → zoom
    def apply_zoom(self, factor):
        self._ignore_zoom = True
        self.current_zoom = factor
        t = QtGui.QTransform(self.base_transform)
        t.scale(factor, factor)
        self.setTransform(t)
        self._ignore_zoom = False
    # def apply_zoom(self, factor):
    #     self._ignore_zoom = True
    #     self.current_zoom = factor

    #     t = QtGui.QTransform(self.base_transform)
    #     t.scale(factor, factor)
    #     self.setTransform(t)

    #     self.update_scrollbar_ranges()
    #     self._ignore_zoom = False
    
    def update_extents(self, **axis_sizes):
        """
        Update global axis extents.
        Example: controller.update_extents(X=1200, Z=800)
        """
        changed = False
        for axis, size in axis_sizes.items():
            if size > self.extents.get(axis, 0):
                self.extents[axis] = size
                changed = True

        if changed:
            self._apply_scene_rects()
    
    def _apply_scene_rects(self):
        """Compute each view's sceneRect from its mapping"""
        for view, mapping in self.views:
            if "h" in mapping and "v" in mapping:
                h_axis, _ = mapping["h"]
                v_axis, _ = mapping["v"]

                w = self.extents[h_axis]
                h = self.extents[v_axis]

                view.setSceneRect(QtCore.QRectF(0, 0, w, h))
                view.update_scrollbar_ranges()

    def update_scrollbar_ranges(self):
        sr = self.sceneRect()
        vp = self.viewport().size()
        z = self.current_zoom

        h_max = max(0, sr.width() * z - vp.width())
        v_max = max(0, sr.height() * z - vp.height())

        self.horizontalScrollBar().setRange(0, int(h_max))
        self.horizontalScrollBar().setPageStep(vp.width())

        self.verticalScrollBar().setRange(0, int(v_max))
        self.verticalScrollBar().setPageStep(vp.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()


class ViewWithLabel(QtWidgets.QWidget):
    def __init__(self, view, label_text):
        super().__init__()
        self.view = view

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        label = QtWidgets.QLabel(label_text)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label.setFixedHeight(20)

        layout.addWidget(label)
        layout.addWidget(view)

    def sizeHint(self):
        return self.view.sizeHint()

    def minimumSizeHint(self):
        return self.view.minimumSizeHint()


def main():
    app = QtWidgets.QApplication(sys.argv)
    dlg = PositionHelper()
    dlg.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
