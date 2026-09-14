"""One supported friction, one next experiment. Live config is exact, never fabricated."""
import os
import subprocess
import sys

from agentgrinder.coach.experiment import activity_experiment, from_history, select_experiment
from agentgrinder.coach.live_config import missing_live_config, live_status_text
from agentgrinder.coach.policy import coach_policy

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_named_unverified_claim_beats_a_claim_id_dump():
    claims = [
        {"id": 1, "turn": 1, "line": "Suite passes."},
        {"id": 2, "turn": 2, "line": "Done, test_never_ran passes."},
    ]
    checks = [
        {"claim_id": 1, "verified": True, "evidence": "3 passed"},
        {"claim_id": 2, "verified": False, "results_in_turn": 1},
    ]
    exp = select_experiment(
        claims=claims, checks=checks, artifacts=[], exists=[], gits=[],
        turns_typed=2, commits=0,
    )
    assert exp["kind"] == "unverified-named-claim"
    assert exp["title"].startswith("Run test_never_ran")
    assert "test_never_ran" in exp["instruction"]
    assert exp["plan"][0].startswith("Friction:")
    assert any(p.startswith("Experiment:") for p in exp["plan"])
    assert "Claims [2]" not in "\n".join(exp["plan"])


def test_policy_plan_is_one_experiment_not_a_claim_list():
    rr = {
        "turns_typed": 2, "commits": 0, "in_git": False,
        "claims": [
            {"id": 1, "turn": 1, "line": "Suite passes."},
            {"id": 2, "turn": 2, "line": "Done, test_never_ran passes."},
        ],
        "artifacts": [{"id": 1, "label": "out.md"}, {"id": 2, "label": "never.md"}],
    }
    history = [
        ("read_run", {}, rr),
        ("check_claim", {"claim_id": 1}, {"claim_id": 1, "verified": True, "evidence": "ok"}),
        ("check_claim", {"claim_id": 2}, {"claim_id": 2, "verified": False, "results_in_turn": 1}),
        ("verify_artifact", {"artifact_id": 1}, {"artifact_id": 1, "label": "out.md", "exists": True}),
        ("verify_artifact", {"artifact_id": 2}, {"artifact_id": 2, "label": "never.md", "exists": False}),
    ]
    step = coach_policy(history)
    assert step[0] == "write_verdict"
    plan = "\n".join(step[1]["plan"])
    assert plan.startswith("Friction:")
    assert "test_never_ran" in plan
    assert "Claims [" not in plan
    exp = from_history(history, rr)
    assert exp["kind"] == "unverified-named-claim"


def test_activity_experiment_does_not_invent_a_success_rate():
    exp = activity_experiment({"turns_typed": 4, "tool_calls": 40, "commits": 0})
    assert exp["kind"] == "activity-no-commit"
    assert "success rate" in exp["friction"]
    assert "0 commits" in exp["friction"]


def test_live_status_names_exact_missing_config_and_never_prints_secrets(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    text = live_status_text()
    assert "LIVE MODEL STATUS" in text
    assert "scripted Strands" in text
    items = missing_live_config()
    assert items, "this environment should not look live-ready without a region and credentials"
    for item in items:
        assert item["id"] in text
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
    assert "wJalrXUtnFEMI" not in live_status_text()
    assert "AKIAIOSFODNN7EXAMPLE" not in live_status_text()


def test_cli_live_status_does_not_start_a_live_run():
    proc = subprocess.run(
        [sys.executable, "-m", "agentgrinder", "coach", "--live-status"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert "LIVE MODEL STATUS" in proc.stdout
    assert proc.returncode in (0, 2)
    assert "wJalr" not in proc.stdout


def test_bedrock_without_config_does_not_fabricate_a_live_verdict(tmp_path, monkeypatch):
    import pytest
    pytest.importorskip("strands", reason="optional coach SDK is not installed")
    from agentgrinder.coach.agent import run_coach
    from agentgrinder.coach.live_config import LiveConfigError
    from tests.test_coach_tools import _sitting
    monkeypatch.setattr("agentgrinder.coach.live_config.missing_live_config", lambda: [
        {"id": "aws-region", "need": "Set AWS_REGION to a Bedrock-enabled region."}
    ])
    path, _, _ = _sitting(tmp_path)
    try:
        run_coach(path, mode="bedrock")
        raise AssertionError("live coaching started without configuration")
    except LiveConfigError as exc:
        assert "aws-region" in str(exc)
        assert "DEGRADED" not in str(exc)
