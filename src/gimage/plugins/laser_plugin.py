# plugins/tools/laser.py

from gimage.plugins.plugin_tool_base import GImageToolBase

class LaserTool(GImageToolBase):
    """
    Laser tool plugin.
    Converts abstract tool actions into laser-specific actions.
    """
    name="laser" #must match the name in the tool_type combo

    def set_init_config(self):
        pass

    def down(self, power=255):
        """
        Turn laser ON at given power.
        Returns an abstract action for Command_Handler.
        """
        return {
            "action": "laserspindleCWON",
            "parameters": {"S": int(power)}
        }

    def up(self):
        """
        Turn laser OFF.
        """
        return {
            "action": "laserspindleCWOFF",
            "parameters": {}
        }
