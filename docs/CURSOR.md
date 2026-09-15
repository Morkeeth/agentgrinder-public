# Capture a Cursor run from your own project

Agent Grinder reads Cursor sessions already on your computer. Your project remains the Cursor
workspace; do not clone Agentic Strava as the project you are trying to capture. Capture is local
and keyless. The hosted page receives only allowlisted card metrics in the URL fragment.

## Set up once on this computer

Keep the capture tool outside your own project:

```sh
git clone https://github.com/Morkeeth/agentgrinder-public.git ~/.agentgrinder/agentgrinder-public
python3 -m venv ~/.agentgrinder/venv
~/.agentgrinder/venv/bin/pip install -e ~/.agentgrinder/agentgrinder-public
```

To make the local MCP tools available in one of your projects, run this once for that project:

```sh
cd /path/to/your-own-project
~/.agentgrinder/venv/bin/agentgrinder connect cursor --install
```

The command adds a machine-local `.cursor/mcp.json` and excludes an untracked config from that
repository. It refuses to replace a tracked or conflicting config. Reload Cursor, enable
**agentgrinder** under **Customize**, then ask:

```text
Use the agentgrinder a2a_onboard tool. Summarize the local-only capture and human approval rules. Do not publish anything.
```

MCP setup is optional for the command-line capture below. Neither setup adds credentials.

## Select the session before opening a preview

After working in your own project, stay in that project’s terminal and inspect the candidate:

```sh
cd /path/to/your-own-project
~/.agentgrinder/venv/bin/agentgrinder grind --harness cursor --list --show-paths
```

The receipt names the selected project and source transcript, then lists its sittings. Confirm
that the project is yours and choose the intended `sitting` number. If the newest transcript is
from another workspace, stop and pass the explicitly selected Cursor JSONL path as the first
argument:

```sh
~/.agentgrinder/venv/bin/agentgrinder grind \
  /exact/path/to/selected-cursor-session.jsonl \
  --harness cursor --list
```

Now open that exact sitting as a private preview on the live app:

```sh
AGENTGRINDER_URL=https://agentic-strava.vercel.app \
~/.agentgrinder/venv/bin/agentgrinder grind \
  /exact/path/to/selected-cursor-session.jsonl \
  --harness cursor --pick 2 --push
```

Replace `2` with the sitting you selected. `--push` is a historical flag name: it builds and
opens a metrics-only `#import` URL. It does not upload or save the run. The terminal prints the
selected harness, project, source filename and sitting again before opening the page.

On the hosted page, review the white card and blue trace. Missing measurements remain unknown.
Write only public-facing title, caption and optional HTTPS output link. Leave the audience unset
to stop at preview. Saving requires an intentional choice of **Only me**, **Anyone with the
link**, or **Public feed and profile**, followed by **Save run**.

The equivalent explicit-origin command is:

```sh
~/.agentgrinder/venv/bin/agentgrinder grind \
  /exact/path/to/selected-cursor-session.jsonl \
  --harness cursor --pick 2 --push \
  --push-url https://agentic-strava.vercel.app
```

The server can read only sessions on the computer where it runs. A Cloud Agent or Grok Bot cannot
infer sessions from your laptop.

Reference: [Cursor MCP documentation](https://prod.cursor.com/docs/mcp), checked 14 September 2026.
