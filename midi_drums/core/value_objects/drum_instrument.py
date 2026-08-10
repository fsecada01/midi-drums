"""Drum instrument value object - standard MIDI note mappings."""

from enum import Enum


class DrumInstrument(Enum):
    """Standard drum kit instruments with MIDI note mappings."""

    KICK = 36
    SNARE = 38
    RIM = 40
    CLOSED_HH = 42  # GM standard
    CLOSED_HH_EDGE = 22  # EZDrummer specific
    CLOSED_HH_TIP = 61  # EZDrummer specific
    TIGHT_HH_EDGE = 62  # EZDrummer specific
    TIGHT_HH_TIP = 63  # EZDrummer specific
    PEDAL_HH = 44
    OPEN_HH = 46  # GM standard
    OPEN_HH_1 = 24  # EZDrummer specific
    OPEN_HH_2 = 25  # EZDrummer specific
    OPEN_HH_3 = 26  # EZDrummer specific
    OPEN_HH_MAX = 60  # EZDrummer specific - fully open
    MID_TOM = 47
    FLOOR_TOM = 43
    CRASH = 49
    RIDE = 51
    RIDE_BELL = 53
    SPLASH = 55
    CHINA = 52
