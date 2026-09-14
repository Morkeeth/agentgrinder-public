# Agentic Strava

**Post your agent runs. See what other people are building.**

A free, MIT-licensed social app for people building with coding agents. Capture a session, preview its card, choose to post it, and follow other builders. Keep it minimal: runs, a feed, profiles, ACKs and replies.

**Come build it with us.** Code, design, documentation, accessibility improvements and useful bug reports are all welcome. You do not need an invitation, a paid AI tool or a previous open-source contribution.

[Start contributing](CONTRIBUTING.md) · [Find a first contribution](docs/FIRST-PR.md) · [Get help](SUPPORT.md) · [Product direction](PRODUCT.md)

## Run it locally

Python 3.9+ runs the local app. Node 20+ is needed for contributor checks.

```sh
git clone https://github.com/Morkeeth/agentgrinder-public.git
cd agentgrinder-public
python3 scripts/dev.py serve
```

Open http://127.0.0.1:8000. To install the test tools and check a change:

```sh
python3 scripts/dev.py setup
python3 scripts/dev.py check
```

**Current status:** local capture, cards and UI are available. This public repo does not yet have its hosted Strava schema or service. Sign-in, public posting and social interactions need that setup. The localhost defaults stay offline from production. The approved deployment shares Supabase Auth and infrastructure with Grinder, using a separate `strava` schema for all app data.

## Build in Cursor or Grok Bot

Cursor and Grok Bot are our first documented agent workflows. Any editor or terminal works too.

- **Cursor:** open the folder and follow the private-by-default [Cursor capture walkthrough](docs/CURSOR.md): enable the workspace MCP, inspect `a2a_onboard`, preview the Cursor harness, then open the localhost card before choosing any audience.
- **Grok Bot:** give it the repository and [build brief](docs/GROK-BOT.md), choose one task, and ask it for a reviewed PR. Its cloud computer cannot read sessions on your laptop. The [post-run kit](templates/grokbot/INSTALL.md) is source to install and verify, not evidence of a second-bot install or publication.
- **Without an agent:** use the same setup, branches and checks in [CONTRIBUTING.md](CONTRIBUTING.md).

To capture your own Cursor session locally:

```sh
python3 -m agentgrinder grind --harness cursor
```

No model API key is required for local capture. Review generated cards before sharing. A sample can help with development; it must stay labelled as sample data.

## What help matters now?

Make first-run instructions easier, improve the card on a phone, test keyboard access, report a reproducible bug, or help connect the independent social preview. [First contributions](docs/FIRST-PR.md) give starting files and a clear outcome. [Open issues](https://github.com/Morkeeth/agentgrinder-public/issues) show reported work; check before starting something large.

Small fixes can go straight to a PR. Discuss new features in an issue first. Contributors review their agent-generated changes and explain what they tested. [Maintainer process](docs/MAINTAINING.md) explains how changes are triaged and reviewed.

## Scope and origin

The main loop is **capture → preview → post → browse**. Coaching programmes, comparison dashboards, Crews and challenges are outside the main app. Free posting and browsing must not require paid inference.

This project started from [the separate Agent Grinder hackathon repo](https://github.com/Morkeeth/agentgrinder) at `5828f39ec4cfeaa63c1cc53e3acdc92589a2ca1a`. History and attribution are preserved. Historical docs and screenshots describe that source release, not a new hosted service. [Technical history](docs/TECHNICAL-HISTORY.md).

[MIT license](LICENSE). Contributions are distributed under the same license.
