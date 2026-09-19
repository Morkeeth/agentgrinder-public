"""Connect agent token UI follows the coordinated RPC contract."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONNECT = (ROOT / "site" / "connect.js").read_text()
INDEX = (ROOT / "site" / "index.html").read_text()
ACCOUNT = (ROOT / "site" / "account.js").read_text()
CONTRACT = Path.home() / ".local/state/day-run/2026-09-19/STRIVE-AGENT-TOKEN-CONTRACT.md"


def test_connect_calls_exact_rpc_names():
    assert 'rpc("agent_token_create"' in CONNECT
    assert "p_label" in CONNECT
    assert 'rpc("agent_token_list"' in CONNECT
    assert 'rpc("agent_token_revoke"' in CONNECT
    assert "p_id" in CONNECT


def test_connect_defaults_private_and_shows_token_once():
    assert "Only me" in CONNECT or "private" in CONNECT
    assert "Save this token now" in CONNECT
    assert "shown once" in CONNECT.lower() or "shown only" in CONNECT.lower() or "once" in CONNECT
    assert "/api/agent/runs" in CONNECT
    assert "public" not in CONNECT.lower().split("create private token")[0] or "Private audience only" in CONNECT


def test_connect_route_and_account_entry():
    assert 'q.has(\'connect\')' in INDEX or 'q.has("connect")' in INDEX or "q.has('connect')" in INDEX
    assert 'src="/connect.js"' in INDEX
    assert 'href="/?connect"' in INDEX
    assert "Open Connect" in ACCOUNT


def test_contract_file_matches_ui():
    text = CONTRACT.read_text()
    assert "agent_token_create(p_label text)" in text
    assert "agent_token_list()" in text
    assert "agent_token_revoke(p_id uuid)" in text
    assert '["private"]' in text
