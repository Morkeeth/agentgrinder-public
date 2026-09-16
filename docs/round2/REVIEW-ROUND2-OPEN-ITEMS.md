# Round 2 review, open items only

Date 2026-09-16. Author Claude, lane pr13. Source PR 13 `codex/strava-review-round2-20260914`,
head `4f638e7`, opened 2026-09-14.

PR 13 was a review, not a feature. Its code fixes are already on main. Commit `4f638e7` was
cherry-picked as `ee4a5e9`, recorded in `archive/hackathon-2026-09/docs/round2/INTEGRATION-RETURN.md`
line 17, and `git merge-base --is-ancestor ee4a5e9 main` returns true in a clone taken today.
This file carries only the findings that PR 13 described and never fixed, and that are still
true on main today.

Settled and closed on main, for the record: R2-01, R2-02, R2-03, R2-04, A2-01, A2-02, A2-03,
A2-04, A2-05. The evidence for each is in the sweep note
`PR-SWEEP-2026-09-16.md` held in Oscar's local day-run state, outside this repo.

## R2-05, Unread filter keeps a viewport-marked card until remount

Where: `site/social.js` `inbox()`. The unread filter is applied once at render time, at
`rows.filter((n) => (filter === "unread" ? !n.read_at : true))`. The IntersectionObserver later
sets `data-read="1"` and swaps the `unread` class for `read`, but it never removes the card from
the rendered list. Read on main today, `site/social.js`, the `inbox()` function.

Severity: medium, user visible. The Unread view keeps showing items the person has just read.

Done when: on `/?inbox&filter=unread` at 390 by 844 with two unread notifications in view, after
the observer marks both, the Unread list contains zero response cards, with no reload and no
navigation. Red if any marked card is still listed.

## R2-06, A click marks a notification read before the destination exists

Where: `site/social.js`, the `[data-response-nav]` click handler. It calls
`markNotificationsRead([id])` on click, before navigation. Opening a notification whose reply was
deleted still marks that notification read. The inbox copy on the same file says
"Unread stays unread until you actually see it". Read on main today, `site/social.js`, the
`inbox()` function, the copy string and the click handler.

Severity: low. It is a promise that the code does not keep in one case.

Ruling needed. Two branches close this, and they are exclusive.
- Branch A, keep the promise. Mark read only after the destination renders a real conversation.
- Branch B, change the promise. Reword the inbox copy to say that opening a notification marks it
  read.

Done when: branch A, opening a notification whose reply was deleted leaves that row unread in
`grinder_notifications` after the deleted state renders. Branch B, the inbox copy no longer claims
that unread stays unread until the person sees the item. Red if the code and the copy still
disagree.

## Not in this file

No code change. No test change. No fix for R2-05 or R2-06 is proposed here, because the fix
depends on the R2-06 ruling above. This file is the record, so the next reader does not repeat
the comparison.
