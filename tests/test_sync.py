"""Automatic fetch (agentgrinder sync): finished sessions become private drafts, once each."""
import io
import json
import os
import shutil
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("STRIVE_HOME", str(tmp_path / ".strive"))
    import importlib
    from agentgrinder import sync
    importlib.reload(sync)
    codex = tmp_path / ".codex" / "sessions" / "2026" / "09" / "24"
    codex.mkdir(parents=True)
    target = codex / "rollout-2026-09-24T10-00-00-test.jsonl"
    shutil.copy(ROOT / "samples/dropin/codex-desktop.jsonl", target)
    old = time.time() - 3600
    os.utime(target, (old, old))
    return tmp_path, sync, target


class Opener:
    def __init__(self):
        self.requests = []

    def __call__(self, request, timeout=30):
        self.requests.append(request)
        body = json.dumps({"id": "11111111-1111-1111-1111-111111111111", "visibility": "private", "existing": False})
        return io.BytesIO(body.encode())


def test_a_finished_session_is_sent_once_as_a_private_run_with_counts_only(home):
    tmp, sync, target = home
    found = sync.discover()
    assert ("codex", str(target)) in found
    opener = Opener()
    counts = sync.sync_once("ag_test", site="https://strive.test", opener=opener, out=lambda *_: None)
    assert counts["sent"] == 1 and counts["failed"] == 0
    req = opener.requests[0]
    assert req.full_url == "https://strive.test/api/agent/runs"
    assert req.get_header("Authorization") == "Bearer ag_test"
    payload = json.loads(req.data)
    assert payload["visibility"] == "private"
    assert "title" not in payload or payload["title"] in (None, "")
    blob = json.dumps(payload)
    for probe in (str(tmp), "PROMPT-SENTINEL", "/Users/", ".jsonl"):
        assert probe not in blob, probe
    # Second run: nothing new is sent, and the state file holds no paths.
    again = Opener()
    counts = sync.sync_once("ag_test", site="https://strive.test", opener=again, out=lambda *_: None)
    assert counts["sent"] == 0 and counts["already"] == 1 and not again.requests
    state = (tmp / ".strive" / "synced.json").read_text()
    assert str(target) not in state and "codex" not in state


def test_the_idempotency_key_is_stable_for_one_file_and_changes_when_it_grows(home):
    _, sync, target = home
    k1 = sync.idempotency_key(sync.file_key("codex", str(target)))
    assert k1 == sync.idempotency_key(sync.file_key("codex", str(target)))
    with open(target, "a") as f:
        f.write("\n")
    old = time.time() - 3600
    os.utime(target, (old, old))
    assert k1 != sync.idempotency_key(sync.file_key("codex", str(target)))


def test_a_session_still_being_written_waits(home):
    _, sync, target = home
    os.utime(target, None)   # just modified
    assert ("codex", str(target)) not in sync.discover()


def test_the_token_file_is_private_and_a_dry_run_sends_nothing(home):
    tmp, sync, _ = home
    path = sync.save_token("ag_secret")
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    assert sync.read_token() == "ag_secret"
    opener = Opener()
    lines = []
    counts = sync.sync_once("ag_secret", dry_run=True, opener=opener, out=lines.append)
    assert counts["sent"] == 1 and not opener.requests and lines
    assert not (tmp / ".strive" / "synced.json").exists()


def test_the_cli_knows_sync():
    from agentgrinder.cli import main
    with pytest.raises(SystemExit) as out:
        main(["sync", "--help"])
    assert out.value.code == 0
