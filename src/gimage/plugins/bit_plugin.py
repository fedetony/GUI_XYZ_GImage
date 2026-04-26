# plugins/tools/pen_plugin.py

from gimage.plugins.plugin_tool_base import GImageToolBase

class BitTool(GImageToolBase):
    """
    Bit tool plugin. For CNC with spindle.
    Converts abstract tool actions into cnc-specific actions.
    """
    name="bit" #must match the name in the tool_type combo

    def set_init_config(self):
        self.touch_pos = self.config.get_value(["tool","touch_z","value"])
        self.retract_pos = self.config.get_value(["tool","retract_z","value"]) 
        self.touch_speed = self.config.get_value(["tool","touch_speed","value"]) or -1
        self.retract_speed = self.config.get_value(["tool","retract_speed","value"]) or -1
        self.spindle_dwell_time_ms = self.config.get_value(["tool","spindle_dwell_time_ms","value"]) or 3333
        self.spindle_direction = self.config.get_value(["tool","spindle_direction","value"]) or "CW"
        self.min_power, self.max_power = self.config.get_value(["technique","power_range","value"])
        feedrange = self.config.get_value(["technique","feedrate_range","value"])
        self.feedrate = self.config.get_value(["technique","rate","value"])
        if feedrange:
            self.min_rate,self.max_rate=feedrange
        else:
            self.min_rate,self.max_rate=(self.feedrate,self.feedrate)
        # Do not allow rapid touch movements
        if self.touch_speed<=0:
            self.touch_speed=self.feedrate
        self.touch_axis='Z'
        if self.touch_pos is None:
            self.touch_pos = 0
        if self.retract_pos is None:
            self.retract_pos = self.touch_pos + 3
        self.is_spindle_on=False
    
    def set_exit_config(self):
        cmds=self.turn_spindle_off()
        return cmds
    
    def turn_spindle_on(self):
        if self.is_spindle_on:
            return []
        power = self.max_power

        # Correct: tool is DOWN → is_up=False
        self.status_update(power=power)
        self.is_spindle_on = True
        cmd_list=[{
            "action": f"laserspindle{self.spindle_direction}ON",
            "parameters": {"S": int(power)}
        },self.dwell(self.spindle_dwell_time_ms)]
        return cmd_list
    
    def dwell(self, ms):
        params=self.ch.Get_Parameters_Needed_for_action('dwell',self.ch.id)
        param_dict={}
        for par,req in params.items(): # can be P or S
            if req == 'required':
                param_dict={par:ms}
        return {"action": 'dwell', "parameters": param_dict}
    
    def turn_spindle_off(self):
        if not self.is_spindle_on:
            return []
        power = 0 # self.min_power

        # Correct: tool is DOWN → is_up=False
        self.status_update(power=power)
        self.is_spindle_off = False
        
        cmd_list=[{
            "action": f"laserspindle{self.spindle_direction}OFF",
            "parameters": {}
            },self.dwell(self.spindle_dwell_time_ms)]
        return cmd_list

    
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
        cmd_list= self.turn_spindle_on()
        cmd_list.append({"action": action, "parameters": params})
        return cmd_list
    
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