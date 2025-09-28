"""Drummer style plugins for applying signature drumming styles to patterns."""

from midi_drums.plugins.drummers.bonham import BonhamPlugin
from midi_drums.plugins.drummers.chambers import ChambersPlugin
from midi_drums.plugins.drummers.dee import DeePlugin
from midi_drums.plugins.drummers.hoglan import HoglanPlugin
from midi_drums.plugins.drummers.porcaro import PorcaroPlugin
from midi_drums.plugins.drummers.roeder import RoederPlugin
from midi_drums.plugins.drummers.weckl import WecklPlugin

__all__ = [
    "BonhamPlugin",
    "ChambersPlugin",
    "DeePlugin",
    "HoglanPlugin",
    "PorcaroPlugin",
    "RoederPlugin",
    "WecklPlugin",
]
