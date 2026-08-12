"""Regression guard for issue #36 item 2.

`GenrePlugin._high_energy_timekeeper()` overrides choose which instrument
hi-hat timekeeping gets promoted to for high-energy sections (issue #18).
`midi_drums.modifications.drummer_mods` (PocketStretching,
MinimalCreativity, SpeedPrecision) needs to recognize any such promoted
instrument as "the timekeeping cymbal". Both sides now read from a single
shared registry - `core.value_objects.timekeeping
.PROMOTABLE_TIMEKEEPING_CYMBALS` - instead of drummer_mods maintaining its
own independent copy, so a genre plugin promoting to a new cymbal can't
silently drift out of sync with what the modifications layer recognizes.

`GenrePlugin._apply_ride_hihat_logic` also enforces this at runtime: it
raises ValueError if a `_high_energy_timekeeper()` override returns
anything outside the shared registry. This test is a second, cheaper
signal that fires at collection time rather than only when a specific
style/section combination actually triggers promotion, and it doubles as
a regression guard on the registry import wiring itself (both consumers
importing the *same* frozenset, not just equal-by-value copies).

This module discovers genre plugin classes by walking
`midi_drums/plugins/genres/` directly (the same approach
`PluginDiscovery._load_plugins_from_directory` uses) rather than
hand-listing plugin classes or styles, so it can't silently drift from
what's actually in the package.
"""

import importlib
import pkgutil

import pytest

import midi_drums.plugins.genres as genres_package
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)
from midi_drums.core.value_objects.timekeeping import (
    PROMOTABLE_TIMEKEEPING_CYMBALS,
)
from midi_drums.modifications.drummer_mods import (
    PROMOTABLE_TIMEKEEPING_CYMBALS as DRUMMER_MODS_REGISTRY,
)
from midi_drums.plugins.interfaces.genre_plugin import GenrePlugin

# One section from GenrePlugin._RIDE_SECTIONS and one plain non-high-energy
# section name. No current override branches on section (all branch on
# parameters.style), but the extension point's signature takes both, so
# both are exercised in case a future override does branch on section.
_SECTIONS = ("chorus", "verse")


def _discover_genre_plugin_classes() -> list[type[GenrePlugin]]:
    """Import every module in midi_drums/plugins/genres and collect every
    concrete GenrePlugin subclass defined there (not imported aliases,
    mirroring PluginDiscovery's own "attr.__module__ == module.__name__"
    filter so imported helper classes aren't double-counted).
    """
    classes: list[type[GenrePlugin]] = []
    for _finder, name, _ispkg in pkgutil.iter_modules(
        genres_package.__path__, genres_package.__name__ + "."
    ):
        module = importlib.import_module(name)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, GenrePlugin)
                and attr is not GenrePlugin
                and attr.__module__ == module.__name__
                and not getattr(attr, "__abstractmethods__", None)
                and attr not in classes
            ):
                classes.append(attr)
    return classes


@pytest.mark.unit
def test_discovery_finds_the_known_genre_plugins():
    """Sanity-checks the discovery helper itself, so a discovery bug can't
    silently make the real test below vacuously pass on zero classes.
    """
    names = {cls.__name__ for cls in _discover_genre_plugin_classes()}
    # The four legacy + four refactored genre plugins that exist today.
    assert {
        "MetalGenrePlugin",
        "RockGenrePlugin",
        "JazzGenrePlugin",
        "FunkGenrePlugin",
    } <= names
    assert len(names) >= 4


@pytest.mark.unit
def test_drummer_mods_imports_the_same_registry_object():
    """drummer_mods must import the shared registry, not maintain its own
    independent copy - otherwise this file's other test would pass while
    the two still silently drift (issue #36 item 2's actual failure mode).
    """
    assert DRUMMER_MODS_REGISTRY is PROMOTABLE_TIMEKEEPING_CYMBALS


@pytest.mark.unit
def test_high_energy_timekeeper_overrides_stay_within_shared_registry():
    """Every instrument any `_high_energy_timekeeper()` override can
    return - across every genre plugin and every style it supports - must
    be a member of the shared `PROMOTABLE_TIMEKEEPING_CYMBALS` registry.

    `_apply_ride_hihat_logic` enforces this with a runtime ValueError too;
    this test catches the same drift earlier, independent of whether any
    particular style/section combination is exercised elsewhere in the
    suite.
    """
    offenders = []
    for plugin_cls in _discover_genre_plugin_classes():
        plugin = plugin_cls()
        for style in plugin.supported_styles:
            for section in _SECTIONS:
                params = GenerationParameters(
                    genre=plugin.genre_name, style=style, complexity=0.5
                )
                instrument = plugin._high_energy_timekeeper(section, params)
                if instrument not in PROMOTABLE_TIMEKEEPING_CYMBALS:
                    offenders.append(
                        (plugin_cls.__name__, style, section, instrument)
                    )

    assert not offenders, (
        "_high_energy_timekeeper override(s) return an instrument not in "
        f"PROMOTABLE_TIMEKEEPING_CYMBALS: {offenders}"
    )
