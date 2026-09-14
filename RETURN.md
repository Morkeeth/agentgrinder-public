# RETURN · Strava identity lane · 2026-09-14

Branch `codex/strava-identity-20260914` off main `56a1bfb`. Commit hash is in the last section.
No push, no PR, no hosted change, no index.html edit. Fleet ACK for rev e2daf56ba4f1 was rejected
(session not in consumers.json); not retried.

## Files

| File | Owner | What |
|---|---|---|
| `site/auth.js` | this lane | Provider-neutral sign-in, onboarding, linking, presentation, local sign-out |
| `supabase/strava/identity.sql` | this lane | `handle`, `display_name`, `avatar_url` on `strava.profiles`; guard trigger; lookup function |
| `scripts/test-identity.mjs` | this lane | Real SQL/RLS in PGlite plus auth.js against a mocked client |
| `scripts/prepare-strava-database.py` | shared, 5 lines | Appends every `supabase/strava/*.sql` except base/preflight after the inherited list |
| `package.json` | shared, 1 line | `npm run test:identity` |

## Database (strava schema only)

- Columns are nullable. Legacy rows (github_handle + name, no handle) keep working untouched.
- `handle` is lowercased and trimmed by trigger, `^[a-z0-9]([a-z0-9_-]{0,38}[a-z0-9])?$`, partial unique index.
- `avatar_url` must be `https://`, max 2048. `display_name` 1 to 60 after trim.
- Guard trigger raises `handle_taken` with SQLSTATE 23505 when a chosen handle equals another profile's `handle` or `github_handle` (case-insensitive), and when a `github_handle` equals another profile's chosen handle. A legacy URL can never change owner.
- `strava.strava_profile_by_handle(text)` resolves chosen handle first, then legacy `github_handle`, case-insensitive with no LIKE wildcards. Security invoker, granted to anon and authenticated.
- `github_handle` keeps its meaning: written only from a real GitHub identity on the Auth user (`identity_data.user_name`), never from a chosen handle, never from X.
- Owner-only edit and delete are the existing profile policies; test proves B gets zero rows on A's update/delete and anon gets 42501.
- Deleting the Strava profile cascades owned rows; the Auth user and `public.profiles` (Grinder) are unchanged, snapshot-compared in the test.

Deploy: a fresh install gets it via `python3 scripts/prepare-strava-database.py`. An already-installed strava schema takes `supabase/strava/identity.sql` on its own; it is retry-safe (applied twice in the test).

## site/auth.js API

Plain script, sets `window.GrinderAuth`; also loads under Node via `require`. Never creates a client.

```js
const auth = GrinderAuth.create({ client: sb, redirectTo: location.origin + '/' });
auth.providers            // [{id:'github'},{id:'x'},{id:'email'}]  (no Cursor, see below)
await auth.current()      // {user, profile, needsOnboarding, suggestion, identities}
await auth.signIn('github' | 'x', {returnTo})   // OAuth redirect
await auth.signIn('email', {email, returnTo})   // OTP link
await auth.onboard({handle, display_name, avatar_url})  // insert-if-missing keyed on auth_uid -> {profile, created}
await auth.updateProfile({handle?, display_name?, avatar_url?})  // owner-scoped update, id unchanged
await auth.byHandle('name')      // /?u= lookup via rpc strava_profile_by_handle
await auth.identities()          // normalised auth.identities of the signed-in user
await auth.link('github' | 'x')  // linkIdentity; redirect
await auth.unlink(identityId)    // refuses the last identity before calling the provider
await auth.syncGithubHandle()    // fills legacy github_handle once after a real GitHub link
await auth.signOutLocal()        // signOut({scope:'local'})
await auth.deleteProfile()       // owner delete then local sign-out; Auth user remains
auth.returnTo()                  // one-shot read of the stashed return location
auth.onChange(handler)           // onAuthStateChange, returns unsubscribe
GrinderAuth.present(row)         // {id, handle, display_name, avatar_url, legacy, url}
GrinderAuth.explain(error)       // {code, message, retry}  codes: handle_taken, handle_format, avatar_invalid,
                                 //   profile_exists, forbidden, linking_disabled, identity_taken, last_identity,
                                 //   identity_missing, provider_unavailable, rate_limited, offline, unknown
```

Errors thrown by the API carry `error.detail` (the `explain` object) and `error.cause`.

### Presentation contract for other lanes

`present(profileRow)` keeps `id` and returns `handle` (falls back to `github_handle`), `display_name`
(falls back to `name`, then `@handle`, then "A builder"), `avatar_url` (https or null), `legacy`
(true when no chosen handle) and `url` (`/?u=<handle>`). Cursor's social.js can adapt with
`const profile = (p) => GrinderAuth.present(p).display_name` and `link = (p) => GrinderAuth.present(p).url`.

## Integration instructions for site/index.html (root)

1. Add `<script src="/auth.js"></script>` after the supabase-js CDN line and before `/social.js` (line 413).
2. After `const sb = ...createClient(...)` (line 552): `const auth = GrinderAuth.create({client: sb, redirectTo: location.origin + '/'});`
3. Every PostgREST embed `profiles!runs_profile_id_fkey(github_handle,name,rig)` and `profiles:from_profile(github_handle,name,rig)` becomes `(...github_handle,name,rig,handle,display_name,avatar_url)`, or the fallback never sees the new columns (lines 445, 728, 739, 1313, 1399, 1434, 1617, 1682).
4. Replace `refreshAuth` (lines 1472-1493): `const {profile, needsOnboarding, suggestion} = await auth.current();` If `needsOnboarding`, render a one-step form prefilled from `suggestion` (handle, display name, avatar) and call `auth.onboard(values)`; on `e.detail.code === 'handle_taken'` show the message and keep the form. Set `ME = profile`. Do not auto-insert a profile from user_metadata any more.
5. Header identity (line 1487): `const me = GrinderAuth.present(ME); $('me').innerHTML = '<a href="'+me.url+'">@'+esc(me.handle)+'</a>'`.
6. Sign-in dialog (line 1465): add `<button id="signin-x">Continue with X</button>` next to GitHub; both call `auth.signIn(provider, {returnTo: location.search})`. Email form calls `auth.signIn('email', {email})`. No Cursor button.
7. Profile page lookup (lines 1431, 1630, 1648): replace `.eq('github_handle',handle).single()` with `await auth.byHandle(handle)`.
8. Edit profile (line 1450-1456): fields handle, display name, avatar URL; save with `auth.updateProfile(...)`. Add a "Linked accounts" list from `auth.identities()` with link buttons for the providers not yet linked and an unlink button per identity; map failures through `e.detail.message`. Call `auth.syncGithubHandle()` once after `current()` when the user has a github identity and `ME.github_handle` is null.
9. Sign-out (line 1751) and delete (line 1754): `auth.signOutLocal()` and `auth.deleteProfile()`; keep the existing confirm text.
10. `avatar(handle, ...)` (line 1216) may use `present(p).avatar_url` when present, else keep the drawn trace tile.

## Tests

```
node scripts/test-identity.mjs      PASS (SQL half + auth.js half)
npm run test:shared-schema          PASS (unchanged, bootstrap now includes identity.sql)
npm run test:database               PASS (Grinder public schema, unchanged)
node --check site/*.js              clean
```

Node used: `/Users/morkeeth/.nvm/versions/node/v22.22.3/bin/node`. `python3 scripts/dev.py check` not run (needs `setup` venv); its JS half is the `node --check` above.

## Research (sources read this session)

- Supabase identity linking guide: automatic linking only on verified same email; manual linking needs the dashboard toggle (`GOTRUE_SECURITY_MANUAL_LINKING_ENABLED`); `linkIdentity`, `getUserIdentities`, `unlinkIdentity`; unlink requires at least two identities. https://supabase.com/docs/guides/auth/auth-identity-linking
- X provider: `signInWithOAuth({provider:'x'})` is the OAuth 2.0 provider; legacy `twitter` is 1.0a and deprecated; "Request email from users" must be on in the X app. https://supabase.com/docs/guides/auth/social-login/auth-twitter
- `signOut({scope:'local'})` signs out this browser only. https://supabase.com/docs/reference/javascript/auth-signout
- Cursor: cursor.com documents Cursor only as a consumer of identity (SSO for Teams/Enterprise, CLI browser login and API keys). No authorize endpoint, no client registration, no "Sign in with Cursor". No button was added. https://cursor.com/docs/cli/reference/authentication · https://cursor.com/docs/enterprise/identity-and-access-management

## Remaining hosted gaps (unverified, root work)

- X provider enabled on the shared project with client id/secret and "Request email" on. Not done here.
- Manual linking toggled on in Auth settings. Until then `link()` returns `linking_disabled`.
- Strava redirect URLs added to the allowlist without changing Grinder's Site URL.
- `strava` exposed in Data API schemas; `identity.sql` applied to the hosted schema.
- X `identity_data` key names are not documented; auth.js reads `user_name`, `preferred_username`, `screen_name`, `username`, `login`. Verify against one real X sign-in and keep the confirmed key.
- Email OTP users get no provider handle; the suggestion falls back to `builder-<8 chars of uid>` and the user edits it.
- Two-person hosted test from PRODUCT.md still pending.

## Commit

See `git log -1` on this branch; hash recorded below after commit.
