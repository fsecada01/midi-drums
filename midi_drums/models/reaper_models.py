"""Data models for Reaper integration."""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Color constants for section types
# ---------------------------------------------------------------------------

#: Professional hex colors keyed by section type name.
SECTION_COLORS: dict[str, str] = {
    "intro": "#808080",
    "outro": "#808080",
    "verse": "#0066CC",
    "chorus": "#CC3300",
    "bridge": "#009900",
    "solo": "#FF9900",
    "breakdown": "#990099",
    "blast_section": "#FF0000",
    "head": "#FFD700",
    "head_out": "#FFD700",
    "groove": "#FF6600",
    "interlude": "#666699",
    "shout": "#FF6600",
    "solos": "#FF9900",
}

#: Fallback color when a section type is not in the registry.
DEFAULT_SECTION_COLOR: str = "#FF5733"


def get_section_color(section_name: str) -> str:
    """Return the canonical hex color for *section_name*.

    Falls back to :data:`DEFAULT_SECTION_COLOR` when the name is not
    found in :data:`SECTION_COLORS`.

    Args:
        section_name: Section type name (e.g. ``"verse"``, ``"chorus"``).

    Returns:
        Hex color string such as ``"#0066CC"``.
    """
    return SECTION_COLORS.get(section_name.lower(), DEFAULT_SECTION_COLOR)


# ---------------------------------------------------------------------------
# Marker
# ---------------------------------------------------------------------------


@dataclass
class Marker:
    """Reaper marker representation.

    Attributes:
        position_seconds: Time position in seconds
        name: Marker display name
        color: Marker color (hex string like "#FF5733" or integer)
        marker_id: Unique marker identifier (auto-assigned if not provided)
    """

    position_seconds: float
    name: str
    color: str = "#FF5733"  # Default orange
    marker_id: int | None = None

    def to_rpp_list(self) -> list:
        """Convert to RPP marker list format.

        Returns:
            List in format: ["MARKER", id, position, "name", color, flags]

        Example:
            >>> marker = Marker(8.0, "Verse", marker_id=2)
            >>> marker.to_rpp_list()
            ['MARKER', '2', '8.0', 'Verse', '0', '0']
        """
        # Convert hex color to integer if needed (simplified for now)
        color_int = "0"  # TODO: Convert hex to Reaper format (0x01BBGGRR)

        return [
            "MARKER",
            str(self.marker_id if self.marker_id else "1"),
            f"{self.position_seconds:.6f}",
            self.name,
            color_int,
            "0",  # Flags (0 = regular marker)
        ]

    @classmethod
    def from_rpp_list(cls, rpp_list: list) -> Marker:
        """Create Marker from RPP list format.

        Args:
            rpp_list: List in format ["MARKER", id, position, name, ...]

        Returns:
            Marker instance

        Example:
            >>> rpp_data = ["MARKER", "2", "8.0", "Verse", "0", "0"]
            >>> marker = Marker.from_rpp_list(rpp_data)
            >>> marker.name
            'Verse'
        """
        if rpp_list[0] != "MARKER":
            raise ValueError(f"Expected 'MARKER' tag, got '{rpp_list[0]}'")

        marker_id = int(rpp_list[1])
        position = float(rpp_list[2])
        name = rpp_list[3]

        return cls(
            position_seconds=position,
            name=name,
            color="#FF5733",  # Default
            marker_id=marker_id,
        )


# ---------------------------------------------------------------------------
# ReaperTrack
# ---------------------------------------------------------------------------


@dataclass
class ReaperTrack:
    """Reaper track representation.

    Attributes:
        name: Track name
        midi_source: Path to MIDI file (optional)
        volume: Track volume (0.0-1.0, default 1.0)
        pan: Stereo pan (-1.0 to 1.0, default 0.0)
    """

    name: str
    midi_source: str | None = None
    volume: float = 1.0
    pan: float = 0.0

    def __post_init__(self):
        """Validate track parameters."""
        if not 0.0 <= self.volume <= 2.0:
            raise ValueError(f"Volume must be 0.0-2.0, got {self.volume}")
        if not -1.0 <= self.pan <= 1.0:
            raise ValueError(f"Pan must be -1.0 to 1.0, got {self.pan}")


# ---------------------------------------------------------------------------
# Genre structure preset models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SectionTemplate:
    """Template describing a single song section within a genre preset.

    Attributes:
        name: Section type name (``"verse"``, ``"chorus"``, etc.)
        bars: Default number of bars for this section
        marker_color: Hex color used for this section's Reaper marker
        label: Human-readable display label (e.g. ``"Verse 1"``)
    """

    name: str
    bars: int
    marker_color: str
    label: str


@dataclass(frozen=True)
class GenreStructurePreset:
    """Describes the canonical song structure for a genre/style combination.

    Attributes:
        genre: Genre name (e.g. ``"metal"``, ``"jazz"``).
        style: Style within the genre, or ``"*"`` for a generic fallback.
        tempo_range: ``(min_bpm, max_bpm)`` typical range for this preset.
        time_signature: ``(numerator, denominator)`` e.g. ``(4, 4)``.
        sections: Ordered list of :class:`SectionTemplate` instances.
        marker_theme: Mapping of ``section_type -> hex_color`` overrides.
    """

    genre: str
    style: str
    tempo_range: tuple[int, int]
    time_signature: tuple[int, int]
    sections: tuple[SectionTemplate, ...]
    marker_theme: dict[str, str] = field(default_factory=dict)

    @property
    def default_tempo(self) -> int:
        """Return the midpoint of the tempo range."""
        lo, hi = self.tempo_range
        return (lo + hi) // 2

    def section_color(self, section_name: str) -> str:
        """Return the marker color for *section_name* according to this preset.

        Checks :attr:`marker_theme` first, then falls back to
        :func:`get_section_color`.

        Args:
            section_name: Section type name.

        Returns:
            Hex color string.
        """
        return self.marker_theme.get(
            section_name.lower(), get_section_color(section_name)
        )


# ---------------------------------------------------------------------------
# Preset registry helpers
# ---------------------------------------------------------------------------


def _sec(
    name: str,
    bars: int,
    label: str = "",
    color: str | None = None,
) -> SectionTemplate:
    """Shorthand factory for :class:`SectionTemplate`.

    Args:
        name: Section type name.
        bars: Number of bars.
        label: Display label (auto-generated from *name* if omitted).
        color: Explicit hex color override (uses :func:`get_section_color` if
            omitted).

    Returns:
        Frozen :class:`SectionTemplate` instance.
    """
    resolved_color = color if color is not None else get_section_color(name)
    resolved_label = label if label else name.replace("_", " ").title()
    return SectionTemplate(
        name=name,
        bars=bars,
        marker_color=resolved_color,
        label=resolved_label,
    )


# ---------------------------------------------------------------------------
# GENRE_STRUCTURE_PRESETS registry
# ---------------------------------------------------------------------------

#: Registry mapping ``(genre, style)`` tuples to :class:`GenreStructurePreset`
#: instances.  Use :func:`get_genre_preset` for look-up with fallback logic.
GENRE_STRUCTURE_PRESETS: dict[tuple[str, str], GenreStructurePreset] = {
    # -----------------------------------------------------------------------
    # Metal — Heavy
    # -----------------------------------------------------------------------
    ("metal", "heavy"): GenreStructurePreset(
        genre="metal",
        style="heavy",
        tempo_range=(130, 180),
        time_signature=(4, 4),
        sections=(
            _sec("intro", 4, "Intro"),
            _sec("verse", 8, "Verse 1"),
            _sec("chorus", 8, "Chorus 1"),
            _sec("verse", 8, "Verse 2"),
            _sec("chorus", 8, "Chorus 2"),
            _sec("bridge", 4, "Bridge"),
            _sec("solo", 8, "Solo"),
            _sec("chorus", 8, "Chorus 3"),
            _sec("outro", 4, "Outro"),
        ),
        marker_theme={
            "intro": "#8B0000",
            "outro": "#8B0000",
            "verse": "#CC4400",
            "chorus": "#FF2200",
            "bridge": "#AA3300",
            "solo": "#FF8800",
        },
    ),
    # -----------------------------------------------------------------------
    # Metal — Death
    # -----------------------------------------------------------------------
    ("metal", "death"): GenreStructurePreset(
        genre="metal",
        style="death",
        tempo_range=(160, 240),
        time_signature=(4, 4),
        sections=(
            _sec("intro", 2, "Intro"),
            _sec("verse", 4, "Verse 1"),
            _sec("blast_section", 4, "Blast Section"),
            _sec("verse", 4, "Verse 2"),
            _sec("chorus", 4, "Chorus"),
            _sec("breakdown", 4, "Breakdown"),
            _sec("outro", 2, "Outro"),
        ),
        marker_theme={
            "intro": "#550000",
            "outro": "#330000",
            "verse": "#880000",
            "blast_section": "#FF0000",
            "chorus": "#CC0000",
            "breakdown": "#660033",
        },
    ),
    # -----------------------------------------------------------------------
    # Metal — Doom
    # -----------------------------------------------------------------------
    ("metal", "doom"): GenreStructurePreset(
        genre="metal",
        style="doom",
        tempo_range=(60, 90),
        time_signature=(4, 4),
        sections=(
            _sec("intro", 8, "Intro"),
            _sec("verse", 16, "Verse 1"),
            _sec("chorus", 8, "Chorus 1"),
            _sec("verse", 16, "Verse 2"),
            _sec("bridge", 8, "Bridge"),
            _sec("outro", 8, "Outro"),
        ),
        marker_theme={
            "intro": "#4B0082",
            "outro": "#4B0082",
            "verse": "#6A0DAD",
            "chorus": "#8B008B",
            "bridge": "#551A8B",
        },
    ),
    # -----------------------------------------------------------------------
    # Metal — Thrash
    # -----------------------------------------------------------------------
    ("metal", "thrash"): GenreStructurePreset(
        genre="metal",
        style="thrash",
        tempo_range=(160, 220),
        time_signature=(4, 4),
        sections=(
            _sec("intro", 4, "Intro"),
            _sec("verse", 8, "Verse 1"),
            _sec("chorus", 8, "Chorus 1"),
            _sec("verse", 8, "Verse 2"),
            _sec("chorus", 8, "Chorus 2"),
            _sec("breakdown", 4, "Breakdown"),
            _sec("solo", 8, "Solo"),
            _sec("outro", 4, "Outro"),
        ),
        marker_theme={
            "intro": "#CC3300",
            "outro": "#CC3300",
            "verse": "#FF4400",
            "chorus": "#FF6600",
            "breakdown": "#990000",
            "solo": "#FF8800",
        },
    ),
    # -----------------------------------------------------------------------
    # Metal — Power
    # -----------------------------------------------------------------------
    ("metal", "power"): GenreStructurePreset(
        genre="metal",
        style="power",
        tempo_range=(140, 190),
        time_signature=(4, 4),
        sections=(
            _sec("intro", 4, "Intro"),
            _sec("verse", 8, "Verse 1"),
            _sec("chorus", 8, "Chorus 1"),
            _sec("verse", 8, "Verse 2"),
            _sec("chorus", 8, "Chorus 2"),
            _sec("bridge", 4, "Bridge"),
            _sec("solo", 8, "Solo"),
            _sec("chorus", 8, "Chorus 3"),
            _sec("outro", 4, "Outro"),
        ),
        marker_theme={
            "intro": "#003399",
            "outro": "#003399",
            "verse": "#0055CC",
            "chorus": "#FFD700",
            "bridge": "#0077AA",
            "solo": "#FFAA00",
        },
    ),
    # -----------------------------------------------------------------------
    # Metal — Progressive
    # -----------------------------------------------------------------------
    ("metal", "progressive"): GenreStructurePreset(
        genre="metal",
        style="progressive",
        tempo_range=(110, 170),
        time_signature=(4, 4),
        sections=(
            _sec("intro", 8, "Intro"),
            _sec("verse", 12, "Verse 1"),
            _sec("chorus", 8, "Chorus 1"),
            _sec("verse", 12, "Verse 2"),
            _sec("interlude", 8, "Interlude"),
            _sec("chorus", 8, "Chorus 2"),
            _sec("outro", 8, "Outro"),
        ),
        marker_theme={
            "intro": "#006666",
            "outro": "#006666",
            "verse": "#008080",
            "chorus": "#00AAAA",
            "interlude": "#005566",
        },
    ),
    # -----------------------------------------------------------------------
    # Metal — Breakdown (standalone style)
    # -----------------------------------------------------------------------
    ("metal", "breakdown"): GenreStructurePreset(
        genre="metal",
        style="breakdown",
        tempo_range=(100, 160),
        time_signature=(4, 4),
        sections=(
            _sec("intro", 4, "Intro"),
            _sec("verse", 8, "Verse 1"),
            _sec("breakdown", 8, "Breakdown 1"),
            _sec("verse", 8, "Verse 2"),
            _sec("breakdown", 8, "Breakdown 2"),
            _sec("outro", 4, "Outro"),
        ),
        marker_theme={
            "intro": "#330033",
            "outro": "#330033",
            "verse": "#660066",
            "breakdown": "#990099",
        },
    ),
    # -----------------------------------------------------------------------
    # Rock — Classic
    # -----------------------------------------------------------------------
    ("rock", "classic"): GenreStructurePreset(
        genre="rock",
        style="classic",
        tempo_range=(120, 160),
        time_signature=(4, 4),
        sections=(
            _sec("intro", 4, "Intro"),
            _sec("verse", 8, "Verse 1"),
            _sec("chorus", 8, "Chorus 1"),
            _sec("verse", 8, "Verse 2"),
            _sec("chorus", 8, "Chorus 2"),
            _sec("bridge", 4, "Bridge"),
            _sec("solo", 8, "Solo"),
            _sec("outro", 4, "Outro"),
        ),
        marker_theme={
            "intro": "#555555",
            "outro": "#555555",
            "verse": "#0066CC",
            "chorus": "#CC3300",
            "bridge": "#009900",
            "solo": "#FF9900",
        },
    ),
    # -----------------------------------------------------------------------
    # Rock — Blues
    # -----------------------------------------------------------------------
    ("rock", "blues"): GenreStructurePreset(
        genre="rock",
        style="blues",
        tempo_range=(80, 120),
        time_signature=(4, 4),
        sections=(
            _sec("intro", 8, "Intro"),
            _sec("verse", 12, "Verse 1"),
            _sec("chorus", 8, "Chorus 1"),
            _sec("verse", 12, "Verse 2"),
            _sec("solo", 12, "Solo"),
            _sec("outro", 8, "Outro"),
        ),
        marker_theme={
            "intro": "#003366",
            "outro": "#003366",
            "verse": "#0055AA",
            "chorus": "#003388",
            "solo": "#336699",
        },
    ),
    # -----------------------------------------------------------------------
    # Jazz — Swing
    # -----------------------------------------------------------------------
    ("jazz", "swing"): GenreStructurePreset(
        genre="jazz",
        style="swing",
        tempo_range=(120, 200),
        time_signature=(4, 4),
        sections=(
            _sec("intro", 8, "Intro"),
            _sec("head", 16, "Head"),
            _sec("solos", 32, "Solos"),
            _sec("head_out", 16, "Head Out"),
            _sec("outro", 8, "Outro"),
        ),
        marker_theme={
            "intro": "#8B6914",
            "outro": "#8B6914",
            "head": "#FFD700",
            "solos": "#FFA500",
            "head_out": "#DAA520",
        },
    ),
    # -----------------------------------------------------------------------
    # Jazz — Bebop
    # -----------------------------------------------------------------------
    ("jazz", "bebop"): GenreStructurePreset(
        genre="jazz",
        style="bebop",
        tempo_range=(180, 280),
        time_signature=(4, 4),
        sections=(
            _sec("intro", 4, "Intro"),
            _sec("head", 8, "Head"),
            _sec("solos", 24, "Solos"),
            _sec("shout", 8, "Shout Chorus"),
            _sec("head_out", 8, "Head Out"),
        ),
        marker_theme={
            "intro": "#003366",
            "head": "#336699",
            "solos": "#6699CC",
            "shout": "#0066FF",
            "head_out": "#003399",
        },
    ),
    # -----------------------------------------------------------------------
    # Funk — Classic
    # -----------------------------------------------------------------------
    ("funk", "classic"): GenreStructurePreset(
        genre="funk",
        style="classic",
        tempo_range=(95, 125),
        time_signature=(4, 4),
        sections=(
            _sec("intro", 4, "Intro"),
            _sec("groove", 8, "Groove 1"),
            _sec("verse", 8, "Verse 1"),
            _sec("chorus", 8, "Chorus 1"),
            _sec("bridge", 4, "Bridge"),
            _sec("groove", 8, "Groove 2"),
            _sec("outro", 4, "Outro"),
        ),
        marker_theme={
            "intro": "#663300",
            "outro": "#663300",
            "groove": "#FF6600",
            "verse": "#CC4400",
            "chorus": "#FF3300",
            "bridge": "#994400",
        },
    ),
}

# ---------------------------------------------------------------------------
# Generic fallback preset
# ---------------------------------------------------------------------------

_GENERIC_FALLBACK = GenreStructurePreset(
    genre="generic",
    style="*",
    tempo_range=(100, 160),
    time_signature=(4, 4),
    sections=(
        _sec("intro", 4, "Intro"),
        _sec("verse", 8, "Verse 1"),
        _sec("chorus", 8, "Chorus 1"),
        _sec("verse", 8, "Verse 2"),
        _sec("chorus", 8, "Chorus 2"),
        _sec("bridge", 4, "Bridge"),
        _sec("outro", 4, "Outro"),
    ),
)


def get_genre_preset(genre: str, style: str = "*") -> GenreStructurePreset:
    """Return the best-matching :class:`GenreStructurePreset` for *genre*/*style*.

    Look-up order:

    1. Exact ``(genre, style)`` match.
    2. Generic ``(genre, "*")`` match (not yet in registry — returns fallback
       with genre name substituted).
    3. The built-in :data:`_GENERIC_FALLBACK`.

    Args:
        genre: Genre name (case-insensitive).
        style: Style within genre, or ``"*"`` for best available.

    Returns:
        A :class:`GenreStructurePreset` — never raises.
    """
    g = genre.lower()
    s = style.lower()

    # 1. Exact match
    if (g, s) in GENRE_STRUCTURE_PRESETS:
        return GENRE_STRUCTURE_PRESETS[(g, s)]

    # 2. Wildcard style: find any preset for this genre
    genre_presets = [
        v for (pg, _ps), v in GENRE_STRUCTURE_PRESETS.items() if pg == g
    ]
    if genre_presets:
        return genre_presets[0]

    # 3. Generic fallback
    return _GENERIC_FALLBACK


def list_genre_presets() -> dict[str, list[str]]:
    """Return a mapping of genre -> list[style] for all registered presets.

    Returns:
        Dictionary such as ``{"metal": ["heavy", "death", ...], "rock": [...]}``.
    """
    result: dict[str, list[str]] = {}
    for genre, style in GENRE_STRUCTURE_PRESETS:
        result.setdefault(genre, []).append(style)
    # Sort styles alphabetically within each genre
    for genre in result:
        result[genre].sort()
    return result
