# STRIVE: tonight's path to two-person use

Updated 15 September 2026 against `main` at `b39eeee`, the merged core pull requests and the live
health endpoint. **STRIVE** is the working public name for now. The live origin remains
[agentic-strava.vercel.app](https://agentic-strava.vercel.app); a full repository, product-copy and
domain rename is deferred.

The core loop stays capture → private preview → deliberate audience and Save → browse → follow →
ACK/reply → Responses return. Keep the white card, blue trace, caption and output link. Missing
measurements stay unknown.

## Tonight's launch handoff

The core implementation is now on `main`:

- [#27](https://github.com/Morkeeth/agentgrinder-public/pull/27): capture from the builder's own
  project.
- [#28](https://github.com/Morkeeth/agentgrinder-public/pull/28): journey continuity and idempotent
  Save.
- [#30](https://github.com/Morkeeth/agentgrinder-public/pull/30): cross-flow hierarchy, response
  return and empty states.

Merge [#23](https://github.com/Morkeeth/agentgrinder-public/pull/23), deploy the resulting reviewed
`main` tip and record the exact deployment receipt. Then complete these still-open acceptance
steps in order:

1. Confirm the shared Supabase Auth redirect allowlist accepts
   `https://agentic-strava.vercel.app` without replacing the shared Site URL or existing callbacks.
2. Verify GitHub and email-link sign-in return to the intended live page with the private draft
   intact. Check cancellation and sign-out as well.
3. Run [the two-person live test](TWO-PERSON-TEST.md) with Oscar and one consenting friend, each
   using their own account and safe real session.
4. On Grok Bot's own computer, explicitly select a safe real JSONL export and create a private
   hosted preview:

   ```sh
   python3 templates/grokbot/post-agent-run/scripts/preview.py \
     path/to/selected-export.jsonl \
     --base-url https://agentic-strava.vercel.app
   ```

   The helper does not publish. The owner must inspect the card, account, destination and audience,
   then deliberately choose **Save run**.

Hosting already exists, and
[`/api/health`](https://agentic-strava.vercel.app/api/health) reports `database: ready`. That does
not prove Auth return, a hosted Grok Save or two-person use. Keep local, tested, deployed and used
evidence separate.

## Keep the scope locked

The launch surface is Feed, Post, My runs, Profile, follow/Following, ACK, reply and Responses.
Public links must reveal only public content, and withdrawing or deleting a run must remove access.
Use the two-person walk to find the largest friction before adding another surface.

[#20](https://github.com/Morkeeth/agentgrinder-public/pull/20) was merged despite the earlier hold.
Do not expand, promote or treat its leaderboard/segment work as part of tonight's launch acceptance.
Do not apply further leaderboard SQL or build a score/comparison dashboard.

Defer all of the following until after the core path is accepted:

- [#26](https://github.com/Morkeeth/agentgrinder-public/pull/26), including OG work and Close
  friends;
- [#29](https://github.com/Morkeeth/agentgrinder-public/pull/29), including the private Cursor hook
  and ridge;
- Close friends migrations, server-enforced access and revocation work;
- the full STRIVE rename, new domain work and broad public announcement.

Do not add coaching, practice programmes, comparisons, Crews or challenges. Do not create
artificial engagement, automated ACKs or invented users, output or results. Grinder public tables,
functions and Auth triggers remain out of bounds.

## Eric's product and launch contribution

Eric has not yet reviewed or used the live product. Do not contact him until the owner approves the
recipient, channel and exact message. The live URL is not permission to send anything.

When explicitly approved, send Eric the repository, this plan and the live URL. Ask him to try one
safe run and critique three things: would he show this card; does a stranger understand it; what
would make him return tomorrow?

Invite him to own one bounded slice through a normal PR: first-post friction, card hierarchy or
response navigation. [CONTRIBUTING.md](../CONTRIBUTING.md) has the setup and
[docs/FIRST-PR.md](FIRST-PR.md) has starting points. Do not present his participation or launch
commitment as established before he agrees.
