#!/usr/bin/env python3
"""Which of the three evidence rules is actually carrying the verified share?

The card's honesty number has two halves and only one of them has ever been measured.

  DENOMINATOR: what counts as a claim. `is_claim_line`, measured 3 Sep 2026, precision 0.63 and
  recall 0.66 on a held-out hand-labelled half. See archive/hackathon-2026-09/docs/CLAIM-RULE-CALIBRATION-2026-09-03.md.

  NUMERATOR: whether a claim was matched to the RIGHT evidence. `evidence_matches`. No label set,
  no measurement, and the module docstring and the card tooltip both say so in words.

This script does not measure whether the numerator is correct, because that needs labelling. It
measures something cheaper that nobody had counted: WHICH BRANCH of `evidence_matches` fires. That
is a property of the code path, not a judgement, so it can be read straight off the corpus.

The two branches are not equally strong.

  TOKEN     a test name or a file path NAMED IN THE CLAIM LINE appears in a tool result from the
            same human turn. The evidence points at the thing the claim was about.
  GENERIC   the result carries "N passed", a line starting "OK", or "exit 0", and does not carry
            "N failed", "FAILED" or "Traceback". Nothing connects it to the claim. One passing
            suite in a turn verifies every claim beside it, whatever they were about.

A claim is counted as GENERIC-ONLY when no result in its turn matched by token. If any result
matched by token, it is TOKEN, because the stronger evidence existed.

    python3 scripts/evidence-branch-report.py                 # the table
    python3 scripts/evidence-branch-report.py --json          # the same numbers, machine readable
    python3 scripts/evidence-branch-report.py --limit 200     # cap the transcripts read

READS ONLY, AND NOTHING LEAVES. It walks the Claude Code transcripts already on this machine, the
only harness the claim rule is applied to, and prints counts. No line of any transcript is
printed, stored or returned.
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentgrinder.claims import (ClaimTracker, _GENERIC_BAD, _GENERIC_OK, claims_in, evidence_kind,
                                 is_tool_result, result_text)
from agentgrinder.authorship import is_human_turn
from agentgrinder.ingest import CLAUDE_GLOB


def branch_of(claim, results):
    """Report which production evidence arm matched. The matcher owns the rule.

    The independent labelled evaluation belongs in tests/test_evidence_scope.py; this
    report measures current branch usage, not accuracy and not the historical split.
    """
    kinds = {evidence_kind(claim, text) for text in results}
    return "token" if "token" in kinds else "generic" if "generic" in kinds else None


class BranchTracker(ClaimTracker):
    """The shipped tracker, with a tally of which arm verified each claim.

    Subclassed rather than edited: `claims.py` is fingerprinted against the published precision
    and recall, so measuring it must not touch it.
    """

    def __init__(self):
        super().__init__()
        self.by_branch = {"token": 0, "generic": 0}
        self.claims_with_tokens = 0

    def _close(self):
        for c in self._turn_claims:
            arm = branch_of(c, self._turn_results)
            c.verified = arm is not None
            self.claims += 1
            self.verified += int(c.verified)
            if c.tokens:
                self.claims_with_tokens += 1
            if arm:
                self.by_branch[arm] += 1
        self._turn_claims = []
        self._turn_results = []


def scan(path, tracker):
    """One transcript through the tracker, same order and same gate as ingest.parse_session."""
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if is_human_turn(o):
                tracker.typed_turn()
            elif is_tool_result(o):
                tracker.tool_result(result_text(o))
            elif o.get("type") == "assistant":
                msg = o.get("message") if isinstance(o.get("message"), dict) else {}
                c = msg.get("content")
                if isinstance(c, list):
                    tracker.assistant_text("\n".join(
                        b.get("text", "") for b in c
                        if isinstance(b, dict) and b.get("type") == "text"))
                elif isinstance(c, str):
                    tracker.assistant_text(c)


def measure(limit=None, max_bytes=15 * 1024 * 1024):
    files = sorted(glob.glob(os.path.expanduser(CLAUDE_GLOB)), key=os.path.getmtime, reverse=True)
    files = [f for f in files if os.path.getsize(f) <= max_bytes]
    if limit:
        files = files[:limit]
    t = BranchTracker()
    read = 0
    for f in files:
        try:
            scan(f, t)
            read += 1
        except OSError:
            continue
    t.close()
    tok, gen = t.by_branch["token"], t.by_branch["generic"]
    return {
        "transcripts_read": read,
        "transcripts_available": len(files),
        "claims": t.claims,
        "verified": t.verified,
        "verified_by_token": tok,
        "verified_by_generic_only": gen,
        "generic_share_of_verified": (gen / t.verified) if t.verified else None,
        "claims_naming_a_token": t.claims_with_tokens,
        "verified_share_of_claims": (t.verified / t.claims) if t.claims else None,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="read at most this many transcripts")
    a = ap.parse_args(argv)
    m = measure(limit=a.limit)
    if a.json:
        print(json.dumps(m, indent=2, sort_keys=True))
        return 0
    if not m["claims"]:
        print("\n  no claims found in any transcript on this machine, so there is nothing to "
              "split.\n  This measurement needs Claude Code sessions to read.\n")
        return 0
    gs = m["generic_share_of_verified"]
    print(f"\n  {m['transcripts_read']:,} Claude Code transcripts, "
          f"{m['claims']:,} claims, {m['verified']:,} verified "
          f"({100 * m['verified_share_of_claims']:.1f}% of claims)\n")
    print(f"  {'branch':<34} {'claims':>8}  {'share of verified':>18}")
    print(f"  {'-' * 34} {'-' * 8}  {'-' * 18}")
    print(f"  {'TOKEN, evidence names the claim':<34} {m['verified_by_token']:>8,}  "
          f"{100 * (1 - gs):>17.1f}%")
    print(f"  {'GENERIC only, a passing token':<34} {m['verified_by_generic_only']:>8,}  "
          f"{100 * gs:>17.1f}%")
    print(f"\n  {m['claims_naming_a_token']:,} of {m['claims']:,} claims "
          f"({100 * m['claims_naming_a_token'] / m['claims']:.1f}%) name a test or a file at all, "
          f"which is\n  the ceiling on how many could ever be verified by the stronger rule.\n")
    print("  READ THIS AS: what share of the verified count rests on the weakest of the two\n"
          "  rules, where nothing connects the evidence to the claim. It is NOT a measurement\n"
          "  that those verifications are wrong. Whether a claim was matched to the RIGHT\n"
          "  evidence has no label set, and this number is the size of the question, not its\n"
          "  answer.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
