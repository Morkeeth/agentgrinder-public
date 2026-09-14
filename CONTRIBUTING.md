# Contributing

Work on a branch and open a PR against this repository. Preserve the MIT license and inherited attribution. The original hackathon repo is a separate release channel.

## Local setup

Python 3.9+ runs the local reader. For tests: `python3 -m pip install -e '.[dev]'` in a virtual environment, then `python3 -m pytest tests/test_agent_mcp.py tests/test_cursor_headline.py`.

Serve the web source with `python3 -m http.server 8000 --directory site`. The labelled example is `http://localhost:8000/?example`. Social storage requires a separately configured Supabase project; it is not provisioned by cloning. The placeholder key `local-development-only` is deliberately not a working credential.

## Independent deployment setup

Use a new Vercel project and a new Supabase project. Apply the inherited schema/migrations in dependency order. Configure the browser constants in `site/index.html`, server values in `server/public-config.json`, and server origin in `server/public-run.mjs`. Supply `AGENTGRINDER_URL`, `AGENTGRINDER_SUPABASE_URL`, and `AGENTGRINDER_SUPABASE_ANON_KEY` to CLI/MCP clients. Never reuse the hackathon database or copy its account rows. Deployment and hosted acceptance are still pending.

Do not commit local transcripts, generated cards, secrets or personal notes. Use labelled disposable fixtures in tests. Show the changed user path and report what you actually ran in each PR.

Legacy hackathon docs and tests remain as history/reference; some assert the original deployment or navigation. Adapt only tests related to the current change and distinguish historical receipts from new verification.
