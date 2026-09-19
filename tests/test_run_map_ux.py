"""Run map and ranked measures stay honest about basis and scores."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (ROOT / "site" / "run-contract.js").read_text()
INDEX = (ROOT / "site" / "index.html").read_text()
SHARING = (ROOT / "site" / "sharing.js").read_text()


def test_share_and_contract_agree_on_turn_order_words():
    assert "turn-order" in CONTRACT
    assert "turn order" in CONTRACT
    assert "ridgeBasisLabel" in SHARING
    assert "turn order" in SHARING and "ridgeBasisLabel" in SHARING


def test_run_map_never_claims_ordinal_chart_is_elapsed_time():
    assert "Not wall-clock elapsed time." in CONTRACT
    assert 'data-ridge-basis="' in CONTRACT
    assert "Run map" in CONTRACT
    assert "peak ${peak}" in CONTRACT or "peak " in CONTRACT


def test_ranked_measures_name_criteria_not_quality():
    assert "Peak tools in one bin" in INDEX
    assert "not a quality score" in INDEX or "not a quality score" in INDEX.lower()
    assert "Coming soon. No score is invented here." in INDEX
    assert "r.prompts??r.turns_typed" in INDEX.replace(" ", "")


def test_css_keeps_white_blue_tokens():
    css = (ROOT / "site" / "design.css").read_text()
    assert "--blue:#0047ff" in css or "--blue: #0047ff" in css.replace(" ", "")
    assert ".run-rank" in css
    assert ".coach-soon" in css
