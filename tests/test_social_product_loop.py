"""The public UI stays focused on posting real runs and responding to them."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()
SOCIAL = (ROOT / "site" / "social.js").read_text()
MIGRATION = (ROOT / "supabase" / "migrations" / "2026-09-14-run-post-fields.sql").read_text()


def test_post_page_exposes_priority_harnesses_and_private_preview():
    block = INDEX[INDEX.index("async function viewPost()") : INDEX.index("async function viewExplore()")]
    composer = INDEX[INDEX.index("function postComposerHtml(") : INDEX.index("function firstRunPrompt()")]
    assert "Capture from Cursor" in INDEX
    assert "python3 -m agentgrinder grind --harness cursor --push" in INDEX
    assert "Grok Bot" in composer
    assert "docs/GROK-PUSH.md" in composer
    assert "capture → preview → choose audience" in block
    assert "private until you choose" in INDEX


def test_card_shows_builder_project_session_caption_and_output():
    card = INDEX[INDEX.index("function runCard(") : INDEX.index("function wireKudos()")]
    assert "runAttribution(r)" in card
    for field in ("project", "started_at", "duration_s", "caption", "output_url"):
        assert field in card
    assert "Open what was built" in card
    assert card.index("${r.caption?") < card.index('<div class="sub">${r.project?')
    assert card.index("${output?") < card.index('<div class="sub">${r.project?')
    assert "card-harness" in card
    assert "Counts show activity, not quality; unknown means not measured." in card
    assert "vptHtml(r)" not in card


def test_social_actions_remain_in_the_focused_app():
    assert ".from(\"grinder_follows\")" in SOCIAL
    assert ".from(\"grinder_replies\")" in SOCIAL
    assert "ACK the work" in INDEX
    assert "Responses" in SOCIAL
    assert "/?people" in SOCIAL
    assert "IntersectionObserver" in SOCIAL
    assert "Open exact reply" in SOCIAL
    assert "ag_response_return" in SOCIAL


def test_caption_and_output_are_bounded_by_database_constraints():
    assert "length(trim(caption)) between 1 and 280" in MIGRATION
    assert "length(output_url) <= 2048" in MIGRATION
    assert "https?" in MIGRATION
