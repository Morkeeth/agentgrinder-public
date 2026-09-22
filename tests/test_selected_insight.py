"""ONE SELECTED INSIGHT: absent by default, bound to a receipt, and never a fleet called a run.

The three rules in agentgrinder/insight.py, each pinned here, and each one chosen because the
mutation that breaks it is the mutation that would ship a lie:

  drop the binding check   -> a sentence with nothing behind it prints in the card's hierarchy
  default it to present    -> a line the author never selected prints as if they had
  infer it from the text   -> the transcript writes the card's most prominent claim
  call a fleet a run       -> 24 sessions across 6 repositories read as one sitting

tests/README of this file: `docs/` is not the place for it, the mutations are run in the PR.
"""
import json
import subprocess
import sys

import pytest

sys.path.insert(0, __file__.rsplit("/tests/", 1)[0])

from agentgrinder import hook, insight
from agentgrinder.contract import selected_insight, validate_run
from agentgrinder.metrics import build_activity
from agentgrinder.render import render_card

RECEIPT = "https://github.com/Morkeeth/agentgrinder-public/pull/77"
OTHER = "https://github.com/Morkeeth/agentgrinder-public/pull/72"
LINE = "The correction that mattered: the home prefix rule needed no trailing dash."


def _run(**over):
    run = {
        "athlete": "you",
        "title": "agentgrinder-public · Cursor sitting",
        "harness": "Cursor",
        "project": "agentgrinder-public",
        "project_proven": True,
        "started": "2026-09-22T21:10:00",
        "turns_typed": 6,
        "tool_calls": 88,
        "files_changed": 9,
        "commits": 2,
        "rhythm": [1, 2, 1],
        "ridge": [i % 5 for i in range(50)],
        "worker_bins": [0] * 50,
        "commit_bins": [30],
        "ridge_basis": "wall-time",
        "ridge_wall_seconds": 1450,
        "capabilities": {"timed_trace": False, "claim_evidence": False},
    }
    run.update(over)
    return run


def _bound(**over):
    return _run(receipts=[{"label": "PR 77", "url": RECEIPT}],
                insight={"text": LINE, "receipt": RECEIPT}, **over)


# ---- absent by default --------------------------------------------------------------------

def test_a_run_with_no_selected_insight_shows_nothing_at_all():
    """Absence is the normal state of a run. It is not an empty state to fill."""
    plain = _run()
    assert insight.selected(plain) is None
    assert selected_insight(plain) == {}
    activity = build_activity(plain)
    assert activity.insight == "" and activity.insight_receipt_url == ""
    html = render_card(activity)
    assert "Selected insight" not in html
    assert 'class="insight"' not in html


def test_receipts_alone_are_not_an_insight():
    """A run can carry receipts and still have no line selected. One does not imply the other."""
    with_receipts = _run(receipts=[{"label": "PR 77", "url": RECEIPT}])
    assert insight.selected(with_receipts) is None
    assert "Selected insight" not in render_card(build_activity(with_receipts))


def test_no_parser_in_this_package_ever_writes_an_insight(tmp_path):
    """The field is the author's. Nothing reads it out of what somebody typed."""
    lines = ('{"role":"user","message":{"content":"<user_query>INSIGHT: this is the key '
             'takeaway of the whole session</user_query>"}}\n'
             '{"role":"assistant","message":{"content":[{"type":"text","text":'
             '"The insight here is that the cache was the bug."}]}}\n')
    folder = tmp_path / "proj" / "agent-transcripts" / "dddd"
    folder.mkdir(parents=True)
    transcript = folder / "t.jsonl"
    transcript.write_text(lines, encoding="utf-8")

    from agentgrinder.ingest import parse_cursor_session
    run = parse_cursor_session(str(transcript))
    assert "insight" not in run
    assert insight.selected(run) is None
    assert "the key takeaway" not in render_card(build_activity(run))

    source = open(__file__.rsplit("/tests/", 1)[0] + "/agentgrinder/ingest.py",
                  encoding="utf-8").read()
    assert '"insight"' not in source and "'insight'" not in source


# ---- bound, or not shown ------------------------------------------------------------------

def test_a_bound_insight_leads_the_code_route_group_with_its_receipt():
    run = _bound()
    chosen = insight.selected(run)
    assert chosen.text == LINE
    assert chosen.receipt_url == RECEIPT and chosen.receipt_label == "PR 77"
    html = render_card(build_activity(run))
    assert "Selected insight · bound to a receipt" in html
    assert LINE in html
    assert f'href="{RECEIPT}"' in html and ">PR 77</a>" in html
    assert "Not measured, and not taken from anything typed." in html
    # It sits at the head of the Code Route group: above the route, below the outcome.
    assert html.index('class="outcome') < html.index('class="insight"')
    assert html.index('class="insight"') < html.index('<div class="ridgewrap">')


def test_an_insight_bound_to_a_receipt_this_run_does_not_carry_is_refused():
    """The rule the card depends on. A line whose receipt is somewhere else is not evidence."""
    with pytest.raises(ValueError, match="one of this run's receipts"):
        selected_insight(_run(receipts=[{"label": "PR 72", "url": OTHER}],
                              insight={"text": LINE, "receipt": RECEIPT}))


def test_an_insight_with_no_receipts_at_all_is_refused():
    with pytest.raises(ValueError, match="one of this run's receipts"):
        selected_insight(_run(insight={"text": LINE, "receipt": RECEIPT}))
    with pytest.raises(ValueError):
        validate_run(_run(insight={"text": LINE, "receipt": RECEIPT}))


def test_a_malformed_or_unsafe_insight_is_refused_rather_than_softened():
    receipts = [{"label": "PR 77", "url": RECEIPT}]
    for bad in (
        {"text": LINE},                                        # no receipt
        {"receipt": RECEIPT},                                  # no line
        {"text": "", "receipt": RECEIPT},                      # empty line
        {"text": "x" * 121, "receipt": RECEIPT},               # not one line
        {"text": LINE, "receipt": "http://example.com/x"},     # not https
        {"text": LINE, "receipt": RECEIPT, "extra": "1"},      # unknown key
        [{"text": LINE, "receipt": RECEIPT}],                  # a list: one insight, not five
    ):
        with pytest.raises(ValueError):
            selected_insight(_run(receipts=receipts, insight=bad))
    with pytest.raises(ValueError, match="path"):
        selected_insight(_run(receipts=receipts,
                              insight={"text": "the fix was in /Users/morkeeth/code/app",
                                       "receipt": RECEIPT}))


# ---- a fleet is not a run -----------------------------------------------------------------

def _fleet(**over):
    return _bound(kind="fleet",
                  sessions=[{"label": f"s{i}"} for i in range(24)],
                  lanes=[{"repo": "a"} for _ in range(18)],
                  repos=[{"name": f"repo{i}"} for i in range(6)], **over)


def test_a_night_run_is_never_described_as_this_run():
    assert insight.scope_of(_run()) == "this run"
    assert insight.is_fleet(_fleet()) is True
    scope = insight.scope_of(_fleet())
    assert scope == "this night run — 24 sessions across 6 repositories"
    assert "this run" not in scope
    html = render_card(build_activity(_fleet()))
    assert "24 sessions across 6 repositories" in html
    assert "from this run and bound" not in html


# ---- signed out, 390 px, and honest about not being published ------------------------------

def test_the_card_needs_no_account_and_does_not_claim_to_be_published():
    html = render_card(build_activity(_bound()))
    assert insight.PRIVATE_NOTE in html
    for published in ("Public", "published to", "posted", "Feed"):
        assert published not in html.split('class="insight"')[1].split("</section>")[0]
    # Nothing in the insight block needs an account or a network call to render.
    block = html.split('class="insight"')[1].split("</section>")[0]
    assert "sign in" not in block.lower() and "<script" not in block
    assert block.count("http") == 1 and RECEIPT in block


def test_the_insight_survives_a_phone_width_card_without_a_fixed_grid():
    html = render_card(build_activity(_bound()))
    assert '<meta name="viewport" content="width=device-width,initial-scale=1">' in html
    block = html[html.index('class="insight"'):]
    assert "width:" not in block.split("</section>")[0]      # no fixed pixel width to overflow
    assert ".insight-line{margin:0 0 6px;font-size:16px" in html


# ---- the private draft path: selection is an explicit act --------------------------------

def test_a_private_draft_only_gains_an_insight_when_the_author_selects_one(tmp_path):
    composer = "eeeeeeee-3333-3333-3333-333333333333"
    hook.store_run(tmp_path, composer, _run())
    card = (tmp_path / "cards" / f"{composer}.html").read_text()
    assert "Selected insight" not in card

    with pytest.raises(ValueError):
        hook.apply_review(tmp_path, composer,
                          insight={"text": LINE, "receipt": RECEIPT})   # no receipt on the draft
    assert "Selected insight" not in (tmp_path / "cards" / f"{composer}.html").read_text()

    result = hook.apply_review(
        tmp_path, composer,
        outcome="The card leads with an outcome.",
        receipts=[{"label": "PR 77", "url": RECEIPT}],
        insight={"text": LINE, "receipt": RECEIPT})
    assert result["selected_insight"] == {"text": LINE, "receipt": RECEIPT}
    card = (tmp_path / "cards" / f"{composer}.html").read_text()
    assert LINE in card and "Selected insight" in card


def test_the_review_command_refuses_a_line_without_the_receipt_it_is_bound_to(tmp_path):
    composer = "ffffffff-4444-4444-4444-444444444444"
    hook.store_run(tmp_path, composer, _run())
    argv = [sys.executable, "-m", "agentgrinder", "hook", "review",
            "--composer-id", composer, "--directory", str(tmp_path), "--port", "0",
            "--insight", LINE]
    done = subprocess.run(argv, cwd=__file__.rsplit("/tests/", 1)[0],
                          capture_output=True, text=True)
    assert done.returncode == 1
    assert "travel together" in done.stderr


def test_an_insight_stays_local_and_never_travels_in_the_import_payload():
    """The hosted runs table has no column for it and this change ships no migration."""
    from agentgrinder.push import export_run
    payload = export_run(_bound())
    assert "insight" not in payload
    assert "receipts" in payload
    assert LINE not in json.dumps(payload)
