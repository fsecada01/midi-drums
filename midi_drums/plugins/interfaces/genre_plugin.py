"""GenrePlugin interface - base class for genre-specific pattern generators."""

import math
from abc import ABC, abstractmethod

from midi_drums.config import VELOCITY
from midi_drums.core.models.pattern import Pattern
from midi_drums.core.models.song import Fill
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)

# Sections that always count as "high energy" for ride/hi-hat switching,
# regardless of complexity.
_RIDE_SECTIONS = frozenset({"chorus", "bridge", "pre_chorus"})

_HIHAT_INSTRUMENTS = frozenset(
    {DrumInstrument.CLOSED_HH, DrumInstrument.OPEN_HH}
)


class GenrePlugin(ABC):
    """Base class for genre-specific pattern generators."""

    @property
    @abstractmethod
    def genre_name(self) -> str:
        """Name of the genre this plugin handles."""
        pass

    @property
    @abstractmethod
    def supported_styles(self) -> list[str]:
        """List of style variations supported by this genre."""
        pass

    @property
    def intensity_profile(self) -> dict[str, float]:
        """Return genre's intensity characteristics (0.0-1.0 scale).

        Defines the characteristic "feel" of this genre across multiple dimensions.
        Used for genre context adaptation when blending patterns.

        Returns:
            Dictionary mapping intensity dimensions to values (0.0-1.0):
                - aggression: How aggressive/heavy (0.0=gentle, 1.0=extreme)
                - speed: Typical tempo tendency (0.0=slow, 1.0=very fast)
                - density: Note density (0.0=sparse, 1.0=very dense)
                - power: Kick/snare intensity (0.0=light, 1.0=maximum)
                - complexity: Pattern complexity (0.0=simple, 1.0=very complex)
                - darkness: Tonal darkness (0.0=bright, 1.0=dark/heavy)

        Default implementation returns neutral (0.5) for all dimensions.
        Override in genre plugins to define characteristic profile.
        """
        return {
            "aggression": 0.5,
            "speed": 0.5,
            "density": 0.5,
            "power": 0.5,
            "complexity": 0.5,
            "darkness": 0.5,
        }

    @abstractmethod
    def generate_pattern(
        self, section: str, parameters: GenerationParameters
    ) -> Pattern:
        """Generate a pattern for the specified section and parameters.

        Args:
            section: Section type ('verse', 'chorus', 'bridge', etc.)
            parameters: Generation parameters including style, complexity, etc.

        Returns:
            Generated Pattern instance
        """
        pass

    @abstractmethod
    def get_common_fills(self) -> list[Fill]:
        """Get common fill patterns for this genre."""
        pass

    def apply_context_blend(
        self,
        pattern: Pattern,
        context_profile: dict[str, float],
        blend_amount: float,
    ) -> Pattern:
        """Adapt pattern to match context genre characteristics.

        Blends this genre's pattern with characteristics from a context genre,
        allowing patterns to adapt to overall song aesthetics while maintaining
        their core identity.

        Args:
            pattern: Base pattern to adapt
            context_profile: Intensity profile of context genre
            blend_amount: Blending strength (0.0=no blend, 1.0=full blend)

        Returns:
            Adapted pattern with blended characteristics

        Example:
            Progressive pattern in metal song context:
            - Base: progressive complexity with moderate power
            - Context: metal's high aggression and power
            - Result: Complex progressive with heavier, more aggressive feel
        """
        if blend_amount <= 0.0:
            return pattern

        adapted = pattern.copy()
        blend_amount = min(1.0, max(0.0, blend_amount))

        # Calculate blended intensity values
        own_profile = self.intensity_profile
        blended_power = (
            own_profile["power"]
            + (context_profile["power"] - own_profile["power"]) * blend_amount
        )
        blended_aggression = (
            own_profile["aggression"]
            + (context_profile["aggression"] - own_profile["aggression"])
            * blend_amount
        )
        blended_density = (
            own_profile["density"]
            + (context_profile["density"] - own_profile["density"])
            * blend_amount
        )

        # Apply power adjustment to kick and snare
        power_boost = int((blended_power - own_profile["power"]) * 20)
        for beat in adapted.beats:
            if beat.instrument in [DrumInstrument.KICK, DrumInstrument.SNARE]:
                beat.velocity = max(1, min(127, beat.velocity + power_boost))

        # Apply aggression (tighter timing for high aggression)
        if blended_aggression > 0.7 and blend_amount > 0.2:
            quantize_strength = blend_amount * 0.5
            for beat in adapted.beats:
                # Quantize to nearest 16th note
                quantized_pos = round(beat.position / 0.25) * 0.25
                # Blend between original and quantized
                beat.position = (
                    beat.position
                    + (quantized_pos - beat.position) * quantize_strength
                )

        # Apply density (add ghost notes on snare for dense contexts)
        if blended_density > own_profile["density"] and blend_amount > 0.3:
            density_increase = (
                blended_density - own_profile["density"]
            ) * blend_amount
            if density_increase > 0.2:
                # Add subtle ghost notes between main snare hits
                import random

                new_beats = []
                snare_positions = [
                    b.position
                    for b in adapted.beats
                    if b.instrument == DrumInstrument.SNARE
                ]
                for pos in snare_positions:
                    if random.random() < density_increase:
                        # Add ghost note before main hit
                        from midi_drums.core.models.pattern import Beat

                        ghost = Beat(
                            position=max(0, pos - 0.125),
                            instrument=DrumInstrument.SNARE,
                            velocity=max(40, int(50 * (1 - blend_amount))),
                            duration=0.05,
                            ghost_note=True,
                        )
                        new_beats.append(ghost)
                adapted.beats.extend(new_beats)

        return adapted

    def _high_energy_timekeeper(
        self, section: str, parameters: GenerationParameters
    ) -> DrumInstrument:
        """Instrument that hi-hat timekeeping is promoted to for
        high-energy sections.

        Defaults to the ride cymbal, matching traditional timekeeping
        practice. Extension point: subclasses may override this to
        select crash, china, or another cymbal instead - ride is not
        the universal high-energy timekeeper across genres (e.g. rock
        and extreme metal idiomatically favor crash/china for this
        role). Genre-aware selection logic is deliberately deferred to
        a follow-up issue; this hook only exists so that follow-up
        doesn't have to touch _apply_ride_hihat_logic itself.
        """
        return DrumInstrument.RIDE

    def _apply_ride_hihat_logic(
        self,
        pattern: Pattern,
        section: str,
        parameters: GenerationParameters,
    ) -> Pattern:
        """Switch hi-hat timekeeping to a higher-energy cymbal (ride by
        default - see _high_energy_timekeeper) for higher-energy
        sections, adding a hi-hat foot pedal ("chick" on every other
        beat) once switched.

        A section is high-energy if its name is chorus/bridge/pre_chorus,
        or if parameters.complexity has crossed parameters.ride_threshold.
        Only ever promotes hi-hat away from hi-hat, never the reverse - a
        pattern that already rides on its own (e.g. jazz's swing verse via
        JazzRidePattern) is left untouched rather than downgraded.
        """
        is_high_energy = (
            section in _RIDE_SECTIONS
            or parameters.complexity >= parameters.ride_threshold
        )
        if not is_high_energy:
            return pattern

        if not any(
            beat.instrument in _HIHAT_INSTRUMENTS for beat in pattern.beats
        ):
            return pattern

        timekeeper = self._high_energy_timekeeper(section, parameters)

        switched = pattern.copy()
        for beat in switched.beats:
            if beat.instrument in _HIHAT_INSTRUMENTS:
                beat.instrument = timekeeper

        existing_pedal_positions = {
            beat.position
            for beat in switched.beats
            if beat.instrument == DrumInstrument.PEDAL_HH
        }
        beats_per_bar = switched.time_signature.beats_per_bar
        for bar in range(math.ceil(switched.duration_bars())):
            bar_offset = bar * beats_per_bar
            beat_num = 1.0
            while beat_num < beats_per_bar:
                position = bar_offset + beat_num
                if position not in existing_pedal_positions:
                    switched.add_beat(
                        position, DrumInstrument.PEDAL_HH, VELOCITY.HIHAT_PEDAL
                    )
                beat_num += 2.0

        return switched

    def get_section_variations(self, section: str) -> list[Pattern]:
        """Get pattern variations for a specific section.

        Default implementation returns empty list.
        Override in subclasses to provide variations.
        """
        return []

    def supports_style(self, style: str) -> bool:
        """Check if this plugin supports the given style."""
        return style in self.supported_styles

    def validate_parameters(self, parameters: GenerationParameters) -> bool:
        """Validate that parameters are appropriate for this genre.

        Default implementation checks genre and style support.
        Override for custom validation.
        """
        if parameters.genre != self.genre_name:
            return False
        return self.supports_style(parameters.style)
