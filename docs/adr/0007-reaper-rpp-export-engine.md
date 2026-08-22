# 0007. Direct .RPP file manipulation for Reaper project export

> **Status**: Accepted (implemented; Workflow A complete, Workflow B partial)
> **Date**: 2026-08-22 (retroactively documented; original implementation predates this doc)

## Context

Beyond plain MIDI file export, there was a need to integrate generated drum
tracks directly into Reaper DAW projects — placing section markers (intro,
verse, chorus, ...) at the correct time positions, and optionally importing
a MIDI track, without requiring the user to manually align anything after
generation. Reaper's native project format is a plain-text `.rpp` file with
a documented (if not officially specified) element syntax.

## Decision

Manipulate `.rpp` files directly and immutably via the `rpp` Python library:
a low-level `ReaperEngine` (`midi_drums/export/reaper/engine.py`, marker/
region/element construction and bars-to-seconds time math) wrapped by a
high-level `ReaperExporter` (`midi_drums/export/reaper/exporter.py`).
**Workflow A** (`Song` → markers written into a project file) was
implemented first and is the primary path — `export_with_markers()` always
takes an input project and writes a *new* output file, never mutating the
original in place, so a failed or unexpected export never corrupts a user's
working project. **Workflow B** (parse an existing project's markers →
generate `Song` structure aligned to them) was scoped as secondary and
shipped only partially: CLI/API surface exists via metadata-file or
manual-structure input, but parsing markers directly out of an existing
`.rpp` file was left unimplemented.

This Python-side engine is a different layer from the Lua-side REAPER panel
integration ([[0001-unified-reaper-panel]]): the panel shells out to the
`midi-drums` CLI and handles markers/regions/MIDI-import on the REAPER
scripting side via REAPER's own API, while this ADR's engine is for
generating a standalone `.rpp` project file from Python without REAPER
running at all.

## Consequences

- Export is safe by construction — the immutable input/output split means a
  botched export can't corrupt an existing project file; the user just
  discards the bad output and re-runs.
- Marker color and MIDI-track-insertion-into-the-same-file remain partially
  TODO (`midi_drums/export/reaper/models.py`'s hex-to-Reaper-color
  conversion, `exporter.py`'s "add MIDI track" path) — both are still
  hardcoded/no-op'd, tracked as open cleanup items rather than resolved by
  this decision.
- Workflow B's marker-parsing half (`.rpp` → `Song`) is unimplemented;
  callers must supply structure via metadata file or explicit
  `--structure` flag instead of round-tripping an existing project's
  markers.
- No dependency on `reapy` (live Reaper control) was taken — this stays a
  pure offline file-manipulation approach, deliberately simpler than a
  live-control integration would have been.

## References

- Original design/status doc has been removed now that this ADR captures
  its decisions — see `claudedocs/archive/2026-08-21_docs-cleanup/REAPER_INTEGRATION.md`
  in git history prior to this ADR's introduction for the full text.
- Shipped in `midi_drums/export/reaper/` (`engine.py`, `exporter.py`,
  `models.py`); compat re-export at `midi_drums/exporters/__init__.py`
- Related, different layer: [[0001-unified-reaper-panel]] (Lua-side panel,
  shells out to the CLI rather than manipulating `.rpp` files from Python)
