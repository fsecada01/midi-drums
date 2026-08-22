"""Genre plugin implementations."""

from .funk import FunkGenrePlugin
from .jazz import JazzGenrePlugin
from .metal import MetalGenrePlugin
from .rock import RockGenrePlugin

__all__ = [
    "MetalGenrePlugin",
    "RockGenrePlugin",
    "JazzGenrePlugin",
    "FunkGenrePlugin",
]
