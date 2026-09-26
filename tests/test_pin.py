"""Pin runs to a profile: migration 015 in PGlite, and the profile and edit panel use it."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site/index.html").read_text()


def test_migration_015_owner_pins_up_to_three():
    out = subprocess.run(["node", "scripts/test-pin-migration.mjs"], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, (out.stdout + out.stderr)[-2000:]


def test_profile_shows_pinned_first_and_only_visible_runs():
    view = INDEX[INDEX.index("async function viewProfile("):INDEX.index("function signInWithGitHub")]
    # Pinned runs come from R, which is already filtered to what this reader may see.
    assert "const PINNED=R.filter(r=>r.pinned_at)" in view and ".slice(0,3)" in view
    assert view.index("${pinnedHtml}") < view.index("Your recent runs")
    assert "const RECENT=R.filter(r=>!PINNED.includes(r))" in view


def test_edit_panel_pins_and_unpins():
    panel = INDEX[INDEX.index("controls.id='run-edit'"):INDEX.index("$('run-delete').onclick")]
    assert 'id="run-pin"' in panel
    assert "pinned_at:pin?(r.pinned_at||new Date().toISOString()):null" in panel
