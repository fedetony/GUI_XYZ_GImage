import threading
import queue
import re
import logging
import time
#from common import *

# install pySerial NOT serial!!!
import serial
import class_CH

from thread_xyz_multi_interface import InterfaceSerialReaderWriterThread

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
ahandler=logging.StreamHandler()
ahandler.setLevel(logging.INFO)
ahandler.setFormatter(formatter)
log.addHandler(ahandler)

class QueueDataTransport:
    def __init__(self, ser_thread:InterfaceSerialReaderWriterThread):
        self.ser = ser_thread
        self.write_q = ser_thread.rx_queue
        self.read_q  = ser_thread.read_queue   # you already have this internally

    def write_line(self, line: str):
        self.write_q.put(line + "\n")

    def read_lines(self):
        lines = []
        try:
            while True:
                lines.append(self.read_q.get_nowait())
        except queue.Empty:
            pass
        return lines

class ProtocolConfig:
    def __init__(self, behavior: dict):
        self.behavior = behavior

        # Dynamically attach all behavior keys as attributes
        for key, value in behavior.items():
            # normalize key names: remove spaces, unify case
            attr = str(key).strip().replace(" ", "")
            setattr(self, attr, value)

        # Provide sane defaults if missing
        self.cycleTime       = float(getattr(self, "cycleTime", 0.1))
        self.maxBufferBytes  = int(getattr(self, "maxBufferBytes", 0))
        self.maxInFlight     = int(getattr(self, "maxInFlight", 1))
        self.statusCommand   = getattr(self, "statusCommand", "")
        self.statusRate      = float(getattr(self, "statusRate", 0.25))

class ProtocolEngine:
    """
    Lightweight flow‑control engine for streamed G‑code.

    This class does NOT parse machine responses and does NOT track machine
    position, status, alarms, or any semantic information. All parsing and
    machine‑specific interpretation is handled by the Command Handler (CH)
    inside the serial thread.

    The ProtocolEngine has a single responsibility:
        → Decide WHEN the next streamed G‑code line may be sent.

    It does this by tracking:
        - in‑flight commands (for machines that acknowledge each line)
        - buffer usage (for machines with byte‑limited input buffers)
        - status‑polling intervals (for machines that require manual polling)

    The ProtocolEngine receives *parsed* feedback from the CH via on_feedback().
    The CH is responsible for detecting ACK/ERROR/ALARM and exposing them as
    boolean flags in the parsed dict.

    This separation ensures:
        - Immediate commands (emergency stop, hold, resume, etc.) bypass the
          streamer safely and are handled directly by the serial thread + CH.
        - Machines with no buffer or strict ACK‑per‑line behavior are respected.
        - Machines with large buffers (GRBL, TinyG) are handled efficiently.
        - The streamer remains firmware‑agnostic and fully config‑driven.
    """

    def __init__(self, cfg: ProtocolConfig):
        """
        Initialize the flow‑control engine.

        Parameters
        ----------
        cfg : ProtocolConfig
            Configuration object containing behavior parameters such as:
                - maxBufferBytes : int
                - maxInFlight    : int
                - statusCommand  : str
                - statusRate     : float
        """
        self.cfg = cfg
        self.in_flight   = 0
        self.buffer_used = 0
        self.last_poll   = 0.0

    def can_send(self, line: str) -> bool:
        """
        Determine whether the next streamed G‑code line may be sent.

        For byte‑buffered machines (e.g., GRBL, TinyG):
            - Uses maxBufferBytes to ensure we do not overflow the device buffer.

        For ACK‑based machines (e.g., Marlin, Reprap, Klipper):
            - Uses maxInFlight to ensure we do not send more lines than the
              firmware can track before acknowledging.

        Parameters
        ----------
        line : str
            The G‑code line being considered for transmission.

        Returns
        -------
        bool
            True if the line may be sent now, False otherwise.
        """
        max_buffer    = getattr(self.cfg, "maxBufferBytes", 0)
        max_in_flight = getattr(self.cfg, "maxInFlight", 1)

        if max_buffer > 0:
            needed = len(line) + 1
            return (self.buffer_used + needed) < max_buffer

        return self.in_flight < max_in_flight

    def on_line_sent(self, line: str):
        """
        Notify the engine that a streamed line has been sent.

        This increments the in‑flight counter and, for byte‑buffered machines,
        increases the estimated buffer usage.

        Parameters
        ----------
        line : str
            The line that was just transmitted.
        """
        self.in_flight += 1
        if self.cfg.maxBufferBytes > 0:
            self.buffer_used += len(line) + 1

    def on_feedback(self, parsed: dict):
        """
        Process parsed feedback from the Command Handler (CH).

        The CH is responsible for:
            - reading raw serial
            - parsing responses
            - detecting ACK/ERROR/ALARM
            - updating machine state

        The ProtocolEngine only reacts to the minimal flow‑control signals:
            - is_ack   → decrement in‑flight
            - is_error → decrement in‑flight + reset buffer
            - is_alarm → decrement in‑flight + reset buffer

        Parameters
        ----------
        parsed : dict
            Parsed machine response produced by CH.Process_Read_Data().
            Expected keys:
                - "is_ack"   : bool
                - "is_error" : bool
                - "is_alarm" : bool
        """
        if parsed.get("is_ack"):
            self.in_flight = max(0, self.in_flight - 1)
            if self.cfg.maxBufferBytes > 0:
                self.buffer_used = max(0, self.buffer_used - 20)

        if parsed.get("is_error") or parsed.get("is_alarm"):
            self.in_flight = max(0, self.in_flight - 1)
            self.buffer_used = 0

    def should_poll_status(self, now: float) -> bool:
        """
        Determine whether it is time to send a status‑polling command.

        Some machines (e.g., GRBL) support auto‑reporting.
        Others require periodic polling (e.g., Marlin, some custom firmwares).

        Parameters
        ----------
        now : float
            Current timestamp.

        Returns
        -------
        bool
            True if a status command should be sent.
        """
        if not self.cfg.statusCommand:
            return False
        return (now - self.last_poll) >= self.cfg.statusRate

    def get_status_command(self) -> str:
        """
        Retrieve the configured status command and update the poll timestamp.

        Returns
        -------
        str
            The status command to send (e.g., '?', 'M114', etc.).
        """
        self.last_poll = time.time()
        return self.cfg.statusCommand

    def is_idle(self) -> bool:
        """
        Check whether all streamed commands have been acknowledged.

        Returns
        -------
        bool
            True if no commands are in flight.
        """
        return self.in_flight == 0

    # def on_response(self, line: str):
    #     l = line.lower()

    #     # OK reduces in‑flight
    #     if "ok" in l:
    #         self.in_flight = max(0, self.in_flight - 1)
    #         if self.cfg.maxBufferBytes > 0:
    #             # approximate release
    #             self.buffer_used = max(0, self.buffer_used - 20)

    #     # Error or alarm resets buffer
    #     if "error" in l or "alarm" in l:
    #         self.in_flight = max(0, self.in_flight - 1)
    #         self.buffer_used = 0


class GCodeStreamer(threading.Thread):
    def __init__(self, transport:QueueDataTransport, 
                 protocol:ProtocolEngine, 
                 killer_event:threading.Event, 
                 stop_event:threading.Event):
        super().__init__(name="GCodeStreamer")

        self.transport    = transport
        self.protocol     = protocol
        self.killer_event = killer_event
        self.stop_event   = stop_event

        self.queue = queue.Queue()
        self.cycle = getattr(self.protocol.cfg, "cycleTime", 0.01)

    def enqueue(self, text: str):
        for raw in text.splitlines():
            line = raw.strip()
            if line and not line.startswith(';'):
                self.queue.put(line)

    def run(self):
        while not self.killer_event.wait(self.cycle):
            now = time.time()

            # 1. Feed machine responses into protocol
            # for resp in self.transport.read_lines():
            #     self.protocol.on_response(resp)
            for parsed in self.transport.read_lines():
                self.protocol.on_feedback(parsed)

            # 2. Status polling
            if self.protocol.should_poll_status(now):
                cmd = self.protocol.get_status_command()
                if cmd:
                    self.transport.write_line(cmd)
                    self.protocol.on_line_sent(cmd)

            # 3. Send next G-code line
            if not self.stop_event.is_set() and not self.queue.empty():
                next_line = self.queue.queue[0]
                if self.protocol.can_send(next_line):
                    self.queue.get()
                    self.transport.write_line(next_line)
                    self.protocol.on_line_sent(next_line)
