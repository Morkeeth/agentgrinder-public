"""Connect uses thin 007 agent_token_* wrappers; Agents stays separate."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONNECT = (ROOT / "site" / "connect.js").read_text()
SOCIAL = (ROOT / "site" / "social.js").read_text()
INDEX = (ROOT / "site" / "index.html").read_text()
ACCOUNT = (ROOT / "site" / "account.js").read_text()


def test_connect_calls_thin_wrappers_exactly():
    assert 'rpc("agent_token_create"' in CONNECT
    assert "p_label" in CONNECT
    assert 'rpc("agent_token_list"' in CONNECT
    assert 'rpc("agent_token_revoke"' in CONNECT
    assert "p_id" in CONNECT
    assert "Array.isArray(data)" in CONNECT
    assert "social.agents" not in CONNECT
    assert "grinder_issue_agent_token" not in CONNECT
    assert "Sign in with GitHub" in CONNECT
    assert "signInGitHub" in CONNECT
    assert "/?agents" in CONNECT


def test_advanced_agents_remain_separate():
    assert 'rpc("grinder_issue_agent_token"' in SOCIAL
    assert "async function agents(" in SOCIAL
    assert "connect-banner" not in SOCIAL
    assert "Open Connect" in ACCOUNT
    assert 'href="/?agents"' in ACCOUNT


def test_connect_route_and_account_entry():
    assert "q.has('connect')" in INDEX
    assert 'src="/connect.js"' in INDEX
    assert 'href="/?connect"' in INDEX
    assert "db:sb" in INDEX
    assert "signInGitHub:()=>signInWithGitHub()" in INDEX
