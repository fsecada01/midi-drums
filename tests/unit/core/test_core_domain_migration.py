"""Tests for the Core Domain migration (issue #9, epic #8).

Covers the issue's acceptance criteria: models/value objects/builders now
live under midi_drums.core with clear boundaries, the old
midi_drums.models.{pattern,song,kit} modules are gone, the core domain has
no dependency on other domains, and the top-level public API is unchanged.
"""

import importlib
from pathlib import Path

import pytest

from tests.unit._domain_migration_helpers import imported_modules

CORE_PACKAGE_ROOT = Path(__file__).resolve().parents[3] / "midi_drums" / "core"

# Domains the core package must not depend on. "midi_drums.core" itself and
# "midi_drums.config" (shared kernel constants) are allowed.
FORBIDDEN_DOMAIN_PREFIXES = (
    "midi_drums.plugins",
    "midi_drums.engines",
    "midi_drums.humanization",
    "midi_drums.validation",
    "midi_drums.exporters",
    "midi_drums.export",
    "midi_drums.generation",
    "midi_drums.ai",
    "midi_drums.modifications",
    "midi_drums.parsers",
    "midi_drums.utils",
    "midi_drums.api",
    "midi_drums.models",
)

# Scoped to the new subpackages added in this phase - models and
# value_objects. builders/ (PatternBuilder) has since moved on to the
# Generation Domain phase (#12) and core/builders/ no longer exists; see
# test_generation_domain_migration.py for its current-state assertions.
NEW_CORE_SUBPACKAGES = ["models", "value_objects"]


def _iter_new_core_files():
    for subpackage in NEW_CORE_SUBPACKAGES:
        yield from (CORE_PACKAGE_ROOT / subpackage).glob("*.py")


class TestNewImportPaths:
    """Issue tasks: models/value objects/builders live under core/."""

    def test_pattern_models_importable_from_core(self):
        from midi_drums.core.models.pattern import Beat, Pattern

        assert Beat is not None
        assert Pattern is not None

    def test_song_models_importable_from_core(self):
        from midi_drums.core.models.song import (
            Fill,
            PatternVariation,
            Section,
            Song,
        )

        assert Song is not None
        assert Section is not None
        assert Fill is not None
        assert PatternVariation is not None

    def test_kit_model_importable_from_core(self):
        from midi_drums.core.models.kit import DrumKit, VelocityRange

        assert DrumKit is not None
        assert VelocityRange is not None

    def test_time_signature_importable_from_value_objects(self):
        from midi_drums.core.value_objects.time_signature import TimeSignature

        assert TimeSignature().beats_per_bar == 4.0

    def test_drum_instrument_importable_from_value_objects(self):
        from midi_drums.core.value_objects.drum_instrument import (
            DrumInstrument,
        )

        assert DrumInstrument.KICK.value == 36

    def test_generation_parameters_importable_from_value_objects(self):
        from midi_drums.core.value_objects.generation_parameters import (
            GenerationParameters,
        )

        params = GenerationParameters(genre="metal")
        assert params.ride_threshold == 0.9

    # PatternBuilder stayed in midi_drums.core.builders when this phase (#9)
    # ran. #12 (Generation Domain) has since moved it and retired
    # midi_drums/core/builders/ entirely - see
    # test_generation_domain_migration.py's TestOldGenerationModulesRemoved
    # for the current-state assertions.


class TestOldModelModulesRemoved:
    """Task: the old midi_drums.models.{pattern,song,kit} are gone, not
    just supplemented - this is a move, not a copy."""

    @pytest.mark.parametrize("module_name", ["pattern", "song", "kit"])
    def test_old_module_no_longer_importable(self, module_name):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(f"midi_drums.models.{module_name}")

    # reaper_models.py stayed in midi_drums.models when this phase (#9) ran,
    # deliberately out of scope pending #10 (Export Domain). #10 has since
    # moved it and retired midi_drums/models/ entirely - see
    # test_export_domain_migration.py's TestOldExportModulesRemoved for the
    # current-state assertions.


class TestCoreDomainHasNoOtherDomainDependency:
    """Success criterion: core domain has zero dependencies on other
    domains. Scoped to models/value_objects - core/engine.py and
    core/builders/ have since moved to the Generation Domain phase (#12)
    and are out of scope here (see module docstring)."""

    def test_new_core_files_exist(self):
        files = list(_iter_new_core_files())
        assert len(files) >= 6, (
            "expected at least 6 files across core/models, "
            "core/value_objects"
        )

    @pytest.mark.parametrize(
        "file_path", list(_iter_new_core_files()), ids=lambda p: p.name
    )
    def test_file_has_no_cross_domain_import(self, file_path):
        modules = imported_modules(file_path)
        violations = [
            m
            for m in modules
            if any(m.startswith(prefix) for prefix in FORBIDDEN_DOMAIN_PREFIXES)
        ]
        assert (
            not violations
        ), f"{file_path} imports from other domains: {violations}"


class TestPublicApiUnchanged:
    """Success criterion: no breaking changes to public API - the
    top-level midi_drums package still exports the same names, backed by
    the same classes now living under core/."""

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

    def test_top_level_pattern_is_core_pattern(self):
        import midi_drums
        from midi_drums.core.models.pattern import Pattern as CorePattern

        assert midi_drums.Pattern is CorePattern

    def test_top_level_generation_parameters_is_core_value_object(self):
        import midi_drums
        from midi_drums.core.value_objects.generation_parameters import (
            GenerationParameters as CoreGenerationParameters,
        )

        assert midi_drums.GenerationParameters is CoreGenerationParameters
