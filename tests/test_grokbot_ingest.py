import json
from pathlib import Path

from agentgrinder.cli import main
from agentgrinder.ingest import parse_grokbot_session
from agentgrinder.mcp_server import preview_run


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "samples" / "sample_grokbot_bot_activity.jsonl"
SAFE_REAL_SHAPE = ROOT / "samples" / "sample_grokbot_safe_real_shape.jsonl"


def test_measured_grokbot_export_parses_as_labelled_bot_activity():
    run = parse_grokbot_session(str(FIXTURE))

    assert run["harness"] == "Grok Bot"
    assert run["activity_label"] == "bot activity"
    assert run["turns_typed"] == 2
    assert run["tool_calls"] == 3
    assert run["shell_calls"] == 2
    assert run["project"] is None
    assert run["commits"] is None
    assert "ridge" not in run
    assert "ridge_wall_seconds" not in run
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


def test_cli_loads_grokbot_fixture_and_keeps_its_unknowns_unknown(tmp_path, capsys):
    """An unknown is still stated, but the card names it in words instead of drawing a dash.

    The terminal keeps the dashes: it prints the five cells as a table, where an em-dash in a
    column is legible. On the card, four dashes side by side made a real session look like a
    session in which nothing happened (verdict on the 22 Sep Cursor card), so the missing
    measurements moved into one sentence that still carries each one's name and explanation.
    """
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

    assert "selected session -> Grok Bot · Unknown project" in output
    assert f"{FIXTURE.name} · sitting 1 of 1" in output
    assert "Grok Bot" in output
    assert "—" not in output          # unknowns are left out of the summary, not dashed
    assert "bot activity" in html
    assert "Grok Bot" in html
    # The local card is the feed card: a figure the export did not measure is not drawn at all.
    card_html = html.split('<article class="card fc">')[1].split("</article>")[0]
    assert "—" not in card_html and "Unknown" not in card_html


def test_mcp_preview_uses_grokbot_adapter(monkeypatch):
    import agentgrinder.ingest as ingest

    monkeypatch.setattr(ingest, "latest_grokbot_session", lambda: str(FIXTURE))
    preview = preview_run("grokbot")
    payload = json.loads(preview.split("\n\n")[1])

    assert payload["activity_label"] == "bot activity"
    assert payload["harness"] == "Grok Bot"
    assert payload["turns_typed"] == 2
    assert payload["duration_s"] is None
    assert payload["files_touched"] is None
    assert payload["shell_calls"] == 2


def test_shell_text_and_failed_attempts_do_not_prove_commits(tmp_path):
    rows = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
    for command in ('echo "git commit did not run"', 'git commit -m failed'):
        rows[6]["message"]["content"][0]["input"]["command"] = command
        rows[7]["message"]["content"][0]["content"] = "fatal: not a git repository"
        path = tmp_path / "attempt.jsonl"
        path.write_text("\n".join(map(json.dumps, rows)))
        assert parse_grokbot_session(str(path))["commits"] is None


def test_discovery_skips_non_object_records(tmp_path, monkeypatch):
    import agentgrinder.ingest as ingest
    path = tmp_path / "grokbot.jsonl"
    path.write_text('null\n[]\n"text"\n42\n{bad json\n' + FIXTURE.read_text())
    monkeypatch.setattr(ingest, "GROKBOT_GLOB", str(tmp_path / "*.jsonl"))
    assert ingest.latest_grokbot_session() == str(path)
    assert parse_grokbot_session(str(path))["turns_typed"] == 2


def test_public_export_keeps_bot_label_and_drops_private_prompt():
    from agentgrinder.push import export_run
    run = parse_grokbot_session(str(FIXTURE))
    run["private_title_prompt"] = "PRIVATE PROMPT SENTINEL"
    payload = export_run(run)
    assert payload["activity_label"] == "bot activity"
    assert "PRIVATE PROMPT SENTINEL" not in json.dumps(payload)
    assert "private_title_prompt" not in payload


def test_safe_real_shape_fixture_preserves_structure_without_exporting_labels_or_paths():
    from agentgrinder.push import export_run

    rows = [
        json.loads(line)
        for line in SAFE_REAL_SHAPE.read_text(encoding="utf-8").splitlines()
    ]
    assert len(rows) == 29
    assert {row["role"] for row in rows} == {"user", "assistant", "tool"}

    fixture_text = SAFE_REAL_SHAPE.read_text(encoding="utf-8")
    assert "[SAFE EXPORT]" in fixture_text
    assert "/SAFE_EXPORT/project" in fixture_text
    assert "/workspace/" not in fixture_text
    assert "/home/" not in fixture_text

    run = parse_grokbot_session(str(SAFE_REAL_SHAPE))
    assert run["activity_label"] == "bot activity"
    assert run["turns_typed"] == 7
    assert run["tool_calls"] == 7
    assert run["shell_calls"] == 4
    assert run["commits"] is None
    assert run["files_touched"] is None

    exported = json.dumps(export_run(run))
    assert "SAFE EXPORT" not in exported
    assert "/SAFE_EXPORT/project" not in exported
    assert "private_title_prompt" not in exported


def test_structured_grokbot_workdir_can_prove_project_without_exporting_path(tmp_path):
    from agentgrinder.push import export_run
    import subprocess

    repo = tmp_path / "honest-project"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    rows = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
    for row in rows:
        row["agentgrinder_sample"] = False
        message = row.get("message") or {}
        for block in message.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                inputs = block.get("input") or {}
                if block.get("name") == "Shell":
                    inputs["working_directory"] = str(repo)
    run = parse_grokbot_session("fixture.jsonl", records=rows)
    payload = export_run(run)
    assert run["project"] == "honest-project"
    assert payload["project"] == "honest-project"
    assert str(tmp_path) not in json.dumps(payload)
