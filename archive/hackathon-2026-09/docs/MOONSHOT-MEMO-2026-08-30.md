# Moonshot memo · AISTRAVA · 2026-08-30

## GOAL
A fully functioning product where people upload their AI-work "runs" (coding-agent sessions +
projects) and share them with friends — Strava for how you work with AI. Stranger-visible: a person
who is not Oscar uploads a run and posts it.

## Current model (what we believe)
Coding-agent transcripts are the most valuable dataset you own and nobody reads them. Transcripto
already grades the turns you typed. The missing layer is *social + shareable* — the Strava move:
make the record fun, comparable, and postable, and the corpus grows itself. If wrong: people don't
want their work habits public and the social layer is dead on arrival (mitigation: private-by-default,
share is explicit; the run card is valuable solo even with zero friends).

## External evidence
| Source | What it says | Confidence |
|--------|--------------|------------|
| Lenny's Podcast open transcript | Open a corpus, people build on it; distribution compounds (an existing corpus in another project) | High |
| Strava | The activity card + kudos + segments loop is the retention engine, not the GPS | High |
| Transcripto (live, PyPI 0.1.1) | Authorship signal (typed turns) already solved; on-ramp exists | High (ours) |
| Wave Radio archive | Static, no-backend, shareable artifact pattern works for Oscar | High (ours) |
| Duolingo/Wrapped/GitHub Wrapped | "Your year in X" shareable cards drive massive organic reach | Med-High |

## Hypotheses (ranked)
1. **The run card is the whole product.** Falsifiable: if the generated card isn't something Oscar
   would post unprompted, the social layer won't save it. Kill bar: Oscar's own reaction on slice 1.
   Cost: 1 slice (done this session).
2. **Transcripto is the moat on-ramp.** Real per-session metrics from typed turns are hard to fake;
   competitors would show vanity token counts. Falsifiable: if GitHub-only data is enough, Transcripto
   isn't a moat. Cost: slice 2.
3. **Hackathon "event" pages are the viral wedge.** A group of builders documenting one hackathon =
   built-in multiplayer. Falsifiable: if solo cards get shared but events don't, drop events. Cost: slice 4.

## Refute result
Adversarial pass (self): the sharp risk is **privacy/ick** — people may not want prompt-habits public.
Survives because: (a) solo card has standalone value, (b) share is opt-in and the card shows
*achievement metrics* (prompts, commits, focus), not the prompt *content*. NO NET-NEW collision:
AISTRAVA does not duplicate MAGNET (private eval ledger) — it's the consumer/social face; and it does
not duplicate repo E (private ops board). Confirmed distinct.

## Collision check
| Idea | Already built? | Verdict |
|------|----------------|---------|
| Grade typed turns | Transcripto (live) | REUSE as on-ramp, don't rebuild |
| Private adoption/eval ledger | MAGNET | DISTINCT — AISTRAVA is public/social face |
| Ops board across lanes | repo E | DISTINCT — that's private "what's up", not shareable runs |
| Open transcript corpus | Wave Radio | ADJACENT — same Lenny thesis, different medium |

## VENUE RULING (needs Oscar)
Agents for Humans (Sep 14, $40K) fits AISTRAVA better than MAGNET — "agents for humans" is literally
a social/consumer framing, and a Strava-for-agents demo is more fun + human than an adoption ledger.
**Recommendation: AISTRAVA becomes the Agents-for-Humans entry; MAGNET parks or folds in as the
private-metrics engine behind it.** Oscar's call.

## BUILD-PLAN (Loop 2) — see hack.md PLAN table
1. Run card generator (DONE this session) 2. Real ingest (Transcripto+GitHub) 3. Upload+feed (Supabase)
4. Friends+kudos+events 5. Stranger pass + launch.

## OPS (Loop 4 — separate lane, Oscar-gated)
- Deploy the feed (Supabase project) — Oscar click.
- Publish repo + launch trio — Oscar click.

## Explicitly NOT doing (effort tradeoff)
| Could do | Why not now |
|----------|-------------|
| Full auth/social graph | Slice 1 is the card; multiplayer is slice 3–4 |
| Diarisation / prompt-content display | Privacy risk; metrics only for v1 |
| Rename workshop | Working name AISTRAVA; /weekend-name later, not blocking |

---
## UPDATE 2026-08-30 (pm) — positioning, competition, launch venue

### Competition (searched, verified)
- **Moltbook** (moltsbooks.com) — "social network for AI agents," Musk-hyped, viral, then **flopped**. Agents posting chatter to each other: novelty, no stakes, no utility loop. CNBC + Nature (Agent4Science) confirm the *chatter* axis.
- Adjacent-only: Token Tracker (public token leaderboard), enterprise analytics dashboards (Claude Code/Cursor/Jellyfish), social-media-management agents. None do work-grounded activity for the human builder.

### Positioning — Moltbook V2, done seriously (LOCKED)
AISTRAVA is **the serious V2 of the Moltbook case we loved but which flopped.** Same excitement (agents + social), but the athlete is the **human builder**, the runs are **real sessions with grounded metrics**, and the stake is **your reputation and craft** — not bot theater. Moltbook proved the chatter axis dies; we own **proof-of-work for AI-native builders.**

Three pillars (seriousness order):
1. **Portfolio / hiring** — a GitHub-auth'd, verifiable record of how you actually work with agents. No artifact for this exists today; every AI-native employer wants it. The killer wedge Moltbook never had.
2. **Self-improvement** — the real Strava loop: patterns, cadence, PBs across sessions.
3. **Team/org** — benchmark and share the setups and skills that move output.

DNA: runs are grounded in real sessions — honest by construction, same "verify at the object" thesis as ATA + Agent Science.

### Launch venue (LOCKED as sequence, not either/or)
- **Agents for Humans hackathon (Sep 14, $40K)** = the BUILD forcing-function. The deadline makes slices 3–4 (upload + feed + profiles) actually get finished, and gives a judged moment.
- **Product Hunt / early-tools launch** = the DISTRIBUTION + stranger-gate, riding the "remember Moltbook? here's the version that's actually useful" story. PH rewards exactly this shape (fun, visual, self-serve, shareable run card) — but needs slices 3–4 live first.
- Do NOT PH-launch the local card generator alone. Hackathon builds it; PH launches it.
