#!/usr/bin/env python3
"""Advanced example: Reaper export with custom options."""

from pathlib import Path

from midi_drums import DrumGenerator
from midi_drums.exporters import ReaperExporter


def export_multiple_genres():
    """Export multiple songs in different genres."""
    print("Exporting multiple genres...")

    generator = DrumGenerator()
    exporter = ReaperExporter()

    genres = [
        ("metal", "doom", 120),
        ("metal", "death", 180),
        ("rock", "classic", 140),
        ("jazz", "swing", 110),
    ]

    for genre, style, tempo in genres:
        print(f"  - {genre}/{style} @ {tempo} BPM...")

        song = generator.create_song(
            genre=genre,
            style=style,
            tempo=tempo,
            structure=[
                ("intro", 4),
                ("verse", 8),
                ("chorus", 8),
            ],
        )

        filename = f"{genre}_{style}_{tempo}bpm.rpp"
        exporter.export_with_markers(song=song, output_rpp=f"output/{filename}")

    print("  [OK] Exported all genres")


def export_with_template():
    """Export using existing Reaper template."""
    print("\nExporting with custom template...")

    # First, create a template project
    from midi_drums.engines.reaper_engine import ReaperEngine

    engine = ReaperEngine()
    template = engine.create_minimal_project(tempo=140)

    # Add some custom settings to template
    # (In real use, you'd have a pre-made template)
    template_path = "output/my_template.rpp"
    engine.save_project(template, template_path)
    print(f"  [OK] Created template: {template_path}")

    # Now use that template
    generator = DrumGenerator()
    song = generator.create_song(
        genre="metal",
        style="heavy",
        tempo=155,
        structure=[
            ("intro", 4),
            ("verse", 8),
        ],
    )

    exporter = ReaperExporter()
    exporter.export_with_markers(
        song=song,
        input_rpp=template_path,
        output_rpp="output/from_template.rpp",
    )

    print("  [OK] Exported using template (template unchanged)")


def export_with_custom_structure():
    """Export song with custom section structure."""
    print("\nExporting with complex structure...")

    generator = DrumGenerator()

    # Create a complex progressive metal song
    song = generator.create_song(
        genre="metal",
        style="progressive",
        tempo=155,
        structure=[
            ("intro", 2),
            ("verse", 8),
            ("pre_chorus", 4),
            ("chorus", 8),
            ("verse", 8),
            ("pre_chorus", 4),
            ("chorus", 8),
            ("bridge", 8),  # Extended bridge
            ("breakdown", 4),
            ("guitar_solo", 8),
            ("chorus", 8),
            ("outro", 4),
        ],
        complexity=0.9,  # High complexity for prog metal
    )

    exporter = ReaperExporter()
    exporter.export_with_markers(
        song=song, output_rpp="output/progressive_metal_complex.rpp"
    )

    print(f"  [OK] Exported {len(song.sections)} sections")
    print(
        f"  [OK] Total duration: ~{sum(s.bars for s in song.sections) * 4 / song.tempo * 60:.1f} seconds"
    )


def main():
    print("=" * 70)
    print("REAPER EXPORT - ADVANCED EXAMPLES")
    print("=" * 70)

    # Create output directory
    Path("output").mkdir(exist_ok=True)

    # Run all examples
    export_multiple_genres()
    export_with_template()
    export_with_custom_structure()

    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETE!")
    print("=" * 70)
    print("\nCheck the output/ directory for generated files")


if __name__ == "__main__":
    main()
