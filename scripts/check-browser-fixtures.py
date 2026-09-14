"""Exercise browser forms with explicit UI fixtures; PostgreSQL permissions have separate tests.
Requires Playwright and an installed Brave browser. No requests reach the hosted database.
"""
from pathlib import Path
import json
import os
import re
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
setup=r'''
window.calls=[];
const owner='10000000-0000-0000-0000-000000000001', practice='20000000-0000-0000-0000-000000000001';
const tables={grinder_practice_versions:[{id:practice,owner_id:owner,title:'Check the changed behavior',task_context:'Small bug fixes',instruction:'Run the named test before claiming it passed.',expected:'A specific result tied to the change.',visibility:'public',harness:'Codex'}],
grinder_practice_attempts:[
  {id:'30000000-0000-0000-0000-000000000001',owner_id:'different-person',practice_id:practice,visibility:'shared',baseline:{measurement_revision:'a'.repeat(64),turns_typed:8,claims_verified:2,artifacts_produced:3,duration_s:600,harness:'Codex',trace_basis:'elapsed'},outcome:{measurement_revision:'b'.repeat(64),turns_typed:6,claims_verified:1,artifacts_produced:2,duration_s:700,harness:'Codex',trace_basis:'elapsed'},decision:'change',note:'The task changed too; this does not isolate the effect.',reviewed_at:'2026-09-04T10:00:00Z'},
  {id:'30000000-0000-0000-0000-000000000002',owner_id:'different-person',practice_id:practice,visibility:'shared',baseline:{measurement_revision:'c'.repeat(64),turns_typed:8,claims_verified:2,artifacts_produced:3,duration_s:600,harness:'Claude Code',trace_basis:'elapsed'},outcome:{measurement_revision:'d'.repeat(64),turns_typed:6,claims_verified:3,artifacts_produced:2,duration_s:700,harness:'Cursor',trace_basis:'elapsed'},decision:'incomparable',note:'Different harnesses. Claim counts are present on both sittings and still do not compare.',reviewed_at:'2026-09-05T10:00:00Z'}
],
runs:[{id:'40000000-0000-0000-0000-000000000001',profile_id:owner,title:'Fixture baseline',measurement_revision:'c'.repeat(64)}],grinder_memberships:[]};
const client={from(name){let filters=[],verb='read',payload;const q={select(){return q},eq(k,v){filters.push(r=>r[k]===v);return q},in(k,values){filters.push(r=>values.includes(r[k]));return q},not(){return q},order(){return q},limit(){return q},insert(v){verb='insert';payload=v;return q},then(resolve,reject){let rows=tables[name]||[];if(verb==='insert'){payload={id:'50000000-0000-0000-0000-000000000001',...payload};rows.push(payload);tables[name]=rows;window.calls.push({name,payload});return Promise.resolve({data:[payload]}).then(resolve,reject)}return Promise.resolve({data:rows.filter(r=>filters.every(f=>f(r)))}).then(resolve,reject)}};return q},async rpc(name,payload){window.calls.push({name,payload});return {data:'60000000-0000-0000-0000-000000000001'}}};
window.fixture=GrinderPractices({client,me:()=>({id:owner}),app:()=>document.getElementById('app'),frame:()=>{},status:(text)=>document.getElementById('status').textContent=text});
'''
with sync_playwright() as p:
    launch=dict(headless=True, args=["--no-sandbox"])
    binary=os.environ.get("BRAVE_BINARY") or os.environ.get("CHROME_BIN")
    if binary:
        launch["executable_path"]=binary
    browser=p.chromium.launch(**launch)
    page=browser.new_page(viewport={'width':390,'height':844})
    failures=[]
    page.on('pageerror',lambda e:failures.append(str(e)))
    style=(ROOT/'site/design.css').read_text()+re.search(r'<style>(.*?)</style>',(ROOT/'site/index.html').read_text(),re.S).group(1)+(ROOT/'site/social.css').read_text()
    page.set_content('<style>'+style+'</style><div style="padding:12px;background:#fff3bb">UI TEST FIXTURE — no live users or results</div><div id="status"></div><main id="app"></main>')
    page.add_script_tag(content=(ROOT/'site/run-contract.js').read_text())
    page.add_script_tag(content=(ROOT/'site/practice-eligibility.js').read_text())
    page.add_script_tag(content=(ROOT/'site/practices.js').read_text())
    page.add_script_tag(content=setup)
    page.evaluate('fixture.index()')
    page.get_by_label('Find by task, practice or harness').fill('Codex')
    page.get_by_role('button',name='Find practices',exact=True).click()
    assert page.get_by_role('link',name='Check the changed behavior').count()==1
    page.get_by_label('Find by task, practice or harness').fill('no match')
    page.get_by_role('button',name='Find practices',exact=True).click()
    page.get_by_text('No matching practices yet.',exact=True).wait_for()
    page.evaluate("fixture.detail('20000000-0000-0000-0000-000000000001')")
    page.get_by_text('Frozen baseline',exact=True).first.wait_for()
    assert page.get_by_role('heading', name='Comparable under the same measurements').count()==1
    assert page.get_by_role('heading', name='Read these as two separate sittings').count()==1
    assert 'Harness differs' in page.content() or 'not the same measurement' in page.content()
    page.screenshot(path='/tmp/grinder-comparable-badge-phone.png', full_page=True)
    assert page.get_by_text('change',exact=True).count()==1
    page.get_by_label('Share my baseline counts',exact=False).check()
    page.get_by_role('button',name='Start attempt',exact=True).click()
    page.wait_for_timeout(100)
    calls=page.evaluate('calls')
    assert calls[-1]['name']=='grinder_start_attempt'
    assert calls[-1]['payload']['share'] is True
    assert calls[-1]['payload']['baseline_run']=='40000000-0000-0000-0000-000000000001'
    assert not failures,failures
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    page.screenshot(path='/tmp/grinder-practice-fixture-mobile.png',full_page=True)
    page.set_viewport_size({'width':1280,'height':900})
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    page.add_script_tag(content=(ROOT/'site/challenges.js').read_text())
    page.evaluate("""() => {
      tables.grinder_challenges=[{id:'event-fixture',owner_id:'someone-else',name:'OCTACON UI fixture',kind:'octacon',capacity:8,closes_at:'2030-01-01T00:00:00Z',contract:{task:'One declared fixture task',checks:['Run the fixture check']}}];
      tables.grinder_challenge_entries=[{id:'entry-a',owner_id:'owner-a',challenge_id:'event-fixture',crew_name:'Fixture Crew A',rig_revision:'rig-a'},{id:'entry-b',owner_id:'owner-b',challenge_id:'event-fixture',crew_name:'Fixture Crew B',rig_revision:'rig-b'}];
      tables.grinder_challenge_submissions=[];
      window.eventView=GrinderChallenges({client,me:()=>null,app:()=>document.getElementById('app'),frame:()=>{},status:text=>{window.fixtureStatus=text}});
    }""")
    page.set_viewport_size({'width':390,'height':844})
    page.evaluate("eventView.show('event-fixture')")
    assert not page.evaluate('window.fixtureStatus'),page.evaluate('window.fixtureStatus')
    page.get_by_text('2 of 8 Crews entered',exact=True).wait_for(timeout=3000)
    assert page.locator('.octacon-place').count()==8
    assert page.get_by_text('Open place',exact=True).count()==6
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert not failures,failures
    page.screenshot(path='/tmp/grinder-octacon-fixture-mobile.png',full_page=True)
    auth=browser.new_page(viewport={'width':390,'height':844})
    auth.route('**/*',lambda route:route.fulfill(status=200,content_type='text/html',body='<main>AUTH UI FIXTURE — no email or OAuth request is sent</main>'))
    auth.goto('https://grinder-fixture.test/#import=eyJ0dXJuc190eXBlZCI6Mn0=')
    html=(ROOT/'site/index.html').read_text()
    signin=html[html.index('function showSignIn(){'):html.index('async function refreshAuth()')]
    stash=html[html.index('const IMPORT_STASH='):html.index('function importRun(){')]
    auth.add_script_tag(content="const $=id=>document.getElementById(id);const status=text=>{window.lastStatus=text};window.authCalls=[];const sb={auth:{async signInWithOAuth(payload){authCalls.push(payload);return {error:null}},async signInWithOtp(payload){authCalls.push(payload);return {error:null}}}};"+stash+signin)
    auth.evaluate('showSignIn()')
    auth.get_by_role('button',name='Continue with GitHub',exact=True).click()
    assert auth.evaluate("sessionStorage.getItem('ag_import')")=='eyJ0dXJuc190eXBlZCI6Mn0='
    assert auth.evaluate('authCalls[0].options.redirectTo')=='https://grinder-fixture.test/'
    auth.get_by_label('Email',exact=True).fill('fixture@example.test')
    auth.get_by_role('button',name='Send a sign-in link',exact=True).click()
    assert auth.evaluate('authCalls[1].email')=='fixture@example.test'
    auth.get_by_text('Check your email for the sign-in link.',exact=False).wait_for(timeout=3000)
    assert not auth.evaluate('document.documentElement.scrollWidth>innerWidth')
    auth.close()
    # Run the real import handler through redirect restoration, server failure and success.
    imported=browser.new_page(viewport={'width':390,'height':844})
    imported.route('**/*',lambda route:route.fulfill(status=200,content_type='text/html',body='<div id="status"></div><main id="app"></main>'))
    payload={'schema_version':1,'harness':'Codex','turns_typed':2,'duration_s':120,'measurement_revision':'a'*64}
    import base64,urllib.parse
    encoded=urllib.parse.quote(base64.b64encode(json.dumps(payload).encode()).decode(),safe='')
    imported.goto('https://grinder-fixture.test/#import='+encoded)
    imported.add_script_tag(content=(ROOT/'site/run-contract.js').read_text())
    handler=html[html.index('function importRun(){'):html.index('async function viewShareRun(')]
    imported.add_script_tag(content=r"""
      const $=id=>document.getElementById(id),esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
      let ME=null;window.importCalls=[];window.failImport=true;
      const frame=()=>{},status=text=>{$('status').textContent=text};
      const sb={from(table){const q={insert(row){window.importCalls.push({table,row});return q},select(){return q},single(){return Promise.resolve(window.failImport?{error:{message:'Fixture backend refused schema'}}:{data:{id:'published-fixture'},error:null})},update(){return q},eq(){return Promise.resolve({error:null})}};return q}};
      function showSignIn(){stashImport(location.hash.match(/import=([^&]+)/)[1]);history.replaceState(null,'','/');$('app').innerHTML='<p>Simulated identity redirect</p>'}
      async function viewRun(id){document.getElementById('app').innerHTML='<h2>Published run '+id+'</h2>';window.openedRun=id}
    """+stash+handler)
    imported.evaluate('importRun()')
    imported.get_by_placeholder('Title (optional, you type this, not scraped)').fill('My chosen run title')
    imported.locator('#i_vis').select_option('public')
    imported.get_by_role('button',name='Sign in to publish',exact=True).click()
    imported.get_by_text('Simulated identity redirect',exact=True).wait_for()
    imported.evaluate("ME={id:'fixture-author',rig:{}};restoreImport();importRun()")
    assert imported.locator('#i_title').input_value()=='My chosen run title'
    assert imported.locator('#i_vis').input_value()=='public'
    imported.get_by_role('button',name='Publish',exact=True).click()
    imported.get_by_text('Fixture backend refused schema',exact=True).wait_for()
    assert len(imported.evaluate('importCalls'))==1 # no silent retry dropping evidence
    assert imported.get_by_role('button',name='Publish',exact=True).is_enabled()
    assert '#import=' in imported.url
    imported.evaluate('window.failImport=false')
    imported.get_by_role('button',name='Publish',exact=True).click()
    imported.get_by_role('heading',name='Published run published-fixture',exact=True).wait_for()
    assert imported.url.endswith('/?run=published-fixture')
    saved=imported.evaluate('importCalls[1].row')
    assert saved['measurement_revision']=='a'*64 and saved['title']=='My chosen run title'
    assert saved['started_at'] is None # do not invent a session timestamp on import
    # A first-time friend arriving at a run must stay there, even with no runs of their own.
    routing=html[html.index('async function route(){'):html.index("document.addEventListener('DOMContentLoaded'")]
    imported.add_script_tag(content="const account={recover(){}};const social={};async function shouldOnboard(){return true};async function viewOnboard(){window.wrongOnboard=true};"+routing)
    imported.evaluate('route()')
    assert imported.evaluate('window.openedRun')=='published-fixture'
    assert not imported.evaluate('window.wrongOnboard')
    imported.close()
    profile=browser.new_page()
    profile.set_content('<div id="me"></div><button id="auth"></button><div id="deletewrap"></div><div id="mobile-product-nav"></div><p id="status"></p>')
    refresh=html[html.index('async function refreshAuth(){'):html.index('// The publish payload')]
    profile.add_script_tag(content=r"""
      const $=id=>document.getElementById(id),esc=s=>String(s),status=(text)=>$('status').textContent=text;
      function syncAuthNav(){}
      let ME=null;window.createdProfiles=0;window.existingProfile={id:'profile-fixture',auth_uid:'auth-fixture',github_handle:'chosen-handle',name:'Chosen name'};
      const sb={auth:{async getSession(){return {data:{session:{user:{id:'auth-fixture',user_metadata:{user_name:'provider-handle'}}}}}}},
        from(){const q={select(){return q},eq(){return q},async maybeSingle(){return {data:window.existingProfile,error:null}},insert(row){window.createdProfiles++;window.existingProfile={id:'profile-fixture',...row};return q},async single(){return {data:window.existingProfile,error:null}}};return q}};
    """+refresh)
    profile.evaluate('refreshAuth()')
    assert profile.evaluate('createdProfiles')==0
    assert profile.get_by_role('link',name='@chosen-handle').count()==1
    profile.evaluate('existingProfile=null;refreshAuth()')
    assert profile.evaluate('createdProfiles')==1
    assert profile.get_by_role('link',name='@provider-handle').count()==1
    profile.close()

    # Auth's initial session and SIGNED_IN must not interleave page rendering.
    race=browser.new_page()
    race.set_content('<main id="app"></main><button id="auth"></button><button id="delete"></button>')
    bootstrap=html[html.index("document.addEventListener('DOMContentLoaded'"):html.index('</script>',html.index("document.addEventListener('DOMContentLoaded'"))]
    race.add_script_tag(content=r"""
      const $=id=>document.getElementById(id),skeletonCard=()=>'',status=()=>{};
      let ME=null;window.activeRenders=0;window.maxRenders=0;window.completedRenders=0;
      const sb={auth:{onAuthStateChange(callback){callback('SIGNED_IN',{user:{id:'race-user'}})}}};
      async function refreshAuth(){await new Promise(resolve=>setTimeout(resolve,20));ME={auth_uid:'race-user'}}
      async function route(){activeRenders++;maxRenders=Math.max(maxRenders,activeRenders);await new Promise(resolve=>setTimeout(resolve,40));activeRenders--;completedRenders++}
    """+bootstrap)
    race.evaluate("document.dispatchEvent(new Event('DOMContentLoaded'))")
    race.wait_for_function('completedRenders===2')
    assert race.evaluate('maxRenders')==1
    race.close()

    print(json.dumps({'fixture':'practice discovery, failed search, before/after, explicit shared attempt','mobile_and_desktop':True,'javascript_errors':failures,'writes':calls}))
    browser.close()
