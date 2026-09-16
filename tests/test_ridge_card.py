"""The ridge is opt-in per run. Legacy cards render byte for byte as before."""
import json
import hashlib
import subprocess
from pathlib import Path

from agentgrinder.metrics import build_activity
from agentgrinder.render import render_card

ROOT = Path(__file__).resolve().parents[1]
LEGACY_SHA256 = "a026a21714faa3d0716e80ec1e79b114bc178e898770e25624904093a7547800"  # main after PR 30, 16 Sep

SCRIPT = r"""
const fs=require('fs'),vm=require('vm'),crypto=require('crypto');
const root=process.argv[1],html=fs.readFileSync(root+'/site/index.html','utf8');
const fn=html.slice(html.indexOf('function runCard('),html.indexOf('function wireKudos('));
const context={GrinderContract:require(root+'/site/run-contract.js'),ME:null,
 esc:s=>String(s??'').replace(/[<>&"']/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&#39;'}[c])),
 fmtDur:m=>!m?'-':(m>=60?`${Math.floor(m/60)}h ${m%60}m`:`${m}m`),
 runAttribution:()=>({handle:'sample',name:'Sample',link:null}),avatar:()=>'',safeOutputUrl:v=>v||null,
 ackPickerHtml:()=>'',suggestAckReasons:()=>[],fiveRow:()=>'<div class="coaching-cell">coaching</div>',
 coachBlock:()=>'<div class="coach">coach</div>'};
vm.createContext(context);vm.runInContext(fn,context);
const base={id:'r1',profile_id:'p1',created_at:'2026-09-14T00:00:00Z',title:'Plain run',
 started_at:'2026-09-14T00:00:00Z',duration_s:600,prompts:3};
const plain=vm.runInContext('runCard('+JSON.stringify(base)+',false,0)',context);
const ridge=Array.from({length:50},(_,i)=>i%9),workers=Array.from({length:50},(_,i)=>i>8&&i<42?(i%4):0);
const shaped=vm.runInContext('runCard('+JSON.stringify({...base,ridge,worker_bins:workers,
 ridge_basis:'wall-time',ridge_wall_seconds:605,commit_bins:[12,38],commits:2,
 output_url:'https://github.com/example/repo/pull/1'})+',false,0)',context);
const outputOnly=vm.runInContext('runCard('+JSON.stringify({...base,ridge,worker_bins:workers,
 ridge_basis:'wall-time',ridge_wall_seconds:605,commit_bins:[],commits:0,
 output_url:'https://github.com/example/repo/pull/1'})+',false,0)',context);
process.stdout.write(JSON.stringify({plainHash:crypto.createHash('sha256').update(plain).digest('hex'),shaped,outputOnly}));
"""


def render():
    result = subprocess.run(
        ["node", "-e", SCRIPT, str(ROOT)], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def test_card_without_ridge_is_byte_identical():
    assert render()["plainHash"] == LEGACY_SHA256
    activity = build_activity({
        "athlete": "you", "title": "Plain", "harness": "Cursor", "project": "sample",
        "turns_typed": 3, "tool_calls": 2, "commits": 1, "rhythm": [1, 2, 1],
    })
    assert hashlib.sha256(render_card(activity).encode()).hexdigest() == \
        "c4db61d25de3c0be88bd8e1b3916f82fa41b7cd1b8e0b9e2a4d385442eb1b827"


def test_card_draws_one_primary_ridge_and_three_numbers():
    html = render()["shaped"]
    assert html.count('class="ridge-line"') == 1
    assert html.count('class="ridge-fill"') == 1
    assert html.count('class="ridge-worker ') <= 3
    assert 'class="ridge-start"' in html and 'class="ridge-end"' in html
    assert html.count('class="ridge-commit"') == 2
    facts = html[html.index('class="run-key-facts"'):html.index('</div></div>', html.index('class="run-key-facts"'))]
    assert facts.count("<div>") == 3
    assert all(label in facts for label in ("Wall time", "Turns", "Commits"))
    assert html.index("<summary>More</summary>") < html.index("coaching-cell")
    output_facts = render()["outputOnly"]
    output_facts = output_facts[output_facts.index('class="run-key-facts"'):]
    assert "<span>Output</span><strong>PR</strong>" in output_facts


OG_SCRIPT = r"""
import {card} from './server/public-run.mjs';
const legacy={id:'r1',title:'Plain run',caption:'c',project:'p',visibility:'public',prompts:3,
 commits:1,wall_time_s:600,rhythm:[1,2,1,3,2],profiles:{handle:'sample'}};
const ridge=Array.from({length:50},(_,i)=>i%9),workers=Array.from({length:50},(_,i)=>i>8&&i<42?(i%4):0);
const shaped={...legacy,ridge,worker_bins:workers,commit_bins:[12,38],ridge_basis:'wall-time',
 ridge_wall_seconds:605.5};
process.stdout.write(JSON.stringify({
 shaped:JSON.stringify(card(shaped)),
 legacy:JSON.stringify(card(legacy))}));
"""


def test_og_renderer_keeps_legacy_cards_and_draws_a_persisted_ridge():
    """PR 29 froze server/public-run.mjs byte for byte. The rename lane had to patch that
    freeze, and slice S2 changes the file again on purpose so the share image can use the
    persisted ridge. A byte pin freezes an implementation, it does not test behaviour, so it
    is replaced here by the property the pin was reaching for: a run with no bins renders the
    same rhythm polyline it always did, and only a run with bins draws the filled ridge."""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", OG_SCRIPT],
        cwd=ROOT, check=True, capture_output=True, text=True)
    rendered = json.loads(result.stdout)
    assert '"type":"polyline"' in rendered["legacy"]
    assert '"type":"polygon"' not in rendered["legacy"]
    assert "Session trace" in rendered["legacy"]
    assert '"type":"polygon"' in rendered["shaped"]
    assert "Agent ridge" in rendered["shaped"]
    assert "Session trace" not in rendered["shaped"]
