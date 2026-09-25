"""Free Lunch confirm (server/fair-confirm.mjs, site/fair.js): off without a secret, signs only a real action."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_confirm_module_with_a_fake_network():
    out = subprocess.run(["node", "scripts/test-fair-confirm.mjs"], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr[-2000:]


def test_the_page_strips_the_challenge_and_holds_no_secret():
    fair = (ROOT / "site/fair.js").read_text()
    assert "/^fair_challenge(=|$)/" in fair and "replaceState" in fair
    assert "SECRET" not in fair.upper().replace("NEVER HOLDS A SECRET", "")
    index = (ROOT / "site/index.html").read_text()
    assert '<script src="/fair.js"></script>' in index
    assert index.count("fairConfirmRun(") == 3  # the helper and the two new-save paths
    assert 'root.StriveFair.confirm("link", body.id)' in (ROOT / "site/dropin.js").read_text()
