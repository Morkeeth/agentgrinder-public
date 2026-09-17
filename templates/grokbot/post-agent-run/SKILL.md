---
name: post-agent-run
description: Turn an explicitly selected Grok Bot export into a private STRIVE card preview. Use when the owner wants to share a real agent run. Stop before Save run so the owner reviews the card, account, destination and audience.
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
sitting boundary only. They do not timestamp tool events, so duration and ridge stay NULL. File
writes and completed commits also stay unknown when the export cannot establish them. Never
invent missing metrics.

Long `#import` hashes can be truncated in bot or chat output. In that case, create an exact browser
handoff without printing the URL:

```sh
python3 /absolute/path/to/post-agent-run/scripts/preview.py \
  /exact/path/to/selected-grokbot-export.jsonl \
  --handoff /tmp/strive-preview-url.txt
```

Pass that file directly to the browser workflow. Do not reconstruct a truncated hash. Adapters
that provide a ridge without `worker_bins` should wait for
[worker bin default PR #42](https://github.com/Morkeeth/agentgrinder-public/pull/42). This Grok
adapter must keep ridge NULL rather than adding placeholders.

Show the card privately. Ask the owner to write the title, short caption and optional output link.
Do not derive them from private prompt text. Stop before **Save run**. A request to capture,
prepare or open a preview is not permission to save or publish.

The owner must review the exact card, signed-in account, destination and audience, then make the
save decision. Never choose an audience, press **Save run**, bypass denied permissions, switch
identities or retry an uncertain write without checking whether it happened.

After an owner saves, verify the actual run URL and audience. Report prepared, saved and
independently visible separately. Do not automatically ACK, reply, follow, invite or send
messages.
