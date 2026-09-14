# Agentic Strava

A minimal, free app to post your agent runs and see other people’s runs.

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

Two people each post a safe real run to the independent service. Each can open the other’s profile, follow and respond. A stranger understands the card without a tour. The current clone still needs its dedicated database schema and hosting before this can be tested publicly.

## Two repositories

This repository is the public product. Morkeeth/agentgrinder remains the hackathon build. Historical code and docs are retained for reference; they do not define this product’s scope.

## Public release requirements · 14 September

- Dedicated `strava` schema in the shared Grinder Supabase project, with separate website hosting under an approved product brand and domain. Auth and infrastructure are shared; app data and profiles are separate.
- GitHub and X sign-in with linked identities belonging to one profile. Origin means Cursor’s code forge. Plan repository connection; ordinary personal sign-in support still needs verification.
- Find and follow friends, browse their runs in Following, open their profiles and continue conversations from Responses. Make these paths useful even with a small personal network.
- A reusable Grok Bot post-run template is required. Source lives in `templates/grokbot/`; second-bot installation and real hosted posting must be verified before calling it released.

Proposed extension for review: privately mark close friends and offer a Close friends posting audience. Ordinary follows already exist; a private audience needs its own server-enforced access and revocation tests, not just a client-side feed filter. No contact upload or automatic social-network following is implied.

Brand direction for review: “See what your friends are building.” Keep the white cards and blue activity trace. Final name/domain and purchase cost need owner approval. No name has been changed or domain purchased.
