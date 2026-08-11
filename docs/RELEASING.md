# Releasing

This project ships **tagged GitHub Releases**, not PyPI packages. Users
install a specific version via:

```bash
uv tool install "git+https://github.com/fsecada01/midi-drums@v0.1.0"
```

or by cloning and checking out a tag directly.

## Versioning Policy

[Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.

The project is currently **pre-1.0** (`0.y.z`). Per the semver spec, that
means the public API may still change in backwards-incompatible ways between
minor versions - `0.1.0 -> 0.2.0` may contain breaking changes, not just
`0.x.0 -> 1.0.0`. Once the public API (see below) has held steady across a
few `0.x` releases without a breaking change, the project moves to `1.0.0`
and the stricter post-1.0 rules apply: breaking changes require a `MAJOR`
bump.

### What counts as "the public API"

- Every name in `midi_drums.__all__` (`DrumGenerator`, `Pattern`, `Beat`,
  `TimeSignature`, `Song`, `Section`, `GenerationParameters`).
- `midi_drums.api.python_api.DrumGeneratorAPI`'s public methods.
- The `midi-drums` CLI's documented commands and flags.
- The compatibility shims documented in `docs/DDD_ARCHITECTURE.md`
  (`midi_drums.exporters.ReaperExporter`,
  `midi_drums.plugins.base.{GenrePlugin,DrummerPlugin,PluginRegistry,PluginManager}`)
  - these are declared permanent; removing one is itself a breaking change.
- The MIDI output format/mapping defaults (EZDrummer 3 GM mapping) and the
  `.RPP` export format - changing these silently changes what users hear or
  see in their DAW, even if no Python signature changed.

### What does NOT require a breaking-change bump

- Adding new genres, styles, or drummer plugins.
- Adding new optional parameters with backwards-compatible defaults.
- Internal refactors that don't change the public API surface above (e.g.
  the epic #8 DDD re-architecture - four phases, zero breaking changes,
  verified by `TestPublicApiUnchanged` in each domain-migration test suite).
- Bug fixes that make behavior match documented behavior (unless the bug
  was itself widely depended upon - use judgment, note it in the CHANGELOG
  either way).

## Release Checklist

1. Move relevant `[Unreleased]` entries in `CHANGELOG.md` into a new
   `## [X.Y.Z] - YYYY-MM-DD` section (use the actual release date).
   Add the new version's compare-link and update the `[Unreleased]` link at
   the bottom of the file to diff from the new tag.
2. Bump the version in both places it's declared (they must match):
   - `pyproject.toml` -> `version = "X.Y.Z"`
   - `midi_drums/__init__.py` -> `__version__ = "X.Y.Z"`
3. Run the full local verification (same gates CI runs):
   ```bash
   uv run pytest -q
   uv run ruff check .
   uv run black --check .
   uv run isort --check-only .
   ```
4. Commit: `git commit -m "chore(release): vX.Y.Z"`.
5. Tag and push:
   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin main --tags
   ```
6. `.github/workflows/release.yml` picks up the tag push, verifies
   `pyproject.toml` and `midi_drums/__init__.py` both declare the tagged
   version, verifies `CHANGELOG.md` has a matching `## [X.Y.Z]` heading with
   content underneath it (fails the release if you forgot step 1 or 2),
   re-runs the test suite, and creates the GitHub Release with that
   section's content as the release notes.
7. Verify the release at
   `https://github.com/fsecada01/midi-drums/releases/tag/vX.Y.Z` looks right.

## Rolling Back a Bad Tag

If a tag was pushed before catching a problem, prefer a `PATCH` release that
fixes the issue over deleting/re-pushing the tag - once a tag is public,
someone may have already fetched it. Only delete a tag if it's had
effectively zero real-world exposure (pushed moments ago, no Release
published yet).
