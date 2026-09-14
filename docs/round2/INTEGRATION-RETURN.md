# RETURN · Round 2 integration · 2026-09-14

Branch `codex/strava-integration-round2-20260914`, worktree
`/Users/morkeeth/CODE/.worktrees/strava-integration-round2-20260914`, base main `503bf7e`.
Code head `62ca7ef` (this receipt is the commit after it). Draft PR only. Nothing merged, nothing
deployed, no hosted or shared Auth change, no message sent, no memory written.

Fleet ACK for rev e2daf56ba4f1 (session f0055411) rejected as unregistered; recorded once, not
retried.

## Lane commits kept traceable

| Source | How it landed here | Receipts |
|---|---|---|
| PR11 `codex/strava-response-return-20260914` (`f04115a`, `f41e359`) | `git merge --no-ff` → `d08dbe8` | `docs/round2/response-return-RETURN.md`, `docs/round2/response-return-STATUS.md` |
| PR12 `codex/strava-account-recovery-20260914` (`e3a9e4c` … `871977c`) | `git merge --no-ff` → `2f8bc2a` | `docs/round2/account-recovery-RETURN.md`, `docs/round2/account-recovery-STATUS.md` |
| Cursor review fix `4f638e7` (review branch) | `git cherry-pick -x` → `ee4a5e9` | findings in `restart-2030/REVIEW-ROUND2.md` |

Both lanes' root `RETURN.md` / `STATUS.md` conflicted (add/add). They were moved under
`docs/round2/<lane>-…` in the integrated tree; the originals in the lane worktrees are untouched.

## Shell integration, in `site/index.html` itself (`fc64e92`)

All eight account hooks from `account-recovery-RETURN.md` applied verbatim (stylesheet, script,
`GrinderAccount` bootstrap, `account.recover()` replacing `authErrorFromUrl`, `?account` route,
`|account` in the return allowlist, Account settings menu item, footer `/?account#danger` with the
`confirm()` listener removed). Response-return hooks: `social.refreshUnread()` after `ME` resolves
in `refreshAuth` and at the top of `route()`; the private/missing `viewRun` empty state renders
Back to Responses through `responseReturnLink()` when `ag_response_return === '?inbox'`.

`scripts/check-account-loop.py` no longer inserts hooks in memory. It refuses to run against a
shell that lacks them (`integrated_index()` raises). The only rewrite any walk applies is the
backend host, so requests go to the disposable PGlite shim instead of the hosted project.

## Defects found and fixed in this round

| Id | Found by | Defect | Fix | Commit |
|---|---|---|---|---|
| R2-03 | Cursor review, own walk | Missing/private run dropped the Responses return context | `responseReturnLink()` on the empty state | `fc64e92` |
| A2-04 | Cursor review | Account walk patched the shell in memory | Walk drives the committed shell | `fc64e92` |
| INT-01 | Walk on phone | Account settings unreachable under 900px (header nav hidden); only the footer delete link led there | Edit profile panel links to Account settings (the empty `#linked-accounts` placeholder) | `4cce662` |
| INT-02 | Screenshot | Zero unread painted a blue dot: base `.nav-badge` rule outranked the `hidden` attribute | `.nav-badge[hidden]{display:none}` | `4cce662` |
| INT-03 | Screenshot | Follow rows offered "Open profile" twice | Skip the actor link when the exact link already opens the profile | `4cce662` |
| INT-04 | Screenshot | Lone "·" separator line on phone rows | Separator span hidden in the column layout | `4cce662` |
| R2-01 | Cursor review | Exact reply past page one reported as removed | Cursor's fix: id lookup, page until found | `ee4a5e9` |
| R2-02 | Cursor review | 0-row read update poisoned `unreadMarked` | Cursor's fix: confirm ids from the update, reset on owner change | `ee4a5e9` |
| R2-04 | Cursor review | Inbox observer never disconnected | Cursor's fix: single handle, disconnected on re-entry | `ee4a5e9` |
| INT-05 | Proving R2-01 | Paging loop could spin if the backend never advanced the cursor | Stop when the cursor id does not move, cap 40 pages | `62ca7ef` |
| A2-02 | Cursor review | `deleteProfile` reported deleted with zero rows removed | `.select("id")` on the delete; refuse when empty | `62ca7ef` |
| SHIM-01 | "@?" in ACK list | Shim ignored `alias:column(...)` embeds (`profiles:from_profile`) | Resolve through the named column | `4cce662` |
| SHIM-02 | R2-01 check would not go red | Shim parsed one order column and dropped `or=` cursor filters, so page two was page one | Multi-column order, PostgREST or/and logic filters | `62ca7ef` |

SHIM-01 and SHIM-02 are test infrastructure only. Hosted PostgREST already behaves this way; the
shim was hiding a real defect (R2-01) and a cosmetic one that is not a product bug.

Not fixed, noted: R2-05 (viewport-marked rows stay listed under the Unread filter until remount;
removing a card while it is being read would be worse), R2-06 (click marks read before the
destination renders; the lane calls this intentional). Observed, out of this round's scope: a
blocked person's profile still shows a Follow button next to Unblock (people lane).

## Integrated user path, driven on the committed shell

`scripts/check-round2-integration.py`, phone viewport 390×844, headless Chrome, disposable PGlite,
TEST DATA actors Casey and Riley. 40 checks, 0 failures, no JavaScript page errors. Screenshots
`docs/round2/screens/integrated/01…20`. Steps and what each screenshot shows:

1. Signed out, capture payload on the URL hash → Preview your run; Save asks for sign-in (01).
   GitHub sign-in cancelled at the provider → landing names the cancel and the surviving draft,
   the preview is back from the restored draft, pending marker settled (02).
2. Casey signed in, same capture → caption, public, Save run → `/?run=` (03, 04).
3. Phone path to Account settings (own handle → Edit profile → Account settings). Handle
   `test-riley` refused as taken with `test-riley-2` offered, nothing changed (05). New handle
   `test-casey-r2` saved, id stable, the posted card shows it. Zero unread draws no badge.
4. Riley follows Casey at the new handle; Following shows the run (06, 07).
5. Riley ACKs and replies (08).
6. Casey cold-loads Discover: badge shows 3 from the shell hook, no visit to Responses (09).
7. Responses lists follow, ACK, reply; follow row offers the profile once (10). 25 newer
   replies inserted; Open exact reply pages to the buried reply and focuses it, no removed
   copy (11). Back to Responses returns; the opened item is read (12).
8. Missing run while in the Responses context → denial copy plus Back to Responses (13),
   which lands on Responses.
9. Riley deletes the reply through the client (one row confirmed). Casey's deep link shows the
   removed copy (14); the inbox row states the removal with no dead link.
10. Riley types the wrong handle on Delete: button stays disabled, walking away leaves the
    profile (15).
11. Casey blocks Riley (16); Riley's composer is withheld on the run (17).
12. Riley deletes the Strava profile with the typed handle: Strava row gone, Grinder
    `public.profiles` snapshot identical, Auth identities untouched, signed out locally (18).
    Casey opens the deleted handle → Profile not found (19). Responses has no dead link;
    `grinder_notifications.actor_id` cascades, so Riley's rows vanish (20).

The R2-01 check was watched failing: with pre-fix `social.js` the same walk reports 39 passed,
1 failed on "a reply past page one is found"; with the cherry-picked fix 40 passed.

## Everything run on the integrated head (local, disposable, synthetic)

| Check | Result |
|---|---|
| `python3 -m pytest -q` | 339 passed, 1 skipped (base 318; +8 account lane, +5 response return incl. Cursor's two, +7 round 2, +1 account shell) |
| `python3 scripts/check-round2-integration.py` | 40 checks passed, screenshots in `docs/round2/screens/integrated/` |
| `python3 scripts/check-account-loop.py` | 51 checks passed against the committed shell, screenshots in `docs/round2/screens/account/` |
| `python3 scripts/check-response-return.py` | passed |
| `python3 scripts/check-people-loop.py` | passed, no JavaScript errors |
| `CHROME_BIN=… python3 scripts/check-social-loop.py` | passed |
| `npm run test:account`, `test:identity`, `test:journey`, `test:database`, `test:people`, `test:shared-schema` | all PASS |
| `python3 scripts/dev.py check` | Contributor checks passed |
| `python3 scripts/check-browser-fixtures.py` | fails with `ReferenceError: auth is not defined` on base `503bf7e` too (pre-existing, not from this round); its route fixture now stubs `account`/`social` instead of `authErrorFromUrl` |

## Not verified here

- **Hosted OAuth** was not run. The cancel fragment is the documented implicit-flow shape,
  produced by the walk's proxy. GoTrue's real cancel codes, the hosted manual-linking flag, the X
  provider and the real link return are as unverified as the account lane left them.
- **No consenting person** has used this. Every actor is a disposable TEST DATA identity in a
  PGlite shim; no row reached the shared Supabase project.
- **Deployment** unchanged. `PROVIDERS_ENABLED` still `["github","email"]`.

## Next for root

Review the draft PR; merge decides whether the integrated shell replaces main. Hosted checks
above stay open until a person runs a real sign-in against the hosted project.
