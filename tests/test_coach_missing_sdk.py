"""`--coach` with no Strands SDK must not exit 0, and must never push.

Measured 3 Sep 2026 on a stock Mac: `grind --coach` under /usr/bin/python3 3.9.6 printed the
"coach needs the Strands SDK" line, rendered the card, and exited 0. With --push it also handed
over a publish URL for a run with no verdict. That is the same quiet degrade as the Cursor branch:
what was asked for did not happen and nothing in the exit code said so.

The SDK is present in this environment, so these tests take it away: setting sys.modules["strands"]
to None makes importlib.util.find_spec return None, which is exactly the state a 3.9 machine is in.
"""
import os
import sys

import pytest

from agentgrinder import cli

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(REPO, "samples", "sample_session.jsonl")


@pytest.fixture
def no_strands(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "strands", None)   # find_spec -> None, as on Python 3.9
    monkeypatch.setenv("AGENTGRINDER_SERIES", str(tmp_path / "series.db"))
    monkeypatch.setattr("webbrowser.open", lambda *a, **k: None)


def test_coach_requested_and_unavailable_is_a_non_zero_exit(no_strands, tmp_path, capsys):
    rc = cli.main(["grind", SAMPLE, "--coach", "--no-open", "-o", str(tmp_path / "card.html")])
    out = capsys.readouterr().out
    assert rc == 1, out
    assert "venv" in out                       # the remedy that can actually succeed
    assert "no verdict" in out
    assert (tmp_path / "card.html").exists()   # the real counts are still written


def test_a_verdictless_run_is_never_pushed(no_strands, tmp_path, capsys):
    rc = cli.main(["grind", SAMPLE, "--coach", "--push", "--no-open",
                   "-o", str(tmp_path / "card.html")])
    out = capsys.readouterr().out
    assert rc == 1
    assert "push ->" not in out and "preview ->" not in out and "#import=" not in out


def test_without_coach_the_same_run_is_still_exit_zero(no_strands, tmp_path, capsys):
    """No false alarm: the SDK is irrelevant to a plain grind."""
    rc = cli.main(["grind", SAMPLE, "--no-open", "-o", str(tmp_path / "card.html")])
    assert rc == 0, capsys.readouterr().out


def test_the_coach_still_runs_and_exits_zero_when_the_sdk_is_there(tmp_path, monkeypatch, capsys):
    pytest.importorskip("strands", reason="optional coach SDK is not installed")
    monkeypatch.setenv("AGENTGRINDER_SERIES", str(tmp_path / "series.db"))
    monkeypatch.setattr("webbrowser.open", lambda *a, **k: None)
    rc = cli.main(["grind", SAMPLE, "--coach", "--no-open", "-o", str(tmp_path / "card.html")])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "verdict" in out and "DEGRADED" not in out
