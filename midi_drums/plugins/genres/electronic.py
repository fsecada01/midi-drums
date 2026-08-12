"""Electronic genre plugin - house, techno, drum & bass, dubstep.

Uses pattern templates from midi_drums.patterns (same infrastructure as
the rock/jazz/funk plugins) via declarative TemplateComposer composition -
no manual PatternBuilder construction. BasicGroove's kick_positions already
express a four-on-the-floor kick (one every quarter note), so no new
pattern template was needed for this genre; see issue #30.
"""

from midi_drums.config import TIMING
from midi_drums.core.models.pattern import Pattern
from midi_drums.core.models.song import Fill
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)
from midi_drums.patterns import (
    BasicGroove,
    CrashAccents,
    TemplateComposer,
    TomFill,
)
from midi_drums.plugins.interfaces.genre_plugin import GenrePlugin

# Four-on-the-floor: kick on every quarter note. Shared by house and
# techno verses/choruses/intros.
_FOUR_ON_THE_FLOOR = [0.0, 1.0, 2.0, 3.0]

# Drum & bass breakbeat kick: syncopated, off the plain quarter-note grid.
_BREAKBEAT_KICK = [0.0, 0.75, 2.5]

# Drum & bass syncopated snare: one hit off the standard 2-and-4 backbeat.
_BREAKBEAT_SNARE = [1.0, 2.75]

# Dubstep half-time kick/snare: sparse, with the single snare hit landing
# on beat 3 rather than the usual 2-and-4 backbeat.
_HALF_TIME_KICK = [0.0, 2.5]
_HALF_TIME_SNARE = [2.0]


class ElectronicGenrePlugin(GenrePlugin):
    """Electronic genre plugin using template composition.

    Supports house, techno, drum_and_bass, and dubstep styles, following
    the same declarative TemplateComposer approach as the refactored
    rock/jazz/funk genre plugins.
    """

    @property
    def genre_name(self) -> str:
        return "electronic"

    @property
    def supported_styles(self) -> list[str]:
        return ["house", "techno", "drum_and_bass", "dubstep"]

    @property
    def intensity_profile(self) -> dict[str, float]:
        """Electronic genre intensity characteristics."""
        return {
            "aggression": 0.4,
            "speed": 0.7,
            "density": 0.6,
            "power": 0.55,
            "complexity": 0.45,
            "darkness": 0.4,
        }

    def generate_pattern(
        self, section: str, parameters: GenerationParameters
    ) -> Pattern:
        """Generate electronic pattern based on section and style."""
        style = parameters.style
        complexity = parameters.complexity

        match section:
            case "intro":
                pattern = self._generate_intro(style, complexity)
            case "verse":
                pattern = self._generate_verse(style, complexity)
            case "chorus":
                pattern = self._generate_chorus(style, complexity)
            case "breakdown":
                pattern = self._generate_breakdown(style, complexity)
            case "bridge" | "pre_chorus":
                pattern = self._generate_bridge(style, complexity)
            case "outro":
                pattern = self._generate_outro(style, complexity)
            case _:
                pattern = self._generate_verse(style, complexity)

        return self._apply_ride_hihat_logic(pattern, section, parameters)

    def get_common_fills(self) -> list[Fill]:
        """Get common electronic fill patterns using templates."""
        fills = []

        # Hi-hat roll building into a crash - typical build-up/drop fill.
        roll_pattern = (
            TemplateComposer("electronic_hihat_roll_fill")
            .add(
                BasicGroove(
                    kick_positions=_FOUR_ON_THE_FLOOR,
                    snare_positions=[],
                    hihat_subdivision=TIMING.SIXTEENTH,
                )
            )
            .add(CrashAccents(positions=[0.0], intensity=0.9))
            .build(bars=1, complexity=0.7)
        )
        fills.append(
            Fill(roll_pattern, trigger_probability=0.7, section_position="end")
        )

        # Tom fill transition into the next section.
        tom_fill_pattern = (
            TemplateComposer("electronic_tom_fill")
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
                trigger_probability=0.5,
                section_position="middle",
            )
        )

        return fills

    # -------------------------------------------------------------------------
    # Section generators
    # -------------------------------------------------------------------------

    def _generate_intro(self, style: str, complexity: float) -> Pattern:
        """Intro pattern - establishes the groove, builds energy."""
        name = f"electronic_{style}_intro"
        intro_complexity = max(0.0, complexity - 0.3)

        match style:
            case "house" | "techno":
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=_FOUR_ON_THE_FLOOR,
                            snare_positions=[],
                            hihat_subdivision=TIMING.EIGHTH,
                        )
                    )
                    .build(bars=1, complexity=intro_complexity)
                )
            case "drum_and_bass":
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=[0.0, 2.0],
                            snare_positions=[],
                            hihat_subdivision=TIMING.SIXTEENTH,
                        )
                    )
                    .build(bars=1, complexity=intro_complexity)
                )
            case _:  # dubstep
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=[0.0],
                            snare_positions=[],
                            hihat_subdivision=TIMING.QUARTER,
                        )
                    )
                    .build(bars=1, complexity=intro_complexity)
                )

    def _generate_verse(self, style: str, complexity: float) -> Pattern:
        """Verse pattern based on style."""
        name = f"electronic_{style}_verse"

        match style:
            case "house":
                # Four-on-the-floor kick, backbeat snare/clap, steady
                # off-beat-filling 8th note hi-hat groove.
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=_FOUR_ON_THE_FLOOR,
                            snare_positions=[1.0, 3.0],
                            hihat_subdivision=TIMING.EIGHTH,
                        )
                    )
                    .build(bars=1, complexity=complexity)
                )
            case "techno":
                # Driving, minimal, mechanical precision: four-on-the-floor
                # kick, a single sparse clap accent, dense 16th-note hats.
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=_FOUR_ON_THE_FLOOR,
                            snare_positions=[2.0],
                            hihat_subdivision=TIMING.SIXTEENTH,
                        )
                    )
                    .build(bars=1, complexity=complexity)
                )
            case "drum_and_bass":
                # Fast breakbeat kick, syncopated snare placement off the
                # standard backbeat grid, fast 16th-note hats.
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=_BREAKBEAT_KICK,
                            snare_positions=_BREAKBEAT_SNARE,
                            hihat_subdivision=TIMING.SIXTEENTH,
                        )
                    )
                    .build(bars=1, complexity=complexity)
                )
            case _:  # dubstep
                # Half-time feel: sparse kick, single heavy snare on beat 3.
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=_HALF_TIME_KICK,
                            snare_positions=_HALF_TIME_SNARE,
                            hihat_subdivision=TIMING.EIGHTH,
                        )
                    )
                    .build(bars=1, complexity=complexity)
                )

    def _generate_chorus(self, style: str, complexity: float) -> Pattern:
        """Chorus pattern - more intense/energetic than verse."""
        name = f"electronic_{style}_chorus"
        chorus_complexity = min(1.0, complexity + 0.2)

        match style:
            case "house":
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=_FOUR_ON_THE_FLOOR,
                            snare_positions=[1.0, 3.0],
                            hihat_subdivision=TIMING.EIGHTH,
                        )
                    )
                    .add(CrashAccents(positions=[0.0], intensity=0.9))
                    .build(bars=1, complexity=chorus_complexity)
                )
            case "techno":
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=_FOUR_ON_THE_FLOOR,
                            snare_positions=[1.0, 3.0],
                            hihat_subdivision=TIMING.SIXTEENTH,
                        )
                    )
                    .add(CrashAccents(positions=[0.0], intensity=0.85))
                    .build(bars=1, complexity=chorus_complexity)
                )
            case "drum_and_bass":
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=_BREAKBEAT_KICK,
                            snare_positions=_BREAKBEAT_SNARE,
                            hihat_subdivision=TIMING.SIXTEENTH,
                        )
                    )
                    .add(TomFill(pattern="around", start_position=3.5))
                    .add(CrashAccents(positions=[0.0], intensity=0.9))
                    .build(bars=1, complexity=chorus_complexity)
                )
            case _:  # dubstep
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=_HALF_TIME_KICK,
                            snare_positions=_HALF_TIME_SNARE,
                            hihat_subdivision=TIMING.EIGHTH,
                        )
                    )
                    .add(CrashAccents(positions=[0.0], intensity=1.0))
                    .build(bars=1, complexity=chorus_complexity)
                )

    def _generate_breakdown(self, style: str, complexity: float) -> Pattern:
        """Breakdown pattern - stripped back, spacious."""
        name = f"electronic_{style}_breakdown"
        breakdown_complexity = max(0.0, complexity - 0.2)

        match style:
            case "house" | "techno":
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=[0.0, 2.0],
                            snare_positions=[],
                            hihat_subdivision=TIMING.QUARTER,
                        )
                    )
                    .build(bars=1, complexity=breakdown_complexity)
                )
            case _:  # drum_and_bass, dubstep
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=[0.0],
                            snare_positions=[2.0],
                            hihat_subdivision=TIMING.EIGHTH,
                        )
                    )
                    .build(bars=1, complexity=breakdown_complexity)
                )

    def _generate_bridge(self, style: str, complexity: float) -> Pattern:
        """Bridge pattern - transition or contrasting section."""
        name = f"electronic_{style}_bridge"
        bridge_complexity = max(0.0, complexity - 0.1)

        match style:
            case "drum_and_bass":
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=_BREAKBEAT_KICK,
                            snare_positions=_BREAKBEAT_SNARE,
                            hihat_subdivision=TIMING.SIXTEENTH,
                        )
                    )
                    .add(TomFill(pattern="around", start_position=3.0))
                    .build(bars=1, complexity=bridge_complexity)
                )
            case "dubstep":
                # Half-time feel: sparse kick, single heavy snare on beat 3,
                # matching every other dubstep section (intro/verse/chorus/
                # breakdown/outro) instead of house/techno's four-on-the-floor.
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=_HALF_TIME_KICK,
                            snare_positions=_HALF_TIME_SNARE,
                            hihat_subdivision=TIMING.EIGHTH,
                        )
                    )
                    .add(TomFill(pattern="ascending", start_position=3.0))
                    .build(bars=1, complexity=bridge_complexity)
                )
            case _:  # house, techno
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=_FOUR_ON_THE_FLOOR,
                            snare_positions=[1.0, 3.0],
                            hihat_subdivision=TIMING.QUARTER,
                        )
                    )
                    .add(TomFill(pattern="ascending", start_position=3.0))
                    .build(bars=1, complexity=bridge_complexity)
                )

    def _generate_outro(self, style: str, complexity: float) -> Pattern:
        """Outro pattern - winds down."""
        name = f"electronic_{style}_outro"
        outro_complexity = max(0.0, complexity - 0.3)

        match style:
            case "house" | "techno":
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=_FOUR_ON_THE_FLOOR,
                            snare_positions=[],
                            hihat_subdivision=TIMING.QUARTER,
                        )
                    )
                    .build(bars=1, complexity=outro_complexity)
                )
            case _:  # drum_and_bass, dubstep
                return (
                    TemplateComposer(name)
                    .add(
                        BasicGroove(
                            kick_positions=[0.0],
                            snare_positions=[],
                            hihat_subdivision=TIMING.EIGHTH,
                        )
                    )
                    .build(bars=1, complexity=outro_complexity)
                )
