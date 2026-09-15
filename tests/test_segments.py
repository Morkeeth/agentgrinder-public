"""Contracts for the fixed-task public segment."""
from pathlib import Path
import json
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_ranking_shares_places_for_equal_wall_time_and_tool_calls():
    runs = [
        {"id": "later", "wall_time_s": 70, "tool_calls": 2},
        {"id": "tie-b", "wall_time_s": 45, "tool_calls": 3},
        {"id": "tie-a", "wall_time_s": 45, "tool_calls": 3},
        {"id": "more-tools", "wall_time_s": 45, "tool_calls": 5},
    ]
    script = """
const {rankRuns}=require(process.argv[1]);
const ranked=rankRuns(JSON.parse(process.argv[2]));
process.stdout.write(JSON.stringify(ranked.map(run=>[run.id,run.rank])));
"""
    result = subprocess.run(
        ["node", "-e", script, str(ROOT / "site/segments.js"), json.dumps(runs)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == [
        ["tie-a", 1],
        ["tie-b", 1],
        ["more-tools", 3],
        ["later", 4],
    ]


def test_segment_page_renders_three_labelled_fixture_runs():
    pytest.importorskip("playwright")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/check-segment-fixtures.py")],
        cwd=ROOT,
        check=True,
    )


def test_segment_schema_stays_in_strava_and_public_reads_are_filtered():
    migration = (ROOT / "supabase/strava/001_segments.sql").read_text()
    page = (ROOT / "site/segments.js").read_text()
    index = (ROOT / "site/index.html").read_text()
    assert "strava.segments" in migration
    assert "strava.runs" in migration
    assert "wall_time_s" in migration
    assert "public." not in migration
    assert '.eq("visibility", "public")' in page
    assert "This run was on segment:" in page
    assert "segment_id:$('f_segment').value||null" in index
    assert "segment_id:$('i_segment').value||null" in index
    assert "wall_time_s:wallTime" in index
    assert index.count("dropNullSegmentColumns(") == 3, "both run inserts omit unset segment columns"
