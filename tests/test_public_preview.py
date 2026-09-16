"""Public and private STRIVE OG image contracts."""
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_RUN = (ROOT / "server" / "public-run.mjs").read_text()
API_RUN = (ROOT / "api" / "run.js").read_text()


def test_sample_and_private_og_images_render_to_png():
    subprocess.run(
        ["node", str(ROOT / "scripts" / "check-public-preview.mjs")],
        cwd=ROOT,
        check=True,
    )


def test_private_and_missing_image_requests_share_the_neutral_response():
    assert "run?card(run):privateCard()" in API_RUN
    assert "res.statusCode=200" in API_RUN
    assert "This run is private on ${BRAND}" in PUBLIC_RUN
    assert "run.visibility==='public'" in PUBLIC_RUN
    for tag in ("og:image", "og:title", "og:description", "twitter:card"):
        assert tag in PUBLIC_RUN
