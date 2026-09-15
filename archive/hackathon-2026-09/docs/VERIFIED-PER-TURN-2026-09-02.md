# Verified per turn — the card headline flip (2 Sep 2026, Fable)

**Finding fixed:** the card mapped Strava *Distance* → human prompts. Prompts are a **cost**
(the denominator), not an achievement. Headlining "47 prompts" celebrates the METR failure
(developers believed 20% faster, measured 19% slower). Spec:
`METRICS-AGENTIC-ENGINEERING-2026-09-02` (an internal spec, not in this repo). Rule: **distance = verified output; prompts = cost.**

Branch `fable/verified-per-turn-2026-09-02`. Not pushed, not deployed.

## The demo card, before → after (`python3 -m agentgrinder demo`, `samples/sample_run.json`)

| Slot | Before (main `12af89c`) | After |
|---|---|---|
| Headline | **47 prompts** (Distance) · 2h 20m · 2:59 /prompt | **0.21 verified per turn** — (6 verified + 4 artifacts) ÷ 47 typed turns |
| Five-number row | — (did not exist) | typed turns **47** `cost` · verified claims **6/9 · 67%** · correction rate **—** · produced ÷ promised **4 ÷ —** · reach **—** |
| Tooltips on `—` | — | Transcripto export-run (typed turns, correction rate) · Helicon witness (verified share) · repo E artifact-detect (promised) · git remotes + gh + launch log (reach) |
| Cost group | (was the headline) | "COST — what the run spent": 47 prompts · 2h 20m · 2:59 /prompt, then effort 213 tool calls · 12 files · 3 commits · 20.1/h |
| Route SVG | present | unchanged |

Terminal summary now prints the same numbers (`cli._render`). Rendered and looked at in light at
620px (headline, five-row, cost group and route all as designed). **390px is unverified:** headless
Chrome on this machine would not lay out below its minimum window width — three attempts at
`--window-size=390` produced the same clipped ~500px layout (five columns still showing, so the
≤420px media query that collapses the row to three columns and shrinks the pace figure never
fired). Check it on a phone before it ships. `privacycheck card.html` → 1 clean, 0 leaking;
`scripts/privacy-audit.py .` → no file touched by this change is DIRTY (the 7 DIRTY hits are
`.git/` internals and a pre-existing `docs/FILM-SCOUT-COMMANDS.md` tilde path).

**The demo's 6 / 9 / 4 are fixture values** — the sample has no per-event data, so the v0 rule
never runs on it. They are marked as illustrative inside `samples/sample_run.json`
(`_five_numbers_note`). The pre-existing `athlete`/`project` strings in that fixture were not
touched; they name a real project and should be replaced by whoever owns the sample.

## What is computed locally now (`agentgrinder ingest.parse_session`)

| Field | Rule | Status |
|---|---|---|
| `turns_typed` | `authorship.py` (vendored Transcripto signal) | as before |
| `claims`, `claims_verified` | **v0 rule, `agentgrinder/claims.py`**: a claim is an assistant text LINE matching `passes|passed|fixed|done|deployed|works|green|verified|ship(s|ped)`; verified when a tool result in the SAME HUMAN TURN (either side of the claim) carries a `test_*` name or file path from the claim line, or `N passed` / a line starting `OK` / `exit 0` not contradicted by `N failed` / `FAILED` / `Traceback` | local stand-in for `helicon witness` |
| `artifacts_produced` | distinct Edit/Write `file_path`s that exist on disk at parse time | v0; "at parse time" ≠ "at close" |
| `corrections` | — | `None`: Transcripto's classifier |
| `artifacts_promised` | — | `None`: repo E |
| `reach` | — | `None`: git remotes + gh + launch log |

**Deviation, stated:** the brief said a claim is verified if *followed* by a tool_use with matching
output. In real traces the agent runs the check and then states the claim, so a strictly-after window
marks nearly every true claim unverified — a red light nobody would audit. The window is the whole
human turn, both sides; evidence from another turn never counts.

**Probe on this machine** (11 most recent sittings with a typed turn, counts only, 2 Sep ~23:5x):
typed turns 1–3 each (fleet lanes, one brief per session) · claims 1–42 · verified share 0–100%
(most 100%) · artifacts produced 0–8 · verified per turn 1.0–18.5. Reading: the rule is loose —
`done` and `ship` match prose and headings, and a generic `N passed` in the same turn verifies any
claim next to it. It over-counts, which is why the share and the claim count sit beside the headline
rather than being hidden inside it. Read it as a ceiling, not a floor; Helicon witness replaces it. The 1–3 typed-turn shape also shows the headline is meaningless for a one-brief lane
session — verified per turn is a number for a sitting where a person actually iterates.

## Tests
`python3 -m pytest -q tests/` → **13 passed** (3 meme + 1 redact + 9 new in
`tests/test_verified_per_turn.py`: headline math, no-fabrication on missing parts, the five-cell row
and its tooltips, the card headlines 0.21 and never `>Distance<`, claim-line tokens, generic-token
rejection when the result also fails, the same-human-turn window, and a synthetic `.jsonl` through
`parse_session`). `tests/test_redact_no_whitelist.py` called `sys.exit` at import and broke
`pytest tests/` collection (INTERNALERROR on main); it now exposes a test function and only exits
under `__main__` — `python3 tests/test_redact_no_whitelist.py` still prints `ok=8 fail=0`.

## Not done / out of scope, flagged
- ~~`agentgrinder/solocard.py` (the `grind` card most users generate) and `site/methodology.html`
  (`heroN: r.prompts`) still headline prompts — the same inversion, not touched here.~~
  **Flipped 3 Sep** (same branch). Correction: `heroN: r.prompts` was in `site/index.html:861`,
  not methodology.html (which carries no numbers). See "3 Sep addendum" below.
- ~~`render_profile` still shows a "Prompts" total; untouched, reads the same `Activity` fields.~~
  **Flipped 3 Sep.**
- Correction rate, promised, reach print `—`: no classifier, no repo E read, no reach probe was built.
- No lift experiment (the spec's "done when a lift number exists") — every card is still a claim.

## 3 Sep addendum — the other three surfaces (Fable, same branch)

One definition now: `metrics.headline_of(run)` / `metrics.five_cells(run)`; every surface reads it.

| Surface | Before | After |
|---|---|---|
| `grind` card (`solocard.py`) | first stat cell **Prompts** (`47`); h1 fallbacks "N prompts → M commits on X", "N prompts, M files changed in X", "N prompts on X" | `.hl` block **verified per turn** (or `—` + "needs …" tooltip) → five-number row (typed turns tagged `cost`) → **COST — what the grind spent**: Prompts · cost, moving time, pace, commits; h1 fallbacks lead with the outcome ("3 commits landed on X", "2 files changed in X, no commit yet"). Rung 2 "1 prompt → 104 tool calls" kept: a leverage sentence. Terminal summary prints the same order. |
| web app (`site/index.html`) | run card first stat `prompts`; share card `heroN: r.prompts` / "prompts typed"; profile totals `runs · prompts · hours · commits`; claim placeholder "prompts" | `vptHtml(r)` + `fiveRow(r)` + "cost — what the grind spent" on the run card; share hero = verified per turn (tooltip = formula), prompts moved into the stats strip as cost; profile totals lead with Σ verified per turn over runs that carry all three parts (`vptTotals`, a run missing a part is left out, never 0); import preview lists verified claims / artifacts produced |
| profile (`profile.py` → `render_profile`) | totals `Runs · Prompts · Run commits · Repos` | `Verified per turn · Runs · Run commits · Repos` + "Cost — N prompts typed across M runs"; each run row leads with `0.21 verified/turn`, `47 prompts · cost` beside it. `totals_of(runs)` is pure (tested without the network). |

`solo.parse_solo` now carries `claims`, `claims_verified`, `artifacts_produced` (v0 rule replayed over
the SAME sitting window as every other count; `corrections` / `artifacts_promised` / `reach` are
`None`). `push.export_run` sends the three counts.

**Not stored by the web app.** The Supabase `runs` table (read 3 Sep via list_tables) has columns
`prompts, tool_calls, files_touched, commits, rhythm, route, tool_mix` and none for the five numbers.
No migration was applied (no deploy on this lane), so every published run reads `—` with a tooltip
that says so and names the owner. The insert stays column-safe; the import preview shows the counts
and says they are not saved yet.

Sample fixture: `athlete`/`title`/`project` are now neutral (`sample-grinder` / `sample-project`);
numbers untouched. `profile.html` (tracked, generated earlier) still carries the old names and the old
"Prompts" total — it is a rendered artefact, not regenerated here (needs a real GitHub user).
`docs/STRANGER-PASS.md` quotes the old demo output verbatim; stale, left as the record of that pass.

Rendered and looked at (light, 1100px): grind card on a real 1-turn lane sitting reads
**6.00 verified per turn — (6 verified + 0 artifacts) ÷ 1**, with `6/6 · 100%` beside it: the v0
over-count on a one-brief lane session, exactly the ceiling the 2 Sep probe predicted. Demo card
0.21, profile 0.21. `privacycheck` on all three → 3 clean, 0 leaking.

Tests: `python3 -m pytest -q tests/` → **18 passed** (13 + 5: grind card via a synthetic `.jsonl`
through `parse_solo`, the h1 ladder fallbacks, the dash on a dump without claim counts, the web
app's source, the profile totals + render).
