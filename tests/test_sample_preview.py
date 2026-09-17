"""Sample provenance must survive the actual helper URL and the shipped import UI."""
import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'templates/grokbot/post-agent-run/scripts/preview.py'


def test_copied_kit_runs_without_repository_parent(tmp_path):
    installed = tmp_path / 'bot-workflow' / 'post-agent-run'
    shutil.copytree(ROOT / 'templates/grokbot/post-agent-run', installed)
    result = subprocess.run(
        [sys.executable, str(installed / 'scripts/smoke_test.py')],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.startswith('PASS:')


def preview(path):
    result = subprocess.run([sys.executable, str(HELPER), str(path)],
                            check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    assert data['selected_export'] == str(path.resolve())
    assert data['selected_sitting'] == 'latest sitting in selected export'
    token = urlsplit(data['preview_url']).fragment.removeprefix('import=')
    payload = json.loads(base64.b64decode(unquote(token)))
    assert payload == data['metrics']
    return data['preview_url'], payload


@pytest.mark.parametrize('name', ['sample_grokbot_bot_activity.jsonl',
                                 'sample_grokbot_safe_real_shape.jsonl'])
def test_sample_helper_preserves_provenance_and_preview_cannot_save(name):
    url, payload = preview(ROOT / 'samples' / name)
    assert payload['is_sample'] is True
    assert all(value not in json.dumps(payload) for value in
               ['SAFE EXPORT', '/SAFE_EXPORT', '/workspace', 'private_title_prompt'])
    render_import(url, sample=True)


def test_unmarked_export_keeps_normal_save_flow(tmp_path):
    rows = [json.loads(line) for line in
            (ROOT/'samples/sample_grokbot_bot_activity.jsonl').read_text().splitlines()]
    for row in rows:
        row.pop('agentgrinder_sample')
    source = tmp_path/'selected.jsonl'
    source.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    url, payload = preview(source)
    assert 'is_sample' not in payload
    render_import(url, sample=False)


def render_import(url, sample):
    script = r'''
const fs=require('fs'),vm=require('vm');
const root=process.argv[1],url=new URL(process.argv[2]),sample=process.argv[3]==='true';
const html=fs.readFileSync(root+'/site/index.html','utf8');
const fn=html.slice(html.indexOf('function importRun(){'),html.indexOf('\nasync function viewShareRun('));
const cardFn=html.slice(html.indexOf('function runCard('),html.indexOf('function wireKudos('));
const nodes={},events={};let signins=0;
function $(id){return nodes[id]??=( {value:'',checked:false,disabled:false,innerHTML:'',addEventListener(type,fn){events[id+':'+type]=fn;}} );}
const context={$: $,GrinderContract:require(root+'/site/run-contract.js'),location:url,ME:null,
 atob:s=>Buffer.from(s,'base64').toString('utf8'),frame:()=>{},esc:s=>String(s),
 sessionStorage:{getItem:()=>null,setItem:()=>{}},
 runAttribution:()=>({handle:'preview',name:'Preview',link:'/?u=preview'}),avatar:()=>'',safeOutputUrl:()=>null,
 status:()=>{},stashImport:()=>{},showSignIn:()=>{signins++}};
vm.createContext(context);vm.runInContext(cardFn+fn+';importRun();',context);
const preview=nodes['import-card-preview'].innerHTML;
if(!preview.includes('Preview · not saved')||preview.includes('/?run=preview')||preview.includes('class="act')) throw Error('Preview has saved-run controls');
const saved=vm.runInContext("runCard({id:'real-run',profile_id:'real-author',created_at:'2026-09-14',title:'Real run'},false,0)",context);
for(const text of ['ACK','Discuss','Share','/?run=real-run'])if(!saved.includes(text))throw Error('Saved run lost '+text);
if(!preview.includes('color:var(--blue)'))throw Error('Preview trace lost blue token');
const rendered=nodes.app.innerHTML;
if(sample){
 if(!rendered.includes('Sample card preview')||!rendered.includes('not your activity')) throw Error('Sample provenance not visible');
 if(!/id="i_pub" disabled/.test(rendered)) throw Error('Sample save not disabled');
}else if(/id="i_pub" disabled/.test(rendered)) throw Error('Real export save disabled');
(async()=>{
 await events['i_pub:click']();
 if(signins!==(sample?0:1)) throw Error('Sample reached sign-in/save, or real path regressed');
})().catch(error=>{console.error(error);process.exitCode=1;});
'''
    subprocess.run(['node', '-e', script, str(ROOT), url, str(sample).lower()], check=True)


def test_captured_sample_draft_keeps_provenance_on_public_export(tmp_path):
    from agentgrinder.capture import connect, scan
    from agentgrinder.push import export_run
    db = connect(tmp_path/'capture')
    try:
        result = scan(db, [('grokbot', ROOT/'samples/sample_grokbot_bot_activity.jsonl')])
        assert result['created'] == 1
        stored = json.loads(db.execute('select payload from drafts').fetchone()[0])
        exported = export_run(stored)
        assert exported['is_sample'] is True
        assert 'private_title_prompt' not in exported
        assert '/workspace' not in json.dumps(exported)
    finally:
        db.close()
