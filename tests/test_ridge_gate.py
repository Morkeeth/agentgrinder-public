"""The store ridge is accepted on structure and window, never on a tool-count comparison.

Every row here is invented. No real store, no real transcript, no network.

The defect this file exists for: parse_cursor_session used to require
sum(store ridge) == transcript tool_calls. The two sides count tool requests in different
vocabularies, so the equality can only hold by coincidence. It held on every fixture because
the fixtures generated both sides from one list. On the author's real store, 16 Sep 2026, it
held for 17 of the 46 sessions the store could serve, and a real 33 hour session printed
Wall time Unknown.
"""
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agentgrinder import cursor_tree
from agentgrinder.ingest import parse_cursor_session

PARENT = "aaaaaaaa-0000-0000-0000-0000000000a1"
START = datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc)


def _bubble(created, tool=None):
    row = {"createdAt": created, "type": 2, "text": "PRIVATE TEXT MUST NOT LEAK",
           "tokenCount": {"inputTokens": 0, "outputTokens": 0}}
    if tool:
        row["toolFormerData"] = {"name": tool, "status": "completed", "rawArgs": "/secret/path"}
    return row


def store_with(folder: Path, tool_bubbles: int, span_seconds: int) -> Path:
    """A store whose tool requests are counted in the store's own vocabulary."""
    db = folder / "state.vscdb"
    conn = sqlite3.connect(db)
    conn.execute("create table cursorDiskKV (key text primary key, value blob)")
    conn.execute("create table composerHeaders (composerId text primary key, workspaceId text,"
                 " isSubagent integer, subagentTypeName text)")
    rows = {"composerData:" + PARENT: {
        "composerId": PARENT, "createdAt": 1700000000000, "lastUpdatedAt": 1700009000000,
        "status": "completed", "name": "secret session title", "subagentComposerIds": [],
        "modelConfig": {"modelName": "default", "selectedModels": [{"modelId": "default"}]},
        "usageData": {}}}
    step = span_seconds / max(1, tool_bubbles - 1)
    for index in range(tool_bubbles):
        stamp = (START + timedelta(seconds=step * index)).isoformat().replace("+00:00", "Z")
        rows["bubbleId:%s:%d" % (PARENT, index)] = _bubble(stamp, tool="edit_file_v2")
    conn.executemany("insert into cursorDiskKV values (?,?)",
                     [(key, json.dumps(value)) for key, value in rows.items()])
    conn.commit()
    conn.close()
    return db


def transcript_with(folder: Path, tool_calls: int, typed_turns=(0,)) -> Path:
    """A transcript that counts the same work in the harness vocabulary."""
    folder = folder / "project" / "agent-transcripts" / PARENT
    folder.mkdir(parents=True)
    path = folder / "session.jsonl"
    lines = []
    for offset in typed_turns:
        when = START + timedelta(seconds=offset)
        lines.append(json.dumps({"role": "user", "message": {"content":
            "<timestamp>%s</timestamp><user_query>PRIVATE MESSAGE</user_query>"
            % when.isoformat().replace("+00:00", "Z")}}))
    lines.append(json.dumps({"role": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Write", "input": {"path": "/private/%d" % index}}
        for index in range(tool_calls)]}}))
    path.write_text("\n".join(lines))
    return path


@pytest.fixture
def parsed(tmp_path, monkeypatch):
    def run(store_calls, transcript_calls, span_seconds=1800, typed_turns=(0,)):
        store = store_with(tmp_path / "store", store_calls, span_seconds)
        transcript = transcript_with(tmp_path / "t", transcript_calls, typed_turns)
        monkeypatch.setenv(cursor_tree.ENV_DB, str(store))
        return parse_cursor_session(str(transcript))
    (tmp_path / "store").mkdir()
    return run


def test_the_two_tool_counts_may_differ_and_the_ridge_survives(parsed):
    """THE TEST THAT WOULD HAVE CAUGHT IT. The store saw 5 requests, the transcript 3."""
    run = parsed(store_calls=5, transcript_calls=3)
    # The symptom first: the old gate threw the timed ridge away and the card said Unknown.
    assert run["ridge_basis"] == "wall-time"
    assert run["ridge_wall_seconds"] == 1800.0
    assert run["duration_s"] == 1800.0
    assert sum(run["ridge"]) == 5
    assert run["tool_calls"] == 3
    assert run["ridge_tool_calls"] == 5
    assert run["ridge_tool_calls"] != run["tool_calls"], "the fixture must disagree, or it proves nothing"
    assert len(run["ridge"]) == len(run["worker_bins"]) == 50
    assert run["capabilities"]["timed_ridge"] is True


def test_an_equal_count_still_works(parsed):
    run = parsed(store_calls=3, transcript_calls=3)
    assert run["ridge_basis"] == "wall-time"
    assert run["ridge_tool_calls"] == 3


def test_a_store_window_far_from_the_typed_turn_window_is_a_different_session(parsed):
    """The real veto. A composer resumed weeks later must not lend its window to this run.
    Measured on 26 real sessions with both windows: median ratio 1.02, one outlier at 620."""
    run = parsed(store_calls=5, transcript_calls=3, span_seconds=1800, typed_turns=(0, 60))
    assert run["ridge_basis"] == "call-index"
    assert run["ridge_wall_seconds"] is None
    assert run["ridge_tool_calls"] is None
    assert run["capabilities"]["timed_ridge"] is False


def test_a_store_window_near_the_typed_turn_window_is_accepted(parsed):
    run = parsed(store_calls=9, transcript_calls=3, span_seconds=1800, typed_turns=(0, 1500))
    assert run["ridge_basis"] == "wall-time"
    assert run["ridge_tool_calls"] == 9


def test_an_empty_store_composer_falls_back(parsed):
    run = parsed(store_calls=0, transcript_calls=3)
    assert run["ridge_basis"] == "call-index"
    assert run["ridge_tool_calls"] is None


def test_the_ridge_payload_still_carries_no_message_text(parsed):
    run = parsed(store_calls=5, transcript_calls=3)
    public = {key: value for key, value in run.items() if not key.startswith("private_")}
    assert "PRIVATE MESSAGE" not in json.dumps(public)
    assert "PRIVATE TEXT MUST NOT LEAK" not in json.dumps(public)
    assert "/secret/path" not in json.dumps(public)
