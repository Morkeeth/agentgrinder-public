# STRIVE new-user journey and build map

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
  title `STRIVE`.
- Live `/api/health`: HTTP 200, 41 bytes,
  `{"service":"strive","database":"ready"}`.
- Receipt-backed deployment: `726f8a57c4e95f6c1d62c789f8e0ddeb437e11b6`, Vercel
  `dpl_3MayWTLoGMc4VsC5wrhrPDDrLxBg`. That release includes merged PR 21 identity and PR 22
  first-minute work.
- After injecting the public deployment configuration, the live index was byte-identical to
  `a01f251da44b7bcee2ae3d6a2b1e48bd0193cad9` and to the unchanged index at the starting merge
  SHA when this review fetched it. This is a later byte observation, not a Vercel deployment
  receipt: it does not establish which post-`726f8a5` commits were deployed. `726f8a5` remains
  the only receipt-backed deployed commit supplied to this review.
- No production identity, post, follow, ACK, reply, message, SQL or Auth setting was used or
  changed. Browser integration used disposable identities labelled `TEST DATA`.
- The shared Auth redirect allowlist entry `https://agentic-strava.vercel.app/**` remains
  unverified. This is a configuration-verification gap, not evidence of a broken callback.
- Current Cursor documentation supports project/global `mcp.json`, explicit repository/branch
  selection for Cloud Agents, durable Cloud agent/run IDs, conversation search, and prompt
  [deep links](https://cursor.com/docs/reference/deeplinks). It does not document a public deep
  link that selects an exact local Cursor sitting or sends a third-party preview into a hosted
  Save flow. STRIVE's hosted `#import=` URL is its own human-review handoff, not a Cursor
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
- Post led to a clone-and-run command for the STRIVE repository, then a separate sign-in action.
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
sitting. STRIVE reads only allowlisted measurements and first opens a private preview. The
builder writes the public explanation and optional output link, checks the signed-in account,
chooses Only me, Link or Public, and presses Save once.

A friend receives a saved public or link URL, understands the caption and output before the
metrics, opens the builder's profile, and chooses to follow, ACK or reply. Those actions require
the friend's own account. The builder later sees a Responses item, opens the exact run and exact
reply, and can return to Responses. On the next day, a response is the reason to return; a second
safe capture is the action available after the conversation.

Cursor and Grok Bot are different capture origins, not different identities or destinations.
Both hand the human to the same STRIVE account, audience control and saved-run route.

## Transition map

| Transition | What exists now | Stop or risk | Required behavior |
|---|---|---|---|
| Discover → understand | `/` and `/?explore` show the STRIVE promise, a sample/featured card, Feed and Post. Public cards put caption and output above the trace. | A cold visitor can browse, but a mostly empty feed cannot prove the social value. Sample content must not look like adoption. | Keep the first action “Post a run”; label every sample and never seed invented people or engagement. |
| Discover → own project | The live first-run command clones this product repository, while `docs/CURSOR.md` says to open this repository to obtain its workspace MCP. | A person came to share work from **their** repository. The product/contributor repository switch is unexplained, and the default command picks the latest eligible sitting rather than asking which one. | Start from the person's own project, install/enable the capture integration there, list eligible sittings without transcript text or paths in agent payloads, and require an exact selection before preview. |
| Cursor work → capture | `grind --harness cursor [SESSION] --pick N`, `--list`, MCP `list_sessions`, `preview_run`, and `a2a_propose_publish` exist. A safe explicit-path walk correctly labelled `my-own-project`, counted two typed turns and one tool call, and left duration/commits unknown. | `docs/CURSOR.md` documents “latest eligible” only. The MCP list identifies only each harness's latest file, so it cannot make an exact sitting choice. A cloud VM cannot read a laptop's Cursor sessions. | A local-only selector on the user's computer must identify the chosen project/session and sitting. Cloud agents must state that they see only their VM. |
| Grok work → export | The adapter reads explicitly supplied Grok JSONL; the source kit helper returns allowlisted metrics and a private import URL without a request. Labelled samples produced 2/3 and 7/7 typed-turn/tool-call counts. | Source availability is not installation. Current skill/docs still use placeholder hosted origins even though the approved live origin exists. No second bot or real export was observed here. | Grok owner installs the complete source directory on a second bot, explicitly selects a real export on that bot's computer, uses the approved STRIVE origin, and returns the private preview URL to the human. |
| Capture → preview | `#import=` carries allowlisted fields in the fragment. `importRun()` validates it, labels sample previews, displays all imported fields, says “not posted,” and renders the white card/blue trace. | A copied/truncated fragment cannot be recovered. Rig notes are described as profile data even for Only me and therefore need careful review. | Invalid links say nothing was posted and point back to capture. Unknown metrics remain absent/unknown. The person reviews every field before auth or save. |
| Preview → auth | `stashImport`, `ag_import_edits`, `ag_auth_return` and profile onboarding preserve the capture and typed title/caption/link/audience in session storage. Cancellation and provider failure have explicit recovery copy. | The exact hosted Auth allowlist is not readable from this run. | Verify callbacks without changing shared Site URL. If browser storage is unavailable, stop before redirect and tell the user to retain their local capture. No auth event may post a run. |
| Auth → account/profile | One shared Supabase Auth user maps to one schema-qualified `strava.profiles` row. Only GitHub is enabled (`PROVIDERS_ENABLED`); email is not offered and X is gated. | “One identity” is a product invariant, but a user still needs to verify the account shown after returning from a provider. | Show account/handle before Save. Keep Cursor/Origin as integrations, never login providers. |
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
| Link (followers and close friends) | Relationship-gated URL; not feed/profile. Bearer alone is not enough. | Source/policies; migration 010; live two-account use outstanding. |
| Public | Feed/profile/public preview; deliberate audience only. | Source and disposable tests; live two-account use outstanding. |
| Withdrawn to private | Friend loses access; owner retains run. | Disposable privacy path exists. |
| Deleted run | Discussion target unavailable; Responses explains it without a link. | Disposable Responses test passed. |
| Deleted reply | Run can still open; exact target says removed/not visible. | Disposable Responses test passed. |
| Unavailable target after inbox click | Neutral run state plus Back to Responses. | Source and disposable exact-return test passed. |

## Ordered build map

Each item stays inside the locked core loop. “Owner request” means a precise handoff recorded here;
no message was sent.

### 1. Capture from the builder's own project into one private hosted preview

- **User problem:** current Cursor onboarding starts in the STRIVE source repository and
  “latest” can select a different sitting than the one the builder intends to share. Grok source
  exists, but a second bot installation and explicit real export remain unverified.
- **Evidence / route:** `docs/CURSOR.md`, `.cursor/mcp.json`, CLI `--list`, explicit session and
  `--pick`; `docs/GROK-BOT.md`, `docs/GROK-PUSH.md`, `templates/grokbot/` and its preview helper.
  Safe local walks proved exact Cursor CLI selection and labelled Grok sample preview, not the
  complete owner workflow.
- **Desired behavior:** from the person's own project, list and deliberately choose one exact
  Cursor project/session/sitting; or explicitly select one Grok JSONL export on the bot's cloud
  computer. Both return a private
  `https://agentic-strava.vercel.app/#import=…` preview to the human.
- **Boundary:** no capture or template implementation in this PR; no laptop-session claim from
  Cloud; no raw transcript in an agent payload; no automatic publish.
- **Owner request:** Grok Bot owns Cursor session selection and Grok export → private hosted
  preview implementation. Existing capture lanes remain separate.
- **Dependency:** Cursor's documented
  [project/global MCP configuration](https://cursor.com/docs/mcp), and Grok's documented
  [persistent cloud computer](https://cursor.com/docs/grok-bot). Neither documents a STRIVE
  native Save or a public deep link selecting an exact local Cursor sitting.
- **Acceptance proof:** clean machine with two Cursor sittings in different own projects selects
  the requested non-latest sitting; a second Grok Bot invokes the installed complete source kit
  on an explicitly selected real export; both previews use the live origin, expose only
  allowlisted fields, keep unknowns unknown and stop before Save.

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

### 3. Make the first post understandable and deliberate

- **User problem:** the cold Post route switches from “share my work” to cloning STRIVE, before
  clearly showing own-project selection. With no public runs visible, the first builder also
  cannot rely on social proof to explain why the card is useful.
- **Evidence / route:** live `/`, `/?post`, `/?explore`; `importRun()` preview; `runCard()`. The
  cold browser saw only a labelled sample and empty discovery. It did see accurate private-first
  and sign-in copy.
- **Desired behavior:** preview the exact white card/blue trace before any write; put the
  builder-authored caption and optional output link first; show account and non-default
  Only me/Link/Public choice; Save once and name the resulting audience.
- **Boundary:** no invented public content, new discovery feature, auto-follow/ACK, ranking,
  Close friends or card-ridge work. Grok-owned first-user/capture polish stays separate.
- **Owner:** this PR owns the journey evidence and unowned Save/first-post boundary; Grok Bot owns
  capture-side first-user clarity.
- **Dependency:** item 1 supplies one exact reviewed preview; item 2 supplies safe Save.
- **Acceptance proof:** at phone and desktop widths, a fresh signed-in TEST DATA account can
  inspect all imported fields, cannot save without caption/audience, sees unknown metrics as
  unknown, and lands on one saved run whose status names its audience.

### 4. Preserve respond → exact conversation → return

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

### 5. Prove the hosted loop with two people and one later return

- **User problem:** healthy bytes and disposable fixtures do not prove a private draft survives
  real Auth or that one person can respond to another and bring them back.
- **Evidence / route:** live `/api/health` is ready; `/?post`, `/?u=`, `/?run=` and `/?inbox`
  exist. Deployment receipt `726f8a5` includes merged PRs 21/22. The exact Auth allowlist and
  two-person acceptance remain unverified; PR 23 owns the checklist.
- **Desired behavior:** two consenting people each save one reviewed safe run, open the other's
  profile, follow, ACK/reply, and return through Responses to the exact conversation. One returns
  later because of that response and may capture a genuinely new sitting.
- **Boundary:** no production SQL/Auth changes or contact from this PR; no fixture counted as
  acceptance; no leaderboard, streak or invented engagement as a return reason.
- **Owner:** Codex owns exact Auth redirect confirmation; Grok Bot coordinates the real
  two-person test; Oscar approves participants/accounts/audiences and records the product result.
- **Dependency:** confirm `https://agentic-strava.vercel.app/**` without changing the shared Site
  URL, then follow PR 23 with two approved identities and safe sessions.
- **Acceptance proof:** PR 23's checklist completed in both directions with redacted
  device/step evidence, plus one later Responses visit that reaches the exact reply. A second
  post, if made, has a distinct capture revision.

PR 26 now owns Close friends and OG implementation. Close friends remains later/outside this
assignment even though that PR is open; this review neither adopts its audience nor edits its SQL.
The same applies to the reserved card ridge, friends/sharing lanes and Grok capture/template
implementation.

PR 20's segment client is present in current main despite the earlier hold. No deployment receipt
for that later main commit is claimed. This map records the coordination mismatch only; it does
not add a segment build item, touch leaderboard code or run its SQL.

## Delivery states

- **Running:** this Cursor Cloud review run is
  `bc-521cf5c3-2609-4e09-959f-321690c9d56b`. Grok Bot's capture/template work remains in its
  separate owner lane `bc-21f9d59a`; it is not merged into this PR.
- **Built:** this branch contains the map and unowned Save-continuity fix. Grok capture/template,
  friends, sharing, card-ridge, Close friends/OG and segments are not built here.
- **Tested:** required contributor checks, 359-test Python suite, production build, 37-check
  disposable Save recovery, disposable exact Responses return, and phone/desktop browser
  screenshots passed. These use labelled test data where writes are required.
- **Deployed:** only `726f8a5` / Vercel `dpl_3MayWTLoGMc4VsC5wrhrPDDrLxBg` has a supplied
  deployment receipt. This PR is not deployed. Later live bytes are an observation with
  unresolved deployment provenance.
- **Used:** no two-consenting-user or later-day return is established. PR 23 remains the
  acceptance script; fixtures and owner-only checks do not count.

## State ledger

| Capability | Exists in source | Tested locally in this run | Hosted | Used by real consenting people |
|---|---:|---:|---:|---:|
| STRIVE landing/feed/Post/Profile shell | Yes | Yes, phone/desktop cold and fixture paths | `726f8a5` receipt; later bytes observed, provenance unresolved | Unverified |
| Cursor explicit-path + sitting capture | Yes | Yes, safe TEST DATA session | CLI is local; import destination is hosted | Unverified |
| Cursor friendly own-project exact selector | Partial | CLI primitives only | No separate hosted component | No |
| Grok adapter/source kit | Yes | Labelled samples only | Hosted import URL generated | Second-bot install/use unverified |
| Draft through cancelled/failed auth | Yes | Disposable fixture | Allowlist/callback unverified | Unverified |
| Imported idempotent save/recovery | Yes | Baseline passed; wording changed here | Prior implementation hosted | Unverified |
| Manual idempotent save/recovery | This PR | 37-check disposable recovery walk passed | Not hosted | No |
| Public/link/private policy paths | Yes | Disposable data | Database healthy; exact live use not performed | Unverified |
| Follow/Following/ACK/reply | Yes | Disposable two-account fixture | Source is hosted | Unverified |
| Exact Responses return/unavailable target | Yes | Disposable two-account fixture passed | Source is hosted | Unverified |
| Continue in Cursor | Yes | PR 24 local evidence; not relaunched here | No deployment receipt claimed | Unverified |
| Segment leaderboard | Yes | Not exercised; outside scope | No deployment receipt claimed; SQL unverified/unapplied by this run | Held pending real use |
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
