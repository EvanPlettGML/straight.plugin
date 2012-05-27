"""Facility to load plugins."""

import sys
import os

from importlib import import_module
from imp import find_module


class Loader(object):

    def __init__(self, *args, **kwargs):
        self._cache = []

    def load(self, *args, **kwargs):
        self._fill_cache(*args, **kwargs)
        self._post_fill()
        self._order()
        return self._cache

    def _meta(self, plugin):
        meta = getattr(plugin, '__plugin__', None)
        return meta

    def _post_fill(self):
        for plugin in self._cache:
            meta = self._meta(plugin)
            if not getattr(meta, 'load', True):
                self._cache.remove(plugin)
            for implied_namespace in getattr(meta, 'imply_plugins', []):
                plugins = self._cache
                self._cache = self.load(implied_namespace)
                self._post_fill()
                self._cache = plugins + self._cache

    def _order(self):
        self._cache.sort(key=self._plugin_priority, reverse=True)

    def _plugin_priority(self, plugin):
        meta = self._meta(plugin)
        return getattr(meta, 'priority', 0.0)


class ModuleLoader(Loader):
    """Performs the work of locating and loading straight plugins.
    
    This looks for plugins in every location in the import path.
    """

    def _isPackage(self, path):
        pkg_init = os.path.join(path, '__init__.py')
        if os.path.exists(pkg_init):
            return True

        return False

    def _findPluginFilePaths(self, namespace):
        already_seen = set()

        # Look in each location in the path
        for path in sys.path:

            # Within this, we want to look for a package for the namespace
            namespace_rel_path = namespace.replace(".", os.path.sep)
            namespace_path = os.path.join(path, namespace_rel_path)
            if os.path.exists(namespace_path):
                for possible in os.listdir(namespace_path):

                    poss_path = os.path.join(namespace_path, possible)
                    if os.path.isdir(poss_path):
                        if not self._isPackage(poss_path):
                            continue
                        base = possible
                    else:
                        base, ext = os.path.splitext(possible)
                        if base == '__init__' or ext != '.py':
                            continue
                    
                    if base not in already_seen:
                        already_seen.add(base)
                        yield os.path.join(namespace, possible)

    def _findPluginModules(self, namespace):
        for filepath in self._findPluginFilePaths(namespace):
            path_segments = list(filepath.split(os.path.sep))
            path_segments = [p for p in path_segments if p]
            path_segments[-1] = os.path.splitext(path_segments[-1])[0]
            import_path = '.'.join(path_segments)

            try:
                module = import_module(import_path)
            except ImportError:
                #raise Exception(import_path)

                module = None

            if module is not None:
                yield module

    def _fill_cache(self, namespace):
        """Load all modules found in a namespace"""

        modules = self._findPluginModules(namespace)

        self._cache = list(modules)


class ObjectLoader(Loader):
    """Loads classes or objects out of modules in a namespace, based on a
    provided criteria.
   
    The load() method returns all objects exported by the module.
    """

    def __init__(self):
        self.module_loader = ModuleLoader()

    def _fill_cache(self, namespace):
        modules = self.module_loader.load(namespace)
        objects = []

        for module in modules:
            for attr_name in dir(module):
                if not attr_name.startswith('_'):
                    objects.append(getattr(module, attr_name))
        
        self._cache = objects
        return objects


class ClassLoader(ObjectLoader):

    def _fill_cache(self, namespace, subclasses=None):
        objects = super(ClassLoader, self)._fill_cache(namespace)
        classes = []
        for cls in objects:
            if isinstance(cls, type):
                if subclasses is None:
                    classes.append(cls)
                elif issubclass(cls, subclasses) and cls is not subclasses:
                    classes.append(cls)

        self._cache = classes
        return classes


def unified_load(namespace, subclasses=None):

    if subclasses is not None:
        return ClassLoader().load(namespace, subclasses=subclasses)
    else:
        return ModuleLoader().load(namespace)

