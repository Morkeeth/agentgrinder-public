"""Footer, favicon, titles, About and 404 on every page (fresh-eyes review, 25 Sep 2026)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
READING = ["privacy.html", "terms.html", "methodology.html", "about.html", "404.html"]


def test_every_page_has_the_icon_and_the_footer():
    for name in READING + ["index.html"]:
        html = (SITE / name).read_text()
        assert '<link rel="icon" href="/favicon.svg" type="image/svg+xml">' in html, name
        foot = html[html.index('<footer class="site-foot">'):]
        for href in ('/about', '/privacy', '/terms', 'github.com/Morkeeth/agentgrinder-public/issues', '/privacy#deletion'):
            assert f'href="{href}' in foot or f'href="https://{href}' in foot, (name, href)
    assert (SITE / "favicon.svg").read_text().startswith("<svg")


def test_deletion_has_an_anchor_and_terms_link_clean_urls():
    assert '<h2 id="deletion">Delete your data</h2>' in (SITE / "privacy.html").read_text()
    terms = (SITE / "terms.html").read_text()
    assert "/privacy.html" not in terms and "←" not in terms


def test_each_spa_page_sets_its_own_title():
    html = (SITE / "index.html").read_text()
    assert "document.title=pageTitle(new URLSearchParams(location.search))" in html
    for label in ("'Marathon and boards'", "'Add a run'", "'Find people'", "'Account settings'"):
        assert label in html


def test_the_404_page_is_branded_and_not_indexed():
    page = (SITE / "404.html").read_text()
    assert '<meta name="robots" content="noindex">' in page and 'href="/"' in page
