# Pacecard new-user journey and build map

Reviewed 15 September 2026 for the Cursor + Grok Bot path. This is the product map for the
bounded card → post → response → return loop. It does not replace
[`COMPLETION-PLAN.md`](COMPLETION-PLAN.md) or PR 23's two-person test.

## Evidence boundary

- Repository: `Morkeeth/agentgrinder-public` only.
- Cursor Cloud run: `bc-521cf5c3-2609-4e09-959f-321690c9d56b` on
  `cursor/full-cursor-grok-user-journey-and-core-loop-build-map-9998`.
- Exact starting SHA and current `origin/main` at review time:
  `29a5074a58014a9d29a1e0bb4e5cfa35943a3b6c`.
- Live origin at review time: `https://agentic-strava.vercel.app`.
- Live `/`: HTTP 200, 136,849 bytes, SHA-256
  `a238ddbedf2a6e1e45e4b8c8b3785ff50d43fd0682b11da33b615a03fb3796ea`,
  title `Pacecard`.
- Live `/api/health`: HTTP 200, 41 bytes,
  `{"service":"pacecard","database":"ready"}`.
- After injecting the public deployment configuration, the live index was byte-identical to
  `a01f251da44b7bcee2ae3d6a2b1e48bd0193cad9` and to the unchanged index at the starting merge
  SHA. Thus Pacecard rename and Continue in Cursor are hosted. This comparison says nothing
  about whether the unapplied segment SQL exists in production.
- No production identity, post, follow, ACK, reply, message, SQL or Auth setting was used or
  changed. Browser integration used disposable identities labelled `TEST DATA`.
- The shared Auth redirect allowlist entry `https://agentic-strava.vercel.app/**` remains
  unverified. This is a configuration-verification gap, not evidence of a broken callback.
- Current Cursor documentation supports project/global `mcp.json`, explicit repository/branch
  selection for Cloud Agents, durable Cloud agent/run IDs, conversation search, and prompt
  [deep links](https://cursor.com/docs/reference/deeplinks). It does not document a public deep
  link that selects an exact local Cursor sitting or sends a third-party preview into a hosted
  Save flow. Pacecard's hosted `#import=` URL is its own human-review handoff, not a Cursor
  platform Save primitive.

The live service and database are healthy. That is not the same as hosted sign-in acceptance,
and neither is evidence of use by two consenting people.

## Cold live walkthrough

The first pass used only the live UI, before implementation inspection, at desktop and 400 px.
No sign-in or write was attempted.

- `/` clearly says “Every run your agent made, on a card you can share,” shows a labelled sample,
  and offers **Post your first run** and **Explore runs**.
- Explore had no public runs. The UI consistently called the card sample data and said a real
  card would put builder, project, caption, output and measured cost together. It did not
  fabricate social proof.
- Find people allowed signed-out public-profile search and explained that sign-in is required to
  follow. There was no profile or public run reachable through the UI during this pass.
- Post led to a clone-and-run command for the Pacecard repository, then a separate sign-in action.
  That is the first material stop for the intended technical builder: the UI has switched from
  “share work from my project” to “clone this product,” and it has not asked which sitting to
  share. This review does not treat a command line as inherently out of scope; Cursor/Grok
  builders are the target. The defect is destination and selection clarity.
- The sign-in dialog accurately said that sign-in keeps profile/responses connected and that a
  run remains private until Public is chosen and saved. It offered GitHub and email; it did not
  imply Cursor is an identity provider.
- Phone retained Feed/Post navigation, readable cards and the same actions with no observed
  horizontal overflow. Desktop exposed the same product path. Representative cold screenshots:
  landing `/tmp/computer-use/f8880.webp`, empty feed `/tmp/computer-use/545f2.webp`, Post
  `/tmp/computer-use/b2334.webp`, sign-in `/tmp/computer-use/9cf51.webp`, phone landing
  `/tmp/computer-use/437ee.webp`, and phone Post `/tmp/computer-use/0b67d.webp`.

The cold pass did not establish that there are zero rows in production; it established only that
the live discovery surfaces returned no public runs or profiles to this signed-out browser.

## The complete journey in plain language

A builder completes useful work in their own project. On the same computer, they deliberately
select that Cursor sitting, or on a Grok Bot computer they explicitly select an exported JSONL
sitting. Pacecard reads only allowlisted measurements and first opens a private preview. The
builder writes the public explanation and optional output link, checks the signed-in account,
chooses Only me, Link or Public, and presses Save once.

A friend receives a saved public or link URL, understands the caption and output before the
metrics, opens the builder's profile, and chooses to follow, ACK or reply. Those actions require
the friend's own account. The builder later sees a Responses item, opens the exact run and exact
reply, and can return to Responses. On the next day, a response is the reason to return; a second
safe capture is the action available after the conversation.

Cursor and Grok Bot are different capture origins, not different identities or destinations.
Both hand the human to the same Pacecard account, audience control and saved-run route.

## Transition map

| Transition | What exists now | Stop or risk | Required behavior |
|---|---|---|---|
| Discover → understand | `/` and `/?explore` show the Pacecard promise, a sample/featured card, Feed and Post. Public cards put caption and output above the trace. | A cold visitor can browse, but a mostly empty feed cannot prove the social value. Sample content must not look like adoption. | Keep the first action “Post a run”; label every sample and never seed invented people or engagement. |
| Discover → own project | The live first-run command clones this product repository, while `docs/CURSOR.md` says to open this repository to obtain its workspace MCP. | A person came to share work from **their** repository. The product/contributor repository switch is unexplained, and the default command picks the latest eligible sitting rather than asking which one. | Start from the person's own project, install/enable the capture integration there, list eligible sittings without transcript text or paths in agent payloads, and require an exact selection before preview. |
| Cursor work → capture | `grind --harness cursor [SESSION] --pick N`, `--list`, MCP `list_sessions`, `preview_run`, and `a2a_propose_publish` exist. A safe explicit-path walk correctly labelled `my-own-project`, counted two typed turns and one tool call, and left duration/commits unknown. | `docs/CURSOR.md` documents “latest eligible” only. The MCP list identifies only each harness's latest file, so it cannot make an exact sitting choice. A cloud VM cannot read a laptop's Cursor sessions. | A local-only selector on the user's computer must identify the chosen project/session and sitting. Cloud agents must state that they see only their VM. |
| Grok work → export | The adapter reads explicitly supplied Grok JSONL; the source kit helper returns allowlisted metrics and a private import URL without a request. Labelled samples produced 2/3 and 7/7 typed-turn/tool-call counts. | Source availability is not installation. Current skill/docs still use placeholder hosted origins even though the approved live origin exists. No second bot or real export was observed here. | Grok owner installs the complete source directory on a second bot, explicitly selects a real export on that bot's computer, uses the approved Pacecard origin, and returns the private preview URL to the human. |
| Capture → preview | `#import=` carries allowlisted fields in the fragment. `importRun()` validates it, labels sample previews, displays all imported fields, says “not posted,” and renders the white card/blue trace. | A copied/truncated fragment cannot be recovered. Rig notes are described as profile data even for Only me and therefore need careful review. | Invalid links say nothing was posted and point back to capture. Unknown metrics remain absent/unknown. The person reviews every field before auth or save. |
| Preview → auth | `stashImport`, `ag_import_edits`, `ag_auth_return` and profile onboarding preserve the capture and typed title/caption/link/audience in session storage. Cancellation, provider failure and expired links have explicit recovery copy. | The exact hosted Auth allowlist is not readable from this run. Email completion can occur in another tab/browser where session storage is unavailable. | Verify callbacks without changing shared Site URL. Keep the original tab open for email; if browser storage is unavailable, stop before redirect and tell the user to retain their local capture. No auth event may post a run. |
| Auth → account/profile | One shared Supabase Auth user maps to one schema-qualified `strava.profiles` row. GitHub and email are enabled in source; X is gated. | “One identity” is a product invariant, but a user still needs to verify the account shown after returning from a provider. | Show account/handle before Save. Keep Cursor/Origin as integrations, never login providers. |
| Draft → audience → Save | Imported captures require title, caption and a deliberate non-default audience. A measurement revision deduplicates imported saves. This PR adds an explicit browser save ID and persisted draft to make manual fallback retries idempotent too. | Baseline lost-response evidence proved the server held a run while UI claimed “Nothing was posted.” Manual fallback could duplicate on retry. | Say “Save not confirmed,” preserve fields and audience, never retry automatically, and on the person's next click look up the exact save before inserting. |
| Saved run → share | `/?run=<id>` works for owner/link access; `/r/<id>` serves public previews. Copy link, profile link and Continue in Cursor exist. | Link is unlisted access, not private. Public means feed/profile/searchable. Private has no friend journey. A manual post has unknown capture metrics. | Name the saved audience in success and recovery states. A card remains understandable from caption/output when measurements are unknown. |
| Friend arrival → identity | Signed-out people can read public and link-visible runs. Follow/ACK/reply asks for sign-in and stashes the social return route. | A private, deleted, blocked or withdrawn target may disappear during auth. | After auth, return only to an allowlisted route. If target is unavailable, show a neutral state and retain a way back; never reveal why private data is hidden. |
| Friend → follow | Public profile and `/?people` support follow; `/?following` shows public runs from followed profiles. | A new feed may have no one to find. Grok Bot owns first-user/friend polish, so this review does not implement discovery UI. | Handoff must preserve explicit follow (no contact upload or auto-follow) and useful zero-content states. |
| Friend → ACK/reply | ACK requires a deliberate confirmation; replies render in `#grind-thread`. Server policies deny blocked writes. | Lost write responses must not trigger automatic social retries. Deleted replies and blocked actors need neutral handling. | Keep ACK/reply separate user actions. Show failure without inventing success; the user checks the thread before retrying an uncertain social write. |
| Response → exact conversation | `/?inbox` shows ACK/reply/follow notifications. Reply links include run ID, reply ID and `#reply-…`; the target is resolved before it can be called missing. `Back to Responses` is retained. | A reply can be older than page one or removed; a run can be withdrawn/deleted between inbox and click. | Existing behavior is correct locally: resolve exact reply, focus it, directly render a deep target beyond the paging cap, and preserve return navigation for unavailable runs. |
| Return → second post | Responses is the human reason to return. Feed/Post/My runs remain available after the conversation. Capture records a new measurement revision for a new sitting. | The product has no real day-two observation. A leaderboard is not a substitute for another person's response. | In the two-person test, one builder returns later through Responses, then captures a genuinely new sitting. Never turn a retry or duplicate into a “second run.” |

## Failure and boundary matrix

| State | Expected result | Current evidence |
|---|---|---|
| Signed out on public/link run | Read card; sign in only for follow/ACK/reply; return to target after auth. | Exists in source; disposable social route tested. Hosted social use not performed. |
| Signed out on private run | Neutral unavailable state, no metadata leak. | Disposable browser passed. |
| Signed out with import draft | Preview remains private; sign-in stores payload and edits; no save. | Source and account browser fixture cover cancellation. Hosted callback unverified. |
| Zero public content | Explain what a real card contains and offer Post; do not fabricate a feed. | Exists in source and cold-first-minute fixture. |
| Cancelled auth | Clean provider error from URL, explain cancellation, retain draft, offer retry. | Disposable account fixture exists; hosted unverified. |
| Expired/used auth link | Explain expiration and start again; retain same-tab draft where storage remains. | Error mapping exists; hosted unverified. |
| Save connection failure before receipt | Preserve draft/audience; label result unconfirmed; no automatic retry. | Imported and manual paths are covered by the changed browser check. |
| Save succeeds but response is lost | Same message as any uncertain response; explicit retry finds exact prior row. | Imported capture passed at baseline; manual fallback is the concrete fix in this PR. |
| Duplicate imported save | Open first run by `(profile_id, measurement_revision)` and say new caption was not applied. | Disposable browser passed. |
| Duplicate manual save | Open first run by browser-generated run UUID; do not insert a second row. | Added in this PR; disposable acceptance required on final source. |
| Unknown metrics | Store/render null; never infer duration, files, commits or outcomes. | Cursor and Grok safe route walks kept unsupported values unknown. |
| Only me | Owner only; not a friend/share route. | Source/policies and disposable tests, not hosted use. |
| Anyone with link | Unlisted readable URL; not feed/profile. | Source/policies; live two-account use outstanding. |
| Public | Feed/profile/public preview; deliberate audience only. | Source and disposable tests; live two-account use outstanding. |
| Withdrawn to private | Friend loses access; owner retains run. | Disposable privacy path exists. |
| Deleted run | Discussion target unavailable; Responses explains it without a link. | Disposable Responses test passed. |
| Deleted reply | Run can still open; exact target says removed/not visible. | Disposable Responses test passed. |
| Unavailable target after inbox click | Neutral run state plus Back to Responses. | Source and disposable exact-return test passed. |

## Ordered build map

Each item stays inside the locked core loop. “Owner request” means a precise handoff recorded here;
no message was sent.

### 1. Prove hosted auth and two-person return

- **User problem:** healthy pages do not prove that a private draft survives real Auth or that
  one person can respond to another.
- **Evidence / route:** live `/api/health` is ready; `/?post`, `/?inbox`, `/?run=` and `/?u=` exist.
  The exact Auth allowlist remains unverified and no two-consenting-user receipt exists.
- **Desired behavior:** two people each save one reviewed safe run, open the other profile,
  follow, ACK/reply, and later return through Responses to the exact conversation.
- **Boundary:** no production SQL/Auth changes in this assignment; follow PR 23's owned script.
- **Owner:** Oscar for approval/config access; Grok Bot for test coordination and first-user polish.
- **Dependency:** verify `https://agentic-strava.vercel.app/**` in the shared callback allowlist
  without changing Site URL; agree identities, safe sessions and audience.
- **Acceptance proof:** PR 23's checklist completed by two consenting people, with redacted
  device/step evidence. Fixtures do not count.

### 2. Make every Save retry honest and idempotent

- **User problem:** a response can be lost after the server commits. Baseline import UI said
  nothing was posted even while the test database contained the run; manual Save could duplicate.
- **Evidence / route:** `site/index.html` `wireComposer()` and `importRun().showRecovery()`;
  `scripts/check-post-recovery.py` lost-response gate.
- **Desired behavior:** preserve the exact draft/account/audience, state that receipt is unknown,
  never retry automatically, and check one stable save identifier before retrying.
- **Boundary:** browser-scoped UUID for manual fallback; existing measurement revision for
  captured imports; no migration or privacy weakening.
- **Owner:** this PR.
- **Dependency:** existing UUID run primary key and owner RLS. PR 26 also changes `site/index.html`
  for reserved Close friends work; integrate line-by-line without adopting its new audience here.
- **Acceptance proof:** forced offline and committed-but-response-lost tests each create at most
  one row, preserve fields/audience, and name the final audience.

### 3. Put Cursor capture in the user's own project and require exact selection

- **User problem:** current onboarding starts in the Pacecard source repository and “latest”
  can select a different sitting than the one the builder intends to share.
- **Evidence / route:** `docs/CURSOR.md` steps 1–4; `.cursor/mcp.json`;
  `agentgrinder/mcp_server.py` `list_sessions`/`preview_run`; CLI `--list`, explicit session and
  `--pick`. Safe local walk proved exact CLI selection works but is undocumented.
- **Desired behavior:** from the user's own project, install/enable the local MCP or CLI, list
  eligible sittings, select one exact project/session/sitting, preview, then hand off to the
  approved hosted origin.
- **Boundary:** local metadata only; no cloud claim about laptop files; no raw transcript in an
  agent payload.
- **Owner request:** Pacecard hook/ridge run
  `bc-d22ad316-cdde-45dd-9094-c094a8b1eec1` (running when rechecked) for capture hook/ridge;
  Cursor integration owner for exact-session selector/docs.
- **Dependency:** reconcile workspace MCP installation with Cursor's documented
  [project and user MCP configuration](https://cursor.com/docs/mcp). Project `.cursor/mcp.json`
  is rooted in the person's workspace; `~/.cursor/mcp.json` is global. Do not require cloning
  Pacecard as the active work project.
- **Acceptance proof:** clean machine, two eligible sittings in different projects, chosen
  non-latest sitting appears in preview, no prompt/code/path is exported, hosted Save remains a
  human click.

### 4. Complete the Grok owner handoff

- **User problem:** a source kit is not an installed workflow, and placeholder origin text makes
  the final destination ambiguous.
- **Evidence / route:** `docs/GROK-BOT.md`, `docs/GROK-PUSH.md`,
  `templates/grokbot/INSTALL.md`, skill `SKILL.md`, and `scripts/preview.py`.
- **Desired behavior:** bot explicitly exports/selects one sitting on its own cloud computer,
  invokes the complete installed source kit, and returns
  `https://agentic-strava.vercel.app/#import=…` to its human for account/audience review.
- **Boundary:** no template rebuild in this PR; no laptop access claim; no automatic publish,
  follow, ACK or reply.
- **Owner request:** Grok Bot owner.
- **Dependency:** current official Grok docs establish a persistent shared cloud computer with
  filesystem/browser/terminal ([Grok Bot](https://cursor.com/docs/grok-bot)) and
  [skills as files](https://cursor.com/docs/skills); they do not establish Pacecard-native export
  or one-click marketplace installation for this source directory.
- **Acceptance proof:** separate receipts for source available, installed on a second bot, real
  export previewed, and owner-saved hosted run. Only the first is established.

### 5. Preserve exact Responses navigation under all target states

- **User problem:** a response is useful only if it returns the builder to what the friend said.
- **Evidence / route:** `site/social.js` `notificationHref`, `thread`, `inbox`;
  `site/index.html` `responseReturnLink`; PR 13 findings R2-01/R2-02 are already represented on
  main.
- **Desired behavior:** open exact reply, focus it, keep Back to Responses, and handle
  old/deleted/private targets without a false deletion claim or privacy leak.
- **Boundary:** no new inbox feature surface.
- **Owner:** existing core implementation; no code change needed in this PR.
- **Dependency:** `strava` RLS and notifications stay consistent when a run/reply is removed.
- **Acceptance proof:** existing disposable two-account browser check passes deep reply beyond
  325 loaded rows, missing reply, missing/private run, unread marking and return.

### 6. Turn zero-content/friend discovery into the first real conversation

- **User problem:** without another builder, Feed and Responses cannot demonstrate why to return.
- **Evidence / route:** `/?explore`, `/?people`, `/?following`, empty `/?inbox`.
- **Desired behavior:** explicit find/follow/profile-share choices and truthful empty states lead
  to one consenting friend's response.
- **Boundary:** no invented users, contact upload, auto-follow, auto-ACK or broad outreach.
- **Owner request:** Grok Bot's reserved friends/first-user polish.
- **Dependency:** item 1's consenting participant; public or link-visible safe runs.
- **Acceptance proof:** observed friend arrival and deliberate response, not seeded fixture data.

### 7. Validate day-two behavior before adding motivation surfaces

- **User problem:** the product promise is return for people, not one-time card generation.
- **Evidence / route:** Responses → exact thread → Post/My runs; no real later-day observation.
- **Desired behavior:** builder returns because a person responded, continues the conversation,
  and optionally posts a genuinely new sitting.
- **Boundary:** no streak, ranking-as-quality, coaching, challenge or Crew.
- **Owner:** product coordinator after item 1.
- **Dependency:** a real response and a later visit.
- **Acceptance proof:** one participant later opens Responses and reaches the exact conversation;
  a second post, if made, has a distinct capture revision.

### 8. Resolve current scope/repository conflicts without reverting owners

- **User problem:** current main and live bytes contain the PR 20 segment leaderboard, while the
  governing completion plan explicitly holds comparison/ranking until real two-person use.
- **Evidence / route:** merged PR 20, `/?segment=`, `site/segments.js`,
  `supabase/strava/001_segments.sql`; the migration is intentionally unapplied.
- **Desired behavior:** the locked core remains the priority and ranking is not presented as
  quality or the reason to return.
- **Boundary:** this PR does not revert PR 20, expand it, invoke the route in acceptance, or run
  its SQL.
- **Owner:** Oscar resolves the product-state mismatch.
- **Dependency:** item 1 real-use evidence and explicit decision.
- **Acceptance proof:** recorded owner decision: continue holding the surface or deliberately
  reopen scope after acceptance.

PR 26 now owns Close friends and OG implementation. Close friends remains later/outside this
assignment even though that PR is open; this review neither adopts its audience nor edits its SQL.
The same applies to the reserved card ridge and Grok capture/template lanes.

## State ledger

| Capability | Exists in source | Tested locally in this run | Hosted | Used by real consenting people |
|---|---:|---:|---:|---:|
| Pacecard landing/feed/Post/Profile shell | Yes | Yes, phone/desktop cold and fixture paths | Yes, byte-matched | Unverified |
| Cursor explicit-path + sitting capture | Yes | Yes, safe TEST DATA session | CLI is local; import destination is hosted | Unverified |
| Cursor friendly own-project exact selector | Partial | CLI primitives only | No separate hosted component | No |
| Grok adapter/source kit | Yes | Labelled samples only | Hosted import URL generated | Second-bot install/use unverified |
| Draft through cancelled/failed auth | Yes | Disposable fixture | Allowlist/callback unverified | Unverified |
| Imported idempotent save/recovery | Yes | Baseline passed; wording changed here | Prior implementation hosted | Unverified |
| Manual idempotent save/recovery | This PR | Final disposable check required | Not hosted | No |
| Public/link/private policy paths | Yes | Disposable data | Database healthy; exact live use not performed | Unverified |
| Follow/Following/ACK/reply | Yes | Disposable two-account fixture | Source is hosted | Unverified |
| Exact Responses return/unavailable target | Yes | Disposable two-account fixture passed | Source is hosted | Unverified |
| Continue in Cursor | Yes | PR 24 local evidence; not relaunched here | Yes | Unverified |
| Segment leaderboard | Yes | Not exercised; outside scope | Client source hosted; SQL state unknown/unapplied by this run | Held pending real use |
| Close friends/OG | Reserved PR 26, not this base | Owner reports disposable tests | Not established | No |
| Two-person acceptance and day-two return | Checklist in PR 23 | Fixtures do not count | Not established | No |

## What this PR changes

Only the unowned save boundary is changed:

1. Imported-save failures no longer make the false claim that nothing was posted after an
   uncertain response.
2. Manual fallback saves receive a browser-scoped UUID, retain their draft and audience in the
   current tab, and check that exact UUID before a deliberate retry.
3. The browser acceptance check forces both offline and committed-but-response-lost paths and
   proves that retry does not create a second row.

No capture hook, Grok adapter/template, friend discovery, card ridge, Close friends, OG,
leaderboard implementation, database migration, Auth configuration or production data is changed.
