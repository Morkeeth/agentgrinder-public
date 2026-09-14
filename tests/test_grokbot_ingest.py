import json
from pathlib import Path

from agentgrinder.cli import main
from agentgrinder.ingest import parse_grokbot_session
from agentgrinder.mcp_server import preview_run


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "samples" / "sample_grokbot_bot_activity.jsonl"


def test_measured_grokbot_export_parses_as_labelled_bot_activity():
    run = parse_grokbot_session(str(FIXTURE))

    assert run["harness"] == "Grok Bot"
    assert run["activity_label"] == "bot activity"
    assert run["turns_typed"] == 2
    assert run["tool_calls"] == 3
    assert run["commits"] == 1
    assert run["started"] == "2026-09-14T13:00:00+00:00"

    # The measured export does not establish these facts. Unknown stays unknown.
    for field in (
        "duration_s",
        "files_touched",
        "claims",
        "claims_verified",
        "artifacts_produced",
        "artifacts_promised",
        "corrections",
        "reach",
    ):
        assert run[field] is None, f"fabricated {field}: {run[field]!r}"


def test_injected_user_turn_without_user_query_is_not_typed(tmp_path):
    rows = FIXTURE.read_text(encoding="utf-8").splitlines()
    injected = json.dumps({
        "role": "user",
        "message": {"content": [{"type": "text", "text":
            "<timestamp>Monday, Sep 14, 2026, 1:05 PM (UTC)</timestamp>\n"
            "<environment_context>injected</environment_context>"}]},
    })
    path = tmp_path / "grokbot.jsonl"
    path.write_text("\n".join([rows[0], injected, *rows[1:]]) + "\n", encoding="utf-8")

    assert parse_grokbot_session(str(path))["turns_typed"] == 2


def test_cli_loads_grokbot_fixture_and_renders_unknowns_as_dashes(tmp_path, capsys):
    card = tmp_path / "grokbot.html"
    assert main([
        "grind",
        str(FIXTURE),
        "--harness",
        "grokbot",
        "--no-open",
        "--no-series",
        "-o",
        str(card),
    ]) == 0
    output = capsys.readouterr().out
    html = card.read_text(encoding="utf-8")

    assert "Grok Bot" in output
    assert "—" in output
    assert "Grok Bot" in html
    assert "—" in html


def test_mcp_preview_uses_grokbot_adapter(monkeypatch):
    import agentgrinder.ingest as ingest

    monkeypatch.setattr(ingest, "latest_grokbot_session", lambda: str(FIXTURE))
    preview = preview_run("grokbot")
    payload = json.loads(preview.split("\n\n")[1])

    assert payload["harness"] == "Grok Bot"
    assert payload["turns_typed"] == 2
    assert payload["duration_s"] is None
    assert payload["files_touched"] is None
