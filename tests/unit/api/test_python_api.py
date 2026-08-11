"""Tests for DrumGeneratorAPI (midi_drums.api.python_api).

Regression coverage for the batch_generate() key-collision bug fixed
alongside the #13 docs/tests phase: a spec dict containing an explicit
'name' (or 'genre'/'style'/'tempo') key used to raise TypeError, because
those keys were forwarded twice - once as an explicit kwarg, once via
**spec.
"""

from midi_drums.api.python_api import DrumGeneratorAPI


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
