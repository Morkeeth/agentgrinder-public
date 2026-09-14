"""The claim rule, pinned by fixtures and by its own published error rate.

Three things are held here, and the third is the point:

1. the rule behaves as the rubric says, on SYNTHETIC lines written for this file;
2. the precision and recall printed in the docs are the numbers that fall out of the counts
   committed beside them, so a figure cannot drift away from its evidence;
3. the rule's own text is digested, and the digest is stored with those numbers. Edit the rule and
   this suite goes red until the calibration is redone. A measured claim about an instrument stops
   being true the moment somebody edits the instrument.

No line from any real transcript appears in this repository. The label set is local to the machine
it was drawn on.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentgrinder.claims import claims_in, is_claim_line, rule_fingerprint

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(REPO, "docs", "claim-calibration.json")
DOC = os.path.join(REPO, "docs", "CLAIM-RULE-CALIBRATION-2026-09-03.md")
PAGE = os.path.join(REPO, "site", "methodology.html")

# ---- 1. the rubric, as fixtures. Every line below was written for this test. ----------------

CLAIMS = [
    "Fixed the off-by-one in the date bucket, and the failing case passes now.",   # repaired state
    "Added the retry helper to the queue worker and the suite is green at 42 tests.",  # action done
    "Deployed the worker to staging; the health check answers 200.",               # action done
    "I re-ran the suite after the rename and 128 tests passed.",                   # check outcome
    "- Lint: passed",                                                             # check outcome
    "Pushed to the release branch at 1a2b3c4.",                                   # action done
]

NOT_CLAIMS = [
    "## What is done",                                    # a heading carrying a completion word
    "| status | done |",                                  # a table row
    "Two things I fixed tonight:",                        # a label that introduces a list
    "Should I mark the migration as done?",               # a question
    "Next I will run the migration and check that it passes.",   # a plan
    "If the suite passes, we ship it tomorrow.",          # a condition
    "Make sure the build is green before you tag it.",    # advice
    "> the suite passed on their machine",                # quoted, and someone else's run
    "The retry helper works by doubling the delay after each failure.",  # how a thing behaves
]


def test_every_rubric_claim_is_read_as_one():
    missed = [s for s in CLAIMS if not is_claim_line(s)]
    assert missed == [], f"the rule no longer reads these as claims: {missed}"


def test_no_rubric_non_claim_is_read_as_a_claim():
    wrong = [s for s in NOT_CLAIMS if is_claim_line(s)]
    assert wrong == [], f"the rule now reads these as claims: {wrong}"


def test_claims_in_keeps_the_line_and_its_tokens():
    cl = claims_in("Fixed tests/test_bucket.py; test_edges passes.\njust thinking out loud\n")
    assert len(cl) == 1
    assert "tests/test_bucket.py" in cl[0].tokens and "test_edges" in cl[0].tokens


# ---- 2. the published figures are recomputed from the committed counts ----------------------

def _weighted(cells, split):
    """Horvitz-Thompson precision and recall: every labelled line stands for its whole cell."""
    tp = fp = fn = 0.0
    for key, c in cells.items():
        if not key.startswith(split + "|"):
            continue
        w = c["pop"] / c["n"]
        tp += w * c["tp"]
        fp += w * c["fp"]
        fn += w * c["fn"]
    return tp / (tp + fp), tp / (tp + fn)


def test_the_docs_print_the_precision_the_counts_produce():
    cal = json.load(open(CAL))
    p_new, r_new = _weighted(cal["cells"]["shipped"], "holdout")
    p_old, r_old = _weighted(cal["cells"]["v0"], "holdout")
    assert round(p_new, 2) == 0.63 and round(r_new, 2) == 0.66
    assert round(p_old, 2) == 0.32 and round(r_old, 2) == 0.37
    surfaces = ((DOC, "the calibration write-up"), (PAGE, "the methodology page"),
                (os.path.join(REPO, "agentgrinder", "claims.py"), "the module docstring"),
                (os.path.join(REPO, "docs", "TECHNICAL-HISTORY.md"), "the inherited technical reference"))
    for path, where in surfaces:
        text = open(path).read()
        for n in ("0.63", "0.66", "0.32", "0.37"):
            assert n in text, f"{where} no longer prints {n}"


def test_the_held_out_half_is_the_one_reported():
    cal = json.load(open(CAL))
    held = {k: c for k, c in cal["cells"]["shipped"].items() if k.startswith("holdout|")}
    assert sum(c["n"] for c in held.values()) == 198
    assert cal["labelled_lines"] == 396
    assert sum(c["n"] for c in cal["cells"]["shipped"].values()) == 396


# ---- 3. the rule cannot move without the numbers moving -------------------------------------

def test_the_rule_matches_the_calibration_it_publishes():
    cal = json.load(open(CAL))
    assert cal["rule_fingerprint"] == rule_fingerprint(), (
        "the claim rule changed since it was calibrated. Re-run the calibration on the labelled "
        "set, update docs/claim-calibration.json and the two pages that print its numbers, then "
        "store the new fingerprint. A published precision belongs to one exact rule.")


def test_the_docs_carry_the_same_fingerprint():
    fp = json.load(open(CAL))["rule_fingerprint"]
    assert re.fullmatch(r"[0-9a-f]{16}", fp)
    assert fp in open(DOC).read() and fp in open(PAGE).read()


# ---- 4. the strata under the headline, and the check that goes red on its own ---------------
#
# The headline blends three harnesses by their share of one machine's corpus. A blend can be
# honestly computed and still hide a stratum nobody measured. These tests hold the per-harness
# figures on the public surfaces, and they hold the floor check in both states: red on the counts
# committed today, green on a set where the thin stratum has been labelled.

sys.path.insert(0, os.path.join(REPO, "scripts"))
import importlib.util as _ilu

_spec = _ilu.spec_from_file_location(
    "claim_calibration_report", os.path.join(REPO, "scripts", "claim-calibration-report.py"))
calreport = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(calreport)


def _harness_row(rule, harness):
    cal = json.load(open(CAL))
    cells = calreport._cells(cal, rule, "holdout", harness)
    return calreport._estimate(cells, calreport._as_labelled), cells


def test_the_per_harness_figures_are_what_the_counts_produce():
    """Claude Code alone reads higher than the headline. That is the point of publishing it."""
    (p_claude, r_claude), _ = _harness_row("shipped", "claude")
    (p_codex, r_codex), _ = _harness_row("shipped", "codex")
    assert round(p_claude, 2) == 0.72 and round(r_claude, 2) == 0.68
    assert round(p_codex, 2) == 0.86 and round(r_codex, 2) == 0.62
    # the headline sits BELOW the harness carrying most of the weight, because a thin, heavily
    # weighted cursor stratum drags the blend down. If this ever flips, the sentence on the
    # methodology page saying so has become false.
    cal = json.load(open(CAL))
    p_all, _ = _weighted(cal["cells"]["shipped"], "holdout")
    assert p_all < p_claude


def test_the_two_pages_print_the_measured_per_harness_figures():
    for path, where in ((DOC, "the calibration write-up"), (PAGE, "the methodology page")):
        text = open(path).read()
        for n in ("0.72", "0.68", "0.86"):
            assert n in text, f"{where} no longer prints the per-harness figure {n}"


def test_neither_page_prints_a_cursor_precision():
    """A point estimate off four predicted positives is the absence of a measurement.

    The counts go on the page. The number 0.33 does not. This test is the guard on that ruling,
    because the tempting edit is to fill the empty cell with the value the script computes.
    """
    (p_cursor, _), cells = _harness_row("shipped", "cursor")
    assert round(p_cursor, 2) == 0.33          # the script still computes it
    tp = sum(c["tp"] for c in cells.values())
    fp = sum(c["fp"] for c in cells.values())
    assert tp + fp == 4                         # off this many predicted positives
    for path, where in ((DOC, "the calibration write-up"), (PAGE, "the methodology page")):
        text = open(path).read()
        assert "0.33" not in text, (
            f"{where} prints 0.33 as a cursor precision. It rests on {tp + fp} predicted "
            "positives and its interval runs 0.00 to 0.86. Print the counts instead.")
        assert "19,403" in text or "19403" in text, (
            f"{where} no longer names the cursor population the thin stratum stands for")


def test_the_floor_check_is_red_on_the_counts_we_publish():
    """Watched going red. The cursor stratum carries 34.9 percent of the weight on 4 positives."""
    out = calreport.report(draws=1)
    unreportable, fatal = calreport.audit(out)
    assert [e["harness"] for e in fatal] == ["cursor"]
    assert fatal[0]["predicted_positives"] == 4
    assert fatal[0]["weight"] > calreport.FLOOR_WEIGHT
    assert "codex" in [e["harness"] for e in unreportable]   # thin, but too light to be fatal
    assert calreport.main(["--json", "--draws", "1"]) == 1


def test_the_floor_check_goes_green_when_the_thin_stratum_is_labelled():
    """Watched going green. A check nobody has seen pass is as untrustworthy as one nobody has
    seen fail, so the same audit runs over a synthetic set where cursor has been hand-labelled."""
    cal = json.load(open(CAL))
    patched = json.loads(json.dumps(cal))
    for key, cell in patched["cells"]["shipped"].items():
        if key.startswith("holdout|") and key.endswith("|cursor"):
            cell.update(tp=12, fp=4, fn=3, tn=60, n=79)
    out = calreport.report(cal=patched, draws=1)
    unreportable, fatal = calreport.audit(out)
    assert fatal == []
    assert [e["harness"] for e in unreportable] == ["codex"]


def test_the_script_reproduces_the_published_headline_interval():
    """The published 0.43 to 0.83 came from a script that was never committed. This one is, and
    it lands within 0.01 of it, which is what a different bootstrap seed costs."""
    out = calreport.report(draws=2000)
    row = out["rules"]["shipped"]["all"]
    assert abs(row["precision_lo"] - 0.43) <= 0.02 and abs(row["precision_hi"] - 0.83) <= 0.02
    assert abs(row["recall_lo"] - 0.46) <= 0.02 and abs(row["recall_hi"] - 0.83) <= 0.02


# ---- 5. the seam: which harnesses the rule is actually applied to ---------------------------
#
# The published precision is a blend over three harnesses. The shipped card runs the rule on one.
# That gap is the defect this section pins, and the pin is deliberately shaped so that CLOSING the
# gap breaks it: wire Cursor or Codex into the claim rule and these tests go red, because at that
# moment the rule starts reading a population it was never calibrated on. The right response to a
# red here is to recalibrate and republish, not to edit the assertion.

from agentgrinder import ingest, solo   # noqa: E402


def test_only_the_claude_parser_feeds_the_claim_rule():
    import inspect
    claude = inspect.getsource(ingest.parse_session)
    assert "ClaimTracker" in claude or "tracker.assistant_text" in claude, (
        "the Claude Code parser no longer feeds the claim rule")
    for fn in (ingest.parse_cursor_session, ingest.parse_codex_session):
        src = inspect.getsource(fn)
        assert "assistant_text" not in src and "ClaimTracker" not in src, (
            f"{fn.__name__} now feeds the claim rule. The published precision and recall were "
            "measured over a line population produced by the parsers as they stood on 3 Sep 2026. "
            "Feeding a new harness in changes that population while the numbers stay still. "
            "Recalibrate on the labelled set, update docs/claim-calibration.json and the pages "
            "that print it, then update this test. Do not simply delete the assertion.")


def test_the_other_claim_path_reads_claude_transcripts_only():
    import inspect
    src = inspect.getsource(solo)
    assert "~/.claude/projects/*/*.jsonl" in src
    for other in ("~/.cursor/", "~/.codex/"):
        assert other not in src, (
            f"solo.py now reads {other}. It builds the second ClaimTracker, so this widens the "
            "population under the published precision. See the note above.")


def test_the_two_non_claude_parsers_return_no_claim_count():
    """Asserted against real transcripts when the machine has them, and against the source when it
    does not, so this is never quietly skipped into a pass."""
    import glob
    checked = 0
    for fn, pattern in ((ingest.parse_cursor_session, ingest.CURSOR_GLOB),
                        (ingest.parse_codex_session, ingest.CODEX_GLOBS[0])):
        files = sorted(glob.glob(os.path.expanduser(pattern), recursive=True),
                       key=os.path.getmtime, reverse=True)
        for path in files[:20]:
            try:
                parsed = fn(path)
            except Exception:
                continue
            assert "claims" not in parsed and "claims_verified" not in parsed, (
                f"{fn.__name__} returned a claim count for {os.path.basename(path)}")
            checked += 1
            break
    # `assert checked >= 0` sat here first, which is a line that cannot fail: a check nobody has
    # seen go red, under a docstring promising it never quietly passes. A machine with no Cursor
    # and no Codex transcripts skips instead, out loud.
    if checked < 2:
        import pytest
        pytest.skip(f"only {checked} of the two harnesses have a transcript on this machine; "
                    "the source-level assertion in the test above still holds")
