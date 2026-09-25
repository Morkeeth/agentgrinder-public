"""The ghost run, the run map and the stride line, on every surface at once.

Oscar, 25 Sep 2026: "Strava is for people who ran. STRIVE is for people who didn't." A run with a
long measured time while the person was not there earns the ghost badge; the line under it is the
run's own numbers and nothing else. The map is the route through folders as station indices, and
the stride line is two lines of plain text to paste anywhere. The browser (site/feed-card.js) and
the local card (agentgrinder/feedcard.py) draw all three from one rule each, and the payload that
leaves a device for /l/ carries indices, never a folder name.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agentgrinder import feedcard, ingest  # noqa: E402

# A real overnight session on the author's machine, 20 Sep 2026, as the browser reader counts it:
# 1 typed turn, 270 tool calls, 12h 18m of moving time, started at 22:44 local. Numbers only.
GHOST = {"id": "g", "title": "Night build", "harness": "Claude Code", "prompts": 1, "tool_calls": 270,
         "duration_s": 44330, "started_hour": 22, "rhythm": [1] + [0] * 23, "route": [0, 0, 1],
         "profiles": {"display_name": "Oscar"}}
DAY_ALONE = {"title": "Afternoon", "harness": "Cursor", "prompts": 2, "tool_calls": 112, "duration_s": 7354,
             "started_hour": 10, "ridge": [i % 5 for i in range(50)]}
DAY_RATIO = {"title": "Delegated", "harness": "Codex", "prompts": 4, "tool_calls": 174, "duration_s": 12495,
             "started_hour": 15}
NOT_GHOST = [
    {"title": "short", "prompts": 1, "tool_calls": 200, "duration_s": 3599, "started_hour": 23},   # under an hour
    {"title": "idle", "prompts": 1, "tool_calls": 29, "duration_s": 7200, "started_hour": 23},     # too few calls
    {"title": "present", "prompts": 12, "tool_calls": 300, "duration_s": 7200, "started_hour": 14},  # 25 per turn by day
    {"title": "no time", "prompts": 1, "tool_calls": 300, "started_hour": 23},                     # no measured time
    {"title": "awake", "prompts": 12, "tool_calls": 30, "duration_s": 3600, "started_hour": 23},   # typed 12 times at night
]
UNKNOWN_TURNS_NIGHT = {"title": "hosted", "tool_calls": 90, "duration_s": 5400, "started_hour": 1}


def node(expr: str, *args) -> str:
    return subprocess.run(["node", "-e", expr, str(ROOT), *args], capture_output=True, text=True, check=True).stdout


def visible(markup: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", markup).split())


def test_the_ghost_rule_is_honest_and_the_same_in_both_readers():
    rows = [GHOST, DAY_ALONE, DAY_RATIO, *NOT_GHOST, UNKNOWN_TURNS_NIGHT]
    js = json.loads(node("const F=require(process.argv[1]+'/site/feed-card.js');process.stdout.write(JSON.stringify(JSON.parse(process.argv[2]).map(F.ghost)))", json.dumps(rows)))
    py = [feedcard.ghost(r) for r in rows]
    assert js == py
    assert py[0] == {"key": "ghost", "label": "Ghost run", "detail": "12h 19m while you slept"}
    assert py[1]["detail"] == "2h 3m, you typed twice"
    assert py[2]["detail"] == "3h 28m, you typed 4 times"
    assert py[3:3 + len(NOT_GHOST)] == [None] * len(NOT_GHOST)
    assert py[-1]["detail"] == "1h 30m while you slept"           # turns unknown, night start
    # The ghost outranks every other badge, and a ghost card says so in its class and its icon.
    assert feedcard.achievement(GHOST)["key"] == "ghost"
    card = feedcard.card(GHOST)
    assert '<article class="card fc ghost">' in card and 'fc-badge fc-ghost' in card
    assert '<article class="card fc">' in feedcard.card(NOT_GHOST[2])


def test_no_disclaimer_rides_with_the_joke():
    text = visible(feedcard.card(GHOST)).lower()
    for word in ("disclaimer", "estimated", "approximately", "may not", "not verified", "unverified", "beta"):
        assert word not in text


def test_the_map_is_drawn_from_indices_and_hidden_without_them():
    with_map = feedcard.card({**GHOST, "route": [0, 1, 0, 2, 1, 3]})
    assert 'class="fc-map"' in with_map and with_map.count('class="fc-hop"') == 5 and with_map.count('class="fc-stn"') == 4
    assert "4 folders · 5 moves · 2 returns" in visible(with_map)
    # A row saved before the readers collapsed stays reads the same: [0, 0, 1] is one move, no return.
    assert "2 folders · 1 move · 0 returns" in visible(feedcard.card({**GHOST, "route": [0, 0, 1]}))
    # A gap in the numbering names no phantom station: [0, 5, 0] is two folders and one return.
    assert "2 folders · 2 moves · 1 return" in visible(feedcard.card({**GHOST, "route": [0, 5, 0]}))
    for route in (None, [], [0], [0, 0, 0], [0, "site"], [0, 16], [-1, 0]):
        assert 'class="fc-map"' not in feedcard.card({**GHOST, "route": route}), route
    # The browser draws the same map, character for character.
    js = node("const F=require(process.argv[1]+'/site/feed-card.js');process.stdout.write(F.routeMap(JSON.parse(process.argv[2])))",
              json.dumps({**GHOST, "route": [0, 1, 0, 2, 1, 3, 3, 0]}))
    assert js == feedcard.route_map({**GHOST, "route": [0, 1, 0, 2, 1, 3, 3, 0]})


def test_the_route_never_carries_a_folder_name(tmp_path):
    session = tmp_path / "s.jsonl"
    lines = [
        {"type": "user", "timestamp": "2026-09-20T22:50:00Z", "cwd": "/Users/alice/SECRET-PROJECT", "promptSource": "typed",
         "message": {"role": "user", "content": "PROMPT-TEXT"}},
        {"type": "assistant", "timestamp": "2026-09-20T22:50:20Z", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/Users/alice/SECRET-PROJECT/site/a.js"}},
            {"type": "tool_use", "name": "Edit", "input": {"file_path": "/Users/alice/SECRET-PROJECT/tests/t.py"}},
            {"type": "tool_use", "name": "Edit", "input": {"file_path": "/Users/alice/SECRET-PROJECT/tests/u.py"}},
            {"type": "tool_use", "name": "Write", "input": {"file_path": "/Users/alice/SECRET-PROJECT/site/b.js"}}]}},
        {"type": "user", "timestamp": "2026-09-20T23:50:00Z", "promptSource": "typed", "message": {"role": "user", "content": "again"}},
    ]
    session.write_text("\n".join(json.dumps(x) for x in lines))
    run = ingest.parse_session(str(session))
    assert run["route"] == [0, 1, 0]                       # site, tests, back to site: two stays in tests are one
    assert run["route_legend"] == ["site", "tests"]        # names stay local (hook.py drops them)
    public = {k: v for k, v in run.items() if k != "route_legend"}
    assert "SECRET-PROJECT" not in json.dumps(public.get("route")) and all(isinstance(v, int) for v in run["route"])
    # The browser payload for the same file: indices, and nothing that names the folder.
    payload = node("const D=require(process.argv[1]+'/site/dropin-parse.js');const r=D.parseText(require('fs').readFileSync(process.argv[2],'utf8'));process.stdout.write(JSON.stringify(D.uploadPayload(r,'t')))", str(session))
    assert json.loads(payload)["route"] == [0, 1, 0]
    for probe in ("SECRET", "alice", "site", "tests", "/Users", "PROMPT-TEXT", "a.js"):
        assert probe not in payload, probe


def test_the_route_caps_stations_and_moves():
    paths = [f"/r/f{i % 20}/x.py" for i in range(1000)]
    route, names = ingest.folder_route(paths)
    assert max(route) == 15 and len(route) <= 400 and len(names) == 16
    js = json.loads(node("const D=require(process.argv[1]+'/site/dropin-parse.js');process.stdout.write(JSON.stringify(D.folderRoute(JSON.parse(process.argv[2]))))", json.dumps(paths)))
    assert js == route
    # The payload sends the route as read or not at all: nothing is clamped into range.
    for bad in ([0, 16], [0, "site"], [1.5], list(range(401))):
        sent = json.loads(node("const D=require(process.argv[1]+'/site/dropin-parse.js');process.stdout.write(JSON.stringify(D.uploadPayload({harness:'Codex',rhythm:[1],route:JSON.parse(process.argv[2])},'t').route))", json.dumps(bad)))
        assert sent is None, bad


def test_the_stride_line_is_the_card_in_two_lines_and_pastes_the_same_from_both_readers():
    rows = [GHOST, DAY_ALONE, {"title": "t", "harness": "Cursor", "tool_calls": 98, "prompts": 1, "duration_s": 1080,
                               "started_hour": 23, "rhythm": [2, 7, 1, 3, 2, 1, 2, 1, 3, 2, 1, 2]}]
    url = "https://agentic-strava.vercel.app/l/k7f2"
    js = json.loads(node("const F=require(process.argv[1]+'/site/feed-card.js');process.stdout.write(JSON.stringify(JSON.parse(process.argv[2]).map(r=>F.strideText(r,process.argv[3]))))", json.dumps(rows), url))
    py = [feedcard.stride_text(r, url) for r in rows]
    assert js == py
    first, second = py[0].split("\n")
    assert first == "STRIVE · Claude Code · 12h 19m while you slept · 270 tool calls · 1 turn · 👻 Ghost run"
    assert py[1].startswith("STRIVE · Cursor · 2h 3m, you typed twice · 112 tool calls · 👻 Ghost run\n")
    assert second.endswith("  agentic-strava.vercel.app/l/k7f2") and re.fullmatch(r"[▁▂▃▄▅▆▇█]{2,12}", second.split("  ")[0])
    assert py[2].startswith("STRIVE · Cursor · 98 tool calls · 18m · 1 turn · One-shot\n")
    # No prompt, no path, no code: the line is figures and a badge, nothing the run typed.
    assert "PROMPT" not in py[0] and "/" not in first
    # Every card carries it; the local card has no Copy button because it carries no script.
    assert '<div class="fc-stride"><pre>' in feedcard.card(GHOST) and "fc-copy" not in feedcard.card(GHOST)
    web = node("const F=require(process.argv[1]+'/site/feed-card.js');process.stdout.write(F.card(JSON.parse(process.argv[2]),{preview:true,copy:true,url:process.argv[3]}))", json.dumps(GHOST), url)
    assert 'class="fc-copy" data-copy="STRIVE · Claude Code' in web
    # And the terminal prints the same two lines.
    lines = feedcard.terminal_lines(GHOST)
    assert lines[-2].strip() == first and lines[-1].strip() == second.split("  ")[0]


def test_orange_is_spent_on_three_marks_only():
    css = (ROOT / "site/feed.css").read_text()
    rules = [line for line in css.splitlines() if "--strive-orange" in line and not line.startswith(":root")]
    selectors = sorted(rule.split("{")[0].strip() for rule in rules)
    # The peak is one mark drawn twice: the dot on the activity line and the tallest bar of the
    # stride line. One rule colours both, so it stays one of the three.
    assert selectors == [".fc-act.kudo.on,.fc-act.kudo.on svg", ".fc-badge.fc-ghost svg,.fc-badge.fc-ghost b", ".fc-peak,.fc-bars b"]
    assert "#fc4c02" not in css.lower().replace(":root{--strive-orange:#fc4c02}", "")
    # The map is blue: none of its classes name the orange.
    for cls in (".fc-rail", ".fc-hop", ".fc-stn"):
        rule = next(line for line in css.splitlines() if line.startswith(cls))
        assert "orange" not in rule


def test_the_landing_and_the_share_image_carry_the_line():
    html = (ROOT / "site/index.html").read_text()
    assert "Strava is for people who ran. <i>__BRAND__</i> is for people who didn't." in html
    assert html.count("Strava is for people who ran. __BRAND__ is for people who didn't.") == 2   # og + twitter
    server = (ROOT / "server/public-run.mjs").read_text()
    assert "Strava is for people who ran. ${BRAND} is for people who didn't." in server
    # The share image draws the ghost in orange and the map from the same geometry as the card.
    assert "badge.key==='ghost'?ORANGE:BLUE" in server and "Feed.routeGeometry(run)" in server
    # `route` is the map, and never a second line on the image.
    assert "'Project ridge'" not in server


def test_a_subagent_capture_reads_claude_code_on_every_surface():
    row = {"title": "", "harness": "claude-agent", "started": "2026-09-25T02:00:00Z", "tool_calls": 40, "prompts": 1, "duration_s": 600}
    card = feedcard.card(row)
    assert "claude-agent" not in card and "Claude Code" in visible(card)
    assert feedcard.stride_text(row).startswith("STRIVE · Claude Code · ")
    assert row["harness"] == "claude-agent"                  # the row keeps the raw value
    js = node("const F=require(process.argv[1]+'/site/feed-card.js');process.stdout.write(F.card(JSON.parse(process.argv[2]),{preview:true,heading:'h1'}))", json.dumps(row))
    assert js == feedcard.card(row, avatars=True)


def test_codex_desktop_rollouts_count_the_prompts_the_person_typed():
    # A 29 Jul 2026 desktop rollout on the author's machine read as 0 typed prompts, which would
    # have fed the ghost badge a false number. The typed turns there are user-role messages.
    run = ingest.parse_codex_session(str(ROOT / "samples/dropin/codex-desktop.jsonl"))
    assert run["turns_typed"] == 2 and run["tool_calls"] == 2 and run["route"] == [0, 1]
    assert "PROMPT-SENTINEL" not in json.dumps({k: v for k, v in run.items() if k not in ("title", "private_title_prompt")})
    with_events = ingest.parse_codex_session(str(ROOT / "samples/dropin/codex-edge.jsonl"))
    assert with_events["turns_typed"] >= 1                   # the event form still reads as before


def test_copy_reads_the_stride_at_the_click_so_the_link_is_on_it():
    # The drop-in wires Copy before a link exists and rewrites data-copy once it does. A handler
    # that read the text at wiring time copied the line without the address.
    out = node("""const {JSDOM}=require(process.argv[1]+'/node_modules/jsdom');
const dom=new JSDOM('<button class="fc-copy" data-copy="A">Copy</button>');
global.window=dom.window;global.document=dom.window.document;
const F=require(process.argv[1]+'/site/feed-card.js');
const got=[];Object.defineProperty(globalThis,'navigator',{value:{clipboard:{writeText:async t=>{got.push(t)}},share:d=>{got.push('share:'+d.text);return Promise.resolve()}},configurable:true});
F.wireStride(document);const b=document.querySelector('.fc-copy');b.dataset.copy='B';
b.click();document.querySelector('.fc-share').click();
setTimeout(()=>process.stdout.write(JSON.stringify(got)),20);""")
    assert json.loads(out) == ["B", "share:B"]


def test_a_ghost_run_leads_with_the_time_it_ran_alone():
    lead = feedcard.headline(GHOST)
    assert (lead["n"], lead["unit"]) == ("12h 19m", "while you slept")
    assert feedcard.headline(DAY_ALONE)["unit"] == "you typed twice"
    # Tool calls come second; the time is never repeated as a small figure.
    assert [k for k, _ in feedcard.stats(GHOST, lead)] == ["Tool calls", "Turns"]
    # A ghost with commits still leads with its time.
    assert feedcard.headline({**DAY_RATIO, "commits": 3, "files_touched": 9})["n"] == "3h 28m"
    # The badge names the run and stops: the hero already says how long and how alone.
    text = visible(feedcard.card(GHOST).split('<div class="fc-stride">')[0])
    assert text.count("12h 19m") == 1 and "while you slept" in text and "Ghost run" in text
    # A run that is not a ghost keeps its old headline.
    assert feedcard.headline({"commits": 2, "files_touched": 5, "tool_calls": 40, "duration_s": 5400, "prompts": 12})["unit"] == "commits"
    js = json.loads(node("const F=require(process.argv[1]+'/site/feed-card.js');process.stdout.write(JSON.stringify(JSON.parse(process.argv[2]).map(r=>{const l=F.headline(r);return [l,F.stats(r,l)]})))",
                         json.dumps([GHOST, DAY_ALONE, DAY_RATIO, *NOT_GHOST])))
    py = [[feedcard.headline(r), [list(f) for f in feedcard.stats(r, feedcard.headline(r))]] for r in [GHOST, DAY_ALONE, DAY_RATIO, *NOT_GHOST]]
    assert js == py


def test_the_stride_bars_are_monospace_with_the_peak_marked_and_copy_plain():
    row = {**GHOST, "rhythm": [2, 7, 1, 3, 2, 1, 2, 1, 3, 2, 1, 2]}
    html = feedcard.stride_html(row, "https://agentic-strava.vercel.app/l/k7f2")
    bars = re.search(r'<span class="fc-bars">(.*?)</span>', html).group(1)
    assert bars.count("<b>") == 1 and re.sub(r"</?b>", "", bars) == feedcard.stride_bars(row)
    assert re.search(r"<b>(.)</b>", bars).group(1) == "█"
    # What is copied is the plain text; the markup is only on the card.
    web = node("const F=require(process.argv[1]+'/site/feed-card.js');process.stdout.write(F.card(JSON.parse(process.argv[2]),{preview:true,copy:true,url:process.argv[3]}))",
               json.dumps(row), "https://agentic-strava.vercel.app/l/k7f2")
    copied = re.search(r'data-copy="([^"]*)"', web).group(1)
    assert "<" not in copied and "&lt;" not in copied and feedcard.stride_bars(row) in copied
    js = node("const F=require(process.argv[1]+'/site/feed-card.js');process.stdout.write(F.strideHtml(JSON.parse(process.argv[2]),process.argv[3]))",
              json.dumps(row), "https://agentic-strava.vercel.app/l/k7f2")
    assert js == html
    css = (ROOT / "site/feed.css").read_text()
    assert "monospace" in next(line for line in css.splitlines() if line.startswith(".fc-bars{"))


def test_a_two_folder_map_is_a_short_strip():
    small = feedcard.route_geometry({"route": [0, 1, 0]})
    full = feedcard.route_geometry({"route": [0, 1, 2]})
    assert small["h"] < full["h"] and 'viewBox="0 0 300 26"' in feedcard.route_map({"route": [0, 1, 0]})
    for route in ([0, 1, 0, 1, 0], [0, 1, 2, 0]):
        js = node("const F=require(process.argv[1]+'/site/feed-card.js');process.stdout.write(F.routeMap(JSON.parse(process.argv[2])))", json.dumps({"route": route}))
        assert js == feedcard.route_map({"route": route})
