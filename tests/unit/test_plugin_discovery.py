"""Test genre/drummer plugin auto-discovery and registration.

Regression coverage for a duplicate-registration bug: every discovered
module was scanned for *any* attribute that looked like a plugin class,
which also caught classes merely imported into that module's namespace
(a composite plugin importing its component plugins, or a
"FooRefactored = Foo" backward-compat alias) and registered them again.
"""

import logging
from collections import Counter

import pytest

from midi_drums.plugins.interfaces.drummer_plugin import DrummerPlugin
from midi_drums.plugins.registry.plugin_registry import PluginManager

EXPECTED_GENRES_WITH_REFACTORED_VARIANT = {"metal", "rock", "jazz", "funk"}
EXPECTED_DRUMMERS_WITH_REFACTORED_VARIANT = {
    "bonham",
    "chambers",
    "dee",
    "hoglan",
    "porcaro",
    "roeder",
    "weckl",
}


@pytest.mark.unit
def test_discover_plugins_overrides_each_name_at_most_once(caplog):
    """Each genre/drummer name has a traditional + refactored file, so
    exactly one "Overriding existing" warning per name is expected. Any
    more means a plugin got registered from more than the two files that
    legitimately declare that name.
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
    over_registered = {msg: n for msg, n in counts.items() if n > 1}
    assert not over_registered, (
        f"Plugin(s) registered more than twice (expected exactly one "
        f"override per name): {over_registered}"
    )

    expected_override_count = len(
        EXPECTED_GENRES_WITH_REFACTORED_VARIANT
    ) + len(EXPECTED_DRUMMERS_WITH_REFACTORED_VARIANT)
    assert len(counts) == expected_override_count == 11


@pytest.mark.unit
def test_discover_plugins_prefers_refactored_class():
    """Refactored plugins are the "modern approach" per the README and
    must win when both a traditional and refactored file declare the
    same genre/drummer name.
    """
    manager = PluginManager()
    manager.discover_plugins()

    bonham = manager.registry.get_drummer_plugin("bonham")
    assert type(bonham).__module__.endswith("bonham_refactored")

    metal = manager.registry.get_genre_plugin("metal")
    assert type(metal).__module__.endswith("metal_refactored")


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

    assert type(chambers).__module__.endswith("chambers_refactored")
    assert type(porcaro).__module__.endswith("porcaro_refactored")
    assert type(roeder).__module__.endswith("roeder_refactored")

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

    from midi_drums.plugins.drummers.bonham_refactored import BonhamPlugin

    fake_module = types.ModuleType("fake_module_with_alias")
    fake_module.__name__ = "fake_module_with_alias"
    fake_module.BonhamPlugin = BonhamPlugin
    fake_module.BonhamPluginRefactored = BonhamPlugin  # same object, 2 names

    # BonhamPlugin is defined in the real bonham_refactored module, not
    # in fake_module, so it should be skipped entirely here - proving
    # the dedup-by-identity guard isn't the only thing carrying this test.
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
