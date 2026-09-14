# Build with us

Eric and new contributors can start here. Use Cursor or hand a task to Grok Bot. The product is small: capture a run, preview it, post it and browse other builders.

## Get running

Install Python 3.9+ and Node 20+. Then:

```sh
git clone https://github.com/Morkeeth/agentgrinder-public.git
cd agentgrinder-public
python3 scripts/dev.py setup
python3 scripts/dev.py serve
```

Open http://127.0.0.1:8000. `serve` needs only Python; `setup` installs test dependencies in `.venv` without changing your global Python. Use `--port 8001` if needed. Stop the server with Ctrl+C.

This opens the local UI. The clone has no working social database yet: sign-in, posting, feed data and replies need independent setup below. You can work on layouts and local capture now. The inherited labelled coaching sample at `/?example` is a development fixture, outside the minimal product flow.

## Cursor

Open this folder in Cursor. The project rule points the agent to the product and contribution instructions. Enable the existing **agentgrinder** MCP server in Customize only if you want local session tools. No MCP setup is required to edit the app.

Ask Cursor: “Read CONTRIBUTING.md and docs/FIRST-PR.md. Help me implement the card contribution. Inspect the code, make the change, run contributor checks and show it in the browser.”

[Cursor details](docs/CURSOR.md) · [Pick a first PR](docs/FIRST-PR.md).

## Grok Bot

Give it this repository URL and [docs/GROK-BOT.md](docs/GROK-BOT.md), plus the specific first contribution you want. Ask it to work on a branch and return a PR with screenshots. Its cloud computer does not have your laptop’s Cursor sessions. Give it safe test data only when needed. A build prompt is included in that file; no special Grok plugin is required for the terminal-based workflow.

## Make a PR

```sh
git switch -c your-name/short-change
python3 scripts/dev.py check
```

Checks cover the Cursor reader, MCP launch and JavaScript syntax. They do not prove hosted sign-in or social behaviour. Open the path you changed in a browser too. Include what changed, screenshots for UI work, and anything not tested.

With repository write access, push your branch and open a PR. Without it, fork the public repo and open a PR from your fork. Do not wait for a collaborator invitation to contribute. Use issues for bugs or larger proposals; small fixes can go straight to a PR. Preserve MIT attribution.

## Where things live

- `site/index.html`: layout, routes, onboarding and run cards.
- `site/social.js`, `site/sharing.js`, `site/progress.js`: social actions, sharing and run history.
- `agentgrinder/ingest.py`, `agentgrinder/mcp_server.py`: local capture and agent tools.
- `server/public-run.mjs`: public link previews.
- `PRODUCT.md`: the agreed product scope.

Older hackathon docs and receipts are historical. Use the current product brief; do not reopen the coach/practice feature set by following old checklists.

## Independent deployment

Create a separate Vercel project and Supabase project. Use `scripts/migration-order.txt` to inspect migration order. Configure browser constants in `site/index.html`, server values in `server/public-config.json`, and origin in `server/public-run.mjs`. CLI/MCP clients accept `AGENTGRINDER_URL`, `AGENTGRINDER_SUPABASE_URL` and `AGENTGRINDER_SUPABASE_ANON_KEY`.

The checked-in `local-development-only` key is not a working credential. Do not reuse the hackathon database, accounts or deployment. Keep local transcripts, generated cards and secrets out of commits. Independent hosting and social acceptance remain pending.
