"""Close friends privacy, post audience, and profile management contracts."""
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()
SOCIAL = (ROOT / "site" / "social.js").read_text()
MIGRATION = (ROOT / "supabase" / "strava" / "002_close_friends.sql").read_text()


def test_close_friends_rls_with_disposable_postgres():
    subprocess.run(
        ["node", str(ROOT / "scripts" / "test-close-friends.mjs")],
        cwd=ROOT,
        check=True,
    )


def test_post_forms_offer_three_private_first_audiences():
    for select_id in ("f_vis", "i_vis"):
        choices = INDEX[
            INDEX.index(f'<select id="{select_id}"')
            : INDEX.index("</select>", INDEX.index(f'<select id="{select_id}"'))
        ]
        assert choices.count("<option") == 5
        assert 'value="" selected disabled' in choices
        assert 'value="private"' in choices
        assert 'value="close_friends"' in choices
        assert 'value="public"' in choices
        assert 'value="link"' in choices
    assert "Your first post defaults to Only me." in INDEX


def test_profile_manages_an_owner_only_list_by_handle():
    assert "strava.close_friends" in MIGRATION
    assert "enable row level security" in MIGRATION.lower()
    assert "owner_profile_id = strava.grinder_profile_id()" in MIGRATION
    assert "as restrictive" in MIGRATION
    assert "visibility = 'close_friends'" in MIGRATION
    assert '.from("close_friends")' in SOCIAL
    assert 'db.rpc("strava_profile_by_handle"' in SOCIAL
    assert "People are not notified" in SOCIAL
    assert "social.closeFriends" in INDEX


def test_empty_close_friends_save_is_blocked_in_each_client_path():
    message = "Add at least one close friend before saving for Close friends."
    assert message in INDEX
    assert INDEX.count("await requireCloseFriendsForSave(audience)") == 3
    assert ".from('close_friends').select('*',{count:'exact',head:true})" in INDEX
    assert message in MIGRATION


def test_close_friends_detail_does_not_claim_link_access():
    detail = INDEX[
        INDEX.index("async function viewRun(") : INDEX.index(
            "async function trendingRepos("
        )
    ]
    assert "Saved for Close friends" in detail
    assert "Only people on your Close friends list can open this run." in detail
