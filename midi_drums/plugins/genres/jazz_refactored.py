"""Refactored Jazz genre plugin using pattern templates.

Demonstrates template system applied to Jazz genre with 7 styles.
Compare with original jazz.py (599 lines) to see code reduction.
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


class JazzGenrePluginRefactored(GenrePlugin):
    """Refactored jazz genre plugin using pattern template system."""

    @property
    def genre_name(self) -> str:
        return "jazz"

    @property
    def supported_styles(self) -> list[str]:
        return [
            "swing",  # Traditional swing with ride patterns
            "bebop",  # Fast, complex bebop rhythms
            "fusion",  # Jazz fusion with electric energy
            "latin",  # Latin jazz with clave patterns
            "ballad",  # Soft, brushed ballad patterns
            "hard_bop",  # Aggressive hard bop rhythms
            "contemporary",  # Modern contemporary jazz
        ]

    @property
    def intensity_profile(self) -> dict[str, float]:
        """Jazz genre intensity characteristics."""
        return {
            "aggression": 0.3,
            "speed": 0.7,
            "density": 0.6,
            "power": 0.4,
            "complexity": 0.85,
            "darkness": 0.3,
        }

    def generate_pattern(
        self, section: str, parameters: GenerationParameters
    ) -> Pattern:
        """Generate jazz pattern based on section and style."""
        style = parameters.style
        complexity = parameters.complexity

        pattern_name = f"jazz_{style}_{section}"

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
        """Get common jazz fill patterns using templates."""
        fills = []

        # Brushed tom fill
        tom_fill = (
            TemplateComposer("jazz_brush_fill")
            .add(
                TomFill(pattern="descending", subdivision=TIMING.EIGHTH_TRIPLET)
            )
            .build(bars=1, complexity=0.6, dynamics=0.5)
        )
        fills.append(Fill(tom_fill, 0.7))

        # Cymbal swell
        cymbal_fill = (
            TemplateComposer("jazz_cymbal_swell")
            .add(CrashAccents(positions=[3.5]))
            .build(bars=1, complexity=0.5, dynamics=0.6)
        )
        fills.append(Fill(cymbal_fill, 0.6))

        return fills

    def _generate_intro(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate intro pattern."""
        if style in ["swing", "bebop"]:
            # Ride pattern intro
            return (
                TemplateComposer(name)
                .add(
                    JazzRidePattern(swing_ratio=0.33, accent_pattern="standard")
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.WHOLE,  # Ride used
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.5)
            )
        elif style == "latin":
            # Latin intro with clave feel
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.5, 2.5],  # Clave pattern
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.6)
            )
        else:
            # Soft intro
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.QUARTER,
                    )
                )
                .build(bars=1, complexity=complexity * 0.8, dynamics=0.4)
            )

    def _generate_verse(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate verse pattern based on style."""
        if style == "swing":
            # Traditional swing with ride
            return (
                TemplateComposer(name)
                .add(
                    JazzRidePattern(swing_ratio=0.33, accent_pattern="standard")
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.WHOLE,  # Ride used
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.6)
            )

        elif style == "bebop":
            # Fast bebop with complex ride
            return (
                TemplateComposer(name)
                .add(JazzRidePattern(swing_ratio=0.33, accent_pattern="bebop"))
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.5, 2.5],  # Syncopated
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.WHOLE,  # Ride used
                    )
                )
                .build(bars=1, complexity=complexity * 1.2, dynamics=0.7)
            )

        elif style == "fusion":
            # Fusion with 16th notes
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.5, 2.0, 3.5],  # Complex
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity * 1.3, dynamics=0.8)
            )

        elif style == "latin":
            # Latin with clave pattern
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.5, 2.5],  # 3-2 clave
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.7)
            )

        elif style == "ballad":
            # Soft ballad with brushes
            return (
                TemplateComposer(name)
                .add(JazzRidePattern(swing_ratio=0.25, accent_pattern="soft"))
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.WHOLE,  # Ride used
                    )
                )
                .build(bars=1, complexity=complexity * 0.7, dynamics=0.4)
            )

        elif style == "hard_bop":
            # Hard bop with aggressive ride
            return (
                TemplateComposer(name)
                .add(
                    JazzRidePattern(swing_ratio=0.33, accent_pattern="driving")
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.5, 2.5, 3.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.WHOLE,  # Ride used
                    )
                )
                .build(bars=1, complexity=complexity * 1.1, dynamics=0.75)
            )

        else:  # contemporary
            # Contemporary with ghost notes
            return (
                TemplateComposer(name)
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
                .build(bars=1, complexity=complexity, dynamics=0.7)
            )

    def _generate_chorus(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate chorus pattern - more intense than verse."""
        if style in ["fusion", "hard_bop"]:
            # High energy with crashes
            return (
                TemplateComposer(name)
                .add(CrashAccents(positions=[0.0, 2.0]))
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.5, 2.0, 3.5],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity * 1.2, dynamics=0.85)
            )

        elif style in ["swing", "bebop"]:
            # Intense ride pattern
            return (
                TemplateComposer(name)
                .add(CrashAccents(positions=[0.0]))
                .add(
                    JazzRidePattern(swing_ratio=0.33, accent_pattern="driving")
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.5, 2.5],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.WHOLE,  # Ride used
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.75)
            )

        else:
            # Standard chorus
            return (
                TemplateComposer(name)
                .add(CrashAccents(positions=[0.0]))
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.7)
            )

    def _generate_breakdown(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate breakdown pattern - sparse and dynamic."""
        return (
            TemplateComposer(name)
            .add(
                BasicGroove(
                    kick_positions=[0.0],
                    snare_positions=[2.0],
                    hihat_subdivision=TIMING.WHOLE,
                )
            )
            .add(TomFill(pattern="accent", start_position=3.0))
            .build(bars=1, complexity=complexity * 0.5, dynamics=0.6)
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
            .build(bars=1, complexity=complexity * 0.8, dynamics=0.5)
        )
