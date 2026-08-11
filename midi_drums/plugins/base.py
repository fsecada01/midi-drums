"""Base classes for plugin system.

GenrePlugin/DrummerPlugin now live in midi_drums.plugins.interfaces;
PluginRegistry/PluginManager now live in midi_drums.plugins.registry (see
#11). This module is kept as a re-export shim so
`from midi_drums.plugins.base import ...` keeps working.
"""

from midi_drums.plugins.interfaces.drummer_plugin import DrummerPlugin
from midi_drums.plugins.interfaces.genre_plugin import GenrePlugin
from midi_drums.plugins.registry.plugin_registry import (
    PluginManager,
    PluginRegistry,
)

__all__ = ["GenrePlugin", "DrummerPlugin", "PluginRegistry", "PluginManager"]
