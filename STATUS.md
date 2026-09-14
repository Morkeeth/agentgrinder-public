# STATUS · Strava account control and sign-in recovery lane

Branch `codex/strava-account-recovery-20260914`, worktree `.worktrees/strava-account-recovery-20260914`.
Baseline main `503bf7e`.

## 2026-09-14 · start

- Baseline checks run in this worktree: `npm run test:identity` PASS (sql + auth.js); `python3 -m pytest -q` 318 passed, 1 skipped.
- Fleet ACK for rev e2daf56ba4f1 with session 8e7f7127-f57d-4355-ac26-04c3674ba5b5 rejected as unregistered. Recorded once, not retried.
- Trace: `site/auth.js` already has link/unlink/signOutLocal/deleteProfile. `site/index.html` has an empty `#linked-accounts` placeholder in the profile edit panel, a footer delete link using `confirm()`, and `authErrorFromUrl()` that only reads the query string. No account route, no recovery for a cancelled provider round trip, no linked-provider UI.
- Plan: additive `auth.js` (URL error recovery, pending sign-in memory, extra error codes), new `site/account.js` + `site/account.css` (`?account` panel), Node + Python tests, Playwright walk against the disposable harness, RETURN.md with shell hooks for root.

## 2026-09-14 · checkpoint: panel walks

- Commit `e3a9e4c`: auth.js recovery additions, site/account.js + account.css, disposable shim auth endpoints, browser walk, Node and Python tests, screenshots.
- `scripts/check-account-loop.py`: 43 checks pass (cancel, failure, pending, duplicate handle with free variant, unlink, server last-identity refusal, isolated deletion with Grinder snapshot, local sign-out scope, menu and footer hooks).
- Full suite: pytest 326 passed 1 skipped; test:identity, test:account, test:journey, people loop, social loop (with CHROME_BIN), dev.py check all pass.
- RETURN.md written with the eight index.html hooks for root. Next: receipt commit, push, draft PR, final advisor review.
