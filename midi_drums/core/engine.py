"""Main drum generation engine and composition system."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from midi_drums.engines.midi_engine import MIDIEngine
from midi_drums.models.kit import DrumKit
from midi_drums.models.pattern import Pattern
from midi_drums.models.song import GenerationParameters, Section, Song
from midi_drums.plugins.base import PluginManager

logger = logging.getLogger(__name__)


class DrumGenerator:
    """Main drum generation engine."""

    def __init__(self, config_path: Path | None = None):
        """Initialize drum generator with optional configuration."""
        self.plugin_manager = PluginManager()
        self.drum_kit = DrumKit.create_ezdrummer3_kit()
        self.midi_engine = MIDIEngine(self.drum_kit)

        # Load plugins
        self._load_plugins()

    def _load_plugins(self) -> None:
        """Load all available plugins."""
        try:
            self.plugin_manager.discover_plugins()
            logger.info(
                f"Loaded genres: {self.plugin_manager.get_available_genres()}"
            )
            logger.info(
                f"Loaded drummers: {self.plugin_manager.get_available_drummers()}"
            )
        except Exception as e:
            logger.error(f"Failed to load plugins: {e}")

    def create_song(
        self,
        genre: str,
        style: str = "default",
        tempo: int = 120,
        structure: list[tuple[str, int]] | None = None,
        drum_kit: DrumKit | None = None,
        **kwargs,
    ) -> Song:
        """Create a complete song structure.

        Args:
            genre: Genre name (e.g., 'metal', 'rock', 'jazz')
            style: Style within genre (e.g., 'death', 'power' for metal)
            tempo: Tempo in BPM
            structure: List of (section_name, bars) tuples. If None, uses default structure.
            drum_kit: Optional DrumKit for MIDI mapping. If None, uses current kit.
            **kwargs: Additional parameters for GenerationParameters

        Returns:
            Complete Song object with generated patterns
        """
        # Update MIDI engine if new drum kit provided
        if drum_kit:
            self.midi_engine = MIDIEngine(drum_kit)
            self.drum_kit = drum_kit

        # Create generation parameters
        params = GenerationParameters(genre=genre, style=style, **kwargs)

        # Use default structure if none provided
        if structure is None:
            structure = [
                ("intro", 4),
                ("verse", 8),
                ("chorus", 8),
                ("verse", 8),
                ("chorus", 8),
                ("bridge", 4),
                ("chorus", 8),
                ("outro", 4),
            ]

        # Create song with basic structure
        song = Song(
            name=f"{genre}_{style}_song", tempo=tempo, global_parameters=params
        )

        # Generate patterns for each section
        for section_name, bars in structure:
            pattern = self.generate_pattern(
                genre, section_name, bars, style=style, **kwargs
            )
            if pattern:
                section = Section(section_name, pattern, bars)

                # Add variations and fills based on complexity
                if params.complexity > 0.5:
                    variations = self._generate_variations(pattern, params)
                    section.variations.extend(variations)

                fills = self._generate_fills(genre, params)
                section.fills.extend(fills)

                song.add_section(section)
            else:
                logger.warning(
                    f"Failed to generate pattern for {genre}/{section_name}"
                )

        return song

    def generate_pattern(
        self, genre: str, section: str = "verse", bars: int = 4, **kwargs
    ) -> Pattern | None:
        """Generate a single pattern.

        Args:
            genre: Genre name
            section: Section type
            bars: Number of bars (for multi-bar patterns)
            **kwargs: Additional generation parameters

        Returns:
            Generated Pattern or None if generation failed
        """
        # Create parameters
        params = GenerationParameters(genre=genre, **kwargs)

        # Generate base pattern
        pattern = self.plugin_manager.generate_pattern(genre, section, params)
        if not pattern:
            return None

        # Apply drummer style if specified
        if params.drummer:
            styled_pattern = self.plugin_manager.apply_drummer_style(
                pattern, params.drummer
            )
            if styled_pattern:
                pattern = styled_pattern

        # Apply humanization if requested
        if params.humanization > 0:
            timing_var = params.humanization * 0.05  # Scale to reasonable range
            velocity_var = int(params.humanization * 20)
            pattern = pattern.humanize(timing_var, velocity_var)

        # Extend pattern for multiple bars if needed
        if bars > 1:
            pattern = self._extend_pattern_to_bars(pattern, bars)

        return pattern

    def apply_drummer_style(
        self, pattern: Pattern, drummer: str
    ) -> Pattern | None:
        """Apply drummer-specific style modifications to a pattern."""
        return self.plugin_manager.apply_drummer_style(pattern, drummer)

    def export_midi(self, song: Song, output_path: Path) -> None:
        """Export song as MIDI file."""
        self.midi_engine.save_song_midi(song, output_path)
        logger.info(f"Exported MIDI to: {output_path}")

    def export_pattern_midi(
        self,
        pattern: Pattern,
        output_path: Path,
        tempo: int = 120,
        drum_kit: DrumKit | None = None,
    ) -> None:
        """Export single pattern as MIDI file."""
        # Use provided drum kit or current one
        engine = self.midi_engine
        if drum_kit:
            engine = MIDIEngine(drum_kit)

        engine.save_pattern_midi(pattern, output_path, tempo)
        logger.info(f"Exported pattern MIDI to: {output_path}")

    def get_available_genres(self) -> list[str]:
        """Get list of available genres."""
        return self.plugin_manager.get_available_genres()

    def get_available_drummers(self) -> list[str]:
        """Get list of available drummers."""
        return self.plugin_manager.get_available_drummers()

    def get_styles_for_genre(self, genre: str) -> list[str]:
        """Get available styles for a genre."""
        return self.plugin_manager.get_styles_for_genre(genre)

    def get_song_info(self, song: Song) -> dict:
        """Get comprehensive information about a song."""
        info = self.midi_engine.get_midi_info(song)
        info.update(
            {
                "genre": (
                    song.global_parameters.genre
                    if song.global_parameters
                    else "unknown"
                ),
                "style": (
                    song.global_parameters.style
                    if song.global_parameters
                    else "default"
                ),
                "drummer": (
                    song.global_parameters.drummer
                    if song.global_parameters
                    else None
                ),
                "sections_count": len(song.sections),
                "unique_sections": list({s.name for s in song.sections}),
            }
        )
        return info

    def set_drum_kit(self, kit: DrumKit) -> None:
        """Set the drum kit configuration."""
        self.drum_kit = kit
        self.midi_engine = MIDIEngine(kit)

    def create_drum_kit(self, kit_type: str) -> DrumKit:
        """Create a drum kit configuration by type."""
        kit_creators = {
            "ezdrummer3": DrumKit.create_ezdrummer3_kit,
            "metal": DrumKit.create_metal_kit,
            "jazz": DrumKit.create_jazz_kit,
            "standard": DrumKit.create_ezdrummer3_kit,  # Alias
        }

        creator = kit_creators.get(kit_type.lower())
        if creator:
            return creator()
        else:
            logger.warning(f"Unknown kit type: {kit_type}, using standard kit")
            return DrumKit.create_ezdrummer3_kit()

    # Private helper methods
    def _generate_variations(
        self, base_pattern: Pattern, params: GenerationParameters
    ) -> list:
        """Generate pattern variations based on complexity."""
        from midi_drums.models.song import PatternVariation

        variations = []

        # Create a simplified variation
        if params.complexity > 0.7:
            simplified = base_pattern.copy()
            simplified.name = f"{base_pattern.name}_simple"

            # Remove some hi-hat hits for variation
            simplified.beats = [
                beat
                for beat in simplified.beats
                if not (
                    beat.instrument.name.endswith("HH")
                    and beat.position % 0.5 != 0
                )
            ]

            variations.append(PatternVariation(simplified, 0.3))

        return variations

    def _generate_fills(self, genre: str, params: GenerationParameters) -> list:
        """Generate fill patterns for the genre."""
        plugin = self.plugin_manager.registry.get_genre_plugin(genre)
        if plugin:
            return plugin.get_common_fills()
        return []

    def _extend_pattern_to_bars(self, pattern: Pattern, bars: int) -> Pattern:
        """Extend a pattern to span multiple bars."""
        if bars <= 1:
            return pattern

        extended_pattern = pattern.copy()
        extended_pattern.name = f"{pattern.name}_{bars}bars"

        original_beats = pattern.beats.copy()
        beats_per_bar = pattern.time_signature.beats_per_bar

        # Repeat pattern for additional bars with slight variations
        for bar in range(1, bars):
            bar_offset = bar * beats_per_bar
            for beat in original_beats:
                import random

                from midi_drums.models.pattern import Beat

                new_beat = Beat(
                    position=beat.position + bar_offset,
                    instrument=beat.instrument,
                    velocity=max(
                        1, min(127, beat.velocity + random.randint(-5, 5))
                    ),  # Slight variation with clamping
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent,
                )
                extended_pattern.beats.append(new_beat)

        return extended_pattern

    @classmethod
    def quick_generate(
        cls, genre: str = "metal", style: str = "heavy", tempo: int = 155
    ) -> Song:
        """Quick song generation with sensible defaults.

        This replicates the functionality of the original script.
        """
        generator = cls()
        return generator.create_song(
            genre=genre,
            style=style,
            tempo=tempo,
            complexity=0.7,
            dynamics=0.6,
            humanization=0.3,
        )
