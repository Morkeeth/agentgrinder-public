"""Primary navigation exposes only the complete social run loop."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()


def test_primary_nav_has_the_product_loop():
    assert 'data-section="feed"' in INDEX
    assert 'data-section="post"' in INDEX
    assert 'data-section="mine"' in INDEX
    assert 'data-section="inbox"' in INDEX
    primary = INDEX.split('id="nav"', 1)[1].split("</nav>", 1)[0]
    before_account = primary.split("<details", 1)[0]
    # Inbox embeds a badge <span>; strip tags for label compare
    top = [
        re.sub(r"<[^>]+>", "", m).strip()
        for m in re.findall(r"<a\s[^>]*>(.*?)</a>", before_account, flags=re.S)
    ]
    assert top == ["Feed", "Post a run", "My runs", "Responses"]
    for label in ("Community", "Following", "Forum", "Crews", "Challenges"):
        assert f">{label}</a>" not in before_account
    assert "Account" in primary


def test_mobile_nav_is_four_or_fewer_destinations():
    mobile = INDEX.split('id="mobile-product-nav"', 1)[1].split("</nav>", 1)[0]
    assert mobile.count("<a ") <= 4
    assert ["Feed", "Post", "My runs", "Responses"] == re.findall(
        r"<a\s[^>]*>([^<]+)", mobile
    )
    assert "Progress" not in mobile and "Practices" not in mobile and "Challenges" not in mobile


def test_posting_defaults_private_and_names_each_audience():
    assert '<option value="" selected disabled>Choose an audience</option>' in INDEX
    assert '<option value="private">Only me - just you</option>' in INDEX
    assert '<option value="close_friends">Close friends - people on your private list</option>' in INDEX
    assert '<option value="public">Public - Feed and profile</option>' in INDEX
    assert "Choosing Public is the deliberate action" in INDEX


def test_account_menu_keyboard_dismiss_wired():
    assert "Escape" in INDEX
    assert "account-menu" in INDEX
