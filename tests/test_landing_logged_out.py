"""The public Strava entry shows the social product without invented activity or sign-in."""
from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] / 'site/index.html').read_text()


def landing():
    return HTML[HTML.index('function landingHTML()'):HTML.index('\nasync function viewLanding()')]


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


def test_landing_labels_the_neutral_sample_without_promoting_coaching():
    body = landing()
    assert '/?example' not in body
    assert 'aria-label="Sample run card"' in body
    assert '<span class="sample-label">SAMPLE</span>' in body
    assert 'data-home-sample="1"' in HTML
    for retired in ('howItWorks()', 'verified per turn', 'coach verdict', 'DEGRADED'):
        assert retired not in body


def test_landing_reads_the_public_count_without_using_it_as_sample_content():
    view = HTML[HTML.index('async function viewLanding()'):HTML.index('async function viewRun(')]
    assert "fetchPublicRunCount()" in view
    assert "No public runs yet. Yours would be the first." in view
    count = HTML[HTML.index('async function fetchPublicRunCount()'):HTML.index("const $=id=>")]
    assert "count:'exact'" in count and ".eq('visibility','public')" in count


def test_sign_in_explains_github_and_private_runs():
    assert 'id="signin-explanation"' in HTML
    assert "runs stay private until you choose Public and post them" in HTML
    assert "Continue with X" not in HTML


def test_capture_command_points_to_the_public_product():
    assert 'git clone https://github.com/Morkeeth/agentgrinder-public' in HTML
    assert 'git clone &lt;repo&gt;' not in HTML
