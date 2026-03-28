import threading
from class_struct_tracker import TreeStructTracker
from PIL import Image
from class_CH import Command_Handler

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
                 stop_event:threading.Event):
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

    def should_stop(self):
        return self.killer_event.is_set() or self.stop_event.is_set()

    def check_stop(self):
        if self.should_stop():
            self.emit_status("Cancelled")
            raise StopIteration

    def process(self):
        raise NotImplementedError
