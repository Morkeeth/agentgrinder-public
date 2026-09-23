"""A HOME DIRECTORY IS NOT A PROJECT NAME, IN ANY OF THE THREE READERS.

`_HOME_PREFIX` wanted a trailing dash, so it stripped `Users-alice-code-myapp` down to
`code-myapp` and left the bare `Users-morkeeth` — a session opened on the home directory itself —
exactly as it was. The browser contract and the server share card had no home rule at all, so on
production 7858535 that slug reached the public 1200x630 image as "Project touched": the one
surface a stranger meets before anything else.

The rule now lives in three places because three readers need it. A rule in three places drifts,
so one table of cases runs through all three and the answers are compared here.
"""
from pathlib import Path
import json
import subprocess

from agentgrinder.ingest import project_label

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "fixtures" / "project_label_probe.mjs"

# workspace name -> what a reader may see. None means "no project", never an account name.
CASES = {
    "Users-morkeeth": None,
    "-Users-morkeeth": None,
    "Users-alice-code-myapp": "code-myapp",
    "-Users-bob-work-thing": "work-thing",
    "home-carol-src-thing": "src-thing",
    "-home-dave-proj": "proj",
    "agentgrinder-public": "agentgrinder-public",
    "the-fair": "the-fair",
    "session": None,
}
ACCOUNTS = ("morkeeth", "alice", "bob", "carol", "dave")


def _javascript() -> dict:
    out = subprocess.check_output(["node", str(PROBE)], cwd=str(ROOT), text=True)
    return json.loads(out)


def test_the_python_reader_drops_a_bare_home_slug():
    for value, expected in CASES.items():
        got = project_label(value)
        if value == "session":
            assert got == "session"      # the Python reader has no "no project" vocabulary
            continue
        assert got == (expected or ""), value


def test_the_browser_contract_and_the_share_card_agree_with_it():
    results = _javascript()
    for value, expected in CASES.items():
        contract = results[value]["contract"]
        server = results[value]["server"]
        assert contract == expected, (value, contract)
        # The server card additionally strips a CODE- worktree prefix and a date stamp, so it is
        # compared on the property that matters rather than on the exact string.
        assert (server or "") == (expected or ""), (value, server)


def test_no_account_name_survives_any_of_the_three():
    results = _javascript()
    for value in CASES:
        for account in ACCOUNTS:
            assert account not in (project_label(value) or ""), (value, account)
            assert account not in (results[value]["contract"] or ""), (value, account)
            assert account not in (results[value]["server"] or ""), (value, account)


def test_the_share_card_still_reads_a_worktree_name_the_way_it_did():
    """The home rule must not eat the existing cleanup: this case shipped and still holds."""
    results = subprocess.check_output(
        ["node", "--input-type=module", "-e",
         "import {projectNameForTest as p} from './server/public-run.mjs';"
         "process.stdout.write(p({project:'CODE-worktrees-strava-night-review-20260915'}))"],
        cwd=str(ROOT), text=True)
    assert results == "strava night review"
