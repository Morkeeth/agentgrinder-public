# Five first contributions

Each of these fits in about 30 minutes, needs no database and no account, and ends with a PR. They are not yet open on GitHub; a maintainer will open them as issues, or you can open one yourself and start. Check [open issues](https://github.com/Morkeeth/agentgrinder-public/issues) first so two people do not do the same one.

Run `python3 scripts/dev.py setup` once, then `python3 scripts/dev.py check` before you push. See [CONTRIBUTING.md](../CONTRIBUTING.md) for branches and the PR template.

## 1. Add a skip-to-content link

Files: `site/index.html` (the primary `<nav id="nav">` at line 379 and `<main id="app">` at line 408).

The page has no skip link, so a keyboard user tabs through every nav item before reaching the feed. Add a visually hidden link as the first focusable element that becomes visible on focus and moves focus to `#app`.

Done when: on a fresh load, one press of Tab shows a "Skip to content" link; Enter moves focus into the main area; the link is invisible when not focused at desktop and phone widths; `python3 scripts/dev.py check` passes.

## 2. Make the local serve message point at the hosted app

Files: `scripts/dev.py` (the `serve` command, around line 73).

`serve` prints `No hosted database configured.` That was true before the app was hosted. The local shell still has no database, but the hosted app now exists at https://agentic-strava.vercel.app.

Done when: `python3 scripts/dev.py serve` prints the local URL, says the local shell has no database, and names the hosted URL for sign-in and posting; the line is under 120 characters; `check` passes.

## 3. Document what local capture writes

Files: `docs/CURSOR.md`, `README.md` (the capture section), `agentgrinder/cli.py` (the `--no-series` flag, around line 161).

`python3 -m agentgrinder grind --harness cursor` writes `./grind.html` and records counts in `~/.agentgrinder/series.db` in the home directory. README says so; `docs/CURSOR.md` does not mention either file or the `--no-series` flag.

Done when: `docs/CURSOR.md` names both paths and the flag in the capture walkthrough, the wording matches the `--help` output of the command, and the README and CURSOR.md sentences agree.

## 4. Add the `api/` folder to the code map

Files: `CONTRIBUTING.md` (section "Code map"), `api/health.js`, `api/run.js`.

The code map lists `site/`, `agentgrinder/`, `server/` and `scripts/` but not `api/`. `api/health.js` answers `/api/health` with `{"service":"strive","database":"ready"}` or `"unavailable"` with status 503. `api/run.js` serves a public run as an HTML preview page, or as a 1200 by 630 PNG when `image=1`, and a plain-text 404 when the run is not public.

Done when: the code map has one line per file in `api/` that says what each endpoint returns, and the sentence about `/api/health` matches the JSON the handler writes.

## 5. Ask bug reporters where they saw it

Files: `.github/ISSUE_TEMPLATE/bug.md`.

The bug template does not ask whether the problem happened on the hosted app or on a local checkout, or at which commit. Maintainers need that to reproduce.

Done when: the template has one line asking "Hosted app (agentic-strava.vercel.app) or local checkout? If local, the commit from `git rev-parse --short HEAD`", the template still renders as a GitHub issue template, and the rest of the template is unchanged.
