from class_struct_tracker import TreeStructTracker
from class_CH import Command_Handler

class GImageMachineBase:
    def __init__(self,  
                 config:TreeStructTracker, 
                 ch:Command_Handler,
                 ):
        self.ch=ch
        self.config=config
        self.available_actions=self.ch.getListofActions()
        self.available_parameters=self.ch.Get_list_of_all_parameters_in_interface(self.ch.id)
        

    def move_to(self, x, y, rapid=False):
        raise NotImplementedError

    def set_units(self):
        raise NotImplementedError

    def home(self):
        raise NotImplementedError

    def move(self, rapid=False, **kwargs):
        """
        Create a semantic movement action.
        The Command_Handler validates and formats it.
        """
        action = "rapidMove" if rapid else "linearMove"
        params = {k: v for k, v in kwargs.items() if v is not None}
        return {"action": action, "parameters": params}
    
    def coordset(self, **kwargs):
        """
        Create a semantic coordinates axis/power/extruder action.
        """
        action = "coordSet"
        params = {k: v for k, v in kwargs.items() if v is not None}
        return {"action": action, "parameters": params}
    
    def a_set(self,action, **kwargs):
        """
        Create a semantic action dictionary for the action. 
        Example: a_set('linearMove', X=10, Y=20, S=200) will return:
        {"action": "linearMove", "parameters": {"X": 10, "Y": 20, "S": 200}}
        """
        params = {k: v for k, v in kwargs.items() if v is not None}
        return {"action": action, "parameters": params}

    def set_position(self, **kwargs):
        return {"action": "setPosition", "parameters": kwargs}

    def home(self):
        return {"action": "Home", "parameters": {}}