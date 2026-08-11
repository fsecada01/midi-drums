"""Plugin registry - storage, lookup, and auto-discovery."""

from midi_drums.plugins.registry.discovery import PluginDiscovery
from midi_drums.plugins.registry.plugin_registry import (
    PluginManager,
    PluginRegistry,
)

__all__ = ["PluginRegistry", "PluginManager", "PluginDiscovery"]
