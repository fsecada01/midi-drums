"""Pattern templates for reusable drum pattern generation.

This module provides composable pattern templates that eliminate code duplication
across genre plugins. Templates can be combined using the TemplateComposer.

Usage:
    from midi_drums.patterns import BasicGroove, TemplateComposer
    from midi_drums.config import VELOCITY, TIMING

    # Create pattern using templates
    pattern = TemplateComposer("rock_verse") \\
        .add(BasicGroove(
            kick_positions=[0.0, 2.0],
            snare_positions=[1.0, 3.0],
            hihat_subdivision=TIMING.EIGHTH
        )) \\
        .build(complexity=0.6)
"""

from midi_drums.patterns.templates import (
    BasicGroove,
    BlastBeat,
    CrashAccents,
    DoubleBassPedal,
    FunkGhostNotes,
    JazzRidePattern,
    PatternTemplate,
    TemplateComposer,
    TomFill,
    create_basic_rock_pattern,
    create_metal_pattern,
)

__all__ = [
    # Base class
    "PatternTemplate",
    # Concrete templates
    "BasicGroove",
    "DoubleBassPedal",
    "BlastBeat",
    "JazzRidePattern",
    "FunkGhostNotes",
    "CrashAccents",
    "TomFill",
    # Composer
    "TemplateComposer",
    # Convenience functions
    "create_basic_rock_pattern",
    "create_metal_pattern",
]
