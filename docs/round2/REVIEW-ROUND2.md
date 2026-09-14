# REVIEW-ROUND2 · independent review · 2026-09-14

Reviewer worktree: `/Users/morkeeth/CODE/.worktrees/strava-review-round2-20260914`
Branch: `codex/strava-review-round2-20260914`
Sources read only (not edited):

| Lane | Worktree | HEAD | Draft PR |
|---|---|---|---|
| Response return | `strava-response-return-20260914` | `f41e359` | #11 |
| Account recovery | `strava-account-recovery-20260914` | `871977c` | #12 |

Fleet ACK: session `cae719e0-fe90-4657-9ba2-f3fe51c5223c` / rev `e2daf56ba4f1` rejected unregistered once; not retried.

`INTEGRATION-READY.json` was **absent** at review time. Findings below are from original lane source plus baseline `site/index.html` (`503bf7e`). Integration had uncommitted `site/index.html` wiring in progress; this review did not edit that tree.

Evidence class: **local disposable / source inspection**. Not hosted OAuth. Not consenting real users.

## Verdict for integration

Ship blockers to fix before calling the integrated shell done:

1. **R2-01** Exact reply deep-link false "removed" for replies outside the first 25-row page.
2. **R2-02** `unreadMarked` treats a 0-row notification update as success (account-switch / stale `me()` race); later views never retry.
3. **R2-03** Private/missing `viewRun` empty state still omits **Back to Responses** unless the shell wires `ag_response_return` (baseline gap; integration must land the RETURN.md hook for real).

Account link/delete isolation and last-identity refusal look sound in lane code plus disposable shim. Cancel/fail recovery works in the **harness-patched** shell; silent link-fail remains if `|account` return allowlist / `account.recover()` are missing from the real shell.

## R2-01 · Exact reply deep-link lies "removed" past page 1 (CRITICAL)

**Where:** `strava-response-return-20260914/site/social.js` `thread()`

**Bug:** After the first `page()` (limit 25, newest first), if `focusReply` was not in that page, the UI inserts:

> That reply was removed or is no longer available.

It never queries by reply id. Clicking **Earlier replies** can load the target into the DOM and set `sawFocus`, but the missing banner is not removed and the reply is not focused/scrolled.

**Exact reproduction (disposable):**

1. Seed one public run with **26+** replies (or 25 newer than the target).
2. Open `/?run=<run>&reply=<oldestReplyId>#reply-<oldestReplyId>` as a signed-in viewer.
3. **Observe:** missing-reply card appears even though `grinder_replies` still has that id.
4. Click **Earlier replies** until the reply node exists.
5. **Observe:** `#reply-<id>` is in the DOM, missing card remains, no `reply-target` focus.

**Fix shape:** Resolve focus reply with `.eq("id", focusReply)` (or paginate until found / known absent). Only show missing when the id lookup returns no row. On late find, remove `.reply-missing` and focus.

**Regression:** assert deep-link to reply rank 26 focuses the card and does not show the removed copy.

## R2-02 · `unreadMarked` + 0-row update poisons read marking (HIGH)

**Where:** `site/social.js` `markNotificationsRead`, module-level `unreadMarked`

```js
pending.forEach((id) => unreadMarked.add(id));
await result(db.from("grinder_notifications").update({ read_at: ... })
  .in("id", pending).eq("recipient_id", me().id).is("read_at", null));
// no check that any row updated; only catch removes ids from the set
```

**Bug:** Supabase returns `error: null` with `data: []` when zero rows match. After a mid-flight `me()` change (sign-out / other profile in the same tab), Casey's notification ids stay in `unreadMarked` forever for that JS lifetime. DB rows stay unread; IntersectionObserver / click paths skip them.

Wrong-person **writes** are blocked by `.eq("recipient_id", me().id)` (and RLS). The failure mode is **stuck unread** for the original recipient after a stale in-flight mark, not marking Riley's rows as Casey's.

**Exact reproduction:**

1. Casey opens `/?inbox` with at least 1 unread card intersecting the viewport (observer schedules `markNotificationsRead`).
2. Before the PATCH completes, sign out and sign in as Riley in the same tab (or force `ME` to Riley while the promise is open).
3. Let the PATCH finish (0 rows).
4. Sign Casey back in (same tab, no full reload) and open `/?inbox`.
5. **Observe:** Casey's notification stays unread in DB; client never retries (`unreadMarked.has(id)`).

**Fix shape:** Clear `unreadMarked` on auth/profile change; only add ids after a successful update that returns those ids (or delete from set when `data` lacks them); `observer.disconnect()` when leaving inbox / remounting.

## R2-03 · Missing/private run empty state drops return context (HIGH for return loop)

**Where:** baseline / pre-hook `site/index.html` `viewRun`:

```js
if(!r){ app.innerHTML='<div class="card"><div class="empty">This run is private or does not exist.</div></div>'; return; }
```

PR11 RETURN.md requires: if `sessionStorage.ag_response_return === '?inbox'`, show **Back to Responses** on that empty state. Thread/profile paths already show the bar; this shell path does not until integration lands it.

**Exact reproduction:**

1. From Responses, click through so `ag_response_return` is `?inbox`.
2. Navigate to a private/missing `/?run=<id>` (or delete the run, then open the notification's run link).
3. **Observe (unwired shell):** denial copy only; no Back to Responses.
4. **Expect (wired shell):** denial copy + Back to Responses.

## R2-04 · IntersectionObserver never disconnected (MEDIUM)

**Where:** `inbox()` creates a new `IntersectionObserver` each visit; nothing calls `disconnect()` on leave.

Detached nodes usually stop intersecting, but in-flight callbacks plus R2-02 make account switches unsafe. Multiple inbox visits leak observers.

**Fix:** Keep one observer handle; `disconnect()` at the start of `inbox()` and on route leave.

## R2-05 · Unread filter keeps viewport-marked items until remount (MEDIUM UX)

**Where:** `inbox()` filters unread at render time only. Observer sets `data-read="1"` and classes but does not remove the card from `filter=unread`.

**Reproduction:** Open `/?inbox&filter=unread` with two unread items on a tall phone viewport; wait for observer marks; cards stay listed under Unread until reload/navigation remount.

## R2-06 · Click marks read before destination exists (LOW)

**Where:** `[data-response-nav]` click calls `markNotificationsRead([id])` before navigation.

Opening a notification whose reply was deleted still marks the notification read. Product copy promises viewed-only marking; click-to-open is intentional, but combined with R2-03 the user never "views" the conversation.

## Account lane (PR12) findings

### A2-01 · Last identity unlink. PASS (local disposable)

UI: no Unlink when `ids.length < 2`.
Client: `unlink()` throws `single_identity_not_deletable` when `list.length < 2`.
Shim: `DELETE /auth/v1/user/identities/:id` returns 422 when last.

Hosted GoTrue behaviour still **unobserved** (lane RETURN). Do not claim hosted.

### A2-02 · Strava delete vs Grinder / Auth. PASS (local disposable)

`deleteProfile()` deletes `strava.profiles` scoped by `id` + `auth_uid`, then `signOut({ scope: "local" })`. Walk snapshot: `public.profiles` unchanged; Auth identities remain.

**Gap:** no check that DELETE affected at least 1 row before sign-out (stale profile id can show "deleted" UI while row remains). Low probability under normal RLS.

### A2-03 · Cancel / fail recovery vs real shell double-route (MEDIUM)

`account.recover()` on non-account routes:

```js
const r = auth.recoverFromUrl();
if (!r) { dropRecovered(); return null; } // clears ag_auth_recovered
```

After a cancel, the first `route()` keeps the notice; any later non-account `route()` with a clean URL **drops** `ag_auth_recovered`. Lane documents this as "moved on". Combined with `refreshAuth()` always calling `status('')`, a second auth refresh can clear both the status line and the stored notice before the person opens Account.

Failed **link** while signed in relies on `ag_social_return === '?account'` **and** the shell allowlist including `account`. Without that allowlist, `recover()` returns early without `say()` when `me()` is set, which is a silent failure on landing. Integration must keep `|account` in the allowlist (PR12 RETURN hook 6).

### A2-04 · Harness inserts production hooks (process risk)

`scripts/check-account-loop.py` patches `site/index.html` **in memory**. That does not prove the committed shell. Round-2 integrated checks must drive the **actual** wired `site/index.html` (no HOOKS rewrite), per root brief.

### A2-05 · `settled()` for non-link actions

`settled(r, user, ids) => r.action === "link" ? providerLinked : !!user`
Any signed-in user clears a stored **sign-in** failure notice. Correct after success; ensure link failures always persist `action: "link"` (they do via pending capture in `recoverFromUrl`).

## Shell hooks integration must not drop

From the two RETURN.md files (read in original worktrees):

**Account (8 + footer confirm removal):** `account.css`, `account.js`, `GrinderAccount({...})`, `account.recover()` replacing `authErrorFromUrl()`, `q.has('account')`, return allowlist `|account`, Account settings menu item, footer `/?account#danger`, remove `confirm()` delete listener.

**Responses:** after ME / each successful `route()`, `social.refreshUnread()`; private/missing empty state Back to Responses when `ag_response_return === '?inbox'`.

## What was not repeated

Did not re-run the lanes' full Playwright walks as the sole review. Those already green-path cancel, duplicate handle, unlink, delete isolation, inbox happy path, deleted reply, block. This review targeted failure cases those walks under-cover (pagination deep-link, unreadMarked race, unwired empty-state return, harness-vs-shell gap).

## Reviewer follow-ups in review worktree

When `INTEGRATION-READY.json` appears, fetch that exact committed head into this worktree and drive the disposable browser against the **committed** shell. Until then: actionable findings above; focused regression tests/fixes for R2-01 / R2-02 land as separate commits on `codex/strava-review-round2-20260914` for integration to cherry-pick.


## Post-review note (integration tree, not READY signal)

While this review was open, integration commit `fc64e92` on
`strava-integration-round2-20260914` wired `responseReturnLink()` into the private/missing
`viewRun` empty state and switched `check-account-loop.py` to the real shell (no in-memory
hooks). That addresses **R2-03** and **A2-04** in that tree. `INTEGRATION-READY.json` was still
absent, so this reviewer did not fetch that head or drive the disposable browser against it.
