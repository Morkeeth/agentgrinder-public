"""The share page for a missing or non-public run is a neutral card, not a plain 404.

Measured live on 16 Sep 2026 at agentic-strava.vercel.app: /r/<missing id>, /r/<close friends id>
and /r/not-a-uuid all answered 404 text/plain "This public run is unavailable.", while
/api/run?id=<missing id>&image=1 answered a 200 PNG neutral card. A link pasted into a message
therefore unfurled nothing and a tap landed on plain text with no way in.

This drives api/run.js through node with a stubbed global fetch, so no database, no
@vercel/og and no network are needed. The image branch is not exercised here; the existing
scripts/check-public-preview.mjs covers it.
"""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MISSING = "00000000-0000-0000-0000-000000000000"

SCRIPT = r'''
const root=process.argv[1],id=process.argv[2],rows=JSON.parse(process.argv[3]);
let fetches=0;
globalThis.fetch=async()=>{fetches++;return{ok:true,json:async()=>rows}};
const handler=require(root+'/api/run.js');
const req={query:{id}};
const headers={};let body='';
const res={statusCode:200,setHeader:(k,v)=>{headers[k.toLowerCase()]=v},end:(b)=>{body=String(b??'')}};
handler(req,res).then(()=>{console.log(JSON.stringify({status:res.statusCode,type:headers['content-type'],body,fetches}))});
'''


def serve(run_id, rows):
    result = subprocess.run(
        ["node", "-e", SCRIPT, str(ROOT), run_id, json.dumps(rows)],
        cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_missing_run_page_is_a_neutral_html_card():
    out = serve(MISSING, [])
    assert out["status"] == 200
    assert out["type"].startswith("text/html")
    page = out["body"]
    assert "This run is private on STRIVE" in page
    assert f'/api/run?id={MISSING}&amp;image=1' in page or f'/api/run?id={MISSING}&image=1' in page
    assert 'property="og:image"' in page
    assert f'href="/?run={MISSING}"' in page
    # Neutral means neutral: no run title, caption, handle, project or counts can be present,
    # because the page was built without a row.
    for leak in ("og:title\" content=\"Grok", "@", "Typed turns", "Wall time"):
        assert leak not in page


def test_non_public_run_page_is_byte_identical_to_the_missing_one():
    # The public-only query returns no row for a close friends run, so the handler cannot tell
    # the two cases apart and must not. Same bytes, same status.
    assert serve(MISSING, []) == serve(MISSING, [])
    other = "11111111-1111-1111-1111-111111111111"
    assert serve(other, [])["body"].replace(other, MISSING) == serve(MISSING, [])["body"]


def test_invalid_id_stays_a_plain_404_and_never_queries():
    out = serve("not-a-uuid", [])
    assert out["status"] == 404
    assert out["type"].startswith("text/plain")
    assert out["fetches"] == 0


def test_public_run_page_is_unchanged():
    row = {"id": MISSING, "title": "Fixture public run", "caption": "one line", "visibility": "public",
           "profiles": {"handle": "fixture-builder"}}
    out = serve(MISSING, [row])
    assert out["status"] == 200
    assert "Fixture public run" in out["body"]
    assert "This run is private on STRIVE" not in out["body"]


def test_a_non_public_row_that_reaches_the_handler_still_gets_the_neutral_page():
    # The public-only filter lives in the query string. If it were ever lost, or the REST layer
    # ignored it, a close friends row would arrive here. The page must still be neutral.
    row = {"id": MISSING, "title": "SECRET TITLE", "caption": "SECRET CAPTION",
           "visibility": "close_friends", "profiles": {"handle": "secret-handle"}}
    out = serve(MISSING, [row])
    assert out["status"] == 200
    assert "This run is private on STRIVE" in out["body"]
    for leak in ("SECRET TITLE", "SECRET CAPTION", "secret-handle"):
        assert leak not in out["body"]
    # Byte-identical to the missing page, so the two cases cannot be told apart.
    assert out["body"] == serve(MISSING, [])["body"]
