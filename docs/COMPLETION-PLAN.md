# Pacecard: from a working loop to people using it

Reviewed with the active Grok Bot on 14 September 2026. This is a proposed execution plan, not a claim of hosting or adoption. Eric's feedback is still pending.

A builder finishes something with an agent, posts a card they want to show, gets a specific response from another builder, and comes back to continue the conversation. The ambition is a daily social home for agent builders, with a simple first experience.

## 1. Land the social loop

Merge the reviewed post, caption, output link, profile and Responses work with the contributor setup. Keep the white card and blue trace. Verify private/public/link audience behaviour, owner-only edits and deletion, captions and safe output links, and desktop/mobile layouts. Record exact tested commits. Keep the Grok adapter in a separate PR so an active worker cannot change the object being reviewed.

## 2. Give people one shared place

Current decision (14 September): use the existing Supabase project for infrastructure and shared Auth, but keep every Pacecard profile, run and social row in the dedicated `strava` schema. Grinder's public tables, functions and Auth triggers are out of bounds. The browser, server and capture clients already have explicit Strava schema adapters; the Grok export adapter and source template kit are in this repository. That is code readiness only: second-bot installation, a real export and a deliberately saved hosted post remain unverified.

Codex owns the pending production work: review/apply the Strava-only bootstrap, expose `strava` through the Data API, configure a separate Vercel project and append the Strava callbacks without changing the shared Site URL. Follow `docs/HOSTED-CUTOVER.md`. Point capture, preview, card links and sign-in to that one approved origin. Do not reuse Grinder app data or claim the app is hosted from local checks.

Deliver a stranger path: open a shared card without signing in → understand what was built → open the output → see the builder → sign in to follow or respond → post a first run. Test errors, cancelled sign-in and empty states as well as success. Public link previews must show only public content; withdrawing/deleting a run must remove access.

Acceptance is two consenting people using their own accounts and safe real sessions: each posts, opens the other's profile, follows and responds; one returns later to see the response. Record observed failures and fix them. A fixture passing locally does not satisfy this step.

## 3. Make posting natural in Cursor and Grok Bot

Run Cursor onboarding from a clean contributor machine. Make the command choose Cursor explicitly and point at the correct service. Show the card before any social write. Preserve unknown measurements and let the builder explain the output.

The Grok export adapter and installable source kit are merged. Next, verify the post-run skill and complete template directory on another bot using an explicitly selected real export. Adapter support, installation, real use and deliberate hosted publication need separate receipts. Both Cursor and Grok previews must lead to the same approved feed.

## 4. Make the response worth returning for

Keep the first surface focused: Feed, Post, My runs, Responses and profiles. A card must explain the work even to someone who did not see the session. Make output links, follow, ACK and reply easy on a phone. Responses should bring the owner back to the exact run and conversation. Fix the largest friction observed in step 2 before adding optional surfaces.

No artificial engagement, activity rankings presented as quality, or automatic social ACKs. Coaching, programmes, Crews and challenges remain outside this app's main scope.

## 5. Eric's product and launch contribution

Hosting and real use are still pending in Codex's lane. Do not contact Eric until the owner approves the recipient, channel and exact message and the stable preview is actually available. Until then the handoff is repository code, the Grok source kit and product direction—not a finished or used app.

When approved and live, send Eric the repository, this plan and the live preview. Ask him to try posting one safe run and critique three things: would he show this card; does a stranger understand it; what would make him return tomorrow?

Invite him to own a small product slice through a normal PR: first-post friction, card hierarchy or response navigation. CONTRIBUTING.md has the local setup; docs/FIRST-PR.md provides starting points. Ask him which initial builder group he would personally bring in and why. Do not treat that as an agreed launch commitment.

## 6. Open the preview with a real reason to join

Proposal: start with a small group of consenting Cursor/Grok builders who each have actual work to show. Choose the group with Eric. Launch around those builds and their conversations, with an immediate route to posting your own. Do not seed invented profiles or synthetic runs into the real feed.

Observe the complete funnel: visitors who open work; builders who finish their first post; posts receiving a response from someone else; builders returning on a later day. Count unique people and distinguish human responses from bot actions. Set targets after observing the first cohort rather than presenting invented thresholds as evidence.

The next build is determined by where real people stop. Public announcement copy and broad outreach come after the working shared URL and first-use observations, with Oscar owning the outward launch.

## Grok Bot's review

Grok Bot agreed to the single feed, human recognition and adapter-first template. Its main correction: a named independent preview URL with real consenting builders must precede further polish. Eric should critique the live loop as soon as it exists, not only this plan. It reported the Grok adapter was absent from social PR head ade7a8f and asked the cloud worker to freeze that PR for review.
