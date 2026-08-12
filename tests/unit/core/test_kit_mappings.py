"""Tests for per-preset MIDI note mappings (issue #47, AC Group 1)."""

import json

import pytest

from midi_drums.core.models.kit import DrumKit
from midi_drums.core.value_objects.drum_instrument import DrumInstrument


class TestPresetsDivergeOnNoteMapping:
    """`get_midi_note()` must differ across presets for EZDrummer-specific
    articulations - previously every preset resolved identically because
    all `custom_mappings` dicts were empty."""

    @pytest.mark.parametrize(
        "instrument",
        [
            DrumInstrument.CLOSED_HH_EDGE,
            DrumInstrument.CLOSED_HH_TIP,
            DrumInstrument.TIGHT_HH_EDGE,
            DrumInstrument.TIGHT_HH_TIP,
            DrumInstrument.OPEN_HH_1,
            DrumInstrument.OPEN_HH_2,
            DrumInstrument.OPEN_HH_3,
            DrumInstrument.OPEN_HH_MAX,
        ],
    )
    def test_ezdrummer3_and_gm_diverge(self, instrument):
        ez_kit = DrumKit.create_ezdrummer3_kit()
        gm_kit = DrumKit.create_gm_drums_kit()

        assert ez_kit.get_midi_note(instrument) != gm_kit.get_midi_note(
            instrument
        )

    def test_gm_collapses_closed_hihat_family_to_gm_closed_hihat(self):
        gm_kit = DrumKit.create_gm_drums_kit()

        for instrument in (
            DrumInstrument.CLOSED_HH_EDGE,
            DrumInstrument.CLOSED_HH_TIP,
            DrumInstrument.TIGHT_HH_EDGE,
            DrumInstrument.TIGHT_HH_TIP,
        ):
            assert (
                gm_kit.get_midi_note(instrument)
                == DrumInstrument.CLOSED_HH.value
            )

    def test_gm_collapses_open_hihat_family_to_gm_open_hihat(self):
        gm_kit = DrumKit.create_gm_drums_kit()

        for instrument in (
            DrumInstrument.OPEN_HH_1,
            DrumInstrument.OPEN_HH_2,
            DrumInstrument.OPEN_HH_3,
            DrumInstrument.OPEN_HH_MAX,
        ):
            assert (
                gm_kit.get_midi_note(instrument) == DrumInstrument.OPEN_HH.value
            )

    def test_ezdrummer3_still_uses_its_own_extended_articulation_notes(self):
        ez_kit = DrumKit.create_ezdrummer3_kit()

        assert ez_kit.get_midi_note(DrumInstrument.OPEN_HH_MAX) == 60
        assert ez_kit.get_midi_note(DrumInstrument.CLOSED_HH_EDGE) == 22

    def test_shared_instruments_still_agree_across_presets(self):
        ez_kit = DrumKit.create_ezdrummer3_kit()
        gm_kit = DrumKit.create_gm_drums_kit()

        for instrument in (
            DrumInstrument.KICK,
            DrumInstrument.SNARE,
            DrumInstrument.CLOSED_HH,
            DrumInstrument.CRASH,
            DrumInstrument.RIDE,
        ):
            assert ez_kit.get_midi_note(instrument) == gm_kit.get_midi_note(
                instrument
            )


class TestGmBaselinePresetsAreActuallyGmCompliant:
    """Regression coverage: presets whose own docstrings claim GM-standard
    compatibility (studio_drummer3, addictive_drums, bfd3, modo_drums,
    ml_drums) previously shipped an empty custom_mappings dict, silently
    inheriting EZDrummer 3's non-GM extended hi-hat notes instead. They
    must resolve identically to the gm_drums preset."""

    @pytest.mark.parametrize(
        "factory",
        [
            DrumKit.create_studio_drummer3_kit,
            DrumKit.create_addictive_drums_kit,
            DrumKit.create_bfd3_kit,
            DrumKit.create_modo_drums_kit,
            DrumKit.create_ml_drums_kit,
        ],
    )
    def test_matches_gm_drums_note_table(self, factory):
        kit = factory()
        gm_kit = DrumKit.create_gm_drums_kit()

        for instrument in DrumInstrument:
            assert kit.get_midi_note(instrument) == gm_kit.get_midi_note(
                instrument
            )

    def test_presets_do_not_share_a_mutable_mappings_dict(self):
        """Each factory call must get its own custom_mappings dict - a
        shared mutable default would let mutating one preset's mappings
        leak into every other GM-baseline preset."""
        kit_a = DrumKit.create_bfd3_kit()
        kit_a.custom_mappings[DrumInstrument.KICK] = 1

        kit_b = DrumKit.create_modo_drums_kit()

        assert (
            kit_b.get_midi_note(DrumInstrument.KICK)
            == DrumInstrument.KICK.value
        )


class TestDrumKitFromDict:
    """DrumKit.from_dict() lets users supply a fully custom mapping."""

    def test_builds_custom_mappings_from_instrument_names(self):
        kit = DrumKit.from_dict(
            {
                "name": "My Custom Kit",
                "channel": 3,
                "mappings": {"KICK": 35, "SNARE": 40},
            }
        )

        assert kit.name == "My Custom Kit"
        assert kit.channel == 3
        assert kit.get_midi_note(DrumInstrument.KICK) == 35
        assert kit.get_midi_note(DrumInstrument.SNARE) == 40

    def test_defaults_name_and_channel_when_omitted(self):
        kit = DrumKit.from_dict({"mappings": {"KICK": 35}})

        assert kit.name
        assert kit.channel == 9

    def test_unmapped_instruments_fall_back_to_enum_value(self):
        kit = DrumKit.from_dict({"mappings": {"KICK": 35}})

        assert (
            kit.get_midi_note(DrumInstrument.RIDE) == DrumInstrument.RIDE.value
        )

    def test_unknown_instrument_name_raises_value_error(self):
        with pytest.raises(ValueError):
            DrumKit.from_dict({"mappings": {"NOT_A_REAL_INSTRUMENT": 40}})

    def test_instrument_name_lookup_is_case_insensitive(self):
        kit = DrumKit.from_dict({"mappings": {"kick": 35}})

        assert kit.get_midi_note(DrumInstrument.KICK) == 35

    def test_non_numeric_note_value_raises_value_error(self):
        """Regression: int(note) used to be called unguarded, so a
        non-numeric string raised Python's raw int() ValueError and a
        list/dict value raised an undocumented TypeError instead of the
        class's own uniformly-typed ValueError."""
        with pytest.raises(ValueError):
            DrumKit.from_dict({"mappings": {"KICK": "thirty-six"}})

    def test_non_scalar_note_value_raises_value_error_not_type_error(self):
        with pytest.raises(ValueError):
            DrumKit.from_dict({"mappings": {"KICK": [36]}})


class TestDrumKitFromJson:
    """DrumKit.from_json() loads a mapping file from disk."""

    def test_loads_kit_from_json_file(self, tmp_path):
        mapping_path = tmp_path / "custom_kit.json"
        mapping_path.write_text(
            json.dumps(
                {
                    "name": "File Kit",
                    "mappings": {"KICK": 35, "SNARE": 37},
                }
            ),
            encoding="utf-8",
        )

        kit = DrumKit.from_json(mapping_path)

        assert kit.name == "File Kit"
        assert kit.get_midi_note(DrumInstrument.KICK) == 35
        assert kit.get_midi_note(DrumInstrument.SNARE) == 37

    def test_accepts_str_path(self, tmp_path):
        mapping_path = tmp_path / "custom_kit.json"
        mapping_path.write_text(
            json.dumps({"mappings": {"KICK": 30}}), encoding="utf-8"
        )

        kit = DrumKit.from_json(str(mapping_path))

        assert kit.get_midi_note(DrumInstrument.KICK) == 30
