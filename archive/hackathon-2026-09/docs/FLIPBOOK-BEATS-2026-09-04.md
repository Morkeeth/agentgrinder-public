# Flipbook beats: Agent Grinder

*Content for T5's flipbook. Beats only, no render. 4 September 2026, against `main` at `d5ce38e`.*

**Every number here carries the command or file that produced it.** A reel about a product whose
argument is that a number without a source is a guess cannot itself carry an unsourced number, and
that constraint is the reason this spine works: each beat is a number and its receipt.

**The spine, in one line:** a product that measures honesty found out its own honesty number was
half-measured, published the half that was missing, and left the check red.

---

### Beat 1. The field is lying to you, and here is the count

**On screen:** `type: "user"` records against how many a person typed.
**Number:** 34,032 records marked `type: "user"`, **966 typed by a person, 2.8%**, over 14 days.
Narrower windows on the same machine: 3,291 / 80 / 2.4% over 24 hours, 58 / 4 / 6.9% over one hour.
**Source:** `python3 -m agentgrinder authorship --hours 336`, `--hours 24`, `--hours 1`, 4 Sep 2026,
after the window fix below.
**The point:** three readings, not one. The share moves a little with the window and the gap does
not move at all. Use all three: one flattering number would be the thing this reel is against.
**READ THIS BEFORE RENDERING.** The earlier version of this beat quoted 334 / 12 / 3.6%, and that
figure is NOT REPRODUCIBLE and never was. `authorship` reused the night-run collector, which
narrows any window to the last contiguous burst of activity, so every reading described whatever
burst happened to be last at the moment it ran, while the command printed a span beside it. Three
readings that looked like three windows were three bursts. Fixed 4 Sep 2026; the numbers above are
the first ones taken over windows anyone actually asked for. If a reel had rendered the old beat it
would have shown an irreproducible number as the opening evidence.

### Beat 2. So the tool counts what a person typed, and prints the sum

**On screen:** five disjoint categories adding to the raw total.
**Number:** `4 + 85 + 6 + 0 + 0 = 95`.
**Source:** `authorship.py`, `CATEGORIES`. The card prints the sum so a reader can check the
correction rather than trust it.

### Beat 3. One command, no account, nothing uploaded

**On screen:** clone, run, card.
**Number:** 1.18 s clone, 16 MB, 143 files, 0.64 s to a card on an empty machine, zero non-standard-library imports.
**Source:** `docs/STRANGER-AUDIT-2026-09-04.md`, cold clone under `env -i`, machine named in the file.
**The point:** the "no dependencies" claim is measured, not asserted.

### Beat 4. The headline is a rate because a count tracks talking

**On screen:** claim count against assistant output tokens.
**Number:** +0.80 for a claim count. +0.56 for distinct verified artefacts. **+0.32** for verified
per turn.
**Source:** `docs/claim-calibration.json`, `verbosity`, 308 held-out sittings.
**The point:** talkativeness sits in both halves of a ratio and divides out. That is why the
headline is a rate.

### Beat 5. The rule that decides what a claim is had never been measured

**On screen:** the old rule against the new one.
**Number:** 0.32 / 0.37 becomes **0.63 / 0.66**. Target was 0.8. **Not reached.**
**Source:** `docs/CLAIM-RULE-CALIBRATION-2026-09-03.md`, 396 hand-labelled lines, rubric written
before the sample was opened, held-out half scored once.
**The point:** the miss is on screen. A target hit is a press release; a target missed and
published is the product.

### Beat 6. That number was a blend, and one third of it was never scored

**On screen:** the per-harness table, with the Cursor cell empty.
**Number:** Claude Code **0.72**, Codex **0.86**, Cursor **not resolved**: 4 predicted positives
across 40 labelled lines standing for 19,403, interval 0.00 to 0.86.
**Source:** `python3 scripts/claim-calibration-report.py`.
**The point:** the empty cell is the beat. A number could go there. It would be an absence wearing
a decimal point.

### Beat 7. And the headline is lower than the harness it actually scores

**On screen:** 0.63 sitting under 0.72.
**Number:** 62.9% of the weight is Claude Code, 34.9% Cursor, 2.2% Codex, and the card runs the
rule on Claude Code only.
**Source:** `ingest.parse_session` builds the tracker; `parse_cursor_session` and
`parse_codex_session` do not; `solo.py` reads `~/.claude/projects` only.
**The point:** the conservative number stays the headline. Raising your own published score on your
own authority is not something this project does quietly. **This is the line of the reel.**

### Beat 8. Then the same question, asked of the other half

**On screen:** two evidence rules, one carrying almost everything.
**Number:** **21.4% by the strong rule, 78.6% by the generic one alone**, and only **13.2%** of
claims name a test or a file at all. The counts under those shares, three runs on the same 1,516
transcripts across one evening: 13,126 claims / 5,806 verified, then 13,309 / 5,960, then 13,324 /
5,975. The counts moved every time. **The share read 78.6% every time**, and the third run was made
independently by a different lane.
**Source:** `python3 scripts/evidence-branch-report.py`. Bind the command, not the counts.
**RENDER THE SHARES, PIN THE COUNTS TO A MOMENT.** The corpus grows while anyone works on it. A
count that never drifts on a live corpus is a count nobody is re-running, so the reel should show
the shares as the claim and the counts as a reading taken at a stated time.
**The point, and it must be said this way:** this is not "four in five verifications are wrong". It
is "four in five rest on a rule whose accuracy nobody has measured". The size of the question, not
its answer.

### Beat 9. The check is red, on purpose

**On screen:** a terminal, exit code 1.
**Number:** `FAIL: cursor is under the floor at 4 predicted positives while carrying 34.9 percent
of the weight`, exit `1`.
**Source:** `python3 scripts/claim-calibration-report.py; echo $?`.
**The point:** a project shipping a red check pointed at its own headline number is making a
different kind of claim than one shipping a green one.

### Beat 10. And it stopped blaming the user's harness

**On screen:** the same Cursor transcript, before and after.
**Number:** before, "Cursor transcripts carry no file paths and no commits", card cell reads a dash
on both sides. After, the cell reads 1. The transcripts carried 2,279 absolute paths all along.
**Source:** `docs/STRANGER-AUDIT-2026-09-04.md`, addendum 2, same fixture both times.
**The point:** the tool was telling a person something false about their own machine.

### Beat 11. The only one anyone caught in themselves first

**On screen:** a terminal on a machine with nothing on it, and the line the tool used to print.
**Number:** `parts sum to the total: 0 + 0 + 0 + 0 + 0 = 0  OK`.
**Source:** `agentgrinder/cli.py`, the comment under the `authorship` branch, and
`tests/test_harness_trace.py`, which now asserts that line is absent on an empty population AND
still present when there is one.
**The point, in the code's own words:** an identity over an empty population passes whatever the
classifier does, so a reader is shown a green check that cannot go red. This tool's whole subject
is a number correct about the wrong object, and it was printing one. Found by running the CLI with
an empty `HOME`, which is the only way anyone was ever going to see it.
**Why it is the heart of the reel:** every other beat is a project auditing its own numbers. This
one is a project finding the exact defect it exists to name, inside itself, before anybody else
did. And the fix is not silence: the check still fires when there is something to check, and a
second test holds that, because silencing a check and fixing one look identical from outside.

---

## Two rules for whoever renders this

1. **Do not smooth beat 8 into "80% wrong".** It is the one number in here that a reel would
   naturally sharpen into a false claim, and doing so would break the reel's own argument.
2. **Bind every beat to its object.** T5's flipbook hashes what a reel was cut from. Every number
   above names a file or a command; a beat whose source cannot be hashed should be cut rather than
   softened.

## What must NOT be in it

- Any figure re-typed rather than re-run. Two rows of the Devpost table moved twice today.
- The word "verified" without the qualifier from beat 8 next to it.
- Anything from `nightrun.html`, which is a private project map that should not be in the public
  repository at all, let alone in a reel.
