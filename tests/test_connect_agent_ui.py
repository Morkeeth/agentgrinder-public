"""Connect reuses deployed grinder_agent token facilities."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONNECT = (ROOT / "site" / "connect.js").read_text()
SOCIAL = (ROOT / "site" / "social.js").read_text()
INDEX = (ROOT / "site" / "index.html").read_text()
ACCOUNT = (ROOT / "site" / "account.js").read_text()


def test_connect_delegates_to_social_agents():
    assert "social.agents" in CONNECT
    assert "connect: true" in CONNECT or "connect:true" in CONNECT.replace(" ", "")
    assert "rpc(\"agent_token_create\"" not in CONNECT
    assert "rpc(\"agent_token_list\"" not in CONNECT


def test_social_still_owns_issue_and_revoke():
    assert 'rpc("grinder_issue_agent_token"' in SOCIAL
    assert "grinder_agent_tokens" in SOCIAL
    assert "AGENTGRINDER_AGENT_TOKEN" in SOCIAL
    assert "async function agents(opts" in SOCIAL


def test_connect_route_and_account_entry():
    assert "q.has('connect')" in INDEX
    assert 'src="/connect.js"' in INDEX
    assert 'href="/?connect"' in INDEX
    assert "Open Connect" in ACCOUNT
