from pathlib import Path


INDEX = (Path(__file__).resolve().parents[1] / "site" / "index.html").read_text()


def identity_setup():
    start = INDEX.index("function viewIdentitySetup()")
    end = INDEX.index("\nasync function refreshAuth()", start)
    return INDEX[start:end]


def test_first_profile_screen_is_one_playful_identity_moment():
    setup = identity_setup()
    assert "Claim your corner of __BRAND__." in setup
    assert "Set your name, grab your @" in setup
    assert "Your name" in setup
    assert "Your __BRAND__ @" in setup
    assert "Private by default" in setup
    assert "Your first run starts private" in setup
    assert "Record a run" not in setup


def test_profile_preview_and_claim_action_follow_the_inputs():
    setup = identity_setup()
    assert "identity-preview-name" in setup
    assert "identity-preview-handle" in setup
    assert "identity-preview-avatar" in setup
    assert "nameInput.addEventListener('input',previewIdentity)" in setup
    assert "handleInput.addEventListener('input',previewIdentity)" in setup
    assert "submit.textContent='Claim @'+handle" in setup
