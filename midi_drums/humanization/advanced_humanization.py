"""Advanced humanization engine inspired by professional recordings.

This module implements professional-grade MIDI humanization techniques
inspired by Toontrack MIDI libraries and real drummer analysis.
"""

import random

from midi_drums.models.pattern import Beat, DrumInstrument, Pattern

# Try to import numpy for Gaussian distribution, fallback to random if not available
try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class AdvancedHumanizer:
    """Professional-grade humanization engine.

    Features:
    - Gaussian timing distribution (more natural than uniform)
    - Instrument-specific timing characteristics
    - Context-aware velocity curves
    - Micro-timing relationships (flams, offsets)
    - Subtle fatigue modeling
    - Musical phrase awareness

    Inspired by analysis of Toontrack MIDI libraries and professional recordings.
    """

    # Instrument timing characteristics (ms offset at 120 BPM baseline)
    # Positive = behind beat, Negative = ahead of beat
    INSTRUMENT_TIMING_BIAS = {
        DrumInstrument.KICK: -2.0,  # Kicks lead slightly (drives rhythm)
        DrumInstrument.SNARE: 0.0,  # Snare is reference point
        DrumInstrument.RIM: 0.0,
        DrumInstrument.CLOSED_HH: 0.0,  # Hi-hat is metronomic reference
        DrumInstrument.CLOSED_HH_EDGE: 0.0,
        DrumInstrument.CLOSED_HH_TIP: 0.0,
        DrumInstrument.TIGHT_HH_EDGE: 0.0,
        DrumInstrument.TIGHT_HH_TIP: 0.0,
        DrumInstrument.OPEN_HH: 1.0,  # Open hi-hat slightly behind
        DrumInstrument.OPEN_HH_1: 1.0,
        DrumInstrument.OPEN_HH_2: 1.0,
        DrumInstrument.OPEN_HH_3: 1.0,
        DrumInstrument.OPEN_HH_MAX: 1.0,
        DrumInstrument.PEDAL_HH: 0.0,
        DrumInstrument.RIDE: 1.0,  # Ride slightly behind
        DrumInstrument.RIDE_BELL: 1.0,
        DrumInstrument.CRASH: 2.0,  # Crashes behind (heavy cymbals)
        DrumInstrument.SPLASH: 1.5,
        DrumInstrument.CHINA: 2.0,
        DrumInstrument.MID_TOM: 0.5,
        DrumInstrument.FLOOR_TOM: 0.5,
    }

    # Timing tightness by instrument (standard deviation in ms)
    # Smaller = tighter timing
    TIMING_TIGHTNESS = {
        DrumInstrument.KICK: 3.0,
        DrumInstrument.SNARE: 4.0,
        DrumInstrument.RIM: 4.0,
        DrumInstrument.CLOSED_HH: 2.0,  # Tightest (metronomic)
        DrumInstrument.CLOSED_HH_EDGE: 2.0,
        DrumInstrument.CLOSED_HH_TIP: 2.0,
        DrumInstrument.TIGHT_HH_EDGE: 2.0,
        DrumInstrument.TIGHT_HH_TIP: 2.0,
        DrumInstrument.OPEN_HH: 3.0,
        DrumInstrument.OPEN_HH_1: 3.0,
        DrumInstrument.OPEN_HH_2: 3.0,
        DrumInstrument.OPEN_HH_3: 3.0,
        DrumInstrument.OPEN_HH_MAX: 3.0,
        DrumInstrument.PEDAL_HH: 2.5,
        DrumInstrument.RIDE: 5.0,
        DrumInstrument.RIDE_BELL: 4.0,
        DrumInstrument.CRASH: 6.0,  # Loosest (heavy, reactive)
        DrumInstrument.SPLASH: 5.0,
        DrumInstrument.CHINA: 6.0,
        DrumInstrument.MID_TOM: 5.0,
        DrumInstrument.FLOOR_TOM: 5.0,
    }

    # Velocity ranges by hit type
    VELOCITY_RANGES = {
        "ghost": (25, 45),  # Subtle ghost notes
        "normal": (65, 90),  # Regular hits
        "accent": (95, 115),  # Accented hits
        "max": (115, 127),  # Maximum power
    }

    def __init__(
        self,
        tempo: int = 120,
        style: str = "balanced",  # tight, balanced, loose
        humanization_amount: float = 0.5,  # 0.0-1.0
    ):
        """Initialize advanced humanizer.

        Args:
            tempo: Song tempo in BPM (affects ms-to-beats conversion)
            style: Humanization style:
                - 'tight': Studio precision (0.5x variance)
                - 'balanced': Natural feel (1.0x variance)
                - 'loose': Live energy (1.8x variance)
            humanization_amount: Overall humanization strength (0.0-1.0)
                - 0.0: Perfect quantization
                - 0.5: Moderate humanization (recommended)
                - 1.0: Maximum humanization
        """
        self.tempo = tempo
        self.style = style
        self.humanization_amount = humanization_amount

        # Style multipliers for timing variation
        self.style_multipliers = {
            "tight": 0.5,  # Studio precision
            "balanced": 1.0,  # Natural
            "loose": 1.8,  # Live energy
        }
        self.multiplier = self.style_multipliers.get(style, 1.0)

        # Calculate ms per beat for timing conversions
        self.ms_per_beat = 60000.0 / self.tempo

    def humanize_pattern(
        self,
        pattern: Pattern,
        section_type: str = "verse",  # verse, chorus, fill, breakdown, intro, outro
    ) -> Pattern:
        """Apply professional humanization to entire pattern.

        Args:
            pattern: Input pattern to humanize
            section_type: Musical context for context-aware humanization
                - 'verse': Tighter, consistent
                - 'chorus': Louder, more energy
                - 'fill': Looser timing, velocity curves
                - 'breakdown': Heavy accents, tight but powerful
                - 'intro': Building energy
                - 'outro': Fading energy

        Returns:
            Humanized pattern with Gaussian timing, velocity curves, and micro-timing
        """
        if self.humanization_amount == 0.0:
            return pattern

        # Get context-aware settings
        context = self._get_context_settings(section_type)

        # Group beats that occur at similar times
        beat_groups = self._group_beats_by_timing(pattern.beats)

        humanized_beats = []

        for position, beats in beat_groups.items():
            # Apply micro-timing relationships (flams, offsets between limbs)
            timed_beats = self._apply_micro_timing(beats, position, context)

            # Apply velocity curves and dynamics
            velocity_beats = self._apply_velocity_curves(
                timed_beats, position, context
            )

            humanized_beats.extend(velocity_beats)

        # Apply gradual fatigue (subtle velocity reduction over time)
        if pattern.duration_bars() >= 8:
            humanized_beats = self._apply_fatigue(
                humanized_beats, pattern.duration_bars()
            )

        # Sort beats by position
        humanized_beats.sort(key=lambda b: b.position)

        return Pattern(
            name=f"{pattern.name}_humanized",
            beats=humanized_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "humanization": "advanced"},
        )

    def _gaussian_timing_offset(
        self, instrument: DrumInstrument, position: float
    ) -> float:
        """Generate Gaussian timing offset for instrument.

        Uses instrument-specific timing bias and tightness.
        Downbeats are naturally tighter (50% tighter timing).

        Args:
            instrument: Drum instrument
            position: Beat position in pattern

        Returns:
            Timing offset in beats (can be positive or negative)
        """
        # Get instrument characteristics
        bias_ms = self.INSTRUMENT_TIMING_BIAS.get(instrument, 0.0)
        tightness_ms = self.TIMING_TIGHTNESS.get(instrument, 4.0)

        # Downbeats are tighter (50% reduction in variance)
        is_downbeat = position % 1.0 < 0.01
        if is_downbeat:
            tightness_ms *= 0.5

        # Apply humanization amount and style multiplier
        tightness_ms *= self.humanization_amount * self.multiplier

        # Generate Gaussian offset (ms)
        if HAS_NUMPY:
            offset_ms = np.random.normal(bias_ms, tightness_ms)
        else:
            # Fallback: approximate Gaussian with sum of uniform randoms (Central Limit Theorem)
            # Sum of 12 uniform randoms approximates Gaussian
            offset_ms = bias_ms + (
                sum(
                    random.uniform(-tightness_ms, tightness_ms)
                    for _ in range(12)
                )
                / 12.0
            )

        # Convert ms to beats (tempo-aware)
        offset_beats = offset_ms / self.ms_per_beat

        return offset_beats

    def _get_context_settings(self, section_type: str) -> dict:
        """Get humanization settings based on musical context.

        Different sections have different energy levels and timing characteristics.
        """
        contexts = {
            "verse": {
                "timing_multiplier": 0.8,  # Tighter
                "velocity_boost": 0,  # Normal volume
                "accent_strength": 1.0,  # Normal accents
            },
            "chorus": {
                "timing_multiplier": 1.2,  # Looser (more energy)
                "velocity_boost": 10,  # Louder
                "accent_strength": 1.3,  # Stronger accents
            },
            "fill": {
                "timing_multiplier": 1.5,  # Loosest (fast playing)
                "velocity_boost": 5,  # Slightly louder
                "accent_strength": 1.5,  # Very strong accents
            },
            "breakdown": {
                "timing_multiplier": 0.9,  # Tight but heavy
                "velocity_boost": 15,  # Very loud
                "accent_strength": 2.0,  # Maximum accents
            },
            "intro": {
                "timing_multiplier": 0.85,  # Controlled
                "velocity_boost": -5,  # Slightly softer
                "accent_strength": 0.8,  # Subdued
            },
            "outro": {
                "timing_multiplier": 1.0,  # Balanced
                "velocity_boost": -10,  # Fading
                "accent_strength": 0.7,  # Fading accents
            },
        }
        return contexts.get(section_type, contexts["verse"])

    def _group_beats_by_timing(
        self, beats: list[Beat]
    ) -> dict[float, list[Beat]]:
        """Group beats that occur at similar times.

        Beats within ~10ms are considered simultaneous and need micro-timing.

        Args:
            beats: List of beats to group

        Returns:
            Dictionary mapping position to list of beats at that position
        """
        groups = {}
        tolerance = 10.0 / self.ms_per_beat  # ~10ms tolerance

        for beat in beats:
            # Find existing group within tolerance
            found_group = False
            for pos in list(groups.keys()):
                if abs(beat.position - pos) < tolerance:
                    groups[pos].append(beat)
                    found_group = True
                    break

            if not found_group:
                groups[beat.position] = [beat]

        return groups

    def _apply_micro_timing(
        self, beats: list[Beat], position: float, context: dict
    ) -> list[Beat]:
        """Apply micro-timing relationships between simultaneous instruments.

        Simulates natural hand/foot coordination timing:
        - Kick + snare flam (1-3ms offset)
        - Hi-hat slightly ahead of kick
        - Crashes naturally behind beat

        Args:
            beats: Beats occurring at similar time
            position: Base position in pattern
            context: Context settings

        Returns:
            List of beats with micro-timing applied
        """
        if len(beats) == 1:
            # Single instrument - apply standard timing
            beat = beats[0]
            offset = self._gaussian_timing_offset(beat.instrument, position)
            offset *= context["timing_multiplier"]

            return [
                Beat(
                    position=max(
                        0.0, beat.position + offset
                    ),  # Prevent negative
                    instrument=beat.instrument,
                    velocity=beat.velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent,
                )
            ]

        # Multiple instruments - apply relational micro-timing
        instruments = {b.instrument for b in beats}
        timed_beats = []

        for beat in beats:
            # Base Gaussian offset
            offset = self._gaussian_timing_offset(beat.instrument, position)
            offset *= context["timing_multiplier"]

            # Apply micro-flams for simultaneous kick + snare
            # In real playing, kick leads by 1-3ms
            if (
                beat.instrument == DrumInstrument.KICK
                and DrumInstrument.SNARE in instruments
            ):
                offset -= 0.002  # Kick 2ms early

            elif (
                beat.instrument == DrumInstrument.SNARE
                and DrumInstrument.KICK in instruments
            ):
                offset += 0.001  # Snare 1ms late (total 3ms flam)

            # Crashes naturally slightly behind everything
            if beat.instrument in {
                DrumInstrument.CRASH,
                DrumInstrument.CHINA,
                DrumInstrument.SPLASH,
            }:
                offset += 0.003  # 3ms extra delay on crashes

            timed_beats.append(
                Beat(
                    position=max(
                        0.0, beat.position + offset
                    ),  # Prevent negative
                    instrument=beat.instrument,
                    velocity=beat.velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent,
                )
            )

        return timed_beats

    def _apply_velocity_curves(
        self, beats: list[Beat], position: float, context: dict
    ) -> list[Beat]:
        """Apply velocity humanization with musical awareness.

        Velocity ranges:
        - Ghost notes: 25-45
        - Normal hits: 65-90
        - Accents: 95-115
        - Maximum: 115-127

        Args:
            beats: Beats to apply velocity curves to
            position: Position in pattern (for musical context)
            context: Context settings

        Returns:
            Beats with humanized velocities
        """
        velocity_beats = []

        # Check if this is a downbeat (stronger)
        is_downbeat = position % 4.0 < 0.01
        downbeat_boost = 5 if is_downbeat else 0

        for beat in beats:
            # Determine base velocity range
            if beat.ghost_note:
                base_range = self.VELOCITY_RANGES["ghost"]
                variance = 3  # Tight variance for ghosts
            elif beat.accent:
                base_range = self.VELOCITY_RANGES["accent"]
                variance = 5  # Moderate variance
            else:
                base_range = self.VELOCITY_RANGES["normal"]
                variance = 8  # Wider variance

            # Calculate target velocity
            target_velocity = (base_range[0] + base_range[1]) // 2

            # Apply Gaussian variation
            if HAS_NUMPY:
                new_velocity = int(
                    np.random.normal(
                        target_velocity, variance * self.humanization_amount
                    )
                )
            else:
                # Fallback to uniform with slight bias toward center
                variation = int(
                    random.uniform(-variance, variance)
                    * self.humanization_amount
                )
                new_velocity = target_velocity + variation

            # Apply context boost (chorus louder, etc.)
            boost = context["velocity_boost"] + downbeat_boost

            # Apply accent boost
            if beat.accent:
                accent_boost = int(10 * context["accent_strength"])
                boost += accent_boost

            new_velocity = new_velocity + boost

            # Clamp to MIDI range
            new_velocity = max(1, min(127, new_velocity))

            velocity_beats.append(
                Beat(
                    position=beat.position,
                    instrument=beat.instrument,
                    velocity=new_velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent,
                )
            )

        return velocity_beats

    def _apply_fatigue(
        self, beats: list[Beat], duration_bars: float
    ) -> list[Beat]:
        """Apply subtle fatigue effect (velocity reduction over time).

        Simulates natural drummer fatigue during long sections.
        Effect is very subtle (max 5% reduction).

        Args:
            beats: Beats to apply fatigue to
            duration_bars: Pattern duration in bars

        Returns:
            Beats with subtle fatigue applied
        """
        fatigued_beats = []

        for beat in beats:
            # Calculate progress through pattern (0.0 to 1.0)
            progress = beat.position / (duration_bars * 4.0)

            # Fatigue factor: 0-5% reduction based on progress
            fatigue_factor = 1.0 - (progress * 0.05 * self.humanization_amount)

            # Apply fatigue to velocity
            new_velocity = int(beat.velocity * fatigue_factor)
            new_velocity = max(1, new_velocity)

            fatigued_beats.append(
                Beat(
                    position=beat.position,
                    instrument=beat.instrument,
                    velocity=new_velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent,
                )
            )

        return fatigued_beats


# Convenience function for quick humanization
def humanize_pattern(
    pattern: Pattern,
    tempo: int = 120,
    style: str = "balanced",
    amount: float = 0.5,
    section_type: str = "verse",
) -> Pattern:
    """Quick humanization of a pattern.

    Args:
        pattern: Pattern to humanize
        tempo: Song tempo in BPM
        style: 'tight', 'balanced', or 'loose'
        amount: Humanization amount (0.0-1.0)
        section_type: 'verse', 'chorus', 'fill', 'breakdown', etc.

    Returns:
        Humanized pattern

    Example:
        >>> from midi_drums.humanization import humanize_pattern
        >>> humanized = humanize_pattern(my_pattern, tempo=140, style="loose", amount=0.7)
    """
    humanizer = AdvancedHumanizer(
        tempo=tempo, style=style, humanization_amount=amount
    )
    return humanizer.humanize_pattern(pattern, section_type=section_type)
