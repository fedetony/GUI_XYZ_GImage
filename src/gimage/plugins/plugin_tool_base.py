from class_struct_tracker import TreeStructTracker
from class_CH import Command_Handler

class GImageToolBase:
    def __init__(self,  
                 config:TreeStructTracker, 
                 ch:Command_Handler,
                 ):
        self.ch=ch
        self.config=config

    def down(self, **kwargs):
        raise NotImplementedError

    def up(self):
        raise NotImplementedError
