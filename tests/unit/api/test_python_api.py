"""Tests for DrumGeneratorAPI (midi_drums.api.python_api).

Regression coverage for the batch_generate() key-collision bug fixed
alongside the #13 docs/tests phase: a spec dict containing an explicit
'name' (or 'genre'/'style'/'tempo') key used to raise TypeError, because
those keys were forwarded twice - once as an explicit kwarg, once via
**spec.
"""

from midi_drums.api.python_api import DrumGeneratorAPI
from midi_drums.core.models.kit import DrumKit


class TestCreateSongDrumKitPrecedence:
    """Regression coverage for #24: create_song() used to always rebuild
    a DrumKit from `mapping` and clobber any caller-supplied `drum_kit`
    kwarg. An explicit drum_kit must now take precedence over mapping."""

    def test_explicit_drum_kit_takes_precedence_over_mapping(self):
        api = DrumGeneratorAPI()
        custom_kit = DrumKit.create_jazz_kit()

        api.create_song(
            "metal",
            "heavy",
            tempo=140,
            mapping="ezdrummer3",
            drum_kit=custom_kit,
        )

        assert api.generator.drum_kit.name == "Jazz Kit"

    def test_mapping_alone_still_works_unchanged(self):
        api = DrumGeneratorAPI()

        api.create_song("metal", "heavy", tempo=140, mapping="ezdrummer3")

        assert api.generator.drum_kit.name == "EZDrummer 3 Kit"

    def test_mapping_default_used_when_neither_arg_given(self):
        api = DrumGeneratorAPI()

        api.create_song("metal", "heavy", tempo=140)

        assert api.generator.drum_kit.name == "EZDrummer 3 Kit"

    def test_explicit_none_drum_kit_falls_back_to_mapping(self):
        """A caller-supplied drum_kit=None must not be treated as an
        explicit choice - it should fall back to mapping instead of
        leaving the generator's previous drum_kit in place."""
        api = DrumGeneratorAPI()
        api.create_song(
            "metal",
            "heavy",
            tempo=140,
            mapping="ezdrummer3",
            drum_kit=DrumKit.create_jazz_kit(),
        )
        assert api.generator.drum_kit.name == "Jazz Kit"

        api.create_song(
            "metal",
            "heavy",
            tempo=140,
            mapping="ezdrummer3",
            drum_kit=None,
        )

        assert api.generator.drum_kit.name == "EZDrummer 3 Kit"

    def test_batch_generate_forwards_explicit_drum_kit(self, tmp_path):
        api = DrumGeneratorAPI()
        specs = [
            {
                "genre": "metal",
                "style": "heavy",
                "tempo": 140,
                "name": "custom_kit_song",
                "drum_kit": DrumKit.create_jazz_kit(),
            }
        ]

        generated_files = api.batch_generate(specs, tmp_path)

        assert len(generated_files) == 1
        assert generated_files[0].exists()
        assert api.generator.drum_kit.name == "Jazz Kit"


class TestBatchGenerate:
    def test_batch_generate_with_explicit_name_in_spec(self, tmp_path):
        """The method's own docstring example passes 'name' in each spec -
        this must not raise TypeError: got multiple values for 'name'."""
        api = DrumGeneratorAPI()
        specs = [
            {
                "genre": "metal",
                "style": "heavy",
                "tempo": 140,
                "name": "heavy_metal",
            },
            {
                "genre": "metal",
                "style": "death",
                "tempo": 180,
                "name": "death_metal",
            },
        ]

        generated_files = api.batch_generate(specs, tmp_path)

        assert len(generated_files) == 2
        assert {f.name for f in generated_files} == {
            "heavy_metal.mid",
            "death_metal.mid",
        }
        assert all(f.exists() for f in generated_files)

    def test_batch_generate_without_explicit_name_in_spec(self, tmp_path):
        """Specs without 'name' still get an auto-generated one."""
        api = DrumGeneratorAPI()
        specs = [{"genre": "metal", "style": "power", "tempo": 160}]

        generated_files = api.batch_generate(specs, tmp_path)

        assert len(generated_files) == 1
        assert generated_files[0].name == "metal_power_00.mid"
        assert generated_files[0].exists()

    def test_batch_generate_forwards_extra_kwargs(self, tmp_path):
        """Non-collision kwargs (e.g. complexity) still reach create_song."""
        api = DrumGeneratorAPI()
        specs = [
            {
                "genre": "metal",
                "style": "heavy",
                "tempo": 140,
                "name": "complex_song",
                "complexity": 0.9,
            }
        ]

        generated_files = api.batch_generate(specs, tmp_path)

        assert len(generated_files) == 1
        assert generated_files[0].exists()
