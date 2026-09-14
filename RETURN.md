# RETURN: response > return lane

**Branch:** `codex/strava-response-return-20260914`
**Baseline:** `503bf7e` (main after PR #10)
**Commit:** `f04115a`
**Draft PR:** https://github.com/Morkeeth/agentgrinder-public/pull/11
**Owner files:** `site/social.js`, `site/people.js`, `site/social.css`, `tests/test_response_return.py`, `tests/test_social_product_loop.py`, `scripts/check-response-return.py`

## What shipped

Phone-friendly Responses inbox with All / Unread filters, blue unread trace on white cards, viewed-only read marking via IntersectionObserver (no bulk mark-all on open), exact reply deep links (`/?run=&reply=#reply-`), Back to Responses return context, deleted-reply and missing-run messaging, blocked-target denial, and unread badge updates from `social.refreshUnread()`.

## Observed user path (disposable TEST DATA)

1. Casey posts a public run.
2. Riley ACKs and replies.
3. Casey opens Responses: both items listed; Open exact reply points at the reply id.
4. Casey opens the exact conversation; reply is focused; Back to Responses returns to inbox.
5. Riley deletes the reply; Casey deep-link shows that the reply was removed or is no longer available.
6. Private/missing run for Riley shows the existing denial copy.
7. Casey blocks Riley; Riley cannot post another reply on Casey's run.

## Tests run

- `python3 scripts/dev.py check`: passed
- `pytest tests/test_response_return.py tests/test_social_product_loop.py`: 7 passed
- `python3 scripts/check-response-return.py` (PGlite + mobile Chromium): passed; artifacts under `artifacts/response-return/`

## Screenshots inspected

- `artifacts/response-return/inbox-unread-mobile.png`: Responses list, All/Unread, Open exact reply
- `artifacts/response-return/exact-reply-return-mobile.png`: exact conversation + Back to Responses
- `artifacts/response-return/deleted-reply-mobile.png`: removed-reply notice
- `artifacts/response-return/private-or-missing-mobile.png`, `blocked-profile-mobile.png`, `reply-mobile.png`

## Shell integration for Codex (do not edit `site/index.html` here)

Wire these in the app shell when integrating:

```js
// After ME resolves / on each successful route():
if (ME && social.refreshUnread) social.refreshUnread();

// When viewRun finds no row, keep return context:
// if sessionStorage ag_response_return === '?inbox', show
// <a href="/?inbox">Back to Responses</a> on the private/missing empty state.
```

Optional: prefer `people.profile` for `/?u=` so the people-lane return bar is central; today `followControl` already injects Back to Responses when return context is set.

## Gaps (hosted / consent)

- Hosted OAuth and real two-person consent journey not run (disposable local only).
- No production or shared Auth changes.
- Unread badge on cold load needs the `refreshUnread` shell hook above.
- No strava-schema SQL added; existing `grinder_notifications.read_at` is sufficient.
- Actor IDs and chosen-handle fallbacks preserved via `GrinderPeople.present`.
