"""Regression coverage for issue #44: the docs-site landing page
(docs/site-pages/index.html) previously drifted out of sync with the
real plugin roster whenever a new genre or drummer plugin shipped
(Electronic genre, Peart/Rich/Copeland drummers all landed without a
corresponding site update). These tests cross-check the page's roster
claims against the actual registered plugins, not hardcoded numbers, so
future roster growth fails loudly here instead of silently stale.
"""

import re
from pathlib import Path

import pytest

from midi_drums.api.python_api import DrumGeneratorAPI

SITE_INDEX = (
    Path(__file__).resolve().parents[3] / "docs" / "site-pages" / "index.html"
)

# The landing page's "legendary styles" grid shows individual drummer
# personalities, each with their own card/bio. Composite plugins (e.g.
# composite_doom_blues, which layers Roeder/Porcaro/Chambers) aren't
# individual personalities and intentionally have no card of their own -
# see CHANGELOG.md's "10 individual drummer plugins ... plus a composite
# plugin" phrasing.
COMPOSITE_DRUMMERS = {"composite_doom_blues"}


@pytest.fixture(scope="module")
def api():
    return DrumGeneratorAPI()


@pytest.fixture(scope="module")
def individual_drummers(api):
    return [d for d in api.list_drummers() if d not in COMPOSITE_DRUMMERS]


@pytest.fixture(scope="module")
def index_html():
    return SITE_INDEX.read_text(encoding="utf-8")


@pytest.mark.unit
class TestLandingPageRosterSync:
    def test_genre_style_count_heading_matches_registered_plugins(
        self, api, index_html
    ):
        genres = api.list_genres()
        total_styles = sum(len(api.list_styles(genre)) for genre in genres)

        heading = re.search(
            r'<h2 class="section-title">(\d+) styles across (\d+) genres</h2>',
            index_html,
        )
        assert heading, "genres section heading not found in index.html"
        assert int(heading.group(1)) == total_styles
        assert int(heading.group(2)) == len(genres)

    def test_drummer_count_heading_matches_individual_drummer_plugins(
        self, individual_drummers, index_html
    ):
        heading = re.search(
            r'<h2 class="section-title">(\d+) legendary styles</h2>',
            index_html,
        )
        assert heading, "drummers section heading not found in index.html"
        assert int(heading.group(1)) == len(individual_drummers)

    def test_every_genre_has_a_genre_block(self, api, index_html):
        for genre in api.list_genres():
            assert (
                f"genre-block gb-{genre}" in index_html
            ), f"no .gb-{genre} block for genre '{genre}'"

    def test_every_individual_drummer_has_a_drummer_card(
        self, individual_drummers, index_html
    ):
        for drummer in individual_drummers:
            assert (
                f"--drummer {drummer}" in index_html
            ), f"no drummer card for '{drummer}'"
