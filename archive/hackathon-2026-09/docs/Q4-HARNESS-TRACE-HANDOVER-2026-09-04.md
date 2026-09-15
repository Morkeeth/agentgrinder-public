# Q4, the harness parsers: what landed, and the blocker nobody had named

*4 September 2026. Branch `lane/claim-rule-population-2026-09-04`. Written because Q4's done-when
is NOT met and the reason is a contract, not an afternoon of typing.*

Q4's done-when, from the build plan: **a Cursor-only and a Codex-only machine each produce a full
card with a trace.** Half of that is done. The other half is blocked on a decision, and the block
is not where the plan assumed it was.

## What landed

Cursor and Codex now read their own file writes, commits, artifacts and repository. Before today
all four printed a dash, with a tooltip that blamed the harness. Both tooltips were false at the
object.

| | Cursor | Codex |
|---|---|---|
| file writes | `Write` and `StrReplace` tool_use, absolute `path` | `patch_apply_end.changes`, keyed by absolute path, `success` gated |
| commits | `Shell` input `command` containing `git commit` | `custom_tool_call` name `exec`, command joined then searched |
| repository | the git work tree enclosing the most-edited path | `session_meta.cwd` |
| window | typed turns only, so edits have no time of their own | every record carries an ISO timestamp |

Measured on the author's machine, 4 Sep 2026: 298 Cursor transcripts holding 2,279 edit blocks,
every path absolute, 2,233 still on disk, 119 shell commands containing `git commit`. 81 Codex
rollouts across both shipped globs.

Both harnesses still render the v1 card. Neither carries the grind trace, and neither carries the
verified-per-turn headline.

## Why verified per turn stays a dash, and must

Filling it means running the claim rule on these transcripts. The published precision of 0.63 was
measured over the line population the parsers produced *before* today. Feeding a new harness in
moves that population while the number sits still, and the suite would stay green through it.
`tests/test_claim_rule.py` holds that seam and goes red the day either parser feeds the rule. The
sequence is: recalibrate on a labelled set for that harness, republish, then wire it. Not the
other way round.

## The blocker: both trace cards ask for an authorship breakdown only Claude Code can supply

This is the finding. It was not in the plan and it changes the size of the remainder.

`solocard.render_solo_card` does not take a bag of numbers. It takes the `parse_solo` run shape,
and two of its asserts are load-bearing honesty rather than plumbing:

```python
assert sum(cats.values()) == naive          # the five categories sum to the raw type:"user" total
assert cats["human"] == run["turns_typed"]  # and the human category IS the denominator
```

**The same two asserts sit in `fleetcard.py:47` and `:48`, not only `solocard.py:177` and `:178`.**
The constraint is on two renderers, so anyone following this file to teach a second harness to
render would meet the second pair the hard way.

The fleet card's own comment explains why they are there better than anything else in this
document, and it was written before today:

> five DISJOINT categories that must add up to the raw total they are correcting. The version this
> replaced printed "tool results, injected context, and the 1,357 lane briefs" as three things,
> when the third was 1,324 of the first. It called harness-written tool output human-authored
> briefs, inside the paragraph whose whole job is to prove the card does not inflate a count.
> Categories that must sum cannot drift like that.

That is this run's entire subject, sitting in the repository as a comment: a number that was
correct about the wrong object, inside the sentence whose job was to prove it was not.

`authorship.classify` produces those categories, and its first line is
`if rec.get("type") != "user": return None`. It then reads `isMeta`, `isSidechain` and a tool
result shape. Every one of those is a Claude Code field. A Codex record is
`{"type": "event_msg", "payload": {"type": "user_message"}}`, so `classify` returns `None` for all
of them and the breakdown does not exist.

So the Codex trace needs one of two things, and only the first is honest:

1. **A Codex authorship classifier** with its own categories, disjoint, summing to the raw count of
   whatever Codex's equivalent of a `type:"user"` record is. Codex ships a real signal for this:
   `event_msg`/`user_message` with the `<recommended_plugins>`, `<environment_context>` and
   `<turn_aborted>` markers already listed in `ingest._INJECT_MARKERS`. This is a day, and it is
   the same shape of work `authorship.py` was for Claude Code.
2. Loosening the two asserts, in either renderer. **Do not.** They are the reason the card's
   correction can be checked by the person reading it, and the comment quoted above is what the
   card looked like before they existed.

The rest of the Codex trace is comparatively cheap once 1 exists: `patch_apply_end` gives per-file
edits with timestamps, `session_meta.cwd` gives the repository, and `gitwork` supplies the commits
and their files exactly as it does for Claude Code.

## The Cursor trace is a product decision, not work

Cursor stamps a time on typed turns only. An edit has no time of its own, so the trace can be
drawn coarse, bucketing edits between the two typed turns that bracket them, or not drawn at all.

Every mark on the grind trace is supposed to BE a timestamp. A bucketed mark is an invented
position for a real event, which is the card asserting something it does not know, in the one
drawing whose whole claim is that it does. **Recommendation: do not draw it, and print the reason
on the card.** Routed to the project owner as R6.

## The order

1. R6 answered: Cursor trace, coarse or absent.
2. R5 answered: whether the published precision headline moves from 0.63 to 0.72. Independent of
   this file, but it gates any change to what the claim rule publishes.
3. Codex authorship classifier, with its categories summing and a test that the sum is printed.
4. Codex trace, on top of 3.
5. Cursor claim scoring and Codex claim scoring, each only after that harness has a labelled set
   and a republished figure. The seam guard goes red first, on purpose.
