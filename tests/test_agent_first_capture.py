"""The primary capture journey starts in the agent chat; file import is recovery only."""
from pathlib import Path


INDEX = (Path(__file__).resolve().parents[1] / "site" / "index.html").read_text()


def block(start: str, end: str) -> str:
    return INDEX[INDEX.index(start):INDEX.index(end)]


def test_add_run_leads_with_share_this_run_and_all_supported_agents():
    capture = block("const AGENT_SHARE_PROMPTS=", "function postExampleFallback()")
    post = block("async function viewPost(){", "async function viewExplore(){")
    assert "Share this run to __BRAND__" in capture
    for agent in ("Claude Code", "Cursor", "Codex", "Grok Bot"):
        assert agent in capture
    assert "private preview" in capture.lower()
    assert "private card + story" in post.lower()


def test_file_drop_is_a_named_recovery_path_not_the_front_door():
    capture = block("function askAgentHtml(){", "function postExampleFallback()")
    connect = block("function connectBodyHtml(){", "function wireConnectCopies(")
    assert "Recovery: import a session file" in capture
    assert capture.index("Share this run to __BRAND__") < capture.index("Recovery: import a session file")
    assert "Recovery: import a session file" in connect
    assert connect.index("connect-agents") < connect.index("${dropZoneHtml()}")


def test_public_metadata_no_longer_promotes_file_drop():
    head = INDEX[:INDEX.index("</head>")]
    assert "Drop a Cursor" not in head
    assert "Drop a session file" not in head


def test_free_lunch_referral_enters_agent_capture_not_the_feed():
    route = block("async function route(){", "document.addEventListener('DOMContentLoaded'")
    post = block("async function viewPost(){", "async function viewExplore(){")
    assert "q.get('via')==='the-fair'" in route
    assert "return viewPost()" in route
    assert "Free Lunch sent you here." in post
    assert "tell the agent in the active build chat" in post.lower()


def test_private_editor_makes_the_story_and_one_proof_visual_explicit():
    imported = block("async function importRun(){", "async function viewShareRun(")
    assert "What did you achieve?" in imported
    assert "What made it difficult?" in imported
    assert "Final proof visual" in imported
    assert "visual_choice" in imported
