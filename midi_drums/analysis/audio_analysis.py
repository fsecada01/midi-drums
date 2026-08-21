"""Onset detection for the riff-lock feature.

Analyzes a rendered audio riff (guitar/bass, typically a single bar) and
returns a :class:`~midi_drums.core.value_objects.riff_accent.RiffAccentMap`
describing where its rhythmic accents fall, for
:class:`midi_drums.modifications.riff_lock.RiffLockTransform` to lock kicks
onto.

``librosa``/``soundfile``/``numpy`` are imported inside :func:`analyze_riff`
rather than at module scope - see the package docstring in
``midi_drums/analysis/__init__.py`` for why.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from midi_drums.config import TIMING
from midi_drums.core.value_objects.riff_accent import RiffAccent, RiffAccentMap

if TYPE_CHECKING:
    from midi_drums.core.value_objects.time_signature import TimeSignature

logger = logging.getLogger(__name__)

# Maps the CLI/API's human-friendly grid names to a beat-fraction interval,
# reusing the existing TIMING constants rather than redeclaring them.
_GRID_INTERVALS: dict[str, float] = {
    "8th": TIMING.EIGHTH,
    "16th": TIMING.SIXTEENTH,
    "32nd": TIMING.THIRTY_SECOND,
    "8th_triplet": TIMING.EIGHTH_TRIPLET,
    "16th_triplet": TIMING.SIXTEENTH_TRIPLET,
}


def analyze_riff(
    wav_path: str | Path,
    tempo: float,
    time_signature: TimeSignature | None = None,
    grid: str = "16th",
    offset_beats: float = 0.0,
    strong_threshold: float = 0.6,
    audio_offset: float | None = None,
    audio_duration: float | None = None,
) -> RiffAccentMap:
    """Detect rhythmic accents in an audio riff and fold them into one bar.

    Args:
        wav_path: Path to the rendered/exported riff audio file.
        tempo: Tempo in BPM used to convert onset times (seconds) to beats.
            No tempo inference is performed - the caller (REAPER project
            tempo, or an explicit --tempo) must supply this.
        time_signature: Bar length for wraparound. Defaults to 4/4.
        grid: Quantization grid - one of "8th", "16th", "32nd",
            "8th_triplet", "16th_triplet".
        offset_beats: Beats to subtract before wrapping, correcting for the
            selected audio not starting exactly on a bar line (see the
            REAPER Lua script's bar-alignment computation).
        strong_threshold: Onset-strength threshold (0.0-1.0, after
            normalization) used only for the mean-quantization-error
            sanity-check log below - RiffAccentMap.strong_accents() applies
            its own threshold independently at consumption time.
        audio_offset: Seconds into the file to start reading (for a shared
            multi-riff audio source file).
        audio_duration: Seconds to read starting at audio_offset.

    Returns:
        RiffAccentMap with all accents folded into [0, beats_per_bar) and
        deduplicated to at most one accent per grid slot (max strength
        wins).

    Raises:
        ValueError: If grid is not a recognized name, or tempo <= 0.
    """
    if grid not in _GRID_INTERVALS:
        raise ValueError(
            f"Unknown grid {grid!r} - expected one of "
            f"{sorted(_GRID_INTERVALS)}"
        )
    if tempo <= 0:
        raise ValueError(f"tempo must be positive, got {tempo}")

    import librosa
    import numpy as np

    from midi_drums.core.value_objects.time_signature import (
        TimeSignature as _TimeSignature,
    )

    time_signature = time_signature or _TimeSignature(4, 4)
    beats_per_bar = time_signature.beats_per_bar
    grid_interval = _GRID_INTERVALS[grid]

    y, sr = librosa.load(
        str(wav_path),
        sr=None,
        offset=audio_offset or 0.0,
        duration=audio_duration,
    )

    if y.size == 0:
        logger.warning("analyze_riff: %s decoded to zero samples", wav_path)
        return RiffAccentMap(accents=(), beats_per_bar=beats_per_bar)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    # Peak-pick without backtracking to get frames at the actual onset
    # envelope peak (needed for a meaningful strength reading), then
    # backtrack those same peaks separately for accurate onset *timing*.
    # Reading strength from the backtracked frame instead (the naive
    # single-call approach) reads near-zero values, since backtrack moves
    # the frame to the local minimum *before* the peak, not the peak
    # itself.
    peak_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr, backtrack=False
    )
    if len(peak_frames) == 0:
        logger.warning("analyze_riff: no onsets detected in %s", wav_path)
        return RiffAccentMap(accents=(), beats_per_bar=beats_per_bar)

    onset_frames = librosa.onset.onset_backtrack(peak_frames, onset_env)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    raw_strengths = onset_env[peak_frames]
    max_strength = float(np.max(raw_strengths)) if raw_strengths.size else 1.0
    if max_strength <= 0:
        max_strength = 1.0

    seconds_per_beat = 60.0 / tempo

    # slot -> (quantized_position, best_strength, sum_abs_error, count)
    slots: dict[int, list[float]] = {}
    for onset_time, raw_strength in zip(
        onset_times, raw_strengths, strict=True
    ):
        beat_position = (onset_time / seconds_per_beat) - offset_beats
        wrapped = beat_position % beats_per_bar
        slot_index = round(wrapped / grid_interval)
        quantized = (slot_index * grid_interval) % beats_per_bar
        strength = float(raw_strength) / max_strength
        error = abs(wrapped - quantized)
        # Handle wraparound error too (e.g. wrapped=3.99, quantized=0.0)
        error = min(error, beats_per_bar - error)

        existing = slots.get(slot_index)
        if existing is None or strength > existing[1]:
            slots[slot_index] = [quantized, strength, error]
        else:
            # Still accumulate error for the sanity-check average even when
            # this onset lost the max-strength dedup.
            existing[2] = max(existing[2], error)

    # Only strong accents are used for the tempo sanity-check - weak/noise
    # onsets naturally quantize worse and would swamp the signal.
    errors = [
        entry[2] for entry in slots.values() if entry[1] >= strong_threshold
    ]
    if errors:
        mean_error = sum(errors) / len(errors)
        if mean_error > 0.3 * grid_interval:
            logger.warning(
                "analyze_riff: mean quantization error %.3f beats exceeds "
                "30%% of the %s grid interval (%.3f beats) - the supplied "
                "--tempo (%s BPM) is likely wrong for %s",
                mean_error,
                grid,
                grid_interval,
                tempo,
                wav_path,
            )

    accents = tuple(
        RiffAccent(position=quantized, strength=strength)
        for quantized, strength, _error in slots.values()
    )
    return RiffAccentMap(accents=accents, beats_per_bar=beats_per_bar)
