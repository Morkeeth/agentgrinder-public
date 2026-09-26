# STRIVE launch, 24 Sep 2026

The launch plan for STRIVE, written before anything is sent. The gate and the kill condition
below are fixed. Do not change them after the result is in.

## 1. The promise

Run one command after a coding-agent session. You get a card of that run: files changed, time,
turns and tool calls, with its activity trace. Nothing leaves your machine until you choose an
audience and press Save run.

The constraint: STRIVE never reads prompts, code or file paths. It counts and times the run only.

## 2. The first ten

Named so far: 1, in row 1 of Oscar's private launch kit. The other nine are the builder club
members Oscar shows STRIVE to on Sunday 27 Sep, plus people Oscar picks himself. Names stay out
of this public repo.

**Open finding:** nine of ten rows have no name yet. The launch skill says to stop when ten
people cannot be named. The Sunday demo is how the list gets filled. Oscar decides whether that
counts.

## 3. Channels, and their state

| Channel | State | Source |
|---|---|---|
| Builder club, in person, Sun 27 Sep | Works. Oscar runs it. | Oscar |
| Direct message to the first named person | Works. Oscar has a direct channel. | Plan B research, 24 Sep |
| X, @morkeeth | `unverified`. Posting was disabled on a dead refresh token on 30 Aug. Probe it before Sunday. | launch skill, 30 Aug |
| The site itself | Works. Prod is still the old UI (024ceab) until tonight's deploy. | Vercel prod, 24 Sep |

## 4. The gate

From Plan B, unchanged. **By 29 Sep 2026 23:59, ten people who are not Oscar have a run in the
STRIVE database.** Today: 0.

The count: distinct profiles with at least one row in `strava.runs`, excluding Oscar's own
profile. The exact query is in Plan B, outside this repo.

Kill condition: **fewer than 3 on 29 Sep 23:59.** Then stop all STRIVE build and distribution,
write the miss on one page, and move the time to other work. 3 to 9: one more week, no new
features. 10 or more: build the cost field.

## 5. The control arm

Two arms, same week. Arm A: the builder club, shown in person, with one ask. Arm B: one X post.
Count the profiles that sign up after each. Tell them apart by the signup time: the club is
Sunday evening, the post goes out Monday. The split is rough. If both arms land in the same
hour, the result cannot say which arm worked.

## 6. Stranger path, run on this branch

Run from an empty `HOME` on macOS. The source was a clone of `origin/main` at 024ceab plus this
branch's diff. The branch is not pushed yet, so the `git+https` install line was not run.
Instead, `uvx --from <that checkout>` stood in for it.

| Step | Result | Time |
|---|---|---|
| `uvx --from <checkout> agentgrinder grind --push` | card written, `preview -> https://agentic-strava.vercel.app/#import=…` printed, nothing uploaded | 2 s, including the build |
| Venv path with macOS system Python 3.9.6 (`pip install -U pip`, `pip install`, `grind --push`) | same output | 13 s, including downloads |
| Open the printed link on prod (read only) | preview renders, button reads Sign in to save, zero non-GET requests | |
| Local build + disposable database: preview, Sign in to save, sign in, create profile, return to the same preview, title kept, Public, Save run | saved; lands on `/?run=<id>` with Copy public link and Open share card | 19 s, scripted |
| Share image for that run (`card()` in `server/public-run.mjs`) | 1200x630 PNG, same card as the preview | |
| Link audience | `readPublic` asks only for `visibility=eq.public` (asserted in `scripts/check-public-preview.mjs`), so a Link run's `/r/<id>` gets the neutral private page and image | |
| 390 px: landing, preview, first-run panel | no horizontal scroll | |
| New account with 0 runs: Post, My runs | first-run panel with one command; My runs says "Your first run starts private" | |
| Broken import link | "This import link could not be read … Nothing was posted." | |

Not exercised: a real GitHub OAuth round trip on prod, and a save to the prod database. Both
would have written a row that counts toward the gate.

## 7. Fixed on this branch

- The feed card is now one card everywhere: feed, import preview, CLI `grind.html` and the share image.
  The Pacecard name is gone.
- `docs/CURSOR.md`: pip upgrade for system Python 3.9, the four real audiences, the sign-in step,
  `--pick 1`, and the printed preview URL (the four Grok stranger blockers).
- `agentgrinder agent --url https://agentic-strava.vercel.app publish` posts to `/api/agent/runs`.
- An unattended run with no typed turns now prints how to capture it.
- `--push` defaults to the hosted app. Before, a stranger's printed link pointed at
  `http://localhost:8000`, which does not exist on their machine.
- The Claude, Codex and Cursor paths all print `preview -> <url>`.
- README opens with "Post your first run": one command, then a venv fallback.
- The site's first-run panel shows the one-line command. Before, it showed
  `python3 -m agentgrinder …`, which fails when the package is not installed.
- A project of `.` shows as empty in the preview.

## 8. Not launch-ready yet

Blockers for Sunday:

1. **Deploy and push.** The README and site command installs from GitHub `main`. It works only
   after this branch is on `main`. Then run
   `uvx --from git+https://github.com/Morkeeth/agentgrinder-public agentgrinder grind --list`
   from an empty `HOME`.
2. **Sign in on prod.** A real GitHub sign-in that returns to the preview is not
   tested. Oscar can test it with his own account and save as Only me. His profile is excluded
   from the count.
3. **Nine unnamed people.** See section 2.

Known and not blocking:

- `main` fails 4 tests plus 1 collection error. CI does not run them, so nobody saw them fail:
  `test_story_contract.py` (missing `supabase/strava/004_shell_calls.sql`),
  `test_grokbot_ingest`, `test_hosted_acceptance` ridge reload, and 2 `test_people_lane` string
  checks. The failures are the same with and without this branch.
- `scripts/check-persisted-journey.py` writes the session under an old storage key, so it never
  signs in.
- A very short run spreads its few tool calls into a flat trace line. The share image then looks
  empty.
- The saved run page shows "0 XUDOS", and the Post page still says "Post a run without a Cursor
  export".
- The landing page on prod shows 1 public run. Post two or three Public runs before Sunday so
  the first screen is not empty.
- The CLI still prints `in .` when a session has no named folder (only the bundled fixture
  does this). The web preview now hides `.`. `test_feed_card_parity.py` does not cover the case.
- The saved run page shows Commits, Files and Session. The card shows files changed, Time, Turns
  and Tool calls. A stranger sees two layouts of the same run.
- Nothing measures the path between visit and save. The SQL count is the only instrument.
