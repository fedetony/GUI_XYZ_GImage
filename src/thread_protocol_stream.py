import threading
import logging

from class_gcode_streamer import *
from thread_xyz_multi_interface import InterfaceSerialReaderWriterThread,XYZMulti

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
ahandler=logging.StreamHandler()
ahandler.setLevel(logging.INFO)
ahandler.setFormatter(formatter)
log.addHandler(ahandler)

RESPONSE_TIME_ABORT = 5.0

class Protocol_Stream(threading.Thread):
    def __init__(self, 
                 xyz_thread:XYZMulti, 
                 stream_killer_event:threading.Event, 
                 stream_stop_event:threading.Event, 
                 stream_hold_event:threading.Event,
                 behavior_override:dict=None):
        
        super().__init__(name="Protocol Stream")

        
        self.xyz_thread = xyz_thread
        
        self.killer_event = stream_killer_event
        self.stop_event = stream_stop_event
        self.hold_event = stream_hold_event

        self.counters = None
        self.CH = self.xyz_thread.ser_read_thread.CH

        # Transport
        self.transport = QueueDataTransport(self.xyz_thread.ser_read_thread)

        # Interface defaults
        self.interface_configuration = self.CH.get_interface_config(
            self.CH.InterfaceConfigallids, self.CH.id
        )

        self.cycle_time = max(float(self.interface_configuration.get('cycletime',0.1)),0.01)
        self.maxBufferBytes = int(self.interface_configuration.get('maxBufferBytes',256))
        self.maxInFlight = int(self.interface_configuration.get('maxInFlight',1))
        self.statusRate = float(self.interface_configuration.get('statusRate',2.5*self.cycle_time))

        status_cmd, is_ok = self.CH.Get_Gcode_for_Action("statusReport", {}, True)
        if not is_ok:
            status_cmd = ""

        behavior = {
            "cycleTime": self.cycle_time,
            "maxBufferBytes": self.maxBufferBytes,
            "maxInFlight": self.maxInFlight,
            "statusCommand": status_cmd,
            "statusRate": self.statusRate
        }

        if behavior_override:
            behavior.update(behavior_override)

        self.protocol = ProtocolEngine(ProtocolConfig(behavior))

        self.streamer = GCodeStreamer(
            transport=self.transport,
            protocol=self.protocol,
            killer_event=self.killer_event,
            stop_event=self.stop_event,
            pause_event=self.hold_event
        )

    # -----------------------------
    # Public API
    # -----------------------------
    def start_stream(self, text:str):
        """Start thread + enqueue text + attach counters."""
        total_lines = len(text.splitlines())
        self.append_counters(total_lines)
        self.start()
        self.enqueue_text(text)

    def enqueue_text(self, text:str):
        for line in text.splitlines():
            self.streamer.enqueue(line)

    def stop_stream(self):
        self.killer_event.set()

    def get_all_nums(self):
        if self.counters:
            return self.counters.get_all_nums()
        return None

    def append_counters(self, number_total_lines:int):
        self.counters = StreamCounters(
            streamer=self.streamer,
            tracker=self.protocol.tracker,
            total_file_lines=number_total_lines
        )
    def machine_is_alive(self):
        # Layer 1: serial thread alive
        if not self.xyz_thread.is_alive():
            return False

        # Layer 2: soft reset or stop means machine is not in a streaming state
        if self.xyz_thread.machine_event_softreset.is_set():
            return False

        # Layer 3: protocol timeout (optional)
        if self.protocol.tracker.in_flight_bytes > 0:
            if time.time() - self.protocol.last_ack_time > RESPONSE_TIME_ABORT:
                return False

        return True

    def log_stream_position(self, reason):
        if self.counters:
            nums = self.counters.get_all_nums()
            buff, txt, consumed, left, tot, totfile = nums
            log.info(f"{reason}: ack={consumed}, sent={tot}, left={left}, buff={buff}")

    # -----------------------------
    # Thread loop
    # -----------------------------
    def run(self):
        self.streamer.start()

        while not self.killer_event.wait(0.05):

            # 1. Detect disconnect
            if not self.machine_is_alive():
                self.log_stream_position("DISCONNECT")
                self.killer_event.set()
                break

            # 2. Pause streaming when machine is on hold
            if self.xyz_thread.machine_event_hold.is_set():
                self.hold_event.set()
                self.log_stream_position("PAUSE")
            else:
                self.hold_event.clear()

            # 3. Stop streaming when machine is stopped
            if self.xyz_thread.machine_event_stop.is_set():
                self.stop_event.set()
                self.log_stream_position("STOP")
            else:
                self.stop_event.clear()

            # 4. Soft reset kills the stream
            if self.xyz_thread.machine_event_softreset.is_set():
                self.log_stream_position("SOFTRESET")
                self.killer_event.set()
                break

            # 5. Resume logging
            if self.xyz_thread.machine_event_resume.is_set():
                self.log_stream_position("RESUME")

        log.info("Protocol Stream ended.")





