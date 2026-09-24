# Preview and deliberately save one Grok Bot run

Capture work from the project Grok Bot is already building on its computer. Do not treat the
Agentic Strava repository as the user’s project. Localhost is only for kit development; normal
capture opens a private import preview on the hosted app.

Localhost can preview a card when developing the kit, but it cannot save social data.
The hosted STRIVE URL for this flow is `https://agentic-strava.vercel.app`.

1. Install the complete `templates/grokbot/post-agent-run/` skill directory using [`templates/grokbot/INSTALL.md`](../templates/grokbot/INSTALL.md). Keep `SKILL.md` beside `scripts/preview.py`.
2. On the bot’s computer, explicitly select the real JSONL export to share. Do not guess a path,
   use the newest file without review, or use an export from someone else’s machine.
3. Build a private hosted preview URL:

   ```sh
   python3 templates/grokbot/post-agent-run/scripts/preview.py \
     /exact/path/to/selected-grokbot-export.jsonl \
     --base-url https://agentic-strava.vercel.app
   ```

   Confirm that `selected_export` in the output is the intended file. The helper selects the
   latest sitting inside that file and reports that choice.
   For kit development only, omit `--base-url`, start `python3 scripts/dev.py serve`, and use
   localhost as a local-only preview.
4. Open the generated hosted `#import` URL. Inspect every imported field, including fields shown
   as unknown. The helper makes no network request and no post.
5. Write the title, caption and optional HTTPS link to what was built.
6. Deliberately choose **Only me**, **Followers and close friends** or **Public feed and profile**, then press **Save run**.

Nothing is posted by installing the skill, selecting an export, running `preview.py` or opening
the preview. Samples stay labelled **SAMPLE** / **bot activity** and cannot be saved. Do not put
credentials in the skill or auto-post, choose an audience, follow or ACK.
