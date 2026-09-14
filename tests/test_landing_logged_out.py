"""The public Strava entry shows the social product without invented activity or sign-in."""
from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] / 'site/index.html').read_text()


def landing():
    return HTML[HTML.index('function landingHTML(r)'):HTML.index('\nasync function viewLanding()')]


def test_logged_out_landing_exposes_browsing_and_first_post():
    body = landing()
    assert 'href="/?explore"' in body
    assert 'Post your first run' in body
    assert 'href="/?onboard"' in body or 'href="/?post"' in body
    assert 'Sign in to browse' not in body


def test_landing_explains_deliberate_publication():
    body = landing()
    assert 'Capture locally' in body and 'Preview privately' in body
    assert 'You choose what goes public' in body


def test_landing_does_not_promote_coaching_or_a_bundled_run_as_the_product():
    body = landing()
    assert '/?example' not in body
    for retired in ('howItWorks()', 'verified per turn', 'coach verdict', 'DEGRADED'):
        assert retired not in body


def test_landing_never_falls_back_to_inherited_grinder_activity():
    view = HTML[HTML.index('async function viewLanding()'):HTML.index('async function viewRun(')]
    assert 'FEATURED_SNAPSHOT' not in view, 'a historical Grinder row is not activity on Strava'


def test_capture_command_points_to_the_public_product():
    assert 'git clone https://github.com/Morkeeth/agentgrinder-public' in HTML
    assert 'git clone &lt;repo&gt;' not in HTML
