# Pacecard

**Every run your agent made, on a card you can share.**

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

**Current status:** the app is live at [agentic-strava.vercel.app](https://agentic-strava.vercel.app). Sign in with GitHub or an email link, post a run, follow people and reply. The feed is new and mostly empty; the first runs you see may be your own. Local capture works offline with no account. This checkout defaults to localhost and does not connect to the hosted database unless you configure it. The hosted app runs on Vercel with a Supabase `strava` schema; see [CONTRIBUTING.md](CONTRIBUTING.md) for the setup notes.

## Build in Cursor or Grok Bot

Cursor and Grok Bot are our first documented agent workflows. Any editor or terminal works too.

- **Cursor:** keep your own project open and follow the [Cursor capture walkthrough](docs/CURSOR.md). Install the capture tool separately, confirm the selected project/session, then open its private preview at the hosted app.
- **Grok Bot:** explicitly select a JSONL export on the bot’s computer and use the [post-run kit](templates/grokbot/INSTALL.md) to open the same hosted private preview. It cannot read sessions on your laptop. Bot activity and samples stay labelled; nothing auto-publishes.
- **Without an agent:** use the same setup, branches and checks in [CONTRIBUTING.md](CONTRIBUTING.md).

After the one-time setup in the walkthrough, capture a selected Cursor sitting from your own
project and open the live private preview:

```sh
AGENTGRINDER_URL=https://agentic-strava.vercel.app \
~/.agentgrinder/venv/bin/agentgrinder grind \
  /exact/path/to/selected-cursor-session.jsonl \
  --harness cursor --pick 1 --push
```

No model API key is required. The command reads that session on this machine, writes
`./grind.html`, and opens an unsaved metrics-only import. Review the card, account and destination;
choosing an audience and pressing **Save run** are deliberate later actions.

## What help matters now?

Make first-run instructions easier, improve the card on a phone, test keyboard access, report a reproducible bug, or improve the empty states a new user meets in a feed with few runs. [First contributions](docs/FIRST-PR.md) and [issues to open](docs/ISSUES-TO-OPEN.md) give starting files and a clear outcome. [Open issues](https://github.com/Morkeeth/agentgrinder-public/issues) show reported work; check before starting something large.

Small fixes can go straight to a PR. Discuss new features in an issue first. Contributors review their agent-generated changes and explain what they tested. [Maintainer process](docs/MAINTAINING.md) explains how changes are triaged and reviewed.

## Scope and origin

The main loop is **capture → preview → post → browse**. Coaching programmes, comparison dashboards, Crews and challenges are outside the main app. Free posting and browsing must not require paid inference.

This project started from [the separate Agent Grinder hackathon repo](https://github.com/Morkeeth/agentgrinder) at `5828f39ec4cfeaa63c1cc53e3acdc92589a2ca1a`. History and attribution are preserved. Hackathon docs and screenshots live under `archive/hackathon-2026-09/` and describe that source release, not this service. [Technical history](docs/TECHNICAL-HISTORY.md).

[MIT license](LICENSE). Contributions are distributed under the same license.
