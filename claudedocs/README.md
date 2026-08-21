# Claude Code Scratch & Archive Directory

This directory is **scratch space and historical archive only**. Anything
meant to last — living reference docs, decision records — belongs in
[`docs/`](../docs/README.md) instead. This split was introduced by
[issue #59](https://github.com/fsecada01/midi-drums/issues/59) after
`claudedocs/`, `docs/`, and `docs/superpowers/` had scattered overlapping
design docs, completion reports, and research notes with no single
indexed home.

## What goes here

- **Scratch notes** for a Claude Code session in progress: a working
  design doc for a feature not yet built, a short-lived research note.
  Once the feature ships (or the doc is superseded), it either becomes an
  ADR (if it recorded a significant decision — see
  [`docs/adr/`](../docs/adr/)), moves into `docs/` (if it's ongoing
  living reference), or moves into `archive/` below (if it's pure
  historical record with no forward-looking value).
- **Archive** (`archive/YYYY-MM[-DD]_topic/`) — completed design docs,
  implementation plans, and closed research, kept for historical record.
  See [`archive/README.md`](archive/README.md) for the full topic index.

## What does NOT go here

- A doc that records *why* a significant, hard-to-reverse decision was
  made → write an ADR in `docs/adr/` instead (see that directory's
  `README.md` for when an ADR is warranted vs. not).
- A guide someone will reference going forward for how a shipped feature
  works → belongs in `docs/`, indexed from `docs/README.md`.

## Currently active (not yet archived)

- **[design_riff_snare_accents.md](design_riff_snare_accents.md)** - Design
  for a `SnareAccentReaction` modification, still being implemented (open
  questions unresolved as of this writing) — stays here until it ships,
  then either becomes an ADR or moves to `archive/`.

## See Also

- **[docs/README.md](../docs/README.md)** - The indexed home for living
  reference docs and ADRs
- **[CLAUDE.md](../CLAUDE.md)** - Main project guidance for Claude Code
- **[README.md](../README.md)** - User-facing project documentation
