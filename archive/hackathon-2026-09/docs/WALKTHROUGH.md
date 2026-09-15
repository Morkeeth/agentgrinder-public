# Agent Grinder, a walkthrough

*What it is, what one command gives you, and what its numbers deliberately do not mean.*

This project's whole claim is that **a number without a source is a guess**. Its own headline
number was one until 3 September 2026. This document is partly the tour and partly the receipt for
that stopping being true.

---

## The problem, in one measurement

Your coding agent tells you it fixed the test, shipped the file and got the suite green. Checking
that means rereading the whole transcript, so nobody checks it.

The obvious fix is to count turns from the session log. That number is confidently wrong. A raw
Claude Code transcript marks far more records as coming from the human than a human ever typed,
because tool results, injected skill bodies, harness envelopes and prompts one agent wrote to
another all carry `type: "user"`.

Run `python3 -m agentgrinder authorship --hours 336` on your own machine and you get your own
version of this. Three windows on the author's machine, 4 September 2026, each one asked for
explicitly:

| window | records marked `type: "user"` | actually typed by a person |
|---|---|---|
| 1 hour | 58 | 4, 6.9% |
| 24 hours | 3,291 | 80, 2.4% |
| 336 hours, 14 days | **34,032** | **966, 2.8%** |

The share moves a little with the window. The gap does not move at all. Every dashboard built on that field is
inflating the number it shows you, and the command prints its five categories with their sum so
you can check the correction rather than trust it.

## One command

```bash
git clone https://github.com/Morkeeth/agentgrinder.git && cd agentgrinder
python3 -m agentgrinder grind
```

That is the whole install. No dependencies, no key, no server, no account. It reads transcripts
you already have and writes `grind.html`. If you have never run a coding agent it says so, names
every path it looked in, and points you at `python3 -m agentgrinder demo`.

Nothing is uploaded. Publishing a card is a separate command and a deliberate click.

```bash
python3 -m agentgrinder demo                  # a card from the bundled sample, no data needed
python3 -m agentgrinder grind --list          # the sittings inside one transcript
python3 -m agentgrinder grind --harness auto  # newest Claude Code, Cursor or Codex session
python3 -m agentgrinder history               # every grind on this machine, ranked
python3 -m agentgrinder authorship            # who actually wrote every type:"user" record
```

## What a grind is

**A sitting, not a file.** A `.jsonl` transcript is a terminal that stayed open. A grind is a
contiguous burst of work ended by 30 minutes of total idle, so one transcript usually holds
several.

## The headline, and why it is a rate

**Verified per turn = (verified claims + artifacts produced) ÷ typed turns.**

Typed turns are the denominator on purpose. They are what the run *cost you*. A card that
headlines "47 prompts" is celebrating whoever talked the most.

It has to be a rate rather than a count because a count of claims tracks how much your agent
talks: over 308 held-out sittings, claim count correlates **+0.80** with assistant output tokens.
Counting distinct verified artefacts instead does not fix it (+0.56). Verified per turn reads
**+0.32**, because talkativeness sits in both halves of a ratio and divides out.

## What the numbers mean

| number | what it counts | where it comes from |
|---|---|---|
| Typed turns | turns a person actually typed | `authorship.py`, five disjoint categories that sum to the raw total |
| Verified claims | claims with matching evidence in the same human turn | `claims.py`, the rule below |
| Artifacts produced | files the run wrote that exist on disk when it is parsed | the transcript, then the filesystem |
| Commits | commits made inside the session window | git, never the transcript |
| Reach | did the output cross to a person who is not you | git remotes and push refs, `reach.py` |

**Shipping is git's word, never the transcript's.** An agent saying it committed something is a
claim. The commit is the evidence, and they are counted separately.

## The claim rule, and its error bar

A rule decides what counts as a claim, so that rule has an error rate, and until 3 September
nobody had measured it.

396 lines of assistant text were hand-labelled against a rubric written **before the sample was
opened**. Sessions were split into a tuning half and a held-out half by a seeded hash before a
single line was read. The rule was iterated on the tuning half only. The held-out half was scored
once, after the rule was frozen.

| held-out half | precision | recall |
|---|---|---|
| the old rule, one vocabulary regex over a line | 0.32 (0.18 to 0.50) | 0.37 (0.21 to 0.55) |
| **the rule shipping today** | **0.63** (0.43 to 0.83) | **0.66** (0.46 to 0.83) |

**The target was precision above 0.8. It was not reached. 0.63 is the number**, and it is printed
on the site, in the README, in the module's own docstring and here.

Reproduce all of it from the committed counts:

```bash
python3 scripts/claim-calibration-report.py
```

## The part that matters if you use Cursor or Codex

That 0.63 is a **blend of three harnesses**, weighted by their share of one machine's corpus. Split
apart, they disagree:

| harness | precision | recall | hand-labelled lines | standing for |
|---|---|---|---|---|
| Claude Code | 0.72 (0.52 to 0.92) | 0.68 (0.49 to 0.87) | 114 | 35,033 lines, 62.9% |
| Codex | 0.86 (0.50 to 1.00) | 0.62 (0.25 to 1.00) | 44 | 1,221 lines, 2.2% |
| Cursor | **not resolved** | not resolved | 40 | 19,403 lines, 34.9% |

Two things follow, and both are stated on the site rather than buried here.

**The Cursor cell is empty on purpose.** Precision is true positives over predicted positives, and
on the held-out Cursor lines the rule predicted **four** positives in total: 1 true, 3 false. A
precision computed from four predicted positives has a 95% interval running from 0.00 to 0.86,
which is nearly the whole scale. There is a number that could go in that cell. It would be an
absence wearing a decimal point.

**The headline is lower than the harness it actually scores.** On Claude Code alone the rule reads
0.72, above the published 0.63, because that thin Cursor stratum drags the blend down. The
conservative number stays the headline. Raising your own published score on your own authority is
not a thing this project does quietly.

## What the numbers deliberately do not mean

- **Verified does not mean correct, and four in five verifications rest on the weaker rule.** A
  claim is verified when a tool result *in its own human turn* carries a matching token. There are
  two ways that can happen, and they are not equally strong: a test name or file path taken from
  the claim line appearing in a result, or just a generic `N passed` / `OK` / `exit 0` somewhere in
  the turn. Whether either match was *right* has no label set. But which one fired is countable,
  and over 1,516 transcripts, 13,126 claims and 5,806 verified: **1,245 by the strong rule (21.4%)
  and 4,561 by the generic one alone (78.6%)**. Only 13.2% of claims name a test or a file at all,
  so for most of them there is nothing stronger to match on. That is the size of the open question,
  not an answer: it does not say those verifications are wrong. Run
  `python3 scripts/evidence-branch-report.py` on your own machine and you get your own split.
- **The claim rule scores Claude Code sessions only.** On a Cursor or Codex run the card prints a
  dash for verified per turn, and hovering it says what is missing. Those cards do carry real files
  touched, commits, artifacts and reach, read from your own transcript.
- **Correction rate and produced ÷ promised are dashes**, because nothing on your machine records
  what a run said it would deliver. A dash is never blank here: hover it and it names the tool that
  owns the number and whether you can supply it today.
- **No number is ever defaulted to zero.** A count with no source stays a dash. A zero is an
  assertion that nothing happened, and that is a different claim.
- **A rank is a rank on your machine**, not against anyone else. This tool will never compare you
  to a famous engineer's session metrics, because those are private and nobody has them.

## Privacy

The card carries counts. It never carried the transcript.

A funded competitor tried the other way. Amp shipped public, internet-wide thread sharing and
withdrew it on 2 June 2026, in their own words: *"It's getting too hard to review a thread to
ensure it doesn't contain any snippets of sensitive files."*
(https://ampcode.com/news/end-of-public-threads). They note the problem gets worse on its own,
because agents read more files into context with every model release.

Agent Grinder never had the transcript to leak. `grind` runs locally, region names stay on your
machine and only integer indices are ever published, and nothing leaves without your click.

## Where the checks are

- `python3 -m pytest -q` runs the suite.
- `python3 scripts/claim-calibration-report.py` recomputes every published figure from the counts
  committed beside them, and **exits non-zero on purpose** while a stratum carrying 10% or more of
  the population weight sits under 10 predicted positives. Cursor sits at four. The check is red
  today, and the reason it is red is written on the methodology page.

A project shipping a red check pointed at its own headline number is making a different kind of
claim than one shipping a green one.

- **Live:** https://agentgrinder.vercel.app
- **Method in full:** `docs/CLAIM-RULE-CALIBRATION-2026-09-03.md`
- **The counts themselves:** `docs/claim-calibration.json`
