# STRIVE

Every run your agent made, on a card you can share.

**Capture → preview → post → browse.**

## The app

- Feed: public run cards from builders.
- Post a run: import a real session, review the card and choose to publish.
- My runs: your session history.
- Profile: your public runs and identity.
- Follow, XUDOS and reply: one reaction (cheer this run), then discussion.

Audience: **Public** is listed and open to anyone signed out at `/r/<id>`. **Private** is owner-only. Every other audience (**Link**, Close friends, crew) is relationship-gated: a signed-in reader needs a follow or close-friends relation with the author (or be the owner). Strangers see the neutral private page. Link is not globally readable from the URL alone. Browser and database agree: migration `supabase/strava/010_link_relationship.sql` must ship with deploy.

Cursor first. Keep the white card and blue activity trace. Prefer a clean, minimal card: one visual plane, a short route, two or three measured facts, identity, and Share, XUDOS and Follow. Tool-call totals use one source across `/r/`, the SPA strip, Explore and share (`tool_calls`, else `ridge_tool_calls`); map scrub labels say "in this slice" so a peak bin is never read as the run total. Code Route appears when the run stored route data; Cursor and Codex capture attach a compact measured route from files and commits when those counts exist, without inventing output links. A measured edit+commit route draws the Code Route map (same label as `/r/`), even on one project; a lonely declared stop stays a short work path. An optional author-selected lifestyle scene may sit beside a genuine output image; the scene is atmosphere, not proof, and photos are never auto-published from a camera roll. Day runs use a multi-project route; a quick fix is before → change → result; one agent lane is action → output. Provenance and raw metrics stay under Explore this run. Unknown measurements stay unknown. An external community or event is at most one optional author-chosen chip/link on the run card - not a directory, not primary nav, and not a calendar integration in this release.

Card ruling, 22 September: a run card opens with an OUTCOME, not a metric identity. One sentence taken from the run — an author-declared outcome with a receipt, the subject of a commit git recorded in the window, the commits counted, or a declared link — and `No shipped output recorded` with the reason when the run shipped nothing. Under it, one number the run can prove (checks passing, commits landed, files changed, else tool calls) and no hero at all when it can prove none. A measurement the run does not have is left out of the card and named in one sentence of prose; an em-dash is never a row. The title is the repository and the work, never a filesystem path, and no home directory or account name reaches a card. Identity is the GitHub account this machine already holds (read locally, sign-in unchanged) or a neutral label — never "you". The brand string on every card is STRIVE.

One selected insight, 22 September: a card may carry ONE line the author chose — the verified outcome, or the correction that mattered — at the head of the Code Route group. It is absent by default, it is shown only while it is bound to a receipt the same run already carries, and it is never read out of a transcript: no parser writes it. The scope sentence says what the line is a fact about, so a night run over many sessions is never called "this run". It renders with no account at 390 px and says on its face that a local card is not published. It stays local until the hosted runs table has a column for it.

The author's choice of visual, 23 September: a run card carries ONE hero visual, and the author picks it in the private preview. The options are Size map (the repository's files, area = the real line count at the end of the run, colour = lines changed in a keyed three-step ramp), Folder line (up to six folders in first-visit order, with returns), Elevation (cumulative lines changed against the clock) and Screenshot (the author's own image, on the existing image path). The default is the Size map when the capture measured file data, and the current ridge when it did not. A visual the run has no data for is not offered, and a choice that outlives its data falls back to the default rather than drawing an empty frame. Every view of one run adds up to the same total and states the source; a deleted file has no box on a map, so its lines are one sentence under it. No file name reaches public bytes: the per-file rows are anonymous and only folder names, counts and totals are words on the card. Light mode, IBM Plex Sans, sentence case, Strava orange `#FC4C02` as the one accent on these marks — the app's blue trace is unchanged. Beside the hero a run may carry an agent gear chip, trophies from measured data only, and one quote the author picked: the quote is never read out of a transcript (line 21's rule), and `chosen_by: author` is what makes an auto-filled one impossible to write by accident. Like the selected insight, the choice stays local until the hosted runs table has a column for it.

Free posting and browsing. Recognition comes from real people seeing and responding to work. No mandatory model calls, coaching flow, practice programme, score dashboard or challenges in the main app. Crews stay out of primary navigation; the first useful Crew is Oscar and Eric's two-person feed where each builder posts a real run and can return through Responses, not an empty feature page and not an official Grok Bot club.

## First useful test

Two people each post a safe real run to the hosted app. Each can open the other’s profile, follow and respond. A stranger understands the card without a tour. Prefer proving that loop inside one shared Crew feed when both people have joined. The service exists; this test still needs two people who are not the owner.

## Two repositories

This repository is the public product. Morkeeth/agentgrinder remains the hackathon build. Historical code and docs are retained under `archive/hackathon-2026-09/` for reference; they do not define this product’s scope.

## What exists · 15 September

- Hosted at [agentic-strava.vercel.app](https://agentic-strava.vercel.app) on Vercel. App data lives in a dedicated `strava` schema in a Supabase project whose Auth is shared with the hackathon build; app data and profiles are separate. `/api/health` reports the database state.
- Sign-in with GitHub or an email link. One profile per account, with a handle and display name you can edit.
- Feed, post a run, My runs, profiles, follow, Following, XUDOS, reply and a Responses inbox. The public feed is new and mostly empty.
- Local capture: `python3 -m agentgrinder grind --harness cursor` reads a real Cursor session with no keys and writes a card to `./grind.html`.
- Private Cursor hook: `python3 -m agentgrinder hook install --harness cursor` watches completed local composers, dedupes by composer id and opens a loopback Pacecard without posting.
- Pacecard ridge: Cursor bubble timestamps draw tool calls over wall time with worker activity behind one blue line. Captures without that clock use call order and say so.
- A Grok Bot post-run template in `templates/grokbot/`. It is source to install; no second bot has been observed using it.

## Open

- X sign-in. The account panel says it is not available; no provider is configured.
- Origin (Cursor’s code forge) repository linking. No app is registered and no button is enabled.
- Close friends: privately mark people and post to a Close friends audience. Needs server-enforced access and revocation tests, not a client-side filter. No contact upload or automatic following is implied.
- Grok Bot verification: a second bot installing the kit and previewing its own export.
- A verified first useful test with two people who are not the owner.
- External event calendars (Grok Bot, Claude, Devin, Codex) stay discovery sources in the journey brief only. No Luma or community directory in the app.

Brand decision, 16 September: the public product is STRIVE, tagline "Post your strides". Pacecard is rejected. Keep the white cards and blue activity trace. The address remains `agentic-strava.vercel.app`. The name and tagline are held in one place, `server/brand.mjs`; internal identifiers, the package name, the CLI command and the `strava` schema are unchanged.
