from class_struct_tracker import TreeStructTracker
from class_CH import Command_Handler

class GImageToolBase:
    def __init__(self,  
                 config:TreeStructTracker, 
                 ch:Command_Handler,
                 status:dict,
                 ):
        self.ch=ch
        self.config=config
        self.set_init_config()
        self.status=status
    
    def set_exit_config(self):
        return None

    def set_init_config(self):
        pass

    def down(self, **kwargs):
        raise NotImplementedError

    def up(self, **kwargs):
        raise NotImplementedError
    
    def status_update(self,**kwargs):
        pass

    