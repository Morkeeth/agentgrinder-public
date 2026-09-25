"""The public UI stays focused on posting real runs and responding to them."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()
SOCIAL = (ROOT / "site" / "social.js").read_text()
MIGRATION = (ROOT / "supabase" / "migrations" / "2026-09-14-run-post-fields.sql").read_text()


def test_post_page_exposes_priority_harnesses_and_private_preview():
    block = INDEX[INDEX.index("async function viewPost()") : INDEX.index("async function viewExplore()")]
    composer = INDEX[INDEX.index("function postComposerHtml(") : INDEX.index("async function viewPost()")]
    # 25 Sep 2026: the page names four agents and gives each its own command, on one page.
    connect = INDEX[INDEX.index("function connectBodyHtml()") : INDEX.index("function wireConnectCopies(")]
    for name, harness in (("Claude Code", "claude"), ("Cursor", "cursor"), ("Codex", "codex")):
        assert f"agent('{name}','{harness}'" in connect
    assert "ONE_LINE('grokbot')" in connect
    assert "Grok Bot" in connect
    assert "docs/GROK-PUSH.md" in connect
    assert "${connectBodyHtml()}" in block
    assert "Capture from Cursor, Claude Code, Codex or Grok Bot" in composer
    assert "capture → preview → share" in block
    assert "private until you choose" in INDEX


def test_card_shows_builder_project_session_caption_and_output():
    card = INDEX[INDEX.index("function runCard(") : INDEX.index("function wireKudos()")]
    assert "runAttribution(r)" in card
    for field in ("project", "started_at", "caption", "output_url"):
        assert field in card
    assert "Open ${esc(ridgeOutput||'output')}" in card
    assert card.index("${r.caption?") < card.index("${visual}")
    assert card.index("${cover}") < card.index("${visual}")
    assert card.index("run-social-actions") < card.index("${explore}")
    assert "Project touched" in card
    assert "Code activity" in card
    assert "Explore this run" in card
    assert "card-follow" in card
    assert "coverHtml" in card or "${cover}" in card
    assert "card-harness" in card
    assert "run-metrics" in card
    assert "heroStats" in card
    assert "run-rank" not in card
    assert "vptHtml(r)" not in card


def test_social_actions_remain_in_the_focused_app():
    assert ".from(\"grinder_follows\")" in SOCIAL
    assert ".from(\"grinder_replies\")" in SOCIAL
    assert "Cheer this run" in INDEX
    assert "Send XUDOS" in INDEX
    assert "ACK the work" not in INDEX
    assert "Send ACK" not in INDEX
    assert "Responses" in SOCIAL
    assert "/?people" in SOCIAL
    assert "IntersectionObserver" in SOCIAL
    assert "Open exact reply" in SOCIAL
    assert "ag_response_return" in SOCIAL
    assert "Oscar and Eric" in SOCIAL
    assert "Grokbot Builders Sunday" not in SOCIAL
    assert "Grokbot Builders Sunday" not in INDEX
    assert "luma.com" not in INDEX
    assert "eventChip" in INDEX or "${eventChip}" in INDEX
    assert "xudos-tip" in INDEX
    assert "Scene photo URL" in INDEX
    assert "history.replaceState(null,'','/?explore')" in INDEX
    assert "async function viewEvent()" in INDEX
    # Since migration 014 an event is a real page: the club's event, who is going, and Join.
    event = INDEX[INDEX.index("async function viewEvent()") : INDEX.index("const forum=")]
    assert "grinder_events" in event and "grinder_join_event" in event and "This event is not on __BRAND__" in event


def test_caption_and_output_are_bounded_by_database_constraints():
    assert "length(trim(caption)) between 1 and 280" in MIGRATION
    assert "length(output_url) <= 2048" in MIGRATION
    assert "https?" in MIGRATION
