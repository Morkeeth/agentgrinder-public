"""Friends / people lane contracts — presentation, empty states, no invented ownership."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PEOPLE = (ROOT / "site" / "people.js").read_text()
SOCIAL = (ROOT / "site" / "social.js").read_text()
CSS = (ROOT / "site" / "people.css").read_text()
MIGRATION = (ROOT / "supabase" / "migrations" / "2026-09-14-people.sql").read_text()
ORDER = (ROOT / "scripts" / "migration-order.txt").read_text()


def test_presentation_adapter_exposes_future_and_legacy_fields():
    assert "display_name" in PEOPLE
    assert "avatar_url" in PEOPLE
    assert "github_handle" in PEOPLE
    assert "profile.handle" in PEOPLE or "profile.handle ===" in PEOPLE
    assert "GrinderPeople.present" in PEOPLE
    assert "never invents ownership" in PEOPLE.lower() or "does not create" in PEOPLE


def test_people_module_owns_lookup_and_shareable_profile():
    assert "grinder_find_people" in PEOPLE
    assert "grinder_recent_builders" in PEOPLE
    assert "Find people" in PEOPLE
    assert "Copy profile link" in PEOPLE
    assert "window.GrinderPeople" in PEOPLE
    assert "async function discover" in PEOPLE
    assert "async function profile" in PEOPLE
    exported = PEOPLE.rsplit("return {", 1)[1]
    assert "discover" in exported and "profile" in exported and "present" in exported


def test_following_empty_states_point_to_people():
    assert "/?people" in SOCIAL
    assert "Follow works before they post" in SOCIAL
    assert "You are not following anyone yet" in SOCIAL
    assert "none have public runs yet" in SOCIAL


def test_follow_control_blocks_self_and_supports_signed_out():
    assert "This is you" in SOCIAL
    assert "Sign in to follow" in SOCIAL
    assert "aria-pressed" in SOCIAL


def test_response_return_links_cover_profile_run_thread():
    assert "Open profile" in SOCIAL
    assert "#grind-thread" in SOCIAL
    assert "Open Following" in SOCIAL


def test_sql_is_strava_namespaced_via_order_and_search_only():
    assert "2026-09-14-people.sql" in ORDER
    assert "grinder_find_people" in MIGRATION
    assert "grinder_recent_builders" in MIGRATION
    assert "grinder_blocked_pair" in MIGRATION
    assert "create table" not in MIGRATION.lower() or "create table if not exists public.profiles" not in MIGRATION
    # Identity columns belong to Claude's lane — comment may name them; SQL must not add them.
    assert "add column" not in MIGRATION.lower()
    assert "alter table" not in MIGRATION.lower()
    assert MIGRATION.count("display_name") <= 1  # comment only
    assert "avatar_url" in MIGRATION  # named in comment
    assert "github_handle" in MIGRATION and "p.github_handle" in MIGRATION
    assert "p.display_name" not in MIGRATION
    assert "p.avatar_url" not in MIGRATION


def test_people_css_keeps_white_cards_and_touch_targets():
    assert "var(--box)" in CSS
    assert "min-height:44px" in CSS
    assert "@media(max-width:600px)" in CSS
