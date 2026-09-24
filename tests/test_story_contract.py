"""The saved story fields are nullable counts with no raw capture data."""
from pathlib import Path

import pytest

from agentgrinder.contract import validate_run
from agentgrinder.push import export_run


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "strava" / "005_shell_calls.sql").read_text()
PUBLIC_RUN = (ROOT / "server" / "public-run.mjs").read_text()


def test_shell_calls_accepts_zero_and_unknown():
    assert validate_run({"shell_calls": 0})["shell_calls"] == 0
    assert validate_run({"shell_calls": None})["shell_calls"] is None
    with pytest.raises(ValueError):
        validate_run({"shell_calls": -1})


def test_shell_calls_migration_is_nullable_and_schema_qualified():
    assert "alter table strava.runs" in MIGRATION
    assert "shell_calls is null or shell_calls >= 0" in MIGRATION
    assert "public.runs" not in MIGRATION
    assert "Command text, results, paths, and exit output are not stored." in MIGRATION


def test_public_export_keeps_counts_and_drops_raw_capture_data():
    run = {
        "schema_version": 1,
        "project": "agentgrinder-public",
        "shell_calls": 0,
        "private_title_prompt": "PRIVATE PROMPT",
        "command": "PRIVATE COMMAND",
        "path": "/private/repo/secret.py",
        "tool_output": "PRIVATE OUTPUT",
    }
    exported = export_run(run)
    assert exported["project"] == "agentgrinder-public"
    assert exported["shell_calls"] == 0
    for key in ("private_title_prompt", "command", "path", "tool_output"):
        assert key not in exported


def test_public_reader_selects_counts_but_not_raw_capture_fields():
    select = PUBLIC_RUN.split("select:'", 1)[1].split("'", 1)[0]
    for field in ("output_url", "project", "shell_calls", "files_touched", "commits", "tool_calls"):
        assert field in select
    for private in ("private_title_prompt", "command", "path", "tool_output"):
        assert private not in select
