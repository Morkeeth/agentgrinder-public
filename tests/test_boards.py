"""Marathon, weekly boards and the profile heatmap: public runs only, one time rule (25 Sep 2026)."""
from pathlib import Path

INDEX = (Path(__file__).resolve().parents[1] / "site/index.html").read_text()
PRODUCT = (Path(__file__).resolve().parents[1] / "PRODUCT.md").read_text()


def test_boards_read_public_runs_only_and_use_the_card_time_rule():
    boards = INDEX[INDEX.index("async function viewBoards()") : INDEX.index("function heatmapSvg(")]
    assert boards.count(".eq('visibility','public')") == 2
    assert "const runSeconds=r=>{const v=r.wall_time_s??r.duration_s;" in INDEX
    assert "const MARATHON_SECS=3*3600;" in INDEX
    assert "GrinderFeed.ghost(r)" in boards  # the feed card's own ghost rule, not a second one
    assert "(r.files_touched===0)||(r.files_touched==null&&r.commits===0)" in boards
    assert "r.files_touched===0?'0 files changed':'0 commits'" in boards
    assert "GrinderContract.toolCallCount(r)" in INDEX
    assert ".order('wall_time_s',{ascending:false,nullsFirst:false})" in boards
    assert "Honest failure of the week" in boards
    # Empty lanes say so. No sample, no placeholder row.
    for empty in ("No ghost run this week yet", "No public run with tool calls this week yet", "No run with zero files changed this week", "No public run of 3 hours or more yet"):
        assert empty in boards
    assert "weekStart(" in boards and "d.getDate()-((d.getDay()+6)%7)" in INDEX


def test_boards_are_routed_and_in_the_menu():
    assert "if(q.has('boards'))return viewBoards();" in INDEX
    assert "['/?boards','Marathon and boards']" in INDEX
    assert 'href="/?boards">Marathon and boards</a>' in INDEX


def test_profile_carries_a_heatmap_of_visible_runs():
    assert "${heatmapSvg(R)}" in INDEX
    heat = INDEX[INDEX.index("function heatmapSvg(") : INDEX.index("// PROJECTS (25 Sep 2026)")]
    assert "runStart(r)" in heat and "52 weeks" in heat
    assert 'role="img"' in heat and "<title>" in heat


def test_product_states_the_rules():
    assert "Time on a run is `wall_time_s` when measured, else `duration_s`" in PRODUCT
    assert "A Marathon is a public run of 3 hours or more" in PRODUCT
