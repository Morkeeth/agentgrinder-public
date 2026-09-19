"""Public continuation prompts stay bounded and render only supported deep links."""
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_node(script: str) -> None:
    subprocess.run(["node", "-e", script, str(ROOT)], check=True)


def test_prompt_builder_caps_escapes_and_ignores_private_fields():
    run_node(
        r"""
const fork=require(process.argv[1]+'/site/fork-run.js');
const run={
  harness:'Cursor',
  project:'pace "card" <web>',
  title:'Fix the & feed',
  caption:'x\\y '.repeat(1000),
  output_url:'https://example.com/a?x=1&y=2',
  get transcript(){throw Error('private transcript was read')},
  get messages(){throw Error('private messages were read')},
  get prompt(){throw Error('private prompt was read')}
};
const prompt=fork.buildPrompt(run);
if(prompt.length>1500) throw Error('prompt exceeds cap: '+prompt.length);
for(const expected of ['Project: "pace \\"card\\" <web>"','Recorded intent: "Fix the & feed"'])
  if(!prompt.includes(expected)) throw Error('missing escaped field: '+expected);
if(prompt.includes('private transcript')) throw Error('private text leaked');
const link=fork.harnessLink(run);
if(!link||!link.href.startsWith('cursor://anysphere.cursor-deeplink/prompt?'))
  throw Error('missing Cursor deep link');
if(new URL(link.href).searchParams.get('text')!==prompt)
  throw Error('deep-link prompt did not round trip');
const oversized=fork.harnessLink({harness:'Cursor',title:'🧪'.repeat(1500)});
if(oversized) throw Error('Cursor URL exceeded its documented 8000 character cap');
"""
    )


def test_run_card_renders_continue_only_when_harness_link_exists():
    run_node(
        r"""
const fs=require('fs'),vm=require('vm');
const root=process.argv[1],html=fs.readFileSync(root+'/site/index.html','utf8');
const start=html.indexOf('function safeOutputUrl('),end=html.indexOf('function wireKudos(');
const context={
  PacecardFork:require(root+'/site/fork-run.js'),ME:null,GrinderContract:require(root+'/site/run-contract.js'),
  esc:s=>String(s??'').replace(/[<>&"']/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&#39;'}[c])),
  runAttribution:()=>({handle:'builder',name:'Builder',link:null,ghost:false}),
  avatar:()=>'',fmtDur:m=>m+'m',ackPickerHtml:()=>'',suggestAckReasons:()=>[],fiveRow:()=>'',coachBlock:()=>''
};
vm.createContext(context);vm.runInContext(html.slice(start,end),context);
const base={id:'run-1',profile_id:'other',created_at:'2026-09-15T00:00:00Z',
  started_at:'2026-09-15T00:00:00Z',title:'Repair the feed',project:'Pacecard',
  caption:'Kept the public card focused.',output_url:'https://example.com/output'};
const render=harness=>vm.runInContext('runCard('+JSON.stringify({...base,harness})+',false,0)',context);
const cursor=render('Cursor');
if(!cursor.includes('Continue in Cursor')||!cursor.includes('Copy prompt')||!cursor.includes('Captured from Cursor'))
  throw Error('Cursor continuation controls missing');
for(const harness of ['Claude Code','Codex',null]){
  const card=render(harness);
  if(card.includes('Continue in Cursor')) throw Error('unsupported harness got deep link');
  if(!card.includes('Copy prompt')) throw Error('unsupported harness lost honest fallback');
}
const preview=vm.runInContext('runCard('+JSON.stringify({...base,harness:'Cursor'})+',false,0,{preview:true})',context);
if(preview.includes('Continue in Cursor')||preview.includes('Copy prompt'))
  throw Error('unsaved preview got continuation controls');
"""
    )
