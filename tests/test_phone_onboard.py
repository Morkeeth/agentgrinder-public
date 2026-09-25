"""The Connect page tells a phone the truth: the session file is on the computer the agent ran on.

Until 25 Sep 2026 this lived in a four-step onboarding wizard at /?onboard. That wizard is gone;
/?onboard, /?connect and the top of /?post are one page. The phone honesty moved with it.
"""
from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] / 'site/index.html').read_text()


def connect_body():
    return HTML[HTML.index('function connectBodyHtml()'):HTML.index('function wireConnectCopies(')]


def test_phone_handoff_says_capture_needs_the_computer():
    body = connect_body()
    assert 'data-phone-handoff="1"' in body
    assert "Capture runs on the computer where your agent runs" in body
    assert "This phone cannot record a sitting" in body
    assert ".ob-phone-handoff{display:none}" in HTML
    assert "@media(max-width:800px)" in HTML
    assert ".ob-phone-handoff{display:block}" in HTML


def test_one_page_one_command_per_agent_and_the_drop_zone():
    body = connect_body()
    assert "${dropZoneHtml()}" in body
    for name, harness in (("Claude Code", "claude"), ("Cursor", "cursor"), ("Codex", "codex")):
        assert f"agent('{name}','{harness}'" in body
    assert "ONE_LINE('grokbot')" in body
    assert "uvx --from git+https://github.com/Morkeeth/agentgrinder-public agentgrinder grind" in HTML
    for path in ("~/.claude/projects/", "~/.cursor/projects/", "~/.codex/sessions/"):
        assert path in HTML
    # No account for the card or the link; sign-in only to post. No email, no mailto.
    assert "No account for the card or the link" in body
    assert "mailto:" not in body and "signInWithOtp" not in body
    # Bots and unsupported agents have a path too, and the token flow keeps its address.
    assert 'href="/?connect=auto"' in body
    assert "docs/AGENT-UPLOAD-API.md" in body and "docs/GROK-PUSH.md" in body


def test_onboard_and_connect_and_post_are_the_same_page():
    assert "async function viewOnboard(){ return viewConnect(); }" in HTML
    assert "if(q.get('connect')==='auto')" in HTML
    post = HTML[HTML.index("async function viewPost(){"):HTML.index("async function viewExplore(){")]
    assert "${connectBodyHtml()}" in post
    assert "firstRunPrompt" not in HTML and "FIRST_RUN_CMD" not in HTML
