# RETURN · Strava account control and sign-in recovery lane · 2026-09-14

Branch `codex/strava-account-recovery-20260914` off main `503bf7e`. Lane commit hash in the last
section. No merge, no hosted change, no `site/index.html` edit, no shared Auth configuration
change, no memory written, no message sent. Fleet ACK for rev e2daf56ba4f1 was rejected
(session 8e7f7127 not in consumers.json); recorded once, not retried.

Root removed the previous lane receipts from the product tree at merge (`ffd713b`); this file and
STATUS.md are on the branch for the same treatment.

## What a person can now do

Open **Account settings** (or the footer's delete link) and, on a phone or with a keyboard:

- Edit the chosen handle and display name. The profile id never changes. A taken handle is
  refused inline with a free variant offered as a button. A malformed handle is explained before
  any request. Duplicate check is the database's, the variant is looked up through the public
  `strava_profile_by_handle` RPC.
- See which sign-in methods are linked to the shared Auth user (GitHub, email link). Link GitHub
  when it is not linked yet; a failed link comes back to the panel with a dismissable notice, a
  successful one shows both methods and fills the legacy `github_handle` from the real identity.
  Unlink any method except the last; the last is labelled as the only way in and has no button.
  The disposable shim, implementing GoTrue's documented `single_identity_not_deletable`, refuses
  it server-side too; hosted GoTrue was not observed. X appears as "not available on this
  service yet" text, never a button, until `PROVIDERS_ENABLED` includes it. There is no Cursor or
  Origin login anywhere; repository connection is named as a separate planned feature.
- Sign out on this device only. The request is `logout?scope=local`; other devices and the
  shared Grinder session are untouched.
- Delete the Strava profile after typing the handle. The copy states what goes (Strava profile,
  posted runs, ACKs and replies here) and what stays (sign-in account, Agent Grinder profile and
  runs, anything local). No `confirm()` dialog. The Auth user is never deleted from the client.
- Recover from a provider round trip that was cancelled, failed or expired: the landing page
  says what happened and that the draft is still there, and the account panel shows it with a
  retry until dismissed, contradicted by a later successful sign-in or link, or passed by on
  another page. A sign-in that was started and never came back shows a dismissable notice
  naming the provider.

## Files

| File | Owner | What |
|---|---|---|
| `site/auth.js` | this lane | Additive: `parseAuthError` (hash and query), `pending`/`clearPending`, `recoverFromUrl`, codes `cancelled`, `link_expired`, `provider_failed`; `signIn`/`link` mark the attempt; `current()` settles it |
| `site/account.js` | this lane | `window.GrinderAccount({...})` → `{view, recover}`; the `/?account` panel |
| `site/account.css` | this lane | Panel styles, 44px targets, phone layout |
| `scripts/check-account-loop.py` | this lane | Playwright walk against the disposable shim; applies the shell hooks below in memory |
| `scripts/test-account.mjs` | this lane | Node test for the auth.js additions; `npm run test:account` |
| `tests/test_account_lane.py` | this lane | Contract strings: honest providers, safe destructive copy, hook coverage |
| `scripts/disposable-supabase.mjs` | shared test infra | `auth.identities` table and seed, `/auth/v1/user` returns identities, `DELETE /auth/v1/user/identities/:id` with last-identity refusal, `/auth/v1/logout`, test-gated provider authorize (JSON for link, redirect with the error fragment), `/_test/insert-identity`, `/_test/grinder-snapshot`, `DISPOSABLE_GRINDER=1` loads the Grinder public fixture |
| `package.json` | shared, 1 line | `test:account` |
| `docs/screens/account-lane/*.png` | this lane | Screenshots from the walk |

No SQL changed. No migration needed. `strava/identity.sql` policies already enforce owner-only
edit and delete; the walk's Grinder snapshot proves `public.profiles` is untouched by a Strava
deletion for the same Auth user.

## Integration hooks for site/index.html (root owns the edit)

These are the exact strings `scripts/check-account-loop.py` applies in memory, so they are known to
apply cleanly to main `503bf7e`.

1. Head, after the people stylesheet: replace `<link rel="stylesheet" href="/people.css"></head>` with
   `<link rel="stylesheet" href="/people.css"><link rel="stylesheet" href="/account.css"></head>`.
2. Scripts: after `<script src="/people.js"></script>` add `<script src="/account.js"></script>`.
3. Bootstrap, after `const challenges=GrinderChallenges({...});`:
   ```js
   const account=GrinderAccount({auth,me:()=>ME,app:()=>$('app'),frame,status,providersEnabled:PROVIDERS_ENABLED,signIn:showSignIn,onProfileChange:p=>{ME=p;refreshAuth();}});
   ```
4. Route start: `async function route(){ authErrorFromUrl();` becomes `async function route(){ account.recover();`.
   `authErrorFromUrl` can then be deleted; it only read the query string, and the default implicit
   flow puts provider errors in the fragment.
5. Route table, before `if(q.has('following'))…`: `if(q.has('account')){return account.view();}`.
6. Return-path allowlist: `(post|mine|following|inbox|run|u|example|people)` gains `|account`.
7. Account menu, after the "My profile" item: `<a href="/?account" role="menuitem" data-auth="1" hidden>Account settings</a>`.
8. Footer: `<a href="#" id="delete">` becomes `<a href="/?account#danger" id="delete">`, and the
   `$('delete').addEventListener('click', … confirm(…) …)` block in DOMContentLoaded is removed.

The profile page's `#linked-accounts` placeholder inside "Edit profile" can stay empty or link to
`/?account`; the panel is the one place for linking.

## Tests run in this worktree (all local, synthetic actors)

| Check | Result |
|---|---|
| `python3 -m pytest -q` | 326 passed, 1 skipped (baseline 318 passed, 1 skipped; +8 in `test_account_lane.py`) |
| `npm run test:identity` | PASS sql + PASS auth.js (unchanged suite still green after the auth.js additions) |
| `npm run test:account` | PASS |
| `npm run test:journey` | passed |
| `python3 scripts/check-account-loop.py` | 51 checks passed, screenshots in `docs/screens/account-lane/` |
| `python3 scripts/check-people-loop.py` | passed, no JavaScript errors |
| `CHROME_BIN=… python3 scripts/check-social-loop.py` | passed (script hard-codes `/usr/local/bin/google-chrome`; the env override is its own) |
| `python3 scripts/dev.py check` | Contributor checks passed |

### Observed user path (browser walk, Chrome headless, disposable PGlite, TEST DATA actors)

1. Signed out on `/?post` with a draft stashed. Sign in → Continue with GitHub. The browser
   navigates to the authorize URL and is sent back with `#error=access_denied…`. Landing shows
   "Sign-in was cancelled before it finished. Nothing changed. Your draft is still here". The
   error fragment is removed; the shell restores the draft to `#import=`; the pending marker is
   settled. Screenshot `cancelled-signin-desktop.png`.
2. Same browser, provider fails (`server_error`). Landing says the provider did not finish.
   Opening Account shows the inline notice with "Try signing in again", which reopens the dialog.
   `failed-signin-desktop.png`.
3. Phone, a GitHub sign-in that never returned: Account shows "Sign-in with GitHub was started and
   has not finished", Dismiss clears it. `pending-signin-mobile.png`, `signed-out-account-mobile.png`.
4. Casey (GitHub + email) on a phone: both methods listed, X as text, delete disabled. Handle
   `test-riley` refused as taken with "Use test-riley-2"; input `aria-invalid`, focus returned.
   Accept the variant, change the name, Save: header becomes `@test-riley-2`, row id unchanged.
   `account-panel-mobile.png`, `duplicate-handle-mobile.png`.
5. Unlink email: succeeds, GitHub now labelled the only way in with no button. Calling the SDK
   directly to unlink the last identity is refused by the server with `last_identity`.
   `sign-in-methods-mobile.png`.
6. Delete with the typed handle: Strava row gone, `public.profiles` snapshot identical, the
   user's Auth identities remain, local session cleared, confirmation shown after the shell's
   sign-out re-route. `delete-confirm-mobile.png`, `deleted-mobile.png`.
7. Riley (email only): no unlink button, Link GitHub offered. Link GitHub with the provider
   failing: the SDK fetches the authorize URL, the browser navigates, comes back with the error
   fragment, the shell returns to Account and the panel shows "Linking GitHub did not finish"
   with Dismiss and no sign-in retry; GitHub still offered. Leaving for the feed and coming back
   clears the seen notice. Link GitHub with the provider approving: the identity is added, the
   session comes back in the fragment, both methods show, no stale failure notice, the pending
   marker is settled and `github_handle` is filled from the identity while the chosen handle is
   unchanged. `link-failed-mobile.png`, `link-success-mobile.png`. Sign out here sends
   `logout?scope=local` only; the profile row survives.
8. Signed in on desktop: Account settings appears in the Account menu; the footer delete link
   opens `/?account#danger`.

## Not verified here (hosted and consent gaps)

- **Hosted OAuth is unverified.** The cancel and failure fragments are the documented implicit
  flow shape; the exact `error_code` values GoTrue emits when a person cancels at GitHub were not
  observed on the hosted project. Unknown codes map to a generic retry message, so nothing breaks,
  but the wording for a real cancel is not evidenced. The successful-link return was simulated by
  the walk's proxy (identity inserted, tokens in the fragment); GoTrue's real link return is
  unobserved.
- **Manual identity linking** must be enabled on the shared Supabase project for Link/Unlink to
  work. Its hosted state is unknown to this lane; a disabled flag surfaces as "Account linking is
  not enabled on this service yet". Changing it is root's call and must preserve Grinder.
- **X provider** has no credentials on the project. It stays gated off in `PROVIDERS_ENABLED`.
- **Origin / Cursor** offer no personal login; nothing is drawn, nothing is pretended.
- **Real people**: no consenting real-user run of link, unlink or deletion. Disposable identities
  only. No account-consent action was taken.
- The email identity's address is shown in the panel to its owner only (from Auth, never from
  the profile row); it is not rendered anywhere public.

## Expectation on root's file

`site/index.html` keeps `PROVIDERS_ENABLED=["github","email"]` until the X provider exists on
the hosted project; the panel reads it, nothing in this lane asserts on it.

## Lane commits

`e3a9e4c` code and tests, `62f604f` first receipt, then the review-fix commit recorded in
STATUS.md (stale-notice rule, link fail and success walk steps, tighter identity check).
