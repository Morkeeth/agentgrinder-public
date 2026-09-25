"""Primary navigation exposes only the complete social run loop."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()


def test_primary_nav_has_the_product_loop():
    """Three places and a drawer: Feed, Post, You, and More for everything else."""
    assert 'data-section="feed"' in INDEX
    assert 'data-section="post"' in INDEX
    assert 'data-section="mine"' in INDEX
    assert 'data-section="inbox"' in INDEX
    primary = INDEX.split('id="nav"', 1)[1].split("</nav>", 1)[0]
    before_menus = primary.split("<details", 1)[0]
    top = [
        re.sub(r"<[^>]+>", "", m).strip()
        for m in re.findall(r"<a\s[^>]*>(.*?)</a>", before_menus, flags=re.S)
    ]
    assert top == ["Feed", "Add a run"]
    summaries = [re.sub(r"<[^>]+>", "", m).strip() for m in re.findall(r"<summary[^>]*>(.*?)</summary>", primary, flags=re.S)]
    assert summaries == ["You", "More"]
    for label in ("Community", "Following", "Forum", "Crews", "Challenges"):
        assert f">{label}</a>" not in before_menus
    more = INDEX[INDEX.index("const MORE_LINKS="):]
    more = more[: more.index("\n")]
    for label in ("Find people", "Following", "A real run", "Privacy"):
        assert label in more
    # 25 Sep 2026: the programme pages left the menu. Their addresses land on the feed.
    for label in ("Community", "Forum", "Crews", "Challenges", "Practices"):
        assert label not in more
    retired = INDEX[INDEX.index("const RETIRED="):]
    retired = retired[: retired.index("\n")]
    for key in ("community", "forum", "challenges", "practices", "experiments", "rigs", "progress", "claim", "pitch"):
        assert f"'{key}'" in retired


def test_mobile_nav_is_four_or_fewer_destinations():
    """Phone: one bottom tab bar. Feed and Post are links; You and More open one sheet."""
    mobile = INDEX.split('id="mobile-product-nav"', 1)[1].split("</nav>", 1)[0]
    labels = [re.sub(r"<[^>]+>", "", m).strip() for m in re.findall(r"<(?:a|button)\s[^>]*>(.*?)</(?:a|button)>", mobile, flags=re.S)]
    assert labels == ["Feed", "Post", "You", "More"]
    assert 'data-sheet="you"' in mobile and 'data-sheet="more"' in mobile
    assert "Progress" not in mobile and "Practices" not in mobile and "Challenges" not in mobile


def test_account_links_are_reachable_on_a_phone():
    """The You sheet carries what the desktop account menu carries; it used to be display:none on phones."""
    you = INDEX[INDEX.index("function menuLinks(kind)"):INDEX.index("function syncAuthNav()")]
    for href in ("/?mine", "/?inbox", "/?connect", "/?account"):
        assert href in you
    # 25 Sep 2026: "Get started" pointed at the retired wizard; the signed-out sheet leads to Connect.
    assert 'href="/?connect" role="menuitem">Connect your agent</a>' in you
    assert "data-signin" in you


def test_posting_defaults_private_and_names_each_audience():
    assert '<option value="" selected disabled>Choose an audience</option>' in INDEX
    assert '<option value="private">Only me - just you</option>' in INDEX
    assert '<option value="close_friends">Close friends - people on your private list</option>' in INDEX
    assert '<option value="public">Public - Feed and profile</option>' in INDEX
    assert "Choosing Public is the deliberate action" in INDEX


def test_account_menu_keyboard_dismiss_wired():
    assert "Escape" in INDEX
    assert "account-menu" in INDEX
