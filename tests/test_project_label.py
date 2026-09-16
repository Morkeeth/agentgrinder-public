"""The author's username was hardcoded in a public reader.

`ingest.py` ended the Cursor project label with `.replace("Users-morkeeth-", "")`. Measured
3 Sep 2026: a stranger's project rendered on the card as `Users-alice-code-myapp`, while the same
fixture under a `Users-morkeeth-CODE-demo` directory rendered as the clean `CODE-demo`. One
person's labels were tidy and everybody else's were not.
"""
import os

from agentgrinder.ingest import parse_cursor_session, project_label
from agentgrinder.push import export_run

CURSOR_LINES = ('{"role":"user","message":{"content":"<user_query>build it</user_query>"}}\n'
                '{"role":"assistant","message":{"content":[{"type":"tool_use"}]}}\n')


def test_any_users_home_prefix_is_stripped_not_one_persons():
    assert project_label("Users-alice-code-myapp") == "code-myapp"
    assert project_label("Users-morkeeth-CODE-demo") == "CODE-demo"
    assert project_label("-Users-bob-work-thing") == "work-thing"
    assert project_label("home-carol-src-thing") == "src-thing"       # Linux


def test_no_username_is_hardcoded_anywhere_in_the_reader():
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "agentgrinder", "ingest.py"), encoding="utf-8").read()
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
    assert "morkeeth" not in code.lower()


def test_a_name_with_no_home_prefix_is_left_alone():
    assert project_label("agentgrinder") == "agentgrinder"
    assert project_label("Users-alice") == "Users-alice"   # too short to be a home prefix


def test_cursor_workspace_label_is_not_published_without_git_evidence(tmp_path):
    d = tmp_path / "Users-alice-code-myapp" / "agent-transcripts" / "aaaa"
    d.mkdir(parents=True)
    p = d / "t.jsonl"
    p.write_text(CURSOR_LINES, encoding="utf-8")
    run = parse_cursor_session(str(p))
    assert run["project"] == "code-myapp"
    assert run["project_proven"] is False
    assert "project" not in export_run(run)
