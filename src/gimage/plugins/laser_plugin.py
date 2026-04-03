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

    def down(self, **kwargs):
        """
        Turn laser ON at given power.
        Returns an abstract action for Command_Handler.
        """
        power = kwargs.get("power", 0)

        # Correct: tool is DOWN → is_up=False
        self.status_update(is_up=False, power=power)

        return {
            "action": "laserspindleCWON",
            "parameters": {"S": int(power)}
        }

    def up(self, **kwargs):
        """
        Turn laser OFF.
        """
        # Correct: tool is UP → is_up=True
        self.status_update(is_up=True, power=0)

        return {
            "action": "laserspindleCWOFF",
            "parameters": {}
        }