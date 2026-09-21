"""Tool-call counts agree across /r/, SPA strip, Explore, share, and slice labels."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "fixtures" / "counts_truth_probe.mjs"
INDEX = (ROOT / "site" / "index.html").read_text()
SOCIAL = (ROOT / "site" / "social.js").read_text()
CONTRACT = (ROOT / "site" / "run-contract.js").read_text()


def test_cross_surface_counts_agree_and_slice_is_labelled():
    out = subprocess.check_output(["node", str(PROBE)], text=True, cwd=ROOT)
    assert '"ok":true' in out.replace(" ", "")


def test_stranger_social_sign_in_copy_is_wired():
    assert "reason==='social'" in INDEX or 'reason==="social"' in INDEX
    assert "cheer this run or follow the builder" in INDEX
    assert "Runs stay private until you choose Public" in INDEX
    assert 'showSignIn({reason:\'social\'})' in INDEX or 'showSignIn({ reason: "social" })' in SOCIAL
    assert "toolCallCount" in CONTRACT
    assert "in this slice" in CONTRACT
