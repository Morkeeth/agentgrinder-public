"""Print what the real capture path would upload for one transcript. No network.

Driven by scripts/test-connect-device.mjs, which then uploads this payload with a paired device
token and searches every table in the strava schema for the canary string and the fake home path
that the transcript is full of. Keeping one helper means the privacy test measures the shipped
code path - capture.read_run then agent_api.run_payload - and not a hand-written payload that
happens to be clean.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agentgrinder.agent_api import run_payload
from agentgrinder.capture import read_run

if __name__ == "__main__":
    transcript = sys.argv[1]
    harness = sys.argv[2] if len(sys.argv) > 2 else "codex"
    print(json.dumps(run_payload(read_run(harness, transcript))))
