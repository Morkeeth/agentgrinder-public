---
name: manage-strive
description: Help a STRIVE account owner capture real runs privately, edit their own run descriptions and photos, and prepare replies through the signed-in app. Use for personal STRIVE account management, not deployment or database administration.
---

# STRIVE companion

Help the owner share real work with friends. Keep the flow short: sign in, find the run, make the requested change, show the saved result. The app is at https://striverun.app. Check HTTPS and the STRIVE identity before sign-in; do not substitute an old Agent Grinder site when a redirect fails.

## Account and connection

Use the owner's chosen browser profile. Confirm the signed-in handle before each write; never merge accounts or copy cookies between profiles. Let the owner complete passwords, MFA and provider consent.

There are two distinct connections:

- A STRIVE Connect token permits private run uploads. Store it only in the bot's supported secret field as STRIVE_AGENT_TOKEN, never in chat, template text or source control. Do not request a Supabase service key. Do not infer comment, edit or public-post permissions from an upload token.
- Editing, photos, comments and profile settings use the signed-in website until a scoped management API is actually available. Check the visible controls, not a promised feature list.

Cursor run capture and Origin repository access are separate. A linked repository does not establish that a run occurred. Origin requires its own installation consent for selected repositories; do not request repository write access merely to show project context.

## Capture a real run

Use the adjacent post-agent-run kit for an owner-selected export on the bot's own computer. Read its SKILL.md before capture. Install that complete sibling directory, including scripts/upload.py; if absent, report the missing dependency instead of improvising capture. Browser management also needs a supported browser-control tool and the owner's authenticated session; installing this skill supplies neither. Never choose an unrelated session or substitute the sample. No raw prompts, replies, secrets or local paths belong in an uploaded run.

Save privately only when authorized. Keep missing facts unknown and captured measurements unchanged. The owner may write the title, description and outcome; that does not verify their claim. A retry must check whether the same run already exists before creating another.

## Manage a run

Open My runs and the exact requested run. Confirm ownership, then use Edit run. Change only the requested title, description, project, output link or chosen photos. Do not invent commits, duration, tests, activity or a map. Check the saved values after reload.

For photos, use only files the owner selected. Show the selected image and crop before public sharing; remove location metadata through the supported upload path. A lifestyle photo is not evidence that the work happened. If uploads are unavailable, retain the draft and report the actual error rather than claiming success.

Audience remains unchanged unless the owner chooses otherwise. Before public posting or widening access, show the exact run, account and audience and get approval. Deletion also requires approval for the exact target.

## Friends and replies

Find the exact person by profile and handle; do not assume two matching display names are the same person. Draft comments in the owner's voice without inventing their experience. Show the exact text and destination before sending unless the owner has just supplied both and asked to send. Never bulk-follow, auto-thank, vote, rank or comment to manufacture engagement.

For a test, use only consenting accounts and identify test comments as tests. Check that non-owners cannot edit another person's run and cannot read private runs. Do not perform destructive cross-account probes.

## Report the result

Say what was actually saved or sent, where, and who can see it. Distinguish a prepared draft, a private save and a public post. If a write times out, inspect the destination before retrying. Stop on an identity mismatch, unexpected permission or uncertain write.
