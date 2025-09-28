#!/usr/bin/env python3
"""
Generate a heavy metal drum track MIDI file mapped for EZDrummer 3.
"""
import random

try:
    from midiutil import MIDIFile
except ImportError:
    print(
        "Error: midiutil library not found. "
        "Install with 'pip install midiutil'."
    )
    exit(1)

# EZDrummer 3 drum mapping
DRUM_MAP = {
    "kick": 36,
    "snare": 38,
    "rim": 40,
    "closed_hh": 42,
    "pedal_hh": 44,
    "open_hh": 46,
    "mid_tom": 47,
    "floor_tom": 43,
    "crash": 49,
    "ride": 51,
    "ride_bell": 53,
}

CHANNEL = 9  # MIDI channel 10 (0-indexed)
TEMPO = 155  # BPM
VOLUME_RANGES = {
    "kick": (95, 110),
    "snare": (100, 120),
    "hh": (70, 90),
    "toms": (95, 110),
    "ride": (70, 90),
}


def rand_velocity(kind):
    lo, hi = VOLUME_RANGES[kind]
    return random.randint(lo, hi)


def add_intro(midi, start_bar):
    for b in range(4):
        bar_time = (start_bar + b) * 4.0
        # Crash on beat 1
        midi.addNote(
            0,
            CHANNEL,
            DRUM_MAP["crash"],
            bar_time + 0.0,
            1.0,
            rand_velocity("ride"),
        )
        # Kick on every quarter
        for i in range(4):
            midi.addNote(
                0,
                CHANNEL,
                DRUM_MAP["kick"],
                bar_time + i * 1.0,
                1.0,
                rand_velocity("kick"),
            )
        # Snare rimshot on beat 3
        midi.addNote(
            0,
            CHANNEL,
            DRUM_MAP["rim"],
            bar_time + 2.0,
            1.0,
            rand_velocity("snare"),
        )


def add_fill(midi, start_bar):
    bar_time = start_bar * 4.0
    pattern = ["snare", "mid_tom", "floor_tom"]
    for i in range(16):  # 16th notes
        inst = pattern[i % len(pattern)]
        note = DRUM_MAP["snare"] if inst == "snare" else DRUM_MAP[inst]
        kind = "snare" if inst == "snare" else "toms"
        midi.addNote(
            0, CHANNEL, note, bar_time + i * 0.25, 0.25, rand_velocity(kind)
        )


def add_verse(midi, start_bar, bars=16):
    for b in range(bars):
        bar_time = (start_bar + b) * 4.0
        # Kick on 1, 1.75, 3
        for offset in (0.0, 0.75, 2.0):
            midi.addNote(
                0,
                CHANNEL,
                DRUM_MAP["kick"],
                bar_time + offset,
                1.0,
                rand_velocity("kick"),
            )
        # Snare on 2 and 4
        for offset in (1.0, 3.0):
            midi.addNote(
                0,
                CHANNEL,
                DRUM_MAP["snare"],
                bar_time + offset,
                1.0,
                rand_velocity("snare"),
            )
        # Closed hi-hat 8ths
        for i in range(8):
            midi.addNote(
                0,
                CHANNEL,
                DRUM_MAP["closed_hh"],
                bar_time + i * 0.5,
                0.5,
                rand_velocity("hh"),
            )


def add_breakdown(midi, start_bar, bars=8):
    for b in range(bars):
        bar_time = (start_bar + b) * 4.0
        # Kick on 1, 2.5, 3.5
        for offset in (0.0, 1.5, 2.5):
            midi.addNote(
                0,
                CHANNEL,
                DRUM_MAP["kick"],
                bar_time + offset,
                1.0,
                rand_velocity("kick"),
            )
        # Snare rimshot on 3
        midi.addNote(
            0,
            CHANNEL,
            DRUM_MAP["rim"],
            bar_time + 2.0,
            1.0,
            rand_velocity("snare"),
        )
        # Tom groove on beats 2 and 4
        for offset in (1.0, 3.0):
            midi.addNote(
                0,
                CHANNEL,
                DRUM_MAP["mid_tom"],
                bar_time + offset,
                1.0,
                rand_velocity("toms"),
            )


def add_chorus(midi, start_bar, bars=16):
    for b in range(bars):
        bar_time = (start_bar + b) * 4.0
        # Double-kick shuffle: kick on quarter and 8th
        for beat in range(4):
            base = bar_time + beat * 1.0
            midi.addNote(
                0, CHANNEL, DRUM_MAP["kick"], base, 0.5, rand_velocity("kick")
            )
            midi.addNote(
                0,
                CHANNEL,
                DRUM_MAP["kick"],
                base + 0.5,
                0.5,
                rand_velocity("kick"),
            )
        # Ride on quarters
        for i in range(4):
            midi.addNote(
                0,
                CHANNEL,
                DRUM_MAP["ride"],
                bar_time + i * 1.0,
                1.0,
                rand_velocity("ride"),
            )
        # Snare on 2 and 4
        for offset in (1.0, 3.0):
            midi.addNote(
                0,
                CHANNEL,
                DRUM_MAP["snare"],
                bar_time + offset,
                1.0,
                rand_velocity("snare"),
            )


def add_outro_fill(midi, start_bar):
    bar_time = start_bar * 4.0
    # Descending fill
    order = ["floor_tom", "mid_tom", "snare", "floor_tom"]
    for i, inst in enumerate(order):
        note = DRUM_MAP["snare"] if inst == "snare" else DRUM_MAP[inst]
        kind = "snare" if inst == "snare" else "toms"
        midi.addNote(
            0, CHANNEL, note, bar_time + i * 1.0, 1.0, rand_velocity(kind)
        )
    # Crash at bar end
    midi.addNote(
        0,
        CHANNEL,
        DRUM_MAP["crash"],
        bar_time + 3.75,
        1.0,
        rand_velocity("ride"),
    )


def create_drum_track():
    track = 0
    midi = MIDIFile(1)
    midi.addTempo(track, 0, TEMPO)
    # Build structure
    add_intro(midi, 0)
    add_fill(midi, 4)
    add_verse(midi, 5, 16)
    add_fill(midi, 21)
    add_breakdown(midi, 22, 8)
    add_fill(midi, 30)
    add_chorus(midi, 31, 16)
    add_fill(midi, 47)
    add_verse(midi, 48, 16)
    add_fill(midi, 64)
    add_chorus(midi, 65, 16)
    add_outro_fill(midi, 81)
    # Write to file
    filename = "ezdrummer3_heavy_metal_porcaro_style.mid"
    with open(filename, "wb") as f:
        midi.writeFile(f)
    print(f"MIDI file written: {filename}")


if __name__ == "__main__":
    create_drum_track()
