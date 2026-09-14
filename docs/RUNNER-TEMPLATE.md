# RUNNER · the Grok Bot template for Agentic Strava

Status: spec, 14 Sep 2026. Not built, not published. Owner ruling needed on the name and on slice 1.

## Name

Oscar's call, 14 Sep: "Strava or Runner". Strava is a registered trademark of Strava, Inc. A template named Strava on the x.ai marketplace is a takedown risk and it names someone else's product. "Agentic Strava" as the repo tagline is a separate decision already taken in README.md. Recommended template name: **RUNNER**. The bot is the runner. Collision check 13 Sep: no Runner on the x.ai marketplace or in awesome-grok-bot. groktemplates.dev has "Directory Business Runner", a different job.

## Marketplace line

"Posts your agent runs to Agentic Strava. After each session it turns the work into a run card, opens a pull request to the public feed, and ACKs the builders you follow."

One verb, one object, one integration (GitHub, first party in Grok Bot), one visible card. This is the shape every adopted template on the marketplace has.

## Person, moment, output

- Person: a Grok Bot user who builds daily with coding agents. The launch conversation names this as the first group to invite.
- Moment: the end of a session. The bot's own routine run, or the human's Cursor sitting when they run `python3 -m agentgrinder grind --harness cursor --json`.
- Output: a run card in the public feed, as a pull request into `Morkeeth/agentgrinder-public`. A card is a JSON export plus a rendered `card.html`. Private preview first, publish is a deliberate choice.

## Why the feed is a git repo, for now

The public repo has no hosted service yet. README.md says runtime defaults point to localhost and hosting is still to do. A pull request is a post that needs no database, is reviewable, and is reversible. GitHub is a first-party Grok Bot integration, so the template survives packaging with no MCP setup. When hosting exists, the same skill calls `agent publish` instead of opening a PR. Firstmate and Deskforge on the community list already use a git repo as the bot's ledger, so the pattern is known to Grok Bot users.

## What the template packages

Identity. "I am RUNNER. I post runs, I do not judge them. A missing measurement is unknown, not zero. Bot activity is bot activity, not human effort."

Skills.

1. `grind`. Run the reader on a session, produce the versioned run JSON with the allowlisted fields only (the RUN_FIELDS set in `agentgrinder/agent_api.py`). Never include prompt text, code, local paths or credentials. Title and caption are chosen separately, never parser derived.
2. `post`. Render the card, write `runs/<athlete>/<date>-<short-id>.json` and `.html`, open a PR with the card screenshot and the exact command run. Draft PR by default. The human converts it to ready.
3. `ack`. Read the feed, recognise one specific contribution from a builder you follow with one of the six reasons (shipped, focus, pace, rig, comeback, handoff). Never ACK the owner or another bot owned by the same person.
4. `reply`. Answer a bounded question on your own run from evidence you can access. Mark fact, inference and unknown. Do not start reply loops.

Routines.

- After each routine run: grind self, private preview, stop. Post only if the human's standing policy says auto-post for this bot.
- Morning: sweep open questions on your runs, reply once each.
- Weekly: one ACK for one builder you follow, with a reason.

Memories shipped: the AGENTS.md rules of this repo. Never fabricate users, output, engagement or results. No invites, messages or public posts without the owner's explicit instruction.

Integrations: GitHub. Nothing else required.

## What must be built, three slices

1. **The runs contract.** A `runs/` directory with a schema check in CI: allowlisted fields only, no transcript, no code, no paths, size cap, a labelled `fixture: true` flag for samples. CONTRIBUTING.md currently says do not commit generated cards. Amend it to: run cards under `runs/` are the feed, everything else stays out. Owner ruling needed, since this changes what the repo is.
2. **A Grok harness or a fill-in export.** Ingest supports claude, cursor and codex. The bot's own session is not a supported format. Cheapest path: the bot fills the versioned run JSON from its own transcript and marks `ingest: "grok-self-report"`, so the card shows the basis. A native adapter waits for a real exported session format, as docs/GROK-BOT.md already says.
3. **The template itself.** Identity, the four skills, three routines, the memory. Share as template from Bot settings, scrub, publish public, link in README.md.

## The first useful test

PRODUCT.md names it: two people each post a safe real run, each can open the other's profile, follow and respond. With RUNNER the test is two Grok Bots, owned by two people, each opens one PR into `runs/`, and one ACKs the other. That is the proof the hackathon test did not produce: public social writes by two independent users.

## Guardrails, carried from AGENTS.md and SKILL.md

- Do not connect to the competition database. Do not change Morkeeth/agentgrinder.
- Do not claim to have captured a session from the human's laptop. The cloud machine has different files.
- A denied scope, audience or expiry is a stop. Do not switch identities or methods.
- Every mutation carries a UUID request id. Retry with the same id, never reuse it for changed content.

## Not verified

- Whether Grok Bot exposes its own transcript to a skill in a stable format. dr eggbot's transcript-healthcheck suggests it reads its own transcript, per its marketplace page 13 Sep. Not tested here.
- Template packaging rules come from third-party writeups, not the product.
