"""The public STRIVE entry leads with the pitch and the drop zone, then a real public run."""
from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] / 'site/index.html').read_text()


def landing():
    return HTML[HTML.index('function landingHTML()'):HTML.index('\nasync function fetchLatestPublicRuns(')]


def view_landing():
    return HTML[HTML.index('async function viewLanding()'):HTML.index('\nasync function mountCoachExperiment(')]


def test_logged_out_landing_exposes_browsing_and_first_post():
    body = landing()
    assert "<title>__BRAND__ · __TAGLINE__</title>" in HTML
    # The joke is the pitch, whole and undisclaimed (Oscar, 25 Sep 2026).
    assert "Strava is for people who ran. <i>__BRAND__</i> is for people who didn't." in body
    assert 'href="/?explore"' in body
    assert 'Post your first run' in body
    assert 'href="/?connect"' in body or 'href="/?post"' in body
    assert 'Sign in to browse' not in body
    # Phone used to pull the feature card above the pitch via order:-1. Keep source order.
    assert '.launch-grid>.landing-feature{order:-1}' not in HTML
    assert body.index('landing-intro') < body.index('landing-feature')


def test_landing_explains_deliberate_publication():
    # The hero is the drop zone since 24 Sep 2026: the file is read in the tab, and the only
    # thing that ever leaves is asked for by name.
    body = landing()
    assert 'Drop a session file' in body and 'id="drop-file"' in body
    assert 'Read on this device. Nothing leaves it until you ask for a link.' in body


def test_landing_names_where_each_harness_keeps_its_session_file():
    body = landing()
    for path in ('~/.claude/projects/', '~/.cursor/projects/', '~/.codex/sessions/'):
        assert path in body
    assert 'Cmd+Shift+G' in body
    assert 'checked on test files only' in body   # Codex: no typed Codex session on the author's Mac
    # The command line stays, below the fold, for power users.
    # The drop zone is one helper since 25 Sep 2026 (shared with Connect); its call site leads.
    assert body.index('${dropZoneHtml()}') < body.index('landing-feature') < body.index('For power users')


def test_landing_points_to_a_real_run_not_the_bundled_sample():
    # 25 Sep 2026: every /?example link became the real public run. A stranger meets a real card.
    body = landing()
    assert "const REAL_RUN='/r/3afa89e7-aff5-488d-bec3-da36196b8c5e';" in HTML
    assert 'href="${REAL_RUN}">A real run</a>' in body
    assert '/?example' not in HTML
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
    # Real run cards above the fold: the newest Public runs, drawn with the feed card.
    assert "fetchLatestPublicRuns(3)" in view
    assert "feedCards(featured" in view
    fetch = HTML[HTML.index('async function fetchLatestPublicRuns('):HTML.index('async function viewLanding()')]
    assert ".eq('visibility','public')" in fetch
    assert "visibility','link'" not in fetch
    assert "HOME_SAMPLE" not in view
    assert "No public run yet" in view
    assert "Link runs stay off this door" in view


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


def test_landing_has_one_action_and_no_numbered_steps():
    body = landing()
    assert body.count('class="act primary"') == 1
    assert 'Explore runs</a>' not in body
    assert '01 ·' not in body and 'launch-steps' not in body
    assert 'if you want the path' not in body
