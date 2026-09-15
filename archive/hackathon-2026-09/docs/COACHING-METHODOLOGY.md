# AGENT GRINDER — coaching methodology (science-based, cited)

The coach earns trust the same way the rest of the product does: **every recommendation is either a
verified fact about your own history, or a documented best-practice with a source.** No invented
scores, no fake precision. If we can't ground it, we don't say it.

## Three tiers of what the coach may say
1. **VERIFIED (your own object).** True facts re-derivable from your local transcripts: real ranks
   (longest focus session #2 of N), real counts (47 prompts, 3 commits), real ratios. Cross-checked
   against ground truth (see VERIFICATION-2026-08-30.md).
2. **GROUNDED + CITED (documented practice).** Best-practices from top agentic engineers, each with a
   source. Applied to a *detected characteristic* of your session.
3. **DESCRIPTIVE (labelled as such).** Real ratios stated plainly ("11 tool calls per prompt"), never
   dressed as a verdict.

Explicitly retired: the arbitrary "grind score" formula and threshold labels (deep focus / explorer).
They were manufactured rigor. Replaced by the checklist below.

## The cited best-practice checklist (what we detect + why)
| Characteristic (detected locally) | Recommendation | Source |
|---|---|---|
| No CLAUDE.md / .cursor/rules / AGENTS.md in the project | Add a rules/context file - the highest-ROI fix | Karpathy's CLAUDE.md rules cut agent mistakes ~41%->11% (aibuilderclub.com/blog/karpathy-claude-md-rules) |
| High tool activity, 0 commits / no ship | Verify and ship, don't just run | "agentic engineering" = explicit objectives + verification loops, vs "vibe coding" (futureproofing.dev, community consensus 2026) |
| Session sprawls across many regions, low depth | One bounded objective per session | Karpathy's rules era = single-session, one task at a time (aibuilderclub) |
| Very low human-in-the-loop ratio | Keep pointing and catching wrong assumptions | Karpathy: shifted to ~80% agent / 20% human edits, human still sets direction |

## What we CANNOT do (and won't fake)
- Compare your metrics to a top engineer's **session metrics** - those are private; nobody has them.
  Any "beat Karpathy's cadence" would be fabricated. Banned.
- Quote a number from a practitioner without its source and date. Verify before quoting.

## Sources to expand (verify each claim at source before quoting a figure)
- Andrej Karpathy - CLAUDE.md rules, the 80/20 shift, single-task sessions.
- Simon Willison - documents his agent workflow + tooling in depth.
- swyx / Latent Space - "agentic engineering" framing.
- Claude Code & Cursor official guidance - verification loops, rules files.

## Honest limits
Rules-file detection needs the session's cwd to be the real project (home-dir sessions read as "no
project"). Verify-vs-ship uses commits as the ship proxy (a PR without a local commit is missed).
Both undercount, never overclaim.
