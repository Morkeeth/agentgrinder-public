"""Sign-in UI must say STRIVE, never Agentgrinder. OAuth app name is Oscar's GitHub setting."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def test_brand_constant_is_strive():
    brand = (ROOT / "server" / "brand.mjs").read_text()
    assert "export const BRAND='STRIVE'" in brand or 'export const BRAND="STRIVE"' in brand
    assert "Agentgrinder" not in brand
    assert "Agent Grinder" not in brand


def test_show_sign_in_copy_has_no_agentgrinder():
    """The in-app sign-in dialog is our copy. GitHub's consent title is not."""
    index = (SITE / "index.html").read_text()
    start = index.index("function showSignIn")
    end = index.index("\nfunction viewIdentitySetup", start)
    block = index[start:end]
    assert "Continue with GitHub" in block
    assert "__BRAND__" in block or "STRIVE" in block
    assert "Agentgrinder" not in block
    assert "Agent Grinder" not in block


def test_auth_js_oauth_does_not_set_app_display_name():
    """We only pass provider+redirectTo; GitHub fills Application name from Oscar's OAuth App."""
    auth = (SITE / "auth.js").read_text()
    assert "signInWithOAuth" in auth
    assert "Agentgrinder" not in auth
    assert "Agent Grinder" not in auth
