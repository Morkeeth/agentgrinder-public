# Cursor setup

The project `.cursor/mcp.json` launches the existing local Python MCP server using a path relative to the workspace. No global config or credentials are installed.

Open the repository in Cursor, enable **agentgrinder** in Customize, then ask:

```text
Use agentgrinder a2a_onboard. Then preview my latest Cursor run with preview_run, harness cursor. Show the metrics and missing fields. Do not publish it.
```

The local MCP protocol and Cursor reader tests can be run separately from an actual Cursor session. The config being present does not prove Cursor has enabled it. The server reads sessions on the machine where it runs. A cloud bot cannot infer sessions on your laptop.

The project template disables inherited agent-write credentials. Publication requires a configured independent service and deliberate audience selection. To develop locally, serve `site` on port 8000. The clone does not provision a database.

Reference: [Cursor MCP documentation](https://prod.cursor.com/docs/mcp), checked 14 September 2026.
