import json
import subprocess
import sys

from agentgrinder.outcome import NOTHING_SHIPPED
from agentgrinder.proposal import classify, propose
from agentgrinder.proposal_preview import render_proposal


def test_single_repo_run_compiles_without_manual_copy():
    run = {
        "project": "strive",
        "project_proven": True,
        "commits": 2,
        "commits_list": [{"subject": "Compile a result card", "at": "2026-09-29T10:00:00Z"}],
        "files_changed": 6,
        "checks_passed": 18,
        "wall_s": 1500,
    }
    card = propose(run)
    assert card.archetype == "shipper"
    assert card.outcome == "Compile a result card"
    assert [m.label for m in card.metrics] == ["commits", "files changed", "checks passing", "elapsed"]
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
    assert [m.label for m in card.metrics] == ["lanes", "returns", "activity estimate"]
    assert all(m.label != "handoffs" for m in card.metrics)
    assert all(m.label != "tool calls" for m in card.metrics)


def test_debug_run_can_propose_a_turn_from_measured_state_change():
    card = propose({
        "tests_failed_before": 2,
        "checks_passed": 43,
        "failed_check_ids_before": ["mobile-card", "privacy"],
        "passed_check_ids_after": ["privacy", "mobile-card", "unrelated"],
        "bugs_fixed": 1,
        "duration_s": 1200,
    })
    assert card.archetype == "debugger"
    assert card.turning_point == "2 matching checks failed before and passed after."
    assert [m.label for m in card.metrics] == ["bugs fixed", "checks passing", "activity estimate"]


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
    assert [(m.value, m.label) for m in card.metrics] == [("1", "commits"), ("2m", "activity estimate")]
    assert card.metrics[-1].basis == "capture-derived activity estimate; not exact active time"


def test_true_elapsed_prefers_wall_s_over_the_capped_gap_estimate():
    card = propose({"commits": 1, "wall_s": 600, "duration_s": 120})
    assert [(m.value, m.label, m.basis) for m in card.metrics][-1] == (
        "10m", "elapsed", "first-to-last event timestamps",
    )


def test_unmatched_fail_and_pass_counts_do_not_invent_a_turn():
    card = propose({"tests_failed_before": 2, "checks_passed": 43})
    assert card.turning_point == ""


def test_zero_web_searches_do_not_reclassify_a_shipper_as_research():
    card = propose({"web_searches": 0, "commits": 1})
    assert card.archetype == "shipper"


def test_cli_writes_a_private_html_proposal_and_does_not_publish_or_open(tmp_path, monkeypatch):
    run = tmp_path / "run.json"
    out = tmp_path / "proposal.html"
    run.write_text(json.dumps({
        "commits": 1,
        "duration_s": 60,
        "raw_transcript": "PRIVATE TRANSCRIPT SENTENCE",
        "session_path": "/Users/private/person/session.jsonl",
    }), encoding="utf-8")
    from agentgrinder import cli
    opened = []
    monkeypatch.setattr(cli._BROWSER, "open", opened.append)
    assert cli.main(["propose", str(run), "-o", str(out)]) == 0
    html = out.read_text()
    assert "Private proposal · local only · not published" in html
    assert "1 commit landed" in html
    assert "PRIVATE TRANSCRIPT SENTENCE" not in html
    assert "/Users/" not in html and "session.jsonl" not in html
    assert opened == []


def test_cli_open_is_explicit_opt_in(tmp_path, monkeypatch):
    run = tmp_path / "run.json"
    out = tmp_path / "proposal.html"
    run.write_text('{"commits":1}', encoding="utf-8")
    from agentgrinder import cli
    opened = []
    monkeypatch.setattr(cli._BROWSER, "open", opened.append)
    assert cli.main(["propose", str(run), "-o", str(out), "--open"]) == 0
    assert opened == [out.resolve().as_uri()]


def test_cli_default_is_a_local_html_file(tmp_path, monkeypatch):
    run = tmp_path / "run.json"
    run.write_text('{"commits":1}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    from agentgrinder import cli
    assert cli.main(["propose", str(run)]) == 0
    assert (tmp_path / "proposal.html").read_text().startswith("<!doctype html>")


def test_preview_renders_result_proof_turn_metrics_limit_and_expandable_basis():
    html = render_proposal(propose({
        "shipped": ["The local card renders the measured result"],
        "receipts": [{"url": "https://example.com/proof", "label": "Inspect proof"}],
        "tests_failed_before": 2,
        "checks_passed": 43,
        "failed_check_ids_before": ["mobile-card", "privacy"],
        "passed_check_ids_after": ["privacy", "mobile-card"],
        "bugs_fixed": 1,
        "regressions_found": 0,
        "duration_s": 1200,
    }))
    for label in (">Result<", ">Proof<", ">Turn<", ">Measured<", ">Limit<"):
        assert label in html
    assert "2 matching checks failed before and passed after." in html
    assert "Inspect proof" in html
    assert html.count('class="metric"') == 4
    assert '<details class="basis"><summary>Measurement basis</summary>' in html
    assert "passing checks recorded by the run" in html


def test_unsupported_sections_and_unknown_metrics_are_absent():
    html = render_proposal(propose({"tool_calls": 90, "raw_transcript": "do not render me"}))
    assert ">Proof<" not in html and ">Turn<" not in html and ">Measured<" not in html
    assert "Measurement basis" not in html
    assert "tool calls" not in html and "do not render me" not in html


def test_activity_route_visual_is_compiled_from_numeric_route_only():
    card = propose({"route": [8, 8, 3, 3, 8, 11], "commits": 1})
    assert card.visual is not None
    assert card.visual.kind == "route"
    assert card.visual.label == "Activity route"
    assert card.visual.values == (50, 0, 50, 100)
    assert "run.route" in card.visual.basis
    assert "evenly sampled" in card.visual.basis
    assert "not a rank" in card.visual.limitation
    assert "quality, progress, success" in card.visual.limitation
    html = render_proposal(card)
    assert ">Activity route<" in html
    assert 'role="img" aria-labelledby="activity-title activity-desc"' in html
    assert "Field and method" in html and "Window" in html and "Limit" in html


def test_visual_is_absent_without_valid_route_or_ridge():
    for payload in ({}, {"route": []}, {"route": ["private/path"]},
                    {"ridge": [1] * 39, "ridge_basis": "wall-time"},
                    {"ridge": [1] * 50, "ridge_basis": "unknown"}):
        card = propose(payload)
        assert card.visual is None
        assert '<svg class="activity-visual"' not in render_proposal(card)

    single = propose({"route": [4]})
    assert single.visual is not None and single.visual.values == (0, 0)


def test_rhythm_visual_drops_private_prose_paths_and_unnormalized_counts():
    payload = {
        "ridge": [0, 4, 20, 8, 0] * 10,
        "ridge_basis": "turn-order",
        "raw_transcript": "PRIVATE SENTENCE",
        "prompt": "ship the secret",
        "session_path": "/Users/person/private/session.jsonl",
    }
    card = propose(payload)
    assert card.visual is not None
    assert card.visual.kind == "rhythm"
    assert set(card.visual.values) == {0, 20, 40, 100}
    compiled = repr(card)
    html = render_proposal(card)
    for private in ("PRIVATE SENTENCE", "ship the secret", "/Users/", "session.jsonl"):
        assert private not in compiled
        assert private not in html
    assert "run.ridge" in html and "turn-order bins" in html
    assert "Relative activity only" in html


def test_visual_replay_is_deterministic():
    payload = {"route": [index % 7 for index in range(5000)], "commits": 2}
    first = render_proposal(propose(payload))
    second = render_proposal(propose(json.loads(json.dumps(payload))))
    assert first == second
    assert len(propose(payload).visual.values) <= 48


def test_activity_visual_markup_stays_mobile_safe():
    html = render_proposal(propose({
        "ridge": [index % 9 for index in range(50)],
        "ridge_basis": "wall-time",
    }))
    assert 'viewBox="0 0 520 116"' in html
    assert ".activity-visual{display:block;width:100%;height:auto;max-width:100%;min-width:0" in html
    assert "preserveAspectRatio=\"none\"" in html
    assert "width:520px" not in html


def test_phone_contract_has_no_fixed_card_width_or_horizontal_overflow():
    html = render_proposal(propose({"commits": 2, "files_changed": 12, "checks_passed": 48}))
    assert '<meta name="viewport" content="width=device-width,initial-scale=1">' in html
    assert "html,body{margin:0;max-width:100%;overflow-x:hidden}" in html
    assert "main{width:100%;max-width:560px" in html
    assert "grid-template-columns:repeat(2,minmax(0,1fr))" in html
    assert ".card{background:var(--box)" in html
    assert "width:390px" not in html


def test_replay_is_byte_identical_and_does_not_embed_the_input_path(tmp_path):
    payload = {"commits": 3, "files_changed": 8, "wall_time_s": 450}
    first = render_proposal(propose(payload))
    second = render_proposal(propose(json.loads(json.dumps(payload))))
    assert first == second
    assert str(tmp_path) not in first


def test_subprocess_cli_writes_html(tmp_path):
    run = tmp_path / "run.json"
    out = tmp_path / "proposal.html"
    run.write_text(json.dumps({"commits": 1, "duration_s": 60}), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "agentgrinder", "propose", str(run), "-o", str(out)],
        capture_output=True, text=True, check=True,
    )
    assert "private proposal" in result.stdout
    assert out.read_text().startswith("<!doctype html>")
