"""High-level Python API for drum generation."""

from pathlib import Path
from typing import Dict, List, Optional, Union

from midi_drums.core.engine import DrumGenerator
from midi_drums.models.kit import DrumKit
from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Song


class DrumGeneratorAPI:
    """High-level API for drum generation with simplified interface."""

    def __init__(self):
        """Initialize the drum generator API."""
        self.generator = DrumGenerator()

    def create_song(
        self,
        genre: str,
        style: str = "default",
        tempo: int = 120,
        name: str | None = None,
        mapping: str = "ezdrummer3",
        **kwargs,
    ) -> Song:
        """Create a complete song.

        Args:
            genre: Musical genre ('metal', 'rock', 'jazz', etc.)
            style: Style within genre ('death', 'power', etc.)
            tempo: Beats per minute
            name: Song name (auto-generated if None)
            mapping: MIDI mapping preset ('ezdrummer3', 'gm_drums', etc.)
            **kwargs: Additional parameters (complexity, humanization, etc.)

        Returns:
            Generated Song object
        """
        # Create drum kit from mapping preset
        drum_kit = DrumKit.from_preset(mapping)
        kwargs["drum_kit"] = drum_kit

        song = self.generator.create_song(genre, style, tempo, **kwargs)
        if name:
            song.name = name
        return song

    def generate_pattern(
        self,
        genre: str,
        section: str = "verse",
        style: str = "default",
        mapping: str = "ezdrummer3",
        **kwargs,
    ) -> Pattern | None:
        """Generate a single drum pattern.

        Args:
            genre: Musical genre
            section: Song section ('verse', 'chorus', 'bridge', etc.)
            style: Style within genre
            mapping: MIDI mapping preset ('ezdrummer3', 'gm_drums', etc.)
            **kwargs: Additional parameters

        Returns:
            Generated Pattern object or None if failed
        """
        return self.generator.generate_pattern(
            genre, section, style=style, **kwargs
        )

    def save_as_midi(self, song: Song, filename: str | Path) -> None:
        """Save song as MIDI file.

        Args:
            song: Song object to save
            filename: Output filename/path
        """
        output_path = Path(filename)
        self.generator.export_midi(song, output_path)

    def save_pattern_as_midi(
        self,
        pattern: Pattern,
        filename: str | Path,
        tempo: int = 120,
        mapping: str = "ezdrummer3",
    ) -> None:
        """Save pattern as MIDI file.

        Args:
            pattern: Pattern object to save
            filename: Output filename/path
            tempo: Tempo for the MIDI file
            mapping: MIDI mapping preset for export
        """
        output_path = Path(filename)
        drum_kit = DrumKit.from_preset(mapping)
        self.generator.export_pattern_midi(
            pattern, output_path, tempo, drum_kit=drum_kit
        )

    def list_genres(self) -> list[str]:
        """Get list of available genres."""
        return self.generator.get_available_genres()

    def list_styles(self, genre: str) -> list[str]:
        """Get list of styles for a genre.

        Args:
            genre: Genre name

        Returns:
            List of available styles
        """
        return self.generator.get_styles_for_genre(genre)

    def list_drummers(self) -> list[str]:
        """Get list of available drummers."""
        return self.generator.get_available_drummers()

    def list_mappings(self) -> dict[str, str]:
        """Get list of available MIDI mapping presets.

        Returns:
            Dictionary mapping preset names to descriptions
        """
        return DrumKit.list_presets()

    def get_song_info(self, song: Song) -> dict:
        """Get detailed information about a song.

        Args:
            song: Song object

        Returns:
            Dictionary with song information
        """
        return self.generator.get_song_info(song)

    # Convenience methods for common use cases
    def metal_song(
        self,
        style: str = "heavy",
        tempo: int = 155,
        complexity: float = 0.7,
        mapping: str = "ezdrummer3",
    ) -> Song:
        """Create a metal song with common parameters."""
        return self.create_song(
            genre="metal",
            style=style,
            tempo=tempo,
            complexity=complexity,
            dynamics=0.6,
            humanization=0.3,
            mapping=mapping,
        )

    def quick_export(
        self,
        genre: str,
        filename: str | Path,
        style: str = "default",
        tempo: int = 120,
        mapping: str = "ezdrummer3",
    ) -> None:
        """Quickly generate and export a song.

        Args:
            genre: Musical genre
            filename: Output MIDI filename
            style: Style within genre
            tempo: Beats per minute
            mapping: MIDI mapping preset
        """
        song = self.create_song(genre, style, tempo, mapping=mapping)
        self.save_as_midi(song, filename)

    def batch_generate(
        self, specs: list[dict], output_dir: str | Path
    ) -> list[Path]:
        """Generate multiple songs from specifications.

        Args:
            specs: List of song specification dictionaries
            output_dir: Directory to save files

        Returns:
            List of generated file paths

        Example:
            specs = [
                {'genre': 'metal', 'style': 'death', 'tempo': 180},
                {'genre': 'metal', 'style': 'power', 'tempo': 140}
            ]
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        generated_files = []

        for i, spec in enumerate(specs):
            genre = spec.get("genre", "metal")
            style = spec.get("style", "default")
            tempo = spec.get("tempo", 120)
            name = spec.get("name", f"{genre}_{style}_{i:02d}")

            song = self.create_song(genre, style, tempo, name=name, **spec)
            filename = output_path / f"{name}.mid"
            self.save_as_midi(song, filename)
            generated_files.append(filename)

        return generated_files
