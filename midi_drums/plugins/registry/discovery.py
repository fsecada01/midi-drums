"""Auto-discovery of genre/drummer plugin modules for PluginRegistry."""

from __future__ import annotations

import importlib
import logging
import pkgutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from midi_drums.plugins.interfaces.drummer_plugin import DrummerPlugin
from midi_drums.plugins.interfaces.genre_plugin import GenrePlugin

if TYPE_CHECKING:
    from midi_drums.plugins.registry.plugin_registry import PluginRegistry

logger = logging.getLogger(__name__)

# Built-in plugin directories are real subpackages of midi_drums.plugins.
# drummers/composite/ is listed explicitly alongside genres/ and drummers/
# because pkgutil.iter_modules() doesn't recurse into subpackages - without
# this, composite drummers would silently drop out of auto-discovery.
_PLUGINS_PACKAGE = "midi_drums.plugins"
_PLUGINS_ROOT = Path(__file__).resolve().parent.parent


class PluginDiscovery:
    """Scans plugin directories and registers discovered plugin classes."""

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    def discover(self, plugin_dirs: list[Path] | None = None) -> None:
        """Auto-discover and load plugins from specified directories.

        Args:
            plugin_dirs: List of directories to search. If None, searches
                default locations.
        """
        if plugin_dirs is None:
            plugin_dirs = [
                _PLUGINS_ROOT / "genres",
                _PLUGINS_ROOT / "drummers",
                _PLUGINS_ROOT / "drummers" / "composite",
            ]

        for plugin_dir in plugin_dirs:
            if plugin_dir.exists() and plugin_dir.is_dir():
                self._load_plugins_from_directory(plugin_dir)

    def _load_plugins_from_directory(self, plugin_dir: Path) -> None:
        """Load plugins from a specific directory."""
        logger.info(f"Loading plugins from: {plugin_dir}")

        try:
            package_name = self._module_package_name(plugin_dir)
            for _finder, name, _ispkg in pkgutil.iter_modules(
                [str(plugin_dir)]
            ):
                try:
                    module_name = f"{package_name}.{name}"
                    module = importlib.import_module(module_name)
                    self._register_plugins_from_module(module)
                except Exception as e:
                    logger.error(f"Failed to load plugin module {name}: {e}")
        except Exception as e:
            logger.error(f"Failed to load plugins from {plugin_dir}: {e}")

    @staticmethod
    def _module_package_name(plugin_dir: Path) -> str:
        """Resolve the dotted package name to import plugin_dir's modules
        under.

        Built-in directories (genres/, drummers/, drummers/composite/) are
        real subpackages of midi_drums.plugins, already imported elsewhere
        under their real fully-qualified path (their __init__.py files
        import the plugin classes directly, or - for composite/ - are
        empty). Importing them again here under a bare top-level alias
        would give the same file two separate module identities, and
        every plugin class in it would get registered twice - once per
        identity. So built-in directories are imported by that same
        fully-qualified path.

        Arbitrary external plugin directories (a documented use case via
        discover_plugins(plugin_dirs=...)) aren't part of any package and
        have no dotted path of their own, so for those we fall back to
        aliasing them onto sys.path as a new top-level package - safe
        here since nothing else imports them by a competing name.
        """
        try:
            plugin_dir.relative_to(_PLUGINS_ROOT)
        except ValueError:
            if str(plugin_dir.parent) not in sys.path:
                sys.path.insert(0, str(plugin_dir.parent))
            return plugin_dir.name

        relative_parts = plugin_dir.relative_to(_PLUGINS_ROOT).parts
        return ".".join((_PLUGINS_PACKAGE, *relative_parts))

    def _register_plugins_from_module(self, module) -> None:
        """Register all plugin classes found in a module."""
        seen: set[type] = set()
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, (GenrePlugin, DrummerPlugin))
                and attr not in (GenrePlugin, DrummerPlugin)
                # Only classes defined here, not ones imported for
                # internal use (e.g. composite plugins importing their
                # component plugins) or bound to a second name (e.g. a
                # "FooRefactored = Foo" backward-compat alias).
                and attr.__module__ == module.__name__
                and attr not in seen
            ):
                seen.add(attr)
                try:
                    plugin_instance = attr()
                    if isinstance(plugin_instance, GenrePlugin):
                        self.registry.register_genre_plugin(plugin_instance)
                    elif isinstance(plugin_instance, DrummerPlugin):
                        self.registry.register_drummer_plugin(plugin_instance)
                except Exception as e:
                    logger.error(
                        f"Failed to instantiate plugin {attr_name}: {e}"
                    )
