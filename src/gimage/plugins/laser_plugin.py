# plugins/tools/laser.py

from gimage.plugins.plugin_tool_base import GImageToolBase

class LaserTool(GImageToolBase):
    """
    Laser tool plugin.
    Converts abstract tool actions into laser-specific actions.
    """
    name="laser" #must match the name in the tool_type combo

    def _set_configuration_values(self):
        self.max_power = self.config.get_value(["tool", "max_power","value"], default=255)
        self.min_power = self.config.get_value(["tool", "min_power","value"], default=0)

    def down(self, power=255):
        """
        Turn laser ON at given power.
        Returns an abstract action for Command_Handler.
        """
        power = max(self.min_power, min(power, self.max_power))
        return {
            "action": "laser_on",
            "parameters": {"power": power}
        }

    def up(self):
        """
        Turn laser OFF.
        """
        return {
            "action": "laser_off",
            "parameters": {}
        }
