"""Run cards keep the blue trace and show honest, shareable session facts."""
import json
import subprocess
from pathlib import Path

from agentgrinder.metrics import build_activity
from agentgrinder.render import render_card

ROOT = Path(__file__).resolve().parents[1]

SCRIPT = r"""
const fs=require('fs'),vm=require('vm');
const root=process.argv[1],html=fs.readFileSync(root+'/site/index.html','utf8');
const fn=html.slice(html.indexOf('function connectWrapperName('),html.indexOf('function wireKudos('));
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
 ridge_basis:'wall-time',ridge_wall_seconds:605,commit_bins:[12,38],shell_calls:4,files_touched:5,commits:2,
 project:'agentgrinder-public',
 output_url:'https://github.com/example/repo/pull/1'})+',false,0)',context);
const outputOnly=vm.runInContext('runCard('+JSON.stringify({...base,ridge,worker_bins:workers,
 ridge_basis:'wall-time',ridge_wall_seconds:605,commit_bins:[],commits:0,
 output_url:'https://github.com/example/repo/pull/1'})+',false,0)',context);
const zero=vm.runInContext('runCard('+JSON.stringify({...base,duration_s:0,prompts:0,tool_calls:0,
 files_touched:0,commits:0})+',false,0)',context);
const unknown=vm.runInContext('runCard('+JSON.stringify({...base,duration_s:null,prompts:null,
 tool_calls:null,shell_calls:null,files_touched:null,commits:null,project:'session',
 private_title_prompt:'PRIVATE PROMPT',command:'PRIVATE COMMAND',path:'/private/secret.py',
 tool_output:'PRIVATE OUTPUT'})+',false,0)',context);
process.stdout.write(JSON.stringify({plain,shaped,outputOnly,zero,unknown}));
"""


def render():
    result = subprocess.run(
        ["node", "-e", SCRIPT, str(ROOT)], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def test_card_without_ridge_keeps_its_recorded_trace():
    """The trace survives a run with no ridge, and the card still leads with its outcome.

    This assertion used to be a sha256 of the whole card. A byte pin freezes one rendering, it
    does not test behaviour: it went red the moment the card changed for any reason, including
    the reasons it was changed for, and it said nothing about what the card had to keep. What it
    was reaching for is below — the recorded trace is drawn, and the numbers on it are the
    numbers the run measured.
    """
    assert 'class="run-signature"' in render()["plain"]
    activity = build_activity({
        "athlete": "you", "title": "Plain", "harness": "Cursor", "project": "sample",
        "turns_typed": 3, "tool_calls": 2, "commits": 1, "rhythm": [1, 2, 1],
    })
    html = render_card(activity)
    assert 'class="fc-spark"' in html and 'class="fc-line"' in html      # the rhythm, drawn
    assert '<dt>Turns</dt><dd class="num">3</dd>' in html                # prompts, as a small figure
    assert '<span class="fc-n num">1</span><span class="fc-u">commit</span>' in html
    assert "1 commit landed in sample" in html


def test_card_draws_one_primary_ridge_and_story_before_effort():
    html = render()["shaped"]
    assert html.count('class="ridge-line"') == 1
    assert html.count('class="ridge-fill"') == 1
    assert html.count('class="ridge-worker ') <= 3
    assert 'class="ridge-start"' in html and 'class="ridge-end"' in html
    assert html.count('class="ridge-commit"') == 2
    assert 'Run map' in html and 'run-map' in html
    facts = html[html.index('class="run-metrics"'):html.index("</dl>", html.index('class="run-metrics"'))]
    assert facts.count('<div class="run-metric') >= 2
    assert "Session" in facts
    assert html.index("Achieved") < html.index('ridge-wrap') < html.index("Open PR")
    assert html.index('ridge-wrap') < html.index("Project touched") < html.index("Code activity")
    assert "4</strong> Shell calls" in html
    assert "5</strong> Files changed" in html
    assert html.index('ridge-wrap') < html.index('class="run-metrics"')
    assert html.index("<summary>Explore this run</summary>") < html.index("coaching-cell")
    output_facts = render()["outputOnly"]
    assert "Open PR" in output_facts
    assert "<strong class=\"num\">0</strong> Commits" in output_facts


def test_card_keeps_recorded_zero_and_hides_missing_metrics():
    rendered = render()
    zero = rendered["zero"][rendered["zero"].index('class="run-metrics"'):]
    assert "<dt>Session</dt><dd class=\"num\">0s</dd>" in zero
    assert zero.count('<dd class="num">0</dd>') == 2
    assert 'class="run-metrics"' not in rendered["unknown"]



def test_browser_card_omits_missing_output_and_sensitive_capture_data():
    unknown = render()["unknown"]
    assert "Project touched" not in unknown
    assert "Code activity" not in unknown
    assert 'class="run-output"' not in unknown
    for private in ("PRIVATE PROMPT", "PRIVATE COMMAND", "/private/", "PRIVATE OUTPUT"):
        assert private not in unknown



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
    assert '"type":"polygon"' in rendered["shaped"]
    # the image carries no series label: the page's card draws the line without one
    for label in ("Session trace", "Agent ridge"):
        assert label not in rendered["legacy"] and label not in rendered["shaped"]


# Card truth: live public OG images on 2026-09-18 printed 0 beside a ridge drawn from 98
# calls, and drew a flat line for a pre-ridge row. These cases pin the share image only.
OG_TRUTH_SCRIPT = r"""
import {card} from './server/public-run.mjs';
const ridge=Array.from({length:50},(_,i)=>i%9);
const workers=Array.from({length:50},(_,i)=>i>8&&i<42?(i%4):0);
const walk=n=>{
 if(n==null)return[];
 if(typeof n==='string'||typeof n==='number')return[String(n)];
 if(Array.isArray(n))return n.flatMap(walk);
 if(typeof n==='object')return walk(n.props?.children);
 return[];
};
const after=(texts,label)=>{
 const i=texts.indexOf(label);return i<0?null:texts[i+1]??null;
};
const base={id:'c1',title:'Cursor night review ridge',caption:'busy graph',
 project:'CODE-worktrees-strava-night-review-20260915',visibility:'public',prompts:12,
 tool_calls:0,ridge_tool_calls:98,ridge,worker_bins:workers,ridge_basis:'wall-time',
 ridge_wall_seconds:3600,profiles:{handle:'sample'}};
const withCode={...base,shell_calls:4,files_touched:5,commits:2};
const effortOnly=base;
const nullRidge={id:'c2',title:'Pre ridge run',caption:'old row',project:'demo',
 visibility:'public',prompts:6,tool_calls:28,ridge:null,rhythm:[0,0,0,0,0],
 profiles:{handle:'sample'}};
const shaped=walk(card(withCode));
const effortTexts=walk(card(effortOnly));
const body=JSON.stringify(card(withCode));
const titleHeight=(body.match(/"fontSize":44,"fontWeight":700,"letterSpacing":-1,"marginTop":22,"height":(\d+)/)||[])[1]||null;
const nullBody=JSON.stringify(card(nullRidge));
const nullTexts=walk(card(nullRidge));
process.stdout.write(JSON.stringify({
 toolCalls:after(shaped,'Tool calls'),
 toolCallsEffortOnly:after(effortTexts,'Tool calls'),
 heroEffortOnly:effortTexts[effortTexts.indexOf('tool calls')-1]??null,
 codeActivity:after(effortTexts,'Code activity'),
 joined:shaped.join(' '),
 titleHeight:titleHeight&&Number(titleHeight),
 nullHasPolyline:nullBody.includes('"type":"polyline"'),
 nullHasPolygon:nullBody.includes('"type":"polygon"'),
 nullTexts,
}));
"""


def _og_truth():
    result = subprocess.run(
        ["node", "--input-type=module", "-e", OG_TRUTH_SCRIPT],
        cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def test_og_card_uses_ridge_tool_calls_when_tool_calls_is_zero():
    """A ridge drawn from 98 calls must not print 0 in the tool call slots."""
    rendered = _og_truth()
    assert rendered["toolCalls"] == "98"
    # With no commits or files, the 98 calls are the card's one big number, not a small figure.
    assert rendered["heroEffortOnly"] == "98"
    assert rendered["toolCallsEffortOnly"] is None
    assert rendered["codeActivity"] is None
    assert "strava night review" not in rendered["joined"]   # the page's card names no project
    assert rendered["titleHeight"] is not None and rendered["titleHeight"] >= 54


def test_og_card_draws_no_flat_line_when_ridge_is_null():
    """A null ridge is a missing shape. Do not draw a flat polyline from leftover rhythm."""
    rendered = _og_truth()
    assert rendered["nullHasPolyline"] is False
    assert rendered["nullHasPolygon"] is False
    joined = " ".join(rendered["nullTexts"]).lower()
    assert "not recorded" not in joined
    assert "unknown" not in joined
    assert "Session" not in rendered["nullTexts"]
    assert "6" in rendered["nullTexts"] and "28" in rendered["nullTexts"]
