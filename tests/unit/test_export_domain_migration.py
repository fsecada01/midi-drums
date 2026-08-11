"""Tests for the Export Domain migration (issue #10, epic #8).

Covers the issue's acceptance criteria: MIDI/Reaper engines, the Reaper
exporter, and reaper_models now live under midi_drums.export, the old
midi_drums.engines.* / midi_drums.exporters.reaper_exporter /
midi_drums.models.reaper_models modules are gone, midi_drums.exporters
keeps re-exporting ReaperExporter as a compat shim, and the export domain
has no dependency on the plugins/application layers (it may depend on
midi_drums.core, the shared kernel).
"""

import ast
import importlib
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "midi_drums"
EXPORT_PACKAGE_ROOT = PACKAGE_ROOT / "export"

# Domains the export package must not depend on. midi_drums.core (shared
# kernel) and midi_drums.export itself are allowed.
FORBIDDEN_DOMAIN_PREFIXES = (
    "midi_drums.plugins",
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

EXPORT_SUBPACKAGES = ["midi", "reaper"]


def _iter_export_files():
    for subpackage in EXPORT_SUBPACKAGES:
        yield from (EXPORT_PACKAGE_ROOT / subpackage).glob("*.py")


def _imported_modules(file_path: Path) -> list[str]:
    tree = ast.parse(
        file_path.read_text(encoding="utf-8"), filename=str(file_path)
    )
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


class TestNewImportPaths:
    """Issue tasks: engine/exporter/models live under export/{midi,reaper}."""

    def test_midi_engine_importable_from_export(self):
        from midi_drums.export.midi.engine import MIDIEngine

        assert MIDIEngine is not None

    def test_midi_exporter_importable_from_export(self):
        from midi_drums.export.midi.exporter import MIDIExporter

        assert MIDIExporter is not None

    def test_reaper_engine_importable_from_export(self):
        from midi_drums.export.reaper.engine import (
            ReaperEngine,
            bars_to_seconds,
        )

        assert ReaperEngine is not None
        assert bars_to_seconds is not None

    def test_reaper_exporter_importable_from_export(self):
        from midi_drums.export.reaper.exporter import ReaperExporter

        assert ReaperExporter is not None

    def test_reaper_models_importable_from_export(self):
        from midi_drums.export.reaper.models import (
            DEFAULT_SECTION_COLOR,
            GenreStructurePreset,
            Marker,
            ReaperTrack,
            SectionTemplate,
            get_genre_preset,
            get_section_color,
            list_genre_presets,
        )

        assert Marker is not None
        assert ReaperTrack is not None
        assert SectionTemplate is not None
        assert GenreStructurePreset is not None
        assert get_genre_preset is not None
        assert get_section_color is not None
        assert list_genre_presets is not None
        assert DEFAULT_SECTION_COLOR == "#FF5733"


class TestOldExportModulesRemoved:
    """Task: the old engines/exporters/reaper_models submodules are gone,
    not just supplemented - this is a move, not a copy."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "midi_drums.engines.midi_engine",
            "midi_drums.engines.reaper_engine",
            "midi_drums.exporters.reaper_exporter",
            "midi_drums.models.reaper_models",
        ],
    )
    def test_old_module_no_longer_importable(self, module_name):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(module_name)

    def test_engines_package_removed(self):
        assert not (PACKAGE_ROOT / "engines").exists()

    def test_models_package_removed(self):
        """reaper_models.py was the last file in midi_drums/models/ -
        the whole package is retired once it moves (#9 moved
        pattern/song/kit, #10 moves reaper_models)."""
        assert not (PACKAGE_ROOT / "models").exists()


class TestExportersCompatShim:
    """Task: exporters/__init__.py re-exports from the new location, so
    `from midi_drums.exporters import ReaperExporter` keeps working even
    though the reaper_exporter submodule itself moved."""

    def test_reaper_exporter_reexported_from_exporters_package(self):
        from midi_drums.export.reaper.exporter import (
            ReaperExporter as CoreReaperExporter,
        )
        from midi_drums.exporters import ReaperExporter

        assert ReaperExporter is CoreReaperExporter


class TestExportDomainHasNoForbiddenDependency:
    """Success criterion (implicit): export domain doesn't reach back into
    plugins/application layers. It's allowed to depend on midi_drums.core
    (the shared kernel) - that's expected, unlike the core domain itself
    which must depend on nothing (see test_core_domain_migration.py)."""

    def test_export_files_exist(self):
        files = list(_iter_export_files())
        assert (
            len(files) >= 4
        ), "expected at least 4 files across export/midi, export/reaper"

    @pytest.mark.parametrize(
        "file_path", list(_iter_export_files()), ids=lambda p: p.name
    )
    def test_file_has_no_forbidden_import(self, file_path):
        modules = _imported_modules(file_path)
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
    top-level midi_drums package still exports the same names (this
    phase doesn't touch core/, so it should be a no-op check)."""

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
