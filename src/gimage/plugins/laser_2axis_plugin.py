# plugins/machines/laser_2axis.py

from gimage.plugins.plugin_machine_base import GImageMachineBase

class Laser2AxisMachine(GImageMachineBase):
    """
    A simple 2-axis laser engraver (e.g., GRBL-based).
    Handles movement, homing, units, feedrate, etc.
    """
    name = "laser_2axis" #must match the name in the machine combo

        
        

    def set_units(self):
        self.units = self.config.get_value(["machine", "units"], default="mm")
        if self.units == "mm":
            return "G21"  # millimeters
        return "G20"      # inches

    def home(self):
        return "$H"  # GRBL homing

    def move_to(self, x, y, f, rapid=False):
        self.feedrate = f
        if rapid:
            return f"G0 X{x:.3f} Y{y:.3f}"
        return f"G1 X{x:.3f} Y{y:.3f} F{self.feedrate}"

    def dwell(self, ms):
        return f"G4 P{ms}"

    def comment(self, text):
        return f"; {text}"
