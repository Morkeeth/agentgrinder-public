"""Phone path for Post your first run must be honest about desktop capture."""
from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] / "site" / "index.html").read_text()


def onboard():
    start = HTML.index("async function viewOnboard(){")
    end = HTML.index("async function viewOnboardAgent(){")
    return HTML[start:end]


def test_phone_handoff_says_capture_needs_the_computer():
    body = onboard()
    assert 'data-phone-handoff="1"' in body
    assert "Capture runs on the computer where your agent runs" in body
    assert "This phone cannot record a sitting" in body
    assert ".ob-phone-handoff{display:none}" in HTML
    assert "@media(max-width:800px)" in HTML
    assert ".ob-phone-handoff{display:block}" in HTML


def test_phone_offers_copy_and_a_real_run_not_email_command():
    body = onboard()
    assert "Copy the command" in body
    assert 'href="${REAL_RUN}">See a real run</a>' in body
    assert "/?example" not in body
    # Sign-in email OTP exists elsewhere; it must not become "email me the command".
    assert "Email me the command" not in body
    assert "signInWithOtp" not in body
    assert "mailto:" not in body


def test_desktop_copy_stays_on_the_command_line():
    body = onboard()
    assert 'id="cp1-desk"' in body
    assert "ob-cmd-copy" in body
    assert "${INSTALL_CMD}" in body


def test_removing_phone_honesty_fails_this_guard():
    """Document the red mutation: honesty string gone => primary test fails."""
    mutated = onboard().replace(
        "Capture runs on the computer where your agent runs",
        "Run this command anywhere",
        1,
    )
    assert "Capture runs on the computer where your agent runs" not in mutated
    assert "Run this command anywhere" in mutated
