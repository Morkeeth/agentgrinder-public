# Grok Bot template kit

Status: source kit only. It is not evidence that the skill has been installed on a second bot,
used on a real export, or published as a template. Those three states must be observed and
reported separately.

## Install on a bot computer

Keep this capture-tool checkout separate from the owner’s project. On the bot’s shared cloud
computer, clone or update this public repository once. The skill source to install is the complete
directory:

```text
templates/grokbot/post-agent-run/
├── SKILL.md
└── scripts/preview.py
```

Use `templates/grokbot/post-agent-run/SKILL.md` as the install path in the current Grok Bot
skill interface, and keep the directory intact so its relative `scripts/preview.py` helper remains
available. Do not claim a one-click import or marketplace install: this kit has no verified
marketplace manifest.

The bot's job is to help its owner preview real bot work. It must not schedule posts, engage
automatically, or carry credentials, transcripts or account-specific paths in the reusable skill.
The owner selects the exact export, public-facing text, signed-in account, destination and
audience.

## Verify sample first

From the repository root on the bot's computer, run:

```sh
python3 templates/grokbot/post-agent-run/scripts/preview.py \
  samples/sample_grokbot_bot_activity.jsonl
```

Before opening the localhost URL, start the site from the repository root in another terminal:

```sh
python3 scripts/dev.py serve
```

The sample card is visibly labelled **Sample preview** and cannot be saved or posted.
Capture a real export to enable saving; a sample run is not your activity.

Expected status is `private preview; not posted`, with `Grok Bot`, `bot activity`, 2 typed turns
and 3 tool calls. The URL must start with `http://localhost:8000/#import=`. The helper performs no
network request and does not publish. This fixture is synthetic, labelled sample bot activity;
running it proves only that the source kit works locally.

## Then preview one selected real export on the hosted app

1. Explicitly select a JSONL export already present on this bot's cloud computer. A bot cannot
   read a person's laptop, discovery must not guess private paths, and “newest file” is not a
   substitute for the owner’s selection.
2. Run the helper with that exact selected file and hosted origin:

   ```sh
   python3 templates/grokbot/post-agent-run/scripts/preview.py \
     /exact/path/to/selected-grokbot-export.jsonl \
     --base-url https://agentic-strava.vercel.app
   ```

3. Confirm `selected_export` in the output, then compare the allowlisted counts with the export.
   Keep duration, file writes, successful commits and other unsupported metrics unknown.
4. Open the returned hosted `#import` URL. It is a private preview, not a saved run or post.
5. The owner reviews the exact white card and blue trace, signed-in account and destination,
   deliberately chooses an audience and presses **Save run**. The helper never chooses or saves.

For local kit development only, omit `--base-url`, start `python3 scripts/dev.py serve`, and open
the localhost preview. Never use the hackathon service.

Report the milestones literally:

- **Installed:** the second bot can invoke this copied skill and helper.
- **Used:** that bot successfully previewed an explicitly selected real export.
- **Published:** the owner deliberately saved an approved post to an approved hosted account and
  audience.

Do not infer one milestone from another. The source kit and labelled sample currently establish
none of these second-bot milestones.

Before sharing the template, inspect the actual exported package for account tokens, conversation history, files and personal configuration. Publish the template only after the owner approves that exact package and destination.
