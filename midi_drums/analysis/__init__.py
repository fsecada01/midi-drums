"""Audio analysis for MIDI Drums Generator.

Deliberately a sibling of ``midi_drums.ai``, not a submodule of it:
``midi_drums.ai.__init__`` eagerly imports the LangChain/pydantic-ai/loguru
LLM stack, and onset detection (DSP, no API keys, no network) has a
categorically different dependency shape from that. Importing anything in
this package must never require an LLM provider to be configured.

The ``librosa``/``soundfile`` dependency itself is imported lazily inside
``analyze_riff`` so that ``import midi_drums.analysis.audio_analysis`` stays
cheap to attempt-and-fail-cleanly when the ``audio`` extras group isn't
installed (``uv sync --group audio`).
"""

from midi_drums.analysis.audio_analysis import analyze_riff

__all__ = ["analyze_riff"]
