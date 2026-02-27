"""Funk genre plugin - refactored using template composition.

Uses pattern templates from midi_drums.patterns to eliminate manual
PatternBuilder construction, reducing code by ~41% while maintaining
full functional equivalence with the original funk.py plugin.
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


class FunkGenrePlugin(GenrePlugin):
    """Funk genre plugin using template composition.

    Refactored version that uses declarative pattern templates instead of
    manual PatternBuilder construction. Supports all 7 original funk styles
    with identical output characteristics.
    """

    @property
    def genre_name(self) -> str:
        return "funk"

    @property
    def supported_styles(self) -> list[str]:
        return [
            "classic",
            "pfunk",
            "shuffle",
            "new_orleans",
            "fusion",
            "minimal",
            "heavy",
        ]

    @property
    def intensity_profile(self) -> dict[str, float]:
        """Funk genre intensity characteristics."""
        return {
            "aggression": 0.4,
            "speed": 0.6,
            "density": 0.7,
            "power": 0.6,
            "complexity": 0.7,
            "darkness": 0.4,
        }

    def generate_pattern(
        self, section: str, parameters: GenerationParameters
    ) -> Pattern:
        """Generate funk pattern based on section and style."""
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
        """Get common funk fill patterns using templates."""
        fills = []

        # Ghost note fill
        ghost_fill_pattern = (
            TemplateComposer("funk_ghost_fill")
            .add(
                FunkGhostNotes(
                    density=0.8,
                    emphasize_one=True,
                    main_snare_positions=[1.0, 3.0],
                )
            )
            .build(bars=1, complexity=0.7)
        )
        fills.append(
            Fill(
                ghost_fill_pattern,
                trigger_probability=0.8,
                section_position="end",
            )
        )

        # Tom fill
        tom_fill_pattern = (
            TemplateComposer("funk_tom_fill")
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
                trigger_probability=0.6,
                section_position="middle",
            )
        )

        # Crash accent fill
        crash_pattern = (
            TemplateComposer("funk_crash_fill")
            .add(
                BasicGroove(
                    kick_positions=[0.0, 2.0],
                    snare_positions=[1.0, 3.0],
                    hihat_subdivision=TIMING.SIXTEENTH,
                )
            )
            .add(CrashAccents(positions=[0.0], intensity=0.9))
            .build(bars=1, complexity=0.6)
        )
        fills.append(
            Fill(
                crash_pattern, trigger_probability=0.5, section_position="start"
            )
        )

        return fills

    # -------------------------------------------------------------------------
    # Section generators
    # -------------------------------------------------------------------------

    def _generate_intro(self, style: str, complexity: float) -> Pattern:
        """Intro pattern - establishes the groove."""
        name = f"funk_{style}_intro"
        intro_complexity = max(0.0, complexity - 0.3)

        return (
            TemplateComposer(name)
            .add(
                FunkGhostNotes(
                    density=0.5,
                    emphasize_one=True,
                    main_snare_positions=[1.0, 3.0],
                )
            )
            .add(
                BasicGroove(
                    kick_positions=[0.0, 2.0],
                    snare_positions=[1.0, 3.0],
                    hihat_subdivision=TIMING.SIXTEENTH,
                )
            )
            .build(bars=1, complexity=intro_complexity)
        )

    def _generate_verse(self, style: str, complexity: float) -> Pattern:
        """Verse pattern based on style."""
        name = f"funk_{style}_verse"

        if style == "classic":
            # James Brown "the one" emphasis
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
                        kick_positions=[0.0, 0.75, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity)
            )
        elif style == "pfunk":
            # Parliament-Funkadelic style
            return (
                TemplateComposer(name)
                .add(
                    FunkGhostNotes(
                        density=0.8,
                        emphasize_one=True,
                        main_snare_positions=[1.0, 3.0],
                    )
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.5, 2.0, 2.5],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .build(bars=1, complexity=complexity)
            )
        elif style == "shuffle":
            # Bernard Purdie shuffle
            return (
                TemplateComposer(name)
                .add(
                    FunkGhostNotes(
                        density=0.6,
                        emphasize_one=False,
                        main_snare_positions=[1.0, 3.0],
                    )
                )
                .add(
                    JazzRidePattern(swing_ratio=0.33, accent_pattern="standard")
                )
                .build(bars=1, complexity=complexity)
            )
        elif style == "new_orleans":
            # Second line funk patterns
            return (
                TemplateComposer(name)
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.5, 1.5, 2.0, 3.0],
                        snare_positions=[1.0, 2.5, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .add(
                    FunkGhostNotes(
                        density=0.6,
                        emphasize_one=True,
                        main_snare_positions=[1.0, 2.5, 3.0],
                    )
                )
                .build(bars=1, complexity=complexity)
            )
        elif style == "fusion":
            # Jazz-funk fusion
            return (
                TemplateComposer(name)
                .add(
                    FunkGhostNotes(
                        density=0.6,
                        emphasize_one=False,
                        main_snare_positions=[1.0, 3.0],
                    )
                )
                .add(
                    JazzRidePattern(swing_ratio=0.2, accent_pattern="standard")
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=complexity)
            )
        elif style == "minimal":
            # Stripped-down pocket groove
            return (
                TemplateComposer(name)
                .add(
                    FunkGhostNotes(
                        density=0.3,
                        emphasize_one=True,
                        main_snare_positions=[1.0, 3.0],
                    )
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=max(0.0, complexity - 0.2))
            )
        else:  # heavy
            # Heavy funk with rock influence
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
                        kick_positions=[0.0, 0.5, 2.0, 2.5],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .add(CrashAccents(positions=[0.0], intensity=0.85))
                .build(bars=1, complexity=complexity)
            )

    def _generate_chorus(self, style: str, complexity: float) -> Pattern:
        """Chorus pattern - more intense than verse."""
        name = f"funk_{style}_chorus"
        chorus_complexity = min(1.0, complexity + 0.2)

        if style == "classic":
            return (
                TemplateComposer(name)
                .add(
                    FunkGhostNotes(
                        density=0.8,
                        emphasize_one=True,
                        main_snare_positions=[1.0, 3.0],
                    )
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.5, 1.5, 2.0, 3.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .add(CrashAccents(positions=[0.0], intensity=0.9))
                .build(bars=1, complexity=chorus_complexity)
            )
        elif style == "shuffle":
            return (
                TemplateComposer(name)
                .add(
                    FunkGhostNotes(
                        density=0.7,
                        emphasize_one=False,
                        main_snare_positions=[1.0, 3.0],
                    )
                )
                .add(JazzRidePattern(swing_ratio=0.33, accent_pattern="elvin"))
                .add(CrashAccents(positions=[0.0], intensity=0.85))
                .build(bars=1, complexity=chorus_complexity)
            )
        elif style == "heavy":
            return (
                TemplateComposer(name)
                .add(
                    FunkGhostNotes(
                        density=0.8,
                        emphasize_one=True,
                        main_snare_positions=[1.0, 3.0],
                    )
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.5, 1.0, 2.0, 2.5, 3.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .add(CrashAccents(positions=[0.0, 2.0], intensity=1.0))
                .build(bars=1, complexity=chorus_complexity)
            )
        elif style == "minimal":
            return (
                TemplateComposer(name)
                .add(
                    FunkGhostNotes(
                        density=0.5,
                        emphasize_one=True,
                        main_snare_positions=[1.0, 3.0],
                    )
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 1.0, 2.0, 3.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .build(bars=1, complexity=chorus_complexity)
            )
        else:  # pfunk, new_orleans, fusion
            return (
                TemplateComposer(name)
                .add(
                    FunkGhostNotes(
                        density=0.75,
                        emphasize_one=True,
                        main_snare_positions=[1.0, 3.0],
                    )
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 0.5, 2.0, 2.5],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.SIXTEENTH,
                    )
                )
                .add(CrashAccents(positions=[0.0], intensity=0.9))
                .build(bars=1, complexity=chorus_complexity)
            )

    def _generate_breakdown(self, style: str, complexity: float) -> Pattern:
        """Breakdown pattern - minimal, spacious groove."""
        name = f"funk_{style}_breakdown"
        return (
            TemplateComposer(name)
            .add(
                FunkGhostNotes(
                    density=0.4,
                    emphasize_one=True,
                    main_snare_positions=[1.0, 3.0],
                )
            )
            .add(
                BasicGroove(
                    kick_positions=[0.0, 2.0],
                    snare_positions=[1.0, 3.0],
                    hihat_subdivision=TIMING.EIGHTH,
                )
            )
            .build(bars=1, complexity=max(0.0, complexity - 0.2))
        )

    def _generate_bridge(self, style: str, complexity: float) -> Pattern:
        """Bridge pattern - often a breakdown or contrasting section."""
        name = f"funk_{style}_bridge"
        bridge_complexity = max(0.0, complexity - 0.1)

        if style in ["shuffle", "fusion"]:
            return (
                TemplateComposer(name)
                .add(
                    JazzRidePattern(swing_ratio=0.33, accent_pattern="standard")
                )
                .add(
                    FunkGhostNotes(
                        density=0.4,
                        emphasize_one=False,
                        main_snare_positions=[1.0, 3.0],
                    )
                )
                .add(TomFill(pattern="around", start_position=3.0))
                .build(bars=1, complexity=bridge_complexity)
            )
        else:
            return (
                TemplateComposer(name)
                .add(
                    FunkGhostNotes(
                        density=0.5,
                        emphasize_one=True,
                        main_snare_positions=[1.0, 3.0],
                    )
                )
                .add(
                    BasicGroove(
                        kick_positions=[0.0, 2.0],
                        snare_positions=[1.0, 3.0],
                        hihat_subdivision=TIMING.EIGHTH,
                    )
                )
                .add(TomFill(pattern="descending", start_position=3.0))
                .build(bars=1, complexity=bridge_complexity)
            )

    def _generate_outro(self, style: str, complexity: float) -> Pattern:
        """Outro pattern - winds down the groove."""
        name = f"funk_{style}_outro"
        outro_complexity = max(0.0, complexity - 0.3)

        return (
            TemplateComposer(name)
            .add(
                FunkGhostNotes(
                    density=0.4,
                    emphasize_one=True,
                    main_snare_positions=[1.0, 3.0],
                )
            )
            .add(
                BasicGroove(
                    kick_positions=[0.0, 2.0],
                    snare_positions=[1.0, 3.0],
                    hihat_subdivision=TIMING.EIGHTH,
                )
            )
            .add(TomFill(pattern="descending", start_position=3.0))
            .add(CrashAccents(positions=[3.75], intensity=1.0))
            .build(bars=1, complexity=outro_complexity)
        )
