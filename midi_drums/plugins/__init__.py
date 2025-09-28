"""Plugin system for extensible drum generation."""

from midi_drums.plugins.base import DrummerPlugin, GenrePlugin, PluginManager

__all__ = ["GenrePlugin", "DrummerPlugin", "PluginManager"]
