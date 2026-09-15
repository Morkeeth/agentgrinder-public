"""Zero-run, manual-post and hosted-cutover contracts for the first-user journey."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()
PROGRESS = (ROOT / "site" / "progress.js").read_text()
HOSTED = (ROOT / "docs" / "HOSTED-CUTOVER.md").read_text()
GROK = (ROOT / "docs" / "GROK-PUSH.md").read_text()
DRY_RUN = (ROOT / "scripts" / "check-hosted-config.mjs").read_text()


def test_fresh_signed_in_builder_lands_on_first_post_not_a_tour():
    route = INDEX[INDEX.index("async function route(){") :]
    assert "if(ME&&(await runCount())===0) return viewPost();" in route
    onboard = INDEX[INDEX.index("async function shouldOnboard(){") : INDEX.index("function stepBar(")]
    assert "runCount()" not in onboard
    assert "Start with a private preview" in INDEX
    assert "python3 -m agentgrinder grind --harness cursor --push" in INDEX
    assert "Using Grok Bot?" in INDEX


def test_zero_run_surfaces_explain_deliberate_save():
    assert "Nothing is posted until you write the title and caption" in INDEX
    assert "Only me, Link or Public" in INDEX
    assert "Your first run starts with a private preview" in PROGRESS
    assert "Grok Bot push guide" in PROGRESS


def test_manual_post_names_its_duplicate_limit():
    composer = INDEX[INDEX.index("function postComposerHtml()") : INDEX.index("async function viewPost()")]
    assert "Manual posts have no capture identifier." in composer
    assert "check <a href=\"/?mine\">My runs</a> before pressing it again" in composer
    assert "cannot reliably detect a duplicate" in composer
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
    assert "hosted Agentic Strava URL" in GROK
    assert "Accept-Profile" in DRY_RUN and "Content-Profile" in DRY_RUN
    assert "No network request or production write was made." in DRY_RUN
