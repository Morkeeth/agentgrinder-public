"""The public UI stays focused on posting real runs and responding to them."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()
SOCIAL = (ROOT / "site" / "social.js").read_text()
MIGRATION = (ROOT / "supabase" / "migrations" / "2026-09-14-run-post-fields.sql").read_text()


def test_post_page_exposes_cursor_capture_and_private_preview():
    block = INDEX[INDEX.index("async function viewPost()") : INDEX.index("async function viewExplore()")]
    assert "Capture from Cursor" in INDEX
    assert "python3 -m agentgrinder grind --push" in INDEX
    assert "capture → preview → choose audience" in block
    assert "private until you choose" in INDEX


def test_card_shows_builder_project_session_caption_and_output():
    card = INDEX[INDEX.index("function runAttribution(") : INDEX.index("function wireKudos()")]
    for field in ("profiles", "project", "started_at", "duration_s", "caption", "output_url"):
        assert field in card
    assert "Open what was built" in card
    assert "Counts describe recorded activity, not quality." in card
    assert "vptHtml(r)" not in card


def test_social_actions_remain_in_the_focused_app():
    assert ".from(\"grinder_follows\")" in SOCIAL
    assert ".from(\"grinder_replies\")" in SOCIAL
    assert "ACK the work" in INDEX
    assert "Responses" in SOCIAL


def test_caption_and_output_are_bounded_by_database_constraints():
    assert "length(trim(caption)) between 1 and 280" in MIGRATION
    assert "length(output_url) <= 2048" in MIGRATION
    assert "https?" in MIGRATION
