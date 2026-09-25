"""Cursor and Codex read their own file writes, their own commits and their own repository.

Until 4 September 2026 both parsers returned `None` for files touched, commits, artifacts and
reach, and the card printed a dash with a sentence blaming the harness. The sentence was wrong.
The facts were in the transcripts the whole time:

  Cursor  `Write` and `StrReplace` tool_use blocks carry an absolute `path`. Measured over the
          298 transcripts on the author's machine: 2,279 such blocks, every path absolute, 2,233
          still on disk. `Shell` carries the command string, so `git commit` is countable.
  Codex   `patch_apply_end` carries `changes`, a dict keyed by absolute path, with a `success`
          flag. `session_meta` carries `cwd`. Every record carries an ISO timestamp.

What this file holds is the behaviour, on fixtures written here. Two rules are load-bearing and
each has its own test: a failed patch is not a write, and a count that has no source stays None
rather than becoming a zero.

Claim detection remains outside these parsers until the harness calibration is resolved.
Missing claim counts and verification stay unknown, never fabricated zeroes.
tests/test_claim_rule.py holds the detector calibration boundary.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentgrinder import reach
from agentgrinder.ingest import parse_cursor_session, parse_codex_session


def _repo(tmp_path, name="proj"):
    root = tmp_path / name
    (root / "src").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root


def _cursor(tmp_path, blocks, turns=2):
    """A Cursor transcript: `turns` typed turns with timestamps, then one assistant message."""
    lines = []
    for i in range(turns):
        lines.append(json.dumps({"role": "user", "message": {"content":
            f"<timestamp>Wednesday, Sep 03, 2026, {10 + i}:00 AM</timestamp>"
            "<user_query>go</user_query>"}}))
    lines.append(json.dumps({"role": "assistant", "message": {"content": blocks}}))
    path = tmp_path / "c.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def _codex(tmp_path, records, cwd):
    # COMPACT, no spaces after the colons. `_codex_count` counts typed turns with a substring
    # scan rather than json.loads, because Codex writes megabyte lines; a pretty-printed fixture
    # would silently report zero typed turns and this whole file would test nothing.
    dump = lambda o: json.dumps(o, separators=(",", ":"))
    lines = [dump({"type": "session_meta", "timestamp": "2026-09-03T10:00:00.000Z",
                   "payload": {"type": "session_meta", "cwd": str(cwd)}}),
             dump({"type": "event_msg", "timestamp": "2026-09-03T10:01:00.000Z",
                   "payload": {"type": "user_message"}})]
    for i, payload in enumerate(records):
        lines.append(dump({"type": "event_msg",
                           "timestamp": "2026-09-03T10:%02d:00.000Z" % (2 + i),
                           "payload": payload}))
    path = tmp_path / "rollout-t.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


# ---- Cursor ---------------------------------------------------------------------------------

def test_cursor_reads_the_files_it_wrote(tmp_path):
    root = _repo(tmp_path)
    made = root / "src" / "a.py"
    made.write_text("x = 1\n", encoding="utf-8")
    gone = root / "src" / "never.py"        # written in the transcript, absent on disk
    run = parse_cursor_session(_cursor(tmp_path, [
        {"type": "tool_use", "name": "Write", "input": {"path": str(made), "contents": "x"}},
        {"type": "tool_use", "name": "StrReplace",
         "input": {"path": str(gone), "old_string": "a", "new_string": "b"}},
        {"type": "tool_use", "name": "Read", "input": {"path": str(made)}},
    ]))
    assert run["files_touched"] == 2          # Read is not a write
    assert run["artifacts_produced"] == 1     # only the one that exists on disk
    assert run["route_legend"] == ["src"]
    assert run["route"] == [0]                # three touches in one folder are one stay


def test_cursor_counts_shell_calls_and_commit_markers(tmp_path):
    root = _repo(tmp_path)
    run = parse_cursor_session(_cursor(tmp_path, [
        {"type": "tool_use", "name": "Write", "input": {"path": str(root / "src" / "a.py")}},
        {"type": "tool_use", "name": "Shell", "input": {"command": "git commit -m x"}},
        {"type": "tool_use", "name": "Shell", "input": {"command": "ls -la"}},
    ]))
    assert run["commits"] == 1
    assert run["shell_calls"] == 2


def test_cursor_finds_the_repository_from_the_files_it_wrote(tmp_path):
    """Cursor never states a working directory, so the repository comes from the writes."""
    root = _repo(tmp_path)
    run = parse_cursor_session(_cursor(tmp_path, [
        {"type": "tool_use", "name": "Write", "input": {"path": str(root / "src" / "a.py")}},
    ]))
    # a real answer from reach.py, not the old "this harness cannot supply it"
    assert run["reach"] is None
    assert run["reach_reason"] == reach.R_NO_WINDOW  # embedded times lack a timezone


def test_cursor_that_wrote_nothing_reports_nothing(tmp_path):
    run = parse_cursor_session(_cursor(tmp_path, [
        {"type": "tool_use", "name": "Read", "input": {"path": "/tmp/x"}},
    ]))
    assert run["files_touched"] is None
    assert run["artifacts_produced"] is None
    assert run["reach_reason"] == reach.R_NO_FILES


# ---- Codex ----------------------------------------------------------------------------------

def test_codex_reads_the_patches_it_applied(tmp_path):
    root = _repo(tmp_path, "codexproj")
    made = root / "src" / "b.py"
    made.write_text("y = 2\n", encoding="utf-8")
    run = parse_codex_session(_codex(tmp_path, [
        {"type": "patch_apply_end", "success": True,
         "changes": {str(made): {"type": "update"},
                     str(root / "src" / "absent.py"): {"type": "add"}}},
    ], cwd=root))
    assert run["files_touched"] == 2
    assert run["artifacts_produced"] == 1
    assert run["route_legend"] == ["src"]


def test_codex_does_not_count_a_failed_patch_as_a_write(tmp_path):
    """An attempt is not an artifact. This is the ceiling problem in a different column."""
    root = _repo(tmp_path, "codexproj")
    run = parse_codex_session(_codex(tmp_path, [
        {"type": "patch_apply_end", "success": False,
         "changes": {str(root / "src" / "c.py"): {"type": "add"}}},
    ], cwd=root))
    assert run["files_touched"] is None
    assert run["artifacts_produced"] is None


def test_codex_counts_a_commit_from_its_exec_tool(tmp_path):
    root = _repo(tmp_path, "codexproj")
    run = parse_codex_session(_codex(tmp_path, [
        {"type": "custom_tool_call", "name": "exec", "input": '{"cmd":["git","commit","-m","x"]}'},
        {"type": "custom_tool_call", "name": "exec", "input": '{"cmd":["ls"]}'},
    ], cwd=root))
    assert run["commits"] == 1


def test_codex_draws_a_window_from_its_own_timestamps(tmp_path):
    root = _repo(tmp_path, "codexproj")
    run = parse_codex_session(_codex(tmp_path, [
        {"type": "patch_apply_end", "success": True,
         "changes": {str(root / "src" / "d.py"): {"type": "add"}}},
    ], cwd=root))
    assert run["started"] is not None
    assert run["duration_s"] and run["duration_s"] > 0
    # a repository AND a window, so reach.py answers rather than the harness excusing itself
    assert run["reach_reason"] == reach.R_NO_COMMITS


# ---- the rule both parsers must keep -------------------------------------------------------

def test_neither_parser_invents_a_zero(tmp_path):
    """A count with no source is None. A zero is an assertion that nothing happened."""
    cur = parse_cursor_session(_cursor(tmp_path, []))
    cod = parse_codex_session(_codex(tmp_path, [], cwd=tmp_path / "nope"))
    for run in (cur, cod):
        for field in ("files_touched", "commits", "artifacts_produced",
                      "artifacts_promised", "corrections", "reach"):
            assert run[field] is None, f"{run['harness']} invented {field} = {run[field]!r}"
        assert run["reach_reason"]
        # Evidence half stays unmeasured — never a fabricated verified=0.
        assert run.get("claims_verified") is None
    # Unresolved detector calibration is unknown, not a measured zero.
    assert "claims" not in cur
    assert "claims" not in cod


# ---- the empty machine: no green check over a population of zero -----------------------------
#
# Found by the stranger audit on 4 Sep 2026, by running the CLI under `env -i` with an empty HOME.
# `authorship` printed the full table of zeros and then "parts sum to the total: 0 + 0 + 0 + 0 + 0
# = 0  OK". The sum is real and the OK means nothing: an identity over an empty population passes
# whatever the classifier does, so it is a check that cannot go red, printed by the one tool whose
# whole subject is a number that is correct about the wrong object.

def test_authorship_prints_no_ok_when_there_is_nothing_to_check(monkeypatch, capsys):
    """Drives the empty-window branch directly rather than by faking HOME.

    The first version of this test monkeypatched `os.path.expanduser`. It passed alone and failed
    in the suite, because by then another test had already imported the modules that resolve those
    paths, so the real machine's 354 records walked into a test about an empty one. A test whose
    result depends on which tests ran before it is not measuring what it claims to measure.
    """
    from agentgrinder import cli, fleet
    monkeypatch.setattr(fleet, "collect", lambda *a, **k: {
        "started": "2026-09-04T10:00:00", "ended": "2026-09-04T10:30:00",
        "lanes": [], "sessions": [],
        "authorship": {"gate": "test", "user_records_total": 0,
                       "by_category": {c: 0 for c in
                                       ("human", "tool_result", "injected", "orchestrator", "harness")},
                       "keystrokes_in_lane_transcripts": 0}})
    rc = cli.main(["authorship"])
    out = capsys.readouterr().out
    assert rc == 0
    # the exact green check, not the substring "OK", so the assertion names what it forbids
    assert "parts sum to the total" not in out, "the sum is printed over an empty population"
    assert "= 0  OK" not in out, "an empty machine is still being shown a green check"
    assert "nothing to check" in out


def test_authorship_still_prints_the_sum_when_there_is_a_population(monkeypatch, capsys):
    """The check must still fire when it means something. Watched going the other way."""
    from agentgrinder import cli, fleet
    cats = {"human": 4, "tool_result": 85, "injected": 6, "orchestrator": 0, "harness": 0}
    monkeypatch.setattr(fleet, "collect", lambda *a, **k: {
        "started": "2026-09-04T10:00:00", "ended": "2026-09-04T10:30:00",
        "lanes": [], "sessions": [],
        "authorship": {"gate": "test", "user_records_total": sum(cats.values()),
                       "by_category": cats, "keystrokes_in_lane_transcripts": 0}})
    rc = cli.main(["authorship"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "parts sum to the total: 4 + 85 + 6 + 0 + 0 = 95  OK" in out


def test_history_does_not_print_empty_rankings(monkeypatch, capsys):
    from agentgrinder import cli, history
    monkeypatch.setattr(history, "load", lambda *a, **k: [])
    rc = cli.main(["history"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "0 grinds on this machine" in out
    assert "by tool calls:" not in out, "five empty headings read like a broken command"
    assert "Nothing to rank yet" in out


def test_vibe_and_roast_name_where_they_looked(monkeypatch, capsys):
    """`grind` names all four transcript paths and offers `demo`. These printed three words."""
    from agentgrinder import cli
    monkeypatch.setattr(cli, "_load_latest_run", lambda *a, **k: None)
    for cmd in ("vibe", "roast"):
        rc = cli.main([cmd])
        out = capsys.readouterr().out
        assert rc == 1, cmd
        assert "~/.claude/projects" in out and "~/.cursor" in out and "~/.codex" in out, cmd
        assert "agentgrinder demo" in out, cmd
