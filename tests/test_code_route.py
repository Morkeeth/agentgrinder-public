"""Code Route: multi-project journey card, privacy bounds, and cross-harness honesty."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agentgrinder.agent_api import RUN_FIELDS, run_payload
from agentgrinder.code_route import (
    compact_from_checkpoints,
    from_manifest,
    public_code_route,
    validate_code_route,
)
from agentgrinder.push import export_run

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"
MULTI = FIXTURES / "code_route_multi_project_manifest.json"
MISS = FIXTURES / "code_route_collector_miss_manifest.json"


def multi_route():
    return from_manifest(json.loads(MULTI.read_text()))


def render_card(run: dict) -> str:
    script = r"""
const fs=require('fs'),vm=require('vm');
const root=process.argv[1];
const html=fs.readFileSync(root+'/site/index.html','utf8');
const start=html.indexOf('function connectWrapperName(');
const end=html.indexOf('function wireKudos(');
const fn=html.slice(start,end);
const GrinderContract=require(root+'/site/run-contract.js');
const context={GrinderContract,ME:null,
 esc:s=>String(s??'').replace(/[<>&"']/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&#39;'}[c])),
 fmtDur:m=>!m?'-':(m>=60?`${Math.floor(m/60)}h ${m%60}m`:`${m}m`),
 runAttribution:()=>({handle:'sample',name:'Sample',link:null}),avatar:()=>'',safeOutputUrl:v=>v||null,
 ackPickerHtml:()=>'',suggestAckReasons:()=>[],fiveRow:()=>'',coachBlock:()=>''};
vm.createContext(context);vm.runInContext(fn,context);
const run=JSON.parse(process.argv[2]);
process.stdout.write(vm.runInContext('runCard('+JSON.stringify(run)+',false,0)',context));
"""
    result = subprocess.run(
        ["node", "-e", script, str(ROOT), json.dumps(run)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_multi_project_manifest_builds_three_lanes_and_ordered_stops():
    route = multi_route()
    assert len(route["projects"]) >= 3
    assert [p["label"] for p in route["projects"]] == [
        "zup",
        "agentgrinder-public",
        "mountain-of-helicon",
    ]
    assert [s["id"] for s in route["stops"]] == [
        "zup-edit",
        "zup-commit",
        "strive-edit",
        "strive-check",
        "strive-merge",
        "helicon-edit",
        "helicon-artifact",
    ]
    assert route["harnesses"]["observed"] == ["cursor", "claude-cli", "codex"]
    assert route["harnesses"]["absent"] == ["grok-bot"]
    assert route["harnesses"]["basis"] == "manifest"


def test_fixture_card_renders_lanes_checkpoints_and_basis_in_accessible_text():
    run = {
        "id": "r-code-route",
        "profile_id": "p1",
        "created_at": "2026-09-20T12:00:00Z",
        "title": "Multi-project night",
        "started_at": "2026-09-20T10:00:00Z",
        "project": "agentgrinder-public",
        "harness": "Cursor + Claude CLI + Codex",
        "commits": 1,
        "files_touched": 10,
        "code_route": multi_route(),
    }
    html = render_card(run)
    assert "code-route" in html
    assert "Trace unavailable" not in html
    text = html
    for name in ("zup", "agentgrinder-public", "mountain-of-helicon"):
        assert name in text
    assert "code-route-projects" in text
    assert "code-route-project-name" in text
    assert "…" not in text  # phone layout must not ellipsize lane names
    assert "measured" in text and "declared" in text
    assert "Projects touched" in text or "projects touched" in text.lower()
    assert "cursor" in text and "claude-cli" in text and "codex" in text
    assert "grok-bot" in text
    assert "observed" in text.lower() and "absent" in text.lower()
    assert "aria-label" in text


def test_single_project_compact_route_or_honest_unavailable():
    ok = compact_from_checkpoints(
        project_label="agentgrinder-public",
        commits=4,
        files_changed=10,
        receipts=3,
        artifact=True,
    )
    assert ok["projects"][0]["label"] == "agentgrinder-public"
    assert any(s["kind"] == "commit" for s in ok["stops"])
    assert ok["finish"]["kind"] == "artifact"
    missing = compact_from_checkpoints(project_label="agentgrinder-public")
    assert "unavailable" in missing
    assert "No checkpoint evidence" in missing["unavailable"]["why"]


def test_collector_miss_names_absent_harness_populations():
    route = from_manifest(json.loads(MISS.read_text()))
    assert "unavailable" in route
    assert route["harnesses"]["observed"] == []
    assert set(route["harnesses"]["absent"]) >= {"cursor", "claude-cli", "codex"}
    assert route["harnesses"]["basis"] == "collector"


def test_code_route_survives_export_and_run_payload():
    run = {"turns_typed": 2, "schema_version": 1, "code_route": multi_route()}
    assert "code_route" in RUN_FIELDS
    for prepared in (export_run(run), run_payload(run)):
        assert prepared["code_route"] == multi_route()


def test_privacy_rejects_paths_prompts_secrets_unknown_keys_and_oversize():
    base = multi_route()
    with pytest.raises(ValueError, match="path"):
        validate_code_route(
            {
                **base,
                "projects": [
                    {"id": "zup", "label": "/Users/me/CODE/secret", "basis": "measured"},
                    base["projects"][1],
                    base["projects"][2],
                ],
            }
        )
    bad_stops = [dict(stop) for stop in base["stops"]]
    bad_stops[0] = {
        **bad_stops[0],
        "evidence": ["~/.claude/projects/x"],
    }
    with pytest.raises(ValueError, match="path|home"):
        validate_code_route({**base, "stops": bad_stops})
    bad_label = [dict(stop) for stop in base["stops"]]
    bad_label[0] = {**bad_label[0], "label": "api_key leaked"}
    with pytest.raises(ValueError, match="secret|prompt|private lane"):
        validate_code_route({**base, "stops": bad_label})
    with pytest.raises(ValueError, match="Unknown"):
        validate_code_route({**base, "prompt": "PRIVATE"})
    with pytest.raises(ValueError, match="at most|holds"):
        validate_code_route(
            {
                **base,
                "stops": base["stops"]
                + [
                    {
                        "id": f"extra-{i}",
                        "project": "zup",
                        "kind": "edit",
                        "label": f"extra {i}",
                        "basis": "measured",
                    }
                    for i in range(40)
                ],
            }
        )


def test_redaction_rejects_private_lane_labels():
    with pytest.raises(ValueError):
        validate_code_route(
            {
                "v": 1,
                "projects": [{"id": "p1", "label": "L12 PRIVATE LANE", "basis": "measured"}],
                "stops": [
                    {
                        "id": "s1",
                        "project": "p1",
                        "kind": "edit",
                        "label": "work",
                        "basis": "measured",
                    }
                ],
                "finish": {"stop": "s1", "kind": "unfinished", "label": "work"},
                "stats": {
                    "projects_touched": 1,
                    "commits": 0,
                    "files_changed": 0,
                    "verified_checkpoints": 1,
                    "shipped_artifacts": 0,
                },
            }
        )
    # Public repo names may travel when explicitly included; private lane tokens may not.
    public = public_code_route({"code_route": multi_route()})
    text = json.dumps(public)
    assert "L12" not in text and "PRIVATE" not in text
    assert "agentgrinder-public" in text


def test_legacy_rhythm_and_ridge_cards_still_render():
    rhythm = render_card(
        {
            "id": "r1",
            "profile_id": "p1",
            "created_at": "2026-09-20T12:00:00Z",
            "title": "Legacy rhythm",
            "started_at": "2026-09-20T10:00:00Z",
            "rhythm": [1, 2, 1, 3],
            "trace_basis": "elapsed",
        }
    )
    assert "run-signature" in rhythm and "Trace unavailable" not in rhythm
    ridge = [i % 5 for i in range(50)]
    workers = [0] * 50
    shaped = render_card(
        {
            "id": "r2",
            "profile_id": "p1",
            "created_at": "2026-09-20T12:00:00Z",
            "title": "Legacy ridge",
            "started_at": "2026-09-20T10:00:00Z",
            "ridge": ridge,
            "worker_bins": workers,
            "ridge_basis": "wall-time",
            "ridge_wall_seconds": 600,
        }
    )
    assert "ridge-wrap" in shaped
