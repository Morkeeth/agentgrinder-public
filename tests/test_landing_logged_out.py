"""The public STRIVE entry shows a real public run first, without invented activity."""
from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] / 'site/index.html').read_text()


def landing():
    return HTML[HTML.index('function landingHTML()'):HTML.index('\nasync function fetchLatestPublicRun()')]


def view_landing():
    return HTML[HTML.index('async function viewLanding()'):HTML.index('\nasync function mountCoachExperiment(')]


def test_logged_out_landing_exposes_browsing_and_first_post():
    body = landing()
    assert "<title>__BRAND__ · __TAGLINE__</title>" in HTML
    assert "Every run your agent made, on a card you can share." in body
    assert 'href="/?explore"' in body
    assert 'Post your first run' in body
    assert 'href="/?onboard"' in body or 'href="/?post"' in body
    assert 'Sign in to browse' not in body


def test_landing_explains_deliberate_publication():
    body = landing()
    assert 'Capture locally' in body and 'Preview privately' in body
    assert 'You choose what goes public' in body


def test_landing_puts_sample_behind_example_link_not_first_fold():
    body = landing()
    assert 'href="/?example"' in body
    assert 'Try a labelled example' in body or 'Labelled example' in body
    assert 'aria-label="Sample run card"' not in body
    assert 'WHAT A RUN LOOKS LIKE' not in body
    assert 'HOME_SAMPLE' not in body
    assert 'data-home-sample="1"' not in body
    assert 'aria-label="A public run"' in body
    assert 'id="landing-feature"' in body
    for retired in ('howItWorks()', 'verified per turn', 'coach verdict', 'DEGRADED'):
        assert retired not in body


def test_landing_loads_latest_public_run_only():
    view = view_landing()
    assert "fetchLatestPublicRun()" in view
    assert "runCard(featured" in view
    fetch = HTML[HTML.index('async function fetchLatestPublicRun()'):HTML.index('async function viewLanding()')]
    assert ".eq('visibility','public')" in fetch
    assert "visibility','link'" not in fetch
    assert "HOME_SAMPLE" not in view
    assert "No public run yet" in view
    assert "Link-only runs stay off this door" in view


def test_landing_reads_the_public_count_without_using_it_as_sample_content():
    view = view_landing()
    assert "fetchPublicRunCount()" in view
    assert "No public runs yet. Yours would be the first." in view
    count = HTML[HTML.index('async function fetchPublicRunCount()'):HTML.index("const $=id=>")]
    assert "count:'exact'" in count and ".eq('visibility','public')" in count


def test_sign_in_explains_github_and_private_runs():
    assert 'id="signin-explanation"' in HTML
    assert "return to this preview or social action" in HTML
    assert "Closing or cancelling sign-in posts nothing" in HTML
    assert "Runs stay private until you choose Public and save them" in HTML
    assert '<button id="auth" class="ghost">Sign in</button>' in HTML
    panel = HTML[HTML.index('id="signin-explanation"') : HTML.index('id="signin-explanation"') + 800]
    assert "Continue with X" not in panel
    assert "Sign in with GitHub" not in panel


def test_capture_command_points_to_the_public_product():
    assert 'git clone https://github.com/Morkeeth/agentgrinder-public' in HTML
    assert 'git clone &lt;repo&gt;' not in HTML
