"""High-level Python API for drum generation."""

from __future__ import annotations

from pathlib import Path

from midi_drums.core.models.kit import DrumKit
from midi_drums.core.models.pattern import Pattern
from midi_drums.core.models.song import Song
from midi_drums.generation.engines.drum_generator import DrumGenerator


class DrumGeneratorAPI:
    """High-level API for drum generation with simplified interface."""

    def __init__(self):
        """Initialize the drum generator API."""
        self.generator = DrumGenerator()

    def create_song(
        self,
        genre: str,
        style: str = "default",
        tempo: int = 120,
        name: str | None = None,
        mapping: str = "ezdrummer3",
        mapping_file: str | Path | None = None,
        **kwargs,
    ) -> Song:
        """Create a complete song.

        Args:
            genre: Musical genre ('metal', 'rock', 'jazz', etc.)
            style: Style within genre ('death', 'power', etc.)
            tempo: Beats per minute
            name: Song name (auto-generated if None)
            mapping: MIDI mapping preset ('ezdrummer3', 'gm_drums', etc.).
                Ignored if a truthy drum_kit is also passed via kwargs -
                an explicit drum_kit takes precedence over mapping, but
                drum_kit=None falls back to mapping instead of being
                treated as an explicit choice.
            mapping_file: Path to a custom MIDI mapping JSON file (see
                DrumKit.from_json()). Takes precedence over mapping when
                supplied, but not over an explicit drum_kit kwarg.
            **kwargs: Additional parameters (complexity, humanization,
                drum_kit, etc.)

        Returns:
            Generated Song object
        """
        # An explicit, truthy drum_kit kwarg always takes precedence over
        # mapping/mapping_file. A caller passing drum_kit=None falls back
        # to mapping_file/mapping rather than leaving None to skip
        # DrumGenerator's own kit swap.
        if not kwargs.get("drum_kit"):
            kwargs["drum_kit"] = (
                DrumKit.from_json(mapping_file)
                if mapping_file
                else DrumKit.from_preset(mapping)
            )

        song = self.generator.create_song(genre, style, tempo, **kwargs)
        if name:
            song.name = name
        return song

    def generate_pattern(
        self,
        genre: str,
        section: str = "verse",
        style: str = "default",
        mapping: str = "ezdrummer3",
        **kwargs,
    ) -> Pattern | None:
        """Generate a single drum pattern.

        Args:
            genre: Musical genre
            section: Song section ('verse', 'chorus', 'bridge', etc.)
            style: Style within genre
            mapping: MIDI mapping preset ('ezdrummer3', 'gm_drums', etc.)
            **kwargs: Additional parameters

        Returns:
            Generated Pattern object or None if failed
        """
        return self.generator.generate_pattern(
            genre, section, style=style, **kwargs
        )

    def save_as_midi(self, song: Song, filename: str | Path) -> None:
        """Save song as MIDI file.

        Args:
            song: Song object to save
            filename: Output filename/path
        """
        output_path = Path(filename)
        self.generator.export_midi(song, output_path)

    def save_pattern_as_midi(
        self,
        pattern: Pattern,
        filename: str | Path,
        tempo: int = 120,
        mapping: str = "ezdrummer3",
    ) -> None:
        """Save pattern as MIDI file.

        Args:
            pattern: Pattern object to save
            filename: Output filename/path
            tempo: Tempo for the MIDI file
            mapping: MIDI mapping preset for export
        """
        output_path = Path(filename)
        drum_kit = DrumKit.from_preset(mapping)
        self.generator.export_pattern_midi(
            pattern, output_path, tempo, drum_kit=drum_kit
        )

    def list_genres(self) -> list[str]:
        """Get list of available genres."""
        return self.generator.get_available_genres()

    def list_styles(self, genre: str) -> list[str]:
        """Get list of styles for a genre.

        Args:
            genre: Genre name

        Returns:
            List of available styles
        """
        return self.generator.get_styles_for_genre(genre)

    def list_drummers(self) -> list[str]:
        """Get list of available drummers."""
        return self.generator.get_available_drummers()

    def list_mappings(self) -> dict[str, str]:
        """Get list of available MIDI mapping presets.

        Returns:
            Dictionary mapping preset names to descriptions
        """
        return DrumKit.list_presets()

    def get_song_info(self, song: Song) -> dict:
        """Get detailed information about a song.

        Args:
            song: Song object

        Returns:
            Dictionary with song information
        """
        return self.generator.get_song_info(song)

    # Convenience methods for common use cases
    def metal_song(
        self,
        style: str = "heavy",
        tempo: int = 155,
        complexity: float = 0.7,
        mapping: str = "ezdrummer3",
    ) -> Song:
        """Create a metal song with common parameters."""
        return self.create_song(
            genre="metal",
            style=style,
            tempo=tempo,
            complexity=complexity,
            dynamics=0.6,
            humanization=0.3,
            mapping=mapping,
        )

    def quick_export(
        self,
        genre: str,
        filename: str | Path,
        style: str = "default",
        tempo: int = 120,
        mapping: str = "ezdrummer3",
    ) -> None:
        """Quickly generate and export a song.

        Args:
            genre: Musical genre
            filename: Output MIDI filename
            style: Style within genre
            tempo: Beats per minute
            mapping: MIDI mapping preset
        """
        song = self.create_song(genre, style, tempo, mapping=mapping)
        self.save_as_midi(song, filename)

    def batch_generate(
        self, specs: list[dict], output_dir: str | Path
    ) -> list[Path]:
        """Generate multiple songs from specifications.

        Args:
            specs: List of song specification dictionaries
            output_dir: Directory to save files

        Returns:
            List of generated file paths

        Example:
            specs = [
                {'genre': 'metal', 'style': 'death', 'tempo': 180},
                {'genre': 'metal', 'style': 'power', 'tempo': 140}
            ]
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        generated_files = []

        for i, spec in enumerate(specs):
            genre = spec.get("genre", "metal")
            style = spec.get("style", "default")
            tempo = spec.get("tempo", 120)
            name = spec.get("name", f"{genre}_{style}_{i:02d}")
            extra = {
                k: v
                for k, v in spec.items()
                if k not in ("genre", "style", "tempo", "name")
            }

            song = self.create_song(genre, style, tempo, name=name, **extra)
            filename = output_path / f"{name}.mid"
            self.save_as_midi(song, filename)
            generated_files.append(filename)

        return generated_files

    # ------------------------------------------------------------------
    # Reaper convenience methods
    # ------------------------------------------------------------------

    def create_reaper_project(
        self,
        genre: str,
        style: str = "default",
        tempo: int | None = None,
        output_rpp: str = "project.rpp",
        with_midi: bool = True,
        input_rpp: str | None = None,
        complexity: float = 0.5,
        humanization: float = 0.3,
        drummer: str | None = None,
    ) -> dict:
        """Generate drums and create a Reaper project with genre-smart markers.

        This is the all-in-one convenience method: it generates a full Song
        with audio patterns using the plugin system, then exports both the
        Reaper project file (``.rpp``) and optionally a MIDI drum track.
        Section markers use per-section colors driven by the genre preset.

        Args:
            genre: Musical genre (``"metal"``, ``"rock"``, ``"jazz"``, etc.)
            style: Style within genre (``"doom"``, ``"classic"``, etc.)
            tempo: Tempo in BPM.  Uses the preset's ``default_tempo`` when
                ``None``.
            output_rpp: Destination Reaper project path (``"project.rpp"``).
            with_midi: When ``True`` (default), also export a ``.mid`` file
                alongside the ``.rpp``.  The MIDI path is derived from
                *output_rpp* by replacing the extension.
            input_rpp: Optional existing ``.rpp`` template to use as project
                base.
            complexity: Pattern complexity (0.0-1.0).
            humanization: Humanization level (0.0-1.0).
            drummer: Optional drummer name to apply (e.g. ``"bonham"``).

        Returns:
            Dictionary with keys:

            * ``rpp_path`` (str) – absolute path to the written ``.rpp``.
            * ``midi_path`` (str | None) – absolute path to the MIDI file, or
              ``None`` when *with_midi* is ``False``.
            * ``preset_used`` (:class:`~midi_drums.export.reaper.models.GenreStructurePreset`) –
              the preset that determined the song structure.
            * ``section_count`` (int) – number of sections / markers.

        Example:
            >>> api = DrumGeneratorAPI()
            >>> result = api.create_reaper_project(
            ...     "metal", "doom", tempo=70, output_rpp="doom.rpp"
            ... )
            >>> print(result["section_count"])
            6
        """
        from midi_drums.export.reaper.exporter import ReaperExporter
        from midi_drums.export.reaper.models import get_genre_preset

        preset = get_genre_preset(genre, style)
        resolved_tempo = tempo if tempo is not None else preset.default_tempo

        # Generate song with audio patterns
        song = self.create_song(
            genre=genre,
            style=style,
            tempo=resolved_tempo,
            complexity=complexity,
            humanization=humanization,
            drummer=drummer,
        )
        # Attach genre metadata so the exporter can pick section colors
        song.metadata["genre"] = genre
        song.metadata["style"] = style

        rpp_path = Path(output_rpp).resolve()
        midi_path = rpp_path.with_suffix(".mid") if with_midi else None

        exporter = ReaperExporter()
        exporter.export_complete(
            song=song,
            output_rpp=str(rpp_path),
            output_midi=str(midi_path) if midi_path else None,
            input_rpp=input_rpp,
        )

        return {
            "rpp_path": str(rpp_path),
            "midi_path": str(midi_path) if midi_path else None,
            "preset_used": preset,
            "section_count": len(song.sections),
        }

    def create_reaper_from_preset(
        self,
        genre: str,
        style: str = "*",
        tempo: int | None = None,
        output_rpp: str = "project.rpp",
        input_rpp: str | None = None,
    ) -> str:
        """Create a Reaper project with genre-smart structure markers only.

        No drum audio or MIDI is generated.  The section structure comes
        entirely from the :class:`~midi_drums.export.reaper.models.GenreStructurePreset`
        registry so this call is very fast.

        Args:
            genre: Genre name (e.g. ``"metal"``).
            style: Style within genre, or ``"*"`` to use the best available
                preset for that genre.
            tempo: Override BPM.  The preset's ``default_tempo`` is used when
                ``None``.
            output_rpp: Destination Reaper project path.
            input_rpp: Optional existing ``.rpp`` template.

        Returns:
            The absolute path to the written ``.rpp`` file.

        Example:
            >>> api = DrumGeneratorAPI()
            >>> path = api.create_reaper_from_preset("jazz", "swing",
            ...                                       output_rpp="jazz.rpp")
            >>> print(path)
            /absolute/path/to/jazz.rpp
        """
        from midi_drums.export.reaper.exporter import ReaperExporter

        exporter = ReaperExporter()
        exporter.export_with_genre_preset(
            genre=genre,
            style=style,
            output_rpp=output_rpp,
            tempo=tempo,
            input_rpp=input_rpp,
        )
        return str(Path(output_rpp).resolve())

    # ------------------------------------------------------------------
    # Bi-directional REAPER sidecar integration
    # ------------------------------------------------------------------

    def export_sections_json(self, song: Song, path: str | Path) -> None:
        """Write a JSON sidecar describing this song's section structure.

        The sidecar is consumed by the REAPER ``create_song_sections.lua``
        script when running in Python-driven mode.  It is also the output
        written by :meth:`save_as_midi_with_sidecar`.

        Args:
            song: Song whose sections should be serialised.
            path: Destination ``.json`` file path.
        """
        import json

        from midi_drums.export.reaper.models import get_section_color

        data = {
            "source": "python",
            "tempo": song.tempo,
            "time_signature": [
                song.time_signature.numerator,
                song.time_signature.denominator,
            ],
            "sections": [
                {
                    "name": section.name.title(),
                    "bars": section.bars,
                    "color": get_section_color(section.name),
                }
                for section in song.sections
            ],
        }
        Path(path).write_text(json.dumps(data, indent=2))

    def create_song_from_sections_json(
        self,
        json_path: str | Path,
        genre: str,
        style: str = "default",
        **kwargs,
    ) -> Song:
        """Generate a song whose structure mirrors a REAPER sidecar JSON file.

        Use this when REAPER drives the section layout: the Lua script writes
        ``midi_drums_sections.json``, then you call this method to produce
        MIDI that matches it bar-for-bar.

        Args:
            json_path: Path to the ``midi_drums_sections.json`` sidecar.
            genre: Genre to generate (``"metal"``, ``"rock"``, etc.).
            style: Style within the genre.
            **kwargs: Extra parameters forwarded to :meth:`create_song`
                (e.g. ``complexity``, ``humanization``).

        Returns:
            Song with section structure taken from the sidecar.

        Raises:
            FileNotFoundError: If *json_path* does not exist.
            ValueError: If the sidecar contains no sections.
        """
        import json

        sidecar = Path(json_path)
        if not sidecar.exists():
            raise FileNotFoundError(f"Sidecar not found: {sidecar}")

        data = json.loads(sidecar.read_text())
        sections = data.get("sections", [])
        if not sections:
            raise ValueError(f"No sections found in sidecar: {sidecar}")

        tempo = data.get("tempo", kwargs.pop("tempo", 120))
        structure = [(s["name"].lower(), s["bars"]) for s in sections]

        return self.create_song(
            genre=genre,
            style=style,
            tempo=tempo,
            structure=structure,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # song_creator song-map bridge (issue #53)
    # ------------------------------------------------------------------

    def create_song_from_song_map(
        self,
        song_map: str | Path | dict,
        genre: str,
        style: str = "default",
        **kwargs,
    ) -> Song:
        """Generate a song from a song_creator-shaped song-map.

        song_creator (a separate REAPER Lua arrangement tool) models a
        song as *regions* containing *segments*, each with its own
        ``bars``/``bpm``/``num``/``denom`` - letting one region contain a
        mid-section tempo or meter change (e.g. an 8-bar 4/4 verse with a
        2-bar 7/8 insert). This reads that shape directly into a Song
        whose Sections carry matching :class:`SongSegment` overrides.

        Args:
            song_map: Path to a song-map JSON file, an already-parsed
                dict in that shape, or a raw JSON string.
            genre: Genre to generate.
            style: Style within the genre.
            **kwargs: Extra parameters forwarded to :meth:`create_song`
                (e.g. ``complexity``, ``humanization``, ``mapping``). If
                ``tempo`` isn't given, the first segment's ``bpm`` across
                all regions is used as the song's global tempo.

        Returns:
            Song with segmented Sections mirroring the song-map's regions.

        Raises:
            FileNotFoundError: If *song_map* is a path that doesn't exist.
            ValueError: If the song-map has no regions, a region has no
                segments or no ``name``, or a region's name doesn't
                produce a matching generated section (shipped genre
                plugins fall back to a default pattern for unrecognized
                names rather than failing, so this last case is rare in
                practice).
        """
        import json

        from midi_drums.core.models.song import SongSegment
        from midi_drums.core.value_objects.time_signature import (
            TimeSignature,
        )

        if isinstance(song_map, dict):
            data = song_map
        else:
            text = str(song_map)
            candidate_path = Path(text)
            try:
                path_exists = candidate_path.exists()
            except OSError:
                # A JSON-content string (not a path) can exceed the OS's
                # max filename length, which raises ENAMETOOLONG on Linux
                # instead of returning False as it does on Windows.
                path_exists = False
            if path_exists:
                data = json.loads(candidate_path.read_text())
            elif candidate_path.suffix == ".json":
                raise FileNotFoundError(f"Song map not found: {text}")
            else:
                data = json.loads(text)

        regions = data.get("regions", [])
        if not regions:
            raise ValueError("No regions found in song map")

        structure: list[tuple[str, int]] = []
        region_segments: list[list[SongSegment]] = []
        for region in regions:
            region_name = region.get("name")
            if not region_name:
                raise ValueError(f"Region has no 'name': {region!r}")
            segments = [
                SongSegment(
                    bars=segment["bars"],
                    tempo=segment.get("bpm"),
                    time_signature=(
                        TimeSignature(segment["num"], segment["denom"])
                        if "num" in segment and "denom" in segment
                        else None
                    ),
                )
                for segment in region.get("segments", [])
            ]
            if not segments:
                raise ValueError(f"Region '{region_name}' has no segments")
            structure.append(
                (region_name.lower(), sum(s.bars for s in segments))
            )
            region_segments.append(segments)

        if kwargs.get("tempo") is None:
            first_tempo = next(
                (
                    seg.tempo
                    for segs in region_segments
                    for seg in segs
                    if seg.tempo
                ),
                None,
            )
            kwargs["tempo"] = first_tempo or 120

        song = self.create_song(
            genre=genre, style=style, structure=structure, **kwargs
        )

        if len(song.sections) != len(structure):
            generated_names = [s.name for s in song.sections]
            expected_names = [name for name, _ in structure]
            missing = [
                name for name in expected_names if name not in generated_names
            ] or ["(duplicate/ambiguous region names)"]
            raise ValueError(
                f"Could not generate a pattern for every region in "
                f"'{genre}/{style}': missing {missing}. Every region "
                "name must be a section name the genre plugin recognizes."
            )

        for section, segments in zip(
            song.sections, region_segments, strict=True
        ):
            section.segments = segments
        for section, region in zip(song.sections, regions, strict=True):
            if region.get("color_group"):
                section.section_parameters["color_group"] = region[
                    "color_group"
                ]
            section.section_parameters.setdefault(
                "display_name", region["name"]
            )

        song.metadata["song_map_title"] = data.get("title")
        song.metadata["color_groups"] = data.get("color_groups", {})

        return song

    def export_song_map_json(self, song: Song, path: str | Path) -> None:
        """Write a song_creator-shaped song-map JSON for this song.

        Reverse direction of :meth:`create_song_from_song_map`: serialises
        each Section (and its :class:`SongSegment` overrides, if any) into
        a song_creator region, so a segmented Song round-trips back into
        the format song_creator itself reads.

        Sections without segments are exported as a single implicit
        segment carrying the song's global tempo/time signature -
        song_creator has no concept of "no segments," every region has
        at least one.

        Args:
            song: Song to serialise.
            path: Destination ``.json`` file path.
        """
        import json

        color_groups = song.metadata.get("color_groups") or {
            "default": [120, 120, 120]
        }

        regions = []
        for section in song.sections:
            segments_json = [
                {
                    "bars": bars,
                    "bpm": tempo,
                    "num": time_sig.numerator,
                    "denom": time_sig.denominator,
                }
                for bars, tempo, time_sig in section.resolved_bar_specs(
                    song.tempo, song.time_signature
                )
            ]

            color_group = section.section_parameters.get("color_group") or next(
                iter(color_groups), "default"
            )
            display_name = section.section_parameters.get(
                "display_name", section.name.title()
            )

            regions.append(
                {
                    "name": display_name,
                    "color_group": color_group,
                    "segments": segments_json,
                }
            )

        data = {
            "title": song.metadata.get("song_map_title") or song.name,
            "color_groups": color_groups,
            "regions": regions,
        }
        Path(path).write_text(json.dumps(data, indent=2, sort_keys=True))

    def export_song_timeline_json(self, song: Song, path: str | Path) -> None:
        """Write a flat, resolved tempo/region timeline for a song.

        Resolves every section's segments (see :class:`SongSegment`) into
        a flat list of tempo/meter change points plus section start/end
        times - the same computation song_creator's
        ``song_model.compute_timeline`` performs, but kept deliberately
        flat (no nested JSON objects-within-objects) so
        ``reaper/create_song_sections.lua``'s regex-based sidecar parser
        can read it without needing a full JSON parser in Lua.

        Args:
            song: Song to resolve (segmented or not - non-segmented
                sections are treated as one implicit segment).
            path: Destination ``.json`` file path.
        """
        import json

        tempo_points = []
        regions = []
        t = 0.0
        last_key = None

        for section in song.sections:
            region_start = t
            display_name = section.section_parameters.get(
                "display_name", section.name.title()
            )
            color_group = section.section_parameters.get("color_group", "")

            bar_specs = section.resolved_bar_specs(
                song.tempo, song.time_signature
            )

            for bars, tempo, time_sig in bar_specs:
                key = (tempo, time_sig.numerator, time_sig.denominator)
                if key != last_key:
                    tempo_points.append(
                        {
                            "time": t,
                            "bpm": tempo,
                            "num": time_sig.numerator,
                            "denom": time_sig.denominator,
                        }
                    )
                    last_key = key
                t += bars * time_sig.beats_per_bar / (tempo / 60.0)

            regions.append(
                {
                    "name": display_name,
                    "color_group": color_group,
                    "start_time": region_start,
                    "end_time": t,
                }
            )

        color_groups_source = song.metadata.get("color_groups") or {}
        color_groups = [
            {"name": name, "r": rgb[0], "g": rgb[1], "b": rgb[2]}
            for name, rgb in color_groups_source.items()
            if isinstance(rgb, (list, tuple)) and len(rgb) == 3
        ]

        data = {
            "tempo_points": tempo_points,
            "regions": regions,
            "color_groups": color_groups,
            "total_time": t,
        }
        Path(path).write_text(json.dumps(data, indent=2))

    def save_as_midi_with_sidecar(
        self, song: Song, filename: str | Path
    ) -> Path:
        """Save MIDI and write a JSON sidecar alongside it.

        Convenience wrapper that calls :meth:`save_as_midi` and then
        :meth:`export_sections_json` in one step.  The sidecar path is
        the same as *filename* but with a ``.json`` extension.

        Args:
            song: Song to export.
            filename: Output ``.mid`` file path.

        Returns:
            Path to the written sidecar ``.json`` file.
        """
        output_path = Path(filename)
        self.save_as_midi(song, output_path)
        sidecar_path = output_path.with_suffix(".json")
        self.export_sections_json(song, sidecar_path)
        return sidecar_path

    def list_genre_presets(self) -> dict[str, list[str]]:
        """List all available genre/style structure presets.

        Returns:
            Dictionary mapping genre names to lists of available style names.

        Example:
            >>> api = DrumGeneratorAPI()
            >>> presets = api.list_genre_presets()
            >>> print(presets["metal"])
            ['breakdown', 'death', 'doom', 'heavy', 'power', 'progressive', 'thrash']
        """
        from midi_drums.export.reaper.models import list_genre_presets

        return list_genre_presets()
