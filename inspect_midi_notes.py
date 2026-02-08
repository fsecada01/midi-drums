"""Inspect MIDI note numbers in a generated file."""

from collections import Counter
from pathlib import Path

import mido


def inspect_midi_file(midi_path: Path):
    """Inspect all note numbers in a MIDI file."""
    midi = mido.MidiFile(midi_path)

    note_counts = Counter()

    for track in midi.tracks:
        for msg in track:
            if msg.type == "note_on" and msg.velocity > 0:
                note_counts[msg.note] += 1

    print(f"\nInspecting: {midi_path.name}")
    print("=" * 60)
    print("\nMIDI Notes Found:")
    for note in sorted(note_counts.keys()):
        count = note_counts[note]
        print(f"  Note {note:3d}: {count:4d} hits")

    # Check specifically for hi-hat notes
    hihat_notes = {
        22: "Closed Edge (EZD)",
        42: "Closed (GM)",
        44: "Pedal",
        46: "Open (GM)",
        60: "Open Max (EZD)",
        61: "Closed Tip (EZD)",
    }

    print("\nHi-Hat Check:")
    for note, desc in hihat_notes.items():
        if note in note_counts:
            print(f"  ✓ Note {note} ({desc}): {note_counts[note]} hits")
        else:
            print(f"  ✗ Note {note} ({desc}): NOT FOUND")


if __name__ == "__main__":
    # Inspect the complete song
    song_path = Path(
        "output/doom_blues_composite_20251028/doom_blues_composite_complete.mid"
    )
    inspect_midi_file(song_path)

    # Also check a verse section
    verse_path = Path(
        "output/doom_blues_composite_20251028/sections/doom_blues_composite_section_02_verse.mid"
    )
    if verse_path.exists():
        inspect_midi_file(verse_path)
