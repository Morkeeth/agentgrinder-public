---
name: post-agent-run
description: Turn an explicitly selected Grok Bot session export into a private Pacecard run-card preview. Use when the owner wants to share a real agent run. Posting requires review of the exact card, account, destination and audience.
---

Run the capture helper from a separate checkout of Morkeeth/agentgrinder-public; the owner’s
project remains the working project being captured. Select the actual export from this bot's
computer; do not assume access to a person's laptop, choose “newest” without owner review, or
invent an export. If the export is unavailable, explain what is needed. The bundled sample is for
testing only and remains labelled SAMPLE / bot activity.

Prepare the preview with the bundled helper:

```sh
python3 templates/grokbot/post-agent-run/scripts/preview.py \
  /exact/path/to/selected-grokbot-export.jsonl \
  --base-url https://agentic-strava.vercel.app
```

Confirm the `selected_export` receipt before opening the returned hosted `#import` URL. The helper
performs no network requests and prints only the selected file receipt, allowlisted measurements
and a private import URL. It does not publish or save. Localhost is for kit development; do not
use the separate hackathon service.

Show the card privately. Ask the owner to write the title, short caption and optional output link. Do not derive these from private prompt text. Grok Bot activity must be labelled; duration, completed commits and file writes stay unknown when the export cannot establish them.

The owner reviews the exact post, signed-in account, destination and audience before saving. A
request to capture or prepare a post is not permission to publish. Open the preview link for the
owner to complete that choice. Never select an audience or press **Save run** automatically,
bypass denied permissions, switch identities or retry an uncertain write without checking whether
it already happened.

After posting, verify the actual run URL and audience. Report prepared, posted and independently visible separately. Do not automatically ACK, reply, follow, invite friends or send messages. Those are separate owner actions.
