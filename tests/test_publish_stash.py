"""GitHub sign-in must not destroy the run it was called to publish.

The defect this file pins (code-verified 3 Sep 2026): the publish payload lives entirely in the
URL fragment, `#import=<base64>`. The sign-in button on that page called
`signInWithOAuth({redirectTo: location.href})` and stashed nothing. RFC 6749 3.1.2 forbids a
fragment in an OAuth `redirect_uri` and providers drop it, so the user came back signed in, on an
empty profile, with the run gone — the one hop in the whole funnel where a stranger loses work.

Two tests over the strings, and one that actually runs the two functions under node when node is
on the machine, so the round trip is measured and not just read.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = open(os.path.join(REPO, "site", "index.html"), encoding="utf-8").read()


def test_the_payload_is_stashed_before_the_redirect_and_the_fragment_is_not_the_redirect_uri():
    body = HTML[HTML.index("async function importRun(){"):]
    body = body[:body.index("\nasync function viewShareRun(")]
    assert "stashImport(m[1]);" in body
    i_stash = body.index("stashImport(m[1])")
    i_dialog = body.index("showSignIn()", i_stash)
    assert i_stash < i_dialog, "the stash must be written before opening sign-in"
    signin=HTML[HTML.index("function showSignIn(){"):HTML.index("async function refreshAuth()") ]
    assert signin.index("stashImport") < signin.index("auth.signIn")
    # a fragment cannot come back through OAuth, so it must not be what we ask to come back to.
    # Comment lines are dropped first: the comment above the fix quotes the old call by name.
    code = "".join(l for l in (body+signin).splitlines() if not l.lstrip().startswith("//"))
    assert "redirectTo:location.href" not in code.replace(" ", "")
    assert "GrinderAuth.create({client:sb,redirectTo:location.origin+'/'}" in HTML.replace(" ", "")


def test_route_restores_the_payload_before_it_reads_the_hash():
    route = HTML[HTML.index("async function route(){"):]
    route = route[:route.index("\ndocument.addEventListener('DOMContentLoaded'")]
    assert route.index("restoreImport()") < route.index("importRun()")


def _js_block() -> str:
    start = HTML.index("const IMPORT_STASH=")
    end = HTML.index("async function importRun(){", start)
    return HTML[start:end]


@pytest.mark.skipif(not shutil.which("node"), reason="node is not on this machine")
def test_a_payload_stashed_before_oauth_is_on_the_url_when_route_runs_and_again_on_the_second_pass():
    """route() fires twice after a redirect (refreshAuth, then onAuthStateChange). Both must find it."""
    harness = _js_block() + r"""
const store={};
globalThis.sessionStorage={getItem:k=>(k in store?store[k]:null),setItem:(k,v)=>{store[k]=String(v)},removeItem:k=>{delete store[k]}};
globalThis.location={hash:'',pathname:'/'};
globalThis.history={replaceState:(a,b,url)=>{const i=url.indexOf('#');location.hash=i<0?'':url.slice(i);}};

const payload='eyJoYXJuZXNzIjoiQ2xhdWRlIn0';
stashImport(payload);                 // the publish page, one click before GitHub
location.hash='';                     // the provider drops the fragment on the way back
restoreImport();                      // pass 1: refreshAuth().then(route)
const first=location.hash;
restoreImport();                      // pass 2: onAuthStateChange().then(route)
const second=location.hash;
console.log(JSON.stringify({first,second,stashLeft:sessionStorage.getItem('ag_import')}));
"""
    out = subprocess.run(["node", "-e", harness], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    got = json.loads(out.stdout.strip().splitlines()[-1])
    assert got["first"] == "#import=eyJoYXJuZXNzIjoiQ2xhdWRlIn0"
    assert got["second"] == got["first"], "the second route() pass lost the run"
    assert got["stashLeft"] is None, "the stash must not outlive the redirect it was written for"


@pytest.mark.skipif(not shutil.which("node"), reason="node is not on this machine")
def test_an_empty_stash_leaves_the_url_alone():
    """No false restore: a normal visit with nothing stashed must not grow a fragment."""
    harness = _js_block() + r"""
const store={};
globalThis.sessionStorage={getItem:k=>(k in store?store[k]:null),setItem:(k,v)=>{store[k]=String(v)},removeItem:k=>{delete store[k]}};
globalThis.location={hash:'',pathname:'/'};
globalThis.history={replaceState:(a,b,url)=>{const i=url.indexOf('#');location.hash=i<0?'':url.slice(i);}};
restoreImport();
console.log(JSON.stringify({hash:location.hash}));
"""
    out = subprocess.run(["node", "-e", harness], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout.strip().splitlines()[-1])["hash"] == ""


@pytest.mark.skipif(not shutil.which("node"), reason="node is not on this machine")
def test_auth_module_preserves_draft_and_uses_fragment_free_redirect_for_each_provider():
    harness = "const GrinderAuth=require(" + json.dumps(os.path.join(REPO, "site", "auth.js")) + ");\n" + _js_block() + r"""
const store={};
globalThis.sessionStorage={getItem:k=>store[k]??null,setItem:(k,v)=>store[k]=String(v),removeItem:k=>delete store[k]};
globalThis.location={origin:'https://strava.example',hash:'#import=private-payload',search:'?post'};
const calls=[];
const client={from(){throw Error('Sign-in must not publish or create a profile');},auth:{
 signInWithOAuth:async request=>{calls.push({request,stash:store.ag_import,returnTo:store.ag_auth_return});return {error:null};},
 signInWithOtp:async request=>{calls.push({request,stash:store.ag_import,returnTo:store.ag_auth_return});return {error:null};}
}};
const auth=GrinderAuth.create({client,redirectTo:location.origin+'/'});
(async()=>{
 for(const provider of ['github','x','email']){
   stashImport('private-payload');
   await auth.signIn(provider,{email:'fixture@example.test',returnTo:location.search});
 }
 console.log(JSON.stringify(calls));
})().catch(e=>{console.error(e);process.exit(1)});
"""
    out = subprocess.run(["node", "-e", harness], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    calls = json.loads(out.stdout)
    assert len(calls) == 3
    for call in calls:
        assert call['stash'] == 'private-payload'
        assert call['returnTo'] == '?post'
        options = call['request']['options']
        assert options.get('redirectTo', options.get('emailRedirectTo')) == 'https://strava.example/'
