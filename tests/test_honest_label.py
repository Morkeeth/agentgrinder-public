"""Achieved is printed only when the run recorded an outcome (25 Sep 2026: REAL for shitty runs)."""
from pathlib import Path

INDEX = (Path(__file__).resolve().parents[1] / "site/index.html").read_text()


def test_achieved_is_conditional():
    assert '<div class="run-story-label achieved">Achieved</div>' not in INDEX.replace("return done?'<div class=\"run-story-label achieved\">Achieved</div>':'';", "")
    assert "${achievedLabel(r)}" in INDEX
    label = INDEX[INDEX.index("function achievedLabel(r)") : INDEX.index("function runCard(")]
    assert "(r.commits>0)||shipped>0||receipts>0||!!(r.output_url&&safeOutputUrl(r.output_url))" in label
