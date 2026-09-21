# Pacecard end-to-end flows

Reviewed 15 September 2026. This map adapts the useful parts of Strava's activity, profile,
recognition, conversation, sharing, privacy and first-activity paths to agent work. It does not
copy athletic language, rankings, segments, streaks or score dashboards.

The product loop remains: **capture → private preview → deliberate audience/Save → friend
response → Responses return → next real capture**. The white card and blue activity trace remain
the visual anchor. Unknown measurements remain unknown.

## Flow map and owned backlog

### 1. Landing / cold start · signed out

1. **Current:** open `/` → see a labelled SAMPLE white card and blue trace → read the promise →
   choose Post or Feed. An empty Feed states that no public runs are visible and invents nothing.
2. **Strava-inspired improvement:** lead with one activity-shaped story, then one primary action:
   **Post your first run**. Name Cursor and Grok Bot without hiding Claude Code or Codex. Keep the
   sample provenance adjacent to the sample.
3. **This PR:** preserves the sample-first phone layout, names all four harness paths and keeps the
   empty Feed's Post action.
4. **Backlog / lane:** first real public card and social proof must come from consenting use, never
   fixtures. Owner: #23 two-person acceptance after deployment.

### 2. Sign-in / Auth return / cancel / error

1. **Current:** choose Sign in → pick GitHub or email → provider returns to an allowlisted route.
   A capture draft and edits are stashed before redirect. Cancel/error copy says nothing changed;
   the same-tab draft survives where browser storage is available.
2. **Strava-inspired improvement:** explain why identity is needed, what remains private and where
   the person will return before leaving the app. Keep cancel and retry calm and reversible.
3. **This PR:** the dialog says sign-in returns to the current preview or social action and that
   closing/cancelling posts nothing. Provider-specific errors remain inline.
4. **Backlog / lane:** confirm `https://agentic-strava.vercel.app/**` in shared Auth without
   changing the shared Site URL. Owner: Codex. Hosted acceptance: #23.

### 3. Profile setup / onboarding

1. **Current:** first authenticated return → choose handle and display name → create one
   `strava.profiles` row → resume the pending route.
2. **Strava-inspired improvement:** make identity, not totals, the profile's first layer. Explain
   that the handle is the public address, the display name is the human label and neither grants
   repository access.
3. **This PR:** clarifies both fields and changes the action to **Create Pacecard profile**. Recent
   runs now precede collapsed profile totals.
4. **Backlog / lane:** verify GitHub-only, email-only and duplicate-handle cases in #23. No Auth or
   profile-schema change is required.

### 4. Capture from the builder's own project

1. **Cursor current:** work in the builder's repository → run the local capture → select a Cursor
   sitting → generate a hosted-origin `#import=` preview. Main still presents a clone-first
   command; exact own-project selection is in #27.
2. **Grok Bot current:** explicitly select one JSONL export on the bot's computer → run the source
   kit helper with `--base-url https://agentic-strava.vercel.app` → receive a private preview URL.
3. **Strava-inspired improvement:** make capture feel like choosing one completed activity:
   identify project and exact sitting/export before preview, with no automatic latest-session
   surprise and no upload.
4. **Backlog / lane:** #27 owns exact Cursor sitting and Grok export selection. This PR changes
   presentation only and keeps both adapters intact. A second-bot real-export receipt remains
   unverified.

### 5. Private preview + metrics hierarchy

1. **Current:** open the fragment → validate allowlisted fields → show imported measurements →
   write title/caption/output → choose audience → inspect the generated card. SAMPLE previews
   cannot save.
2. **Strava-inspired improvement:** activity story first: title, caption and output link before
   stats. Put optional/recorded detail behind disclosure. Keep unknown values as dashes/Unknown,
   not zero.
3. **This PR:** moves story and privacy controls ahead of the recorded-measurement disclosure;
   the card remains immediately below with caption/output before project/harness/time and stats.
4. **Backlog / lane:** #27 supplies the exact selected source; #28 preserves draft fields through
   retry. Do not add inferred metrics.

### 6. Audience choice + Save + idempotent retry

1. **Current:** leave audience unset → deliberately select Only me, Link or Public → press Save.
   Imported retries use a measurement revision; #28 adds the complete uncertain-response and
   manual idempotency path.
2. **Strava-inspired improvement:** privacy language must describe reach at the decision:
   **Only me - just you**, **Link - followers and close friends**, **Public - Feed and profile**.
3. **This PR:** aligns those labels and success copy across manual/import/edit controls. It does
   not alter Save identity, retry or server policy.
4. **Backlog / lane:** #28 owns no-auto-retry, retained draft/audience and exact prior-save lookup.
   #23 exercises all three audiences with disposable/approved accounts.

### 7. Success / share link / public OG

1. **Current:** successful Save opens `/?run=<id>`; public/link runs can copy a URL; Share card is
   lower on the activity detail.
2. **Strava-inspired improvement:** put the saved destination and one large next action directly
   under the card. Public: copy public link or open the clean share card. Link: copy the
   relationship-gated URL for followers and close friends. Only me: explain that sharing requires an audience change.
3. **This PR:** moves audience-aware share success directly below the card and makes the relevant
   next action primary. It adds no write or OG endpoint.
4. **Backlog / lane:** #26 owns public-only Pacecard OG. Its Close friends migration is separate
   and not pulled into this flow.

### 8. Friend arrival · run → profile → follow

1. **Current:** open a public/link run signed out → read builder/story/output/stats → sign in for a
   social action → open the builder profile → deliberately Follow.
2. **Strava-inspired improvement:** the activity is the acquisition page. Put **Open builder
   profile** directly below it; keep Follow beside identity and explain what Following changes.
3. **This PR:** promotes the profile action below the card and keeps profile identity/recent runs
   above totals. No automatic follow or fabricated follower count.
4. **Backlog / lane:** #23 proves return after real Auth and target-unavailable behavior.

### 9. Following feed empty + Find people

1. **Current:** open Following → if no follows, choose Find people or Discover; if followed people
   have no runs, their profiles remain available.
2. **Strava-inspired improvement:** teach the first social action: find one known handle or follow
   from a real run. State explicitly that nobody is imported or followed automatically.
3. **This PR:** sharpens both empty states and offers Post as the parallel builder action.
4. **Backlog / lane:** real people populate the feed through #23; no ranking or recommended-user
   fabrication.

### 10. ACK + reply on phone

1. **Current:** tap ACK → choose a specific reason → send; or write a reply → post. Both require
   sign-in and blocked writes are denied. Phone actions meet touch targets.
2. **Strava-inspired improvement:** make recognition easy to start like kudos, while retaining
   Pacecard's deliberate reason. Keep the reply composer full-width and close to the activity.
3. **This PR:** keeps ACK visually primary on phone, clarifies **Talk about this run**, and leaves
   the reason picker and server write path intact.
4. **Backlog / lane:** #23 verifies one real ACK and reply each way. No automatic ACK and no
   engagement score.

### 11. Responses → exact conversation → return

1. **Current:** open Responses → filter All/Unread → open exact reply/run/profile → resolve and
   focus the target → use Back to Responses. Removed/private targets degrade neutrally.
2. **Strava-inspired improvement:** describe Responses as the route back to a conversation, not a
   notification score. Empty state should teach post → share → receive; populated state should
   offer the next real run after responding.
3. **This PR:** improves the header/empty copy and adds **Post your next run** after recent
   responses. Exact-link, paging, unread and return behavior remain unchanged.
4. **Backlog / lane:** existing Responses core owns navigation; #23 proves it with two people.

### 12. Day two · response, then second capture

1. **Current:** a later visit can open an unread response and return to the exact run. Post remains
   in global navigation; a new capture creates a new measurement revision.
2. **Strava-inspired improvement:** another person's useful response is the return reason. After
   reading/replying, offer a second real capture without streaks, rankings or synthetic urgency.
3. **This PR:** connects populated Responses to **Post your next run** and keeps capture available
   from the run/profile/Following empty states.
4. **Backlog / lane:** #23 records one later return and distinct second capture. Until observed,
   day-two use remains unverified.

## Tonight merge and acceptance order

1. Merge #27: exact own-project Cursor/Grok capture.
2. Merge #28: journey continuity and idempotent Save.
3. Merge this PR: cross-flow hierarchy, empty states and this map.
4. Merge #23: refreshed two-person checklist.
5. Deploy the merged tip and record a new receipt.
6. Confirm the Auth allowlist.
7. Run the approved two-person walk, then one later Responses return and distinct second capture.

#26 public OG and #29 local Cursor hook/ridge remain next after the core. Do not apply Close
friends SQL through this PR. #20 is merged despite the hold; do not expand segments or
leaderboards.
