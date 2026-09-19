"""Returning-friend social flow: follow, Following, Responses return, close-friends clarity."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()
SOCIAL = (ROOT / "site" / "social.js").read_text()


def test_follow_signed_out_uses_github():
    block = SOCIAL.split("async function followControl")[1].split("async function")[0]
    assert 'id="follow-signin"' in block
    assert "Sign in with GitHub" in block
    assert "signInGitHub" in block


def test_auth_return_keeps_inbox_filter_and_profile_query():
    assert "people|account|connect)(=|&|$)" in INDEX
    pat = re.compile(r"^\?(post|mine|following|inbox|run|u|example|people|account|connect)(=|&|$)")
    assert pat.match("?inbox&filter=unread")
    assert pat.match("?u=friend")
    assert not pat.match("?explore")


def test_following_states_public_only_and_points_close_friends_to_profile():
    assert "Close-friends runs stay on their profile, not here" in SOCIAL
    assert "Following only lists Public runs" in SOCIAL
    assert '.eq("visibility", "public")' in SOCIAL


def test_profile_empty_and_heading_respect_viewer():
    assert "Recent runs you can see" in INDEX
    assert "No runs you can see yet" in INDEX
    assert "Close friends runs (if you are on their list)" in INDEX


def test_responses_return_and_ack_paths_remain():
    assert "ag_response_return" in SOCIAL
    assert "Back to Responses" in SOCIAL
    assert "Open exact reply" in SOCIAL
    assert "ACK the work" in INDEX
