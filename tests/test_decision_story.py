"""The signed-out decision page is derived from one supplied Code Route."""
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "api" / "decision.js").read_text()
VERCEL = (ROOT / "vercel.json").read_text()


def test_decision_story_render_and_continuation_contract():
    subprocess.run(
        ["node", str(ROOT / "tests" / "fixtures" / "decision_story_probe.mjs")],
        cwd=ROOT,
        check=True,
    )


def test_decision_url_reads_only_the_public_run():
    assert "readPublic(id)" in API
    assert "neutralDecisionHtml(id)" in API
    assert '"/d/:id"' in VERCEL
    assert '"/api/decision?id=:id"' in VERCEL
