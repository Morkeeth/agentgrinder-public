"""Zero-run, Connect, My runs and deliberate-share contracts for the first-user journey."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()
PROGRESS = (ROOT / "site" / "progress.js").read_text()
CONNECT = (ROOT / "site" / "connect.js").read_text()
SOCIAL = (ROOT / "site" / "social.js").read_text()
HOSTED = (ROOT / "docs" / "HOSTED-CUTOVER.md").read_text()
GROK = (ROOT / "docs" / "GROK-PUSH.md").read_text()
DRY_RUN = (ROOT / "scripts" / "check-hosted-config.mjs").read_text()


def test_fresh_signed_in_builder_lands_on_first_post_not_a_tour():
    route = INDEX[INDEX.index("async function route(){") :]
    assert "if(ME&&(await runCount())===0) return viewPost();" in route
    onboard = INDEX[INDEX.index("async function shouldOnboard(){") : INDEX.index("function stepBar(")]
    assert "runCount()" not in onboard
    assert "Start with a private preview" in INDEX or "Your first post defaults to Only me." in INDEX
    assert "python3 -m agentgrinder grind --harness cursor --push" in INDEX
    assert "Using Grok Bot?" in INDEX


def test_zero_run_surfaces_connect_and_deliberate_save():
    assert "Your first post defaults to Only me." in INDEX
    assert "Review the title, caption and audience" in INDEX
    assert "Your first run starts private" in PROGRESS
    assert 'href="/?connect">Connect an agent</a>' in PROGRESS
    assert "Private uploads appear here" in PROGRESS
    assert "Share explicitly for public Latest runs" in PROGRESS
    assert "Grok Bot push guide" in PROGRESS


def test_my_runs_hides_unknown_and_signs_in_with_github():
    assert "Unknown" not in PROGRESS
    assert "Sign in with GitHub" in PROGRESS
    assert "signInGitHub" in PROGRESS
    assert "signInGitHub:()=>signInWithGitHub()" in INDEX
    assert "countBits" in PROGRESS


def test_connect_primary_still_points_at_mine():
    assert 'href="/?mine">See my runs</a>' in CONNECT
    assert "Private uploads appear in" in CONNECT


def test_private_run_offers_deliberate_audience_cta():
    assert 'href="#run-audience">Choose who can see this</a>' in INDEX
    assert "Private uploads stay in My runs until you deliberately choose Link or Public below." in INDEX


def test_responses_signed_out_uses_github():
    assert "Sign in with GitHub" in SOCIAL
    assert "signInGitHub" in SOCIAL
    assert "signInGitHub:()=>signInWithGitHub()" in INDEX


def test_manual_post_names_its_duplicate_limit():
    composer = INDEX[INDEX.index("function postComposerHtml(") : INDEX.index("async function viewPost()")]
    assert "Manual posts have no capture identifier." in composer
    assert "browser gives each save an identifier" in composer
    assert "Check and try again" in composer
    assert "never invents a measurement revision" in composer


def test_landing_featured_card_keeps_caption_and_output_primary():
    card = INDEX[INDEX.index("function featuredCard(") : INDEX.index("function howItWorks()")]
    assert "r.caption" in card
    assert "Open what was built" in card
    assert 'class="primary-output"' in card


def test_cutover_docs_and_dry_run_cover_schema_boundary():
    for value in (
        "AGENTGRINDER_URL",
        "AGENTGRINDER_SUPABASE_URL",
        "AGENTGRINDER_SUPABASE_ANON_KEY",
        "SB_URL",
        "SB_KEY",
        "SB_SCHEMA",
        'storageKey:"agentic-strava-auth"',
        "Auth Redirect URLs",
    ):
        assert value in HOSTED
    assert "localhost can preview" in GROK.lower()
    assert "hosted Pacecard URL" in GROK
    assert "Accept-Profile" in DRY_RUN and "Content-Profile" in DRY_RUN
    assert "No network request or production write was made." in DRY_RUN
