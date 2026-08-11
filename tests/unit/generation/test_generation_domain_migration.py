"""Tests for the Generation Domain migration (issue #12, epic #8).

Covers the issue's acceptance criteria: DrumGenerator and PatternBuilder now
live under midi_drums.generation, the old midi_drums.core.engine /
midi_drums.core.builders.pattern_builder modules are gone (and the now-empty
midi_drums.core.builders package with them), new PatternStrategy/FillStrategy
interfaces and a GenerationService orchestrator exist, and the generation
domain's dependencies are limited to what DrumGenerator/PatternBuilder
actually need (core, export, plugins - not the sibling application-level
domains).
"""

import importlib
from abc import ABC
from pathlib import Path

import pytest

from tests.unit._domain_migration_helpers import imported_modules

PACKAGE_ROOT = Path(__file__).resolve().parents[3] / "midi_drums"
GENERATION_PACKAGE_ROOT = PACKAGE_ROOT / "generation"
CORE_PACKAGE_ROOT = PACKAGE_ROOT / "core"

# Domains the generation package must not depend on. midi_drums.core
# (shared kernel), midi_drums.export and midi_drums.plugins are allowed -
# DrumGenerator legitimately depends on MIDIEngine and PluginManager.
FORBIDDEN_DOMAIN_PREFIXES = (
    "midi_drums.humanization",
    "midi_drums.validation",
    "midi_drums.ai",
    "midi_drums.modifications",
    "midi_drums.parsers",
    "midi_drums.utils",
    "midi_drums.api",
    "midi_drums.models",
    "midi_drums.engines",
    "midi_drums.exporters",
)

GENERATION_SUBPACKAGES = ["engines", "builders", "strategies", "services"]


def _iter_generation_files():
    for subpackage in GENERATION_SUBPACKAGES:
        yield from (GENERATION_PACKAGE_ROOT / subpackage).glob("*.py")


class TestNewImportPaths:
    """Issue tasks: engine/builder live under generation/, plus the new
    strategy interfaces and service orchestrator this phase introduces."""

    def test_drum_generator_importable_from_generation(self):
        from midi_drums.generation.engines.drum_generator import (
            DrumGenerator,
        )

        assert DrumGenerator is not None

    def test_pattern_builder_importable_from_generation(self):
        from midi_drums.generation.builders.pattern_builder import (
            PatternBuilder,
        )

        pattern = PatternBuilder("test").kick(0.0).build()
        assert len(pattern.beats) == 1

    def test_pattern_strategy_interface_importable(self):
        from midi_drums.generation.strategies.pattern_strategy import (
            PatternStrategy,
        )

        assert issubclass(PatternStrategy, ABC)
        with pytest.raises(TypeError):
            PatternStrategy()  # abstract - cannot be instantiated directly

    def test_fill_strategy_interface_importable(self):
        from midi_drums.generation.strategies.fill_strategy import (
            FillStrategy,
        )

        assert issubclass(FillStrategy, ABC)
        with pytest.raises(TypeError):
            FillStrategy()  # abstract - cannot be instantiated directly

    def test_generation_service_importable(self):
        from midi_drums.generation.services.generation_service import (
            GenerationService,
        )

        service = GenerationService()
        assert service.drum_generator is not None

    def test_generation_service_generates_pattern(self):
        from midi_drums.generation.services.generation_service import (
            GenerationService,
        )

        service = GenerationService()
        pattern = service.generate_pattern(
            "metal", section="verse", bars=1, style="heavy"
        )
        assert pattern is not None


class TestOldGenerationModulesRemoved:
    """Task: the old core.engine / core.builders.pattern_builder are gone,
    not just supplemented - this is a move, not a copy."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "midi_drums.core.engine",
            "midi_drums.core.builders.pattern_builder",
            "midi_drums.core.builders",
        ],
    )
    def test_old_module_no_longer_importable(self, module_name):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(module_name)

    def test_core_engine_file_removed(self):
        assert not (CORE_PACKAGE_ROOT / "engine.py").exists()

    def test_core_builders_package_removed(self):
        """pattern_builder.py was the only file in midi_drums/core/builders/
        - the whole subpackage is retired once it moves (#9 created it,
        #12 empties and retires it)."""
        assert not (CORE_PACKAGE_ROOT / "builders").exists()

    def test_core_package_still_exists(self):
        """core/ itself survives - models/ and value_objects/ are untouched
        by this phase, only engine.py and builders/ move out."""
        assert (CORE_PACKAGE_ROOT / "models").exists()
        assert (CORE_PACKAGE_ROOT / "value_objects").exists()


class TestGenerationDomainHasAllowedDependenciesOnly:
    """Success criterion (implicit): generation domain doesn't reach into
    sibling application-level domains (ai, api, humanization, validation,
    etc). It's allowed to depend on midi_drums.core, midi_drums.export and
    midi_drums.plugins - those are DrumGenerator's real, legitimate
    dependencies (MIDIEngine, PluginManager)."""

    def test_generation_files_exist(self):
        files = list(_iter_generation_files())
        assert len(files) >= 4, (
            "expected at least 4 files across generation/engines, "
            "generation/builders, generation/strategies, "
            "generation/services"
        )

    @pytest.mark.parametrize(
        "file_path", list(_iter_generation_files()), ids=lambda p: p.name
    )
    def test_file_has_no_forbidden_import(self, file_path):
        modules = imported_modules(file_path)
        violations = [
            m
            for m in modules
            if any(m.startswith(prefix) for prefix in FORBIDDEN_DOMAIN_PREFIXES)
        ]
        assert (
            not violations
        ), f"{file_path} imports from forbidden domains: {violations}"


class TestPublicApiUnchanged:
    """Success criterion: no breaking changes to public API - the
    top-level midi_drums package still exports the same names, backed by
    the same DrumGenerator class now living under generation/."""

    def test_top_level_exports_unchanged(self):
        import midi_drums

        for name in (
            "DrumGenerator",
            "Pattern",
            "Beat",
            "TimeSignature",
            "Song",
            "Section",
            "GenerationParameters",
        ):
            assert hasattr(midi_drums, name), f"midi_drums.{name} missing"

    def test_top_level_drum_generator_is_generation_drum_generator(self):
        import midi_drums
        from midi_drums.generation.engines.drum_generator import (
            DrumGenerator as GenerationDrumGenerator,
        )

        assert midi_drums.DrumGenerator is GenerationDrumGenerator
