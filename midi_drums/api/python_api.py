"""High-level Python API for drum generation."""

from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path

from ..core.engine import DrumGenerator
from ..models.pattern import Pattern
from ..models.song import Song


class DrumGeneratorAPI:
    """High-level API for drum generation with simplified interface."""

    def __init__(self):
        """Initialize the drum generator API."""
        self.generator = DrumGenerator()

    def create_song(self,
                   genre: str,
                   style: str = "default",
                   tempo: int = 120,
                   name: Optional[str] = None,
                   **kwargs) -> Song:
        """Create a complete song.

        Args:
            genre: Musical genre ('metal', 'rock', 'jazz', etc.)
            style: Style within genre ('death', 'power', etc.)
            tempo: Beats per minute
            name: Song name (auto-generated if None)
            **kwargs: Additional parameters (complexity, humanization, etc.)

        Returns:
            Generated Song object
        """
        song = self.generator.create_song(genre, style, tempo, **kwargs)
        if name:
            song.name = name
        return song

    def generate_pattern(self,
                        genre: str,
                        section: str = "verse",
                        style: str = "default",
                        **kwargs) -> Optional[Pattern]:
        """Generate a single drum pattern.

        Args:
            genre: Musical genre
            section: Song section ('verse', 'chorus', 'bridge', etc.)
            style: Style within genre
            **kwargs: Additional parameters

        Returns:
            Generated Pattern object or None if failed
        """
        return self.generator.generate_pattern(genre, section, style=style, **kwargs)

    def save_as_midi(self, song: Song, filename: Union[str, Path]) -> None:
        """Save song as MIDI file.

        Args:
            song: Song object to save
            filename: Output filename/path
        """
        output_path = Path(filename)
        self.generator.export_midi(song, output_path)

    def save_pattern_as_midi(self, pattern: Pattern, filename: Union[str, Path],
                            tempo: int = 120) -> None:
        """Save pattern as MIDI file.

        Args:
            pattern: Pattern object to save
            filename: Output filename/path
            tempo: Tempo for the MIDI file
        """
        output_path = Path(filename)
        self.generator.export_pattern_midi(pattern, output_path, tempo)

    def list_genres(self) -> List[str]:
        """Get list of available genres."""
        return self.generator.get_available_genres()

    def list_styles(self, genre: str) -> List[str]:
        """Get list of styles for a genre.

        Args:
            genre: Genre name

        Returns:
            List of available styles
        """
        return self.generator.get_styles_for_genre(genre)

    def list_drummers(self) -> List[str]:
        """Get list of available drummers."""
        return self.generator.get_available_drummers()

    def get_song_info(self, song: Song) -> Dict:
        """Get detailed information about a song.

        Args:
            song: Song object

        Returns:
            Dictionary with song information
        """
        return self.generator.get_song_info(song)

    # Convenience methods for common use cases
    def metal_song(self,
                   style: str = "heavy",
                   tempo: int = 155,
                   complexity: float = 0.7) -> Song:
        """Create a metal song with common parameters."""
        return self.create_song(
            genre="metal",
            style=style,
            tempo=tempo,
            complexity=complexity,
            dynamics=0.6,
            humanization=0.3
        )

    def quick_export(self,
                    genre: str,
                    filename: Union[str, Path],
                    style: str = "default",
                    tempo: int = 120) -> None:
        """Quickly generate and export a song.

        Args:
            genre: Musical genre
            filename: Output MIDI filename
            style: Style within genre
            tempo: Beats per minute
        """
        song = self.create_song(genre, style, tempo)
        self.save_as_midi(song, filename)

    def batch_generate(self,
                      specs: List[Dict],
                      output_dir: Union[str, Path]) -> List[Path]:
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
            genre = spec.get('genre', 'metal')
            style = spec.get('style', 'default')
            tempo = spec.get('tempo', 120)
            name = spec.get('name', f"{genre}_{style}_{i:02d}")

            song = self.create_song(genre, style, tempo, name=name, **spec)
            filename = output_path / f"{name}.mid"
            self.save_as_midi(song, filename)
            generated_files.append(filename)

        return generated_files