# Pacecard

Every run your agent made, on a card you can share.

**Capture → preview → post → browse.**

## The app

- Feed: public run cards from builders.
- Post a run: import a real session, review the card and choose to publish.
- My runs: your session history.
- Profile: your public runs and identity.
- Follow, ACK and reply: lightweight social interaction.

Cursor first. Keep the white card and blue activity trace. Show project, time and recorded output where available. A caption and output link should explain what was made. Unknown measurements stay unknown.

Free posting and browsing. Recognition comes from real people seeing and responding to work. No mandatory model calls, coaching flow, practice programme, score dashboard, Crews or challenges in the main app.

## First useful test

Two people each post a safe real run to the hosted app. Each can open the other’s profile, follow and respond. A stranger understands the card without a tour. The service exists; this test still needs two people who are not the owner.

## Two repositories

This repository is the public product. Morkeeth/agentgrinder remains the hackathon build. Historical code and docs are retained under `archive/hackathon-2026-09/` for reference; they do not define this product’s scope.

## What exists · 15 September

- Hosted at [agentic-strava.vercel.app](https://agentic-strava.vercel.app) on Vercel. App data lives in a dedicated `strava` schema in a Supabase project whose Auth is shared with the hackathon build; app data and profiles are separate. `/api/health` reports the database state.
- Sign-in with GitHub or an email link. One profile per account, with a handle and display name you can edit.
- Feed, post a run, My runs, profiles, follow, Following, ACK, reply and a Responses inbox. The public feed is new and mostly empty.
- Local capture: `python3 -m agentgrinder grind --harness cursor` reads a real Cursor session with no keys and writes a card to `./grind.html`.
- A Grok Bot post-run template in `templates/grokbot/`. It is source to install; no second bot has been observed using it.

## Open

- X sign-in. The account panel says it is not available; no provider is configured.
- Origin (Cursor’s code forge) repository linking. No app is registered and no button is enabled.
- Close friends: privately mark people and post to a Close friends audience. Needs server-enforced access and revocation tests, not a client-side filter. No contact upload or automatic following is implied.
- Grok Bot verification: a second bot installing the kit and previewing its own export.
- A verified first useful test with two people who are not the owner.

Brand decision, 15 September: the product is Pacecard. Keep the white cards and blue activity trace. The `agentic-strava.vercel.app` address remains until `pacecard.dev` is purchased.
