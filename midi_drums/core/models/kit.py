"""Drum kit configuration and instrument mapping."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from midi_drums.core.value_objects.drum_instrument import DrumInstrument

# DrumInstrument's baseline values are EZDrummer-3-specific for these 8
# extended hi-hat articulations (notes 22, 24-26, 60-63), which aren't real
# GM Level 1 percussion notes. Presets that claim GM-standard/GM-baseline
# compatibility need to collapse each to its nearest true GM equivalent -
# closed-hat family to CLOSED_HH, open-hat family to OPEN_HH - otherwise a
# strict GM-compliant sampler would receive wrong notes (e.g. 60 = GM "Hi
# Bongo", not an open hi-hat).
_GM_HIHAT_COLLAPSE: dict[DrumInstrument, int] = {
    DrumInstrument.CLOSED_HH_EDGE: DrumInstrument.CLOSED_HH.value,
    DrumInstrument.CLOSED_HH_TIP: DrumInstrument.CLOSED_HH.value,
    DrumInstrument.TIGHT_HH_EDGE: DrumInstrument.CLOSED_HH.value,
    DrumInstrument.TIGHT_HH_TIP: DrumInstrument.CLOSED_HH.value,
    DrumInstrument.OPEN_HH_1: DrumInstrument.OPEN_HH.value,
    DrumInstrument.OPEN_HH_2: DrumInstrument.OPEN_HH.value,
    DrumInstrument.OPEN_HH_3: DrumInstrument.OPEN_HH.value,
    DrumInstrument.OPEN_HH_MAX: DrumInstrument.OPEN_HH.value,
}


@dataclass
class VelocityRange:
    """Velocity range for realistic drum dynamics."""

    min_velocity: int = 1
    max_velocity: int = 127
    default_velocity: int = 100

    def __post_init__(self):
        """Validate velocity values."""
        for vel in [
            self.min_velocity,
            self.max_velocity,
            self.default_velocity,
        ]:
            if not 1 <= vel <= 127:
                raise ValueError(f"Velocity must be 1-127, got {vel}")
        if self.min_velocity > self.max_velocity:
            raise ValueError("Min velocity cannot be greater than max velocity")


@dataclass
class DrumKit:
    """Drum kit configuration with instrument mappings and velocity ranges."""

    name: str = "Standard Kit"
    channel: int = 9  # MIDI channel 10 (0-indexed)

    # Velocity ranges for different instrument types
    velocity_ranges: dict[str, VelocityRange] = field(
        default_factory=lambda: {
            "kick": VelocityRange(95, 120, 110),
            "snare": VelocityRange(90, 127, 115),
            "hihat": VelocityRange(60, 100, 80),
            "toms": VelocityRange(85, 115, 100),
            "cymbals": VelocityRange(70, 120, 95),
            "ride": VelocityRange(65, 100, 80),
        }
    )

    # Custom instrument mappings (overrides default DrumInstrument values)
    custom_mappings: dict[DrumInstrument, int] = field(default_factory=dict)

    def get_midi_note(self, instrument: DrumInstrument) -> int:
        """Get MIDI note number for an instrument."""
        return self.custom_mappings.get(instrument, instrument.value)

    def get_velocity_range(self, instrument: DrumInstrument) -> VelocityRange:
        """Get velocity range for an instrument category."""
        # Map instruments to velocity categories
        category_map = {
            DrumInstrument.KICK: "kick",
            DrumInstrument.SNARE: "snare",
            DrumInstrument.RIM: "snare",
            DrumInstrument.CLOSED_HH: "hihat",
            DrumInstrument.CLOSED_HH_EDGE: "hihat",
            DrumInstrument.CLOSED_HH_TIP: "hihat",
            DrumInstrument.TIGHT_HH_EDGE: "hihat",
            DrumInstrument.TIGHT_HH_TIP: "hihat",
            DrumInstrument.PEDAL_HH: "hihat",
            DrumInstrument.OPEN_HH: "hihat",
            DrumInstrument.OPEN_HH_1: "hihat",
            DrumInstrument.OPEN_HH_2: "hihat",
            DrumInstrument.OPEN_HH_3: "hihat",
            DrumInstrument.OPEN_HH_MAX: "hihat",
            DrumInstrument.MID_TOM: "toms",
            DrumInstrument.FLOOR_TOM: "toms",
            DrumInstrument.CRASH: "cymbals",
            DrumInstrument.SPLASH: "cymbals",
            DrumInstrument.CHINA: "cymbals",
            DrumInstrument.RIDE: "ride",
            DrumInstrument.RIDE_BELL: "ride",
        }

        category = category_map.get(instrument, "toms")
        return self.velocity_ranges.get(category, VelocityRange())

    def randomize_velocity(self, instrument: DrumInstrument) -> int:
        """Get a randomized velocity within the instrument's range."""
        import random

        velocity_range = self.get_velocity_range(instrument)
        return random.randint(
            velocity_range.min_velocity, velocity_range.max_velocity
        )

    @classmethod
    def create_ezdrummer3_kit(cls) -> "DrumKit":
        """Create an EZDrummer 3 compatible kit configuration."""
        return cls(
            name="EZDrummer 3 Kit",
            channel=9,
            # DrumInstrument's own note values already target EZDrummer 3's
            # extended hi-hat articulations (see drum_instrument.py), so no
            # overrides are needed here - this preset is the enum baseline.
            custom_mappings={},
        )

    @classmethod
    def create_metal_kit(cls) -> "DrumKit":
        """Create a metal-optimized kit configuration."""
        return cls(
            name="Metal Kit",
            channel=9,
            velocity_ranges={
                "kick": VelocityRange(100, 127, 120),  # Powerful kicks
                "snare": VelocityRange(110, 127, 120),  # Loud snares
                "hihat": VelocityRange(40, 90, 65),  # Quieter hihats
                "toms": VelocityRange(90, 120, 105),  # Punchy toms
                "cymbals": VelocityRange(90, 127, 110),  # Loud crashes
                "ride": VelocityRange(60, 100, 80),  # Controlled ride
            },
        )

    @classmethod
    def create_jazz_kit(cls) -> "DrumKit":
        """Create a jazz-optimized kit configuration."""
        return cls(
            name="Jazz Kit",
            channel=9,
            velocity_ranges={
                "kick": VelocityRange(70, 100, 85),  # Softer kicks
                "snare": VelocityRange(60, 110, 85),  # Dynamic snares
                "hihat": VelocityRange(40, 85, 65),  # Subtle hihats
                "toms": VelocityRange(60, 105, 80),  # Warm toms
                "cymbals": VelocityRange(50, 100, 75),  # Controlled crashes
                "ride": VelocityRange(45, 90, 70),  # Prominent ride
            },
        )

    @classmethod
    def create_studio_drummer3_kit(cls) -> "DrumKit":
        """Create a Studio Drummer 3 (Native Instruments) compatible kit.

        No Studio Drummer 3-specific note research has been done yet (see
        claudedocs/research_vendor_drum_midi_maps_20260812.md) - this uses
        the GM-collapsed baseline so it's at least GM-compliant rather than
        silently inheriting EZDrummer 3's non-GM extended hi-hat notes.
        """
        return cls(
            name="Studio Drummer 3 Kit",
            channel=9,
            custom_mappings=dict(_GM_HIHAT_COLLAPSE),
        )

    @classmethod
    def create_addictive_drums_kit(cls) -> "DrumKit":
        """Create an Addictive Drums 2 (XLN Audio) compatible kit.

        No Addictive Drums 2-specific note research has been done yet (see
        claudedocs/research_vendor_drum_midi_maps_20260812.md) - this uses
        the GM-collapsed baseline so it's at least GM-compliant rather than
        silently inheriting EZDrummer 3's non-GM extended hi-hat notes.
        """
        return cls(
            name="Addictive Drums 2 Kit",
            channel=9,
            custom_mappings=dict(_GM_HIHAT_COLLAPSE),
        )

    @classmethod
    def create_bfd3_kit(cls) -> "DrumKit":
        """Create a BFD3 (FXpansion) compatible kit using common mappings.

        No BFD3-specific note research has been done yet (see
        claudedocs/research_vendor_drum_midi_maps_20260812.md) - this uses
        the GM-collapsed baseline so it's at least GM-compliant rather than
        silently inheriting EZDrummer 3's non-GM extended hi-hat notes.
        """
        return cls(
            name="BFD3 Kit",
            channel=9,
            custom_mappings=dict(_GM_HIHAT_COLLAPSE),
        )

    @classmethod
    def create_gm_drums_kit(cls) -> "DrumKit":
        """Create a General MIDI standard drum kit."""
        return cls(
            name="General MIDI Drums",
            channel=9,
            custom_mappings=dict(_GM_HIHAT_COLLAPSE),
        )

    @classmethod
    def create_modo_drums_kit(cls) -> "DrumKit":
        """Create a MODO Drums (IK Multimedia) compatible kit.

        No MODO Drums-specific note research has been done yet (see
        claudedocs/research_vendor_drum_midi_maps_20260812.md) - this uses
        the GM-collapsed baseline so it's at least GM-compliant rather than
        silently inheriting EZDrummer 3's non-GM extended hi-hat notes.
        """
        return cls(
            name="MODO Drums Kit",
            channel=9,
            custom_mappings=dict(_GM_HIHAT_COLLAPSE),
        )

    @classmethod
    def create_ml_drums_kit(cls) -> "DrumKit":
        """Create an ML Drums (ML Sound Lab) compatible kit.

        No ML Drums-specific note research has been done yet (see
        claudedocs/research_vendor_drum_midi_maps_20260812.md) - this uses
        the GM-collapsed baseline so it's at least GM-compliant rather than
        silently inheriting EZDrummer 3's non-GM extended hi-hat notes.
        """
        return cls(
            name="ML Drums Kit",
            channel=9,
            custom_mappings=dict(_GM_HIHAT_COLLAPSE),
        )

    @classmethod
    def from_preset(cls, preset_name: str) -> "DrumKit":
        """Create a drum kit from a preset name.

        Args:
            preset_name: Name of the preset ('ezdrummer3', 'studio_drummer3',
                        'addictive_drums', 'bfd3', 'gm_drums', 'modo_drums',
                        'ml_drums', 'metal', 'jazz')

        Returns:
            DrumKit configured for the specified preset

        Raises:
            ValueError: If preset_name is not recognized
        """
        preset_map = {
            "ezdrummer3": cls.create_ezdrummer3_kit,
            "ez_drummer_3": cls.create_ezdrummer3_kit,
            "studio_drummer3": cls.create_studio_drummer3_kit,
            "studio_drummer_3": cls.create_studio_drummer3_kit,
            "addictive_drums": cls.create_addictive_drums_kit,
            "addictive_drums_2": cls.create_addictive_drums_kit,
            "bfd3": cls.create_bfd3_kit,
            "gm_drums": cls.create_gm_drums_kit,
            "gm": cls.create_gm_drums_kit,
            "general_midi": cls.create_gm_drums_kit,
            "modo_drums": cls.create_modo_drums_kit,
            "ml_drums": cls.create_ml_drums_kit,
            "metal": cls.create_metal_kit,
            "jazz": cls.create_jazz_kit,
        }

        preset_name_lower = preset_name.lower()
        if preset_name_lower not in preset_map:
            available_presets = ", ".join(sorted(preset_map.keys()))
            raise ValueError(
                f"Unknown preset '{preset_name}'. "
                f"Available presets: {available_presets}"
            )

        return preset_map[preset_name_lower]()

    @classmethod
    def from_dict(cls, data: dict) -> "DrumKit":
        """Create a drum kit from a plain dict, e.g. loaded from JSON.

        Expected shape::

            {
                "name": "My Custom Kit",              # optional
                "channel": 9,                          # optional, default 9
                "mappings": {"KICK": 36, "SNARE": 38}  # DrumInstrument
                                                        # names -> MIDI note
            }

        Instruments not present in "mappings" fall back to their
        `DrumInstrument` enum value via `get_midi_note()`.

        Args:
            data: Mapping dict as described above.

        Returns:
            DrumKit configured with the supplied custom mappings.

        Raises:
            ValueError: If a mapping key isn't a known DrumInstrument name,
                or a mapping value isn't a valid MIDI note number.
        """
        custom_mappings: dict[DrumInstrument, int] = {}
        for instrument_name, note in data.get("mappings", {}).items():
            try:
                instrument = DrumInstrument[instrument_name.upper()]
            except KeyError as exc:
                raise ValueError(
                    f"Unknown drum instrument in mapping file: "
                    f"'{instrument_name}'"
                ) from exc
            try:
                custom_mappings[instrument] = int(note)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid MIDI note for '{instrument_name}': {note!r}"
                ) from exc

        return cls(
            name=data.get("name", "Custom Kit"),
            channel=data.get("channel", 9),
            custom_mappings=custom_mappings,
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "DrumKit":
        """Create a drum kit from a JSON mapping file.

        Args:
            path: Path to a JSON file matching the `from_dict()` shape.

        Returns:
            DrumKit configured with the supplied custom mappings.
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def list_presets(cls) -> dict[str, str]:
        """List all available drum kit presets.

        Returns:
            Dictionary mapping preset names to descriptions
        """
        return {
            "ezdrummer3": ("EZDrummer 3 (Toontrack) - GM Extended compatible"),
            "studio_drummer3": (
                "Studio Drummer 3 (Native Instruments) - Multiple kit mappings"
            ),
            "addictive_drums": (
                "Addictive Drums 2 (XLN Audio) - GM compatible with keymap"
            ),
            "bfd3": "BFD3 (FXpansion) - Flexible mapping system",
            "gm_drums": "General MIDI Drums - Standard GM drum mapping",
            "modo_drums": "MODO Drums (IK Multimedia) - GM convention",
            "ml_drums": "ML Drums (ML Sound Lab) - Modular drum sampler",
            "metal": "Metal Kit - Optimized for heavy music genres",
            "jazz": "Jazz Kit - Optimized for jazz and acoustic styles",
        }
