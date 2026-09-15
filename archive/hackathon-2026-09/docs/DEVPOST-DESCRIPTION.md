# Agent Grinder

Draft for the Agents for Humans submission. One entry; MAGNET is the disclosed engine library.

## Tagline

Record your agent work. Share the moment. Try a better next run.

## The problem

People who build with coding agents finish a session with a transcript, some changed files, and a feeling about how it went. It is hard to show the work worth sharing or carry a useful technique into the next session. An agent saying “done” does not settle what happened.

## What it does

Agent Grinder is a social training log for agent work: record, flex, improve. It reads supported coding-session transcripts locally and separates human turns from tool results and agent-injected context. The optional grind coach checks claims and artifacts through Strands tools and refuses a verdict that disagrees with their returned counts.

A builder can attach an authored moment to a measured run: what happened, an exact evidence reference and excerpt, a limit on the claim, and one thing to try next. Those fields follow the run’s audience. The builder reviews the selected text before saving or exporting a share card; raw transcripts are not uploaded by this flow.

Another signed-in builder can keep the technique as a private practice, choose a measured run of their own as the frozen baseline, and return with a later session. The comparison uses their own two sessions. Missing measurements remain unknown. A keep, change, drop, or incomparable decision is the participant’s observation, not proof of causation. If the original builder removes access, the source stops resolving while the reader’s own practice and review remain.

## Why Strands is here

The coach uses the Strands agent loop, tool registry, dispatch, and after-tool hooks. Its tools read the run, check claims, inspect artifacts and Git evidence, and write a constrained verdict. In the keyless path, a scripted local model supplies the plan; it is not an LLM choosing tools. Bedrock mode is implemented as an opt-in provider. We do not claim a current live Bedrock run of the Grinder integration.

## What has been tested

On the September 10 local candidate, the browser journey covers authored moment, reviewed image export, frozen practice baseline, later return, and another reader keeping a practice. These are labelled controlled accounts and responses. Separate PostgreSQL/PGlite checks execute the real migrations and access rules, including a refused attempt to substitute someone else’s baseline and a refused retry with a changed baseline.

The coach runs on the bundled sample through the real Strands loop. The refusal demonstration offers inflated counts and receives a rejection. The sample is demonstration data. We have not established independent adoption, retention, or improved productivity.

## Current availability

The hosted site exists, but the September 10 read-only probe found the moments script and the moments/adoption database tables unavailable there. The shared-moment practice journey described above is runnable on the local candidate and is not yet a hosted release. Judge instructions must match the final released revision. See `docs/DEADLINE-READINESS-2026-09-10.md` for the exact boundary.

## Pre-existing code, disclosed

The rules ask for work built inside the submission period, 10 August to 14 September 2026, and for
any other pre-existing code to be disclosed. This repository was created on 31 August 2026. Three
pieces of it did not start life here:

- **`agentgrinder/authorship.py` is vendored from Transcripto**, an earlier project by the same
  author. It is the rule that decides which `type: "user"` records a person actually typed, and it
  is named at the top of the file.
- **The coach scaffolding in `agentgrinder/coach/`** (the agent creation shape, the scripted local
  model that replays a plan through the real Strands event loop, and the three-mode dispatch with
  the DEGRADED banner) is lifted from
  [Morkeeth/agents-for-humans](https://github.com/Morkeeth/agents-for-humans), the same author's
  MIT repository, built from 29 August 2026 onwards, inside the submission period. The five coach
  tools, the refusal and the verdict are new here. That repository does not enter this hackathon;
  it is used as a disclosed engine library only.
- **The per-project series logic in `agentgrinder/engine/`** (a verdict over a series of readings,
  `baseline` under two readings) comes from the same repository, which itself ported the stack
  logic from [Morkeeth/mountain-of-helicon](https://github.com/Morkeeth/mountain-of-helicon), also
  the same author, written before the period.

Everything else in this repository was written inside the period. The Strands Agents SDK is a
dependency, not copied code.

## Built with

Python, Strands Agents SDK, JavaScript, PostgreSQL/Supabase, SQLite, Vercel. Amazon Bedrock is an optional provider implementation, not a claimed current live demonstration.
