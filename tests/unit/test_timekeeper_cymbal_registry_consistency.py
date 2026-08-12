"""Regression guard for issue #36 item 2.

`drummer_mods._TIMEKEEPING_CYMBALS` is a fixed frozenset of instruments the
modifications layer (PocketStretching, MinimalCreativity, SpeedPrecision)
treats as "the timekeeping cymbal". Genre plugins independently choose
which instrument `GenrePlugin._high_energy_timekeeper()` promotes hi-hat to
for high-energy sections (issue #18), and nothing links the two lists: a
future genre plugin promoting to a new instrument (e.g. a splash or bell)
would need someone to remember to also add it to `_TIMEKEEPING_CYMBALS` by
hand, with no compile-time or test-time signal if they forget.

This module is that signal. It discovers genre plugin classes by walking
`midi_drums/plugins/genres/` directly (the same approach
`PluginDiscovery._load_plugins_from_directory` uses) rather than
hand-listing plugin classes or styles, so it can't silently drift from
what's actually in the package - a new genre plugin, or a new style branch
inside an existing `_high_energy_timekeeper` override, is picked up
automatically without editing this file.

Per issue #36's own scope, this is the "no" (document, don't restructure)
resolution's minimum bar: a cheap guard against silent drift, without
introducing a shared registry/constant that would restructure the
plugin/modifications dependency direction.
"""

import importlib
import pkgutil

import pytest

import midi_drums.plugins.genres as genres_package
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)
from midi_drums.modifications.drummer_mods import _TIMEKEEPING_CYMBALS
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
def test_high_energy_timekeeper_overrides_stay_within_timekeeping_cymbals():
    """Every instrument any `_high_energy_timekeeper()` override can
    return - across every genre plugin and every style it supports - must
    be a member of `drummer_mods._TIMEKEEPING_CYMBALS`.

    If it isn't, PocketStretching/MinimalCreativity/SpeedPrecision
    silently stop recognizing that promoted cymbal as "the timekeeping
    cymbal" for high-energy sections, because those modifications match
    on instrument membership in that frozenset (issue #36 item 2).
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
                if instrument not in _TIMEKEEPING_CYMBALS:
                    offenders.append(
                        (plugin_cls.__name__, style, section, instrument)
                    )

    assert not offenders, (
        "_high_energy_timekeeper override(s) return an instrument not in "
        f"drummer_mods._TIMEKEEPING_CYMBALS: {offenders}"
    )
