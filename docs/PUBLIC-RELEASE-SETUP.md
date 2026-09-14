# Shared Supabase release setup

Owner decision, 14 September: use the existing Agent Grinder Supabase project. Keep Grinder's public schema intact; all Strava app data and functions use a new `strava` schema. Auth identities, provider settings, limits, backups and outages are project-wide. This is application data separation, not separate authentication tenants. No new paid plan is needed just to add a schema.

## Current evidence

Local PostgreSQL/WASM checks install both apps, compare Grinder definitions/grants/data before and after, and exercise independent profile creation, private-run denial, owner writes, follows, replies, notifications and withdrawal. The disposable browser flow exercises posting, following, ACKs, replies and return at phone and desktop sizes, requiring explicit Strava schema headers. These are synthetic tests, not hosted acceptance or real users.

Production schema installation, API exposure, auth-trigger inspection, callback setup and the separate website remain pending. Chrome's Supabase session is signed out; automated login timed out. No production database change has been made.

## Database installation

1. Confirm the existing Grinder project identity. Run `supabase/strava/preflight.sql` read-only. Inspect auth-user triggers before installation: shared signup must not unexpectedly populate Grinder data. Do not change those triggers as part of this deployment.
2. Generate the first-install transaction with `python3 scripts/prepare-strava-database.py > /tmp/strava-bootstrap.sql`. Review it. It creates only the new schema, no user data, and deliberately refuses an existing `strava` schema. Do not drop an existing schema to retry; inspect its deployment state instead. Do not use the inherited `prepare-migration.py` against production: it targets Grinder's public schema.
3. Apply the reviewed transaction in the confirmed project. Retain the result and run preflight again. Add `strava` to the Data API's exposed schemas, preserving every existing entry. Do not change the project-wide default search path or default privileges.
4. Every later Strava migration must use qualified `strava` targets and restricted function search paths. The bootstrap translates the explicitly reviewed inherited migration list; it is not a general SQL transformer. Review additions and rerun isolation checks before use.

Browser SDK uses `db.schema = strava`; public server/CLI reads send `Accept-Profile: strava`; agent POSTs send `Content-Profile: strava`. Auth requests use the shared project. There is no fallback to public on errors. No privileged key belongs in frontend assets.

## Hosting and sign-in

Use a separate Vercel project. Move the browser/server/CLI endpoint configuration together: site/index.html, server/public-config.json, server/public-run.mjs, AGENTGRINDER_URL, AGENTGRINDER_SUPABASE_URL and AGENTGRINDER_SUPABASE_ANON_KEY. Keep schema selection fixed to strava. Configure the approved origin in page metadata and explicit auth redirects; append callbacks to the allowlist without changing Grinder's Site URL. Strava uses its own auth storage key and local-scope sign-out.

Start with GitHub and X linked to one internal identity, with separate Strava onboarding/profile. The existing github_handle and GitHub metadata assumptions need a compatibility migration before enabling X. Do not match account ownership by public handles. Origin is Cursor's code forge: repository connection is planned; personal sign-in support remains unverified.

Final brand/domain and exact purchase cost require owner approval. No name has been changed or domain purchased.

## Friends, template and hosted acceptance

Add direct person lookup/profile sharing so users can find friends before a run appears in Discover. Test follow/unfollow and Following, empty states, blocks and exact-run response links. A Close friends audience remains a proposal requiring membership/revocation rules.

Install templates/grokbot on a second bot using the current Grok interface. Verify a real export, owner review, deliberate post, second-person response and withdrawal. Installation, real use and publication are distinct states.

Two consenting people must each post a safe real run, find/follow/respond and return on the hosted Strava website. Verify privacy, deletion and links, plus that Grinder continues working. Messages and public posts need approval of recipient, channel and exact text.
