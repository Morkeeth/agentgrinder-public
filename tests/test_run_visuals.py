"""The run-card components: measured or absent, one total, no names, and readable at 390px.

Every test here is a rule from the 23 September ruling, written as something that can fail:

  * a component whose data is missing is not drawn, not offered and not apologised for;
  * three views of one run print one total, and a payload whose parts disagree is refused;
  * a coloured tile carries no text, and no file name or home directory reaches public bytes;
  * nothing shouts: no all-caps string and no `text-transform:uppercase` in the components;
  * a phone can read it: every label inside 390px, checked in a real headless browser;
  * the browser and the local card draw the same pixels, which is checked by comparing them.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
from html import escape
from pathlib import Path

import pytest

from agentgrinder import filework, runviz
from agentgrinder.contract import public_components, validate_run
from agentgrinder.metrics import build_activity
from agentgrinder.push import export_run
from agentgrinder.render import render_card

ROOT = Path(__file__).resolve().parents[1]
VISUALS_JS = ROOT / "site/run-visuals.js"
CONTRACT_JS = ROOT / "site/run-contract.js"


def measured_work(**over):
    """A small, self-consistent payload shaped exactly like a real capture's."""
    work = {
        "v": 1,
        "source": "git numstat over the run's commits, and line counts at the end commit",
        "folders": [
            {"name": "agentgrinder", "files_end": 3, "lines_end": 900, "touched_files": 2,
             "lines_changed": 620, "deleted_files": 1, "deleted_lines": 120, "returns": 2},
            {"name": "tests", "files_end": 2, "lines_end": 400, "touched_files": 1,
             "lines_changed": 180, "deleted_files": 0, "deleted_lines": 0, "returns": 1},
            {"name": "docs", "files_end": 1, "lines_end": 60, "touched_files": 0,
             "lines_changed": 0, "deleted_files": 0, "deleted_lines": 0, "returns": 0},
        ],
        "files": [[0, 500, 400], [0, 300, 100], [0, 100, 0], [1, 300, 180], [1, 100, 0],
                  [2, 60, 0]],
        "files_capped": 0,
        "binary_end": 1,
        "binary_touched": 0,
        "deleted": {"files": 1, "lines": 120},
        "totals": {"files_end": 6, "files_touched": 4, "lines_end": 1360, "lines_changed": 800},
        "marks": [[0, 100], [300, 200], [900, 120], [1500, 180], [2400, 200]],
        "span_s": 2400,
        "commits": 5,
    }
    work.update(over)
    return filework.validate_file_work(work)


def test_a_run_that_measured_nothing_draws_and_offers_nothing():
    """Absence is the normal state. No empty frame, no placeholder, no option in the picker."""
    bare = {"harness": "Cursor"}
    assert runviz.available(bare) == []
    assert runviz.chosen(bare) == ""
    assert runviz.hero_html(bare) == ""
    assert runviz.components_html(bare) == ""
    for draw in (runviz.size_map_html, runviz.folder_line_html, runviz.elevation_html):
        assert draw(None) == ""
        assert draw({}) == ""


def test_each_component_is_hidden_when_its_own_data_is_absent():
    work = measured_work()
    assert runviz.size_map_html(work)
    assert runviz.size_map_html(measured_work(files=[], totals={
        "files_end": 0, "files_touched": 4, "lines_end": 0, "lines_changed": 800})) == ""
    untouched = [dict(folder, lines_changed=0, deleted_files=0, deleted_lines=0, touched_files=0)
                 for folder in work["folders"]]
    quiet = measured_work(folders=untouched, files=[[0, 500, 0], [0, 300, 0], [0, 100, 0],
                                                    [1, 300, 0], [1, 100, 0], [2, 60, 0]],
                          deleted={"files": 0, "lines": 0}, marks=[],
                          totals={"files_end": 6, "files_touched": 0, "lines_end": 1360,
                                  "lines_changed": 0})
    assert runviz.folder_line_html(quiet) == ""
    assert runviz.elevation_html(quiet) == ""
    assert runviz.screenshot_html({}) == ""
    assert runviz.gear_chip_html({"gear": {}}) == ""
    assert runviz.quote_html({"quote": None}) == ""
    assert runviz.trophies_html({"trophies": []}) == ""


def test_the_elevation_needs_five_points_over_ten_minutes():
    """Four dots and a guess is not a profile, and nine minutes is not a run against a clock."""
    assert filework.has_elevation(measured_work())
    few = measured_work(marks=[[0, 400], [600, 200], [1200, 200]], span_s=1200,
                        totals={"files_end": 6, "files_touched": 4, "lines_end": 1360,
                                "lines_changed": 800})
    assert not filework.has_elevation(few)
    assert runviz.elevation_html(few) == ""
    assert "elevation" not in runviz.available({"file_work": few})
    brief = measured_work(marks=[[0, 100], [60, 200], [120, 120], [180, 180], [240, 200]],
                         span_s=240)
    assert not filework.has_elevation(brief)


def test_the_author_chooses_and_a_choice_without_data_is_not_honoured():
    work = measured_work()
    run = {"file_work": work, "ridge": [1] * 50}
    assert runviz.available(run) == ["size-map", "folder-line", "elevation", "ridge"]
    assert runviz.chosen(run) == "size-map"          # the default when file data exists
    assert runviz.chosen(dict(run, hero_visual="elevation")) == "elevation"
    assert runviz.chosen(dict(run, hero_visual="screenshot")) == "size-map"
    assert runviz.chosen({"ridge": [1] * 50}) == "ridge"
    with_image = {"image_url": "https://example.com/shot.png", "ridge": [1] * 50}
    assert runviz.available(with_image) == ["screenshot", "ridge"]
    assert runviz.chosen(with_image) == "ridge"      # no default, so the card keeps what it had
    assert 'data-visual="screenshot"' in runviz.hero_html(
        dict(with_image, hero_visual="screenshot"))


def test_every_view_of_one_run_states_the_same_total_and_its_source():
    work = measured_work()
    total = f"{work['totals']['lines_changed']:,} lines changed"
    views = [runviz.size_map_html(work), runviz.folder_line_html(work),
             runviz.elevation_html(work)]
    for view in views:
        assert total in view, view[:200]
        assert escape(work["source"]) in view
    # And the elevation climbs to exactly that total rather than to a fourth number.
    assert sum(mark[1] for mark in work["marks"]) == work["totals"]["lines_changed"]
    # The size map cannot draw a file that no longer exists, so the difference is a sentence.
    assert "Also deleted: 1 file, 120 lines." in views[0]
    drawn = sum(row[2] for row in work["files"])
    assert drawn + work["deleted"]["lines"] == work["totals"]["lines_changed"]


@pytest.mark.parametrize("break_it", [
    {"totals": {"files_end": 6, "files_touched": 4, "lines_end": 1360, "lines_changed": 799}},
    {"deleted": {"files": 1, "lines": 119}},
    {"marks": [[0, 100], [300, 200], [900, 120], [1500, 180], [2400, 201]]},
    {"files": [[0, 500, 400], [0, 300, 100], [0, 100, 0], [1, 300, 180], [1, 100, 0]]},
])
def test_a_payload_whose_parts_do_not_add_up_is_refused(break_it):
    """Three views that disagree are three claims. The boundary refuses before anything is drawn."""
    with pytest.raises(ValueError):
        measured_work(**break_it)


def test_a_coloured_tile_carries_no_text():
    """A treemap label is unreadable at 390px and a file name is private. The legend has the words."""
    svg, drawn, _tiny = runviz.size_map_svg(measured_work())
    assert drawn == 6
    assert "<text" not in svg and "</text>" not in svg
    assert svg.count("<rect") == 6
    # The words are underneath, in the legend, with the folder names and the totals.
    legend = runviz.size_map_html(measured_work()).split("</svg>", 1)[1]
    assert "agentgrinder" in legend and "Untouched" in legend and "200 or more" in legend


def test_the_keyed_ramp_is_the_ruling_and_both_surfaces_carry_it():
    ramp = measured_work(files=[[0, 500, 400], [0, 300, 60], [0, 100, 10], [1, 300, 180],
                               [1, 100, 30], [2, 60, 0]],
                         folders=[
                             {"name": "agentgrinder", "files_end": 3, "lines_end": 900,
                              "touched_files": 3, "lines_changed": 590, "deleted_files": 1,
                              "deleted_lines": 120, "returns": 2},
                             {"name": "tests", "files_end": 2, "lines_end": 400,
                              "touched_files": 2, "lines_changed": 210, "deleted_files": 0,
                              "deleted_lines": 0, "returns": 1},
                             {"name": "docs", "files_end": 1, "lines_end": 60,
                              "touched_files": 0, "lines_changed": 0, "deleted_files": 0,
                              "deleted_lines": 0, "returns": 0}],
                         totals={"files_end": 6, "files_touched": 6, "lines_end": 1360,
                                 "lines_changed": 800})
    svg, _drawn, _tiny = runviz.size_map_svg(ramp)
    for name in ("pc-t0", "pc-t1", "pc-t2", "pc-t3"):
        assert f'class="{name}"' in svg
    css = (ROOT / "site/design.css").read_text()
    for name, colour in (("pc-t0", "#EEF0F3"), ("pc-t1", "#FFD8C4"), ("pc-t2", "#FF9A6B"),
                         ("pc-t3", "#FC4C02")):
        assert f"{name}{{fill:{colour}}}" in runviz.CSS.replace(" ", "").replace("\n", "")
        assert f"{name}{{fill:{colour}}}" in css.replace(" ", "").replace("\n", "")


def test_nothing_shouts():
    """Sentence case, never all caps — in the components' own styles and in what they accept."""
    for sheet in (runviz.CSS, (ROOT / "site/design.css").read_text()):
        block = sheet[sheet.index(".pc-visual"):] if ".pc-visual" in sheet else ""
        assert "text-transform:uppercase" not in block.replace(" ", "")
    work = measured_work()
    words = re.findall(r"[A-Za-z]{4,}", re.sub(r"<[^>]+>", " ", runviz.size_map_html(work)))
    assert words and not [word for word in words if word.isupper()]
    with pytest.raises(ValueError):
        public_components({"trophies": [{"id": "longest-run", "label": "LONGEST RUN",
                                        "value": "2h 41m", "basis": "Longest captured run"}]})
    with pytest.raises(ValueError):
        public_components({"quote": {"text": "THIS RUN WAS ENORMOUS", "chosen_by": "author"}})


def test_the_quote_is_the_authors_or_it_does_not_exist():
    """PRODUCT.md, line 21: never read out of a transcript. No parser in the package writes it."""
    with pytest.raises(ValueError):
        public_components({"quote": {"text": "Looks good to me", "chosen_by": "parser"}})
    with pytest.raises(ValueError):
        public_components({"quote": {"text": "Looks good to me"}})
    chosen = public_components({"quote": {"text": "The map found folders I forgot.",
                                          "chosen_by": "author"}})
    assert chosen["quote"] == {"text": "The map found folders I forgot.", "chosen_by": "author"}
    # NO PARSER WRITES IT. Every module that reads a transcript, a store or a capture database is
    # checked for an assignment to the field; the only writer in the package is the CLI flag the
    # author types, and the only reader is the contract that validates it.
    readers = ["ingest.py", "solo.py", "capture.py", "cursor_chats.py", "cursor_tree.py",
               "native_sittings.py", "fleet.py", "hook.py", "gear.py", "filework.py",
               "runviz.py", "metrics.py", "push.py", "automated_capture.py"]
    for name in readers:
        source = (ROOT / "agentgrinder" / name).read_text()
        assert not re.search(r"""\[\s*["']quote["']\s*\]\s*=""", source), name
    assert re.search(r"""run\["quote"\]\s*=""", (ROOT / "agentgrinder/cli.py").read_text())


def test_no_file_name_and_no_home_directory_reaches_public_bytes():
    """The rows are anonymous triples: the size of a file is the work, the name is the person."""
    work = measured_work()
    payload = export_run({"turns_typed": 2, "file_work": work, "hero_visual": "size-map"})
    raw = json.dumps(payload)
    assert "file_work" in payload and payload["hero_visual"] == "size-map"
    assert ".py" not in raw and ".js" not in raw and "/" not in raw.replace("\\/", "")
    for row in payload["file_work"]["files"]:
        assert [type(cell) for cell in row] == [int, int, int]
    for unsafe in ("/Users/oscar", "Users-oscar-code", "~", "../secrets", "my secrets"):
        with pytest.raises(ValueError):
            filework.validate_file_work(dict(work, folders=[
                dict(work["folders"][0], name=unsafe)] + work["folders"][1:]))
    from agentgrinder import privacy

    assert not privacy.scan(runviz.size_map_html(work) + runviz.folder_line_html(work))


def test_the_local_card_shows_the_chosen_hero_and_hides_the_rest():
    run = {"harness": "Cursor", "project": "agentgrinder-public", "title": "Components",
           "turns_typed": 4, "tool_calls": 80, "commits": 5, "files_touched": 4,
           "ridge": [1] * 50, "ridge_basis": "wall-time", "ridge_wall_seconds": 900,
           "file_work": measured_work()}
    card = render_card(build_activity(run))
    assert 'data-visual="size-map"' in card
    assert '<div class="ridgewrap">' not in card      # one hero, not two
    picked = render_card(build_activity(dict(run, hero_visual="folder-line")))
    assert 'data-visual="folder-line"' in picked and 'data-visual="size-map"' not in picked
    plain = render_card(build_activity({k: v for k, v in run.items() if k != "file_work"}))
    assert '<div class="ridgewrap">' in plain and '<figure class="pc-visual' not in plain


def test_the_reduced_motion_rule_covers_the_only_thing_that_moves():
    """A small draw-in for the lines, and nothing else. Reduced motion finishes it immediately."""
    for sheet in (runviz.CSS, (ROOT / "site/design.css").read_text()):
        tight = sheet.replace(" ", "").replace("\n", "")
        assert "prefers-reduced-motion:reduce" in tight
        assert ".pc-draw{animation:none;stroke-dashoffset:0}" in tight
    work = measured_work()
    assert "pc-draw" in runviz.folder_line_html(work)
    assert "pc-draw" in runviz.elevation_html(work)
    assert "pc-draw" not in runviz.size_map_svg(work)[0]      # tiles do not animate


def _node(script, *args):
    return subprocess.run(["node", "-e", script, *[str(a) for a in args]],
                          capture_output=True, text=True, check=True).stdout


def test_the_browser_draws_the_same_pixels_as_the_local_card():
    """Two implementations of one drawing. A rounding rule apart is a tenth of a pixel apart."""
    work = measured_work()
    out = _node(
        "const v=require(process.argv[1]);const w=JSON.parse(process.argv[2]);"
        "v.validateFileWork(w);"
        "process.stdout.write(JSON.stringify([v.sizeMapHtml(w),v.folderLineHtml(w),"
        "v.elevationHtml(w),v.heroHtml({file_work:w})]));",
        VISUALS_JS, json.dumps(work))
    size, folder, lift, hero = json.loads(out)
    assert size == runviz.size_map_html(work)
    assert folder == runviz.folder_line_html(work)
    assert lift == runviz.elevation_html(work)
    assert hero == runviz.hero_html({"file_work": work})


def test_the_browser_boundary_refuses_what_the_local_contract_refuses():
    bad = [dict(measured_work(), totals={"files_end": 6, "files_touched": 4, "lines_end": 1360,
                                         "lines_changed": 12}),
           dict(measured_work(), v=2)]
    out = _node(
        "const c=require(process.argv[1]);const rows=JSON.parse(process.argv[2]);"
        "let refused=0;for(const file_work of rows){try{c.validate({file_work})}catch(e){refused++}}"
        "process.stdout.write(String(refused));",
        CONTRACT_JS, json.dumps(bad))
    assert out == "2"
    for payload in bad:
        with pytest.raises(ValueError):
            validate_run({"file_work": payload})


def test_the_picker_offers_only_what_the_capture_measured():
    work = measured_work()
    out = _node(
        "const v=require(process.argv[1]);const w=JSON.parse(process.argv[2]);"
        "process.stdout.write(JSON.stringify([v.pickerHtml({file_work:w,ridge:Array(50).fill(1)}),"
        "v.pickerHtml({}),v.available({file_work:w})]));",
        VISUALS_JS, json.dumps(work))
    picker, empty, offered = json.loads(out)
    assert offered == ["size-map", "folder-line", "elevation"]
    for label in ("Size map", "Folder line", "Elevation", "Activity ridge"):
        assert label in picker
    assert "Screenshot" not in picker              # no image on this run, so it is not offered
    assert picker.count('type="radio"') == 4
    assert 'value="size-map" checked' in picker
    assert "no visual yet" in empty and "radio" not in empty


# ---------------------------------------------------------------------------------------------
# 390px, in a real browser, with the app's own stylesheet. Every label is measured where it
# actually landed: a folder line whose first station's name hangs off the left edge passes every
# string test in this file and fails the only reader who matters.
#
# The page is the components inside a 390px column, not the whole card, because the card's own
# layout at 390 is what it was before this change and this test is about what was added.
# ---------------------------------------------------------------------------------------------
PROBE = """
<script>
window.addEventListener('load',()=>{
  const worst=[];
  document.querySelectorAll('#at390 *').forEach(node=>{
    if(node.children.length) return;
    const box=node.getBoundingClientRect();
    if(box.width===0&&box.height===0) return;
    if(box.left<-0.5||box.right>390.5) worst.push(node.tagName+' '+
      (node.textContent||'').slice(0,22).trim()+' ['+box.left.toFixed(1)+','+
      box.right.toFixed(1)+']');
  });
  const column=document.getElementById('at390');
  document.documentElement.dataset.fits=String(!worst.length&&column.scrollWidth<=390);
  document.documentElement.dataset.worst=worst.slice(0,4).join(' | ')+
    ' scrollWidth='+column.scrollWidth;
});
</script>
"""

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="design.css">
<style>body{margin:0;background:#fff;font:15px/1.5 'IBM Plex Sans',system-ui,sans-serif}
#at390{width:390px;background:#fff}</style></head>
<body><div id="at390">__BODY__</div>__PROBE__</body></html>"""


def _browser():
    for candidate in [os.environ.get("CHROME_BIN"), "/opt/google/chrome/chrome",
                      "google-chrome", "chromium", "chromium-browser",
                      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]:
        if candidate and (Path(candidate).is_file() or shutil.which(candidate)):
            return candidate if Path(candidate).is_file() else shutil.which(candidate)
    return None


def test_every_component_fits_a_390px_phone():
    chrome = _browser()
    if not chrome:
        pytest.skip("390px render NOT RUN: set CHROME_BIN to a Chrome-compatible browser.")
    long_names = [{"name": "agentgrinder", "files_end": 3, "lines_end": 900, "touched_files": 2,
                   "lines_changed": 620, "deleted_files": 1, "deleted_lines": 120, "returns": 2},
                  {"name": "supabase-migrations-strava", "files_end": 2, "lines_end": 400,
                   "touched_files": 1, "lines_changed": 180, "deleted_files": 0,
                   "deleted_lines": 0, "returns": 1},
                  {"name": "docs", "files_end": 1, "lines_end": 60, "touched_files": 0,
                   "lines_changed": 0, "deleted_files": 0, "deleted_lines": 0, "returns": 0}]
    work = measured_work(folders=long_names)
    run = {"file_work": work, "image_url": "https://example.com/shot.png",
           "quote": {"text": "The folder line showed the run went back to tests four times.",
                     "chosen_by": "author"},
           "gear": {"agent": "Cursor agent", "harness": "Cursor", "model": "Claude Opus 4.1",
                    "runs": 42, "commits": 91, "basis": "Counted from the runs captured here"},
           "trophies": [{"id": "longest-run", "label": "Longest run", "value": "2h 41m",
                         "basis": "Longest moving time across the captured runs"},
                        {"id": "biggest-pr", "label": "Biggest pull request", "value": "2,639",
                         "basis": "Most lines changed in a captured run with a pull request"}]}
    for hero in ("size-map", "folder-line", "elevation"):
        body = (runviz.hero_html(dict(run, hero_visual=hero))
                + runviz.components_html(run))
        assert f'data-visual="{hero}"' in body
        with tempfile.TemporaryDirectory(prefix="pc-390-") as folder:
            shutil.copy(ROOT / "site/design.css", Path(folder) / "design.css")
            page = Path(folder) / "at390.html"
            page.write_text(PAGE.replace("__BODY__", body).replace("__PROBE__", PROBE),
                            encoding="utf-8")
            shot = Path(folder) / f"{hero}-390.png"
            result = subprocess.run(
                [chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
                 "--disable-background-networking", "--hide-scrollbars",
                 f"--user-data-dir={folder}/profile", "--window-size=390,1400",
                 "--virtual-time-budget=1200", f"--screenshot={shot}", "--dump-dom",
                 page.resolve().as_uri()],
                text=True, capture_output=True, timeout=60, check=True)
        dom = result.stdout
        worst = re.search(r'data-worst="([^"]*)"', dom)
        assert 'data-fits="true"' in dom, f"{hero} does not fit 390px: {worst and worst.group(1)}"


def test_the_repository_can_measure_itself():
    """The capture, run on this repository's own recent history. No fixture, real git."""
    work = filework.measure_range(str(ROOT), "HEAD~3", "HEAD")
    if not work:
        pytest.skip("No commit with a counted line change in HEAD~3..HEAD.")
    filework.validate_file_work(work)
    totals = work["totals"]
    assert totals["lines_changed"] > 0 and totals["files_touched"] > 0
    assert totals["files_end"] == len(work["files"]) > 0
    assert sum(row[2] for row in work["files"]) + work["deleted"]["lines"] == totals["lines_changed"]
    assert sum(folder["lines_changed"] for folder in work["folders"]) == totals["lines_changed"]
    assert re.match(r"^[0-9a-f]{7,40}\.\.[0-9a-f]{7,40}$", work["range"])
    assert runviz.size_map_html(work).count("<text") == 0
