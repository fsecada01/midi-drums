#!/usr/bin/env python3
"""
Generate a complex death metal song with proper song directory organization.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from midi_drums import DrumGenerator
from midi_drums.api.python_api import DrumGeneratorAPI


class ComplexSongProject:
    """Manages complex song generation with proper directory structure."""

    def __init__(self, song_name: str, base_dir: str = "songs"):
        self.song_name = song_name
        self.base_dir = Path(base_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create project directory with timestamp
        safe_name = "".join(
            c for c in song_name.lower() if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        safe_name = safe_name.replace(" ", "_")
        self.project_dir = self.base_dir / f"{safe_name}_{self.timestamp}"

        # Create subdirectories
        self.sections_dir = self.project_dir / "sections"
        self.complete_dir = self.project_dir / "complete"
        self.stems_dir = self.project_dir / "stems"
        self.metadata_dir = self.project_dir / "metadata"

        # Initialize API and generator
        self.api = DrumGeneratorAPI()
        self.generator = DrumGenerator()

        # Track project data
        self.metadata = {
            "song_name": song_name,
            "generated_at": datetime.now().isoformat(),
            "generator_version": "1.0.0",
            "project_dir": str(self.project_dir),
            "parameters": {},
            "structure": [],
            "files": {},
            "success_count": 0,
            "error_count": 0,
            "errors": [],
        }

    def create_directories(self):
        """Create the project directory structure."""
        print(f"Creating project: {self.project_dir}")

        for directory in [
            self.project_dir,
            self.sections_dir,
            self.complete_dir,
            self.stems_dir,
            self.metadata_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def save_file_safely(
        self, pattern, filepath: Path, tempo: int, section_name: str
    ) -> bool:
        """Save a MIDI file with error handling and metadata tracking."""
        try:
            self.api.save_pattern_as_midi(pattern, filepath, tempo=tempo)

            # Track successful file
            self.metadata["files"][
                str(filepath.relative_to(self.project_dir))
            ] = {
                "section": section_name,
                "tempo": tempo,
                "beats": len(pattern.beats),
                "size_bytes": (
                    filepath.stat().st_size if filepath.exists() else 0
                ),
                "status": "success",
            }
            self.metadata["success_count"] += 1
            return True

        except Exception as e:
            # Track failed file
            error_msg = str(e)
            self.metadata["files"][
                str(filepath.relative_to(self.project_dir))
            ] = {
                "section": section_name,
                "tempo": tempo,
                "status": "failed",
                "error": error_msg,
            }
            self.metadata["errors"].append(f"{section_name}: {error_msg}")
            self.metadata["error_count"] += 1
            print(f"  ! Failed to save {filepath.name}: {error_msg}")
            return False

    def generate_complex_death_metal(self):
        """Generate the complex death metal song with full organization."""
        print(f"GENERATING: {self.song_name}")
        print("=" * 60)

        self.create_directories()

        # Set generation parameters
        params = {
            "death_tempo": 180,
            "doom_tempo": 70,
            "progressive_tempo": 160,
            "complexity": 0.9,
            "humanization": 0.4,
            "primary_drummer": "hoglan",
            "secondary_drummers": ["chambers", "weckl"],
        }
        self.metadata["parameters"] = params

        # Define song structure
        structure = [
            {
                "section": "intro",
                "style": "death",
                "bars": 4,
                "tempo": 180,
                "drummer": "hoglan",
            },
            {
                "section": "verse",
                "style": "death",
                "bars": 8,
                "tempo": 180,
                "drummer": "hoglan",
            },
            {
                "section": "chorus",
                "style": "death",
                "bars": 8,
                "tempo": 180,
                "drummer": "hoglan",
            },
            {
                "section": "verse",
                "style": "death",
                "bars": 8,
                "tempo": 180,
                "drummer": "hoglan",
            },
            {
                "section": "chorus",
                "style": "death",
                "bars": 8,
                "tempo": 180,
                "drummer": "hoglan",
            },
            {
                "section": "breakdown",
                "style": "doom",
                "bars": 8,
                "tempo": 70,
                "drummer": None,
            },
            {
                "section": "bridge",
                "style": "progressive",
                "bars": 6,
                "tempo": 160,
                "drummer": "chambers",
            },
            {
                "section": "bridge",
                "style": "progressive",
                "bars": 6,
                "tempo": 160,
                "drummer": "weckl",
            },
            {
                "section": "verse",
                "style": "death",
                "bars": 8,
                "tempo": 180,
                "drummer": "hoglan",
            },
            {
                "section": "chorus",
                "style": "death",
                "bars": 12,
                "tempo": 180,
                "drummer": "hoglan",
            },
            {
                "section": "outro",
                "style": "death",
                "bars": 4,
                "tempo": 180,
                "drummer": "hoglan",
            },
        ]
        self.metadata["structure"] = structure

        print("PHASE 1: Generating base patterns...")
        base_patterns = {}

        # Generate base patterns for each unique combination
        unique_patterns = set()
        for item in structure:
            pattern_key = (item["section"], item["style"])
            unique_patterns.add(pattern_key)

        for section, style in unique_patterns:
            try:
                pattern = self.api.generate_pattern("metal", section, style)
                if pattern:
                    base_patterns[(section, style)] = pattern
                    print(
                        f"  > {section} ({style}): {len(pattern.beats)} beats"
                    )
                else:
                    print(f"  ! {section} ({style}): Failed to generate")
            except Exception as e:
                print(f"  ! {section} ({style}): Error - {e}")

        print()
        print("PHASE 2: Applying drummer styles...")
        styled_patterns = {}
        drummer_collections = {"hoglan": [], "chambers": [], "weckl": []}

        for item in structure:
            section_key = (item["section"], item["style"])
            drummer = item["drummer"]
            tempo = item["tempo"]

            if section_key in base_patterns:
                base_pattern = base_patterns[section_key]

                if drummer:
                    try:
                        styled_pattern = self.generator.apply_drummer_style(
                            base_pattern, drummer
                        )
                        styled_key = (
                            f"{item['section']}_{item['style']}_{drummer}"
                        )
                        styled_patterns[styled_key] = (
                            styled_pattern,
                            tempo,
                            drummer,
                        )
                        drummer_collections[drummer].append(
                            (styled_key, styled_pattern, tempo)
                        )
                        print(
                            f"  > {styled_key}: {len(styled_pattern.beats)} beats"
                        )
                    except Exception as e:
                        print(f"  ! {styled_key}: Error - {e}")
                else:
                    # No drummer style (like doom break)
                    plain_key = f"{item['section']}_{item['style']}"
                    styled_patterns[plain_key] = (base_pattern, tempo, None)
                    print(f"  > {plain_key}: {len(base_pattern.beats)} beats")

        print()
        print("PHASE 3: Saving organized files...")

        # Save individual sections
        print("Saving sections...")
        section_files = []
        for i, (key, (pattern, tempo, drummer)) in enumerate(
            styled_patterns.items(), 1
        ):
            drummer_suffix = f"_{drummer}" if drummer else ""
            filename = f"{i:02d}_{key}_{tempo}bpm.mid"
            filepath = self.sections_dir / filename

            if self.save_file_safely(pattern, filepath, tempo, key):
                section_files.append(filepath.name)
                print(f"  > Saved: {filename}")

        # Save drummer-specific stems
        print()
        print("Saving drummer stems...")
        for drummer, patterns in drummer_collections.items():
            if patterns:
                stem_filename = f"{drummer}_compilation.mid"
                stem_filepath = self.stems_dir / stem_filename

                # For now, save the first pattern as representative
                # TODO: Could combine multiple patterns into one file
                if patterns:
                    first_pattern = patterns[0][1]  # Get the pattern
                    tempo = patterns[0][2]  # Get the tempo
                    if self.save_file_safely(
                        first_pattern, stem_filepath, tempo, f"{drummer}_stem"
                    ):
                        print(
                            f"  > Saved: {stem_filename} ({len(patterns)} patterns)"
                        )

        # Save complete song attempt
        print()
        print("Creating complete song...")
        try:
            song_structure = [
                (item["section"], item["bars"]) for item in structure
            ]
            complete_song = self.generator.create_song(
                genre="metal",
                style="death",
                tempo=params["death_tempo"],
                structure=song_structure,
                complexity=params["complexity"],
                humanization=params["humanization"],
            )

            if complete_song:
                # Try to apply primary drummer style
                styled_complete = self.generator.apply_drummer_style(
                    complete_song, params["primary_drummer"]
                )
                complete_filepath = (
                    self.complete_dir / "complete_song_180bpm.mid"
                )

                try:
                    self.generator.export_midi(
                        styled_complete, complete_filepath
                    )
                    self.metadata["files"][
                        "complete/complete_song_180bpm.mid"
                    ] = {
                        "section": "complete_song",
                        "tempo": params["death_tempo"],
                        "sections": len(complete_song.sections),
                        "total_beats": sum(
                            len(s.pattern.beats) for s in complete_song.sections
                        ),
                        "status": "success",
                    }
                    print("  > Saved: complete_song_180bpm.mid")
                    print(f"    Sections: {len(complete_song.sections)}")
                except Exception as e:
                    print(f"  ! Complete song export failed: {e}")
            else:
                print("  ! Failed to create complete song")

        except Exception as e:
            print(f"  ! Complete song generation failed: {e}")

        # Generate project documentation
        self.generate_documentation()

        # Save metadata
        self.save_metadata()

        return self.get_project_summary()

    def generate_documentation(self):
        """Generate README and arrangement guide."""
        readme_content = f"""# {self.song_name}

Generated: {self.metadata['generated_at']}
Project Directory: `{self.project_dir.name}/`

## Song Structure

"""

        for i, item in enumerate(self.metadata["structure"], 1):
            readme_content += f"{i:2d}. **{item['section'].title()}** "
            readme_content += f"({item['style']}) - {item['tempo']} BPM"
            if item.get("drummer"):
                readme_content += f" - {item['drummer'].title()} style"
            readme_content += f" ({item['bars']} bars)\n"

        readme_content += f"""

## Files Generated

### Sections (`sections/`)
Individual MIDI files for each song section with tempo and drummer information.

### Stems (`stems/`)
Drummer-specific compilations for easier mixing.

### Complete (`complete/`)
Full song arrangements (where possible).

## DAW Import Instructions

1. **Import sections individually** for maximum control
2. **Apply tempo automation**:
   - Death metal sections: 180 BPM
   - Doom break: 70 BPM
   - Progressive sections: 160 BPM
3. **Consider time signature changes** for progressive parts (7/8, 5/4)
4. **Layer drummer styles** as desired

## Generation Statistics

- **Files successfully generated**: {self.metadata['success_count']}
- **Files with errors**: {self.metadata['error_count']}
- **Total patterns**: {len(self.metadata['structure'])}

## Drummer Styles Implemented

- **Gene Hoglan**: Mechanical precision, blast beats, progressive complexity
- **Dennis Chambers**: Funk mastery, incredible chops (where successful)
- **Dave Weckl**: Linear playing, fusion expertise

---

*Generated by MIDI Drums Generator v{self.metadata['generator_version']}*
"""

        readme_path = self.project_dir / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")

        # Create arrangement guide
        arrangement_content = f"""# Arrangement Guide - {self.song_name}

## Tempo Automation Timeline

0:00 - 0:30  | Intro (Hoglan)           | 180 BPM
0:30 - 1:30  | Verse 1 (Hoglan)         | 180 BPM
1:30 - 2:30  | Chorus 1 (Hoglan)        | 180 BPM
2:30 - 3:30  | Verse 2 (Hoglan)         | 180 BPM
3:30 - 4:30  | Chorus 2 (Hoglan)        | 180 BPM
4:30 - 6:00  | DOOM BREAK               | 70 BPM ⬅ SLOW DOWN
6:00 - 6:45  | Progressive (Chambers)   | 160 BPM
6:45 - 7:30  | Progressive (Weckl)      | 160 BPM
7:30 - 8:30  | Final Verse (Hoglan)     | 180 BPM ⬅ SPEED UP
8:30 - 10:00 | Extended Chorus (Hoglan) | 180 BPM
10:00 - 10:30| Outro (Hoglan)           | 180 BPM

## Mixing Suggestions

- **Death Metal Sections**: Heavy compression, gate for tightness
- **Doom Break**: Reverb, delay, atmospheric processing
- **Progressive**: Clean, detailed, highlight technical elements
- **Transitions**: Use automation to smooth tempo changes

## Time Signature Options

- **Standard sections**: 4/4
- **Progressive sections**: Try 7/8 or 5/4 for complexity
- **Doom break**: 4/4 with half-time feel
"""

        arrangement_path = self.complete_dir / "arrangement_guide.txt"
        arrangement_path.write_text(arrangement_content, encoding="utf-8")

    def save_metadata(self):
        """Save project metadata as JSON."""
        metadata_path = self.metadata_dir / "project_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    def get_project_summary(self) -> dict[str, Any]:
        """Return a summary of the project generation."""
        return {
            "project_dir": self.project_dir,
            "song_name": self.song_name,
            "files_generated": self.metadata["success_count"],
            "files_failed": self.metadata["error_count"],
            "total_structure_items": len(self.metadata["structure"]),
            "metadata": self.metadata,
        }


def main():
    """Generate the organized complex death metal song."""
    project = ComplexSongProject("Epic Complex Death Metal Song")

    result = project.generate_complex_death_metal()

    print()
    print("PROJECT GENERATION COMPLETE!")
    print("=" * 60)
    print(f"Project saved to: {result['project_dir']}")
    print(f"Song name: {result['song_name']}")
    print(f"Files generated: {result['files_generated']}")
    print(f"Files with errors: {result['files_failed']}")
    print()
    print("Directory structure:")
    print(f"  {result['project_dir'].name}/")
    print("  ├── sections/          # Individual MIDI sections")
    print("  ├── complete/          # Full arrangements")
    print("  ├── stems/             # Drummer-specific files")
    print("  ├── metadata/          # JSON metadata")
    print("  ├── README.md          # Project documentation")
    print("  └── arrangement_guide.txt")
    print()
    print("🎵 Ready for DAW import! Check the README.md for instructions.")


if __name__ == "__main__":
    main()
