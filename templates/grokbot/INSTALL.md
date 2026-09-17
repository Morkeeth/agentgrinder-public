# STRIVE Grok Bot publish kit

Status: source kit only. Installing or running the labelled sample does not prove that a second
bot used a real export or that an owner saved a post.

## Install only the kit

The `post-agent-run` directory is a complete, standard-library-only install unit:

```text
post-agent-run/
├── SKILL.md
├── samples/sample_grokbot_bot_activity.jsonl
└── scripts/
    ├── preview.py
    └── smoke_test.py
```

No `agentgrinder-public` parent checkout is required at runtime. To copy only this directory into
a bot workflow, replace `DEST` with that workflow's skill directory and run this one command:

```sh
DEST="$HOME/bot-workflow/post-agent-run"; TMP="$(mktemp -d)"; \
git clone --depth 1 --filter=blob:none --sparse https://github.com/Morkeeth/agentgrinder-public.git "$TMP" && \
git -C "$TMP" sparse-checkout set templates/grokbot/post-agent-run && \
mkdir -p "$DEST" && cp -R "$TMP/templates/grokbot/post-agent-run/." "$DEST/" && \
rm -rf "$TMP"
```

Install `post-agent-run/SKILL.md` through the current Grok Bot skill interface and keep the
directory intact. This kit has no verified marketplace manifest.

The reusable skill must not contain credentials, transcripts or account-specific paths. The
owner selects the exact export, public-facing text, signed-in account, destination and audience.

## Verify the isolated install

Run the bundled smoke check from any working directory:

```sh
python3 /absolute/path/to/post-agent-run/scripts/smoke_test.py
```

It runs the bundled labelled sample, decodes the hosted import, and asserts that no duration or
ridge was fabricated. The expected result starts with `PASS`. The sample cannot be saved as a
real run.

## Preview one selected real export

The default preview destination is STRIVE at `https://agentic-strava.vercel.app`:

```sh
python3 /absolute/path/to/post-agent-run/scripts/preview.py \
  /exact/path/to/selected-grokbot-export.jsonl
```

1. Confirm `selected_export` is the file the owner selected.
2. Check the allowlisted counts against the export. Duration, files touched, completed commits
   and ridge remain unknown when the export does not establish them.
3. Open the returned hosted `#import` URL.
4. Review the white card and blue trace, account, destination and all unknown fields.
5. Stop before **Save run**. The owner writes the title and caption, chooses the audience, and
   decides whether to save.

The helper makes no network request and performs no social write. It never exports prompt text,
tool inputs, tool results or paths.

## Avoid a truncated import hash

Long `#import` hashes can be truncated by bot or chat output. Write the complete URL directly to a
handoff file:

```sh
python3 /absolute/path/to/post-agent-run/scripts/preview.py \
  /exact/path/to/selected-grokbot-export.jsonl \
  --handoff /tmp/strive-preview-url.txt
```

Pass `/tmp/strive-preview-url.txt` directly to the browser workflow instead of copying a printed
hash. For adapters that carry a ridge but omit `worker_bins`, wait for
[worker bin default PR #42](https://github.com/Morkeeth/agentgrinder-public/pull/42) before relying
on that import. This Grok kit does not invent a ridge or worker bins.

For local kit development only, pass `--base-url http://localhost:8000` to a separately running
STRIVE development server. Never use the hackathon service or repository.

Report milestones separately:

- **Installed:** a second bot can invoke this copied skill and helper.
- **Used:** that bot previewed an explicitly selected real export.
- **Published:** the owner deliberately saved an approved post to the approved account and
  audience.

Do not infer one milestone from another. Do not automatically save, ACK, reply, follow, invite or
send messages.
