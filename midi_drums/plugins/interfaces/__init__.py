"""Plugin interfaces - GenrePlugin and DrummerPlugin base classes."""

from midi_drums.plugins.interfaces.drummer_plugin import DrummerPlugin
from midi_drums.plugins.interfaces.genre_plugin import GenrePlugin

__all__ = ["GenrePlugin", "DrummerPlugin"]
