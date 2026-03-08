import threading
import logging
from class_CH import Command_Handler
import os
from queue import Queue
from PIL import Image

# Add logger
ggg_fun_name="GImageGcodeGenerator"
from class_LogHandler import get_appPath, LM ,init_logger_manager
try:
    log = LM.get_logger_with_handler(ggg_fun_name,
                                     "debug",
                                     True,
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
import os


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
        try:
            self.log.info("GImageGcodeGenerator started")
            self.emit_status("Starting image processing")
            technique_name = self.struct_tracker.get_value(["technique","technique_type","value"])
            plugin_cls = PluginRegistry.get(technique_name)
            if plugin_cls is None:
                self.log.error(f"Technique '{technique_name}' not found")
                self.log.info(f"Available Pluggins: {self.registered_plugins}")
                self.emit_status(f"Technique '{technique_name}' not found")
                return

            plugin = plugin_cls(
                                image=self.image,
                                config=self.struct_tracker,   
                                ch=self.ch,                             
                                emit_action=self.actions_queue.put,
                                emit_progress=self.emit_progress,
                                emit_status=self.emit_status,
                                killer_event=self.killer_event,
                                stop_event=self._stop_event
                                )


            plugin.process()  # fills actions_queue

            # Now convert actions to G-code using CommandHandler
            gcode_lines = []
            line_number = 0
            available_actions=self.ch.getListofActions()
            def has_action(action):
                return action in available_actions
            while not self.actions_queue.empty() and (not self.killer_event.is_set() or not self._stop_event.is_set()):
                action = self.actions_queue.get()
                line_number += 1
                action["linenumber"] = line_number
                if not has_action(action["action"]):
                    if action["action"]:
                        self.log.warning(f"Unknown action: {action['action']}")
                    continue
                gcode_line, parameters_ok = self.ch.Get_Gcode_for_Action(action["action"],action["parameters"])
                if gcode_line is not None and parameters_ok:
                    gcode_lines.append(gcode_line)

            self.result_gcode = "\n".join(gcode_lines)
            self.emit_status("Finished")
            self.emit_progress(100, {"lines_total": line_number})

        except Exception as e:
            self.log.exception("Error in GImageGcodeGenerator")
            self.emit_status(f"Error: {e}")

