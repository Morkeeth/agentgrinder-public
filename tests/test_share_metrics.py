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
const {metricStrip:strip,storyFacts:story}=context.window.GrinderSharing;
const base={id:'r1',title:'A real run',visibility:'public',profiles:{handle:'sample'}};
const zero={...base,duration_s:0,prompts:0,tool_calls:0,files_touched:0,commits:0};
const unknown={...base,duration_s:null,prompts:null,tool_calls:null,files_touched:null,commits:null};
const rich={...base,caption:'Human caption',project:'agentgrinder-public',output_url:'https://github.com/example/repo/pull/34',
 shell_calls:4,files_touched:7,commits:2,tool_calls:22,private_title_prompt:'PRIVATE PROMPT',
 command:'PRIVATE COMMAND',path:'/private/repo/secret.py',tool_output:'PRIVATE OUTPUT'};
const generic={...base,project:'session',tool_calls:9};
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
  generic:story(generic),
  ogRich:text(card(rich)),
  ogGeneric:text(card(generic)),
  ogZero:text(card(zero)),
  ogUnknown:text(card(unknown)),
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


def test_download_share_strip_preserves_zero_and_unknown():
    result = render()
    assert result["zero"] == [
        ["Session", "0s"],
        ["Turns", "0"],
        ["Tool calls", "0"],
    ]
    assert [value for _, value in result["unknown"]] == ["Unknown"] * 3


def test_public_link_preview_preserves_zero_and_unknown():
    result = render()
    zero = " ".join(result["ogZero"])
    for value in ("0s", "0 files changed", "0 commits"):
        assert value in zero
    assert result["ogZero"].count("0") == 2
    assert result["ogUnknown"].count("Unknown") == 5


def test_share_surfaces_tell_output_project_and_code_story_without_raw_data():
    result = render()
    assert result["rich"] == {
        "project": "agentgrinder-public",
        "output": "PR linked",
        "code": "4 shell calls · 7 files changed · 2 commits",
    }
    assert result["generic"] == {
        "project": "Unknown",
        "output": None,
        "code": "9 tool calls",
    }
    joined = " ".join(result["ogRich"])
    for value in ("PR linked", "agentgrinder-public", "4 shell calls", "7 files changed", "2 commits"):
        assert value in joined
    for private in ("PRIVATE PROMPT", "PRIVATE COMMAND", "/private/", "PRIVATE OUTPUT"):
        assert private not in joined
    assert "Output" not in result["ogGeneric"]
