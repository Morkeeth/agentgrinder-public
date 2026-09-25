"""X sign-in: offered the moment Supabase reports the provider on, handles shown on the profile.

The switch lives in the Supabase dashboard (an X developer app plus the provider toggle), which
is a human's click. The site must not need a redeploy when that click happens, and it must never
show a Continue with X button that leads to a provider that is off.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()
AUTH = (ROOT / "site" / "auth.js").read_text()
ACCOUNT = (ROOT / "site" / "account.js").read_text()
MIGRATION = (ROOT / "supabase" / "strava" / "013_x_handle.sql").read_text()


def test_providers_are_read_from_auth_settings_at_load():
    assert 'const PROVIDERS_ENABLED=["github"];' in INDEX
    assert "async function loadProviders()" in INDEX
    assert "'/auth/v1/settings'" in INDEX
    assert "ext.x===true||ext.twitter===true" in INDEX
    assert "PROVIDERS_ENABLED.push('x')" in INDEX
    # The first route waits for the settings call, and a failed call still routes.
    assert "loadProviders().then(refreshAndRoute,refreshAndRoute);" in INDEX


def test_sign_in_dialog_offers_each_enabled_oauth_provider():
    dialog = INDEX[INDEX.index("function showSignIn(") : INDEX.index("function viewIdentitySetup()")]
    assert "p==='github'||p==='x'" in dialog
    assert "Continue with '+providerLabel(p)+'" in dialog
    assert "Sign in with GitHub or X" in INDEX


def test_x_handle_is_provider_owned_like_github_handle():
    assert "function xHandleOf(user)" in AUTH
    assert 'i.provider === "x" || i.provider === "twitter"' in AUTH
    assert "/^[a-z0-9_]{1,15}$/i" in AUTH
    assert "async function syncProviderHandles()" in AUTH
    assert "if (x && !p.x_handle) patch.x_handle = x;" in AUTH
    assert "syncGithubHandle: syncProviderHandles" in AUTH
    assert "auth.syncProviderHandles || auth.syncGithubHandle" in ACCOUNT


def test_profile_shows_proved_links_only():
    assert "function profileLinksHtml(prof,mine)" in INDEX
    assert "GrinderAuth.linksOf(prof)" in INDEX
    assert "GitHub @${esc(L.github.handle)}" in INDEX and "X @${esc(L.x.handle)}" in INDEX
    assert "if(!L.x&&PROVIDERS_ENABLED.includes('x')) parts.push('<a href=\"/?account\">Link X</a>');" in INDEX
    assert "${profileLinksHtml(prof,mine)}" in INDEX


def test_migration_is_additive_and_checked():
    assert "add column if not exists x_handle text" in MIGRATION
    assert "'^[A-Za-z0-9_]{1,15}$'" in MIGRATION
    assert "create unique index if not exists profiles_x_handle_key" in MIGRATION
    for word in ("drop ", "grant ", "policy", "trigger"):
        assert word not in MIGRATION.lower().replace("no policy, grant, function or\n-- trigger changes", "")


def test_build_can_switch_x_on_without_a_commit():
    build = (ROOT / "scripts" / "build-site.mjs").read_text()
    assert "process.env.AGENTGRINDER_X_SIGNIN==='1'" in build
    assert "'const PROVIDERS_ENABLED=[\"github\",\"x\"];'" in build
