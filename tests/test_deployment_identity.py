"""Deployment identity comes only from Vercel's immutable commit value."""
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SHA = "0123456789abcdef0123456789abcdef01234567"


def build(commit_sha=None):
    env = os.environ.copy()
    env.pop("VERCEL_GIT_COMMIT_SHA", None)
    if commit_sha is not None:
        env["VERCEL_GIT_COMMIT_SHA"] = commit_sha
    subprocess.run(
        ["node", str(ROOT / "scripts" / "build-site.mjs")],
        cwd=ROOT,
        env=env,
        check=True,
    )
    return (ROOT / "dist" / "index.html").read_text()


def health(commit_sha=None):
    script = """
const assert = require('node:assert/strict');
const handler = require('./api/health.js');
global.fetch = async () => ({ok: true});
const headers = {};
let status;
let body;
const res = {
  setHeader(name, value) { headers[name] = value; },
  status(value) { status = value; return this; },
  json(value) { body = value; },
};
handler({}, res).then(() => {
  process.stdout.write(JSON.stringify({headers, status, body}));
});
"""
    env = os.environ.copy()
    env.pop("VERCEL_GIT_COMMIT_SHA", None)
    if commit_sha is not None:
        env["VERCEL_GIT_COMMIT_SHA"] = commit_sha
    result = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_build_adds_the_vercel_commit_to_a_meta_tag():
    html = build(SHA)
    assert f'<meta name="strive-git-sha" content="{SHA}">' in html


def test_build_omits_missing_or_invalid_commit_values():
    assert 'name="strive-git-sha"' not in build()
    assert 'name="strive-git-sha"' not in build("not-a-git-sha")


def test_health_exposes_the_same_commit_in_json_and_a_header():
    response = health(SHA)
    assert response["status"] == 200
    assert response["body"]["git_sha"] == SHA
    assert response["headers"]["X-Strive-Git-Sha"] == SHA


def test_health_omits_missing_or_invalid_commit_values():
    for value in (None, "not-a-git-sha"):
        response = health(value)
        assert "git_sha" not in response["body"]
        assert "X-Strive-Git-Sha" not in response["headers"]
