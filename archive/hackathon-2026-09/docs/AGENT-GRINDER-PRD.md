# AGENT GRINDER — PRD (product-first)

**One coherent product: the social network for agentic coding.** Strava's *loop* informs it —
record → detail → feed → kudos → crews → events → PRs → segments — but the vocabulary, metrics,
and mechanics are agent-native. The brand book (`AGENT-GRINDER-BRANDBOOK.md`) is the appendix; this
is the spine. Design comes *after* the loop works.

> Product = **Record agent sessions → publish Runs → follow builders → kudos on a feed → grind
> together at events.** The card is marketing for the URL, not the product.

## The unit: a Run
One bounded agent SITTING (Claude Code / Cursor / Codex) — a contiguous burst of work ended by 30
minutes of total idle, not a whole transcript file. A `.jsonl` is a terminal that stays open: 151
of the 194 transcripts on this machine carrying a human turn hold more than one sitting, and the
median holds 3 (`agentgrinder/solo.py`, re-probed 31 Aug 06:4x; the `171 … median 5` this line
carried until then does not reproduce against the current splitter). The solo and fleet cards use the same gap.

> **Vocabulary correction, 31 Aug.** This section used to read *"'Grind' is the verb and the
> culture; a **Run** is the noun you log."* The brand book §4 — which this PRD names as the source
> of truth for vocabulary — makes **Grind** the noun and explicitly retires `run/route/lap`. The
> shipped command is `agentgrinder grind` (`run` still resolves, so nothing that worked stops
> working) and the drawing is **the grind trace**. `nightrun` keeps its name: it is a compound
> that reads as one word and it is already the shipped fleet command.

**Honest metrics only — from logs, never vibes** (the "no ghost runs" rule):
| Strava | Agent Run | Source |
|---|---|---|
| **Distance (headline)** | **verified per turn** = (verified claims + artifacts produced) ÷ typed turns — what the prompts *bought* | `agentgrinder/metrics.py` · claims v0 in `claims.py` (Helicon witness later) · produced = Edit/Write paths that exist |
| — (cost, the denominator) | human prompts — typed turns, shown as cost, never as the achievement (METR: self-report is worthless) | `agentgrinder/authorship.py` · `promptSource` typed OR queued, dropping isMeta / isSidechain / tool_result |
| — (the five numbers, one row) | typed turns (cost) · verified-claims share · correction rate · produced ÷ promised · reach; `—` with a tooltip naming Transcripto / Helicon / repo E / gh when not computable here | internal metric spec `METRICS-AGENTIC-ENGINEERING-2026-09-02` (not in this repo); receipt `docs/VERIFIED-PER-TURN-2026-09-02.md` |
| Moving time | session duration | first→last timestamp |
| Pace | time per human prompt (cost group) | derived |
| Elevation | tool calls (effort) | assistant tool_use |
| Route map | **the grind trace** — one row per file, ordered by first arrival; marks where the work was; the path it took between them | `agentgrinder/soloroute.py` · Edit/Write/Read tool_use with a file_path |
| Segments / PRs | commits, on the row of every file git says they contain | `git log --all --name-only`, window-bounded, offset explicit |
| — (no Strava analogue) | **the longest span nobody typed through**, ranked by agent-active time | `solo.longest_stretch` |
| Personal records | your place among every sitting on this machine | `agentgrinder/history.py` |
| Gear | harness + model | session |
| Description | your caption (optional; never raw prompts) | user |
| Proof | commits / PR link (optional attach) | GitHub |

## Feature stack (Strava mapping) — build order
1. **Record (v1, SHIPPED):** `agentgrinder grind` ingests the latest sitting → draft Run; title auto-suggest
   ("repo A · Sunday night"); privacy private / link-only / public / crew-only; publish = upload + URL.
   *Without this loop there is no network, only a screenshot generator.*
2. **Run detail page (v1):** a permalink — headline stats, grind curve + optional 15-min splits,
   secondary (tools/files/commits), your note, kudos + comments, "compare to your avg" (same project,
   your history only at first). The share card is an *export* of this page.
3. **Feed (v1):** follow builders (asymmetric ok); home feed of friends' Runs, reverse-chron; kudos
   (one tap); short comments on the Run (never the transcript); "Alex kudoed your run" notifications.
   *This is the network.*
4. **Profile / Scrapbook (v1):** avatar + handle; totals (runs, prompts, hours, commits); recent Runs;
   PRs; harnesses used. *A profile without a feed is a graveyard.*
5. **Events & Crews (v1 — the viral wedge):** Crew = your fleet/squad (Strava club); Event = a grind
   event ("Agents for Humans · Sep 14", date range); event feed = all Runs tagged `#agents-for-humans`;
   opt-in Challenges ("5 runs this week"). **No global leaderboard v1** — shame-y and gameable; event-scoped only.
6. **Personal Records (v1.5):** longest session, most prompts in a run, best sustained pace, most
   commits, Focus PB (rule already built). Shown on run detail: "★ PR — most prompts this month."
7. **Segments (v2):** context segments, not GPS — compare your cadence on a project over time, day 1
   vs day 2 of an event, or a manual phase tag (research/build/debug). "Beat your last repo A run."
8. **Discover (v2):** browse *events*, not people; "12 grinders on Agents for Humans this week";
   trending opt-in public projects. Avoid "top builders."
9. **Wrapped / achievements (v2 — launch marketing):** Year in the Grind; badges (first run, hackathon
   finisher, ship streak). GitHub-Wrapped energy, receipted.
10. **Integrations (moat):** Transcripto = authorship gate (typed turns only); GitHub = commits/PR link;
    MAGNET (private) = "this stack vs baseline" badge, opt-in, never a public score.

## What NOT to build (early)
Prompt text on public pages · global leaderboard / "best prompter" Elo · token-count vanity · live
presence · a design system before feed+follow+event exist · **agent-to-agent autonomous posting**
(humans share; this is the anti-Moltbook rule).

## MVP cut
**v0.1 — "Strava minimum":** 1) record run from session, 2) run detail URL, 3) profile, 4) follow +
home feed, 5) kudos, 6) one event page (Sep 14 hackathon).
**v0.2 — retention:** 7) PRs + compare-to-self, 8) crews, 9) comments, 10) share-card export (design lands here, once the shape is right).

## Slices (reordered — upload + feed before polish)
- 0–2 ✅ run-card generator + native session ingest + local profile (done)
- **3 — upload (Supabase):** `push` writes a Run; run detail URL. *(backend schema live; needs GitHub OAuth + exposed schema)*
- **4 — feed + follow + kudos**
- **5 — one event page (Agents for Humans, Sep 14)**
- **6 — stranger pass + share-card export (design)**

## Backend (live)
Supabase schema `agentgrinder` (in project xengine-review): `profiles` (crew + rig jsonb), `runs`
(metrics + grind curve + visibility, private by default), `acks` (evidence-linked kudos). RLS on:
public reads public Runs; owners own theirs. GitHub OAuth = sign-in.
*(DB table currently named `loops`; rename → `runs` for term coherence — empty, trivial migration.)*

## CLI target
`run` → `push` → `feed`

## Launch bar (pre-declared)
A stranger opens a Run URL cold **and** posts their own Run before **Sep 14**. Hackathon = the build
forcing-function; Product Hunt = the distribution ("remember Moltbook? here's the real version").

## Credit
Product-first stack and the "don't lead with the card" push: Cursor. Honesty DNA (a check is not a
claim; no ghost runs): the OpenAI PRD + the Agent Science / ATA lineage.
