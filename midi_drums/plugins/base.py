"""Base classes for plugin system."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Type
from pathlib import Path
import importlib
import pkgutil
import logging

from ..models.pattern import Pattern
from ..models.song import GenerationParameters, Fill


logger = logging.getLogger(__name__)


class GenrePlugin(ABC):
    """Base class for genre-specific pattern generators."""

    @property
    @abstractmethod
    def genre_name(self) -> str:
        """Name of the genre this plugin handles."""
        pass

    @property
    @abstractmethod
    def supported_styles(self) -> List[str]:
        """List of style variations supported by this genre."""
        pass

    @abstractmethod
    def generate_pattern(self,
                        section: str,
                        parameters: GenerationParameters) -> Pattern:
        """Generate a pattern for the specified section and parameters.

        Args:
            section: Section type ('verse', 'chorus', 'bridge', etc.)
            parameters: Generation parameters including style, complexity, etc.

        Returns:
            Generated Pattern instance
        """
        pass

    @abstractmethod
    def get_common_fills(self) -> List[Fill]:
        """Get common fill patterns for this genre."""
        pass

    def get_section_variations(self, section: str) -> List[Pattern]:
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


class DrummerPlugin(ABC):
    """Base class for drummer style modifiers."""

    @property
    @abstractmethod
    def drummer_name(self) -> str:
        """Name of the drummer this plugin emulates."""
        pass

    @property
    @abstractmethod
    def compatible_genres(self) -> List[str]:
        """List of genres this drummer style works well with."""
        pass

    @abstractmethod
    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply drummer-specific style modifications to a pattern.

        Args:
            pattern: Base pattern to modify

        Returns:
            Modified pattern with drummer's style applied
        """
        pass

    @abstractmethod
    def get_signature_fills(self) -> List[Fill]:
        """Get fill patterns characteristic of this drummer."""
        pass

    def is_compatible_with_genre(self, genre: str) -> bool:
        """Check if this drummer style is compatible with the genre."""
        return genre in self.compatible_genres

    def get_style_parameters(self) -> Dict[str, float]:
        """Get style-specific parameter adjustments.

        Returns dict with parameter names and their adjusted values.
        Default implementation returns empty dict.
        """
        return {}


class PluginRegistry:
    """Registry for managing genre and drummer plugins."""

    def __init__(self):
        self._genre_plugins: Dict[str, GenrePlugin] = {}
        self._drummer_plugins: Dict[str, DrummerPlugin] = {}

    def register_genre_plugin(self, plugin: GenrePlugin) -> None:
        """Register a genre plugin."""
        genre_name = plugin.genre_name.lower()
        if genre_name in self._genre_plugins:
            logger.warning(f"Overriding existing genre plugin for '{genre_name}'")
        self._genre_plugins[genre_name] = plugin
        logger.info(f"Registered genre plugin: {genre_name}")

    def register_drummer_plugin(self, plugin: DrummerPlugin) -> None:
        """Register a drummer plugin."""
        drummer_name = plugin.drummer_name.lower()
        if drummer_name in self._drummer_plugins:
            logger.warning(f"Overriding existing drummer plugin for '{drummer_name}'")
        self._drummer_plugins[drummer_name] = plugin
        logger.info(f"Registered drummer plugin: {drummer_name}")

    def get_genre_plugin(self, genre: str) -> Optional[GenrePlugin]:
        """Get genre plugin by name."""
        return self._genre_plugins.get(genre.lower())

    def get_drummer_plugin(self, drummer: str) -> Optional[DrummerPlugin]:
        """Get drummer plugin by name."""
        return self._drummer_plugins.get(drummer.lower())

    def get_available_genres(self) -> List[str]:
        """Get list of available genre names."""
        return list(self._genre_plugins.keys())

    def get_available_drummers(self) -> List[str]:
        """Get list of available drummer names."""
        return list(self._drummer_plugins.keys())

    def get_styles_for_genre(self, genre: str) -> List[str]:
        """Get available styles for a genre."""
        plugin = self.get_genre_plugin(genre)
        return plugin.supported_styles if plugin else []

    def get_compatible_drummers_for_genre(self, genre: str) -> List[str]:
        """Get drummers compatible with the given genre."""
        return [name for name, plugin in self._drummer_plugins.items()
                if plugin.is_compatible_with_genre(genre)]


class PluginManager:
    """Main plugin management system."""

    def __init__(self):
        self.registry = PluginRegistry()

    def discover_plugins(self, plugin_dirs: Optional[List[Path]] = None) -> None:
        """Auto-discover and load plugins from specified directories.

        Args:
            plugin_dirs: List of directories to search. If None, searches default locations.
        """
        if plugin_dirs is None:
            # Default plugin directories
            plugin_dirs = [
                Path(__file__).parent / "genres",
                Path(__file__).parent / "drummers"
            ]

        for plugin_dir in plugin_dirs:
            if plugin_dir.exists() and plugin_dir.is_dir():
                self._load_plugins_from_directory(plugin_dir)

    def _load_plugins_from_directory(self, plugin_dir: Path) -> None:
        """Load plugins from a specific directory."""
        logger.info(f"Loading plugins from: {plugin_dir}")

        # Add the directory to Python path temporarily
        import sys
        if str(plugin_dir.parent) not in sys.path:
            sys.path.insert(0, str(plugin_dir.parent))

        try:
            # Import all Python modules in the directory
            package_name = plugin_dir.name
            for finder, name, ispkg in pkgutil.iter_modules([str(plugin_dir)]):
                try:
                    module_name = f"{package_name}.{name}"
                    module = importlib.import_module(module_name)
                    self._register_plugins_from_module(module)
                except Exception as e:
                    logger.error(f"Failed to load plugin module {name}: {e}")
        except Exception as e:
            logger.error(f"Failed to load plugins from {plugin_dir}: {e}")

    def _register_plugins_from_module(self, module) -> None:
        """Register all plugin classes found in a module."""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and
                issubclass(attr, (GenrePlugin, DrummerPlugin)) and
                attr not in (GenrePlugin, DrummerPlugin)):
                try:
                    plugin_instance = attr()
                    if isinstance(plugin_instance, GenrePlugin):
                        self.registry.register_genre_plugin(plugin_instance)
                    elif isinstance(plugin_instance, DrummerPlugin):
                        self.registry.register_drummer_plugin(plugin_instance)
                except Exception as e:
                    logger.error(f"Failed to instantiate plugin {attr_name}: {e}")

    def generate_pattern(self,
                        genre: str,
                        section: str,
                        parameters: GenerationParameters) -> Optional[Pattern]:
        """Generate a pattern using the appropriate genre plugin."""
        plugin = self.registry.get_genre_plugin(genre)
        if not plugin:
            logger.error(f"No plugin found for genre: {genre}")
            return None

        if not plugin.validate_parameters(parameters):
            logger.error(f"Invalid parameters for genre {genre}: {parameters}")
            return None

        try:
            return plugin.generate_pattern(section, parameters)
        except Exception as e:
            logger.error(f"Error generating pattern for {genre}/{section}: {e}")
            return None

    def apply_drummer_style(self,
                           pattern: Pattern,
                           drummer: str) -> Optional[Pattern]:
        """Apply drummer style to a pattern."""
        plugin = self.registry.get_drummer_plugin(drummer)
        if not plugin:
            logger.error(f"No plugin found for drummer: {drummer}")
            return None

        try:
            return plugin.apply_style(pattern)
        except Exception as e:
            logger.error(f"Error applying drummer style {drummer}: {e}")
            return None

    # Convenience methods for accessing registry data
    def get_available_genres(self) -> List[str]:
        """Get list of available genres."""
        return self.registry.get_available_genres()

    def get_available_drummers(self) -> List[str]:
        """Get list of available drummers."""
        return self.registry.get_available_drummers()

    def get_styles_for_genre(self, genre: str) -> List[str]:
        """Get available styles for a genre."""
        return self.registry.get_styles_for_genre(genre)