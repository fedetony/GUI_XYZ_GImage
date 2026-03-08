
# gimage/plugins/registry.py
class PluginRegistry:
    _plugins = {}

    @classmethod
    def register(cls, plugin_cls):
        cls._plugins[plugin_cls.name] = plugin_cls

    @classmethod
    def get(cls, name):
        if isinstance(name,str):
            return cls._plugins.get(name)
        return None

    @classmethod
    def all(cls):
        return cls._plugins


