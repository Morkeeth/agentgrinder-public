"""Capture > preview > deliberate post: recovery, no duplicate, honest exact-reply target.

String contracts on the committed shell. The browser proof is scripts/check-post-recovery.py.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()
SOCIAL = (ROOT / "site" / "social.js").read_text()
SOCIAL_CSS = (ROOT / "site" / "social.css").read_text()
PUSH = (ROOT / "agentgrinder" / "push.py").read_text()
WALK = (ROOT / "scripts" / "check-post-recovery.py").read_text()
IMPORT = INDEX[INDEX.index("function importRun(){") : INDEX.index("async function viewShareRun(")]


def test_failed_save_keeps_the_draft_and_offers_an_explicit_retry():
    assert 'id="i_recover"' in IMPORT
    assert "Nothing was posted by this attempt." in IMPORT
    assert 'id="i_retry"' in IMPORT and "Try again" in IMPORT
    assert 'href="/?mine">Your runs' in IMPORT
    # no timer or loop re-sends the insert; the only retry is the person's click
    assert "setTimeout" not in IMPORT and "setInterval" not in IMPORT
    assert "Check Your runs before retrying" not in IMPORT


def test_same_capture_is_one_run_not_two():
    assert "const dedupe=run.measurement_revision?{measurement_revision:run.measurement_revision}" in IMPORT
    assert "started_at:run.started,harness:run.harness" in IMPORT
    assert "async function existingRun()" in IMPORT
    assert "prior=await existingRun()" in IMPORT
    assert "error.code==='23505'" in IMPORT
    assert "already saved as a run" in IMPORT and "was not applied" in IMPORT


def test_a_failed_rig_update_never_reads_as_a_failed_save():
    saved = IMPORT[IMPORT.index("let {data:published,error}=await sb.from('runs').insert") :]
    assert "The run is saved from here on" in saved
    assert "were not updated; edit them from your profile" in saved


def test_the_preview_names_what_the_export_carries_and_matches_the_allowlist():
    assert 'class="hint export-contents"' in IMPORT
    assert "the project folder name, counts, timing, the activity trace and route as numbers" in IMPORT
    assert "one sentence about reach" in IMPORT and "the stack notes you wrote" in IMPORT
    assert "It never carries prompts, code or file paths." in IMPORT
    assert "MCP names travel only if you tick the box below." in IMPORT
    assert "saved to your profile even when the run is Only me" in IMPORT
    # the words are pinned to the exporter's allowlist: if a new field starts travelling, this
    # test must be revisited with the copy
    keys = set(re.findall(r'^\s+"([a-z_]+)":', PUSH, re.M))
    assert keys == {
        "harness", "is_sample", "activity_label", "project", "turns_typed", "duration_s", "tool_calls",
        "files_touched", "commits", "claims", "claims_verified", "artifacts_produced", "reach",
        "reach_reason", "coach_verdict", "coach_plan", "coach_tool_calls", "coach_mode",
        "coach_experiment", "progress_verdict", "progress_delta", "started", "rhythm", "route",
        "trace_basis", "rig_mcps", "rig_skills", "rig_share_names", "rig_mcp_names", "rig_notes",
    }, keys
    assert "No prompt text, no paths" in PUSH


def test_a_chopped_import_link_is_named_not_swallowed():
    assert "This import link is incomplete" in IMPORT
    assert "catch(_){ return false; }" not in IMPORT


def test_the_dead_retry_promise_is_gone():
    assert "the insert is retried" not in IMPORT and "const unsaved=''" not in IMPORT


def test_exact_reply_past_the_paging_cap_is_rendered_directly_not_called_removed():
    thread = SOCIAL[SOCIAL.index("async function thread(") : SOCIAL.index("async function inbox(")]
    assert "function renderReply(reply)" in thread
    assert "if (!focusKnownMissing) focusedRow = focused[0];" in thread
    assert "if (focusReply && !sawFocus && focusedRow)" in thread
    assert 'direct.className = "reply-direct"' in thread
    assert "shown here on its own" in thread
    assert "That reply was removed or is not visible to you." in thread
    assert ".reply-direct{" in SOCIAL_CSS


def test_the_browser_walk_covers_the_journey():
    for needle in (
        'route.abort("connectionfailed")',
        "no automatic retry fired",
        "lost response: Try again found the saved run by start time and harness",
        "re-save: opens the existing run",
        "This import link is incomplete",
        "cap: the exact reply past the 12-page load is rendered directly",
        "missing reply: named as removed or not visible",
    ):
        assert needle in WALK, needle
