---
doc: hack
project: AGENT GRINDER — where you post your real runs
phase: BUILD
event: CANDIDATE — Agents for Humans (Devpost, Sun 14 Sep 2026, $40K)
ruling: OSCAR 3 Sep OPTION C — Grinder is the product and Sep-14 entry; MAGNET is its disclosed engine library
canonical: docs/AGENT-GRINDER-PRD.md · docs/AGENT-GRINDER-BRANDBOOK.md
last-touched: 2026-09-02 (Fable)
---

# AGENT GRINDER — hack.md

## STATE 2026-09-02 (Fable, probed)
- `Morkeeth/agentgrinder` PUBLIC (HTTP 200), main, 0 unpushed. Live agentgrinder.vercel.app. STRANGER-PASS done (`docs/STRANGER-PASS.md`). `aistrava` (no remote, 82 commits) is the history; this repo is the seed. **Ruling 6 (clean seed → new remote) is executed.**
- Ruling of record (OSCAR 3 Sep OPTION C): Grinder is the product and Sep-14 entry. MAGNET is its disclosed Strands/engine library, not another product or submission.
- **Metric finding (METRICS-AGENTIC-ENGINEERING-2026-09-02, an internal spec not in this repo):** the PRD maps Strava Distance → human prompts. Prompts are a COST (the denominator), not an achievement. A card that headlines "47 prompts" celebrates the METR failure. Rule needed: **distance = verified output; prompts = cost.** The card's five numbers: typed turns · verified-claims share · correction rate · produced ÷ promised · reach. Headline = verified-per-turn.
- PRD gate lines: buyer = none at v0 (consumer face of MAGNET's data); recurring number = runs shared per week by non-authors; incumbent test = GitHub could ship "session wrapped" in a sprint, the wedge is cross-harness authorship + the honest verified term; day-two user = a builder who wants to post a real run; vision = the social layer for AI-native work.


> **Where you post your real runs.** Log grinds from Claude, Cursor, Codex — track progression,
> run with crews, earn ACKs. Strava-shaped loop; agent-native vocabulary (see brand book).

## ⭐ NORTH STAR (the press-release line)
*"I finished a 2-hour session on repo A — 47 prompts, 3 commits, a personal best on focus —
and my friends gave it kudos before I closed the terminal."* A stranger sees a friend's AGENT GRINDER run
and wants their own.

## 🚀 MOONSHOT GATE (every hack.md carries this now — Oscar 2026-08-30)
**Next slice is not the plan. The 10x is.** This project ships to a *stranger*, not to Oscar.
- **The 10x:** the social layer for AI-native work — "Strava for agents." Network effect = friends' feeds.
- **The company:** the shareable/consumer face of the same data MAGNET tracks privately. Distribution engine for the whole verification thesis.
- **The stranger + date:** ≥1 person who is not Oscar uploads a run and shares it, by the hackathon deadline.
- **Kill if:** the run-card isn't cool enough that Oscar wants to post his own on day one. Coolness is the gate, measured by "would you share this," not by tests passing.

## PROMISE LINE
Where you post your real runs — after any coding-agent session, one command turns it into a card
you'd actually share. Every metric traces to the session log.

## CONSTRAINT
Every metric traces to the session log. `47 prompts` means 47 typed turns were counted, not a vibe.
On-ramp reuses Transcripto's authorship signal (typed turns only), never raw `type:user` records.

## CONSTITUTION
1. Fun first — if the card isn't shareable, nothing else matters.
2. Reuse Transcripto for authorship; do not re-solve "which turns did the human type."
3. Real metrics or none. `baseline`/`—`, never a fabricated stat.
4. Local-first on-ramp (like Transcripto); the social feed is opt-in upload, explicit.
5. No auto-post, no auto-upload — sharing is the user's click.
6. MIT.

## PLAN (risk-first — the wow spike is slice 1)
| # | Slice | Done when |
|---|-------|-----------|
| 0 | Repo + memo + this hack.md | clone works |
| 1 | **Run card generator** (session JSON → shareable HTML activity card, the signature "session route") | `python3 -m agentgrinder demo` opens a card you'd post |
| 2 | Ingest real sources: Transcripto output + GitHub events → run JSON | `agentgrinder from-transcripto` makes a real card from your last session |
| 3 | Upload + feed (Supabase): a run gets a public URL; a feed page lists runs | a second person opens your run URL cold |
| 4 | Friends + kudos; hackathon "event" pages (group runs) | two athletes, one kudos |
| 5 | Stranger pass + launch trio | STRANGER-PASS.md green; posts drafted |

## NOW (updated 2 Sep 2026 — stranger pass)

**Slice 5 (stranger pass):** `docs/STRANGER-PASS.md` PASS — cold `demo` + `pitch-demo.sh` exit 0 with sample fallback when no `~/.claude`. Fix: `scripts/pitch-demo.sh` detects empty machine, uses `samples/sample_run.json` for vibe/roast/grind/share.

**Next slice:** ≥1 non-Oscar stranger cold-read. The current entry and engine relationship is fixed by OSCAR 3 Sep OPTION C; do not revive the stale 1 Sep split.

**Shipped this wave:** `docs/MOONSHOT-MEMO-2026-09-02.md` · `docs/STRANGER-PASS.md` · `docs/DEVPOST-READY.md` · `docs/FILM-SCOUT-COMMANDS.md` · `docs/OSCAR-CLICK-LIST-2026-09-02.md` · pitch-demo cold-path fix.

**Live:** [github.com/Morkeeth/agentgrinder](https://github.com/Morkeeth/agentgrinder) · [agentgrinder.vercel.app](https://agentgrinder.vercel.app) · pitch: `/?pitch` · event: `/?event=agents-for-humans`

Receipt: `docs/CLOUD-RECEIPT-grinder-ambitious-2026-09-02.md`

## LOG

| When | What |
|------|------|
| 2026-09-02 | LOOP 0: fetched Devpost rules, StraVIBE, Moltbook; wrote moonshot memo |
| 2026-09-02 | LOOP 1 refute: main `pitch-demo.sh` failed at vibe (no sessions) — not stranger-ready |
| 2026-09-02 | BUILD slice 1: fixed pitch-demo sample fallback; STRANGER-PASS PASS |
| 2026-09-02 | BUILD slices 2-4: Devpost pack, film scout, Oscar click-list docs |
| 2026-09-02 | BUILD slice 5: `pytest tests/test_meme.py` 3 passed; redact test 8/8 |

## PREVIOUS (1 Sep 2026 — pitch-ready)
Slices 1-2 shipped. **The NIGHT RUN card ships** — `agentgrinder nightrun [--public]` turns a whole
multi-agent night (orchestrator + every subagent lane) into one Run and draws THE SESSION ROUTE:
a human trunk, agent lanes forking at real spawn times, a lanes-open elevation profile, a commit
rail, and an annotated handoff. Rendered and looked at in light, dark and at a true 390px.
Receipts + the honest "would I post this" answer: `NIGHTRUN-2026-08-31.md`. Shots: `docs/shots/`.

Next: (1) a cold stranger read of the card; (2) slice 3/D — a run gets a URL a second person opens
cold, share = an explicit human click (redaction now exists, hosting is Oscar's); (3) give the SOLO
card the same treatment — it is still the v1 sparkline and it is the one most users generate first.
