# Moonshot memo · Agent Grinder · 2026-09-02

## GOAL

≥1 stranger cold-clones, grinds one session, and would post the card — Sep 14 Agents for Humans readiness.

Press-release line: *"I finished a 2-hour agent session and my friends ACK'd it before I closed the terminal."*

Kill bar: if `docs/STRANGER-PASS.md` cannot run on a fresh clone without Oscar credentials, the night failed — not "tests pass."

---

## External evidence (fetched 2026-09-02)

| Source | What it says | Confidence |
|--------|--------------|------------|
| [agentsforhumans.devpost.com/rules](https://agentsforhumans.devpost.com/rules) | Build a **new** AI agent with **Strands Agents SDK**; judging: Technical Implementation (Strands use), Design, Impact, Creativity, Presentation; optional AgentCore deploy strengthens score; deadline Sep 14 2026 5pm PDT | High (fetched) |
| [agentsforhumans.devpost.com](https://agentsforhumans.devpost.com/) | 579 participants; $40K; tracks: Everyday Agent / Builder's Companion / Team Multiplier | High |
| [StraVIBE](https://stravibe.vercel.app/) | "Strava for vibe coders" — npm install + login, **token leaderboard**, auto-sync SessionEnd hook, Wrapped-style share cards. Vanity axis = tokens generated | High (fetched) |
| [devcard (augbastos)](https://github.com/augbastos/devcard) | Live embeddable SVG stats card from PostToolUse hooks + git; measures edits not keystrokes; Cloudflare sync | Med (repo page only) |
| [Moltbook](https://www.moltbook.com/) | Agent-only social network; agents auto-post on heartbeat; humans observe. Anti-pattern we reject | High (fetched) |
| Agent Grinder `hack.md` + PRD | Honest metrics from typed turns; human publish gate; grind trace signature drawing | High (ours) |

### Baseline arm (naive competitor any team builds in 2 hours)

**StraVIBE** — install npm package, sign in, get token-count Wrapped card + leaderboard rank. Zero transcript parsing, zero authorship gate, zero grind trace. Wins on friction; loses on honesty and craft signal.

We must beat StraVIBE on *"would you post this"* for a builder who cares about receipts, not on install steps.

---

## Hypotheses (ranked)

1. **The solo grind card is the stranger door.** Almost nobody runs a fleet; `agentgrinder grind` / `demo` must produce a card a cold reader would screenshot. Falsifiable: stranger cold-read says no. Kill: Oscar wouldn't post his own.
2. **Honest-by-construction beats token vanity.** StraVIBE's leaderboard optimizes tokens; we optimize typed turns + commits + grind trace. Falsifiable: judges prefer token leaderboard story. Cost: must show side-by-side cards.
3. **Human publish gate is the anti-Moltbook wedge.** "Agents propose, humans publish" must read in 10s on `/?pitch`. Falsifiable: judges think we're another agent chatter feed.
4. **Stranger pass without keys is the real ship bar.** `pip install -e . && demo && pitch-demo` on empty machine. Falsifiable: pitch-demo exits non-zero without local transcripts (was true on main before tonight's fix).
5. **BLOCKING — Strands Agents SDK eligibility.** Hackathon rules require Strands Agents. Agent Grinder does not use Strands today. Falsifiable: organizer forum says social-layer projects without Strands are disqualified. **Oscar must rule** — options: thin Strands wrapper for ingest/publish, or enter as portfolio piece outside this hackathon.

---

## Refute result (Loop 1 — adversarial, honest)

| Question | Answer | Evidence |
|----------|--------|----------|
| Would a stranger post this vs a terminal screenshot? | **Maybe, not yet proven.** The bundled sample card is polished; a stranger with no Claude sessions only sees sample data — honest but not *their* grind. Terminal screenshot still wins for authenticity until they run a real session. | `demo` renders sample; `grind` needs `~/.claude` |
| Is "agents propose, humans publish" legible in 10s on `/?pitch`? | **Yes.** Pitch view states it in the subhead and demo panel; onboard-agent view has explicit human gate step. | `site/index.html` `viewPitch()` + `viewOnboardAgent()` |
| What embarrasses us if judge runs `pip install -e . && agentgrinder demo`? | **Works** — sample card renders. **Embarrassment:** (a) no Strands Agents anywhere, (b) `flex`/`vibe`/`roast` fail on main without local sessions — **fixed tonight** via sample fallback in `pitch-demo.sh`, (c) OAuth publish path needs Oscar's Supabase redirect URLs. | Stranger pass run 2026-09-02 |
| Does StraVIBE beat us on cold path? | **On friction, yes** — one npm command + login vs pip + (optional) Claude install. **On card honesty, no** — they count tokens; we count typed turns. | Fetched stravibe.vercel.app |
| Moltbook comparison? | We are the inverse: human is the athlete, agent is gear. Strong positioning if judge knows Moltbook lore. | Moltbook fetched |

**Surviving hypothesis:** #1 + #2 + #3 survive. **#5 resolved — MAGNET submits Sep 14; Grinder is product only (EYES panel 1 Sep 2026).**

## Ruling (2 Sep 2026)

| Entry | Role |
|-------|------|
| **MAGNET** (`agents-for-humans`) | Sep 14 Devpost submission — Strands + eval wedge |
| **Agent Grinder** | Product moonshot — stranger would-post, distribution |
| **Hybrid** | Post-Sep 14 — not this week |

**NO NET-NEW collision:** Agent Grinder is distinct from MAGNET (private eval), repo E (ops board), Transcripto (authorship library — we reuse, not rebuild).

---

## BUILD-PLAN (Loop 2 — max 5 slices, risk first)

| # | Slice | Done when | Risk |
|---|-------|-----------|------|
| 1 | **STRANGER-PASS cold path** | `docs/STRANGER-PASS.md` PASS with pasted output | Highest — was failing on `pitch-demo.sh` |
| 2 | Devpost pack | `docs/DEVPOST-READY.md` complete | Strands gap must be disclosed |
| 3 | Share-card WOW path | `docs/FILM-SCOUT-COMMANDS.md` | Film depends on Oscar's machine |
| 4 | OAuth/deploy click-list | `docs/OSCAR-CLICK-LIST-2026-09-02.md` | Oscar only — do not deploy |
| 5 | Hygiene | `pytest tests/test_meme.py` green; `hack.md` NOW = one slice | Low |

---

## OPEN QUESTIONS (not decided — blocking ones stop the phase)

| # | Question | Blocking? | Owner |
|---|----------|-----------|-------|
| 1 | Is Agent Grinder eligible without Strands Agents SDK integration? | **YES for Devpost submit** | Oscar + hackathon organizers |
| 2 | Thin Strands wrapper: ingest CLI as Strands tool vs skip hackathon | YES if submitting | Oscar |
| 3 | Has ≥1 non-Oscar stranger posted a card? | YES for moonshot gate | Oscar recruits |
| 4 | Are `docs/shots/*.png` human-eyeball cleared? | YES for public publish | Oscar |

---

## LOG

| When | What |
|------|------|
| 2026-09-02 LOOP 0 | Fetched Devpost rules, StraVIBE, Moltbook; read hack.md, PRD, pitch doc |
| 2026-09-02 LOOP 1 | Refute: stranger pass failed on main (`pitch-demo` exit 1 at vibe); demo passes |
| 2026-09-02 LOOP 2 | Build plan locked — stranger pass slice 1 |
| 2026-09-02 BUILD | Fixed `scripts/pitch-demo.sh` sample fallback; stranger pass PASS locally |
