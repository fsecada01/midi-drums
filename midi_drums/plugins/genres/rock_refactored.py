"""Refactored Rock genre plugin using pattern templates.

Demonstrates template system applied to Rock genre with 7 styles.
Compare with original rock.py (513 lines) to see code reduction.
"""

from midi_drums.config import TIMING
from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill, GenerationParameters
from midi_drums.patterns import (
    BasicGroove,
    CrashAccents,
    JazzRidePattern,
    TemplateComposer,
    TomFill,
)
from midi_drums.plugins.base import GenrePlugin


class RockGenrePluginRefactored(GenrePlugin):
    """Refactored rock genre plugin using pattern template system."""

    @property
    def genre_name(self) -> str:
        return "rock"

    @property
    def supported_styles(self) -> list[str]:
        return [
            "classic",  # 70s classic rock (Led Zeppelin, Deep Purple)
            "blues",  # Blues rock with shuffles and triplets
            "alternative",  # 90s alternative rock
            "progressive",  # Complex progressive rock patterns
            "punk",  # Fast, aggressive punk rock
            "hard",  # Hard rock with heavy emphasis
            "pop",  # Pop rock with clean patterns
        ]

    @property
    def intensity_profile(self) -> dict[str, float]:
        """Rock genre intensity characteristics."""
        return {
            "aggression": 0.6,
            "speed": 0.6,
            "density": 0.6,
            "power": 0.75,
            "complexity": 0.5,
            "darkness": 0.5,
        }

    def generate_pattern(
        self, section: str, parameters: GenerationParameters
    ) -> Pattern:
        """Generate rock pattern based on section and style."""
        style = parameters.style
        complexity = parameters.complexity

        pattern_name = f"rock_{style}_{section}"

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
        """Get common rock fill patterns using templates."""
        fills = []

        # Classic rock tom fill
        tom_fill = (
            TemplateComposer("rock_tom_fill")
            .add(TomFill(pattern="descending", subdivision=TIMING.EIGHTH))
            .build(bars=1, complexity=0.7, dynamics=0.8)
        )
        fills.append(Fill(tom_fill, 0.8))

        # Snare roll fill
        snare_roll = (
            TemplateComposer("rock_snare_roll")
            .add(
                BasicGroove(
                    kick_positions=[],
                    snare_positions=[i * TIMING.SIXTEENTH for i in range(16)],
                    hihat_subdivision=TIMING.WHOLE,
                )
            )
            .build(bars=1, complexity=0.6, dynamics=0.7)
        )
        fills.append(Fill(snare_roll, 0.7))

        return fills

    # Section generators using templates

    def _generate_intro(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate intro pattern."""
        composer = TemplateComposer(name).add(CrashAccents(positions=[0.0]))

        if style == "classic":
            # Classic rock: quarters with backbeat
            composer.add(
                BasicGroove(
                    kick_positions=[0.0, 2.0],
                    snare_positions=[1.0, 3.0],
                    hihat_subdivision=TIMING.QUARTER,
                )
            )
        elif style == "punk":
            # Punk: fast eighth notes
            composer.add(
                BasicGroove(
                    kick_positions=[0.0, 1.0, 2.0, 3.0],
                    snare_positions=[1.0, 3.0],
                    hihat_subdivision=TIMING.EIGHTH,
                )
            )
        else:
            # Default: moderate intro
            composer.add(
                BasicGroove(
                    kick_positions=[0.0, 2.0],
                    snare_positions=[1.0, 3.0],
                    hihat_subdivision=TIMING.EIGHTH,
                )
            )

        return composer.build(bars=1, complexity=complexity, dynamics=0.7)

    def _generate_verse(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate verse pattern based on style."""
        if style == "classic":
            # Classic rock: Bonham-style triplets and quarters
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.75, 2.0],  # Bonham kicks
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.75)
            )

        elif style == "blues":
            # Blues rock: shuffle feel with triplets
            return (
                TemplateComposer(name)
                .add(
                    JazzRidePattern(swing_ratio=0.33, accent_pattern="standard")
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.WHOLE,  # Minimal (ride used)
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.7)
            )

        elif style == "alternative":
            # Alternative rock: syncopated, dynamic
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.5, 2.5],  # Syncopated
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity * 1.1, dynamics=0.8)
            )

        elif style == "progressive":
            # Progressive rock: complex patterns
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.75, 1.5, 2.25, 3.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity * 1.3, dynamics=0.75)
            )

        elif style == "punk":
            # Punk rock: fast, driving, simple
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.0, 2.0, 3.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity * 0.8, dynamics=0.9)
            )

        elif style == "hard":
            # Hard rock: heavy, powerful
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.5, 2.0, 2.5],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.85)
            )

        else:  # pop (default)
            # Pop rock: clean, simple
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity * 0.7, dynamics=0.7)
            )

    def _generate_chorus(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate chorus pattern - more intense than verse."""
        if style in ["punk", "hard"]:
            # High energy with crashes
            return (
                TemplateComposer(name)
                .add(CrashAccents(positions=[0.0, 2.0]))
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.5, 1.0, 2.0, 2.5, 3.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.95)
            )

        elif style == "blues":
            # Blues chorus with ride
            return (
                TemplateComposer(name)
                .add(CrashAccents(positions=[0.0]))
                .add(
                    JazzRidePattern(swing_ratio=0.33, accent_pattern="driving")
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.WHOLE,  # Minimal (ride used)
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.85)
            )

        else:
            # Standard chorus with crash
            return (
                TemplateComposer(name)
                .add(CrashAccents(positions=[0.0]))
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.5, 2.0, 2.5],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity * 1.1, dynamics=0.9)
            )

    def _generate_breakdown(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate breakdown pattern - sparse and heavy."""
        return (
            TemplateComposer(name)
            .add(
                BasicGroove(
                    kick_positions=[0.0, 2.5],  # Sparse kicks
                    snare_positions=[2.0],  # Single snare hit
                    hihat_subdivision=TIMING.WHOLE,  # Minimal
                )
            )
            .add(TomFill(pattern="accent", start_position=3.0))
            .build(bars=1, complexity=complexity * 0.6, dynamics=0.9)
        )

    def _generate_bridge(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate bridge pattern - transitional."""
        # Use verse with reduced complexity
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
            .add(CrashAccents(positions=[3.5]))  # Final crash
            .build(bars=1, complexity=complexity, dynamics=0.8)
        )
