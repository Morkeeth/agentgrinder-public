import json
import subprocess
import sys

from agentgrinder.outcome import NOTHING_SHIPPED
from agentgrinder.proposal import classify, propose


def test_single_repo_run_compiles_without_manual_copy():
    run = {
        "project": "strive",
        "project_proven": True,
        "commits": 2,
        "commits_list": [{"subject": "Compile a result card", "at": "2026-09-29T10:00:00Z"}],
        "files_changed": 6,
        "checks_passed": 18,
        "wall_time_s": 1500,
    }
    card = propose(run)
    assert card.archetype == "shipper"
    assert card.outcome == "Compile a result card"
    assert [m.label for m in card.metrics] == ["commits", "files changed", "checks passing", "wall time"]
    assert card.turning_point == ""
    assert "outside use" in card.limit


def test_parallel_run_uses_fleet_evidence_and_keeps_unknowns_out():
    card = propose({
        "projects": ["strive", "helicon", "favour"],
        "lane_count": 3,
        "lanes_returned": 2,
        "duration_s": 7200,
        "tool_calls": 400,
    })
    assert card.archetype == "fleet"
    assert card.outcome == NOTHING_SHIPPED
    assert [m.label for m in card.metrics] == ["lanes", "returns", "elapsed"]
    assert all(m.label != "handoffs" for m in card.metrics)
    assert all(m.label != "tool calls" for m in card.metrics)


def test_debug_run_can_propose_a_turn_from_measured_state_change():
    card = propose({
        "tests_failed_before": 2,
        "checks_passed": 43,
        "bugs_fixed": 1,
        "duration_s": 1200,
    })
    assert card.archetype == "debugger"
    assert card.turning_point == "2 failing checks became 43 passing."
    assert [m.label for m in card.metrics] == ["bugs fixed", "checks passing", "elapsed"]


def test_unreceipted_transcript_style_turning_point_is_not_used():
    card = propose({"turning_point": "The model realised everything", "tool_calls": 10})
    assert card.turning_point == ""
    assert card.outcome == NOTHING_SHIPPED


def test_receipted_declared_result_stays_declared_and_clickable():
    card = propose({
        "shipped": ["The reader opens the exact result"],
        "receipts": [{"url": "https://example.com/result", "label": "Try result"}],
        "assets_created": 1,
    })
    assert card.archetype == "creator"
    assert card.outcome == "The reader opens the exact result"
    assert card.proof_url == "https://example.com/result"
    assert card.proof_label == "Try result"
    assert "supplied by the author" in card.limit


def test_archetype_is_a_policy_not_a_confidence_score():
    assert classify({"sources_count": 4}) == "research"
    card = propose({"sources_count": 4})
    assert not hasattr(card, "confidence")


def test_fractional_elapsed_seconds_are_measured_not_dropped():
    card = propose({"commits": 1, "duration_s": 90.5})
    assert [(m.value, m.label) for m in card.metrics] == [("1", "commits"), ("2m", "elapsed")]


def test_cli_writes_a_private_proposal_and_does_not_publish(tmp_path):
    run = tmp_path / "run.json"
    out = tmp_path / "proposal.json"
    run.write_text(json.dumps({"commits": 1, "duration_s": 60}), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "agentgrinder", "propose", str(run), "-o", str(out)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "private proposal" in result.stdout
    payload = json.loads(out.read_text())
    assert payload["outcome"] == "1 commit landed"
    assert payload["archetype"] == "shipper"
    assert "published" not in payload
