"""The avatar is the grind trace, never a stock glyph.

The defect this file pins: on 3 Sep 2026 every avatar on the site was a bordered circle with one
initial in it (M, a, n). Section 6 of archive/hackathon-2026-09/docs/AGENT-GRINDER-BRANDBOOK.md says the opposite in
writing: "The mark is generative: the grind trace, the rhythm of a real session drawn as a
profile line. Every grind has a different shape, so the logo is never a stock glyph." A letter in
a circle is a stock glyph, and it is the same glyph for every account whose handle starts with
the same letter.

These are contract tests over site/index.html. The string tests pin the shape of the source (no
call site left rendering a letter, no circle, no second accent). The node tests RUN the shipped
avatar code and read what it actually returns, because "the source says empty" is not the same
claim as "an account with no runs renders the empty hairline".
"""
import json
import os
import re
import shutil
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = open(os.path.join(REPO, "site", "index.html"), encoding="utf-8").read()

# The slice of the shipped file that draws every avatar. Sliced by marker, so if the block is
# renamed or moved these tests fail loudly instead of grading code nobody ships.
START = "const TRACES={}, TRACE_LOOKED={}, TRACE_AGENT={};"
END = "\nconst esc="
AVATAR_SRC = HTML[HTML.index(START):HTML.index(END, HTML.index(START))]
# Load the shipped presentation rule, not a stub of its legacy/identity fallback.
PROFILE_HELPER = re.search(r"^const profileHandle=.*;$", HTML, re.M).group(0)
AVATAR_RUNTIME = ("const GrinderAuth=require(" + json.dumps(os.path.join(REPO, "site", "auth.js")) + ");\n"
                  + PROFILE_HELPER + "\n" + AVATAR_SRC)


# ---------------------------------------------------------------- the source

def test_no_call_site_renders_a_bare_initial():
    # the old render, in every form it took, is gone
    assert "return esc((handle||'?')[0]).toUpperCase()" not in HTML
    assert "esc((h[0]||'?').toUpperCase())" not in HTML
    assert ".toUpperCase()" not in AVATAR_SRC
    # and no call site wraps avatar() in the old div, which is how a letter got a circle
    assert '<div class="av">${avatar' not in HTML
    assert '<span class="av">${avatar' not in HTML


def test_the_only_hand_written_av_tile_left_is_the_loading_skeleton():
    # every `class="av` in the file is either the tile avatar() builds, or the grey skeleton box
    hits = [m.start() for m in re.finditer(r'class="av', HTML)]
    inside_avatar = HTML.index(START), HTML.index(END, HTML.index(START))
    skeleton = HTML.index("function skeletonCard()")
    skeleton_end = HTML.index("}", HTML.index("</div>`;", skeleton))
    for h in hits:
        assert (inside_avatar[0] <= h <= inside_avatar[1]) or (skeleton <= h <= skeleton_end), \
            "a hand written avatar tile at offset %d" % h


def test_every_avatar_carries_the_handle_for_a_screen_reader():
    # the letter is gone, so the handle has to ride in aria-label
    assert 'role="img" aria-label="${esc(label)}"' in AVATAR_SRC
    assert "'@'+handle" in AVATAR_SRC


def test_nonpublic_runs_never_write_their_authors_profile_trace():
    # A reusable profile mark must not preserve a revoked private audience trace.
    assert "if(!r||r.visibility!=='public') return;" in AVATAR_SRC


def test_the_agent_rule_reads_a_row_and_never_a_name():
    # an account is an agent because its own row says so, not because the name looked like one
    assert "const isAgentProfile=p=>!!(p&&p.rig&&p.rig.agent===true);" in AVATAR_SRC
    assert ".av.agent::after" in HTML          # one hairline underline, no badge, no new colour
    assert "background:var(--ink)}" in HTML[HTML.index(".av.agent::after"):HTML.index(".av.agent::after") + 200]


def test_the_tile_is_square_hairline_and_monochrome():
    css = HTML[HTML.index(".av{"):HTML.index("}", HTML.index(".av{")) + 1]
    assert "border-radius:50%" not in css        # the circle is gone
    assert "font-size" not in css                # nothing in the tile is type any more
    assert "1px solid var(--rule)" in css        # still a hairline box
    trace = HTML[HTML.index(".trace{"):HTML.index("}", HTML.index(".trace{")) + 1]
    assert "var(--blue)" not in trace and "#0047ff" not in trace   # the accent carries meaning elsewhere
    assert "animation" not in trace and "box-shadow" not in trace  # no pulsing, no shadow
    # the share tile stops being a circle too
    share = HTML[HTML.index(".share-av{"):HTML.index("}", HTML.index(".share-av{")) + 1]
    assert "border-radius" not in share


# ---------------------------------------------------------------- the render

NODE = shutil.which("node")
HARNESS = """
const esc=s=>(s||'').replace(/[<>&]/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]));
%s
const out={};
// an account this page looked for and found nothing for
noteLooked(['nobody']);
noteLooked(['owner'],'all');   // your own view reads your private runs too
out.empty=avatar('nobody');
out.mine=avatar('owner');
// an account with two runs: the newest one is the mark
noteTraces([
  {visibility:'public',created_at:'2026-09-01T00:00:00Z',rhythm:[1,1,1,1],profiles:{github_handle:'Morkeeth'}},
  {visibility:'public',created_at:'2026-09-02T00:00:00Z',rhythm:[9,0,4,7,2],profiles:{github_handle:'Morkeeth'}}]);
out.real=avatar('Morkeeth');
noteTraces([{visibility:'public',created_at:'2026-09-02T00:00:00Z',rhythm:[9,0,4,7,2],profiles:{handle:'email-builder',github_handle:null}}]);
out.chosen=avatar('email-builder');
// an anonymous run must not become anyone's mark
noteTraces([{visibility:'anonymous',created_at:'2026-09-03T00:00:00Z',rhythm:[5,5,5],
             profiles:{github_handle:'shy'}}]);
out.anon=avatar('shy');
noteTraces([{visibility:'close_friends',created_at:'2026-09-03T00:00:00Z',rhythm:[8,1,8],
             profiles:{github_handle:'close-builder'}}]);
out.close=avatar('close-builder');
out.ghost=avatar('ghost',{ghost:true});
// an agent account, flagged by its own row
noteTraces([{visibility:'public',created_at:'2026-09-02T00:00:00Z',rhythm:[3,1,4],
             profiles:{github_handle:'bot',rig:{agent:true}}}]);
out.agent=avatar('bot');
out.big=avatar('Morkeeth',{size:56,cls:'share-av'});
console.log(JSON.stringify(out));
"""


def render():
    if not NODE:
        pytest.skip("node is not on this machine")
    r = subprocess.run([NODE, "-e", HARNESS % AVATAR_RUNTIME], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_an_account_with_no_runs_renders_the_empty_hairline_and_says_so():
    o = render()
    assert '<line class="trace empty"' in o["empty"]
    assert "<polyline" not in o["empty"]
    # a logged out visitor can only read public runs, so the tile says exactly that
    assert 'title="no public grind yet"' in o["empty"]
    assert 'aria-label="@nobody, no public grind yet"' in o["empty"]
    # a flat line, drawn once across the middle of a 26px tile
    assert 'y1="13.0" x2="23.5" y2="13.0"' in o["empty"]


def test_only_your_own_view_may_say_no_grind_at_all():
    # every other view reads public runs only, so "no grind yet" there would be a claim the
    # query could not support: someone with private runs is not someone with no runs.
    o = render()
    assert 'title="no grind yet"' in o["mine"]
    assert "public" not in o["mine"]


def test_an_account_with_runs_draws_its_newest_rhythm_and_no_letter():
    o = render()
    assert '<polyline class="trace"' in o["real"]
    assert "title=" not in o["real"]
    assert 'aria-label="@Morkeeth, grind trace"' in o["real"]
    pts = re.search(r'points="([^"]+)"', o["real"]).group(1).split(" ")
    assert len(pts) == 5                        # the newest run, 5 minutes, not the older 4
    ys = [float(p.split(",")[1]) for p in pts]
    assert ys[0] < ys[1]                        # the 9 sits above the 0: a real profile line
    assert len(set(ys)) > 1                     # not a flat line, so it is not the empty state


def test_two_accounts_do_not_share_a_mark():
    o = render()
    assert o["real"] != o["agent"]
    assert re.search(r'points="([^"]+)"', o["real"]).group(1) != \
        re.search(r'points="([^"]+)"', o["agent"]).group(1)


def test_an_anonymous_grind_leaves_no_mark_on_anyone():
    o = render()
    assert '<line class="trace empty"' in o["anon"]      # the ghost's author keeps no shape
    assert '<line class="trace empty"' in o["ghost"]
    assert 'aria-label="anonymous grinder, no trace"' in o["ghost"]
    assert "grind yet" not in o["ghost"]                # we never looked, so we never claim


def test_a_close_friends_grind_leaves_no_reusable_profile_mark():
    o = render()
    assert '<line class="trace empty"' in o["close"]
    assert "<polyline" not in o["close"]


def test_an_agent_account_is_one_extra_hairline_not_a_badge_or_a_colour():
    o = render()
    assert 'class="av agent"' in o["agent"]
    assert "<polyline" in o["agent"]
    for word in ("badge", "emoji", "svg fill", "#", "bot-"):
        assert word not in o["agent"].replace('aria-label="@bot, grind trace"', "")


def test_the_share_tile_is_the_same_trace_at_56px():
    o = render()
    assert 'class="av share-av"' in o["big"]
    assert 'viewBox="0 0 56 56"' in o["big"]


def test_chosen_handle_without_github_gets_its_real_trace():
    out = render()
    assert '<polyline' in out['chosen']
    assert '@email-builder' in out['chosen']
