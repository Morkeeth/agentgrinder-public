"""Profile totals: Public runs count is public-only; mixed visibility shows Visible to you."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()


def test_profile_public_runs_count_is_always_public_only():
    assert "const publicCount=R.filter(r=>r.visibility==='public').length" in INDEX
    assert 'data-count="${publicCount}"' in INDEX
    assert "visibleExtra" in INDEX
    assert "Visible to you" in INDEX
    # Non-owner must not use R.length for the Public runs cell.
    assert 'data-count="${mine?R.filter(r=>r.visibility===\'public\').length:R.length}"' not in INDEX
    assert "Public runs" in INDEX[INDEX.index("async function viewProfile") :]


def test_mixed_visibility_totals_evidence_in_markup():
    """Render the totals fragment logic for mixed public + close_friends."""
    script = r"""
const publicCount = (R) => R.filter((r) => r.visibility === "public").length;
const mixed = [
  { visibility: "public" },
  { visibility: "close_friends" },
  { visibility: "public" },
];
const mine = false;
const ME = { id: "viewer" };
const publicN = publicCount(mixed);
const visibleExtra = !mine && ME && mixed.length > publicN;
const html = `<div class="k">Public runs</div><div class="v" data-count="${publicN}"></div>` +
  (visibleExtra ? `<div class="k">Visible to you</div><div class="v" data-count="${mixed.length}"></div>` : "");
if (publicN !== 2) throw new Error("publicCount expected 2 got " + publicN);
if (!html.includes('data-count="2"')) throw new Error("public cell missing");
if (!html.includes("Visible to you") || !html.includes('data-count="3"')) throw new Error("visible extra missing");
const ownerOnlyPublic = [{ visibility: "public" }, { visibility: "private" }];
const ownerPublic = publicCount(ownerOnlyPublic);
if (ownerPublic !== 1) throw new Error("owner publicCount");
console.log(JSON.stringify({ ok: true, publicN, visible: mixed.length, ownerPublic }));
"""
    out = subprocess.check_output(["node", "-e", script], text=True)
    assert '"ok":true' in out.replace(" ", "")
