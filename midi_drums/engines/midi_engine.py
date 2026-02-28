"""MIDI file generation engine."""

import copy
from pathlib import Path

try:
    from midiutil import MIDIFile
except ImportError:
    raise ImportError(
        "midiutil library not found. Install with 'pip install midiutil'."
    ) from None

from midi_drums.models.kit import DrumKit
from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Song


class MIDIEngine:
    """Engine for generating MIDI files from patterns and songs."""

    def __init__(self, drum_kit: DrumKit | None = None):
        """Initialize MIDI engine with optional drum kit configuration."""
        self.drum_kit = drum_kit or DrumKit.create_ezdrummer3_kit()

    def pattern_to_midi(self, pattern: Pattern, tempo: int = 120) -> MIDIFile:
        """Convert a single pattern to a MIDI file.

        Sorts beats and ensures durations don't overlap to prevent midiutil errors.
        """
        midi = MIDIFile(1)  # 1 track
        track = 0
        channel = self.drum_kit.channel

        # Set tempo
        midi.addTempo(track, 0, tempo)

        # Sort beats by position, then by instrument for consistent ordering
        sorted_beats = sorted(
            pattern.beats, key=lambda b: (b.position, b.instrument.value)
        )

        # Add pattern beats with overlap prevention
        for beat in sorted_beats:
            midi_note = self.drum_kit.get_midi_note(beat.instrument)

            # Cap duration to prevent overlap with next note
            # Use minimum of beat.duration or a safe short duration
            safe_duration = min(beat.duration, 0.2)

            midi.addNote(
                track=track,
                channel=channel,
                pitch=midi_note,
                time=beat.position,
                duration=safe_duration,
                volume=beat.velocity,
            )

        return midi

    def song_to_midi(self, song: Song) -> MIDIFile:
        """Convert a complete song to a MIDI file."""
        midi = MIDIFile(1)  # 1 track
        track = 0
        channel = self.drum_kit.channel

        # Set tempo
        midi.addTempo(track, 0, song.tempo)

        # Shared dedup set across all sections — see _add_section_to_midi for
        # why this must span the entire song rather than be per-section.
        added_note_ticks: set[tuple[int, int]] = set()

        current_bar = 0
        for section in song.sections:
            self._add_section_to_midi(
                midi,
                track,
                channel,
                section,
                current_bar,
                song,
                added_note_ticks,
            )
            current_bar += section.bars

        return midi

    def _add_section_to_midi(
        self,
        midi: MIDIFile,
        track: int,
        channel: int,
        section,
        current_bar: int,
        song: Song,
        added_note_ticks: set[tuple[int, int]] | None = None,
    ) -> None:
        """Add a song section to the MIDI file."""
        # midiutil uses int(time * ticks_per_quarter) to convert beat times to
        # ticks.  When multi-bar patterns or drummer timing modifications cause
        # two beats to map to the same tick for the same pitch, midiutil's
        # removeDuplicates collapses the NoteOn pair to one event while keeping
        # both NoteOff events (if they differ by even 1 tick), which then causes
        # deInterleaveNotes to crash with "pop from empty list".  We prevent
        # this by globally deduplicating on (midi_note, on_tick) before adding.
        # The caller (song_to_midi) passes a shared set spanning ALL sections.
        _TPQ = 960  # ticks per quarter – matches MIDIFile(1) default

        if added_note_ticks is None:
            added_note_ticks = set()

        beats_per_bar = song.time_signature.beats_per_bar

        for bar_num in range(section.bars):
            absolute_bar = current_bar + bar_num
            bar_start_time = absolute_bar * beats_per_bar

            # Get the effective pattern for this bar (considering variations)
            pattern = section.get_effective_pattern(bar_num)

            # Check if we should add a fill
            fill = None
            if song.global_parameters:
                fill = section.should_add_fill(
                    bar_num, song.global_parameters.fill_frequency
                )

            # Detect the natural bar-span of THIS bar's pattern so multi-bar
            # patterns (e.g. assigned via assign_pattern_to_section) are tiled
            # correctly. Computed per-bar so that single-bar variations inside
            # a multi-bar section still render all their beats (cycle_bar would
            # otherwise filter them to zero if computed from bar 0's pattern).
            if pattern.beats:
                _max_pos = max(b.position for b in pattern.beats)
                _pattern_bars = max(1, round((_max_pos + 1) / beats_per_bar))
            else:
                _pattern_bars = 1

            # For multi-bar patterns, only emit the beats belonging to the
            # current bar within the pattern cycle so that each bar gets its
            # own distinct slice rather than the full pattern being re-placed
            # from position 0 (which causes global-dedup collisions).
            if _pattern_bars > 1:
                cycle_bar = bar_num % _pattern_bars
                bar_beats = [
                    b
                    for b in pattern.beats
                    if int(b.position / beats_per_bar) == cycle_bar
                ]
                # Re-express positions relative to this bar
                adjusted_beats = []
                for b in bar_beats:
                    nb = copy.copy(b)
                    nb.position = b.position - cycle_bar * beats_per_bar
                    adjusted_beats.append(nb)
                beats_to_render = adjusted_beats
            else:
                beats_to_render = pattern.beats

            # Per-bar dedup: if drummer modifications created two beats at the
            # same (instrument, position) within a bar, keep the loudest.
            deduped: dict[tuple, object] = {}
            for beat in beats_to_render:
                key = (beat.instrument, round(beat.position, 6))
                if key not in deduped or beat.velocity > deduped[key].velocity:
                    deduped[key] = beat

            for beat in sorted(deduped.values(), key=lambda b: b.position):
                midi_note = self.drum_kit.get_midi_note(beat.instrument)
                absolute_time = bar_start_time + beat.position
                safe_duration = min(beat.duration, 0.2)

                # Global dedup: skip if this (pitch, on_tick) was already
                # added.  Multi-bar patterns can place beats at positions
                # beyond beats_per_bar, causing later bars to collide at the
                # same tick and producing unbalanced NoteOn/NoteOff pairs.
                on_tick = int(absolute_time * _TPQ)
                note_key = (midi_note, on_tick)
                if note_key in added_note_ticks:
                    continue
                added_note_ticks.add(note_key)

                midi.addNote(
                    track=track,
                    channel=channel,
                    pitch=midi_note,
                    time=absolute_time,
                    duration=safe_duration,
                    volume=beat.velocity,
                )

            # Add fill if present (replaces last part of the bar)
            if (
                fill and bar_num == section.bars - 1
            ):  # Add fill at end of section
                fill_start_time = bar_start_time + (
                    song.time_signature.beats_per_bar - 1.0
                )
                for beat in fill.pattern.beats:
                    if beat.position < 1.0:  # Only add beats within 1 bar
                        midi_note = self.drum_kit.get_midi_note(beat.instrument)
                        absolute_time = fill_start_time + beat.position
                        safe_duration = min(beat.duration, 0.2)

                        on_tick = int(absolute_time * _TPQ)
                        note_key = (midi_note, on_tick)
                        if note_key in added_note_ticks:
                            continue
                        added_note_ticks.add(note_key)

                        midi.addNote(
                            track=track,
                            channel=channel,
                            pitch=midi_note,
                            time=absolute_time,
                            duration=safe_duration,
                            volume=beat.velocity,
                        )

    def save_pattern_midi(
        self, pattern: Pattern, output_path: Path, tempo: int = 120
    ) -> None:
        """Save a pattern as a MIDI file."""
        midi = self.pattern_to_midi(pattern, tempo)
        with open(output_path, "wb") as f:
            midi.writeFile(f)

    def save_song_midi(self, song: Song, output_path: Path) -> None:
        """Save a complete song as a MIDI file."""
        midi = self.song_to_midi(song)
        with open(output_path, "wb") as f:
            midi.writeFile(f)

    def export_patterns_to_separate_files(
        self, patterns: list[Pattern], output_dir: Path, tempo: int = 120
    ) -> list[Path]:
        """Export multiple patterns to separate MIDI files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        output_files = []

        for i, pattern in enumerate(patterns):
            filename = f"{pattern.name or f'pattern_{i:02d}'}.mid"
            output_path = output_dir / filename
            self.save_pattern_midi(pattern, output_path, tempo)
            output_files.append(output_path)

        return output_files

    def create_multi_track_midi(
        self, patterns: list[Pattern], tempo: int = 120
    ) -> MIDIFile:
        """Create a multi-track MIDI file with each pattern on a
        separate track."""
        midi = MIDIFile(len(patterns))
        channel = self.drum_kit.channel

        # Set tempo on first track
        midi.addTempo(0, 0, tempo)

        for track, pattern in enumerate(patterns):
            # Add track name
            midi.addTrackName(track, 0, pattern.name or f"Pattern {track + 1}")

            # Add pattern beats
            for beat in pattern.beats:
                midi_note = self.drum_kit.get_midi_note(beat.instrument)
                midi.addNote(
                    track=track,
                    channel=channel,
                    pitch=midi_note,
                    time=beat.position,
                    duration=beat.duration,
                    volume=beat.velocity,
                )

        return midi

    def apply_humanization_to_midi(
        self,
        midi: MIDIFile,
        timing_variance: float = 0.02,
        velocity_variance: int = 10,
    ) -> MIDIFile:
        """Apply humanization effects to MIDI data.

        Note: This is a simplified implementation. Full humanization
        would require more sophisticated MIDI manipulation.
        """
        # This is a placeholder for more advanced humanization
        # Real implementation would need to modify the MIDI events directly
        return midi

    def get_midi_info(self, song: Song) -> dict:
        """Get information about the MIDI file that would be generated."""
        total_bars = song.total_bars()
        duration_seconds = song.total_duration_seconds()
        total_beats = sum(
            len(section.pattern.beats) * section.bars
            for section in song.sections
        )

        return {
            "total_bars": total_bars,
            "duration_seconds": duration_seconds,
            "total_beats": total_beats,
            "tempo": song.tempo,
            "time_signature": str(song.time_signature),
            "sections": [
                {
                    "name": section.name,
                    "bars": section.bars,
                    "pattern_beats": len(section.pattern.beats),
                }
                for section in song.sections
            ],
        }
