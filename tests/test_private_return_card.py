"""Private STRIDE card: selected outcome, commit-derived Code Route, absent stays absent."""
import json
from pathlib import Path

import pytest

from agentgrinder import hook
from agentgrinder.code_route import attach_measured_code_route
from agentgrinder.metrics import build_activity
from agentgrinder.render import render_card


def _measured_run(**extra):
    run = {
        "athlete": "you",
        "title": "Cursor sitting",
        "harness": "Cursor",
        "project": "agentgrinder-public",
        "project_proven": True,
        "started": "2026-09-22T08:00:00+00:00",
        "turns_typed": 4,
        "tool_calls": 40,
        "files_touched": 6,
        "commits": 2,
        "rhythm": [1] * 20,
        "ridge": [0] * 50,
        "ridge_basis": "call-index",
        "ridge_wall_seconds": 180,
        "worker_bins": [0] * 50,
        "commit_bins": [],
        "capabilities": {"timed_trace": False},
    }
    run.update(extra)
    return attach_measured_code_route(run)


def test_private_card_omits_outcome_and_receipts_when_absent():
    html = render_card(build_activity(_measured_run()))
    assert "Selected outcome" not in html
    assert "Receipts" not in html
    assert "Code Route" in html
    assert "6 files changed" in html
    assert "2 commits landed" in html


def test_private_card_shows_selected_outcome_with_receipt_links():
    run = _measured_run(
        shipped=["Pitch and Post your first run stay above the card at 390 px."],
        receipts=[{
            "label": "PR 72",
            "url": "https://github.com/Morkeeth/agentgrinder-public/pull/72",
        }],
    )
    html = render_card(build_activity(run))
    assert "Selected outcome" in html
    assert "Pitch and Post your first run stay above the card at 390 px." in html
    assert "PR 72" in html
    assert "https://github.com/Morkeeth/agentgrinder-public/pull/72" in html


def test_caption_alone_does_not_become_selected_outcome():
    # Guard: a caption without receipts must not invent a receipt-backed hero.
    html = render_card(build_activity(_measured_run(caption="Looks great")))
    assert "Selected outcome" not in html
    assert "Looks great" not in html


def test_review_rejects_non_https_receipt(tmp_path):
    composer = "bbbbbbbb-1111-1111-1111-111111111111"
    hook.store_run(tmp_path, composer, _measured_run())
    with pytest.raises(ValueError):
        hook.apply_review(
            tmp_path, composer,
            outcome="A real selected outcome",
            receipts=[{"label": "bad", "url": "http://example.com/not-https"}],
        )
    # Card must still lack the rejected outcome (reload persistence of prior state).
    card = (tmp_path / "cards" / f"{composer}.html").read_text()
    assert "Selected outcome" not in card


def test_review_reload_preserves_selected_outcome_and_route(tmp_path):
    composer = "cccccccc-2222-2222-2222-222222222222"
    hook.store_run(tmp_path, composer, _measured_run())
    first = hook.apply_review(
        tmp_path, composer,
        outcome="Landing pitch leads at 390 px.",
        receipts=[{
            "label": "PR 72",
            "url": "https://github.com/Morkeeth/agentgrinder-public/pull/72",
        }],
        repo_url="https://github.com/Morkeeth/agentgrinder-public",
    )
    assert first["selected_outcome"] == "Landing pitch leads at 390 px."
    assert first["has_code_route"] is True
    card_path = Path(first["card"])
    html1 = card_path.read_text()
    # Reload: read draft again and re-render without changing selection.
    from agentgrinder.capture import connect
    db = connect(tmp_path / "capture")
    draft_id = __import__("hashlib").sha256(("cursor-composer:" + composer).encode()).hexdigest()
    payload = json.loads(db.execute("select payload from drafts where id=?", (draft_id,)).fetchone()[0])
    db.close()
    html2 = render_card(build_activity(payload))
    assert "Landing pitch leads at 390 px." in html1
    assert "Landing pitch leads at 390 px." in html2
    assert "Code Route" in html1 and "Code Route" in html2
    assert "PR 72" in html2


def test_unproven_project_yields_no_code_route_on_card():
    run = _measured_run(project_proven=False)
    # attach_measured_code_route should leave code_route absent
    assert "code_route" not in run or run.get("code_route") is None
    html = render_card(build_activity(run))
    assert "Code Route" not in html
