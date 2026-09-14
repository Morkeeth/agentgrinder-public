# Grok Bot · Agentic Strava build brief

Paste this task into Grok Bot after granting it access to the public repository:

```text
Build Agentic Strava with us: a free social home for people building with agents. Strava for agents. Cursor first. Build something, post the run, get noticed.

Clone https://github.com/Morkeeth/agentgrinder-public. Read AGENTS.md, PRODUCT.md and CONTRIBUTING.md. Work on a branch in this repo. The original agentgrinder repo and its hackathon deployment are a separate product channel.

Use the contribution selected by the human. If none is selected, your first slice is to make a Cursor builder's first run feel native. Use the existing reader and MCP server. Create one clear capture → private preview → deliberate share flow, with a useful output link and short caption. Keep the white card and blue trace. Profiles, follows, discussion and ACKs carry the social value. Keep it minimal: no coach, practice programme, comparison dashboard, Crews or challenges in the main app. Paid model calls must not be required.

First inspect what already works. Read docs/FIRST-PR.md and use the task the contributor selected; do not run all three. Run python3 scripts/dev.py setup, then python3 scripts/dev.py serve. Run python3 scripts/dev.py check for the contributor checks. Build the selected complete improvement, then open it in your browser and show the resulting flow. Open a PR with screenshots, exact checks, and the remaining independent deployment steps. Do not post on social media, change the hackathon repo, copy its database, or deploy without a separate deployment task.

Do not claim to have captured a Cursor session from my laptop: your cloud machine has different files. Use a deliberately provided safe sample or a real session available on your own machine, clearly labelled. Bot activity is bot activity, not human effort. Do not invent successful runs or engagement.
```

The build brief above remains a handoff for contributing code; it is separate from transcript
capture support.

Agent Grinder now has a native `grokbot` adapter tested against the measured Grok Bot cloud-computer
export format: JSONL records with `user`, `assistant` and `tool` roles and content blocks for text,
tool use and tool results. Use an explicitly provided export:

```sh
python3 -m agentgrinder grind path/to/export.jsonl --harness grokbot
```

For local MCP discovery, place exports deliberately in
`~/.agentgrinder/imports/grokbot/`. This import path does not read sessions from a user's laptop,
and the bot's cloud computer cannot access laptop files. Typed human turns require both
`<timestamp>` and `<user_query>` wrappers; injected turns are excluded. The measured format does
not establish elapsed duration, native file writes or completed commits, so those fields remain unknown. Shell requests do not prove successful commits. Grok Bot
runs are labelled as bot activity. The committed fixture
`samples/sample_grokbot_bot_activity.jsonl` is synthetic sample bot activity, not a real user run.

Cursor documents Grok Bot as a persistent cloud computer with terminal, filesystem and browser: [Grok Bot overview](https://prod.cursor.com/docs/grok-bot), checked 14 September 2026. That supports the repo-building workflow above; it does not establish native Grinder capture compatibility.

## Install and verify the post-run source kit

The reusable [posting skill source kit](../templates/grokbot/INSTALL.md) lives at
`templates/grokbot/post-agent-run/`. Install that complete directory through the current Grok Bot
skill interface so both `SKILL.md` and `scripts/preview.py` remain together. This is a source path,
not a verified marketplace or one-click install.

Always exercise the labelled sample before selecting a real export:

```sh
python3 templates/grokbot/post-agent-run/scripts/preview.py \
  samples/sample_grokbot_bot_activity.jsonl
```

The command prints allowlisted metrics and a private localhost import URL. It performs no network
request and publishes nothing. Next, run the same command against an explicitly selected real
export on the bot's own computer:

`samples/sample_grokbot_safe_real_shape.jsonl` is an additional regression fixture derived from
the supplied description of a real 29-record role/content shape. Its seven prompts, tool inputs,
result bodies, identifiers and paths are replaced with conspicuous `SAFE EXPORT` labels. It
remains labelled sample bot data and is not evidence that a second bot was used.

```sh
python3 templates/grokbot/post-agent-run/scripts/preview.py path/to/selected-export.jsonl
```

Until an approved hosted Agentic Strava URL exists, omit `--base-url` and stop at the localhost
preview. Once the owner supplies an approved HTTPS origin, passing it changes only the import URL;
the owner must still review the card, account and destination, choose an audience deliberately,
and save. Never point the helper at the hackathon service.

Keep the evidence states separate:

- **Source available:** this repository contains the kit.
- **Installed:** a second bot was observed invoking the installed skill.
- **Used:** that bot previewed its explicitly selected real export.
- **Published:** the owner deliberately saved an approved run through an approved hosted account.

Only the first state is established here. Do not describe the source kit or sample run as installed
on a second bot, used on a real export, or published in a marketplace or social product.
