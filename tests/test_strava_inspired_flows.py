"""The Strava-inspired pass stays inside STRIVE's response-led core loop."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()
SOCIAL = (ROOT / "site" / "social.js").read_text()
MAP = (ROOT / "docs" / "STRAVA-INSPIRED-FLOWS.md").read_text()


def test_all_twelve_flows_are_mapped_with_lanes_and_boundaries():
    for number in range(1, 13):
        assert f"### {number}." in MAP
    for phrase in (
        "Current:",
        "Strava-inspired improvement:",
        "Backlog / lane:",
        "#27",
        "#28",
        "#23",
        "do not expand segments or",
    ):
        assert phrase in MAP


def test_private_preview_leads_with_story_and_plain_privacy_choices():
    preview = INDEX[INDEX.index("const sample=run.is_sample===true;") : INDEX.index("const editFields=")]
    assert preview.index("STORY FIRST") < preview.index('id="i_caption"')
    assert preview.index('id="i_caption"') < preview.index("Review recorded measurements")
    assert preview.index('id="i_output_url"') < preview.index("Review recorded measurements")
    assert "Only me - just you" in preview
    assert "Link - followers and close friends" in preview
    assert "Public - Feed and profile" in preview
    assert "Unknown measurements stay unknown" not in preview
    assert "It never carries prompts" in preview


def test_run_detail_promotes_audience_aware_next_action():
    detail = INDEX[INDEX.index("async function viewRun(") : INDEX.index("async function trendingRepos(")]
    for phrase in (
        "Saved to Public feed and profile",
        "Copy public link",
        "Open share card",
        "Saved for followers and close friends",
        "Saved for Only me",
        "Open builder profile",
        "Follow lives on the card with XUDOS and Share",
    ):
        assert phrase in detail
    assert "Link audience. This run does not appear on the public profile" in detail
    assert "card-follow" in detail or "Follow lives on the card" in detail
    assert detail.index("+nextAction") < detail.index("grind-thread")
    assert "Grokbot Builders Sunday" not in INDEX
    assert "Send XUDOS" in INDEX
    assert "Oscar and Eric" in SOCIAL


def test_profile_and_response_return_are_people_first():
    profile = INDEX[INDEX.index("async function viewProfile(") : INDEX.index("function showSignIn(")]
    assert profile.index("Identity first, then recent work") < profile.index("Recent public runs")
    assert profile.index("Recent public runs") < profile.index("Profile totals")
    assert "Post a real run and share it with a friend" in SOCIAL
    assert "Open the exact conversation, then come back here" in SOCIAL
    assert "Post your next run" in SOCIAL
    assert "nobody is imported or followed automatically" in SOCIAL
