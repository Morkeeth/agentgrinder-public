# Agentic Strava: from a live loop to two-person use

Updated 15 September 2026 against `main`, [PRODUCT.md](../PRODUCT.md), the open pull requests and the live health endpoint. Hosting exists; two-person use and Eric's critique are not yet established.

A builder finishes something with an agent, previews a white card with a blue activity trace, adds a caption and output link, posts it deliberately, gets a response from another builder, and returns to the conversation.

## 1. Keep the core loop locked

The product surface is Feed, Post, My runs, Profile, follow/Following, ACK, reply and Responses. Caption and output link come first on the card. Keep missing measurements unknown.

Review and merge [#21](https://github.com/Morkeeth/agentgrinder-public/pull/21) for identity and [#22](https://github.com/Morkeeth/agentgrinder-public/pull/22) for the anonymous first minute when their normal review is complete, then deploy those reviewed commits together. Draft [#13](https://github.com/Morkeeth/agentgrinder-public/pull/13) can be closed if its review findings and fixes are already represented on `main`; confirm that before closing it.

**HOLD [#20](https://github.com/Morkeeth/agentgrinder-public/pull/20).** Its segment leaderboard is a score/comparison dashboard and conflicts with the locked scope. Do not apply its SQL migration, deploy it or use it as the next product slice.

## 2. Finish the live acceptance path

The shared place now exists at [agentic-strava.vercel.app](https://agentic-strava.vercel.app). It is a separate Vercel app using the dedicated Supabase `strava` schema and shared Auth. On 15 September, [`/api/health`](https://agentic-strava.vercel.app/api/health) reported `database: ready`. This proves service and database health, not sign-in completion or real two-person use. Grinder public tables, functions and Auth triggers remain out of bounds.

Remaining release work:

1. Confirm the shared Supabase Auth redirect allowlist includes the exact Agentic Strava return origin without replacing the shared Site URL or existing callbacks.
2. After review, merge and deploy #21 and #22. Verify the deployed commit and confirm GitHub and email-link sign-in return to the intended live page with private draft state preserved. Check cancellation and sign-out too.
3. Run [the two-person test](TWO-PERSON-TEST.md) with Oscar and one consenting friend, each using their own account and safe real session.

Acceptance is both people completing the live post → follow → ACK/reply → Responses return path, with observed friction recorded. A local fixture, health response or owner-only walkthrough does not satisfy it.

## 3. Make real capture lead to deliberate posting

For Cursor, run onboarding from a clean contributor checkout, select a safe real session, and show the private card before any social write. Point hosted imports only at the approved live origin. Preserve unknown measurements and let the builder supply the public caption and output link.

For Grok Bot, explicitly select a real JSONL export on that bot's computer and create a private preview:

```sh
python3 templates/grokbot/post-agent-run/scripts/preview.py \
  path/to/selected-export.jsonl \
  --base-url https://agentic-strava.vercel.app
```

The helper does not publish. The owner must inspect the card, signed-in account, destination and audience, then deliberately choose **Save run**. Record source available, installed, real export previewed and saved as separate states; only source availability is currently established.

## 4. Fix friction before adding surfaces

Use the two-person test to find the largest break in understanding, posting, following, responding or returning. Responses must open the exact run and conversation. Public links must reveal only public content, and withdrawing or deleting a run must remove access.

Do not add coaching, practice programmes, comparisons, score dashboards, Crews or challenges. Do not create artificial engagement, automated ACKs or invented users, output or results.

## 5. Eric's product and launch contribution

Eric has not yet reviewed or used the live product. Do not contact him until the owner approves the recipient, channel and exact message. The live URL now exists, but that alone is not permission to send anything.

When explicitly approved, send Eric the repository, this plan and the live URL. Ask him to try one safe run and critique three things: would he show this card; does a stranger understand it; what would make him return tomorrow?

Invite him to own one bounded slice through a normal PR: first-post friction, card hierarchy or response navigation. [CONTRIBUTING.md](../CONTRIBUTING.md) has the setup and [docs/FIRST-PR.md](FIRST-PR.md) has starting points. Ask which initial builder group he would personally bring in and why; do not present that as an agreed launch commitment.

## 6. Sequence later work and launch

After the core live path works for two people, consider Close friends only with server-enforced membership, visibility and revocation tests. X sign-in needs provider configuration. Origin repository linking needs an app registration and reviewed callback flow.

Public announcement and broad outreach come last, after observed two-person use and fixes to its largest friction. Oscar owns any outward launch. Do not seed synthetic runs or claim adoption from test data.
