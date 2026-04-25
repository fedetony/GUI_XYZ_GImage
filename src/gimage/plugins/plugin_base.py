import threading
import math
from class_struct_tracker import TreeStructTracker
from PIL import Image
from class_CH import Command_Handler
import copy

EXCLUDE_CH_PARAMS = ['par','msg','Gcommand','G54toG59','setting','value','Block','gcode']

STATUS_TRACKER_BASE = {
    "ch_tracker":{},
    "last_position": {"x": 0, "y": 0, "z": 0},
    "position": {"x": 0, "y": 0, "z": 0},
    "last_tool_state": {"is_up": None, 
                        "power": 0, 
                        "extrude": 0, 
                        "feedrate":0,
                        "color":None
                        },
    "tool_state": {"is_up": None, 
                        "power": 0, 
                        "extrude": 0, 
                        "feedrate":0,
                        "color":None
                        },
    "distances": {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "linear": 0.0,
        "rapid": 0.0,
        "total": 0.0,
    },
    "feed": {
        "last": 0,
        "sum": 0,
        "count": 0,
    },
    "machine": {
        "units": "mm",
        "mode": "absolute",
    }
}

class GImageTechniqueBase:
    def __init__(self, 
                 image:Image.Image, 
                 config:TreeStructTracker, 
                 ch:Command_Handler,
                 machine,
                 tool,
                 emit_action, 
                 emit_progress, 
                 emit_status, 
                 killer_event:threading.Event, 
                 stop_event:threading.Event,
                 status:dict,
                 ):
        self.machine = machine
        self.tool = tool
        self.image = image
        self.config = config
        self.emit_action = emit_action
        self.emit_progress = emit_progress
        self.emit_status = emit_status
        self.killer_event = killer_event
        self.stop_event = stop_event
        self.ch=ch
        self.status=status
        # Shared status tracker
        self.status = status if status else copy.deepcopy(STATUS_TRACKER_BASE)
        # Attach status_update to both plugins
        setattr(self.tool, "status_update", self.status_update)
        setattr(self.machine, "status_update", self.status_update)
        all_params=self.ch.Get_list_of_all_parameters_in_interface(self.ch.id)
        self.available_parameters=[]
        for param in set(all_params):
            if param in EXCLUDE_CH_PARAMS:
                continue
            self.available_parameters.append(param)
        self.axis_parameters=self._list_parameters_for_action("coordSet")
        setattr(self.tool, "status", self.status)
        setattr(self.machine, "status", self.status)

        
    def _list_parameters_for_action(self,action):
        parameters=self.ch.Get_Parameters_Needed_for_action(action,self.ch.id)
        return list(parameters.keys())

    def should_stop(self):
        return self.killer_event.is_set() or self.stop_event.is_set()

    def check_stop(self):
        if self.should_stop():
            self.emit_status("Cancelled")
            raise StopIteration

    def process(self):
        raise NotImplementedError

    def status_update(self, **kwargs):
        """
        Update the shared status tracker with any combination of:
        axis values (X,Y,Z,A,E,R,S,H...), feed, rapid, power, extrude, is_up,
        feedrate, color, etc.

        This version is fully axis‑agnostic and adapts to ANY machine interface.
        """

        ch_tracker      = self.status["ch_tracker"]
        pos             = self.status["position"]
        last_pos        = self.status["last_position"]
        dist            = self.status["distances"]
        feedstat        = self.status["feed"]
        tool_state      = self.status["tool_state"]
        last_tool_state = self.status["last_tool_state"]

        # ---------------------------------------------------------
        # 0. Update CH tracker for ALL known parameters
        # ---------------------------------------------------------
        for kwa, val in kwargs.items():
            if kwa in self.available_parameters:
                ch_tracker[kwa] = val

        # ---------------------------------------------------------
        # 1. Extract axis values dynamically
        # ---------------------------------------------------------
        axis_values = {
            axis: kwargs.get(axis)
            for axis in self.axis_parameters
            if axis in kwargs
        }

        # Extract non-axis parameters
        feed     = kwargs.get("feed")
        rapid    = kwargs.get("rapid", False)
        power    = kwargs.get("power") or kwargs.get("S")
        extrude  = kwargs.get("extrude") or kwargs.get("E")
        is_up    = kwargs.get("is_up")
        feedrate = kwargs.get("feedrate") or kwargs.get("F")
        color    = kwargs.get("color")

        # ---------------------------------------------------------
        # 2. Compute movement deltas for ALL axes
        # ---------------------------------------------------------
        moved_axes = {}

        for axis, new_val in axis_values.items():
            if axis in pos and new_val is not None:
                delta = new_val - pos[axis]
                if delta != 0:
                    moved_axes[axis] = delta

        # ---------------------------------------------------------
        # 3. Distance tracking (multi-axis)
        # ---------------------------------------------------------
        if moved_axes:
            # Euclidean distance across all axes
            euclidean = math.sqrt(sum(delta * delta for delta in moved_axes.values()))

            # Rapid vs linear
            if rapid:
                dist["rapid"] += euclidean
            else:
                dist["linear"] += euclidean

            # Per-axis distances
            for axis, delta in moved_axes.items():
                dist.setdefault(axis, 0.0)
                dist[axis] += abs(delta)

            dist["total"] += euclidean

            # Update last and current positions
            for axis, delta in moved_axes.items():
                last_pos[axis] = pos[axis]
                pos[axis] = axis_values[axis]

        # ---------------------------------------------------------
        # 4. Accumulative Feed tracking
        # ---------------------------------------------------------
        if feed is not None:
            feedstat["last"] = feed
            feedstat["sum"] += feed
            feedstat["count"] += 1

        # ---------------------------------------------------------
        # 5. Tool state tracking
        # ---------------------------------------------------------
        if power is not None:
            last_tool_state["power"] = tool_state["power"]
            tool_state["power"] = power

        if color is not None:
            last_tool_state["color"] = tool_state["color"]
            tool_state["color"] = color

        if feedrate is not None:
            last_tool_state["feedrate"] = tool_state["feedrate"]
            tool_state["feedrate"] = feedrate

        if extrude is not None:
            last_tool_state["extrude"] = tool_state["extrude"]
            tool_state["extrude"] += extrude

        if is_up is not None:
            last_tool_state["is_up"] = tool_state["is_up"]
            tool_state["is_up"] = is_up

        return self.status




