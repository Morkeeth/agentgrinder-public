"""Round 2 integration contracts: the shell carries the hooks itself and the walk drives it as is."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()
SOCIAL = (ROOT / "site" / "social.js").read_text()
WALK = (ROOT / "scripts" / "check-round2-integration.py").read_text()
ACCOUNT_WALK = (ROOT / "scripts" / "check-account-loop.py").read_text()


def test_unread_badge_is_refreshed_by_the_shell_on_cold_load_and_route():
    refresh_auth = INDEX[INDEX.index("async function refreshAuth(){"):INDEX.index("const IMPORT_STASH=")]
    assert "social.refreshUnread()" in refresh_auth
    route = INDEX[INDEX.index("async function route(){"):INDEX.index("document.addEventListener('DOMContentLoaded'")]
    assert "social.refreshUnread()" in route


def test_zero_unread_badge_is_not_drawn():
    """The base .nav-badge rule would otherwise outrank the hidden attribute and show a blue dot."""
    assert ".nav-badge[hidden]{display:none}" in INDEX


def test_missing_or_private_run_keeps_the_responses_return_path():
    view_run = INDEX[INDEX.index("async function viewRun(id){"):INDEX.index("function showSignIn(){")]
    assert "This run is private or does not exist." in view_run
    assert "responseReturnLink()" in view_run
    assert "function responseReturnLink()" in INDEX and "ag_response_return" in INDEX


def test_phone_path_to_account_settings_exists():
    """Under 900px the header menu is hidden; the profile's Edit profile panel must link there."""
    assert '<div id="linked-accounts"><p class="meta">' in INDEX
    assert 'href="/?account">Account settings</a>' in INDEX


def test_follow_row_offers_the_profile_once():
    assert 'n.kind !== "follow" && !runGone && !replyGone && actor.href' in SOCIAL


def test_walks_do_not_insert_production_hooks():
    for script in (WALK, ACCOUNT_WALK):
        assert "HOOKS" not in script and "HOOK_" not in script
        assert script.count("body.replace(") == 1, "only the backend host is rewritten"
        assert "const SB_URL=" in script


def test_walk_covers_the_assigned_integrated_path():
    for needle in (
        "capture_hash()", "Preview your run", "cancelled sign-in", "duplicate handle", "Follow", "Post reply",
        "cold load", "Open exact reply", "Back to Responses", "missing run", "deleted reply", "delete cancel",
        "Block", "deleted profile", "grinder-snapshot", "hosted_oauth", "consenting_users",
    ):
        assert needle in WALK, needle
