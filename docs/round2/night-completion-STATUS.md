# STATUS · Strava completion lane (night run 14–15 September)

Branch `codex/strava-night-completion-20260914`, worktree `.worktrees/strava-night-completion-20260914`.
Baseline main `dad083e` (merge of PR #14). Read `FINAL-REVIEW.json` (restart-2030) first.

## 2026-09-15 · start

- Fleet ACK for rev e2daf56ba4f1 rejected as unregistered (this session). Recorded once, not retried.
- `python3 scripts/dev.py setup` completed in this worktree (venv + npm).
- Identity, people, account recovery and Responses return are complete on main (FINAL-REVIEW.json R2-01..03 fixed). Not rebuilt here.
- Trace of the capture > preview > post path as committed (`site/index.html` importRun, `site/social.js` thread):
  - G1 A failed or offline save shows raw backend text or a one-line status that tells the person to check Your runs themselves. There is no retry affordance and no duplicate guard: if the insert landed but the response was lost, a second Save creates a second run.
  - G2 An exact-reply deep link ranked past 40 pages (1000 replies) is reported removed even though the id lookup found it (documented INT-05 cap).
  - G3 The preview does not say, in words, what the export contains at the bytes: the project folder name, counts, timing, trace, coach sentences, rig counts; MCP names only when ticked.
  - G4 A comment in importRun promises a retry without coach columns that does not exist (`unsaved=''`). The strava first-install schema has those columns (`supabase/strava/base.sql`).
- Plan: fix G1 with a pre-insert lookup keyed on the capture's measurement revision (or started time + harness), an inline recovery panel with an explicit Try again button and a Your runs link, no automatic retry; fix G2 by rendering the found reply directly above the thread when paging stops short; fix G3 with a contents line pinned to `agentgrinder/push.py`'s allowlist by a test; delete G4's dead comment. Prove all of it with a disposable browser walk (`scripts/check-post-recovery.py`) and phone screenshots, then a draft PR and a 5-minute stranger script.

## 2026-09-15 · checkpoint: fixes proven

- Commit `665067c`: G1 (recovery card, one run per capture, lost-response retry finds the row), G2 (direct render past 12 pages, cap lowered from 40), G3 (export contents line pinned to push.py allowlist), G4 (dead comment gone), G5 (chopped link named).
- `scripts/check-post-recovery.py` 28/28, artifacts `/tmp/agentic-strava-post-recovery`, eight phone screenshots inspected and copied to `docs/round2/screens/completion/`. First runs found two walk bugs, not product bugs: the fixture seeds one run for Casey (now excluded), and page one plus 12 pages is 325 so the target must sit past 325 (331 seeded).
- pytest 347 passed 1 skipped (baseline in this worktree before changes: 322 passed 6 skipped, with the six skips from a venv without playwright; system python3 has it). round2 walk 40/40, response-return pass, social loop pass, `dev.py check` pass.
- Next: stranger script, push, draft PR, NIGHT-RETURN.md.

## 2026-09-15 · completion

- Review pass added: the export line now names the reach sentence, stack notes and the route as numbers (probed with `export_run` on `samples/sample_run.json`); the walk proves the start time + harness dedupe fallback on an export without a measurement revision, and Back to Responses on the direct reply card. All eight screenshots read one by one.
- Walk 29/29 · pytest 347 passed 1 skipped · round2 walk 40/40 · response-return · social loop · `dev.py check` all pass at the final head.
- Draft PR #15 open, not merged, not deployed. NIGHT-RETURN.md written.
