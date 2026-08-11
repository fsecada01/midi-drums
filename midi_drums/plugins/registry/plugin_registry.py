"""Plugin registry and manager - storage, lookup, and orchestration."""

from __future__ import annotations

import logging
from pathlib import Path

from midi_drums.core.models.pattern import Pattern
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)
from midi_drums.plugins.interfaces.drummer_plugin import DrummerPlugin
from midi_drums.plugins.interfaces.genre_plugin import GenrePlugin
from midi_drums.plugins.registry.discovery import PluginDiscovery

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing genre and drummer plugins."""

    def __init__(self):
        self._genre_plugins: dict[str, GenrePlugin] = {}
        self._drummer_plugins: dict[str, DrummerPlugin] = {}

    def register_genre_plugin(self, plugin: GenrePlugin) -> None:
        """Register a genre plugin."""
        genre_name = plugin.genre_name.lower()
        if genre_name in self._genre_plugins:
            logger.warning(
                f"Overriding existing genre plugin for '{genre_name}'"
            )
        self._genre_plugins[genre_name] = plugin
        logger.info(f"Registered genre plugin: {genre_name}")

    def register_drummer_plugin(self, plugin: DrummerPlugin) -> None:
        """Register a drummer plugin."""
        drummer_name = plugin.drummer_name.lower()
        if drummer_name in self._drummer_plugins:
            logger.warning(
                f"Overriding existing drummer plugin for '{drummer_name}'"
            )
        self._drummer_plugins[drummer_name] = plugin
        logger.info(f"Registered drummer plugin: {drummer_name}")

    def get_genre_plugin(self, genre: str) -> GenrePlugin | None:
        """Get genre plugin by name."""
        return self._genre_plugins.get(genre.lower())

    def get_drummer_plugin(self, drummer: str) -> DrummerPlugin | None:
        """Get drummer plugin by name."""
        return self._drummer_plugins.get(drummer.lower())

    def get_available_genres(self) -> list[str]:
        """Get list of available genre names."""
        return list(self._genre_plugins.keys())

    def get_available_drummers(self) -> list[str]:
        """Get list of available drummer names."""
        return list(self._drummer_plugins.keys())

    def get_styles_for_genre(self, genre: str) -> list[str]:
        """Get available styles for a genre."""
        plugin = self.get_genre_plugin(genre)
        return plugin.supported_styles if plugin else []

    def get_compatible_drummers_for_genre(self, genre: str) -> list[str]:
        """Get drummers compatible with the given genre."""
        return [
            name
            for name, plugin in self._drummer_plugins.items()
            if plugin.is_compatible_with_genre(genre)
        ]


class PluginManager:
    """Main plugin management system."""

    def __init__(self):
        self.registry = PluginRegistry()
        self._discovery = PluginDiscovery(self.registry)

    def discover_plugins(self, plugin_dirs: list[Path] | None = None) -> None:
        """Auto-discover and load plugins from specified directories.

        Args:
            plugin_dirs: List of directories to search. If None, searches
                default locations.
        """
        self._discovery.discover(plugin_dirs)

    def _load_plugins_from_directory(self, plugin_dir: Path) -> None:
        """Load plugins from a specific directory (delegates to
        PluginDiscovery; kept here for backward-compat direct callers,
        e.g. tests exercising discovery internals)."""
        self._discovery._load_plugins_from_directory(plugin_dir)

    def _register_plugins_from_module(self, module) -> None:
        """Register all plugin classes found in a module (delegates to
        PluginDiscovery; kept here for backward-compat direct callers,
        e.g. tests exercising discovery internals)."""
        self._discovery._register_plugins_from_module(module)

    def generate_pattern(
        self, genre: str, section: str, parameters: GenerationParameters
    ) -> Pattern | None:
        """Generate a pattern using the appropriate genre plugin."""
        plugin = self.registry.get_genre_plugin(genre)
        if not plugin:
            logger.error(f"No plugin found for genre: {genre}")
            return None

        if not plugin.validate_parameters(parameters):
            logger.error(f"Invalid parameters for genre {genre}: {parameters}")
            return None

        try:
            return plugin.generate_pattern(section, parameters)
        except Exception as e:
            logger.error(f"Error generating pattern for {genre}/{section}: {e}")
            return None

    def apply_drummer_style(
        self, pattern: Pattern, drummer: str
    ) -> Pattern | None:
        """Apply drummer style to a pattern."""
        plugin = self.registry.get_drummer_plugin(drummer)
        if not plugin:
            logger.error(f"No plugin found for drummer: {drummer}")
            return None

        try:
            return plugin.apply_style(pattern)
        except Exception as e:
            logger.error(f"Error applying drummer style {drummer}: {e}")
            return None

    # Convenience methods for accessing registry data
    def get_available_genres(self) -> list[str]:
        """Get list of available genres."""
        return self.registry.get_available_genres()

    def get_available_drummers(self) -> list[str]:
        """Get list of available drummers."""
        return self.registry.get_available_drummers()

    def get_styles_for_genre(self, genre: str) -> list[str]:
        """Get available styles for a genre."""
        return self.registry.get_styles_for_genre(genre)

    def get_genre_plugin(self, genre: str) -> GenrePlugin | None:
        """Get genre plugin by name."""
        return self.registry.get_genre_plugin(genre)
