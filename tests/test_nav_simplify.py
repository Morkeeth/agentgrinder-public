"""Primary navigation exposes only the complete social run loop."""
import re
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()


def test_primary_nav_has_the_product_loop():
    """One rail: the feed, own runs, and profile. Posting is contextual."""
    assert 'data-section="feed"' in INDEX
    rail = INDEX[INDEX.index("function railHtml(active,runs)"):INDEX.index("function setPrimarySection")]
    for label in ("Feed", "My runs", "Discover"):
        assert f"'{label}'" in rail
    assert "Projects" not in rail and 'class="rail-post"' not in rail
    assert "More" not in rail and "Responses" not in rail and "Privacy" not in rail
    retired = INDEX[INDEX.index("const RETIRED="):]
    retired = retired[: retired.index("\n")]
    for key in ("community", "forum", "challenges", "practices", "experiments", "rigs", "progress", "claim", "pitch"):
        assert f"'{key}'" in retired


def test_mobile_nav_is_four_or_fewer_destinations():
    """Phone matches the desktop destinations; posting stays in the top action."""
    mobile = INDEX.split('id="mobile-product-nav"', 1)[1].split("</nav>", 1)[0]
    labels = [re.sub(r"<[^>]+>", "", m).strip() for m in re.findall(r"<(?:a|button)\s[^>]*>(.*?)</(?:a|button)>", mobile, flags=re.S)]
    assert labels == ["Feed", "My runs", "Discover"]
    assert "data-sheet" not in mobile
    assert "Progress" not in mobile and "Practices" not in mobile and "Challenges" not in mobile


def test_account_links_are_reachable_from_the_avatar():
    """The avatar menu owns identity and settings, never product destinations or responses."""
    you = INDEX[INDEX.index("function menuLinks(kind)"):INDEX.index("function syncAuthNav()")]
    for href in ("/?u=", "/?account"):
        assert href in you
    assert "/?mine" not in you and "/?inbox" not in you
    signed_in = you[you.rindex("return `") :]
    assert ">Profile</a>" in signed_in and ">Settings</a>" in signed_in
    assert ">Connections</a>" not in signed_in
    assert "data-signin" in you


def test_signed_out_feed_keeps_the_desktop_and_phone_navigation():
    """Run the actual rail helper with no profile; Feed never collapses to a landing-only shell."""
    start = INDEX.index("function railHtml(active,runs)")
    helper = INDEX[start : INDEX.index("function setPrimarySection", start)]
    script = f"""
      const ME=null;
      const esc=(value)=>String(value);
      {helper}
      const rail=railHtml('feed');
      process.stdout.write(JSON.stringify({{rail}}));
    """
    observed = json.loads(subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True).stdout)
    assert observed["rail"].count("<a ") == 3
    assert ">Feed<" in observed["rail"] and ">My runs<" in observed["rail"] and ">Discover<" in observed["rail"]
    view = INDEX[INDEX.index("async function viewLanding()") : INDEX.index("async function mountCoachExperiment(")]
    assert "frame(railHtml('feed'),null,true)" in view
    mobile = INDEX.split('id="mobile-product-nav"', 1)[1].split("</nav>", 1)[0]
    assert "data-auth" not in mobile and " hidden" not in mobile


def test_posting_defaults_private_and_names_each_audience():
    preview = INDEX[INDEX.index("async function importRun(){"):INDEX.index("async function viewShareRun(")]
    assert '<option value="private" selected>Only me</option>' in preview
    assert '<option value="close_friends">Close friends</option>' in preview
    assert '<option value="public">Public feed and profile</option>' in preview
    assert "stays private unless you choose another audience and save" in preview


def test_account_menu_keyboard_dismiss_wired():
    assert "Escape" in INDEX
    assert "account-menu" in INDEX


def test_responses_are_a_notification_drawer_not_navigation():
    assert 'id="notifications-drawer"' in INDEX
    assert 'id="notifications-toggle"' in INDEX
    assert "social.notificationsPanel" in INDEX
    assert "social.markAllNotificationsRead" in INDEX
    mobile = INDEX.split('id="mobile-product-nav"', 1)[1].split("</nav>", 1)[0]
    assert "Responses" not in mobile
    assert '.notice-drawer[aria-hidden="true"]{display:none}' in INDEX
    assert 'id="notifications-drawer" class="notice-drawer" aria-label="Notifications" aria-hidden="true" inert' in INDEX
