"""Refactored Metal genre plugin using pattern templates.

This is a demonstration of how the template system reduces code duplication
and improves maintainability. Compare with the original metal.py (373 lines)
to see the dramatic reduction in code while maintaining functionality.
"""

from midi_drums.config import TIMING
from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill, GenerationParameters
from midi_drums.patterns import (
    BasicGroove,
    BlastBeat,
    CrashAccents,
    DoubleBassPedal,
    TemplateComposer,
    TomFill,
)
from midi_drums.plugins.base import GenrePlugin


class MetalGenrePluginRefactored(GenrePlugin):
    """Refactored metal genre plugin using pattern template system."""

    @property
    def genre_name(self) -> str:
        return "metal"

    @property
    def supported_styles(self) -> list[str]:
        return [
            "heavy",
            "death",
            "power",
            "progressive",
            "thrash",
            "doom",
            "breakdown",
        ]

    @property
    def intensity_profile(self) -> dict[str, float]:
        """Metal genre intensity characteristics."""
        return {
            "aggression": 0.9,
            "speed": 0.8,
            "density": 0.8,
            "power": 1.0,
            "complexity": 0.6,
            "darkness": 0.9,
        }

    def generate_pattern(
        self, section: str, parameters: GenerationParameters
    ) -> Pattern:
        """Generate metal pattern based on section and style."""
        style = parameters.style
        complexity = parameters.complexity

        # Map sections to pattern generators
        pattern_name = f"metal_{style}_{section}"

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
        elif section in ["outro", "ending"]:
            return self._generate_outro(pattern_name, style, complexity)
        else:
            # Default to verse
            return self._generate_verse(pattern_name, style, complexity)

    def get_common_fills(self) -> list[Fill]:
        """Get common metal fill patterns using templates."""
        fills = []

        # Tom roll fill - descending pattern
        tom_fill = (
            TemplateComposer("metal_tom_roll")
            .add(TomFill(pattern="descending", subdivision=TIMING.SIXTEENTH))
            .build(bars=1, complexity=0.8, dynamics=0.8)
        )
        fills.append(Fill(tom_fill, 0.8))

        # Blast beat fill
        blast_fill = (
            TemplateComposer("metal_blast_fill")
            .add(BlastBeat(style="traditional", intensity=0.9))
            .build(bars=1, complexity=0.7, dynamics=0.7)
        )
        fills.append(Fill(blast_fill, 0.6))

        return fills

    # Section generators using templates

    def _generate_intro(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate intro pattern with crash accent."""
        composer = TemplateComposer(name).add(CrashAccents(positions=[0.0]))

        if style == "death":
            # Death metal intro: double bass with snare
            composer.add(
                DoubleBassPedal(subdivision=TIMING.EIGHTH, intensity=0.8)
            )
            composer.add(
                BasicGroove(
                    kick_positions=[],  # Kicks from DoubleBassPedal
                    snare_positions=[1.0, 3.0],
                    hihat_subdivision=TIMING.WHOLE,  # Minimal hihat
                )
            )
            return composer.build(bars=1, complexity=complexity, dynamics=0.9)
        else:
            # Standard heavy intro: quarters kicks, snare on 3
            composer.add(
                BasicGroove(
                    kick_positions=[0.0, 1.0, 2.0, 3.0],
                    snare_positions=[2.0],
                    hihat_subdivision=TIMING.WHOLE,  # Minimal hihat
                )
            )
            return composer.build(bars=1, complexity=complexity, dynamics=0.8)

    def _generate_verse(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate verse pattern based on style."""
        if style == "death":
            # Blast beat verse
            return (
                TemplateComposer(name)
                .add(BlastBeat(style="traditional", intensity=0.9))
                .build(bars=1, complexity=complexity, dynamics=0.85)
            )

        elif style == "power":
            # Power metal: galloping kicks with driving hihat
            return (
                TemplateComposer(name)
                .add(DoubleBassPedal(pattern_type="gallop", intensity=0.7))
                .add(
                    BasicGroove(
                        kick_positions=[],  # Kicks from DoubleBassPedal
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.8)
            )

        elif style == "doom":
            # Doom metal: slow, heavy, simple
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.QUARTER,  # Slow quarters
                    )
                )
                .build(bars=1, complexity=complexity * 0.5, dynamics=1.0)
            )

        elif style == "progressive":
            # Progressive metal: complex patterns, varied subdivisions
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.75, 2.0, 2.75],  # Syncopated
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,  # Fast subdivisions
                    )
                )
                .build(bars=1, complexity=complexity * 1.2, dynamics=0.75)
            )

        elif style == "thrash":
            # Thrash metal: fast, aggressive, driving
            return (
                TemplateComposer(name)
                .add(
                    DoubleBassPedal(subdivision=TIMING.SIXTEENTH, intensity=0.8)
                )
                .add(
                    BasicGroove(
                        kick_positions=[],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.9)
            )

        else:  # heavy (default)
            # Classic heavy metal verse
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.75, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.8)
            )

    def _generate_chorus(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate chorus pattern - more intense than verse."""
        if style == "death":
            # Hammer blast for intensity
            return (
                TemplateComposer(name)
                .add(CrashAccents(positions=[0.0]))
                .add(BlastBeat(style="hammer", intensity=1.0))
                .build(bars=1, complexity=complexity, dynamics=1.0)
            )

        elif style == "power":
            # Power metal chorus: anthemic with crash accents
            return (
                TemplateComposer(name)
                .add(CrashAccents(positions=[0.0, 2.0]))
                .add(DoubleBassPedal(pattern_type="continuous", intensity=0.9))
                .add(
                    BasicGroove(
                        kick_positions=[],
                        snare_positions=[1.0, 3.0],
                        # Minimal hihat (crashes used)
                        hihat_subdivision=TIMING.WHOLE,
                    )
                )
                .build(bars=1, complexity=complexity, dynamics=0.95)
            )

        else:  # heavy, doom, progressive, thrash
            # Heavier version of verse with crashes
            return (
                TemplateComposer(name)
                .add(CrashAccents(positions=[0.0]))
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.5, 1.5, 2.0, 2.5, 3.5],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity * 1.1, dynamics=0.95)
            )

    def _generate_breakdown(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate breakdown pattern - syncopated and heavy."""
        # Breakdowns are similar across styles: sparse, heavy, syncopated
        return (
            TemplateComposer(name)
            .add(
                BasicGroove(
                    kick_positions=[0.0, 1.5, 2.5],  # Syncopated
                    snare_positions=[2.0],  # Rimshot on 3
                    hihat_subdivision=TIMING.WHOLE,  # Minimal
                )
            )
            .add(TomFill(pattern="accent", start_position=1.0))  # Tom accents
            .build(bars=1, complexity=complexity * 0.7, dynamics=1.0)
        )

    def _generate_bridge(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate bridge pattern - often simpler or transitional."""
        # Use verse pattern but with reduced complexity
        verse_pattern = self._generate_verse(
            name.replace("_bridge", "_verse"), style, complexity * 0.8
        )
        verse_pattern.name = name
        return verse_pattern

    def _generate_outro(
        self, name: str, style: str, complexity: float
    ) -> Pattern:
        """Generate outro pattern with descending tom fill."""
        return (
            TemplateComposer(name)
            .add(TomFill(pattern="descending", start_position=0.0))
            .add(CrashAccents(positions=[3.75]))  # Final crash
            .build(bars=1, complexity=complexity, dynamics=0.85)
        )
