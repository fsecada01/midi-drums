"""Plugin system for extensible drum generation."""

from midi_drums.plugins.interfaces.drummer_plugin import DrummerPlugin
from midi_drums.plugins.interfaces.genre_plugin import GenrePlugin
from midi_drums.plugins.registry.plugin_registry import PluginManager

__all__ = ["GenrePlugin", "DrummerPlugin", "PluginManager"]
