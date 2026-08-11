"""Tests for the Plugin Domain migration (issue #11, epic #8).

Covers the issue's acceptance criteria: GenrePlugin/DrummerPlugin now live
under midi_drums.plugins.interfaces, PluginRegistry/PluginManager now live
under midi_drums.plugins.registry (with auto-discovery split into its own
discovery module), the composite drummer moved into
drummers/composite/doom_blues.py, midi_drums.plugins.base keeps
re-exporting the four names as a compat shim, and plugin auto-discovery
still finds every built-in genre/drummer - including the relocated
composite one - after the move.

Also covers the plugins domain's dependency-boundary rule documented in
docs/DDD_ARCHITECTURE.md: plugins/ may depend on core/ and, as a named
exception, generation/builders/ (PatternBuilder is a dependency-free
construction utility every genre/drummer plugin uses) - but not
export/, generation/engines/, generation/services/, generation/strategies/,
or any sibling application-level domain.
"""

import importlib
from pathlib import Path

import pytest

from tests.unit._domain_migration_helpers import imported_modules

PACKAGE_ROOT = Path(__file__).resolve().parents[3] / "midi_drums"
PLUGINS_PACKAGE_ROOT = PACKAGE_ROOT / "plugins"

# Domains the plugins package must not depend on. midi_drums.core (shared
# kernel), midi_drums.config, and the application-level packages plugins
# already legitimately use (modifications, patterns, utils, validation) are
# allowed; midi_drums.generation.builders is allowed as a named exception
# (see module docstring) despite midi_drums.generation itself being
# forbidden otherwise. This is the actual export/orchestration boundary:
# plugins/ has no reason to know how a pattern gets saved to disk
# (export/) or which engine/service invoked it (generation/engines,
# generation/services, generation/strategies).
FORBIDDEN_DOMAIN_PREFIXES = (
    "midi_drums.export",
    "midi_drums.exporters",
    "midi_drums.engines",
    "midi_drums.humanization",
    "midi_drums.ai",
    "midi_drums.parsers",
    "midi_drums.api",
    "midi_drums.models",
    "midi_drums.generation",
)
ALLOWED_EXCEPTION_PREFIXES = ("midi_drums.generation.builders",)


def _iter_plugin_files():
    yield from PLUGINS_PACKAGE_ROOT.glob("**/*.py")


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


class TestPluginDomainHasAllowedDependenciesOnly:
    """Success criterion: plugins/ doesn't reach into export/ or the
    orchestration parts of generation/ (engines/services/strategies) - only
    core/ and, as a named exception, generation/builders/ (PatternBuilder).
    """

    def test_plugin_files_exist(self):
        files = list(_iter_plugin_files())
        assert len(files) >= 10, "expected at least 10 files under plugins/"

    @pytest.mark.parametrize(
        "file_path", list(_iter_plugin_files()), ids=lambda p: p.name
    )
    def test_file_has_no_forbidden_import(self, file_path):
        modules = imported_modules(file_path)
        violations = [
            m
            for m in modules
            if any(m.startswith(prefix) for prefix in FORBIDDEN_DOMAIN_PREFIXES)
            and not any(
                m.startswith(allowed) for allowed in ALLOWED_EXCEPTION_PREFIXES
            )
        ]
        assert (
            not violations
        ), f"{file_path} imports from forbidden domains: {violations}"


class TestPluginPackageStructure:
    def test_interfaces_package_exists(self):
        assert (PACKAGE_ROOT / "plugins" / "interfaces").is_dir()

    def test_registry_package_exists(self):
        assert (PACKAGE_ROOT / "plugins" / "registry").is_dir()

    def test_composite_drummers_package_exists(self):
        assert (PACKAGE_ROOT / "plugins" / "drummers" / "composite").is_dir()

    def test_base_module_still_exists_as_shim(self):
        assert (PACKAGE_ROOT / "plugins" / "base.py").exists()
