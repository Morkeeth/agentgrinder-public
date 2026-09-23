"""THE HOME PAGE, AS A POST SEES IT.

Launch audit of production 7858535: the address people actually post — the root — carried zero
`og:` and zero `twitter:` tags. A run page has had them since it shipped, so a link to one run
unfurled with a title, a description and a 1200x630 image, while a link to the product itself
showed as a bare URL. If a post sends a thousand people, that bare link is the first thing all
thousand see.

Every test here fails on the old head: it had none of these tags.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()
BUILD = (ROOT / "scripts" / "build-site.mjs").read_text()
PUBLIC_RUN = (ROOT / "server" / "public-run.mjs").read_text()
# Read lazily: on a tree that has no share-image endpoint at all, this file's assertions are the
# report, not a collection error.
OG_ENDPOINT = (ROOT / "api" / "og.js").read_text() if (ROOT / "api" / "og.js").is_file() else ""


def _built() -> str:
    subprocess.run(["node", str(ROOT / "scripts" / "build-site.mjs")], cwd=ROOT, check=True)
    return (ROOT / "dist" / "index.html").read_text()


def test_the_home_page_source_carries_the_share_tags():
    for tag in ('property="og:type"', 'property="og:title"', 'property="og:description"',
                'property="og:image"', 'property="og:url"', 'name="twitter:card"',
                'name="twitter:image"'):
        assert tag in INDEX, tag
    assert 'name="twitter:card" content="summary_large_image"' in INDEX
    assert 'property="og:image:width" content="1200"' in INDEX
    assert 'property="og:image:height" content="630"' in INDEX
    # The name and address stay tokens, so renaming or moving the site is still one edit.
    assert '<meta property="og:title" content="__BRAND__ · __TAGLINE__">' in INDEX
    assert '<meta property="og:image" content="__ORIGIN__/api/og">' in INDEX


def test_the_built_page_points_a_crawler_at_an_absolute_image():
    built = _built()
    assert "__ORIGIN__" not in built and "__BRAND__" not in built
    image = re.search(r'<meta property="og:image" content="([^"]+)">', built).group(1)
    assert image.startswith(("https://", "http://localhost")), image
    assert image.endswith("/api/og")
    assert re.search(r'<meta property="og:title" content="STRIVE · Post your strides">', built)
    assert '<meta name="twitter:card" content="summary_large_image">' in built
    for tag in ("og:image", "twitter:card"):
        assert built.count(tag) >= 1
    # A relative image is the failure mode this replaced: crawlers do not resolve one.
    assert 'content="/api/og"' not in built


def test_the_build_refuses_to_ship_a_page_that_lost_its_share_tags():
    assert "The home page lost its share tag" in BUILD
    assert "The share image must be an absolute URL" in BUILD
    assert "__ORIGIN__" in BUILD


def test_the_share_image_is_the_run_image_pipeline_not_a_committed_png():
    assert "homeCard" in OG_ENDPOINT and "@vercel/og" in OG_ENDPOINT
    assert "width:1200,height:630" in OG_ENDPOINT
    assert "export function homeCard()" in PUBLIC_RUN
    assert "readPublic" not in OG_ENDPOINT      # the home image reads no database and no run
    subprocess.run(["node", str(ROOT / "scripts" / "check-home-unfurl.mjs")], cwd=ROOT, check=True)


def test_the_unfurl_describes_the_product_and_names_the_tools_it_reads():
    description = re.search(r'<meta property="og:description" content="([^"]+)">', INDEX).group(1)
    for tool in ("Cursor", "Claude Code", "Codex", "Grok Bot"):
        assert tool in description, tool
    assert "private until you choose to share" in description.lower()
