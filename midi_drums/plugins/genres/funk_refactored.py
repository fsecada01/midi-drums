"""Refactored Funk genre plugin using pattern templates.

Demonstrates template system applied to Funk genre with 7 styles.
Compare with original funk.py (561 lines) to see code reduction.
"""

from midi_drums.config import TIMING
from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill, GenerationParameters
from midi_drums.patterns import (
    BasicGroove,
    CrashAccents,
    FunkGhostNotes,
    JazzRidePattern,
    TemplateComposer,
    TomFill,
)
from midi_drums.plugins.base import GenrePlugin


class FunkGenrePluginRefactored(GenrePlugin):
    """Refactored funk genre plugin using pattern template system."""

    @property
    def genre_name(self) -> str:
        return "funk"

    @property
    def supported_styles(self) -> list[str]:
        return [
            "classic",  # James Brown "the one" emphasis
            "pfunk",  # Parliament-Funkadelic grooves
            "shuffle",  # Bernard Purdie shuffle patterns
            "new_orleans",  # Second line funk patterns
            "fusion",  # Jazz-funk fusion styles
            "minimal",  # Stripped-down pocket grooves
            "heavy",  # Heavy funk with rock influence
        ]

    @property
    def intensity_profile(self) -> dict[str, float]:
        """Funk genre intensity characteristics."""
        return {
            "aggression": 0.5,
            "speed": 0.5,
            "density": 0.75,
            "power": 0.65,
            "complexity": 0.7,
            "darkness": 0.4,
        }

    def generate_pattern(
        self, section: str, parameters: GenerationParameters
    ) -> Pattern:
        """Generate funk pattern based on section and style."""
        style = parameters.style
        complexity = parameters.complexity

        pattern_name = f"funk_{style}_{section}"

        if section == "intro":
            return self._generate_intro(pattern_name, style, complexity)
        elif section == "verse":
            return self._generate_verse(pattern_name, style, complexity)
        elif section == "chorus":
            return self._generate_chorus(pattern_name, style, complexity)
        elif section == "breakdown":
            return self._generate_breakdown(pattern_name, style, complexity)
        elif section in ["bridge", "pre_chorus"]:
            return self._generate_bridge(pattern_name, style, complexity)
        elif section == "outro":
            return self._generate_outro(pattern_name, style, complexity)
        else:
            return self._generate_verse(pattern_name, style, complexity)

    def get_common_fills(self) -> list[Fill]:
        """Get common funk fill patterns using templates."""
        fills = []

        # Funky tom fill
        tom_fill = (
            TemplateComposer("funk_tom_fill")
            .add(TomFill(pattern="descending", subdivision=TIMING.SIXTEENTH))
            .build(bars=1, complexity=0.7, dynamics=0.7)
        )
        fills.append(Fill(tom_fill, 0.7))

        # Ghost note fill
        ghost_fill = (
            TemplateComposer("funk_ghost_fill")
            .add(FunkGhostNotes(density=0.8, main_snare_positions=[3.0]))
            .build(bars=1, complexity=0.8, dynamics=0.6)
        )
        fills.append(Fill(ghost_fill, 0.6))

        return fills

    def _generate_intro(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate intro pattern."""
        if style == "classic":
            # Emphasis on "the one"
            return (
                TemplateComposer(name)
                .add(CrashAccents(positions=[0.0]))  # THE ONE
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.8)
            )
        else:
            # Standard funk intro
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.7)
            )

    def _generate_verse(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate verse pattern based on style."""
        if style == "classic":
            # Classic funk with heavy ghost notes
            return (
                TemplateComposer(name)
                .add(
                    FunkGhostNotes(
                        density=0.7,
                        emphasize_one=True,
                        main_snare_positions=[1.0, 3.0],
                    )
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[],  # Ghost notes handle
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.75)
            )

        elif style == "pfunk":
            # P-Funk with syncopated kicks
            return (
                TemplateComposer(name)
                .add(
                    FunkGhostNotes(density=0.6, main_snare_positions=[1.0, 3.0])
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.5, 2.5],  # Syncopated
                        snare_positions=[],  # Ghost notes handle
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity * 1.1, dynamics=0.8)
            )

        elif style == "shuffle":
            # Purdie shuffle with triplets
            return (
                TemplateComposer(name)
                .add(
                    JazzRidePattern(swing_ratio=0.33, accent_pattern="standard")
                )
                .add(
                    FunkGhostNotes(density=0.5, main_snare_positions=[1.0, 3.0])
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[],  # Ghost notes handle
                        hihat_subdivision=TIMING.WHOLE,  # Ride used
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.7)
            )

        elif style == "new_orleans":
            # Second line feel
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.5, 2.5, 3.5],  # Second line
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.75)
            )

        elif style == "fusion":
            # Jazz-funk fusion
            return (
                TemplateComposer(name)
                .add(
                    FunkGhostNotes(density=0.6, main_snare_positions=[1.0, 3.0])
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.5, 2.0, 3.5],  # Complex
                        snare_positions=[],  # Ghost notes handle
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity * 1.2, dynamics=0.8)
            )

        elif style == "minimal":
            # Minimal pocket groove
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity * 0.8, dynamics=0.6)
            )

        else:  # heavy
            # Heavy funk with rock influence
            return (
                TemplateComposer(name)
                .add(
                    FunkGhostNotes(density=0.5, main_snare_positions=[1.0, 3.0])
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.5, 2.0, 2.5],  # Heavy
                        snare_positions=[],  # Ghost notes handle
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.85)
            )

    def _generate_chorus(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate chorus pattern - more intense than verse."""
        if style in ["pfunk", "heavy"]:
            # High energy with crashes
            return (
                TemplateComposer(name)
                .add(CrashAccents(positions=[0.0, 2.0]))
                .add(
                    FunkGhostNotes(density=0.7, main_snare_positions=[1.0, 3.0])
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.5, 2.0, 3.5],
                        snare_positions=[],  # Ghost notes handle
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity * 1.2, dynamics=0.9)
            )

        elif style == "classic":
            # Emphasis on "the one" in chorus
            return (
                TemplateComposer(name)
                .add(CrashAccents(positions=[0.0]))  # THE ONE
                .add(
                    FunkGhostNotes(density=0.8, main_snare_positions=[1.0, 3.0])
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[],  # Ghost notes handle
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.85)
            )

        else:
            # Standard funk chorus
            return (
                TemplateComposer(name)
                .add(CrashAccents(positions=[0.0]))
                .add(
                    FunkGhostNotes(density=0.6, main_snare_positions=[1.0, 3.0])
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[],  # Ghost notes handle
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.8)
            )

    def _generate_breakdown(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate breakdown pattern - sparse pocket."""
        return (
            TemplateComposer(name)
            .add(
                BasicGroove(
                    kick_positions=[0.0],
                    snare_positions=[1.0],
                    hihat_subdivision=TIMING.SIXTEENTH,
                )
            )
            .build(bars=1, complexity=complexity * 0.6, dynamics=0.7)
        )

    def _generate_bridge(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate bridge pattern."""
        verse_pattern = self._generate_verse(
            name.replace("_bridge", "_verse"), style, complexity * 0.9
        )
        verse_pattern.name = name
        return verse_pattern

    def _generate_outro(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate outro pattern."""
        return (
            TemplateComposer(name)
            .add(TomFill(pattern="descending", start_position=0.0))
            .add(CrashAccents(positions=[3.75]))
            .build(bars=1, complexity=complexity, dynamics=0.7)
        )
