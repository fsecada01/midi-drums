"""Test genre/drummer plugin auto-discovery and registration.

Regression coverage for a duplicate-registration bug: every discovered
module was scanned for *any* attribute that looked like a plugin class,
which also caught classes merely imported into that module's namespace
(a composite plugin importing its component plugins, or a
"FooRefactored = Foo" backward-compat alias) and registered them again.

The original bug surfaced via a traditional-file + refactored-file pair
declaring the same genre/drummer name (see issue #62); those traditional
files have since been deleted and the refactored files renamed to drop
the `_refactored` suffix, so there is now exactly one file per name and
zero legitimate overrides are expected.
"""

import logging
from collections import Counter

import pytest

from midi_drums.plugins.interfaces.drummer_plugin import DrummerPlugin
from midi_drums.plugins.registry.plugin_registry import PluginManager


@pytest.mark.unit
def test_discover_plugins_registers_each_name_exactly_once(caplog):
    """Every genre/drummer name is now declared in exactly one file, so
    discovery must produce zero "Overriding existing" warnings.
    """
    with caplog.at_level(
        logging.WARNING, logger="midi_drums.plugins.registry.plugin_registry"
    ):
        manager = PluginManager()
        manager.discover_plugins()

    override_messages = [
        r.getMessage()
        for r in caplog.records
        if "Overriding existing" in r.getMessage()
    ]

    counts = Counter(override_messages)
    assert not counts, (
        f"Expected zero plugin-name overrides now that each genre/drummer "
        f"has exactly one file, got: {dict(counts)}"
    )


@pytest.mark.unit
def test_discover_plugins_registers_plain_module_names():
    """Genre/drummer plugins register under their plain module path (no
    `_refactored` suffix, since the original/refactored split no longer
    exists).
    """
    manager = PluginManager()
    manager.discover_plugins()

    bonham = manager.registry.get_drummer_plugin("bonham")
    assert type(bonham).__module__.endswith("plugins.drummers.bonham")

    metal = manager.registry.get_genre_plugin("metal")
    assert type(metal).__module__.endswith("plugins.genres.metal")


@pytest.mark.unit
def test_composite_plugin_does_not_reregister_component_drummers():
    """composite_doom_blues.py imports ChambersPlugin/PorcaroPlugin/
    RoederPlugin to compose them internally - discovery must not treat
    those imported names as new plugin definitions to register.
    """
    manager = PluginManager()
    manager.discover_plugins()

    chambers = manager.registry.get_drummer_plugin("chambers")
    porcaro = manager.registry.get_drummer_plugin("porcaro")
    roeder = manager.registry.get_drummer_plugin("roeder")

    assert type(chambers).__module__.endswith("plugins.drummers.chambers")
    assert type(porcaro).__module__.endswith("plugins.drummers.porcaro")
    assert type(roeder).__module__.endswith("plugins.drummers.roeder")

    # The composite itself must still register under its own name.
    composite = manager.registry.get_drummer_plugin("composite_doom_blues")
    assert composite is not None
    assert isinstance(composite, DrummerPlugin)


@pytest.mark.unit
def test_register_plugins_from_module_ignores_backward_compat_alias():
    """A "FooRefactored = Foo" alias in the same module must not cause
    the class to be instantiated and registered twice.
    """
    import types

    from midi_drums.plugins.drummers.bonham import BonhamPlugin

    fake_module = types.ModuleType("fake_module_with_alias")
    fake_module.__name__ = "fake_module_with_alias"
    fake_module.BonhamPlugin = BonhamPlugin
    fake_module.BonhamPluginRefactored = BonhamPlugin  # same object, 2 names

    # BonhamPlugin is defined in the real bonham module, not in fake_module,
    # so it should be skipped entirely here - proving the dedup-by-identity
    # guard isn't the only thing carrying this test.
    manager = PluginManager()
    manager._register_plugins_from_module(fake_module)
    assert manager.registry.get_drummer_plugin("bonham") is None


@pytest.mark.unit
def test_discover_plugins_loads_external_directory(tmp_path):
    """discover_plugins(plugin_dirs=[...]) must still support directories
    outside midi_drums.plugins (a documented extension point for
    third-party/custom plugins) - not just the built-in genres/drummers
    subpackages.
    """
    external_dir = tmp_path / "my_custom_plugins"
    external_dir.mkdir()
    (external_dir / "__init__.py").write_text("")
    (external_dir / "custom_drummer.py").write_text(
        "from midi_drums.plugins.base import DrummerPlugin\n"
        "\n"
        "class CustomDrummerPlugin(DrummerPlugin):\n"
        "    @property\n"
        "    def drummer_name(self):\n"
        "        return '_external_test_drummer'\n"
        "\n"
        "    @property\n"
        "    def compatible_genres(self):\n"
        "        return ['rock']\n"
        "\n"
        "    def apply_style(self, pattern):\n"
        "        return pattern\n"
        "\n"
        "    def get_signature_fills(self):\n"
        "        return []\n"
    )

    manager = PluginManager()
    manager.discover_plugins([external_dir])

    plugin = manager.registry.get_drummer_plugin("_external_test_drummer")
    assert plugin is not None
    assert type(plugin).__module__ == "my_custom_plugins.custom_drummer"


@pytest.mark.unit
def test_register_plugins_from_module_registers_locally_defined_class_once():
    """A plugin class actually defined in the scanned module registers
    exactly once, even if bound to two attribute names in that module.
    """

    class _LocalDrummer(DrummerPlugin):
        @property
        def drummer_name(self) -> str:
            return "_local_test_drummer"

        @property
        def compatible_genres(self) -> list[str]:
            return ["rock"]

        def apply_style(self, pattern):
            return pattern

        def get_signature_fills(self):
            return []

    import types

    fake_module = types.ModuleType("fake_module_local")
    _LocalDrummer.__module__ = "fake_module_local"
    fake_module.LocalDrummer = _LocalDrummer
    fake_module.LocalDrummerAlias = _LocalDrummer

    manager = PluginManager()
    manager._register_plugins_from_module(fake_module)

    assert (
        manager.registry.get_drummer_plugin("_local_test_drummer") is not None
    )
    assert (
        manager.registry.get_available_drummers().count("_local_test_drummer")
        == 1
    )
