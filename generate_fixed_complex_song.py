#!/usr/bin/env python3
"""
Generate complex death metal song with MIDI export workaround.
Handles midiutil library issues with overlapping notes.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from midi_drums import DrumGenerator


def safe_export_pattern(generator, pattern, filepath, tempo):
    """Safely export pattern with error handling."""
    try:
        generator.export_pattern_midi(pattern, filepath, tempo)
        return True
    except IndexError as e:
        if "pop from empty list" in str(e):
            print(f"  ⚠️  MIDI export issue (midiutil bug): {filepath.name}")
            return False
        raise
    except Exception as e:
        print(f"  ❌ Export failed: {filepath.name} - {e}")
        return False


def main():
    print("=" * 70)
    print("Epic Complex Death Metal Song - Fixed Generation")
    print("=" * 70)
    print()

    # Setup
    generator = DrumGenerator()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = f"epic_complex_death_metal_song_{timestamp}"
    project_dir = Path("songs") / project_name

    # Create directories
    sections_dir = project_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "song_name": "Epic Complex Death Metal Song",
        "generated_at": datetime.now().isoformat(),
        "generator_version": "1.0.0 (fixed)",
        "project_dir": str(project_dir),
        "files": {},
        "success_count": 0,
        "error_count": 0,
    }

    # Define song structure with context blending
    # Progressive sections get 30% metal context for cohesion
    structure = [
        {
            "section": "intro",
            "style": "death",
            "bars": 4,
            "tempo": 180,
            "drummer": "hoglan",
            "context_blend": 0.0,  # Pure death metal
        },
        {
            "section": "verse",
            "style": "death",
            "bars": 8,
            "tempo": 180,
            "drummer": "hoglan",
            "context_blend": 0.0,
        },
        {
            "section": "chorus",
            "style": "death",
            "bars": 8,
            "tempo": 180,
            "drummer": "hoglan",
            "context_blend": 0.0,
        },
        {
            "section": "breakdown",
            "style": "doom",
            "bars": 8,
            "tempo": 70,
            "drummer": None,
            "context_blend": 0.2,  # Slight metal context for doom
        },
        {
            "section": "bridge",
            "style": "progressive",
            "bars": 6,
            "tempo": 160,
            "drummer": "chambers",
            "context_blend": 0.3,  # Metal-adapted progressive
        },
        {
            "section": "bridge",
            "style": "progressive",
            "bars": 6,
            "tempo": 160,
            "drummer": "weckl",
            "context_blend": 0.3,  # Metal-adapted progressive
        },
        {
            "section": "outro",
            "style": "death",
            "bars": 4,
            "tempo": 180,
            "drummer": "hoglan",
            "context_blend": 0.0,
        },
    ]

    print("Phase 1: Generating patterns...")
    print()

    # Generate and save each section
    for i, item in enumerate(structure, 1):
        section = item["section"]
        style = item["style"]
        bars = item["bars"]
        tempo = item["tempo"]
        drummer = item["drummer"]
        context_blend = item.get("context_blend", 0.0)

        # Generate pattern with metal context adaptation
        pattern = generator.generate_pattern(
            genre="metal",
            section=section,
            style=style,
            bars=bars,
            drummer=drummer,
            song_genre_context="metal",  # Overall song is metal
            context_blend=context_blend,  # Blend amount per section
        )

        if not pattern:
            print(f"{i:02d}. ❌ Failed to generate: {section}_{style}")
            metadata["error_count"] += 1
            continue

        # Build filename
        drummer_suffix = f"_{drummer}" if drummer else ""
        blend_suffix = (
            f"_ctx{int(context_blend*100)}" if context_blend > 0 else ""
        )
        filename = f"{i:02d}_{section}_{style}{drummer_suffix}{blend_suffix}_{tempo}bpm.mid"
        filepath = sections_dir / filename

        # Export
        context_info = (
            f" [metal context {int(context_blend*100)}%]"
            if context_blend > 0
            else ""
        )
        print(
            f"{i:02d}. {section}_{style}{drummer_suffix} "
            f"@ {tempo} BPM ({len(pattern.beats)} beats){context_info}..."
        )

        if safe_export_pattern(generator, pattern, filepath, tempo):
            print(f"     ✅ Saved: {filename}")
            metadata["files"][filename] = {
                "section": f"{section}_{style}{drummer_suffix}",
                "tempo": tempo,
                "bars": bars,
                "beats": len(pattern.beats),
                "status": "success",
            }
            metadata["success_count"] += 1
        else:
            print("     ❌ Export failed (midiutil issue)")
            metadata["files"][filename] = {
                "section": f"{section}_{style}{drummer_suffix}",
                "tempo": tempo,
                "status": "failed",
                "error": "MIDI export issue",
            }
            metadata["error_count"] += 1

    # Save metadata
    metadata_file = project_dir / "project_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print()
    print("=" * 70)
    print("Generation Complete")
    print("=" * 70)
    print(f"Project: {project_dir}")
    print(f"Success: {metadata['success_count']} files")
    print(f"Errors:  {metadata['error_count']} files")
    print()
    print("Note: Some export errors are due to midiutil library limitations,")
    print("      not the pattern generation (which is working correctly).")
    print("=" * 70)


if __name__ == "__main__":
    main()
