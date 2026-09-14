# Agent Grinder

**Strava for agents. Build something. Post the run. Get noticed.**

A free, open-source social home for people building with coding agents. Cursor first: turn a real session into a card, share what shipped, follow other builders and give credit for work you like.

The product loop is **build → preview → post → get a response → build again**. Run cards are the signature. Profiles, follows, discussion and ACKs make them social. Coaching is optional.

## Two repositories

- [agentgrinder-public](https://github.com/Morkeeth/agentgrinder-public): the independent free product and collaboration home.
- [agentgrinder](https://github.com/Morkeeth/agentgrinder): the hackathon build, judging material and competition deployment.

Branched from hackathon main `5828f39ec4cfeaa63c1cc53e3acdc92589a2ca1a`. History and MIT attribution are preserved. This repository has no independent hosted service yet. Runtime defaults point to localhost, not the hackathon database. Older docs and screenshots describe the source release.

## Start in Cursor

```sh
git clone https://github.com/Morkeeth/agentgrinder-public.git
cd agentgrinder-public
python3 -m agentgrinder grind --harness cursor
```

Python 3.9+; local capture needs no API key. If there is no supported session, run `python3 -m agentgrinder demo` for the labelled sample.

Open this folder in Cursor. Enable the project MCP server from Customize. It exposes local run previews through the existing Python server. [Cursor setup](docs/CURSOR.md) explains the boundaries and the first tool call.

## Build together

Read [PRODUCT.md](PRODUCT.md) for direction, [CONTRIBUTING.md](CONTRIBUTING.md) for setup, and [the Grok Bot brief](docs/GROK-BOT.md) for a bounded first build.

**Working inheritance:** local readers, cards, MCP, web social features and optional coaching. **New here:** separate repository, public-product brief, Cursor config and isolated runtime defaults. **Still to do:** independent hosting/database, a real Cursor onboarding pass, and a Grok Bot run. No independent adoption is claimed.

Free means no mandatory paid model or subscription for capture and sharing. Optional model calls can still have provider costs. Recognition must come from people responding to real work; activity counts are not a universal quality score.

MIT licensed. [Inherited technical reference](docs/TECHNICAL-HISTORY.md).
