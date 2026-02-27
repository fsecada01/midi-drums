"""Metal genre plugin - refactored using template composition.

Uses pattern templates from midi_drums.patterns to eliminate manual
PatternBuilder construction, reducing code by ~22% while maintaining
full functional equivalence with the original metal.py plugin.
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


class MetalGenrePlugin(GenrePlugin):
    """Metal genre plugin using template composition.

    Refactored version that uses declarative pattern templates instead of
    manual PatternBuilder construction. Supports all 7 original metal styles
    with identical output characteristics.
    """

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

        if section == "intro":
            return self._generate_intro(style, complexity)
        elif section == "verse":
            return self._generate_verse(style, complexity)
        elif section == "chorus":
            return self._generate_chorus(style, complexity)
        elif section == "breakdown":
            return self._generate_breakdown(style, complexity)
        elif section in ["bridge", "pre_chorus"]:
            return self._generate_bridge(style, complexity)
        elif section in ["outro", "ending"]:
            return self._generate_outro(style, complexity)
        else:
            return self._generate_verse(style, complexity)

    def get_common_fills(self) -> list[Fill]:
        """Get common metal fill patterns using TomFill template."""
        fills = []

        # Tom roll fill using TomFill template
        tom_roll_pattern = (
            TemplateComposer("metal_tom_roll")
            .add(
                TomFill(
                    pattern="descending",
                    subdivision=TIMING.SIXTEENTH,
                    start_position=0.0,
                )
            )
            .build(bars=1, complexity=0.8)
        )
        fills.append(Fill(tom_roll_pattern, 0.8))

        # Blast beat fill using BlastBeat template
        blast_pattern = (
            TemplateComposer("metal_blast_fill")
            .add(BlastBeat(style="traditional", intensity=0.9))
            .build(bars=1)
        )
        fills.append(Fill(blast_pattern, 0.6))

        return fills

    # -------------------------------------------------------------------------
    # Section generators
    # -------------------------------------------------------------------------

    def _generate_intro(self, style: str, complexity: float) -> Pattern:
        """Intro pattern - builds energy with crash accent."""
        name = f"metal_{style}_intro"

        if style == "death":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.HALF,
                    )
                )
                .add(CrashAccents(positions=[0.0], intensity=1.0))
                .build(bars=1, complexity=complexity)
            )
        else:
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.0, 2.0, 3.0],
                        snare_positions=[2.0],
                        hihat_subdivision=TIMING.QUARTER,
                    )
                )
                .add(CrashAccents(positions=[0.0], intensity=1.0))
                .build(bars=1, complexity=complexity)
            )

    def _generate_verse(self, style: str, complexity: float) -> Pattern:
        """Verse pattern based on style."""
        name = f"metal_{style}_verse"

        if style == "death":
            return (
                TemplateComposer(name)
                .add(
                    DoubleBassPedal(
                        subdivision=TIMING.EIGHTH,
                        intensity=1.0,
                        pattern_type="continuous",
                    )
                )
                .add(BlastBeat(style="traditional", intensity=0.9))
                .build(bars=1, complexity=complexity)
            )
        elif style == "power":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.0, 2.0, 3.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.QUARTER,
                    )
                )
                .build(bars=1, complexity=complexity)
            )
        elif style == "doom":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.QUARTER,
                    )
                )
                .build(bars=1, complexity=max(0.0, complexity - 0.2))
            )
        elif style == "progressive":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.75, 1.5, 2.25, 3.0],
                        snare_positions=[1.0, 2.75, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .add(TomFill(pattern="around", start_position=3.5))
                .build(bars=1, complexity=complexity)
            )
        elif style == "thrash":
            return (
                TemplateComposer(name)
                .add(
                    DoubleBassPedal(
                        subdivision=TIMING.SIXTEENTH,
                        intensity=0.9,
                        pattern_type="gallop",
                    )
                )
                .add(BlastBeat(style="hammer", intensity=0.8))
                .build(bars=1, complexity=complexity)
            )
        elif style == "breakdown":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.5, 2.5],
                        snare_positions=[2.0],
                        hihat_subdivision=TIMING.HALF,
                    )
                )
                .add(TomFill(pattern="descending", start_position=3.0))
                .build(bars=1, complexity=complexity)
            )
        else:  # heavy
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.75, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity)
            )

    def _generate_chorus(self, style: str, complexity: float) -> Pattern:
        """Chorus pattern - more intense than verse."""
        name = f"metal_{style}_chorus"
        # Increase intensity by 20%
        chorus_complexity = min(1.0, complexity + 0.2)

        if style == "death":
            return (
                TemplateComposer(name)
                .add(BlastBeat(style="traditional", intensity=1.0))
                .add(CrashAccents(positions=[0.0, 2.0], intensity=1.0))
                .build(bars=1, complexity=chorus_complexity)
            )
        elif style == "power":
            return (
                TemplateComposer(name)
                .add(
                    DoubleBassPedal(
                        subdivision=TIMING.EIGHTH,
                        intensity=0.9,
                        pattern_type="gallop",
                    )
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.0, 2.0, 3.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.QUARTER,
                    )
                )
                .add(CrashAccents(positions=[0.0, 2.0], intensity=1.0))
                .build(bars=1, complexity=chorus_complexity)
            )
        elif style == "doom":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.5, 2.0, 3.5],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .add(CrashAccents(positions=[0.0], intensity=1.0))
                .build(bars=1, complexity=chorus_complexity)
            )
        else:  # heavy, progressive, thrash, breakdown
            return (
                TemplateComposer(name)
                .add(
                    DoubleBassPedal(
                        subdivision=TIMING.EIGHTH,
                        intensity=0.9,
                        pattern_type="continuous",
                    )
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.0, 2.0, 3.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.QUARTER,
                    )
                )
                .build(bars=1, complexity=chorus_complexity)
            )

    def _generate_breakdown(self, style: str, complexity: float) -> Pattern:
        """Breakdown pattern - syncopated, heavy."""
        name = f"metal_{style}_breakdown"
        return (
            TemplateComposer(name)
            .add(
                BasicGroove(
                    kick_positions=[0.0, 1.5, 2.5],
                    snare_positions=[2.0],
                    hihat_subdivision=TIMING.HALF,
                )
            )
            .add(TomFill(pattern="descending", start_position=3.0))
            .build(bars=1, complexity=complexity)
        )

    def _generate_bridge(self, style: str, complexity: float) -> Pattern:
        """Bridge pattern - often simpler, with added tom fills."""
        name = f"metal_{style}_bridge"
        # Reduce complexity slightly for bridge
        bridge_complexity = max(0.0, complexity - 0.1)

        return (
            TemplateComposer(name)
            .add(
                BasicGroove(
                    kick_positions=[0.0, 2.0],
                    snare_positions=[1.0, 3.0],
                    hihat_subdivision=TIMING.QUARTER,
                )
            )
            .add(TomFill(pattern="around", start_position=3.0))
            .build(bars=1, complexity=bridge_complexity)
        )

    def _generate_outro(self, style: str, complexity: float) -> Pattern:
        """Outro pattern - descending tom fill with final crash."""
        name = f"metal_{style}_outro"
        # Reduce intensity by 30% for outro
        outro_complexity = max(0.0, complexity - 0.3)

        return (
            TemplateComposer(name)
            .add(TomFill(pattern="descending", start_position=0.0))
            .add(CrashAccents(positions=[3.75], intensity=1.0))
            .build(bars=1, complexity=outro_complexity)
        )
