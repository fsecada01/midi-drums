"""Tests for midi_drums.analysis.audio_analysis (onset detection).

Requires the `audio` extras group (librosa/soundfile) - skipped entirely
when not installed, per pytest.ini's `requires_audio` marker.
"""

import pytest

librosa = pytest.importorskip("librosa")
soundfile = pytest.importorskip("soundfile")
import numpy as np  # noqa: E402

from midi_drums.analysis.audio_analysis import analyze_riff  # noqa: E402
from midi_drums.core.value_objects.time_signature import (  # noqa: E402
    TimeSignature,
)

pytestmark = pytest.mark.requires_audio


def _synthesize_click_track(
    tmp_path,
    tempo=120.0,
    clicks_at_beats=(0.0, 1.0, 2.0, 3.0),
    sr=22050,
    lead_in_seconds=0.25,
):
    """Write a short click track WAV with clicks at the given beat positions.

    A short lead-in of silence precedes the first click - librosa's onset
    detector reliably misses onsets sitting exactly at sample 0 (no runway
    for the STFT window), and a real REAPER riff selection would virtually
    never start with silence-free sample 0 either, so this is both a test
    workaround and a more realistic fixture.
    """
    seconds_per_beat = 60.0 / tempo
    duration = lead_in_seconds + 4 * seconds_per_beat + 0.5
    y = np.zeros(int(duration * sr), dtype=np.float32)

    click_len = int(0.01 * sr)
    click = np.hanning(click_len).astype(np.float32)
    for beat in clicks_at_beats:
        start = int((lead_in_seconds + beat * seconds_per_beat) * sr)
        end = min(start + click_len, len(y))
        y[start:end] += click[: end - start]

    path = tmp_path / "click_track.wav"
    soundfile.write(str(path), y, sr)
    return path


def test_analyze_riff_recovers_click_positions(tmp_path):
    tempo = 120.0
    lead_in_seconds = 0.25
    path = _synthesize_click_track(
        tmp_path,
        tempo=tempo,
        clicks_at_beats=(0.0, 1.0, 2.0, 3.0),
        lead_in_seconds=lead_in_seconds,
    )

    # offset_beats corrects for the lead-in, same role the REAPER Lua
    # script's bar-alignment computation plays for a real riff selection.
    lead_in_beats = lead_in_seconds / (60.0 / tempo)
    accent_map = analyze_riff(
        path,
        tempo=tempo,
        time_signature=TimeSignature(4, 4),
        grid="16th",
        offset_beats=lead_in_beats,
    )

    assert len(accent_map) >= 3
    positions = sorted(a.position for a in accent_map.accents)
    for expected in (0.0, 1.0, 2.0, 3.0):
        assert any(
            abs(p - expected) < 0.2
            or abs(p - expected) > 4.0 - 0.2  # wraparound near 0.0
            for p in positions
        )


def test_analyze_riff_empty_audio_returns_empty_map(tmp_path):
    sr = 22050
    y = np.zeros(int(0.5 * sr), dtype=np.float32)  # 0.5s of silence
    path = tmp_path / "silence.wav"
    soundfile.write(str(path), y, sr)

    accent_map = analyze_riff(path, tempo=120.0)
    assert len(accent_map) == 0


def test_analyze_riff_rejects_bad_grid(tmp_path):
    path = _synthesize_click_track(tmp_path)
    with pytest.raises(ValueError):
        analyze_riff(path, tempo=120.0, grid="not_a_grid")


def test_analyze_riff_rejects_nonpositive_tempo(tmp_path):
    path = _synthesize_click_track(tmp_path)
    with pytest.raises(ValueError):
        analyze_riff(path, tempo=0)
