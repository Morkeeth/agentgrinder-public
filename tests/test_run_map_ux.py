"""Run map is interactive; missing metrics stay off the card."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (ROOT / "site" / "run-contract.js").read_text()
INDEX = (ROOT / "site" / "index.html").read_text()
SHARING = (ROOT / "site" / "sharing.js").read_text()


def test_share_labels_turn_order():
    assert "ridgeBasisLabel" in SHARING
    assert "turn order" in SHARING


def test_run_map_is_interactive():
    assert "mountRunMaps" in CONTRACT
    assert "run-map-hit" in CONTRACT
    assert "run-map-scrub" in CONTRACT
    assert "run-map-readout" in CONTRACT
    assert "data-run-map" in CONTRACT


def test_no_fake_ranked_metrics_or_unknown_disclaimers():
    card = INDEX[INDEX.index("function runCard(") : INDEX.index("function wireKudos(")]
    assert "run-rank" not in card
    assert "ranked.push" not in card
    assert "Unknown stays Unknown" not in INDEX
    assert "Unknown measurements stay unknown" not in INDEX
    assert "Unknown stays unknown" not in INDEX
    assert "No score is invented" not in INDEX
    assert "Coming soon. Short notes on what to try next after a run." in INDEX
    assert "filter(Boolean)" in card or ".filter(Boolean)" in card


def test_sign_in_with_github_invokes_github():
    assert "function signInWithGitHub" in INDEX
    assert "auth.signIn('github'" in INDEX
    assert "signInWithGitHub" in INDEX
