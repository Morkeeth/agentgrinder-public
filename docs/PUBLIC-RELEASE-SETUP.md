# Independent release setup

Current status: Grok adapter PR #5 merged after review. The independent database, domain, multi-provider login and installed template are not deployed.

Use a new Supabase project and new Vercel project for agentgrinder-public. Existing agentgrinder and aistrava projects are not proof of this product's independent deployment. Vercel account access was verified; Supabase's browser session returned to sign-in during project creation on 14 September. Restore that session before provisioning. No project was created in this attempt.

## Database and hosting

Provision independent Postgres/Auth and apply a complete schema plus ordered migrations. Do not treat tests/fixtures/hosted-base.sql as a verified production bootstrap. Validate fresh-project creation, row policies and owner access on the actual project before connecting the public UI.

Move the browser/server/CLI public endpoint configuration together: site/index.html, server/public-config.json, server/public-run.mjs and AGENTGRINDER_URL / AGENTGRINDER_SUPABASE_URL / AGENTGRINDER_SUPABASE_ANON_KEY. Keep privileged keys out of frontend assets. Set the new origin in sign-in callbacks and link metadata. Configure the approved domain, DNS and TLS. No domain purchase is authorised until its exact name and price are approved.

## Sign-in

Start with GitHub and X. Both need provider applications configured for the independent Supabase callback. Keep one internal person/profile ID, with linked provider identities and a separately chosen public handle. The existing github_handle column and GitHub metadata assumptions need a compatibility migration before enabling X. Do not infer account ownership by matching public handles. Third provider awaits clarification.

Primary docs: [GitHub](https://supabase.com/docs/guides/auth/social-login/auth-github), [X](https://supabase.com/docs/guides/auth/social-login/auth-twitter), [identity linking](https://supabase.com/docs/guides/auth/auth-identity-linking).

## Friends and return

Add direct person lookup/profile sharing so someone can find a friend without waiting for their run to appear in Discover. Exercise follow/unfollow and the Following feed, including empty state, own-profile handling and blocks. Responses must return to the exact run. A close-friends audience is a proposed extension; define membership/revocation before adding it, and deny strangers in the database and public-link handlers.

## Grok template

The source kit is in templates/grokbot. Its helper creates a private preview, not a social write. Install on a second bot using the actual current Grok interface. Verify a real export, human review, deliberate post to the new service, response by a second person and withdrawal. Template installation, successful real use and marketplace publication are separate states.

## Launch evidence

Two consenting people on the independent service must each post a safe real run, follow/respond and return. Inspect phone and desktop views. Verify signed-out cards, private/link audiences, owner edits/deletion and response links. Use their observed friction to guide the next change. Outbound messages and public posts require owner approval of recipient, channel and exact text.
