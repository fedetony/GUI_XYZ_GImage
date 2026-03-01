
# gimage/plugins/registry.py
class PluginRegistry:
    _plugins = {}

    @classmethod
    def register(cls, plugin_cls):
        cls._plugins[plugin_cls.name] = plugin_cls

    @classmethod
    def get(cls, name):
        return cls._plugins.get(name)

    @classmethod
    def all(cls):
        return cls._plugins


