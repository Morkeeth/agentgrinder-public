"""Cursor's per-session chat store and the fallback order around it.

The fixture is built here rather than copied from a real store, so no private bytes enter the
repository. The encoder below writes the same three fields the real records carry, and
`test_the_reader_refuses_a_record_without_the_signature` proves the reader can go red.
"""
import sqlite3
import struct
from pathlib import Path

import pytest

from agentgrinder import cursor_chats


def varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(out)


def field(number: int, wire: int) -> bytes:
    return varint((number << 3) | wire)


def delimited(number: int, body: bytes) -> bytes:
    return field(number, 2) + varint(len(body)) + body


def scalar(number: int, value: int) -> bytes:
    return field(number, 0) + varint(value)


def shell_body(command: str) -> bytes:
    """field 1 -> field 1 -> field 1 is where the real store keeps the command string."""
    inner = delimited(1, command.encode("utf8"))
    return delimited(1, inner)


def tool_record(call_id: str, requested_ms: int, command: str | None = None) -> bytes:
    body = b""
    if command is not None:
        body += delimited(cursor_chats.FIELD_SHELL, shell_body(command))
    else:
        body += delimited(8, b"\x0a\x03abc")          # some other tool kind, no command
    body += delimited(cursor_chats.FIELD_CALL_ID, call_id.encode("utf8"))
    body += scalar(cursor_chats.FIELD_REQUESTED_AT, requested_ms)
    body += scalar(cursor_chats.FIELD_RESULT_AT, requested_ms + 100)
    return delimited(cursor_chats.FIELD_TOOL_RECORD, body)


def write_store(folder: Path, composer_id: str, records: list[bytes],
                messages: list[bytes] | None = None, meta_extra: dict | None = None) -> Path:
    home = folder / "0123456789abcdef0123456789abcdef" / composer_id
    home.mkdir(parents=True)
    db = home / "store.db"
    conn = sqlite3.connect(db)
    conn.execute("create table blobs (id TEXT PRIMARY KEY, data BLOB)")
    conn.execute("create table meta (key TEXT PRIMARY KEY, value TEXT)")
    for index, blob in enumerate(records + (messages or [])):
        conn.execute("insert into blobs values (?,?)", ("%064x" % index, blob))
    import json
    meta = {
        "agentId": composer_id,
        "latestRootBlobId": "0" * 64,
        "createdAt": 1789457877614,
    }
    meta.update(meta_extra or {})
    conn.execute("insert into meta values ('0', ?)", (json.dumps(meta).encode().hex(),))
    conn.commit()
    conn.close()
    (home / "meta.json").write_text(
        '{"schemaVersion":1,"createdAtMs":1789457877614,"hasConversation":true,'
        '"title":"fixture","updatedAtMs":1789541773811,"cwd":"/tmp"}')
    return db


BASE = 1_789_000_000_000


def test_the_chat_store_is_found_by_composer_id_under_any_workspace_hash(tmp_path):
    write_store(tmp_path, "aaaa-bbbb", [tool_record("call-1", BASE)])
    assert cursor_chats.store_for("aaaa-bbbb", tmp_path) is not None
    assert cursor_chats.store_for("no-such-session", tmp_path) is None


def test_tool_request_times_come_back_and_nothing_else_does(tmp_path):
    db = write_store(tmp_path, "s1", [
        tool_record("call-0", BASE),
        tool_record("call-1", BASE + 60_000, "git commit -m 'a private message'"),
        tool_record("call-2", BASE + 120_000, "ls /Users/someone/private"),
    ])
    with cursor_chats.CopiedChatDb(db) as conn:
        activity = cursor_chats.session_activity(conn)
    assert len(activity["tool_stamps"]) == 3
    assert len(activity["commit_stamps"]) == 1
    # Not one command string, path or id survives.
    flat = repr(activity)
    for private in ("private message", "/Users/someone", "call-0", "ls "):
        assert private not in flat


def test_a_json_message_blob_is_never_read_as_a_step(tmp_path):
    db = write_store(tmp_path, "s2", [tool_record("call-0", BASE)],
                     messages=[b'{"role":"tool","content":[{"toolCallId":"call-0"}]}'])
    with cursor_chats.CopiedChatDb(db) as conn:
        activity = cursor_chats.session_activity(conn)
    assert len(activity["tool_stamps"]) == 1


def test_the_reader_refuses_a_record_without_the_signature(tmp_path):
    """A check nobody has seen fail is not a check. Drop field 59 and the record must not count."""
    body = (delimited(8, b"\x0a\x03abc")
            + delimited(cursor_chats.FIELD_CALL_ID, b"call-0")
            + scalar(cursor_chats.FIELD_RESULT_AT, BASE))
    db = write_store(tmp_path, "s3", [delimited(cursor_chats.FIELD_TOOL_RECORD, body)])
    with cursor_chats.CopiedChatDb(db) as conn:
        activity = cursor_chats.session_activity(conn)
    assert activity["tool_stamps"] == []


def test_the_ridge_is_timed_and_its_window_is_the_real_span(tmp_path):
    write_store(tmp_path, "s4", [tool_record("call-%d" % i, BASE + i * 60_000)
                                 for i in range(20)])
    ridge = cursor_chats.build_ridge("s4", tmp_path)
    assert ridge["ridge_basis"] == "wall-time"
    assert ridge["ridge_wall_seconds"] == pytest.approx(19 * 60.0)
    assert sum(ridge["ridge"]) == 20
    assert len(ridge["ridge"]) == 50


def test_cursor_capture_prefers_the_per_session_timed_ridge(tmp_path, monkeypatch):
    from agentgrinder.ingest import parse_cursor_session

    composer = "capture-session"
    chats = tmp_path / "chats"
    write_store(chats, composer, [
        tool_record("call-0", BASE),
        tool_record("call-1", BASE + 15 * 60_000),
    ])
    transcript_dir = tmp_path / "project" / "agent-transcripts" / composer
    transcript_dir.mkdir(parents=True)
    transcript = transcript_dir / "session.jsonl"
    transcript.write_text(
        '{"role":"user","message":{"content":"<user_query>private</user_query>"}}\n'
        '{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{}}]}}\n'
    )
    monkeypatch.setenv(cursor_chats.ENV_CHATS, str(chats))

    run = parse_cursor_session(str(transcript))

    assert run["ridge_source"] == "cursor-chat-store"
    assert run["ridge_basis"] == "wall-time"
    assert run["ridge_wall_seconds"] == run["duration_s"] == 15 * 60
    assert run["capabilities"]["timed_ridge"] is True


def test_worker_bins_come_from_child_store_parent_metadata(tmp_path):
    parent = "parent-session"
    write_store(tmp_path, parent, [
        tool_record("parent-%d" % i, BASE + i * 60_000) for i in range(6)
    ])
    link = {"subagentInfo": {
        "parentAgentId": parent,
        "rootParentAgentId": parent,
        "typeName": "generalPurpose",
    }}
    write_store(tmp_path, "child-one", [
        tool_record("child-one-%d" % i, BASE + i * 60_000) for i in (1, 3)
    ], meta_extra=link)
    write_store(tmp_path, "child-two", [
        tool_record("child-two-%d" % i, BASE + i * 60_000) for i in (2, 4)
    ], meta_extra=link)
    analysis_store = write_store(tmp_path, "analysis-only", [], meta_extra=link)
    analysis_store.with_name("meta.json").write_text(
        '{"createdAtMs":1789000120000,"updatedAtMs":1789000180000}')
    write_store(tmp_path, "grandchild", [
        tool_record("grandchild-%d" % i, BASE + i * 60_000) for i in (2, 3)
    ], meta_extra={"subagentInfo": {
        "parentAgentId": "child-one",
        "rootParentAgentId": parent,
        "typeName": "explore",
    }})

    ridge = cursor_chats.build_ridge(parent, tmp_path)

    assert max(ridge["worker_bins"]) == 3
    assert sum(1 for value in ridge["worker_bins"] if value) > 1
    # The grandchild is not a direct worker of the orchestrator.
    windows = cursor_chats.worker_windows(parent, tmp_path)
    assert len(windows) == 3
    assert all(set(window) == {"started_at", "ended_at"} for window in windows)
    assert parent not in repr(windows)
    assert "child-" not in repr(windows)


def test_an_absent_session_returns_none_rather_than_a_guess(tmp_path):
    assert cursor_chats.build_ridge("not-here", tmp_path) is None


def transcript_for(folder: Path, composer_id: str, ended: bool, age_seconds: float) -> Path:
    import os
    import time
    home = folder / "project" / "agent-transcripts" / composer_id
    home.mkdir(parents=True)
    path = home / (composer_id + ".jsonl")
    lines = ['{"role": "user", "message": {"content": "hello"}}']
    if ended:
        lines.append('{"type":"turn_ended","status":"success"}')
    path.write_text("\n".join(lines))
    when = time.time() - age_seconds
    os.utime(path, (when, when))
    return path


def test_the_hook_sees_a_finished_chat_session(tmp_path, monkeypatch):
    chats, projects = tmp_path / "chats", tmp_path / "projects"
    write_store(chats, "done", [tool_record("call-0", BASE)])
    transcript_for(projects, "done", ended=True, age_seconds=600)
    monkeypatch.setenv(cursor_chats.ENV_PROJECTS, str(projects))
    assert cursor_chats.finished_chat_composers(chats) == ["done"]


def test_a_session_still_being_typed_in_is_not_offered_yet(tmp_path, monkeypatch):
    """The marker says a TURN ended, not the session. A still warm transcript waits."""
    chats, projects = tmp_path / "chats", tmp_path / "projects"
    write_store(chats, "warm", [tool_record("call-0", BASE)])
    transcript_for(projects, "warm", ended=True, age_seconds=5)
    monkeypatch.setenv(cursor_chats.ENV_PROJECTS, str(projects))
    assert cursor_chats.finished_chat_composers(chats) == []


def test_a_session_whose_last_turn_never_ended_is_not_offered(tmp_path, monkeypatch):
    chats, projects = tmp_path / "chats", tmp_path / "projects"
    write_store(chats, "open", [tool_record("call-0", BASE)])
    transcript_for(projects, "open", ended=False, age_seconds=600)
    monkeypatch.setenv(cursor_chats.ENV_PROJECTS, str(projects))
    assert cursor_chats.finished_chat_composers(chats) == []


def test_a_session_with_no_transcript_is_skipped_rather_than_churned(tmp_path, monkeypatch):
    """`_capture` needs a transcript. Offering one without it makes the hook retry forever."""
    chats, projects = tmp_path / "chats", tmp_path / "projects"
    projects.mkdir()
    write_store(chats, "no-transcript", [tool_record("call-0", BASE)])
    monkeypatch.setenv(cursor_chats.ENV_PROJECTS, str(projects))
    assert cursor_chats.finished_chat_composers(chats) == []


def test_the_window_beside_the_store_is_read_as_iso(tmp_path):
    write_store(tmp_path, "s5", [tool_record("call-0", BASE)])
    window = cursor_chats.session_window("s5", tmp_path)
    assert window == ("2026-09-15T07:37:57.614000Z", "2026-09-16T06:56:13.811000Z")
