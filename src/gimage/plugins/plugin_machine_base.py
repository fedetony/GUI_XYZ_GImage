from class_struct_tracker import TreeStructTracker
from class_CH import Command_Handler

class GImageMachineBase:
    def __init__(self,  
                 config:TreeStructTracker, 
                 ch:Command_Handler,
                 status:dict,
                 ):
        self.ch=ch
        self.config=config
        self.available_actions=self.ch.getListofActions()
        self.available_parameters=self.ch.Get_list_of_all_parameters_in_interface(self.ch.id)
        self.status=status
        

    def move_to(self, x, y, rapid=False):
        raise NotImplementedError

    def set_units(self):
        raise NotImplementedError
    
    def status_update(self,**kwargs):
        "placeholder the function is set in plugin_base"
        pass

    def move(self, rapid=False, **kwargs):
        """
        Create a semantic movement action.
        The Command_Handler validates and formats it.
        """
        # Update live state BEFORE building the action
        self.status_update(rapid=rapid, **kwargs)

        action = "rapidMove" if rapid else "linearMove"
        params = {k: v for k, v in kwargs.items() if v is not None}
        return {"action": action, "parameters": params}


    def coordset(self, **kwargs):
        """
        Create a semantic coordinates axis/power/extruder action.
        """
        # Update state with all provided parameters
        self.status_update(**kwargs)
        action = "coordSet"
        params = {k: v for k, v in kwargs.items() if v is not None}

        return {"action": action, "parameters": params}


    def a_set(self, action, **kwargs):
        """
        Create a semantic action dictionary for the action.
        Example:
            a_set('linearMove', X=10, Y=20, S=200)
            -> {"action": "linearMove", "parameters": {"X": 10, "Y": 20, "S": 200}}
        """
        # Update state depending on the action type
        if action == "rapidMove":
            self.status_update(rapid=True, **kwargs)
        elif action == "linearMove":
            self.status_update(rapid=False, **kwargs)
        else:
            self.status_update(**kwargs)
        params = {k: v for k, v in kwargs.items() if v is not None}

        return {"action": action, "parameters": params}

    def set_position(self, **kwargs):
        """
        Directly set machine position (used for homing, resets, etc.)
        Does NOT compute distances — it is a hard override.
        """
        pos = self.status["position"]
        # Update position dictionary directly
        for axis, val in kwargs.items():
            pos[axis] = val

        return {"action": "setPosition", "parameters": kwargs}

    def home(self):
        return {"action": "Home", "parameters": {}}