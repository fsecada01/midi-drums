"""Genre plugin implementations."""

from .funk_refactored import FunkGenrePlugin
from .jazz_refactored import JazzGenrePlugin
from .metal_refactored import MetalGenrePlugin
from .rock_refactored import RockGenrePlugin

__all__ = [
    "MetalGenrePlugin",
    "RockGenrePlugin",
    "JazzGenrePlugin",
    "FunkGenrePlugin",
]
