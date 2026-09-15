# Inherited technical reference

Historical README from the hackathon source at 5828f39. Deployment links and measured results below belong to that source, not this independent product.

# Agent Grinder

**Strava for agents.** Turn a Claude Code, Cursor or Codex session into a run card. Share the work, follow builders and find your next practice.

[Open the app](https://agentgrinder.vercel.app) · [Try the labelled example](https://agentgrinder.vercel.app/?example) · [Judge guide](../archive/hackathon-2026-09/docs/JUDGE.md) · [Launch guide and screenshot](../archive/hackathon-2026-09/docs/LAUNCH.md)

## Start with one run

Capture a sitting locally, inspect its card, then choose whether to post it. Your profile keeps your runs. Follow another builder, discuss their work, or try a practice on your next sitting.

The smallest launch loop is **record → preview → post → follow → return**. Coaching and practice comparisons add depth inside a run. The labelled example shows that loop's coaching path without an account or paid model.

Runs start private. No raw transcript is uploaded by the run importer. Measurements describe session activity and supported evidence checks; they are not independent proof of quality. Independent-user adoption and improvement are not yet measured.

### Record your own session locally

```bash
git clone https://github.com/Morkeeth/agentgrinder.git && cd agentgrinder
python3 -m agentgrinder grind        # your most recent session -> grind.html
python3 -m agentgrinder grind --push # open a preview; choose audience before posting
```

**Web:** [agentgrinder.vercel.app](https://agentgrinder.vercel.app)

No install, no dependencies, no key, no server. The clone runs directly with Python. The optional coach has separate dependencies.

If you would rather have it on your `$PATH`, that needs a venv, not the stock python:

```bash
python3.12 -m venv .venv               # any python3.10+ you have
.venv/bin/pip install -e .             # then `.venv/bin/agentgrinder grind` works from any directory
```

The wheel includes the demo assets, so a non-editable install also works. Use Python 3.9 or newer for the local reader. The optional Strands coach needs Python 3.10 or newer.

`grind` discovers the latest Claude Code, Cursor or Codex session. Codex transcripts split at an observed idle gap before a new human turn. Cursor transcripts split at a dated human-turn gap; untimed agent activity means that gap does not prove idle time. `--list` shows sittings; `--pick 1` selects the first. Cursor timestamps need an explicit timezone for a dated comparison. Missing timing stays unknown.

If no supported transcript is available, `python3 -m agentgrinder demo` renders the bundled sample. The sample is labelled and does not represent your work.

It finds your last Claude Code sitting, keeps only the turns **you typed**, asks git what actually
shipped, and draws **the grind trace**: one row per file, your prompts as ticks on your own line,
commits on the row of every file git says they contain, and the longest span nobody typed through.

Nothing is uploaded. Sharing is your click.

```bash
python3 -m agentgrinder grind --list          # the sittings in that transcript
python3 -m agentgrinder grind --pick 2        # render a specific one
python3 -m agentgrinder grind --harness auto  # freshest Claude Code, Cursor or Codex session
python3 -m agentgrinder share                  # fun share card from latest grind
python3 -m agentgrinder share --claim          # invite card — claim your handle
python3 -m agentgrinder history               # every grind on this machine, ranked
python3 -m agentgrinder nightrun --since ISO  # a whole multi-agent night as one grind
python3 -m agentgrinder authorship            # who wrote every type:user record
```

## What a grind is

**A sitting, not a file.** A `.jsonl` transcript is a terminal that stays open; 151 of the 194
transcripts on this machine that carry a human turn hold more than one sitting, and the median
holds 3 (re-measured 31 Aug 06:4x over all 1,370 transcripts; a `171 … median 5` written earlier
the same night no longer reproduces — `human_sittings` over `~/.claude/projects/*/*.jsonl`). A grind is a
contiguous burst of work, ended by 30 minutes of total idle — the same rule at solo and fleet
scale, so the two cards cannot disagree about where a grind begins.

## The honesty rule — no ghost grinds

Every number names what it counted and over which population, or it prints an em-dash.

- **A prompt is a keystroke.** `type: "user"` is not a person: on this machine, in one night-run
  window, 2,415 records carried it and 40 were typed by a human. The gate is Transcripto's
  measured signal — `promptSource` typed or queued, dropping injected and sidechain records —
  vendored in `agentgrinder/authorship.py`, which sorts every record into five disjoint categories
  that **sum to the raw total**. The card prints the sum so you can check it.
- **Shipping is git's word, never the transcript's.** Every edited file is in exactly one of four
  states, and they add up too: landed in a commit made during the grind · committed after it
  closed · nothing has committed it since · outside the repository or git-ignored, so git was
  never asked.
- **A rank is a real rank.** "#12 of 625" is your place among every sitting on this machine. A
  badge fires when **any one** of five measures — longest no-typing stretch, moving time, tool
  calls, files changed, prompts typed — clears *that measure's* top-2% bar. Five bars, so the
  badge is rarer than a coin flip but commoner than 2%: replayed over all 625 sittings on this
  machine it fires on **34 of them, 5.4%** (31 Aug; the replay is `history.badge` over
  `history.load()`, and the per-measure cut is `max(3, 2% of the population)`).

## The numbers — verified output is the distance, prompts are the cost

The headline of every card is **verified per turn** = (verified claims + artifacts produced) ÷
typed turns. Typed turns are the denominator: what the run *spent*. A card that headlines
"47 prompts" celebrates the person who talked the most — the METR finding (developers believed
they were 20% faster and measured 19% slower). The rule, from the internal metric spec
(`METRICS-AGENTIC-ENGINEERING-2026-09-02`, not in this repo): *a good agentic engineer turns the
fewest human decisions into the most verified, delivered work — distance = verified output; prompts = cost.*

| Number | Role | Definition | Computed here? | If not: what it needs, and can you supply it today? |
|---|---|---|---|---|
| **Verified per turn** | **headline** | (verified claims + artifacts produced) ÷ typed turns | yes, when its three parts exist | — |
| Typed turns | cost | human-authored turns (`authorship.py`: typed OR queued, drops isMeta / isSidechain / tool_result) | yes | — |
| Verified-claims share | run number | of the agent's claims, the fraction with tool evidence in the same trace | **yes**, and calibrated (`claims.py`, rule below): the claim side reads precision 0.63, recall 0.66 on a held-out hand-labelled set | the evidence side has no label set yet, so the share carries one measured error and one unmeasured one |
| Correction rate | run number | typed turns that correct the agent ÷ typed turns | **not measured yet** — prints `—` | every turn labelled as undoing the one before it. No harness records that, so nothing on your machine can supply it today |
| Produced ÷ promised | run number | deliverables that exist at their path ÷ deliverables the run named | produced **v0**; promised **not measured yet**, prints `—` | a record of what the run said it would deliver. Nothing records it, so you cannot supply it today |
| Reach | run number | did the output cross to a person who is not the author | **yes on all three harnesses** (`reach.py`): true, false, or `—` when the machine cannot tell | when it prints `—`, the hover names the fact that is missing for that session: no commit in the window, a working directory that is gone, a session run outside a git work tree, or nothing written inside one |
| Moving time · pace · effort · segments · commits · cadence | cost group | unchanged from the v1 card | yes | — |

A `—` is never blank: hover it and the tooltip says, in plain words, which fact is missing and
whether you can supply it today. No number on a card is ever defaulted to zero, and no `—` points
at a tool you cannot install.

**Reach** (`agentgrinder/reach.py`, 3 Sep 2026) is read from git on your own machine, and needs no
network for the negative case:

* **true** — a commit made inside the session window sits on a remote owned by neither you nor an
  organisation you belong to, and the push landed while the window was open. Ownership comes from
  `git config remote.<name>.url` (not `git remote -v`, which prints URLs after any `insteadOf`
  rewrite), the push time from the remote-tracking ref's reflog, and your organisations from a
  signed-in `gh`. An open pull request on a repository you do not own counts too. The first real
  run of this returned *yes* for a push to the author's own GitHub organisation, which was true
  about the string and false about the world, so an unfamiliar owner is now checked against your
  organisations before anything is claimed.
* **false** — the window closed with commits that are on no remote at all, or only on a
  directory of yours: the work never left this machine.
* **`—`** — everything else, each with its own sentence on hover: no commit in the window, a push
  that landed after the window closed, a remote nobody can attribute, no account name on this
  machine to compare an owner against, an unfamiliar owner with no signed-in `gh` to say whether
  it is an organisation of yours (that one you can supply today: `gh auth login`), or commits that
  reached only your OWN remote, because a repository you own is not another person and this disk
  cannot say who read it.

**The claim rule** (`agentgrinder/claims.py`, measured 3 Sep 2026):
a *claim* is a line of assistant text whose sentences assert, as accomplished fact, that work in
this session is finished, correct, or checked. Headings, table rows, labels that introduce a list,
questions, plans, conditions, imperatives, quoted output and descriptions of how a thing behaves are
not claims. The evidence matcher changed on 4 September 2026. A test claim needs successful
output **in the same human turn**, with every named test or file matched. A failed result cannot
support it. A generic suite result can support an unnamed suite claim, but cannot support a named
test, file creation, deployment or compound completion claim. Those stay unknown. This is text
matching, not independent proof of execution; the detector scores below do not measure this matcher.
*Artifacts produced* =
distinct Edit/Write paths that exist on disk when the transcript is parsed.

**The rule publishes its own error bar.** 396 lines of assistant text from real sessions were hand
labelled against a rubric written before the sample was opened, split by session into a tuning half
and a held-out half. On the held-out half the rule reads **precision 0.63 and recall 0.66**, against
0.32 and 0.37 for the vocabulary regex it replaces. We aimed for precision above 0.8 and did not
reach it.

**What that figure describes, and the stratum it hides.** It is one machine's line population across
three harnesses, blended by that corpus's own share of each, so it is neither a general number nor a
Claude Code number. Split out: Claude Code reads 0.72 precision and 0.68 recall over 114 labelled
lines standing for 62.9% of the weight, Codex reads 0.86 and 0.62 over 44 lines standing for 2.2%,
and **Cursor is not resolved**. The rule predicted 4 positives in total across the held-out Cursor
lines, 1 true and 3 false, from 40 labelled lines standing for 34.9% of the weight, and a precision
from 4 predicted positives has a 95% interval of 0.00 to 0.86. So a third of the weight behind 0.63
is unmeasured, and it is the third dragging the blend below Claude Code's own 0.72.

**And the card only ever scores one of those three.** The claim rule runs in two places,
`ingest.parse_session` and `solo.py`, and both read Claude Code transcripts only.
`parse_cursor_session` and `parse_codex_session` return no claim count at all, checked on 4 September
2026 against the 298 Cursor transcripts and 81 Codex rollouts on the author's machine at the paths
this tool ships with. A Cursor run's card prints a dash for verified per turn and names what is
missing, which is correct. It also means the published 0.63 is measured over a population 37.1%
larger than the one it is applied to, and the figure describing what the card does is the Claude Code
row, 0.72 and 0.68. The conservative number stays the headline until the project owner rules
otherwise, because raising your own published score is not a quiet edit. More Cursor labelling is not
the fix; it would sharpen a stratum nothing scores. A test holds that seam and goes red the day
either parser starts feeding the claim rule. `python3 scripts/claim-calibration-report.py` reproduces
every figure here and **exits non-zero**, naming the thin stratum. The check is red on purpose.

Method, intervals, per-cell counts and what it still gets wrong:
[`archive/hackathon-2026-09/docs/CLAIM-RULE-CALIBRATION-2026-09-03.md`](../archive/hackathon-2026-09/docs/CLAIM-RULE-CALIBRATION-2026-09-03.md) and
[`docs/claim-calibration.json`](docs/claim-calibration.json). What is **not** measured: whether a
claim was matched to the *right* evidence. A generic `N passed` in a turn still verifies any claim
beside it, so read the share as one measured half and one unmeasured half.

**How big the unmeasured half is.** Which of the two evidence rules fires is a code path, not a
judgement, so it is countable without labelling anything. Over 1,516 Claude Code transcripts on one
machine, 13,126 claims and 5,806 verified: **1,245 (21.4%) were verified by a test name or file path
taken from the claim line, and 4,561 (78.6%) only by a generic passing token somewhere in the turn.**
The reason sits upstream of the matcher: only 1,732 claims, 13.2%, name a test or a file at all, so
for the rest there is nothing stronger to match on. That is the size of the open question, not an
answer to it: it does not say those verifications are wrong. `python3 scripts/evidence-branch-report.py`.

**Why the headline is a rate, not a count.** Over 308 held-out sittings the claim count correlates
+0.80 with how many tokens the agent wrote, and counting distinct verified artefacts instead does
not fix it (+0.56). Verified per turn reads +0.32 and the verified share +0.20, because
talkativeness sits in both halves of a ratio and divides out.

## The grind coach: an agent owns the numbers

The card above is a self-report checked by a rule. `coach` makes it a receipt: a
[Strands Agents](https://strandsagents.com) agent reads the sitting through five tools, checks
every claim against the evidence in its own human turn, asks the disk whether every file the run
wrote exists, asks git which of them landed, and only then writes the verdict block and a
next-session plan. It cannot write a number a tool did not return: `write_verdict` refuses it.

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e ".[coach]"   # Strands SDK, Python 3.10 or newer
.venv/bin/agentgrinder coach samples/sample_session.jsonl        # keyless, nothing leaves the machine
.venv/bin/agentgrinder grind --coach                             # your last sitting, verdict on the card
```

The five tools, in `agentgrinder/coach/tools.py`:

| Tool | Returns | Never returns |
|---|---|---|
| `read_run` | counts, the claim lines with ids, tool results per turn, one label per written file | a typed prompt, an absolute path, code |
| `check_claim` | verified or not, the token that matched, a 200-char snippet of the evidence | anything outside the claim's own turn |
| `verify_artifact` | exists, size, last modified, whether that instant is inside the window | the path |
| `git_evidence` | commits inside the window containing the file, the first later commit that touched it, or why git could not be asked | |
| `write_verdict` | accepted with five numbers, one paragraph and a 1-5 line plan, or refused with the reasons | a number no tool returned |

Three modes, and the mode is always printed:

- **local** (default): a real `strands.Agent` event loop over the five `@tool`s, driven by a
  scripted local model (`coach/local_model.py`). The loop, the tool registry, the dispatch and
  the `AfterToolCallEvent` hook that counts the calls are genuine Strands. The token generation
  is not a language model: it is a deterministic policy (`coach/policy.py`) that reads the run,
  checks every claim and file, and fills the verdict from the tool results. No key, no network,
  no spend. The report says so under NOTE every time.
- **bedrock** (`--model bedrock`, opt-in): the same loop with a real model on Amazon Bedrock
  choosing the tools. Needs AWS credentials and costs money. The claim lines and result snippets
  of the sitting leave the machine; the command prints that before it runs. Never the default.
- **none**: the five functions called in order, no agent. The fallback. If an agent mode fails
  the report prints the reason and ends with `status DEGRADED`; it never degrades quietly.

The card shows the verdict with "verdict produced by N tool calls", and N is the hook's count,
not the plan's.

**The series.** Every `grind` also records its five numbers as one reading in a local per-project
series (`~/.agentgrinder/series.db`, counts only, `--no-series` to skip). The card then says how
this grind compares with your previous grind on the same project by verified per turn: `baseline`
under two measured readings (a first reading is not a trend), then `helped`, `hurt` or
`unchanged`. `agentgrinder predict "ships 2 files"` writes down what you expect before you sit
down; the next grind on that project prints the prediction beside its verdict. The rule is in
`agentgrinder/engine/reporter.py`. Tested in `tests/test_coach.py`: the keyless path never constructs a Bedrock
model and opens no internet socket; a policy that writes a wrong number is refused.

## The lexicon

| Term | Meaning | Strava analogue |
|---|---|---|
| **Grind** | one logged agent work session against a goal | an activity |
| **The grind trace** | the drawing: where the work went, and how hard | the route + elevation |
| **Rig** | your setup: model, harness, tools, MCPs, human gates | your gear |
| **The Box** | the bounded workspace a grind runs in | — |
| **Ship** | a checked release that left the Box | a PR |
| **ACK** | evidence-linked recognition — never a like | kudos |
| **Crew** | a human and their agents; also a group you grind with | a club |
| **Scrapbook** | your public history of grinds, ships, failures and ACKs | your profile |

Retired, and not used here: Loop, Push, Builder's Diary, LOOPMAXXER, run/route/lap.

## Commands

| | |
|---|---|
| `coach` · `grind --coach` | the grind coach: a Strands agent checks every claim and file, then writes the verdict (keyless by default) |
| `predict` | write down what your next grind on a project will do; the next card shows it beside the verdict |
| `grind` | one sitting → the grind card (`run` is kept as an alias; `--harness auto` picks freshest agent) |
| `flex` | compare your real runs across Claude, Cursor, and Codex on this machine |
| `share` | screenshot-ready share card with claim-your-handle stub (`--vibe` `--roast`) |
| `vibe` · `roast` | meme label and honest shape roast — no streaks |
| `rig` | share your stack with friends (`--share-names` opt-in) |
| `heist` | rig heist card when someone ACKs your setup |
| `login` · `grind --push` | GitHub onboard and publish flow |
| `a2a` | Agent Activity protocol (export, feed, ACK propose) |
| `history` | every grind on this machine, ranked. Local only |
| `nightrun` | a whole multi-agent night as one grind, with `--public` redaction |
| `authorship` | the authorship tally as a table, so the card's claim is checkable without opening it |
| `profile <github-user>` | your Scrapbook: GitHub public data + your grinds |
| `demo` · `card RUN.json` · `v1card` | the bundled sample and the pre-trace card |

## Privacy

Local-first and dependency-free. `history` caches one small record per sitting in
`~/.agentgrinder/history.json`: **counts and timestamps only** — never a line of a prompt, never a
file path from inside a repository. Its *keys* are the transcript paths on this machine, and
Claude Code encodes the working directory into those, so the file does name the directories you
have worked in. It never leaves the machine, and nothing reads it but `agentgrinder history`.
Delete it and the next run rebuilds it: **7.8s** over 1,370 transcripts here, 0.04s warm (measured 31 Aug 06:2x; a 6.8s figure written on 30 Aug had already been re-measured at 6.1s and was never corrected here — it is a timing, so it moves).
`nightrun --public` redacts repository and lane names while leaving every number and the shape
unchanged. No auto-post, no auto-upload.

The coach runs on counts, claim lines and git evidence. It never reads a typed prompt into a
tool result, never returns an absolute path (paths become the labels the card prints), never
returns code. In the default `local` mode nothing leaves the machine. In `bedrock` mode the
claim lines and tool-result snippets are sent to Amazon Bedrock, and the command prints that
sentence before it runs; it is opt-in and never the default.

## Pre-existing code, disclosed

The Agents for Humans rules ask for new work built inside the submission period (10 Aug to 14 Sep
2026) and for any other pre-existing code to be disclosed. This repository was created on 31 Aug
2026. Three pieces of it did not start life here:

- `agentgrinder/authorship.py` is vendored from Transcripto (same author, earlier project). It is
  the rule that decides which `type: "user"` records a person typed. Named at the top of the file.
- The coach scaffolding in `agentgrinder/coach/` (the agent creation shape, the scripted local
  model that replays a plan through the real Strands event loop, and the three-mode dispatch with
  the DEGRADED banner) is lifted from [Morkeeth/agents-for-humans](https://github.com/Morkeeth/agents-for-humans)
  (MAGNET, same author, MIT, built from 29 Aug 2026 onwards, inside the submission period). The
  five coach tools and the verdict are new here. MAGNET does not enter this hackathon.
- The per-project series logic in `agentgrinder/engine/` (a verdict over a series of readings,
  `baseline` under two readings) comes from the same MAGNET repo, which itself ported it from
  [Morkeeth/mountain-of-helicon](https://github.com/Morkeeth/mountain-of-helicon) (same author,
  before the period).

Everything else in this repository was written inside the period. The Strands Agents SDK is a
dependency, not copied code.

MIT. See `LICENSE`.
