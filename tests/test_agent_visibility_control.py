"""Existing Connect agents can become public without flipping sibling runs."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOCIAL = (ROOT / "site" / "social.js").read_text()
CONNECT = (ROOT / "site" / "connect.js").read_text()
INDEX = (ROOT / "site" / "index.html").read_text()
DATABASE = (ROOT / "scripts" / "test-database.mjs").read_text()


def test_agents_list_edits_visibility_after_create():
    assert "data-agent-visibility" in SOCIAL
    assert "Save visibility" in SOCIAL
    assert 'from("grinder_agents")' in SOCIAL
    assert "update({ visibility })" in SOCIAL
    assert "Other Only-me runs stay private" in SOCIAL
    assert SOCIAL.index("agentVisibilityForm") < SOCIAL.index("async function agents(")


def test_run_save_requires_consent_before_making_the_linked_agent_public():
    assert "attachAgentShareGate" in SOCIAL
    assert "run-agent-public-consent" in SOCIAL
    assert "await attachAgentShareGate(runId)" in SOCIAL
    assert "Make this agent public. Do not change other Only-me runs." in SOCIAL
    gate = SOCIAL[SOCIAL.index("async function attachAgentShareGate") : SOCIAL.index("async function thread(")]
    assert 'audience === "public"' in gate or "audienceNeedsPublicAgent" in gate
    assert "saveAgentVisibility" in gate
    assert "run-save" in gate


def test_connect_and_run_copy_never_claims_a_bulk_publish():
    for source in (SOCIAL, CONNECT):
        assert "Other Only-me runs stay private" in source
        assert "bulk" not in source.lower()
    assert "Keep private" in DATABASE
    assert "Want public" in DATABASE
    assert "sibling Only-me runs stay private" in DATABASE


def test_private_run_still_offers_the_audience_control():
    assert 'href="#run-audience">Choose who can see this</a>' in INDEX
    assert "id=\"run-save\"" in INDEX or "id='run-save'" in INDEX
