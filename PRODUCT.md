# STRIVE

Every run your agent made, on a card you can share.

**Capture → preview → post → browse.**

## The app

- Feed: public run cards from builders.
- Post a run: import a real session, review the card and choose to publish.
- My runs: your session history.
- Profile: your public runs and identity.
- Follow, XUDOS and reply: one reaction (cheer this run), then discussion.

Cursor first. Keep the white card and blue activity trace. Prefer a clean, minimal card: one visual plane, a short route, two or three measured facts, identity, and Share, XUDOS and Follow. An optional author-selected lifestyle scene may sit beside a genuine output image; the scene is atmosphere, not proof, and photos are never auto-published from a camera roll. Day runs use a multi-project route; a quick fix is before → change → result; one agent lane is action → output. Provenance and raw metrics stay under Explore this run. Unknown measurements stay unknown. Attaching a run to an external event or community is later and author-chosen only - not a STRIVE club, partnership, or membership import.

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

Brand decision, 16 September: the public product is STRIVE, tagline "Post your strides". Pacecard is rejected. Keep the white cards and blue activity trace. The address remains `agentic-strava.vercel.app`. The name and tagline are held in one place, `server/brand.mjs`; internal identifiers, the package name, the CLI command and the `strava` schema are unchanged.
