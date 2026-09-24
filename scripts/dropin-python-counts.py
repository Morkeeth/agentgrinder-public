"""Print the counts the Python readers give for session files, as JSON. Used only by
scripts/test-dropin-parity.mjs, which compares them with the browser reader site/dropin-parse.js.
Usage: dropin-python-counts.py <harness> <path> [<harness> <path> ...]"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agentgrinder import ingest  # noqa: E402

KEYS = ("turns_typed", "tool_calls", "files_touched", "commits", "duration_s", "rhythm")


def counts(harness, path):
    try:
        if harness == "Claude Code":
            run = ingest.parse_session(path)
        elif harness == "Cursor":
            run = ingest.parse_cursor_session(path, cursor_db="/nonexistent/state.vscdb")
        elif harness == "Codex":
            run = ingest.parse_codex_session(path)
        else:
            raise SystemExit("unknown harness " + harness)
    except ValueError as error:
        return {"error": str(error)[:80]}
    out = {k: run.get(k) for k in KEYS}
    out["started"] = datetime.fromisoformat(run["started"]).timestamp() if run.get("started") else None
    # A Cursor wall time read from the local chat store is not in the file, so the browser cannot
    # have it. Say which source answered so the test compares like with like.
    out["duration_source"] = run.get("ridge_source", "file")
    return out


args = sys.argv[1:]
print(json.dumps([counts(args[i], args[i + 1]) for i in range(0, len(args), 2)]))
