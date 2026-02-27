"""Drummer style plugins for applying signature drumming styles to patterns."""

from midi_drums.plugins.drummers.bonham_refactored import BonhamPlugin
from midi_drums.plugins.drummers.chambers_refactored import ChambersPlugin
from midi_drums.plugins.drummers.dee_refactored import DeePlugin
from midi_drums.plugins.drummers.hoglan_refactored import HoglanPlugin
from midi_drums.plugins.drummers.porcaro_refactored import PorcaroPlugin
from midi_drums.plugins.drummers.roeder_refactored import RoederPlugin
from midi_drums.plugins.drummers.weckl_refactored import WecklPlugin

__all__ = [
    "BonhamPlugin",
    "ChambersPlugin",
    "DeePlugin",
    "HoglanPlugin",
    "PorcaroPlugin",
    "RoederPlugin",
    "WecklPlugin",
]
