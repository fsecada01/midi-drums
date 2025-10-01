#!/usr/bin/env python3
"""
Generate a complex death metal song with multiple drummers, tempo changes, and progressive sections.

Song structure:
- [intro, verse, bridge, chorus] x 2
- Break (doom metal, slow)
- Progressive sections (Chambers + Weckl inspired)
- Final [verse, bridge, extended chorus]
- Dedicated ending
"""

from pathlib import Path

from midi_drums import DrumGenerator
from midi_drums.api.python_api import DrumGeneratorAPI


def create_complex_death_metal_song():
    """Create the complex song as specified."""
    print("GENERATING COMPLEX DEATH METAL SONG")
    print("=" * 50)

    api = DrumGeneratorAPI()
    generator = DrumGenerator()

    # Song parameters
    base_tempo = 180  # Death metal tempo
    slow_tempo = 70  # Doom break tempo
    prog_tempo = 160  # Progressive tempo

    print(f"Base tempo: {base_tempo} BPM")
    print(f"Doom break tempo: {slow_tempo} BPM")
    print(f"Progressive tempo: {prog_tempo} BPM")
    print()

    # Generate individual sections
    sections = []

    print("GENERATING DEATH METAL SECTIONS WITH HOGLAN STYLE...")

    # Main death metal sections (Hoglan style)
    intro = api.generate_pattern("metal", "intro", "death")
    verse = api.generate_pattern("metal", "verse", "death")
    bridge = api.generate_pattern("metal", "bridge", "death")
    chorus = api.generate_pattern("metal", "chorus", "death")

    # Apply Hoglan style to main sections
    if intro:
        intro_hoglan = generator.apply_drummer_style(intro, "hoglan")
        print(f"  > Intro: {len(intro_hoglan.beats)} beats with Hoglan style")

    if verse:
        verse_hoglan = generator.apply_drummer_style(verse, "hoglan")
        print(f"  > Verse: {len(verse_hoglan.beats)} beats with Hoglan style")

    if bridge:
        bridge_hoglan = generator.apply_drummer_style(bridge, "hoglan")
        print(f"  > Bridge: {len(bridge_hoglan.beats)} beats with Hoglan style")

    if chorus:
        chorus_hoglan = generator.apply_drummer_style(chorus, "hoglan")
        print(f"  > Chorus: {len(chorus_hoglan.beats)} beats with Hoglan style")

    print()
    print("GENERATING DOOM BREAK SECTION...")

    # Doom break section
    doom_break = api.generate_pattern("metal", "breakdown", "doom")
    if doom_break:
        print(f"  > Doom break: {len(doom_break.beats)} beats")

    print()
    print("GENERATING PROGRESSIVE SECTIONS...")

    # Progressive sections with different drummer influences
    prog_base = api.generate_pattern("metal", "verse", "progressive")

    if prog_base:
        # Chambers-inspired progressive section
        prog_chambers = generator.apply_drummer_style(prog_base, "chambers")
        print(f"  > Progressive (Chambers): {len(prog_chambers.beats)} beats")

        # Weckl-inspired progressive section
        prog_weckl = generator.apply_drummer_style(prog_base, "weckl")
        print(f"  > Progressive (Weckl): {len(prog_weckl.beats)} beats")

    print()
    print("GENERATING FINALE SECTIONS...")

    # Extended chorus and ending
    extended_chorus = api.generate_pattern("metal", "chorus", "death")
    ending = api.generate_pattern("metal", "outro", "death")

    if extended_chorus:
        extended_chorus_hoglan = generator.apply_drummer_style(
            extended_chorus, "hoglan"
        )
        print(f"  > Extended chorus: {len(extended_chorus_hoglan.beats)} beats")

    if ending:
        ending_hoglan = generator.apply_drummer_style(ending, "hoglan")
        print(f"  > Ending: {len(ending_hoglan.beats)} beats")

    print()
    print("SAVING INDIVIDUAL SECTIONS...")

    # Save individual sections
    output_dir = Path("complex_song_sections")
    output_dir.mkdir(exist_ok=True)

    sections_to_save = [
        (intro_hoglan, "01_intro_hoglan.mid"),
        (verse_hoglan, "02_verse_hoglan.mid"),
        (bridge_hoglan, "03_bridge_hoglan.mid"),
        (chorus_hoglan, "04_chorus_hoglan.mid"),
        (doom_break, "05_doom_break.mid"),
        (prog_chambers, "06_progressive_chambers.mid"),
        (prog_weckl, "07_progressive_weckl.mid"),
        (extended_chorus_hoglan, "08_extended_chorus_hoglan.mid"),
        (ending_hoglan, "09_ending_hoglan.mid"),
    ]

    for i, (pattern, filename) in enumerate(sections_to_save, 1):
        if pattern:
            file_path = output_dir / filename
            # Save with appropriate tempo for each section
            if "doom" in filename:
                api.save_pattern_as_midi(pattern, file_path, tempo=slow_tempo)
            elif "progressive" in filename:
                api.save_pattern_as_midi(pattern, file_path, tempo=prog_tempo)
            else:
                api.save_pattern_as_midi(pattern, file_path, tempo=base_tempo)
            print(f"  {i:2d}. Saved: {filename}")

    print()
    print("CREATING COMPLETE SONG STRUCTURE...")

    # Create the complete song using DrumGenerator for custom structure
    # Note: This creates the structure, but individual tempo changes would need
    # to be handled in post-production or with a more advanced MIDI editor

    song_structure = [
        # First cycle
        ("intro", 4),  # Intro
        ("verse", 8),  # Verse 1
        ("bridge", 4),  # Bridge 1
        ("chorus", 8),  # Chorus 1
        # Second cycle
        ("verse", 8),  # Verse 2
        ("bridge", 4),  # Bridge 2
        ("chorus", 8),  # Chorus 2
        # Doom break
        ("breakdown", 8),  # Doom break (slow)
        # Progressive sections
        ("verse", 6),  # Progressive 1 (would be Chambers style)
        ("bridge", 6),  # Progressive 2 (would be Weckl style)
        # Final sections
        ("verse", 8),  # Final verse
        ("bridge", 4),  # Final bridge
        ("chorus", 12),  # Extended chorus
        ("outro", 4),  # Ending
    ]

    complete_song = generator.create_song(
        genre="metal",
        style="death",
        tempo=base_tempo,
        structure=song_structure,
        complexity=0.9,
        humanization=0.4,
    )

    if complete_song:
        # Apply Hoglan style to the complete song
        styled_song = generator.apply_drummer_style(complete_song, "hoglan")
        output_path = "complex_death_metal_song_complete.mid"
        generator.export_midi(styled_song, output_path)
        print(f"  > Complete song: {output_path}")
        print(f"    Sections: {len(complete_song.sections)}")
        total_beats = sum(
            len(section.pattern.beats) for section in complete_song.sections
        )
        print(f"    Total beats: {total_beats}")

    print()
    print("SONG STRUCTURE SUMMARY:")
    print("=" * 50)
    print("1. Intro (Hoglan) - 180 BPM")
    print("2. Verse 1 (Hoglan) - 180 BPM")
    print("3. Bridge 1 (Hoglan) - 180 BPM")
    print("4. Chorus 1 (Hoglan) - 180 BPM")
    print("5. Verse 2 (Hoglan) - 180 BPM")
    print("6. Bridge 2 (Hoglan) - 180 BPM")
    print("7. Chorus 2 (Hoglan) - 180 BPM")
    print("8. DOOM BREAK - 70 BPM")
    print("9. Progressive (Chambers style) - 160 BPM")
    print("10. Progressive (Weckl style) - 160 BPM")
    print("11. Final Verse (Hoglan) - 180 BPM")
    print("12. Final Bridge (Hoglan) - 180 BPM")
    print("13. Extended Chorus (Hoglan) - 180 BPM")
    print("14. Ending (Hoglan) - 180 BPM")
    print()
    print("GENERATION COMPLETE!")
    print(f"Individual sections saved to: {output_dir}")
    print("Import into your DAW and arrange with tempo changes!")
    print()
    print("TIPS FOR DAW ARRANGEMENT:")
    print(
        "- Apply tempo automation: 180 BPM -> 70 BPM (doom) -> 160 BPM (prog) -> 180 BPM"
    )
    print(
        "- Consider time signature changes for progressive sections (7/8, 5/4)"
    )
    print("- Layer the individual sections for precise control")
    print("- Add reverb/delay effects to the doom break section")


if __name__ == "__main__":
    create_complex_death_metal_song()
