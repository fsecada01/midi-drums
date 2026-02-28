"""
docs/make.py — Documentation builder for MIDI Drums Generator.

Generates an HTML API reference from Python docstrings using pdoc,
combined with custom static pages for guides, recipes, and tutorials.
The output is a self-contained static site suitable for GitHub Pages.

Usage:
    python docs/make.py                   # build -> docs/site/
    python docs/make.py --serve           # start dev server (localhost:8080)
    python docs/make.py --check           # verify pdoc, print config
    python docs/make.py -o /tmp/my-docs   # custom output directory

Requirements:
    pdoc >= 14  (uv pip install pdoc  OR  pip install pdoc)
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

DOCS_DIR = Path(__file__).parent
REPO_ROOT = DOCS_DIR.parent
PACKAGE = "midi_drums"
TEMPLATES_DIR = DOCS_DIR / "pdoc_templates"
DEFAULT_OUT = DOCS_DIR / "site"


# ── Environment bootstrap ─────────────────────────────────────────────────────


def _configure_environment() -> None:
    """Add repo root to sys.path so pdoc can import midi_drums."""
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


# ── Build ─────────────────────────────────────────────────────────────────────


def build(output_dir: Path) -> None:
    """Generate static HTML docs into *output_dir* via pdoc's Python API."""
    _configure_environment()

    import pdoc
    import pdoc.render

    pdoc.render.configure(
        template_directory=TEMPLATES_DIR,
        docformat="google",
        show_source=True,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    pdoc.pdoc(PACKAGE, output_directory=output_dir)

    # Copy custom site pages (home, quickstart, recipes, reaper) to output root.
    site_pages_dir = DOCS_DIR / "site-pages"
    if site_pages_dir.is_dir():
        pages = list(site_pages_dir.glob("*.html"))
        for page in pages:
            shutil.copy2(page, output_dir / page.name)
        print(f"  Copied {len(pages)} site page(s) from {site_pages_dir.name}/")


# ── Dev server ────────────────────────────────────────────────────────────────


def serve(host: str = "localhost", port: int = 8080) -> None:
    """Start pdoc's built-in live-reloading dev server."""
    _configure_environment()

    import pdoc.render
    import pdoc.web

    pdoc.render.configure(
        template_directory=TEMPLATES_DIR,
        docformat="google",
        show_source=True,
    )

    server = pdoc.web.DocServer((host, port), [PACKAGE])
    print(f"  Serving docs at http://{host}:{port}/")
    print("  Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")


# ── CLI ────────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build MIDI Drums Generator API docs with pdoc.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=DEFAULT_OUT,
        metavar="DIR",
        help="Output directory (default: docs/site/)",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start pdoc's built-in dev server instead of writing files",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Dev-server port (default: 8080)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify pdoc is available and print configuration, then exit",
    )
    args = parser.parse_args()

    try:
        import pdoc as _pdoc

        pdoc_version = _pdoc.__version__
    except ImportError:
        sys.exit(
            "ERROR: pdoc not found.\n"
            "  Install with:  uv pip install pdoc\n"
            "  Or:            pip install pdoc\n"
        )

    print(f"  pdoc {pdoc_version}")

    if args.check:
        print(f"  Package   : {PACKAGE}")
        print(f"  Templates : {TEMPLATES_DIR}")
        print(f"  Output    : {args.output_dir}")
        return

    if args.serve:
        serve(port=args.port)
        return

    print(f"\n  Building docs -> {args.output_dir}\n")
    build(args.output_dir)
    print(f"\n  Done. API ref: {args.output_dir / PACKAGE}.html")
    print(f"        Home:    {args.output_dir}/index.html")


if __name__ == "__main__":
    main()
