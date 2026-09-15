# The claim rule, calibrated (3 Sep 2026)

The card's honesty number counts CLAIMS and how many of them carried evidence. Until today the
detector that decides what a claim is had never been measured. This page is the label rubric, the
measurement, and the error bar. Every number here comes from a hand-labelled set of assistant
lines drawn from real agent transcripts on one machine. **No line of that text is reproduced here,
in the repository, or in any commit. Only counts leave.**

## 1. The rubric, written before the sample was opened

A **claim about work done** is a sentence the agent wrote that asserts, as accomplished fact, that
work in this session is finished, correct, or checked. The test a labeller applies is one question:

> Could a reader answer "prove it", and expect the proof to come from this session?

Three kinds count:

1. **Action completed.** The agent says it changed, created, removed, shipped or deployed something.
2. **Check outcome.** The agent says a test, build, lint, or run passed, failed, or was clean.
3. **Repaired state.** The agent says a named defect is now gone, or a named thing now works.

These do **not** count, and each one is a way the v0 rule went wrong:

- a **heading or a label** that happens to contain a completion word;
- a **plan, an intention, an offer, or an instruction** (I will run it, let us ship it, make sure it
  is green);
- a **question**, or a **condition** (if the suite passes, then ...);
- **quoted output**, an error message, a diff line, or code;
- a **description of how something behaves in general**, rather than an assertion about this
  session's work;
- someone **else's** words or work being reported.

A fourth label, **finding**, is recorded separately: a factual assertion about the state of the
system that the agent discovered this session but did not itself cause ("the config carries no
retry key"). Findings are not "work done", so they sit outside the headline class. They are counted
so the measurement can be re-read under the wider definition, and both readings are published below.

### Six examples, all synthetic

Written for this page, not taken from any transcript.

**Claims about work done**

- `Fixed the off-by-one in the date bucket, and the failing case passes now.`
- `Added the retry helper to the queue worker and the suite is green at 42 tests.`
- `Deployed the worker to staging; the health check answers 200.`

**Not claims**

- `## What is done` (a heading; the completion word is a label, not an assertion)
- `Next I will run the migration and check that it passes.` (a plan)
- `The retry helper works by doubling the delay after each failure.` (how a thing behaves, not what
  was done this session)

### Two boundaries the rubric did not settle, ruled during labelling

Recorded as amendments rather than folded back into the text above, because the text above was
committed before the sample was opened and the honest record is the order things happened in.

1. **A line ending in a colon that only counts or names what follows is a label, not a claim**
   ("Three actions done, all verified:"). A line that names the specific object it acted on and then
   introduces detail is a claim. The evidence for a summary line lives in the items under it, and
   counting both would count the same work twice.
2. **A fact about the outside world is not a finding.** The finding label covers assertions about the
   code, repository or environment the agent probed in this session. A researched fact about a
   deadline, a price or someone else's product is neither work done nor a finding, and is labelled
   as not a claim.

## 2. How the set was built

- Unit: one stripped, non-empty **line** of assistant text, exactly what the rule scores.
- Corpus: every transcript under 15 MB on one machine, across three harnesses, split into sittings
  by the product's own 30-minute idle rule; only sittings with at least one typed human turn.
- **Split first.** Every session file was assigned to `train` or `holdout` by a seeded hash of its
  name **before any line was read**. The holdout half was scored once, at the end, and never tuned on.
- **Three strata,** so recall is measurable and not just precision:
  - **A** the current rule fires;
  - **B** the rule does not fire but the line carries one of a broader list of 28 completion words
    fixed in advance (committed, commit, commits, pushed, merged, added, created, wrote, written,
    updated, implemented, removed, deleted, landed, confirmed, complete, completed, passing, ran,
    renamed, replaced, working, now, all tests, no errors, success, successful);
  - **C** everything else.
  Each stratum was crossed with harness. Population sizes per cell were recorded, so precision is a
  plain proportion inside A, and recall is a stratum-weighted (Horvitz-Thompson) estimate over the
  whole line population.
- Labelling was **blind**: the labeller saw the line and nothing else, no stratum, no rule verdict.
- **One labeller, one pass.** No second labeller and no re-label, so there is no inter-rater
  agreement number. On the hardest boundary, work done against finding, a second labeller would
  probably disagree on some lines, and that disagreement is not in the intervals below. The
  measurement asked for two labellers or one twice; it got one, once. Read the intervals as the
  sampling error only.

## 3. Results

396 lines were labelled: 198 in the tuning half, 198 in the held-out half. The rule was iterated on
the tuning half only. The held-out half was scored once, after the rule was frozen, and the number
below is that score, not a best-of.

Precision and recall are population-weighted (Horvitz-Thompson): each labelled line stands for the
lines in its cell, so these estimate what the rule does to a real transcript, where 78 percent of
lines carry no completion word at all. Intervals are 2.5 to 97.5 percentiles of 2,000 bootstrap
resamples inside cells. The counts they are computed from are in `docs/claim-calibration.json`, and
a test recomputes these figures from those counts.

### The held-out half, the number that counts

| rule | precision | recall | F1 |
|---|---|---|---|
| v0, one vocabulary regex over the line | **0.32** (0.18 to 0.50) | **0.37** (0.21 to 0.55) | 0.34 |
| this rule, sentence-level | **0.63** (0.43 to 0.83) | **0.66** (0.46 to 0.83) | 0.65 |

Unweighted, on the 198 held-out lines as sampled: the old rule fired on 76 lines, 29 right and 47
wrong. The new rule fires on 46, 34 right and 12 wrong, and misses 15.

On the tuning half the new rule reads precision 0.86 and recall 0.76. The gap between 0.86 there and
0.63 here is what tuning buys you and a held-out half takes back. **The target set for this work was
precision above 0.8 on the held-out half. It was not reached. 0.63 is the number.**

### The three harnesses under that one number

*Added 4 September 2026. The counts were always in `docs/claim-calibration.json`. Nobody had summed
them by harness, so nobody had noticed what the headline is a blend of.*

The corpus was stratified by harness as well as by session shape, and the three harnesses do not
agree. Reproduce this table with `python3 scripts/claim-calibration-report.py`.

| held-out, by harness | precision | recall | labelled | stands for |
|---|---|---|---|---|
| Claude Code | **0.72** (0.52 to 0.92) | **0.68** (0.49 to 0.87) | 114 | 35,033 lines, 62.9% |
| Codex | **0.86** (0.50 to 1.00) | **0.62** (0.25 to 1.00) | 44 | 1,221 lines, 2.2% |
| Cursor | not resolved, see below | not resolved | 40 | 19,403 lines, 34.9% |
| all three, the headline | **0.63** (0.43 to 0.83) | **0.66** (0.46 to 0.83) | 198 | 55,657 lines, 100% |

Two things fall out of that, and the second is the defect.

**The headline is not a general number and it is not a Claude Code number.** It describes one
machine's line population across three harnesses, blended by that corpus's own share of each. On
Claude Code alone the rule reads 0.72, which is higher than the published figure, not lower. A
reader on Claude Code is being told the rule is worse than it measures on their own transcripts.

**A third of the weight behind 0.63 rests on four predicted positives.** Precision is true
positives over predicted positives. Across the three held-out Cursor cells the rule predicted 4
positives in total: 1 true positive and 3 false positives, alongside 3 false negatives and 33 true
negatives, from 40 hand-labelled lines standing for 19,403. Bootstrapped, that precision runs from
0.00 to 0.86. There is no measurement there. A point estimate would be an absence wearing a
decimal point, so the table prints the counts and leaves the cell empty. Codex is thin too, at 7
predicted positives, but it carries 2.2 percent of the weight and cannot move the blend.

### The card never scores two of those three harnesses

*Found 4 September 2026, while writing the guard for the harness-parser slice. It is the more
serious of the two findings on this page and it supersedes the remedy the section above first
proposed.*

The claim rule runs in exactly two places in the shipped product, and both read Claude Code
transcripts only.

- `agentgrinder/ingest.py:74` builds a `ClaimTracker` inside `parse_session`, the Claude Code
  parser. `parse_cursor_session` and `parse_codex_session` never construct one and never call
  `assistant_text`. Their return dicts carry no `claims` key and no `claims_verified` key.
- `agentgrinder/solo.py:457` builds the other tracker, over events collected in `_scan`, and the
  only glob `solo.py` reads is `~/.claude/projects/*/*.jsonl`.

Checked against real transcripts on the author's machine on 4 September 2026, not read off the
code: 298 Cursor transcripts at the shipped `CURSOR_GLOB` and 81 Codex rollouts at the shipped
globs. The newest of each parses cleanly, returns turn and tool counts, and returns no claim count.
Rendered, a Cursor run prints a dash for verified per turn with a tooltip naming what it needs,
which is the gate behaving correctly.

**So the published figure is measured over a population 37.1 percent larger than the population it
is ever applied to.** The number that describes what this card does is the Claude Code row: 0.72
precision, 0.68 recall. 0.63 is the corpus-wide figure and it is the more conservative of the two.

**What this changes about the fix.** More hand-labelled Cursor lines would sharpen a stratum the
card does not score, so it is not the remedy. The remedy is to say which population the card scores,
which is what this section and the methodology page now do. Whether the headline should move to 0.72
with 0.63 kept as the corpus note is a ruling for the owner of the project, not a change to make
quietly, because it raises a published score.

**The seam is now held by a test.** `tests/test_claim_rule.py` asserts that the Cursor and Codex
parsers return no claim count and that the Claude Code parser does. Wire either harness into the
claim rule and the suite goes red, because at that moment the rule starts reading a population it
was never calibrated on. Labelling those strata becomes the fix on that day and not before.

**And the floor check is red until then.** `scripts/claim-calibration-report.py` exits non-zero when
a stratum carrying 10 percent or more of the population weight sits under 10 predicted positives.
Cursor sits at 4. The script names the stratum, the count and the weight, and it fails rather than
warning, because a correct sentence in a document has to be re-read by somebody and a check does
not.

### Said plainly

The old rule was wrong about two lines in every three it called a claim, and it missed nearly two
thirds of the real ones. The new rule is wrong about one in three and misses one in three. It is
roughly twice as good in both directions, and it is still not good enough to publish a per-line
verdict without a person reading it. The share it feeds is a measurement with a known error bar
rather than a regex with an unknown one, which is the whole difference between the two versions.

### What the rule still gets wrong

The 12 held-out false positives split two ways. Five are **findings**: a sentence stating something
true the agent discovered about the system, which the rubric excludes because it is not work done.
That is the hardest boundary in the label set. Seven are **not claims at all**, and seven of the
twelve begin with a bold marker rather than a hash: a heading or a label written as `**LIKE THIS**`
is invisible to a rule that only refuses `#`. That is the cheapest remaining fix and it is named
here rather than made, because the rule is frozen at the numbers above.

The 15 false negatives are mostly claims folded into a heading or a label, or into a line ending in
a colon, which the rule refuses on purpose. Refusing them is what bought the precision.

## 4. The verbosity coupling

The research lane measured that the v0 claim COUNT correlates 0.86 with how many messages the agent
writes: a chattier agent scored higher on the same work. Fixing the detector does not fix that, and
here is the measurement, over 308 held-out sittings, against assistant output tokens:

| quantity | correlation with assistant tokens |
|---|---|
| claim count, v0 rule | +0.81 |
| claim count, this rule | +0.80 |
| verified claim count, this rule | +0.65 |
| distinct verified artefacts, this rule | +0.56 |
| **verified per turn (the card headline)** | **+0.32** |
| **verified share of claims (honesty)** | **+0.20** |

**A count of claims cannot be a headline, whatever rule produces it.** Counting distinct verified
artefacts instead, the fix proposed before the measurement, does not solve it either: +0.56 is still
mostly verbosity. Only the two RATIOS fall away, because the agent's talkativeness sits in the
numerator and the denominator and divides out. The card's headline is a rate already, and it reads
+0.32 held-out, so it does not need the denominator changed. The honesty share, at +0.20, is the
cleanest number in the set and is the one this rule exists to make trustworthy.

## 5. What is still unmeasured, stated

`evidence_matches`, which decides whether a claim carried evidence, has **no label set**. A generic
"N passed" in the same turn still verifies any claim beside it. The claim COUNT now has a measured
error rate; the verified SHARE inherits an unmeasured one on top of it. That is the next label set,
and until it exists the share should be read as an estimate with one measured half.

Rule digest at the time of measurement: `e49d8713c3c2df38` (`agentgrinder.claims.rule_fingerprint`).
Measured 3 September 2026.
