"""Migration 010 ships with the bootstrap and enforces Link relationship gating in SQL."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "strava" / "010_link_relationship.sql").read_text()
PRIVACY = (ROOT / "site" / "privacy.html").read_text()
PROGRESS = (ROOT / "site" / "progress.js").read_text()


def test_link_relationship_migration_enforces_follow_or_close_friends():
    assert "grinder_is_close_friend_of" in MIGRATION
    assert "grinder_follows_author" in MIGRATION
    assert "grinder_link_relationship" in MIGRATION
    assert "grinder_link_not_enumerable" in MIGRATION
    assert "grinder_link_access(id)" in MIGRATION
    assert "grinder_link_relationship(profile_id)" in MIGRATION
    assert "grant execute on function strava.grinder_link_relationship(uuid) to anon, authenticated" in MIGRATION
    assert "Anyone with a link" not in MIGRATION


def test_prepare_strava_bootstrap_includes_010():
    out = subprocess.check_output(
        ["python3", str(ROOT / "scripts" / "prepare-strava-database.py")],
        text=True,
    )
    assert "-- strava/010_link_relationship.sql" in out
    assert "grinder_link_relationship" in out
    assert "create policy grinder_link_not_enumerable" in out


def test_privacy_and_progress_match_relationship_gate():
    assert "relationship-gated" in PRIVACY
    assert "Anyone with a link to a link-only run" not in PRIVACY
    assert "Followers and close friends" in PROGRESS
    assert "Anyone with the link" not in PROGRESS
