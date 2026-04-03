import threading
import logging
import os
from queue import Queue
from PIL import Image
import json
import tempfile
from class_CH import Command_Handler

# Add logger
ggg_fun_name="GImageGcodeGenerator"
from class_LogHandler import get_appPath, LM ,init_logger_manager
try:
    log = LM.get_logger_with_handler(ggg_fun_name,
                                     "debug",
                                     False, # Blocks GUI if true
                                     "%(asctime)s [%(levelname)s] (%(name)s) %(message)s")
    log.info(f"{ggg_fun_name} Logger started")
except (AttributeError, ImportError):
    LM = init_logger_manager(None)
    log = LM.get_logger(__name__)
    log.info("GImage Gcode Generator Thread Logger initialized...")

gimage_path = os.path.join(get_appPath(),"gimage")
gimage_plugins_path = os.path.join(gimage_path,"plugins")

# gimage/plugins/loader.py
import importlib.util
import inspect
PROCESS_QUEUE_SIZE=5000

from gimage.plugins.loader import load_plugins_from_path
from gimage.plugins.registry import PluginRegistry 
from class_ST import SignalTracker
from class_struct_tracker import TreeStructTracker

class GImagePluginHandler(threading.Thread):
    def __init__(self, 
                 image:Image.Image, 
                 config_dict:dict, 
                 command_handler:Command_Handler, 
                 killer_event:threading.Event,
                 signal_tracker:SignalTracker,
                 progress_callback=None, 
                 status_callback=None):
        super().__init__()
        self.st = signal_tracker
        self.log = log
        self.image = image                  
        self.config = config_dict   # contains technique, process info, interface, etc.
        self.ch = command_handler           
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.struct_tracker =TreeStructTracker(self.config)

        self.actions_queue = Queue()        # queue of action dicts
        self.killer_event = killer_event
        self._stop_event = threading.Event()
        # Load all plugins once
        load_plugins_from_path(gimage_plugins_path)
        self.registered_plugins=list(PluginRegistry.all().keys())
        self.log.info(f"Loaded plugins: {self.registered_plugins}")
        self.line_number=0
        self.processed_lines=0

    def stop(self):
        self._stop_event.set()

    def emit_progress(self, percent, stats=None):
        self.st.GImage_Progress(percent, stats)
        # if self.progress_callback:
        #     self.progress_callback(percent, stats or {})

    def emit_status(self, msg):
        self.st.GImage_Status(msg)
        # if self.status_callback:
        #     self.status_callback(msg)

    def run(self):
        """
        Main execution entry point for the GImageGcodeGenerator thread.

        Responsibilities:
        • Read the selected technique, machine, and tool types from the
            configuration tree (TreeStructTracker).
        • Retrieve the corresponding plugin classes from the PluginRegistry.
        • Instantiate machine and tool plugins, passing the Command_Handler
            so they can query interface actions and parameters.
        • Instantiate the technique plugin, injecting all required context
            (image, config, machine, tool, callbacks, cancellation flags).
        • Execute the technique plugin's process() method, which emits
            abstract actions via emit_action() → put_and_process().
        • After the technique completes, flush any remaining queued actions
            by calling process_queue(), which converts actions to G‑code and
            streams them to temporary files.
        • Emit final status and progress updates.

        This method forms the high‑level orchestration layer: plugins generate
        abstract actions, the queue batches them, and process_queue() performs
        the actual G‑code translation. Exceptions are caught and logged to
        prevent thread crashes.
        """
        try:
            self.log.info("GImageGcodeGenerator started")
            self.emit_status("Starting image processing")

            # Resolve plugin names from configuration
            technique_name = self.struct_tracker.get_value(["technique", "technique_type", "value"])
            machine_type   = self.struct_tracker.get_value(["machine", "machine_type", "value"])
            tool_type      = self.struct_tracker.get_value(["tool", "tool_type", "value"])

            ##############################
            ##############################
            # To be removed
            # Not connected yet interface and machine selection within Gimage
            self.ch.set_id("4") # Grbl 1.1k-ORTUR 
            ##############################
            ##############################
            self.status_tracker={}
            # Retrieve plugin classes
            plugin_cls  = PluginRegistry.get(technique_name)
            machine_cls = PluginRegistry.get(machine_type)
            tool_cls    = PluginRegistry.get(tool_type)

            # Instantiate machine and tool plugins
            machine = machine_cls(ch=self.ch, config=self.struct_tracker,status=self.status_tracker)
            tool    = tool_cls(ch=self.ch, config=self.struct_tracker,status=self.status_tracker)

            # Validate technique plugin
            if plugin_cls is None:
                self.log.error(f"Technique '{technique_name}' not found")
                self.log.info(f"Available Plugins: {self.registered_plugins}")
                self.emit_status(f"Technique '{technique_name}' not found")
                return

            # Instantiate technique plugin
            plugin = plugin_cls(
                image=self.image,
                config=self.struct_tracker,
                ch=self.ch,
                machine=machine,
                tool=tool,
                emit_action=self.put_and_process,
                emit_progress=self.emit_progress,
                emit_status=self.emit_status,
                killer_event=self.killer_event,
                stop_event=self._stop_event,
                status=self.status_tracker,
            )
            # Prepare the temp files
            self.prepare_temp_files()

            # Execute technique → fills queue incrementally
            plugin.process()

            # Final flush of remaining actions
            self.process_queue()

            # Final UI updates
            self.emit_status("Finished")
            self.log.info(f"Actions dumped to: {self.actions_path}")
            self.log.info(f"G-code dumped to: {self.gcode_path}")
            self.emit_progress(100, {"lines_total": self.line_number})

        except Exception as e:
            self.log.exception(f"Error in GImageGcodeGenerator: {e}")
            self.emit_status(f"Error: {e}")

    def prepare_temp_files(self):
        """
        Initialize temporary output files for action logging (JSONL) and
        G‑code output. This method creates or overwrites the files, writes
        a small header entry to both, and prepares them for incremental
        appending by process_queue().

        Files created:
        • gimage_actions.jsonl — one JSON object per action
        • gimage_output.gcode — generated G‑code lines

        These files are opened in write mode ('w') to start fresh for each
        job. Subsequent writes during queue processing use append mode ('a').
        """
        # Prepare temp file paths
        self.actions_path = os.path.join(tempfile.gettempdir(), "gimage_actions.jsonl")
        self.gcode_path   = os.path.join(tempfile.gettempdir(), "gimage_output.gcode")

        self.log.info(f"Dumping actions to: {self.actions_path}")
        self.log.info(f"Dumping G-code to: {self.gcode_path}")

        # Open files in write mode to start clean
        with open(self.actions_path, "w", encoding="utf-8") as actions_file, \
            open(self.gcode_path,   "w", encoding="utf-8") as gcode_file:

            # Header message
            msg = "Made with coffee and love"
            action = {"action": "Message", "parameters": {"msg": msg}, "linenumber": 0}

            # Write header action to JSONL
            actions_file.write(json.dumps(action) + "\n")

            # Convert header action to G‑code
            gcode_line, parameters_ok = self.ch.Get_Gcode_for_Action(
                action["action"],
                action["parameters"]
            )

            # Write header G‑code if valid
            if gcode_line and parameters_ok:
                gcode_file.write(gcode_line + "\n")

    def process_queue(self):
        """
        Process all pending abstract actions from the internal queue, translate them
        into firmware‑specific G‑code using the Command_Handler, and stream both the
        raw actions and generated G‑code to temporary files.

        This method performs the following steps:
        • Dequeues actions emitted by technique/machine/tool plugins.
        • Validates each action against the active interface's supported actions.
        • Assigns a global line number to each action for traceability.
        • Writes each action as a JSON line (JSONL) to a temporary debug file.
        • Converts valid actions into G‑code via Command_Handler.
        • Streams generated G‑code line‑by‑line to a temporary .gcode file.
        • Accumulates G‑code in memory for final output (self.result_gcode).

        The design supports extremely large toolpaths by avoiding full in‑memory
        storage of intermediate action lists. Only the final G‑code string is kept
        in memory, while all intermediate data is streamed to disk.

        Temporary output files:
        • gimage_actions.jsonl — one JSON object per action (debug/inspection)
        • gimage_output.gcode — generated G‑code in execution order

        This function respects cancellation flags (killer_event, stop_event) and
        exits early if processing is interrupted.
        """

        total_actions = self.actions_queue.qsize()
        processed = 0

        available_actions = self.ch.getListofActions()

        def has_action(action):
            return action in available_actions

        gcode_lines = []

        # Open files in append mode for streaming
        with open(self.actions_path, "a", encoding="utf-8") as actions_file, \
            open(self.gcode_path,   "a", encoding="utf-8") as gcode_file:

            while not self.actions_queue.empty() and (not self.killer_event.is_set() or not self._stop_event.is_set()):

                action = self.actions_queue.get()
                processed += 1
                self.line_number += 1
                action["linenumber"] = self.line_number

                # Validate action
                if not has_action(action["action"]):
                    if action["action"]:
                        msg = f"Missing action: {action['action']} [{action['parameters']}]"
                        self.log.warning(msg)
                        action = {"action": "Message", "parameters": {"msg": msg}, "linenumber": self.line_number}

                # Write action to JSONL
                actions_file.write(json.dumps(action) + "\n")

                # Convert to G-code
                gcode_line, parameters_ok = self.ch.Get_Gcode_for_Action(
                    action["action"],
                    action["parameters"]
                )

                if gcode_line and parameters_ok:
                    gcode_file.write(gcode_line + "\n")
                    gcode_lines.append(gcode_line)

                # Emit progress (0–99)
                if total_actions > 0:
                    percent = int((processed / total_actions) * 99)
                    self.emit_progress(percent, {"lines_total": self.line_number})

        # Store final G-code in memory
        self.result_gcode = "\n".join(gcode_lines)
        self.processed_lines += total_actions
        self.log.info(f"Finished processing a {total_actions} elements queue -> Processed {self.processed_lines}")

    def put_and_process(self, item, block: bool = True, timeout: float | None = None) -> None:
        """
        Enqueue one or more abstract action dictionaries produced by technique,
        machine, or tool plugins. Supports both single actions (dict) and batches
        (list of dicts). This method is also responsible for triggering incremental
        queue processing when the queue grows beyond a configured threshold.

        Behavior:
        • Returns immediately if a cancellation event is active.
        • Accepts either a single action dict or a list of action dicts.
        • Pushes actions into the internal queue in the order received.
        • If the queue size exceeds PROCESS_QUEUE_SIZE, the queue is partially
            flushed by calling process_queue(), which streams actions and G‑code
            to temporary files and frees memory.

        This design allows extremely large toolpaths to be generated without
        exhausting RAM, since actions are processed in chunks rather than all
        at once.
        """

        # Stop immediately if cancellation was requested
        if self.killer_event.is_set() or self._stop_event.is_set():
            return

        # Enqueue actions
        if isinstance(item, dict):
            self.actions_queue.put(item, block, timeout)

        elif isinstance(item, list):
            # Avoid partial enqueueing if cancellation happens mid‑list
            if self.killer_event.is_set() or self._stop_event.is_set():
                return
            for iii in item:
                self.actions_queue.put(iii, block, timeout)

        # Trigger partial processing if queue grows too large
        if self.actions_queue.qsize() > PROCESS_QUEUE_SIZE:
            self.process_queue()

        

