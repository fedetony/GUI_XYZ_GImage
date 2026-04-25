# plugins/tools/pen_plugin.py

from gimage.plugins.plugin_tool_base import GImageToolBase

class PenTool(GImageToolBase):
    """
    Pen tool plugin.
    Converts abstract tool actions into laser-specific actions.
    """
    name="pen" #must match the name in the tool_type combo

    def set_init_config(self):
        self.touch_pos = self.config.get_value(["tool","touch_z","value"])
        self.retract_pos = self.config.get_value(["tool","retract_z","value"]) 
        self.touch_speed = self.config.get_value(["tool","touch_speed","value"]) or -1
        self.retract_speed = self.config.get_value(["tool","retract_speed","value"]) or -1
        self.touch_axis='Z'
        if self.touch_pos is None:
            self.touch_pos = 0
        if self.retract_pos is None:
            self.retract_pos = self.touch_pos + 3
    
    def _go_to_touch_position(self,z=None):
        if self.touch_speed == 0:
            return {"action": "Comment", "parameters": {"msg":"Touch is Off"}}  
        rapid = (self.touch_speed < 0)  
        action = "rapidMove" if rapid else "linearMove"
        z_pos=z if z is not None else self.touch_pos
        if rapid:
            params = {self.touch_axis: z_pos}
        else:
            params = {self.touch_axis: z_pos, "F": self.touch_speed}
        return {"action": action, "parameters": params}
    
    def _go_to_retract_position(self,z=None):
        if self.retract_speed == 0:
            return {"action": "Comment", "parameters": {"msg":"Retract is Off"}}  
        rapid = (self.retract_speed < 0)  
        action = "rapidMove" if rapid else "linearMove"
        z_pos=z if z is not None else self.retract_pos
        if rapid:
            params = {self.touch_axis: z_pos}
        else:
            params = {self.touch_axis: z_pos, "F": self.retract_speed}
        return {"action": action, "parameters": params}


    def down(self, **kwargs):
        """
        Moves head to position.
        Returns an abstract action for Command_Handler.
        """
        axis=self.touch_axis.lower()
        z = kwargs.get(self.touch_axis.lower())
        # tool is DOWN → is_up=False
        
        if axis == 'z':
            self.status_update(is_up=False, z=z)
        elif axis == 'x':
            self.status_update(is_up=False, x=z)
        elif axis == 'y':
            self.status_update(is_up=False, y=z)
        elif axis == 'a':
            self.status_update(is_up=False, a=z)    
        else:
            self.status_update(is_up=False)

        return self._go_to_touch_position(z)

    def up(self, **kwargs):
        """
        Moves head to position.
        Returns an abstract action for Command_Handler.
        """
        axis=self.touch_axis.lower()
        z = kwargs.get(self.touch_axis.lower())
        # tool is DOWN → is_up=False
        
        if axis == 'z':
            self.status_update(is_up=False, z=z)
        elif axis == 'x':
            self.status_update(is_up=False, x=z)
        elif axis == 'y':
            self.status_update(is_up=False, y=z)
        elif axis == 'a':
            self.status_update(is_up=False, a=z)    
        else:
            self.status_update(is_up=False)

        return self._go_to_retract_position(z)