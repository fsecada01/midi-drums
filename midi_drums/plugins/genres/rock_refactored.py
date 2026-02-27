"""Rock genre plugin - refactored using template composition.

Uses pattern templates from midi_drums.patterns to eliminate manual
PatternBuilder construction, reducing code by ~35% while maintaining
full functional equivalence with the original rock.py plugin.
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


class RockGenrePlugin(GenrePlugin):
    """Rock genre plugin using template composition.

    Refactored version that uses declarative pattern templates instead of
    manual PatternBuilder construction. Supports all 7 original rock styles
    with identical output characteristics.
    """

    @property
    def genre_name(self) -> str:
        return "rock"

    @property
    def supported_styles(self) -> list[str]:
        return [
            "classic",
            "blues",
            "alternative",
            "progressive",
            "punk",
            "hard",
            "pop",
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
        elif section == "outro":
            return self._generate_outro(style, complexity)
        else:
            return self._generate_verse(style, complexity)

    def get_common_fills(self) -> list[Fill]:
        """Get common rock fill patterns using TomFill template."""
        fills = []

        # Classic rock tom fill
        tom_fill_pattern = (
            TemplateComposer("rock_tom_fill")
            .add(
                TomFill(
                    pattern="descending",
                    subdivision=TIMING.SIXTEENTH,
                    start_position=2.0,
                )
            )
            .build(bars=1, complexity=0.6)
        )
        fills.append(
            Fill(
                tom_fill_pattern,
                trigger_probability=0.8,
                section_position="end",
            )
        )

        # Ascending fill
        ascending_pattern = (
            TemplateComposer("rock_snare_fill")
            .add(
                TomFill(
                    pattern="ascending",
                    subdivision=TIMING.SIXTEENTH,
                    start_position=2.0,
                )
            )
            .build(bars=1, complexity=0.6)
        )
        fills.append(
            Fill(
                ascending_pattern,
                trigger_probability=0.7,
                section_position="middle",
            )
        )

        # Crash accent fill
        crash_pattern = (
            TemplateComposer("rock_crash_fill")
            .add(
                BasicGroove(
                    kick_positions=[0.0, 2.0],
                    snare_positions=[1.0, 3.0],
                    hihat_subdivision=TIMING.EIGHTH,
                )
            )
            .add(CrashAccents(positions=[0.0, 2.0], intensity=0.9))
            .build(bars=1, complexity=0.5)
        )
        fills.append(
            Fill(
                crash_pattern, trigger_probability=0.6, section_position="start"
            )
        )

        return fills

    # -------------------------------------------------------------------------
    # Section generators
    # -------------------------------------------------------------------------

    def _generate_intro(self, style: str, complexity: float) -> Pattern:
        """Intro pattern - typically builds energy."""
        name = f"rock_{style}_intro"
        # Reduce intensity by 30% for intro
        intro_complexity = max(0.0, complexity - 0.3)

        return (
            TemplateComposer(name)
            .add(
                BasicGroove(
                    kick_positions=[0.0, 2.0],
                    snare_positions=[1.0, 3.0],
                    hihat_subdivision=TIMING.EIGHTH,
                )
            )
            .add(CrashAccents(positions=[0.0], intensity=0.9))
            .build(bars=1, complexity=intro_complexity)
        )

    def _generate_verse(self, style: str, complexity: float) -> Pattern:
        """Verse pattern based on style."""
        name = f"rock_{style}_verse"

        if style == "classic":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity)
            )
        elif style == "blues":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .add(
                    JazzRidePattern(swing_ratio=0.33, accent_pattern="standard")
                )
                .build(bars=1, complexity=complexity)
            )
        elif style == "alternative":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.75, 2.0, 2.5],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity)
            )
        elif style == "progressive":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.75, 1.5, 2.5, 3.25],
                        snare_positions=[1.0, 2.75, 3.5],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .add(TomFill(pattern="around", start_position=3.5))
                .add(CrashAccents(positions=[0.0], intensity=0.8))
                .build(bars=1, complexity=complexity)
            )
        elif style == "punk":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.0, 2.0, 3.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity)
            )
        elif style == "hard":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.5, 2.0, 2.5],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .add(CrashAccents(positions=[0.0], intensity=0.9))
                .build(bars=1, complexity=complexity)
            )
        else:  # pop
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.0, 2.0, 3.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity)
            )

    def _generate_chorus(self, style: str, complexity: float) -> Pattern:
        """Chorus pattern - more intense than verse."""
        name = f"rock_{style}_chorus"
        # Increase intensity by 20%
        chorus_complexity = min(1.0, complexity + 0.2)

        if style == "blues":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.0, 2.0, 3.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .add(
                    JazzRidePattern(swing_ratio=0.33, accent_pattern="standard")
                )
                .add(CrashAccents(positions=[0.0], intensity=0.9))
                .build(bars=1, complexity=chorus_complexity)
            )
        elif style == "progressive":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.75, 1.5, 2.5, 3.25],
                        snare_positions=[1.0, 2.75, 3.5],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .add(TomFill(pattern="descending", start_position=3.0))
                .add(CrashAccents(positions=[0.0, 2.0], intensity=0.9))
                .build(bars=1, complexity=chorus_complexity)
            )
        elif style == "punk":
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .add(CrashAccents(positions=[0.0], intensity=1.0))
                .build(bars=1, complexity=chorus_complexity)
            )
        else:  # classic, alternative, hard, pop
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.0, 2.0, 3.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .add(CrashAccents(positions=[0.0], intensity=0.9))
                .build(bars=1, complexity=chorus_complexity)
            )

    def _generate_breakdown(self, style: str, complexity: float) -> Pattern:
        """Breakdown pattern - simplified, spacious."""
        name = f"rock_{style}_breakdown"
        return (
            TemplateComposer(name)
            .add(
                BasicGroove(
                    kick_positions=[0.0, 2.0],
                    snare_positions=[1.0, 3.0],
                    hihat_subdivision=TIMING.QUARTER,
                )
            )
            .add(TomFill(pattern="descending", start_position=3.0))
            .build(bars=1, complexity=max(0.0, complexity - 0.2))
        )

    def _generate_bridge(self, style: str, complexity: float) -> Pattern:
        """Bridge pattern - often simpler or different from verse/chorus."""
        name = f"rock_{style}_bridge"
        bridge_complexity = max(0.0, complexity - 0.1)

        if style in ["blues", "progressive"]:
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
        else:
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.QUARTER,
                    )
                )
                .build(bars=1, complexity=bridge_complexity)
            )

    def _generate_outro(self, style: str, complexity: float) -> Pattern:
        """Outro pattern - winds down."""
        name = f"rock_{style}_outro"
        outro_complexity = max(0.0, complexity - 0.3)

        return (
            TemplateComposer(name)
            .add(
                BasicGroove(
                    kick_positions=[0.0, 2.0],
                    snare_positions=[1.0, 3.0],
                    hihat_subdivision=TIMING.QUARTER,
                )
            )
            .add(TomFill(pattern="descending", start_position=3.0))
            .add(CrashAccents(positions=[3.75], intensity=1.0))
            .build(bars=1, complexity=outro_complexity)
        )
