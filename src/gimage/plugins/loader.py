# gimage/plugins/loader.py
import importlib.util
import inspect
import os

from .plugin_base import GImageTechniqueBase
from .plugin_machine_base import GImageMachineBase
from .plugin_tool_base import GImageToolBase
from .registry import PluginRegistry

def load_plugins_from_path(path):
    for filename in os.listdir(path):
        if not filename.endswith(".py"):
            continue
        if filename.startswith("_"):
            continue
        if not filename.endswith("_plugin.py"):
            continue

        module_path = os.path.join(path, filename)
        module_name = f"gimage.plugins.{filename[:-3]}"

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # scan for plugin classes
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, GImageTechniqueBase) and obj is not GImageTechniqueBase:
                PluginRegistry.register(obj)
            elif issubclass(obj, GImageMachineBase) and obj is not GImageMachineBase:
                PluginRegistry.register(obj)
            elif issubclass(obj, GImageToolBase) and obj is not GImageToolBase:
                PluginRegistry.register(obj)
