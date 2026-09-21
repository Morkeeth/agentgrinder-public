"""Relationship gate for non-public runs: Public open, Link needs follow/close-friends."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ACCESS = (ROOT / "site" / "run-access.js").read_text()
INDEX = (ROOT / "site" / "index.html").read_text()
PUBLIC_RUN = (ROOT / "server" / "public-run.mjs").read_text()


def test_run_access_module_wires_into_index():
    assert "viewerMayOpenRun" in ACCESS
    assert "visibility === 'link'" in ACCESS
    assert "crew_shared" in ACCESS
    assert "grinder_is_close_friend_of" in ACCESS
    assert 'src="/run-access.js"' in INDEX
    assert "GrinderRunAccess.viewerMayOpenRun" in INDEX
    assert "authClient.auth.getSession()" in INDEX
    assert "headers.set('x-grinder-run-id',runId)" in INDEX


def test_share_page_stays_public_only_and_handoff_to_spa():
    assert "visibility:'eq.public'" in PUBLIC_RUN
    assert "visibility:'in.(public,link)'" not in PUBLIC_RUN
    assert "location.replace" in PUBLIC_RUN
    assert "/?run=" in PUBLIC_RUN


def test_viewer_may_open_run_matrix():
    script = ROOT / "tests" / "fixtures" / "run_access_probe.mjs"
    subprocess.run(["node", str(script)], cwd=ROOT, check=True)
