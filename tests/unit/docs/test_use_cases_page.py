"""Regression coverage for issue #44 AC Group 2: the docs site had no
end-to-end Use Cases page, and the existing pages didn't cross-link to
it. These tests pin both halves down so a future site edit can't drop
the page or the nav wiring silently.
"""

from pathlib import Path

import pytest

SITE_PAGES = Path(__file__).resolve().parents[3] / "docs" / "site-pages"
README = Path(__file__).resolve().parents[3] / "README.md"

EXISTING_PAGES = [
    "index.html",
    "quickstart.html",
    "recipes.html",
    "reaper.html",
]


@pytest.mark.unit
class TestUseCasesPage:
    def test_use_cases_page_exists(self):
        assert (SITE_PAGES / "use-cases.html").is_file()

    def test_use_cases_page_has_shared_nav_and_footer(self):
        html = (SITE_PAGES / "use-cases.html").read_text(encoding="utf-8")
        assert 'href="index.html"' in html
        assert 'href="quickstart.html"' in html
        assert 'href="recipes.html"' in html
        assert 'href="reaper.html"' in html
        assert "<footer>" in html

    @pytest.mark.parametrize("page", EXISTING_PAGES)
    def test_existing_page_links_to_use_cases(self, page):
        html = (SITE_PAGES / page).read_text(encoding="utf-8")
        assert 'href="use-cases.html"' in html

    def test_readme_docs_table_has_use_cases_row(self):
        readme = README.read_text(encoding="utf-8")
        assert "use-cases.html" in readme
