---
name: post-agent-run
description: Turn an explicitly selected Grok Bot export into a private STRIVE card preview, or save it as a private run with the owner's Connect token. Use when the owner wants to share a real agent run. Stop before Save run so the owner reviews the card, account, destination and audience.
---

This directory is the complete STRIVE Grok Bot kit. It needs Python 3 and no parent repository,
package install or third-party dependency.

Select the actual JSONL export on this bot's computer. Do not assume access to a person's laptop,
guess a private path, choose the newest file without owner review, or invent an export. If no
export is available, explain what the owner must provide. The bundled sample is testing data only.

First verify this isolated install:

```sh
python3 /absolute/path/to/post-agent-run/scripts/smoke_test.py
```

Then prepare a real private preview. STRIVE at `https://agentic-strava.vercel.app` is the default:

```sh
python3 /absolute/path/to/post-agent-run/scripts/preview.py \
  /exact/path/to/selected-grokbot-export.jsonl
```

Confirm the `selected_export` receipt before opening the returned hosted `#import` URL. The helper
performs no network request and prints only the selected-file receipt, allowlisted measurements
and private import URL. It does not publish or save.

Grok Bot activity stays labelled `bot activity`. Typed-turn timestamps establish the start and
sitting boundary only. They do not timestamp tool events, so duration stays NULL. The ridge is
drawn in turn order: 50 bins, tool calls placed by the typed turn they followed, with
`ridge_basis: "turn-order"`. It makes no wall-time claim. File writes and completed commits stay
unknown when the export cannot establish them. Never invent missing metrics.

Long `#import` hashes can be truncated in bot or chat output. In that case, create an exact browser
handoff without printing the URL:

```sh
python3 /absolute/path/to/post-agent-run/scripts/preview.py \
  /exact/path/to/selected-grokbot-export.jsonl \
  --handoff /tmp/strive-preview-url.txt
```

Pass that file directly to the browser workflow. Do not reconstruct a truncated hash. This
adapter always sends `worker_bins` with its ridge (all zero, because the export shows one bot).

## Automatic private upload

If the owner created a token with **Connect** on STRIVE and set it as `STRIVE_AGENT_TOKEN`, the
bot can save the run directly as a private run:

```sh
python3 /absolute/path/to/post-agent-run/scripts/upload.py \
  /exact/path/to/selected-grokbot-export.jsonl --dry-run
python3 /absolute/path/to/post-agent-run/scripts/upload.py \
  /exact/path/to/selected-grokbot-export.jsonl
```

Run `--dry-run` first and check the payload: metrics only, no prompt or reply text. The token can
only save private runs, so this never publishes. The helper refuses the bundled sample. Running it
again for the same export returns the run already saved (`"status": "already saved"`), never a
duplicate. Report the `visibility` the server returned. Never print or store the token.

Show the card privately. Ask the owner to write the title, short caption and optional output link.
Do not derive them from private prompt text. Stop before **Save run**. A request to capture,
prepare or open a preview is not permission to save or publish.

The owner must review the exact card, signed-in account, destination and audience, then make the
save decision. Never choose an audience, press **Save run**, bypass denied permissions, switch
identities or retry an uncertain write without checking whether it happened.

After an owner saves, verify the actual run URL and audience. Report prepared, saved and
independently visible separately. Do not automatically ACK, reply, follow, invite or send
messages.
