"""The Responses inbox marks only viewed items and opens exact conversations."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOCIAL = (ROOT / "site" / "social.js").read_text()
SOCIAL_CSS = (ROOT / "site" / "social.css").read_text()
PEOPLE = (ROOT / "site" / "people.js").read_text()


def test_inbox_does_not_bulk_mark_all_unread_on_load():
    inbox = SOCIAL[SOCIAL.index("async function inbox()") : SOCIAL.index("async function shareControl(")]
    assert "IntersectionObserver" in inbox
    assert 'data-read="0"' in inbox
    assert ".is(\"read_at\", null)" in SOCIAL or '.is("read_at", null)' in SOCIAL
    # Must not mark every unread row immediately after rendering the list.
    assert "rows.filter((r) => !r.read_at).map((r) => r.id)" not in inbox
    assert "Open exact reply" in inbox
    assert "filter=unread" in inbox
    assert "This run was deleted or is no longer available." in inbox
    assert "That reply was removed" in inbox


def test_exact_reply_navigation_and_return_context():
    assert "#reply-" in SOCIAL
    assert "reply=${encodeURIComponent(n.source_id)}" in SOCIAL or "reply=" in SOCIAL
    assert "ag_response_return" in SOCIAL
    assert "Back to Responses" in SOCIAL
    assert "reply-target" in SOCIAL
    assert "refreshUnread" in SOCIAL
    assert "Back to Responses" in PEOPLE


def test_response_inbox_phone_styles_use_blue_unread_trace():
    assert ".response-item.unread" in SOCIAL_CSS
    assert "border-left:3px solid var(--blue)" in SOCIAL_CSS
    assert ".response-filters" in SOCIAL_CSS
    assert "min-height:44px" in SOCIAL_CSS
