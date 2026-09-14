# Cursor setup

The project `.cursor/mcp.json` launches the local Agent Grinder MCP server from this
checkout. It installs no global configuration, needs no account for capture and contains no
publishing credential.

## Capture and inspect locally

1. Open this repository as the workspace in Cursor.
2. Open **Customize**, find the workspace MCP server named **agentgrinder**, and enable it.
   If it does not start, confirm that `python3` is available, then open **Output → MCP Logs**.
   The presence of `.cursor/mcp.json` alone does not mean the server is enabled.
3. In Cursor chat, make the discovery call:

```text
Use the agentgrinder a2a_onboard tool. Summarize the local-only capture and human approval rules. Do not publish anything.
```

4. After doing some work in this workspace, ask for the metrics-only harness preview:

```text
Use the agentgrinder preview_run tool with harness set to cursor. Show the measured metrics and fields that remain unknown. Do not export, propose, or publish the run.
```

`preview_run` reads the latest eligible Cursor sitting on this machine and returns an allowlisted
metrics preview. It sends nothing and excludes prompts, code and file paths. The server can read
only sessions on the machine where it runs; a Cloud Agent or Grok Bot cannot infer sessions from
your laptop.

## Open the private card preview

Start the local site in one terminal:

```sh
python3 scripts/dev.py serve
```

Then, in another terminal in this repository, build and open the import preview:

```sh
python3 -m agentgrinder grind --harness cursor --push --push-url http://localhost:8000
```

Despite the historical `--push` flag name, this command makes a metrics-only URL fragment and
opens it on localhost. It does not upload to a hosted service or save a run. The page says **not
posted** and keeps the card private until you sign in, write public-facing text, choose an
audience and press **Save run**. Leave the audience unset to stop at preview. Choose **Only me**
for a deliberately saved private run; **Anyone with the link** and **Public feed and profile**
are broader audiences and must be selected deliberately.

The clone does not provision a database, so saving and social actions are unavailable in a
local-only checkout. A configured hosted product origin and sign-in are separate prerequisites;
do not substitute the hackathon service. The workspace MCP config also disables inherited
agent-write credentials.

The MCP protocol and reader tests can be exercised without a personal session:

```sh
python3 scripts/dev.py check
```

Reference: [Cursor MCP documentation](https://prod.cursor.com/docs/mcp), checked 14 September 2026.
