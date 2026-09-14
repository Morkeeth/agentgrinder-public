# Grok Bot · Agentic Strava build brief

Paste this task into Grok Bot after granting it access to the public repository:

```text
Build Agentic Strava with us: a free social home for people building with agents. Strava for agents. Cursor first. Build something, post the run, get noticed.

Clone https://github.com/Morkeeth/agentgrinder-public. Read AGENTS.md, PRODUCT.md and CONTRIBUTING.md. Work on a branch in this repo. The original agentgrinder repo and its hackathon deployment are a separate product channel.

Your first slice: make a Cursor builder's first run feel native. Use the existing reader and MCP server. Create one clear capture → private preview → deliberate share flow, with a useful output link and short caption. Keep the white card and blue trace. Profiles, follows, discussion and ACKs carry the social value. Keep it minimal: no coach, practice programme, comparison dashboard, Crews or challenges in the main app. Paid model calls must not be required.

First inspect what already works. Run the local labelled sample and relevant tests. Build the smallest complete first-run improvement, then open it in your browser and show the resulting flow. Open a PR with screenshots, exact checks, and the remaining independent deployment steps. Do not post on social media, change the hackathon repo, copy its database, or deploy without a separate deployment task.

Do not claim to have captured a Cursor session from my laptop: your cloud machine has different files. Use a deliberately provided safe sample or a real session available on your own machine, clearly labelled. Bot activity is bot activity, not human effort. Do not invent successful runs or engagement.
```

This is a build handoff, not a shipped Grok Bot transcript adapter. The existing parser supports Claude Code, Cursor and Codex. Native Grok Bot capture needs a real exported session format and a separate adapter test before we claim support.

Cursor documents Grok Bot as a persistent cloud computer with terminal, filesystem and browser: [Grok Bot overview](https://prod.cursor.com/docs/grok-bot), checked 14 September 2026. That supports the repo-building workflow above; it does not establish native Grinder capture compatibility.
