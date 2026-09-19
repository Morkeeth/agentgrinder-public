"""Grok Bot export draws a turn-order ridge, not a flat call-index comb.

Measured on 16 Sep 2026. Call-index with fewer than 50 calls spreads evenly and
draws a 1 and 0 comb. That comb is not a shape. Tool counts per typed turn on
brief-v2-export-a.jsonl were 1, 2, 5, 13, 0, 7. The card must show that burst.
"""
import base64
import json
import urllib.parse
from pathlib import Path

from agentgrinder.cursor_tree import ridge_from_turn_order
from agentgrinder.ingest import parse_grokbot_session
from agentgrinder.push import export_run, import_url


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "samples" / "sample_grokbot_bot_activity.jsonl"
SAFE_REAL_SHAPE = ROOT / "samples" / "sample_grokbot_safe_real_shape.jsonl"
BURST_EXPORT = ROOT / "samples" / "sample_grokbot_turn_order_burst.jsonl"
BURST_COUNTS = [1, 2, 5, 13, 0, 7]


def test_ridge_from_turn_order_keeps_the_burst_shape():
    result = ridge_from_turn_order(BURST_COUNTS)
    assert result["ridge_basis"] == "turn-order"
    assert len(result["ridge"]) == 50
    assert sum(result["ridge"]) == sum(BURST_COUNTS)
    assert result["ridge_wall_seconds"] is None
    # Sparse peaks at turn positions, not a flat comb of ones.
    nonzero = [value for value in result["ridge"] if value]
    assert nonzero == [1, 2, 5, 13, 7]
    assert result["ridge"].count(1) == 1
    assert max(result["ridge"]) == 13


def test_call_index_on_the_same_total_is_a_flat_comb():
    from agentgrinder.cursor_tree import ridge_from_calls
    flat = ridge_from_calls([None] * sum(BURST_COUNTS))
    assert flat["ridge_basis"] == "call-index"
    assert set(flat["ridge"]) <= {0, 1}
    assert max(flat["ridge"]) == 1


def test_grokbot_fixture_uses_turn_order():
    run = parse_grokbot_session(str(FIXTURE))
    assert run["ridge_basis"] == "turn-order"
    assert len(run["ridge"]) == 50
    assert sum(run["ridge"]) == run["tool_calls"] == 3
    assert run["ridge_wall_seconds"] is None
    assert run["duration_s"] is None
    assert run["capabilities"]["timed_ridge"] is False
    assert run["ridge_source"] == "turn-order"
    # Two typed turns with counts 2 then 1.
    assert [value for value in run["ridge"] if value] == [2, 1]


def test_grokbot_safe_real_shape_stays_turn_order_not_wall_time():
    run = parse_grokbot_session(str(SAFE_REAL_SHAPE))
    assert run["turns_typed"] >= 2
    assert run["ridge_basis"] == "turn-order"
    assert sum(run["ridge"]) == run["tool_calls"]
    assert run["ridge_wall_seconds"] is None


def test_grokbot_export_with_no_tool_calls_has_an_empty_turn_order_ridge(tmp_path):
    rows = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
    only_typed = [row for row in rows if row.get("role") == "user"]
    path = tmp_path / "typed-only.jsonl"
    path.write_text("\n".join(map(json.dumps, only_typed)) + "\n")
    run = parse_grokbot_session(str(path))
    assert run["tool_calls"] == 0
    assert run["ridge_basis"] == "turn-order"
    assert sum(run["ridge"]) == 0


def test_burst_fixture_matches_measured_turn_counts():
    run = parse_grokbot_session(str(BURST_EXPORT))
    assert run["ridge_basis"] == "turn-order"
    assert sum(run["ridge"]) == run["tool_calls"] == 28
    assert [value for value in run["ridge"] if value] == [1, 2, 5, 13, 7]


def test_turn_order_ridge_travels_in_the_export_payload_and_the_preview():
    run = parse_grokbot_session(str(FIXTURE))
    payload = export_run(run)
    assert payload["ridge"] == run["ridge"]
    assert payload["ridge_basis"] == "turn-order"
    assert payload.get("ridge_wall_seconds") is None
    assert "ridge_source" not in payload

    token = import_url(run, "http://localhost:8000").split("#import=", 1)[1]
    decoded = json.loads(base64.b64decode(urllib.parse.unquote(token)))
    assert sum(decoded["ridge"]) == 3
    assert decoded["ridge_basis"] == "turn-order"
    assert decoded["worker_bins"] == [0] * 50
    assert "ridge_source" not in decoded


def test_migration_004_extends_basis_without_leaving_it_open():
    sql = (ROOT / "supabase" / "strava" / "004_ridge_turn_order.sql").read_text()
    statements = "\n".join(
        line for line in sql.splitlines() if not line.lstrip().startswith("--")
    )
    assert "turn-order" in statements
    assert "wall-time" in statements and "call-index" in statements
    assert "add constraint runs_ridge_basis_check" in statements
    # The drop exists only to replace the check inside one transaction.
    assert "drop constraint if exists runs_ridge_basis_check" in statements
    assert "drop column" not in statements.lower()


def test_standalone_grok_kit_preserves_burst_in_hosted_import(tmp_path):
    """Exercise the actual distributable script outside the source checkout."""
    import shutil
    import subprocess
    import sys

    script = tmp_path / "preview.py"
    shutil.copyfile(ROOT / "templates/grokbot/post-agent-run/scripts/preview.py", script)
    result = subprocess.run(
        [sys.executable, "-I", str(script), str(BURST_EXPORT)],
        cwd=tmp_path, check=True, capture_output=True, text=True,
    )
    receipt = json.loads(result.stdout)
    payload = json.loads(base64.b64decode(urllib.parse.unquote(
        receipt["preview_url"].split("#import=", 1)[1])))
    assert payload["ridge_basis"] == "turn-order"
    assert [value for value in payload["ridge"] if value] == [1, 2, 5, 13, 7]
    assert sum(payload["ridge"]) == payload["tool_calls"] == 28
    assert payload["ridge"] == parse_grokbot_session(str(BURST_EXPORT))["ridge"]
    assert "duration_s" not in payload
    assert "ridge_wall_seconds" not in payload
    assert "private_title_prompt" not in payload
