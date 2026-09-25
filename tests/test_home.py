"""The signed-out home (site/home.js) and migration 014 (clubs, events), checked without a network."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _node(script):
    out = subprocess.run(["node", script], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, (out.stdout + out.stderr)[-2000:]


def test_home_rows_from_real_shaped_data():
    _node("scripts/test-home.mjs")


def test_migration_014_clubs_and_events_in_pglite():
    _node("scripts/test-social-migration.mjs")


def test_home_invents_nothing():
    index = (ROOT / "site/index.html").read_text()
    landing = index[index.index("function landingHTML(){"):index.index("// THE DROP ZONE. One markup")]
    for word in ("sample", "Sample", "example club", "demo"):
        assert word not in landing
    home = (ROOT / "site/home.js").read_text()
    assert "No events planned yet." in index and "No clubs yet." in index
    assert "Math.random" not in home
