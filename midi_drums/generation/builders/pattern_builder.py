"""Pattern builder - fluent construction API for Pattern."""

from midi_drums.config import VELOCITY
from midi_drums.core.models.pattern import Pattern
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.time_signature import TimeSignature


class PatternBuilder:
    """Builder pattern for creating drum patterns."""

    def __init__(self, name: str, time_signature: TimeSignature | None = None):
        self.pattern = Pattern(
            name=name, time_signature=time_signature or TimeSignature()
        )

    def kick(self, position: float, velocity: int = 100) -> "PatternBuilder":
        """Add kick drum at position."""
        self.pattern.add_beat(position, DrumInstrument.KICK, velocity)
        return self

    def snare(self, position: float, velocity: int = 100) -> "PatternBuilder":
        """Add snare at position."""
        self.pattern.add_beat(position, DrumInstrument.SNARE, velocity)
        return self

    def hihat(
        self, position: float, velocity: int = 80, open: bool = False
    ) -> "PatternBuilder":
        """Add hi-hat at position."""
        instrument = (
            DrumInstrument.OPEN_HH if open else DrumInstrument.CLOSED_HH
        )
        self.pattern.add_beat(position, instrument, velocity)
        return self

    def ride(self, position: float, velocity: int = 80) -> "PatternBuilder":
        """Add ride cymbal at position."""
        self.pattern.add_beat(position, DrumInstrument.RIDE, velocity)
        return self

    def hihat_foot(
        self, position: float, velocity: int = VELOCITY.HIHAT_PEDAL
    ) -> "PatternBuilder":
        """Add hi-hat foot pedal ("chick") at position."""
        self.pattern.add_beat(position, DrumInstrument.PEDAL_HH, velocity)
        return self

    def crash(self, position: float, velocity: int = 110) -> "PatternBuilder":
        """Add crash cymbal at position."""
        self.pattern.add_beat(position, DrumInstrument.CRASH, velocity)
        return self

    def build(self) -> Pattern:
        """Build and return the pattern."""
        return self.pattern
