"""The two acceptance checks that had never been run, wired into the suite so they can go red.

Both drive a real Chromium against the repository's disposable stack. Neither writes to the hosted
database, creates an account, or posts anything.

A skip here is a skip, not a pass. If no interpreter on this machine has Playwright, the reason is
printed rather than the check quietly disappearing.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _interpreter_with_playwright() -> str | None:
    candidates = [sys.executable]
    for name in ("python3", "python3.12", "python3.11"):
        found = shutil.which(name)
        if found and found not in candidates:
            candidates.append(found)
    for candidate in candidates:
        probe = subprocess.run([candidate, "-c", "import playwright.sync_api"],
                               capture_output=True)
        if probe.returncode == 0:
            return candidate
    return None


PYTHON = _interpreter_with_playwright()
NEEDS_BROWSER = pytest.mark.skipif(
    PYTHON is None,
    reason="no interpreter on this machine has playwright, so the browser round trip cannot run")


@NEEDS_BROWSER
def test_a_saved_ridge_survives_a_browser_reload():
    """Control first: a run with no bins must draw no ridge, or the pass proves nothing."""
    done = subprocess.run([PYTHON, str(ROOT / "scripts/check-ridge-reload-browser.py")],
                          cwd=str(ROOT), capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "PASS" in done.stdout


@NEEDS_BROWSER
def test_three_readers_two_surfaces_and_the_excluded_reader_is_red_on_both():
    done = subprocess.run([PYTHON, str(ROOT / "scripts/check-three-reader-visibility.py")],
                          cwd=str(ROOT), capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "PASS" in done.stdout
