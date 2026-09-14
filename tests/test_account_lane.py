"""Account control and sign-in recovery lane contracts: honest providers, safe destructive copy."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNT = (ROOT / "site" / "account.js").read_text()
AUTH = (ROOT / "site" / "auth.js").read_text()
CSS = (ROOT / "site" / "account.css").read_text()
LOOP = (ROOT / "scripts" / "check-account-loop.py").read_text()
INDEX = (ROOT / "site" / "index.html").read_text()
PACKAGE = (ROOT / "package.json").read_text()


def test_account_module_owns_the_panel_and_recovery():
    assert "window.GrinderAccount" in ACCOUNT
    assert "async function view" in ACCOUNT
    assert "function recover" in ACCOUNT
    exported = ACCOUNT.rsplit("return {", 1)[1]
    assert "view" in exported and "recover" in exported


def test_no_cursor_or_origin_login_and_x_is_gated():
    assert "data-link=\"cursor\"" not in ACCOUNT and "Continue with Cursor" not in ACCOUNT and "Continue with Origin" not in ACCOUNT
    assert "not a login" in ACCOUNT
    assert "is not available on this service yet" in ACCOUNT
    assert "providersEnabled" in ACCOUNT
    assert 'PROVIDERS_ENABLED=["github","email"]' in INDEX, "X stays off until the hosted provider exists"


def test_destructive_action_explains_what_goes_and_stays_without_confirm_dialog():
    assert "Goes:" in ACCOUNT and "Stays:" in ACCOUNT
    assert "Agent Grinder profile" in ACCOUNT
    assert "cannot be restored" in ACCOUNT
    assert "Type your handle" in ACCOUNT
    assert "confirm(" not in ACCOUNT
    assert "deleteProfile" in ACCOUNT and "signOutLocal" in ACCOUNT


def test_last_identity_and_duplicate_handle_are_actionable():
    assert "only way to sign in" in ACCOUNT
    assert "handle_taken" in ACCOUNT and "freeVariant" in ACCOUNT
    assert 'aria-invalid' in ACCOUNT and 'role="status"' in ACCOUNT


def test_auth_recovery_reads_hash_and_query_and_remembers_pending():
    assert "parseAuthError" in AUTH and "recoverFromUrl" in AUTH
    assert "ag_auth_pending" in AUTH
    for code in ("cancelled", "link_expired", "provider_failed", "last_identity", "identity_taken", "linking_disabled"):
        assert '"' + code + '"' in AUTH


def test_profile_id_stays_stable_and_deletion_is_strava_only():
    assert 'eq("auth_uid", u.id)' in AUTH
    assert 'from("profiles").delete()' in AUTH
    assert "auth.admin" not in AUTH and "deleteUser" not in AUTH, "no Auth-user deletion from the client"
    assert 'scope: "local"' in AUTH


def test_phone_and_keyboard_surface():
    assert "min-height:44px" in CSS
    assert "@media(max-width:600px)" in CSS
    assert "aria-labelledby" in ACCOUNT and "aria-live" in ACCOUNT


def test_browser_walk_covers_the_assigned_checks_and_shell_hooks():
    for needle in ("access_denied", "last_identity", "grinder-snapshot", "test-riley-2", "scope=local", "HOOK_ROUTE2_NEW", "HOOK_CONFIRM_OLD"):
        assert needle in LOOP
    assert '"test:account"' in PACKAGE
