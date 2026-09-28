"""Share cards use the same honest session strip as the browser card."""
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = r"""
import fs from 'node:fs';
import vm from 'node:vm';
import {card} from './server/public-run.mjs';

const context={window:{},URL};
vm.runInNewContext(fs.readFileSync('./site/sharing.js','utf8'),context);
const {metricStrip:strip,shareFacts:share,workLabel:work,storyFacts:story,traceSeries:trace,shareQualifier:qualifier}=context.window.GrinderSharing;
const base={id:'r1',title:'A real run',visibility:'public',profiles:{handle:'sample'}};
const zero={...base,duration_s:0,prompts:0,tool_calls:0,files_touched:0,commits:0};
const unknown={...base,duration_s:null,prompts:null,tool_calls:null,files_touched:null,commits:null};
const rich={...base,caption:'Human caption',project:'agentgrinder-public',output_url:'https://github.com/example/repo/pull/34',
 shell_calls:4,files_touched:7,commits:2,tool_calls:22,private_title_prompt:'PRIVATE PROMPT',
 command:'PRIVATE COMMAND',path:'/private/repo/secret.py',tool_output:'PRIVATE OUTPUT'};
const generic={...base,project:'session',tool_calls:9};
const cursor={...rich,ridge:Array.from({length:50},(_,i)=>i%7),worker_bins:Array(50).fill(0),
 ridge_basis:'wall-time',ridge_wall_seconds:900,rhythm:[9,9]};
const grok={...base,harness:'Grok Bot',duration_s:null,rhythm:[1,1,1],
 trace_basis:'typed-turn order; Grok Bot export has no top-level event timestamps'};
const grokRidge={...grok,ridge:[1,0,0,0,0,0,0,0,2,0,0,0,0,0,0,0,5,0,0,0,0,0,0,0,13,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,7,0,0,0,0,0,0,0,0,0],
 worker_bins:Array(50).fill(0),ridge_basis:'turn-order'};
const text=node=>{
  if(node==null)return[];
  if(typeof node==='string'||typeof node==='number')return[String(node)];
  const children=node.props&&node.props.children;
  return Array.isArray(children)?children.flatMap(text):text(children);
};
process.stdout.write(JSON.stringify({
  zero:strip(zero),
  unknown:strip(unknown),
  rich:story(rich),
  shareRich:share({...rich,wall_time_s:900,prompts:3}),
  shareRecorded:share({...base,duration_s:300,turns_typed:2,commits:null,files_changed:4,files_touched:19,tool_calls:88}),
  shareRecordedWithBasis:share({...base,duration_s:300,trace_basis:'elapsed',turns_typed:2}),
  shareNamedCheck:share({...base,checks_passed:12,check_label:'Browser journey',commits:2,wall_time_s:61,prompts:1}),
  shareUnknown:share({...unknown,files_touched:12,tool_calls:40}),
  shareZeroWork:share({...base,commits:0,files_changed:0,duration_s:60,prompts:1}),
  workRich:work(rich),
  generic:story(generic),
  cursorTrace:trace(cursor),
  grokTrace:trace(grok),
  grokRidgeTrace:trace(grokRidge),
  ogRich:text(card(rich)),
  ogGeneric:text(card(generic)),
  ogZero:text(card(zero)),
  ogUnknown:text(card(unknown)),
  ogOutcome:text(card({...base,note:'Builder says the import now opens.',duration_s:300})),
  qualifierCoach:qualifier?qualifier({label:'Observed outcome',outcomeSource:'runs.coach_verdict'},false):null,
  qualifierBuilder:qualifier?qualifier({label:'Builder’s account',outcomeSource:'runs.note'},false):null,
}));
"""


def render():
    result = subprocess.run(
        ["node", "--input-type=module", "-e", SCRIPT],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_download_share_strip_preserves_zero_and_hides_missing():
    result = render()
    assert result["zero"] == [
        ["Session", "0s"],
        ["Turns", "0"],
        ["Tool calls", "0"],
    ]
    assert result["unknown"] == []


def test_public_link_preview_preserves_zero_and_omits_unrecorded_fields():
    # The share image draws the feed card's figures (Feed.headline, Feed.stats): a recorded zero
    # turn count is drawn, and nothing the row did not record is drawn or guessed.
    result = render()
    zero = result["ogZero"]
    assert zero[zero.index("Turns") + 1] == "0"
    assert "Unknown" not in result["ogUnknown"]
    for label in ("Time", "Turns", "Tool calls", "Files", "Commits"):
        assert label not in result["ogUnknown"]


def test_share_surfaces_tell_output_project_and_code_story_without_raw_data():
    result = render()
    assert result["rich"] == {
        "project": "agentgrinder-public",
        "output": "PR linked",
        "code": "4 shell calls · 7 files touched · 2 commits",
    }
    assert result["generic"] == {
        "project": None,
        "output": None,
        "code": "9 tool calls",
    }
    joined = " ".join(result["ogRich"])
    for value in ("PR linked", "2 commits"):
        assert value in joined
    assert "agentgrinder-public" not in joined     # the page's card names no project either
    rich = result["ogRich"]
    assert rich[rich.index("Tool calls") + 1] == "22" and rich[rich.index("Files touched") + 1] == "7"
    assert "files changed" not in joined.lower()
    for private in ("PRIVATE PROMPT", "PRIVATE COMMAND", "/private/", "PRIVATE OUTPUT"):
        assert private not in joined
    assert "Output" not in result["ogGeneric"]


def test_download_share_photo_uses_the_card_metric_contract():
    result = render()
    assert result["shareRich"] == [
        ["commits", "2"],
        ["Elapsed", "15m"],
        ["Your prompts", "3"],
    ]
    # files_touched is an attempted-target count. Only the separately measured files_changed may
    # become the work fact, and a duration without a wall-clock basis remains explicitly unknown.
    assert result["shareRecorded"] == [
        ["files changed", "4"],
        ["Duration · basis unknown", "5m"],
        ["Your prompts", "2"],
    ]
    assert result["shareRecordedWithBasis"] == [
        ["Recorded time", "5m"],
        ["Your prompts", "2"],
    ]
    assert result["shareNamedCheck"] == [
        ["Browser journey", "12 passed"],
        ["Elapsed", "1m"],
        ["Your prompts", "1"],
    ]
    assert result["shareUnknown"] == []
    assert result["shareZeroWork"] == [
        ["Duration · basis unknown", "1m"],
        ["Your prompts", "1"],
    ]
    assert result["workRich"] == {"label": "View pull request", "host": "github.com"}


def test_share_photo_keeps_provenance_and_limits_off_the_image():
    source = (ROOT / "site" / "sharing.js").read_text()
    draw = source.split("function draw(){", 1)[1].split("form.addEventListener", 1)[0]
    for stale in ("sourceLine", "Limit: ", "SESSION TIME", "OUTPUT", "CODE ACTIVITY", "EFFORT"):
        assert stale not in draw


def test_share_photo_attributes_the_account_that_supplied_the_outcome():
    result = render()
    assert result["qualifierCoach"] == "Observed outcome · measured facts describe this run"
    assert result["qualifierBuilder"] == "Builder’s account · measured facts describe this run"


def test_server_share_image_keeps_source_and_limit_in_explore():
    result = render()
    image_text = " ".join(result["ogOutcome"])
    assert "Evidence source:" not in image_text
    assert "Limit:" not in image_text
    assert "Duration · basis unknown" in image_text
    assert "Session time" not in image_text
    assert "Builder-authored account." not in image_text


def test_removed_account_shortcut_does_not_break_session_restore():
    index = (ROOT / "site" / "index.html").read_text()
    assert "if($('deletewrap'))$('deletewrap').hidden=!ME" in index
    assert "private until you choose and save" not in index


def test_download_uses_cursor_timed_ridge_and_keeps_grok_time_unknown():
    result = render()
    assert result["cursorTrace"]["label"] == "Tool calls over wall time"
    assert len(result["cursorTrace"]["values"]) == 50
    assert result["grokTrace"]["label"] == "Session activity · time basis unknown"
    assert result["grokTrace"]["values"] == [1, 1, 1]
    assert result["unknown"] == []


def test_share_image_labels_turn_order_ridge_not_call_order():
    result = render()
    assert result["grokRidgeTrace"]["label"] == "Tool calls over turn order"
    assert result["grokRidgeTrace"]["values"][24] == 13
