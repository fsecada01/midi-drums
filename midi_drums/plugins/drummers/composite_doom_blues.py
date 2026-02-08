"""Composite drummer plugin combining Roeder, Porcaro, and Chambers styles."""

import logging

from midi_drums.models.pattern import Pattern
from midi_drums.plugins.base import DrummerPlugin
from midi_drums.plugins.drummers.chambers import ChambersPlugin
from midi_drums.plugins.drummers.porcaro import PorcaroPlugin
from midi_drums.plugins.drummers.roeder import RoederPlugin
from midi_drums.utils.pattern_fixer import remove_ride_hihat_conflicts
from midi_drums.validation.physical_constraints import PhysicalValidator

logger = logging.getLogger(__name__)


class CompositeDoomBluesPlugin(DrummerPlugin):
    """
    Composite drummer combining three legendary styles for doom/blues fusion.

    Layers:
    1. Jason Roeder - Atmospheric sludge foundation (minimal, crushing)
    2. Jeff Porcaro - Blues shuffle and ghost notes (groove, precision)
    3. Dennis Chambers - Funk pocket and dynamics (feel, mastery)

    This creates a unique sound that combines:
    - Roeder's atmospheric weight and space
    - Porcaro's shuffle feel and ghost note work
    - Chambers' deep pocket and dynamic control
    """

    def __init__(self):
        """Initialize the composite drummer with all three component plugins."""
        self.roeder = RoederPlugin()
        self.porcaro = PorcaroPlugin()
        self.chambers = ChambersPlugin()
        self.validator = PhysicalValidator()

    @property
    def drummer_name(self) -> str:
        """Return the composite drummer name."""
        return "composite_doom_blues"

    @property
    def compatible_genres(self) -> list[str]:
        """Compatible with doom metal and blues-influenced genres."""
        return ["metal", "rock", "blues"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """
        Apply layered modifications from all three drummers.

        Order of application:
        1. Roeder first - establishes the minimal, heavy foundation
        2. Porcaro second - adds blues feel and ghost notes
        3. Chambers last - adds funk pocket and final dynamics

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with all three styles blended
        """
        # Start with a copy
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_doom_blues_composite"

        # Layer 1: Roeder - Atmospheric foundation
        # Applies minimal, crushing weight with lots of space
        styled_pattern = self.roeder.apply_style(styled_pattern)
        # Clamp after each layer to prevent negative positions
        for beat in styled_pattern.beats:
            if beat.position < 0.0:
                beat.position = 0.0

        # Layer 2: Porcaro - Blues shuffle and ghost notes
        # Adds shuffle feel and subtle ghost note work
        styled_pattern = self.porcaro.apply_style(styled_pattern)
        # Clamp after each layer to prevent negative positions
        for beat in styled_pattern.beats:
            if beat.position < 0.0:
                beat.position = 0.0

        # Layer 3: Chambers - Funk pocket and dynamics
        # Final layer adds deep pocket and dynamic control
        styled_pattern = self.chambers.apply_style(styled_pattern)
        # Final clamp before validation
        for beat in styled_pattern.beats:
            if beat.position < 0.0:
                beat.position = 0.0

        # Validate for physical conflicts
        conflicts = self.validator.validate_pattern(styled_pattern)
        if conflicts:
            logger.info(
                f"Composite drummer created {len(conflicts)} physical conflicts - "
                "applying automatic fixes"
            )

            # Apply automatic conflict resolution
            styled_pattern = remove_ride_hihat_conflicts(styled_pattern)

            # Validate again to ensure all conflicts are resolved
            remaining_conflicts = self.validator.validate_pattern(
                styled_pattern
            )
            if remaining_conflicts:
                logger.warning(
                    f"After fixes, {len(remaining_conflicts)} conflicts remain"
                )
            else:
                logger.info("All physical conflicts successfully resolved")

        return styled_pattern

    def get_signature_fills(self) -> list:
        """
        Combine signature fills from all three drummers.

        Returns a blend of:
        - Roeder's atmospheric crashes
        - Porcaro's shuffle-based fills
        - Chambers' funky, syncopated fills
        """
        fills = []

        # Get fills from each drummer
        fills.extend(self.roeder.get_signature_fills())
        fills.extend(self.porcaro.get_signature_fills())
        fills.extend(self.chambers.get_signature_fills())

        return fills

    def get_description(self) -> str:
        """Return description of this composite style."""
        return (
            "Composite drummer combining Jason Roeder (atmospheric sludge), "
            "Jeff Porcaro (blues shuffle), and Dennis Chambers (funk pocket) "
            "for a unique doom metal/blues fusion sound."
        )
