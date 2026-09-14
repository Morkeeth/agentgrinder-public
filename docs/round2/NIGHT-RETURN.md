# NIGHT-RETURN · Strava completion lane · 2026-09-15

**Baseline** main `dad083e` (PR #14 merged). FINAL-REVIEW.json (restart-2030) read first; identity, people, account recovery and Responses return left as they were.

**Commits** on `codex/strava-night-completion-20260914`: `9307450` STATUS · `665067c` product change · stranger script + checkpoint. **Draft PR #15** https://github.com/Morkeeth/agentgrinder-public/pull/15 (not merged, not deployed).

## What changed for the person posting a run

| Gap | Before (main `dad083e`) | Now |
|---|---|---|
| Offline / failed save | raw backend text or "check Your runs before retrying"; second Save could make a second run | inline **Not saved** card: reason, nothing posted, draft kept, **Try again** (their click) and **Your runs**; no auto-retry |
| Same capture twice | second row | lookup by measurement revision (or start + harness) before insert and on 23505; existing run opens, caption not applied is said |
| Insert landed, response lost | duplicate on retry | Try again finds the saved run |
| Rig update fails after save | read as failed save | run opens; note says rig counts not updated |
| What the export contains | only a JSON dump behind a disclosure | one line in words, pinned to `push.py` allowlist by test |
| Chopped import link | silent landing page | "This import link is incomplete", nothing posted |
| Exact reply past cap | "removed" (dishonest) | rendered directly from the id lookup; cap 40 → 12 pages |
| Reply the lookup cannot see | "removed or no longer available" | "removed or not visible to you" |

## Tests

- `scripts/check-post-recovery.py` 28/28 (new; disposable PGlite, TEST DATA, phone viewport, POST counter proves no silent retry).
- pytest 347 passed 1 skipped (baseline here 322/6 skipped, venv lacked playwright; system python3 has it).
- `check-round2-integration.py` 40/40 · `check-response-return.py` pass · `check-social-loop.py` pass · `dev.py check` pass.
- Eight screenshots inspected by eye and committed under `docs/round2/screens/completion/`. Two walk-side fixes during the night: fixture seeds one Casey run (excluded from counts); 12 pages after page one is 325, so the deep target is seeded at 331.

## Actual user outcome

None with a real person. Everything above is local disposable data. No hosted OAuth, no consenting user, no production write, no shared Auth change.

## Known limits

- Manual post form (`wireComposer`) has no duplicate guard: no natural key. Out of this journey.
- Exports without `measurement_revision` and without `started`+`harness` (schema_version 0 without a start) cannot be deduplicated; the recovery card says so and points to Your runs.
- Direct render shows the reply out of sequence; earlier replies around it are not loaded.
- Fleet ACK rejected as unregistered (session 080cddbb); reported once.

## Exact next step

Coordinator reviews PR #15. If accepted, merge to main; no deploy from this lane. Then run `docs/round2/STRANGER-TRIAL-5MIN.md` with one person who is not Oscar.
