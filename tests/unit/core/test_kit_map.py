"""Tests for DrumKit.kit_map() (ADR 0009 - Step Editor panel note map).

`kit_map()` is what the `list kit-map` CLI verb serializes and what the
REAPER panel's Step Editor tab will consume in place of a hardcoded Lua
drum-note table - see docs/adr/0009-unified-step-editor-panel.md.
"""

import pytest

from midi_drums.core.models.kit import DrumKit
from midi_drums.core.value_objects.drum_instrument import DrumInstrument


class TestKitMapShape:
    def test_every_entry_has_the_expected_keys(self):
        kit = DrumKit.create_gm_drums_kit()

        for entry in kit.kit_map():
            assert set(entry.keys()) == {
                "note",
                "instrument",
                "label",
                "group",
                "family",
                "default_velocity",
            }

    def test_entries_are_sorted_by_ascending_note(self):
        kit = DrumKit.create_ezdrummer3_kit()

        notes = [entry["note"] for entry in kit.kit_map()]
        assert notes == sorted(notes)

    def test_group_matches_get_velocity_range_category(self):
        kit = DrumKit.create_gm_drums_kit()

        for entry in kit.kit_map():
            instrument = DrumInstrument[entry["instrument"]]
            expected_default = kit.get_velocity_range(
                instrument
            ).default_velocity
            assert entry["default_velocity"] == expected_default


class TestKitMapDedupesCollapsedArticulations:
    """GM-baseline presets collapse EZDrummer-specific hi-hat
    articulations onto CLOSED_HH/OPEN_HH (see _GM_HIHAT_COLLAPSE) -
    kit_map() must not list the same resolved note twice."""

    def test_gm_kit_map_has_no_duplicate_notes(self):
        kit = DrumKit.create_gm_drums_kit()

        notes = [entry["note"] for entry in kit.kit_map()]
        assert len(notes) == len(set(notes))

    def test_gm_kit_map_keeps_canonical_closed_hihat_not_aliases(self):
        kit = DrumKit.create_gm_drums_kit()

        instruments = {entry["instrument"] for entry in kit.kit_map()}
        assert "CLOSED_HH" in instruments
        for alias in (
            "CLOSED_HH_EDGE",
            "CLOSED_HH_TIP",
            "TIGHT_HH_EDGE",
            "TIGHT_HH_TIP",
        ):
            assert alias not in instruments

    def test_gm_kit_map_keeps_canonical_open_hihat_not_aliases(self):
        kit = DrumKit.create_gm_drums_kit()

        instruments = {entry["instrument"] for entry in kit.kit_map()}
        assert "OPEN_HH" in instruments
        for alias in ("OPEN_HH_1", "OPEN_HH_2", "OPEN_HH_3", "OPEN_HH_MAX"):
            assert alias not in instruments

    def test_ezdrummer3_kit_map_keeps_every_articulation_distinct(self):
        """EZDrummer 3's own preset has no collapse - all 21
        DrumInstrument members resolve to distinct notes."""
        kit = DrumKit.create_ezdrummer3_kit()

        assert len(kit.kit_map()) == len(list(DrumInstrument))


class TestKitMapArticulationFamilies:
    def test_closed_hihat_siblings_share_a_family(self):
        kit = DrumKit.create_ezdrummer3_kit()
        by_instrument = {entry["instrument"]: entry for entry in kit.kit_map()}

        closed_family = by_instrument["CLOSED_HH"]["family"]
        for alias in (
            "CLOSED_HH_EDGE",
            "CLOSED_HH_TIP",
            "TIGHT_HH_EDGE",
            "TIGHT_HH_TIP",
        ):
            assert by_instrument[alias]["family"] == closed_family

    def test_open_hihat_siblings_share_a_family(self):
        kit = DrumKit.create_ezdrummer3_kit()
        by_instrument = {entry["instrument"]: entry for entry in kit.kit_map()}

        open_family = by_instrument["OPEN_HH"]["family"]
        for alias in ("OPEN_HH_1", "OPEN_HH_2", "OPEN_HH_3", "OPEN_HH_MAX"):
            assert by_instrument[alias]["family"] == open_family

    def test_kick_and_snare_do_not_share_a_family(self):
        kit = DrumKit.create_ezdrummer3_kit()
        by_instrument = {entry["instrument"]: entry for entry in kit.kit_map()}

        assert (
            by_instrument["KICK"]["family"] != by_instrument["SNARE"]["family"]
        )


class TestKitMapAcrossAllPresets:
    @pytest.mark.parametrize("preset_name", DrumKit.list_presets().keys())
    def test_every_preset_produces_a_kit_map(self, preset_name):
        kit = DrumKit.from_preset(preset_name)

        entries = kit.kit_map()

        assert entries
        assert all(1 <= entry["note"] <= 127 for entry in entries)
