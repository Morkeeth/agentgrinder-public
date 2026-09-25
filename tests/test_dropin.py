"""The drop-in: a session file read in the browser, a card, an unlisted link.

The heavy checks are Node scripts (npm run test:dropin): parity of the browser reader with
ingest.py, the payload and rate limits through the real handler, and migration 011 in PGlite.
These are the fast guards that sit with the Python suite.
"""
import json
import re
import subprocess
from pathlib import Path

from agentgrinder import feedcard

ROOT = Path(__file__).resolve().parents[1]
READER = (ROOT / "site/dropin-parse.js").read_text()
UI = (ROOT / "site/dropin.js").read_text()

ROWS = [
    {"duration_s": 10800, "turns_typed": 5, "tool_calls": 40},                  # marathon
    {"duration_s": 600, "prompts": 1, "tool_calls": 60},                        # one-shot
    {"duration_s": 600, "prompts": 3, "tool_calls": 9, "started_hour": 23},     # night owl
    {"duration_s": 600, "prompts": 3, "tool_calls": 9, "started_hour": 4},      # night owl, early
    {"prompts": 4, "tool_calls": 9, "commits": 5},                              # shipper
    {"prompts": 4, "tool_calls": 9, "files_touched": 25},                       # wide net
    {"prompts": 2, "tool_calls": 61},                                           # delegator, rounds 30.5 up
    {"duration_s": 899, "prompts": 2, "tool_calls": 3, "commits": 1},           # sprint
    {"wall_time_s": 3600, "prompts": 2, "tool_calls": 3},                       # deep focus
    {"prompts": 2, "tool_calls": 3, "started_hour": 6},                         # early bird
    {"prompts": 2, "tool_calls": 3, "started_hour": 12, "duration_s": 60},      # nothing earned
    {"prompts": 1, "tool_calls": 59},                                           # one short of one-shot
    {"started_hour": True, "prompts": 2, "tool_calls": 3},                      # a boolean is not an hour
    {"tool_calls": 0, "ridge": [1] * 50, "ridge_tool_calls": 70, "prompts": 1}, # counts through the ridge
]


def test_the_badge_is_the_same_in_the_browser_and_on_the_local_card():
    js = subprocess.run(["node", "-e", "const F=require(process.argv[1]);process.stdout.write(JSON.stringify(JSON.parse(process.argv[2]).map(F.achievement)))",
                         str(ROOT / "site/feed-card.js"), json.dumps(ROWS)], capture_output=True, text=True, check=True).stdout
    assert json.loads(js) == [feedcard.achievement(r) for r in ROWS]
    keys = [a and a["key"] for a in json.loads(js)]
    assert keys == ["marathon", "one-shot", "night-owl", "night-owl", "shipper", "wide-net", "delegator",
                    "sprint", "deep-focus", "early-bird", None, None, None, "one-shot"]


def test_every_badge_prints_the_number_that_earned_it():
    assert feedcard.achievement(ROWS[1])["detail"] == "1 prompt, 60 tool calls"
    assert feedcard.achievement(ROWS[6])["detail"] == "31 tool calls per prompt"
    assert feedcard.achievement({"duration_s": 11000})["detail"] == "3h 3m in one session"


def test_the_reader_makes_no_request():
    # The page says nothing leaves the device while the file is read. The reader has no way to send.
    for call in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "import(", "navigator."):
        assert call not in READER, call
    # The page's one send is the link request, with the allowlisted payload only.
    assert UI.count("fetch(") == 1 and 'fetch("/api/link"' in UI
    assert "GrinderDropin.uploadPayload(run, titleText())" in UI


def test_the_upload_allowlist_matches_the_database_allowlist():
    js = re.search(r"const UPLOAD_KEYS = \[(.*?)\]", READER).group(1)
    sql = re.search(r"allowed constant text\[\] := array\[(.*?)\];", (ROOT / "supabase/strava/011_dropin_links.sql").read_text(), re.S).group(1)
    words = lambda s: sorted(re.findall(r"'([a-z_]+)'|\"([a-z_]+)\"", s))
    assert sorted(w[0] or w[1] for w in words(js)) == sorted(w[0] or w[1] for w in words(sql))


def test_migration_011_only_creates():
    sql = (ROOT / "supabase/strava/011_dropin_links.sql").read_text()
    body = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\balter\s+table\s+strava\.(?!dropin_)", body, re.I)
    assert not re.search(r"\bdrop\s+(table|policy|function|trigger|column)\b", body, re.I)
    assert not re.search(r"\bcreate\s+(or\s+replace\s+)?policy\b", body, re.I)
    assert not re.search(r"\bgrant\s+[^;]*\bon\s+(table\s+)?strava\.(?!dropin_)", body, re.I)
