
from PyQt6 import QtCore #, QtGui, QtWidgets
import threading
import logging

import datetime

from class_ST import SignalTracker
#from thread_xyz_multi_interface import XYZMulti,InterfaceSerialReaderWriterThread
#from class_gcode_streamer import GCodeStreamer
from class_CH import *

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
ahandler=logging.StreamHandler()
ahandler.setLevel(logging.INFO)
ahandler.setFormatter(formatter)
log.addHandler(ahandler)
# ┌──────────────────────────────┐
# │ Serial Thread (raw parsing)  │
# └───────────────┬──────────────┘
#                 │ set_data(**raw)
#                 ▼
# ┌──────────────────────────────┐
# │     DataStatusTracker        │
# │  (maps raw → MachineStatus)  │
# └───────────────┬──────────────┘
#                 │ statusChanged(dict)
#                 ▼
# ┌──────────────────────────────┐
# │       MachineStatus          │
# │ (central normalized state)   │
# └───────────────┬──────────────┘
#                 │
#                 ▼
# ┌──────────────────────────────┐
# │             UI               │
# │ visualizer, dialogs, panels  │
# └──────────────────────────────┘

class DataStatusTracker:
    def __init__(self, CH:Command_Handler=None):
        super().__init__()
        self.data={}
        self.machine_status=None
        if CH:
            self.CH=CH
            self.init_data()
        else:
            self.machine_status=MachineStatus([])
    
    def init_data(self):
        an_id=self.CH.id #actual interface id
        parameter_list=self.CH.Get_list_of_all_parameters_in_interface(an_id)
        for param in parameter_list:
            self.data[param]=None
        # Set machine status
        self.machine_status=MachineStatus(parameter_list)
    
    def get_data(self):
        return self.machine_status.snapshot()

    def set_data(self, **kwargs):
        self.machine_status.update(**kwargs)

    def add_param(self,param,value=None):
        self.machine_status.add_param(param,value)
    
    def remove_param(self,param):
        self.machine_status.remove_param(param)
    
    def get_param(self,param):
        return self.machine_status.get_param(param)


class TimeTracker:
    """
    Tracks start/stop times, elapsed time, deltas, and timestamps.
    Independent of UI and threads.
    """
    def __init__(self):
        self._start = None
        self._last = None
        self._running = False
    
    def set_last(self, last:datetime.datetime):
        self._last = last

    def start(self):
        now = datetime.datetime.now()
        self._start = now
        self._last = now
        self._running = True

    def stop(self):
        self._running = False

    def reset(self):
        self._start = None
        self._last = None
        self._running = False

    def elapsed(self):
        if not self._running or self._start is None:
            return datetime.timedelta(0)
        return datetime.datetime.now() - self._start

    def delta(self):
        """
        Time since last delta() call.
        Useful for simulation step updates.
        """
        if not self._running or self._last is None:
            return datetime.timedelta(0)
        now = datetime.datetime.now()
        dt = now - self._last
        self._last = now
        return dt

    def timestamp(self):
        return datetime.datetime.now()

###############################################
#       Monitoring status
###############################################

# ┌──────────────────────────────┐
# │        StreamMonitor         │
# │ (queue, ack, progress)       │
# └──────────────────────────────┘

class MachineStatus(QtCore.QObject):
    statusChanged = QtCore.pyqtSignal(dict)

    def __init__(self, param_names:list):
        super().__init__()
        self._mutex = QtCore.QMutex()
        self._data = {name: 0.0 for name in param_names}
        self._data["state"] = "disconnected"

    def update(self, **kwargs):
        changed = False
        with QtCore.QMutexLocker(self._mutex):
            for k, v in kwargs.items():
                if k in self._data and self._data[k] != v:
                    self._data[k] = v
                    changed = True
        if changed:
            self.statusChanged.emit(self.snapshot())

    def snapshot(self):
        with QtCore.QMutexLocker(self._mutex):
            return dict(self._data)
    
    def add_param(self, param, value=None):
        with QtCore.QMutexLocker(self._mutex):
            if param not in self._data:
                self._data[param] = value
                self.statusChanged.emit(self.snapshot())

    def remove_param(self, param):
        with QtCore.QMutexLocker(self._mutex):
            if param in self._data:
                self._data.pop(param)
                self.statusChanged.emit(self.snapshot())

    def set_param(self, param, value=None):
        with QtCore.QMutexLocker(self._mutex):
            if param in self._data and self._data[param] != value:
                self._data[param] = value
                self.statusChanged.emit(self.snapshot())

    def get_param(self,param):
        with QtCore.QMutexLocker(self._mutex):
            if param in self._data:
                return self._data[param]
            return None

# on main 
# self.data_tracker = DataStatusTracker(self.CH)
# Connect the signal
# self.data_tracker.machine_status.statusChanged.connect(self.on_machine_status_changed)


# For main
# def on_machine_status_changed(self, data):
#     # Update main UI
#     self.update_main_labels(data)

#     # Forward to status dialog
#     if self.status_dialog is not None:
#         self.status_dialog.update_status(data)

#     # Forward to visualizer
#     if self.visualizer is not None:
#         self.visualizer.update_position(data)

#     # Forward to position viewer
#     if self.position_viewer is not None:
#         self.position_viewer.update_coordinates(data)



#                 ┌──────────────────────────────┐
#                 │          Sender Thread       │
#                 │  (queue, ACK, flow control)  │
#                 └───────────────▲──────────────┘
#                                 │
#                                 │ direct ACK/error/alarm
#                                 │
# ┌───────────────────────────────┴──────────────────────────────┐
# │                        Read Thread                           │
# │   (parses machine lines, updates MachineStatus, emits ACK)   │
# └───────────────▲───────────────────────────────▲──────────────┘
#                 │                               │
#                 │ statusChanged(dict)           │ UI events
#                 │                               │
# ┌───────────────┴──────────────┐     ┌──────────┴──────────────┐
# │        MachineStatus         │     │      SignalTracker      │
# │ (central state cache only)   │     │ (UI-only event bus)     │
# └───────────────▲──────────────┘     └──────────▲──────────────┘
#                 │                               │
#                 │                               │
# ┌───────────────┴───────────────┐     ┌─────────┴───────────────┐
# │           Main Window         │     │   Visualizer / Status   │
# │ (distributes state to UI)     │     │   Dialog / Position UI  │
# └───────────────────────────────┘     └─────────────────────────┘

# ┌──────────────────────────────┐
# │      Read Thread             │
# │  (parses machine lines)      │
# └───────────────┬──────────────┘
#                 │
#                 ▼
# ┌──────────────────────────────┐
# │     MachineStatusUpdater     │
# │  (updates central state)     │
# └───────────────┬──────────────┘
#                 │ statusChanged(dict)
#                 ▼
# ┌──────────────────────────────┐
# │       MachineStatus          │
# │  (single source of truth)    │
# └───────────────┬──────────────┘
#                 │
#                 ▼
# ┌──────────────────────────────┐
# │      UIStateController       │
# │ (enable/disable, timers, UI) │
# └───────────────┬──────────────┘
#                 │
#                 ▼
# ┌──────────────────────────────┐
# │       SignalTracker          │
# │ (UI-only event bus)          │
# └──────────────────────────────┘

class MachineStatusUpdater(threading.Thread):
    def __init__(self, machine_status:MachineStatus, 
                 xyz_thread,#:XYZMulti, 
                 killer_event:threading.Event):
        super().__init__(name="MachineStatusUpdater")
        self.machine_status = machine_status
        self.xyz_thread = xyz_thread
        self.killer_event = killer_event
        self.cycle_time = xyz_thread.ser_read_thread.cycle_time

    def run(self):
        while not self.killer_event.wait(self.cycle_time):
            data = self.xyz_thread.read()
            self.machine_status.update(
                X=data.get('XPOS'),
                Y=data.get('YPOS'),
                Z=data.get('ZPOS'),
                state=data.get('STATE_XYZ'),
                STATUS=data.get('STATUS')
            )

from class_gcode_streamer import ProtocolEngine
class StreamMonitor(QtCore.QObject):
    streamChanged = QtCore.pyqtSignal(dict)

    def __init__(self, 
                 protocol_engine: ProtocolEngine,
                 killer_event: threading.Event, 
                 cycle:float =0.1
                 ):
        super().__init__()
        self.engine = protocol_engine
        self.killer_event = killer_event
        self.cycle = cycle

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while not self.killer_event.wait(self.cycle):
            snap = self.engine.tracker.snapshot()
            self.streamChanged.emit(snap)


class UIStateController(QtCore.QObject):
    def __init__(self, 
                 ST:SignalTracker, 
                 machine_status:MachineStatus,
                 stream_monitor:StreamMonitor = None):
        super().__init__()

        self.ST = ST
        self.machine_status = machine_status
        self.stream_monitor = stream_monitor

        self.tt = TimeTracker()
        self.timer_running = False
        self.start_time = None

        # Connect machine status
        machine_status.statusChanged.connect(self.on_status_changed)

        # Connect stream progress (optional)
        if stream_monitor:
            stream_monitor.streamChanged.connect(self.on_stream_changed)

    # -------------------------------
    # MACHINE STATUS HANDLING
    # -------------------------------
    def on_status_changed(self, data):
        state = data.get("state")

        # Enable/disable buttons
        running_states = [5,6,7,8,9,10]
        self.ST.enable_bSTOP.emit(state in running_states)
        self.ST.enable_bHOLD.emit(state in running_states)

        # Timer update
        if self.timer_running:
            elapsed = datetime.datetime.now() - self.start_time
            self.ST.timer_change.emit(str(elapsed))

        # State text
        self.ST.state_text.emit(str(state))

        # Start/stop timer based on state
        if state == 5:  # running
            if not self.timer_running:
                self.start_timer()
        elif state in [0,1,2]:  # idle, disconnected, ready
            self.stop_timer()

    # -------------------------------
    # STREAM PROGRESS HANDLING
    # -------------------------------
    def on_stream_changed(self, info:dict):
        # Forward raw info
        self.ST.stream_info_change.emit(info)

        sent = info["sent"]
        ack = info["ack"]
        finalized = info["finalized"]
        in_flight = info["in_flight_bytes"]
        total = info["total_bytes"]

        # Progress %
        if sent > 0:
            progress = (finalized / sent) * 100
            self.ST.progress_change.emit(progress)

        # Throughput (bytes/sec)
        dt = self.tt.delta().total_seconds()
        if dt > 0:
            throughput = info["delta"] / dt
            self.ST.throughput_change.emit(throughput)

        # ETA
        if finalized > 0 and sent > finalized:
            remaining = sent - finalized
            eta = remaining / max(throughput, 1e-6)
            self.ST.eta_change.emit(eta)

    # -------------------------------
    # TIMER CONTROL
    # -------------------------------
    def set_start(self, start_time=None):
        if start_time:
            self.tt.set_last(start_time)
            self.start_time = start_time

    def start_timer(self):
        self.timer_running = True
        self.start_time = datetime.datetime.now()
        self.tt.start()

    def stop_timer(self):
        self.timer_running = False
        self.tt.stop()

