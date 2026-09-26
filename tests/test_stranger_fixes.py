"""Three things a stranger sees (26 Sep night): the card's share link at 390 px, sign-in docs that
match the live site, and decision stories that refuse malformed routes."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_the_share_link_is_never_cut_off_in_the_card():
    # A run address is longer than a 390 px card; nowrap clipped it (flipbook 26 Sep, screen 04).
    for path in ("site/feed.css",):
        rule = re.search(r"\.fc-where\{([^}]*)\}", (ROOT / path).read_text()).group(1)
        assert "nowrap" not in rule and "overflow-wrap:anywhere" in rule
    assert "white-space:nowrap}" not in re.search(r"\.fc-where\{[^}]*\}", (ROOT / "agentgrinder/feedcard.py").read_text()).group(0)


def test_docs_offer_only_the_sign_in_the_site_offers():
    index = (ROOT / "site/index.html").read_text()
    providers = json.loads(re.search(r"const PROVIDERS_ENABLED=(\[[^\]]*\]);", index).group(1))
    for doc in ("README.md", "PRODUCT.md"):
        text = " ".join((ROOT / doc).read_text().split())
        if "email" not in providers:
            assert "email link" not in text, f"{doc} promises email sign-in the site does not offer"
        assert re.search(r"[Ss]ign[- ]in with GitHub", text), f"{doc} no longer says how to sign in"


def test_malformed_routes_tell_no_decision_story():
    js = r"""
const m=await import('./server/decision-story.mjs');
const id='ffffffff-0000-4111-8222-333333333333';
const run=r=>({id,title:'T',code_route:{v:1,...r}});
const S=[{id:'1',project:'a',kind:'edit',label:'One',basis:'measured'},{id:'2',project:'a',kind:'edit',label:'Two',basis:'measured'},{id:'3',project:'b',kind:'edit',label:'Fin',basis:'measured'}];
const P=[{id:'a',label:'alpha'},{id:'b',label:'beta'}];
const out={
 inherited: m.hasDecisionStory(run({projects:P,stops:S,connectors:[{from:'toString',to:'3',kind:'handoff'}],finish:{stop:'3'}})),
 duplicate: m.hasDecisionStory(run({projects:[{id:'a',label:'alpha'},{id:'a',label:'beta'}],stops:S.slice(0,2),connectors:[]})),
 kindObject: m.hasDecisionStory(run({projects:P,stops:[{...S[0],kind:{}},S[2]],connectors:[]})),
 kindMissing: m.hasDecisionStory(run({projects:P,stops:[{id:'1',project:'a',label:'One',basis:'measured'},S[2]],connectors:[]})),
 good: m.hasDecisionStory(run({projects:P,stops:S,connectors:[{from:'2',to:'3',kind:'handoff'}],finish:{stop:'3'}})),
};
process.stdout.write(JSON.stringify(out));
"""
    out = json.loads(subprocess.run(["node", "--input-type=module", "-e", js], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
    assert out["good"] is True
    assert out["inherited"] is False, "a handoff from an inherited name counts"
    assert out["duplicate"] is False, "duplicate project ids are kept"
    assert out["kindObject"] is False and out["kindMissing"] is False, "a stop kind that is not a string is printed"
