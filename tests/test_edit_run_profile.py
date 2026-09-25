"""Slice H: the owner edits a run's title, project and photo, and the profile photo, on existing columns."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site/index.html").read_text()


def test_run_edit_panel_offers_title_project_and_photo():
    panel = INDEX[INDEX.index("controls.id='run-edit'"):INDEX.index("$('run-delete').onclick")]
    for field in ("run-title", "run-project", "run-image-url", "run-caption", "run-output-url", "run-audience"):
        assert f'id="{field}"' in panel
    # runs.title is NOT NULL: an empty title is refused in the page, an empty project saves null.
    assert "if(!title){status('Add a title.',true)" in panel
    assert "update({title,project:project||null,image_url:imageUrl||null" in panel
    assert "isRunPhotoUrl(imageUrl)" in panel
    # Only the owner gets the panel.
    assert "if(ME?.id===r.profile_id){" in INDEX[INDEX.index("async function viewRun(id){"):INDEX.index("controls.id='run-edit'")]


def test_run_photo_rule_matches_the_contract():
    import json, subprocess
    start = INDEX.index("function isRunPhotoUrl(u){")
    fn = INDEX[start:INDEX.index("\n}\n", start) + 2]
    cases = {
        "https://example.com/a.jpg": True,
        "https://example.com/a.webp?x=1": True,
        "http://example.com/a.jpg": False,
        "https://example.com/a.gif": False,
        "https://example.com/\"onerror=\"x.jpg": False,
        "https://example.com/" + "a" * 300 + ".png": False,
        "javascript:alert(1)//.png": False,
    }
    js = fn + "\nconst c=" + json.dumps(cases) + ";process.stdout.write(JSON.stringify(Object.keys(c).map(k=>isRunPhotoUrl(k)===c[k])))"
    out = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
    assert all(out), dict(zip(cases, out))


def test_profile_edit_offers_a_photo_link_and_refuses_http():
    assert 'id="e_avatar"' in INDEX
    save = INDEX[INDEX.index("$('savep').addEventListener"):INDEX.index("function signInWithGitHub")]
    assert "avatar_url:avatarUrl" in save
    assert "/^https:\\/\\/[^\\s]+$/i.test(avatarUrl)" in save


def test_profile_header_shows_the_face_for_a_person():
    assert "GrinderFeed.face({profiles:prof},56)" in INDEX
