"""Regression coverage for issue #44 AC Group 3: recipes.html covered
Death Metal, Modern Jazz, and Progressive Rock end-to-end but had no
Funk or Electronic recipe despite both being fully supported genres.
"""

import re
from pathlib import Path

import pytest

from midi_drums.api.python_api import DrumGeneratorAPI

RECIPES_HTML = (
    Path(__file__).resolve().parents[3] / "docs" / "site-pages" / "recipes.html"
)


@pytest.fixture(scope="module")
def api():
    return DrumGeneratorAPI()


@pytest.fixture(scope="module")
def html():
    return RECIPES_HTML.read_text(encoding="utf-8")


@pytest.mark.unit
class TestFunkElectronicRecipes:
    def test_funk_recipe_card_present(self, html):
        assert "recipe-card rc-funk" in html
        assert "tag-funk" in html

    def test_funk_recipe_uses_a_real_funk_style(self, api, html):
        card = re.search(
            r'<div class="recipe-card rc-funk"[\s\S]*?(?=<div class="recipe-card|'
            r'<h2 id="batch")',
            html,
        )
        assert card, "funk recipe card not found"
        funk_styles = api.list_styles("funk")
        assert any(style in card.group(0) for style in funk_styles)

    def test_electronic_recipe_card_present(self, html):
        assert "recipe-card rc-electronic" in html
        assert "tag-electronic" in html

    def test_electronic_recipe_uses_a_real_electronic_style(self, api, html):
        card = re.search(
            r'<div class="recipe-card rc-electronic"[\s\S]*?(?=<div class="recipe-card|'
            r'<h2 id="batch")',
            html,
        )
        assert card, "electronic recipe card not found"
        electronic_styles = api.list_styles("electronic")
        assert any(style in card.group(0) for style in electronic_styles)

    def test_toc_links_to_both_new_recipes(self, html):
        assert 'href="#funk-groove"' in html
        assert 'href="#electronic-track"' in html
