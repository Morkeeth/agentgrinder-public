"""A cold proof page reads only public runs and never leaks a private title."""
from pathlib import Path
import json
import subprocess


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "11111111-1111-1111-1111-111111111111"
API_SCRIPT = r'''
const root=process.argv[1],id=process.argv[2],rows=JSON.parse(process.argv[3]);
let fetches=0;
globalThis.fetch=async()=>{fetches++;return{ok:true,json:async()=>rows}};
const handler=require(root+'/api/proof.js');
const req={query:{id}};
const headers={};let body='';
const res={statusCode:200,setHeader:(k,v)=>{headers[k.toLowerCase()]=v},end:(b)=>{body=String(b??'')}};
handler(req,res).then(()=>console.log(JSON.stringify({status:res.statusCode,type:headers['content-type'],body,fetches})));
'''


def serve(run_id, rows):
    result = subprocess.run(
        ["node", "-e", API_SCRIPT, str(ROOT), run_id, json.dumps(rows)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_public_proof_render_and_private_red_path():
    result = subprocess.run(
        ["node", str(ROOT / "tests" / "fixtures" / "public_proof_probe.mjs")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS public proof" in result.stdout


def test_public_proof_route_uses_the_existing_public_only_reader():
    api = (ROOT / "api" / "proof.js").read_text()
    routes = (ROOT / "vercel.json").read_text()
    assert "readPublic(id)" in api
    assert "neutralProofHtml(id)" in api
    assert '"/proof/:id"' in routes
    assert '"/api/proof?id=:id"' in routes


def test_nonpublic_row_is_neutral_in_the_real_proof_handler():
    private = {
        "id": RUN_ID,
        "visibility": "link",
        "title": "SECRET NIGHT RUN",
        "code_route": {"v": 1, "projects": [], "stops": []},
    }
    out = serve(RUN_ID, [private])
    assert out["status"] == 200
    assert out["type"].startswith("text/html")
    assert "This public proof is unavailable" in out["body"]
    assert "SECRET NIGHT RUN" not in out["body"]


def test_public_row_reaches_the_proof_handler():
    public = {
        "id": RUN_ID,
        "visibility": "public",
        "title": "Fixture public proof",
        "code_route": {
            "v": 1,
            "projects": [{"id": "app", "label": "app"}],
            "stops": [{"id": "check", "project": "app", "label": "Check passed", "basis": "measured"}],
        },
    }
    out = serve(RUN_ID, [public])
    assert out["status"] == 200
    assert "Fixture public proof" in out["body"]
    assert "1/1 checkpoints are recorded as measured" in out["body"]


def test_public_row_without_a_route_is_truthful_not_503():
    public = {
        "id": RUN_ID,
        "visibility": "public",
        "title": "Public run without a route",
        "code_route": None,
    }
    out = serve(RUN_ID, [public])
    assert out["status"] == 200
    assert out["type"].startswith("text/html")
    assert "Public run without a route" in out["body"]
    assert "no recorded Code Route" in out["body"]
    assert f'/r/{RUN_ID}' in out["body"]
    assert "Public proof temporarily unavailable" not in out["body"]
