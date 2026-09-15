---
name: post-agent-run
description: Turn an explicitly selected Grok Bot session export into a private Pacecard run-card preview. Use when the owner wants to share a real agent run. Posting requires review of the exact card, account, destination and audience.
---

Run from a checkout of Morkeeth/agentgrinder-public containing the Grok adapter. Select the actual export from this bot's computer; do not assume access to a person's laptop or invent an export. If the export is unavailable, explain what is needed. The bundled sample is for testing only.

Prepare the preview with the bundled helper:

```sh
python3 templates/grokbot/post-agent-run/scripts/preview.py path/to/export.jsonl --base-url https://the-configured-product-domain
```

Use the actual independent product origin configured by the owner. Until it exists, omit `--base-url` for localhost. Do not use the hackathon service. The helper performs no network requests and prints only allowlisted measurements plus a private import URL. It does not publish.

Show the card privately. Ask the owner to write the title, short caption and optional output link. Do not derive these from private prompt text. Grok Bot activity must be labelled; duration, completed commits and file writes stay unknown when the export cannot establish them.

The owner reviews the exact post, signed-in account, destination and audience before publishing. A request to capture or prepare a post is not permission to publish. Open the preview link for the owner to complete that choice, or request explicit approval immediately before a supported UI publishing action. Never bypass denied permissions, switch identities or retry an uncertain write without checking whether it already happened.

After posting, verify the actual run URL and audience. Report prepared, posted and independently visible separately. Do not automatically ACK, reply, follow, invite friends or send messages. Those are separate owner actions.
