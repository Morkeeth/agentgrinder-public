"""A Grok Bot export carries a ridge on call order, never on wall time.

Measured on three real exports on 16 Sep 2026: the only clock in a Grok Bot export is the
<timestamp> tag on typed user turns, at minute resolution. No tool_use block carries a time.
So a wall-time ridge cannot be drawn, and a call-index ridge can. The card labels that basis
"Tool calls over call order", the same label the Cursor fallback uses.
"""
import base64
import json
import urllib.parse
from pathlib import Path

from agentgrinder.ingest import parse_grokbot_session
from agentgrinder.push import export_run, import_url


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "samples" / "sample_grokbot_bot_activity.jsonl"
SAFE_REAL_SHAPE = ROOT / "samples" / "sample_grokbot_safe_real_shape.jsonl"


def test_grokbot_run_carries_a_call_index_ridge():
    run = parse_grokbot_session(str(FIXTURE))
    assert run["ridge_basis"] == "call-index"
    assert len(run["ridge"]) == 50
    assert sum(run["ridge"]) == run["tool_calls"] == 3
    assert run["worker_bins"] == [0] * 50
    assert run["commit_bins"] == []
    # No clock was read, so nothing timed may appear.
    assert run["ridge_wall_seconds"] is None
    assert run["ridge_tool_calls"] is None
    assert run["duration_s"] is None
    assert run["capabilities"]["timed_ridge"] is False
    assert run["ridge_source"] == "call-index"


def test_grokbot_ridge_never_claims_wall_time_even_with_typed_stamps():
    # The safe real shape has several typed turns with <timestamp> tags. Those stamp the
    # human, not the tool calls, so the basis must stay call-index.
    run = parse_grokbot_session(str(SAFE_REAL_SHAPE))
    assert run["turns_typed"] >= 2
    assert run["ridge_basis"] == "call-index"
    assert sum(run["ridge"]) == run["tool_calls"]
    assert run["ridge_wall_seconds"] is None


def test_grokbot_export_with_no_tool_calls_has_an_empty_ridge(tmp_path):
    rows = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
    only_typed = [row for row in rows if row.get("role") == "user"]
    path = tmp_path / "typed-only.jsonl"
    path.write_text("\n".join(map(json.dumps, only_typed)) + "\n")
    run = parse_grokbot_session(str(path))
    assert run["tool_calls"] == 0
    assert run["ridge_basis"] == "call-index"
    assert sum(run["ridge"]) == 0


def test_grokbot_ridge_travels_in_the_export_payload_and_the_preview():
    run = parse_grokbot_session(str(FIXTURE))
    payload = export_run(run)
    assert payload["ridge"] == run["ridge"]
    assert payload["ridge_basis"] == "call-index"
    assert payload.get("ridge_wall_seconds") is None
    assert "ridge_source" not in payload

    # The Grok Bot helper (templates/grokbot/post-agent-run/scripts/preview.py) opens the site
    # through import_url, so this is the exact payload the browser Save path receives.
    token = import_url(run, "http://localhost:8000").split("#import=", 1)[1]
    decoded = json.loads(base64.b64decode(urllib.parse.unquote(token)))
    assert sum(decoded["ridge"]) == 3
    assert decoded["ridge_basis"] == "call-index"
    assert decoded["worker_bins"] == [0] * 50
    assert "ridge_source" not in decoded
