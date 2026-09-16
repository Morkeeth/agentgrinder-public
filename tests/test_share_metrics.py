"""Share cards use the same honest session strip as the browser card."""
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = r"""
import fs from 'node:fs';
import vm from 'node:vm';
import {card} from './server/public-run.mjs';

const context={window:{}};
vm.runInNewContext(fs.readFileSync('./site/sharing.js','utf8'),context);
const strip=context.window.GrinderSharing.metricStrip;
const base={id:'r1',title:'A real run',visibility:'public',profiles:{handle:'sample'}};
const zero={...base,duration_s:0,prompts:0,tool_calls:0,files_touched:0,commits:0};
const unknown={...base,duration_s:null,prompts:null,tool_calls:null,files_touched:null,commits:null};
const text=node=>{
  if(node==null)return[];
  if(typeof node==='string'||typeof node==='number')return[String(node)];
  const children=node.props&&node.props.children;
  return Array.isArray(children)?children.flatMap(text):text(children);
};
process.stdout.write(JSON.stringify({
  zero:strip(zero),
  unknown:strip(unknown),
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
        ["Files", "0"],
        ["Commits", "0"],
    ]
    assert [value for _, value in result["unknown"]] == ["Unknown"] * 5


def test_public_link_preview_preserves_zero_and_unknown():
    result = render()
    assert result["ogZero"].count("0") == 4
    assert "0s" in result["ogZero"]
    assert result["ogUnknown"].count("Unknown") == 5
