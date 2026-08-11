"""Tests for the Plugin Domain migration (issue #11, epic #8).

Covers the issue's acceptance criteria: GenrePlugin/DrummerPlugin now live
under midi_drums.plugins.interfaces, PluginRegistry/PluginManager now live
under midi_drums.plugins.registry (with auto-discovery split into its own
discovery module), the composite drummer moved into
drummers/composite/doom_blues.py, midi_drums.plugins.base keeps
re-exporting the four names as a compat shim, and plugin auto-discovery
still finds every built-in genre/drummer - including the relocated
composite one - after the move.
"""

import importlib
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[3] / "midi_drums"


class TestNewImportPaths:
    def test_genre_plugin_importable_from_interfaces(self):
        from midi_drums.plugins.interfaces.genre_plugin import GenrePlugin

        assert GenrePlugin is not None

    def test_drummer_plugin_importable_from_interfaces(self):
        from midi_drums.plugins.interfaces.drummer_plugin import (
            DrummerPlugin,
        )

        assert DrummerPlugin is not None

    def test_plugin_registry_and_manager_importable_from_registry(self):
        from midi_drums.plugins.registry.plugin_registry import (
            PluginManager,
            PluginRegistry,
        )

        assert PluginRegistry is not None
        assert PluginManager is not None

    def test_discovery_importable_from_registry(self):
        from midi_drums.plugins.registry.discovery import PluginDiscovery

        assert PluginDiscovery is not None


class TestCompositeDrummerMoved:
    """Task: composite drummers -> drummers/composite/ - a move, not a
    copy, and the file drops its now-redundant 'composite_' prefix."""

    def test_composite_doom_blues_importable_from_new_location(self):
        from midi_drums.plugins.drummers.composite.doom_blues import (
            CompositeDoomBluesPlugin,
        )

        assert CompositeDoomBluesPlugin is not None

    def test_old_composite_module_no_longer_importable(self):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(
                "midi_drums.plugins.drummers.composite_doom_blues"
            )


class TestBaseCompatShim:
    """Task: base.py re-exports from the new locations, so
    `from midi_drums.plugins.base import ...` keeps working even though
    the real classes moved (mirrors midi_drums.exporters from #10)."""

    def test_genre_plugin_reexported(self):
        from midi_drums.plugins.base import GenrePlugin as ShimGenrePlugin
        from midi_drums.plugins.interfaces.genre_plugin import (
            GenrePlugin as CoreGenrePlugin,
        )

        assert ShimGenrePlugin is CoreGenrePlugin

    def test_drummer_plugin_reexported(self):
        from midi_drums.plugins.base import DrummerPlugin as ShimDrummerPlugin
        from midi_drums.plugins.interfaces.drummer_plugin import (
            DrummerPlugin as CoreDrummerPlugin,
        )

        assert ShimDrummerPlugin is CoreDrummerPlugin

    def test_plugin_manager_reexported(self):
        from midi_drums.plugins.base import PluginManager as ShimPluginManager
        from midi_drums.plugins.registry.plugin_registry import (
            PluginManager as CorePluginManager,
        )

        assert ShimPluginManager is CorePluginManager

    def test_plugin_registry_reexported(self):
        from midi_drums.plugins.base import PluginRegistry as ShimPluginRegistry
        from midi_drums.plugins.registry.plugin_registry import (
            PluginRegistry as CorePluginRegistry,
        )

        assert ShimPluginRegistry is CorePluginRegistry


class TestPluginDiscoveryFindsRelocatedComposite:
    """Regression: moving composite_doom_blues.py into a drummers/composite/
    subpackage must not silently drop it from auto-discovery -
    pkgutil-based directory scanning doesn't recurse into subpackages by
    default, so the discovery mechanism must explicitly account for it."""

    def test_discover_plugins_finds_composite_after_move(self):
        from midi_drums.plugins.registry.plugin_registry import (
            PluginManager,
        )

        manager = PluginManager()
        manager.discover_plugins()

        composite = manager.registry.get_drummer_plugin("composite_doom_blues")
        assert composite is not None
        assert (
            type(composite).__module__
            == "midi_drums.plugins.drummers.composite.doom_blues"
        )


class TestPluginPackageStructure:
    def test_interfaces_package_exists(self):
        assert (PACKAGE_ROOT / "plugins" / "interfaces").is_dir()

    def test_registry_package_exists(self):
        assert (PACKAGE_ROOT / "plugins" / "registry").is_dir()

    def test_composite_drummers_package_exists(self):
        assert (PACKAGE_ROOT / "plugins" / "drummers" / "composite").is_dir()

    def test_base_module_still_exists_as_shim(self):
        assert (PACKAGE_ROOT / "plugins" / "base.py").exists()
