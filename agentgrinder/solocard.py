"""THE GRIND CARD — one ordinary session, made postable.

Runs are the product noun; grind remains the compatible CLI command. The trace is the signature visual across local cards and the network.

THE NUMBER AT THE TOP IS VERIFIED PER TURN, never the prompt count. Prompts are the cost of a
grind (the denominator); a card whose first big number is "47 prompts" crowns the person who
typed the most (METR 2025: developers believed +20%, measured -19%). The Strava-shaped numbers --
prompts, moving time, pace, commits -- are all still here, grouped under COST. Where the run has
no verified-claims count (an old `--json` dump), the headline is an em-dash whose tooltip names
what is missing, not a zero. `metrics.headline_of` is the one definition every surface reads.

Every sentence here names what it counted and over which population, or prints an em-dash.
"""
from __future__ import annotations
from .brand import BRAND, CARD_THEME

import os
from datetime import datetime

from .authorship import CATEGORIES, COMMAND
from . import privacy
from .metrics import ARTIFACTS_PER_TURN_TIP, HEADLINE_TIP, headline_of
from .render import GRID_CSS, _five_block, _has_value, _unmeasured_note
from .soloroute import render_route_svg, render_phone_svg, _esc, span_minutes


def _dur(s) -> str:
    if not s:
        return "—"
    h, r = divmod(int(s), 3600)
    m, sec = divmod(r, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m {sec:02d}s"


def _pace(s) -> str:
    if not s:
        return "—"
    m, sec = divmod(int(round(s)), 60)
    return f"{m}:{sec:02d}"


def headline(run: dict) -> tuple[str, str]:
    """(title, callout). A LADDER, and each rung states the population it measured.

    Rung 1 is the fact the fleet card puts at the top of a night run, measured the same way at
    one-session scale: the longest span nobody typed through. It is only allowed to be the
    headline when the agent was demonstrably working through it -- 8 minutes of ACTIVE time and
    at least 12 tool calls -- because "you left the room for an hour" is a gap, not a stretch,
    and a card that crowned it would be inflating in the flattering direction.

    The GATE is `active_s` (the agent's moving time). The NUMBER printed is `wall_s`, because the
    noun is "minutes without touching the keyboard" and that is a fact about the person, not about
    the agent's moving time. Printing `active_s` under that noun was a correct count of the wrong
    thing: the callout right below it prints both boundary timestamps, so on `grind-deep` the card
    said "52 minutes" over "14:40 ... 15:37", which is 57. Two correct numbers, adjacent, asserting
    a relation that does not hold -- caught 31 Aug by subtracting the two stamps the card itself
    prints. The trace band label is the same number, from the same field, for the same reason.

    And the number is computed from the two stamps AS PRINTED (`span_minutes` floors both to the
    minute, exactly as `%H:%M` does), not from raw seconds: rounding raw `wall_s` put "14 minutes"
    over "16:29 ... 16:44" on `grind-ordinary`, a one-minute version of the same defect. The rule
    is that the reader's own subtraction is the definition.
    """
    st = run.get("stretch")
    proj = run["project"]
    typed = run["turns_typed"]
    wall_m = max(span_minutes(run["started"], run["ended"]), 1)
    never = run["ship_states"]["never"]

    def _n(k, word):
        return f'{k} {word}' + ("" if k == 1 else "s")

    # RUNG 1 — the hands-off stretch. Two gates, not one. The second was added 31 Aug after
    # looking at six real grinds side by side: on an 11-minute oscar-site sitting the stretch was
    # 11 of 11 minutes, so "11 minutes without touching the keyboard" was a true sentence that
    # said only how long the session was. A headline has to distinguish this grind from the
    # session's own duration, so the stretch has to be a PART of the grind, not the whole of it.
    if st and st["active_s"] >= 480 and st["tool_calls"] >= 12:
        mins = span_minutes(st["start"], st["end"])
        if mins <= 0.85 * wall_m:
            t0 = datetime.fromisoformat(st["start"]).strftime("%H:%M")
            t1 = datetime.fromisoformat(st["end"]).strftime("%H:%M")
            bits = [f'<b>{st["tool_calls"]}</b> tool calls']
            if st["edits"]:
                bits.append(f'<b>{st["edits"]}</b> file edits')
            if st["commits"]:
                bits.append(f'<b>{st["commits"]}</b> commit{"" if st["commits"] == 1 else "s"} landed')
            return (f'{mins} minutes without touching the keyboard',
                    f'You typed at <b>{t0}</b> and did not type again until <b>{t1}</b>. In between: '
                    + ", ".join(bits) + " — and <b>0</b> prompts from you.")

    # RUNG 2 — LEVERAGE. One or two sentences typed, and the machine did a hundred things. This
    # is the sentence a short grind actually has and the old ladder threw away: a 10-minute
    # a one-prompt sitting was headlined "1 prompts, 4 files changed" (sic) when what
    # happened was one prompt and 104 tool calls.
    if typed and typed <= 3 and run["tool_calls"] >= 40 * typed:
        tail = ""
        if run["files_edited"]:
            tail = f' and changed {_n(run["files_edited"], "file")}'
        return (f'{_n(typed, "prompt")} → {run["tool_calls"]} tool calls',
                f'You typed <b>{typed}</b> time{"" if typed == 1 else "s"} in '
                f'<b>{wall_m}</b> minutes. The agent made <b>{run["tool_calls"]}</b> tool calls'
                + tail + '.')

    # RUNG 3 — the DNF. Files changed that nothing has committed since is the state Strava has no
    # word for and every builder recognises. It outranks a commit count because it is the rarer
    # fact: 1 sitting of the 625 on this machine has three or more of them
    # (`python3 scratchpad/shapes2.py`, 31 Aug 06:0x).
    if never >= 2 and never >= run["files_edited"] - 1:
        return (f'{_n(never, "file")} changed, nothing has committed {"it" if never == 1 else "them"} since',
                f'Asked of git file by file. <b>{run["commits"]}</b> commits were made during this '
                f'grind, and <b>{never}</b> of the <b>{run["files_edited"]}</b> files it changed '
                f'{"is" if never == 1 else "are"} in none of them, nor in any commit since.')

    # The plain fallbacks lead with the OUTCOME. Until 3 Sep they read "47 prompts → 3 commits",
    # "47 prompts, 12 files changed", "47 prompts on proj": the largest text on the card opened
    # with the cost. The prompt count is on the card, under COST, where a denominator belongs.
    if run["commits"]:
        return (f'{_n(run["commits"], "commit")} landed on {proj}',
                f'From <b>{typed}</b> typed prompt{"" if typed == 1 else "s"} in <b>{wall_m}</b> minutes.')
    if run["files_edited"]:
        return (f'{_n(run["files_edited"], "file")} changed in {proj}, no commit yet',
                f'From <b>{typed}</b> typed prompt{"" if typed == 1 else "s"} in <b>{wall_m}</b> minutes.')
    if run["files_touched"]:
        return (f'A reading grind — {run["files_touched"]} files opened, none changed', "")
    return (f'A grind on {proj} — no files opened, nothing committed',
            f'<b>{typed}</b> typed prompt{"" if typed == 1 else "s"} in <b>{wall_m}</b> minutes.')


def _practice_block(run: dict) -> str:
    items = run.get("practice_context") or []
    if not items:
        return ""
    parts = ['<section class="verdict"><div class="who">Your chosen practices · private</div>']
    for practice in items:
        parts.append(f'<p><b>{_esc(practice["title"])}</b></p>')
        if practice.get("expected"):
            parts.append(f'<p>What you expected: {_esc(practice["expected"])}</p>')
        attempts = practice.get("attempts") or []
        if attempts:
            latest = attempts[0]
            parts.append(f'<p>Last review: {_esc(latest.get("outcome") or "not reviewed yet")} · tried: {_esc(latest["tried"])}</p>')
        else:
            parts.append('<p>No attempt recorded yet.</p>')
    parts.append('</section>')
    return "".join(parts)


def _verdict_block(run: dict) -> str:
    """The coach's verdict and the series line. Null-safe: a run with neither draws nothing,
    a run with one draws that one. Every sentence here was written from tool results or from
    the local series, never from the transcript's prose. Paths never leave this block."""
    from .coach.experiment import public_text
    v = public_text(run.get("coach_verdict"))
    plan = public_text(run.get("coach_plan"))
    n = run.get("coach_tool_calls")
    prog = run.get("progress") or {}
    line = run.get("progress_line") or ""
    if not v and not line:
        return ""
    parts = ['<div class="verdict">']
    if v:
        by = (f"verdict produced by <b>{n}</b> tool call{'' if n == 1 else 's'}" if n
              else "verdict")
        mode = (run.get("coach_mode") or "").split(" (")[0]
        parts.append(f'<div class="who">The coach: {by}' + (f' · {_esc(mode)}' if mode else '') + '</div>')
        parts.append(f'<div>{_esc(v)}</div>')
        if plan:
            items = "".join(f"<li>{_esc(p)}</li>" for p in str(plan).splitlines() if p.strip())
            parts.append(f'<ul>{items}</ul>')
    if line:
        pred = prog.get("prediction")
        # the line already leads with its verdict word; bold that word instead of repeating it
        head, _, rest = line.partition(" ")
        parts.append(f'<div class="prog"><b>{_esc(head)}</b> {_esc(rest)}'
                     + (f'<div class="pred">you predicted: {_esc(pred)}</div>' if pred else '') + '</div>')
    parts.append('</div>')
    return "".join(parts)


def _avatar(run: dict) -> str:
    """The author's GitHub avatar when this run carries an account, a neutral disc when it does
    not. Never an initial taken from a placeholder word: the old card drew a "Y" over "you"."""
    from .identity import of_run
    who = of_run(run)
    if who.signed_in:
        return (f'<img class="av" src="{who.avatar_url}" alt="" width="38" height="38" '
                f'loading="lazy">')
    return '<div class="av none" aria-hidden="true"></div>'


def _photo_hero(photo_src: str | None, h_title: str, pill: str) -> str:
    """The headline, on the author's photo when there is one. The line under the photo says
    what it is: added by the author, not measured, location and camera data removed."""
    if not photo_src:
        return f"<h1>{h_title}{pill}</h1>"
    return (f'<figure class="photo"><img src="{photo_src}" alt="Photo added by the author">'
            f'<h1>{h_title}{pill}</h1></figure>'
            f'<div class="decl">Photo added by you, not measured. '
            f'Location and camera data removed before this card was drawn.</div>')


def render_solo_card(run: dict, title: str | None = None, ranks: dict | None = None,
                     photo_src: str | None = None) -> str:
    from . import runviz

    # OPT-IN ON THIS CARD. The grind trace below is already this card's hero, so a visual only
    # appears here when the author named one (`grind --hero`). The quote, gear chip and trophies
    # are absent by default like every other declared field.
    chosen_visual = runviz.picked_hero_html(run)
    components = runviz.components_html(run)
    svg, m = render_route_svg(run)
    # The SAME numbers in a layout a 390px screen can hold: see soloroute.Geo for the measurement
    # that forced two layouts rather than one responsive drawing.
    psvg, _pm = render_phone_svg(run)
    t0 = datetime.fromisoformat(run["started"])
    t1 = datetime.fromisoformat(run["ended"])
    a = run["authorship"]
    cats = a["by_category"]
    naive = a["user_records_total"]
    # the honest paragraph can only be checked if its parts add up to the number it corrects
    assert sum(cats.values()) == naive, (cats, naive)
    assert cats["human"] == run["turns_typed"], (cats["human"], run["turns_typed"])
    pct = 100 * cats["human"] / naive if naive else 0

    from .history import badge as _badge, best_rank as _best
    bdg = _badge(ranks) if ranks else None
    br = _best(ranks) if ranks else None
    pill = (f'<span class="pb" title="{bdg[1]}">★ {bdg[0]} · {bdg[1]}</span>' if bdg else "")
    prog = ""
    if br:
        prog = (f'<div class="prog">This is your <b>#{br[0]}</b> grind of <b>{br[1]:,}</b> on this '
                f'machine by {br[2]}. <span class="q">Ranked against every Claude Code sitting '
                f'on this machine, split by the same 30-minute idle rule — '
                f'<span class="mono">agentgrinder history</span>.</span></div>')
    from .identity import of_run
    who = of_run(run)
    note = f" · {who.note}" if who.note else ""
    h_title, callout = headline(run)
    h_title = title or h_title
    hl = headline_of(run)          # verified per turn, or a dash that names what is missing
    tip = ARTIFACTS_PER_TURN_TIP if hl.metric_id == "artifacts_per_turn" else HEADLINE_TIP
    five = _five_block(hl.five)
    pace = (run["duration_s"] / run["turns_typed"]) if run["turns_typed"] else None
    per_prompt = (run["tool_calls"] / run["turns_typed"]) if run["turns_typed"] else None
    sit = run["sitting"]
    date_line = f'{t0.strftime("%a %d %b %Y")} · {t0.strftime("%H:%M")} → {t1.strftime("%H:%M")}'
    # The subtitle used to quote the first prompt the author typed, always. That sentence is a
    # keystroke log, and it reached shipped screenshots verbatim. It is now printed only when the
    # run says it was explicitly opted in (`grind --show-paths`), and `privacy.safe_prompt` has
    # already refused it if it carries a path.
    prompt = _esc(run["title"]) if run.get("prompt_shown") else ""

    # ---- WHAT SHIPPED: three states, each one a question git can be asked about a file.
    # The first version of this block asked only "is it in a commit inside the window", which on
    # a real repo C grind called four files dead ends that were all committed 41 minutes after
    # the window closed. A window boundary is an arbitrary line through a working day; the state
    # a reader cares about is whether anything has committed the file SINCE they changed it.
    dead = run["deadends"]
    st_ = run["ship_states"]
    assert sum(st_.values()) == run["files_edited"], (st_, run["files_edited"])
    dead_line = ""
    if run["files_edited"] and run["git"]["root"]:
        later = run.get("later") or []
        parts = []
        if st_["shipped"]:
            parts.append(f'<b>{st_["shipped"]}</b> landed in the <b>{run["commits"]}</b> '
                         f'commit{"" if run["commits"] == 1 else "s"} made during it')
        if st_["later"]:
            when = datetime.fromisoformat(later[0]["at"]).strftime("%H:%M") if later else ""
            parts.append(f'<b>{st_["later"]}</b> {"was" if st_["later"] == 1 else "were"} '
                         f'committed after it closed'
                         + (f' (first at <b>{when}</b>)' if when else ""))
        if st_["unasked"]:
            parts.append(f'<b>{st_["unasked"]}</b> {"is" if st_["unasked"] == 1 else "are"} outside '
                         f'{_esc(run["project"])} or git-ignored, so git was never asked')
        if st_["never"]:
            shown = ", ".join(f"<code>{_esc(d)}</code>" for d in dead[:4])
            parts.append(f'<b>{st_["never"]}</b> nothing has committed since'
                         + (f': {shown}' if shown else "") + (" …" if len(dead) > 4 else ""))
        klass = "dead" if st_["never"] else "dead ok"
        total = " + ".join(str(st_[k]) for k in ("shipped", "later", "unasked", "never") if st_[k])
        _n_ed = run["files_edited"]
        dead_line = (f'<div class="{klass}"><b>{_n_ed}</b> file{"" if _n_ed == 1 else "s"} '
                     f'{"was" if _n_ed == 1 else "were"} edited in this '
                     f'grind. ' + "; ".join(parts) + f'. <span class="q">Asked of git per file — '
                     f'<span class="mono">git log --all --reverse -- &lt;file&gt;</span>. '
                     f'Disjoint, and they add up: <b>{total} = {run["files_edited"]}</b>.</span></div>')

    commits_src = ("git log --all --name-only" if run["git"]["root"]
                   else run["git"]["reason"] or "no git work tree")
    # A cost the grind did not measure is left out of the row entirely. An untimed harness used
    # to draw "—" under Moving time and Pace, two empty boxes beside two real numbers.
    cost_cells = [
        f'<div class="stat"><div class="v">{value}</div><div class="k">{label}</div>'
        f'<div class="src">{source}</div></div>'
        for value, label, source in [
            (run["turns_typed"], "Prompts · cost", "promptSource typed|queued"),
            (_dur(run["duration_s"]), "Moving time", "gaps capped at 20m"),
            (_pace(pace), "Pace /prompt", "moving time ÷ prompts"),
            (run["commits"], "Commits", f"{commits_src}, during the grind"),
        ] if _has_value(value)]
    cost = (f'<div class="stats" data-n="{len(cost_cells)}">{"".join(cost_cells)}</div>'
            if cost_cells else "")
    n_rows = len(run["rows"]) + (1 if (run.get("more") or {}).get("files") else 0)
    more = run.get("more") or {}
    trace_note = (f'one row per file · {run["files_touched"]} opened, {run["files_edited"]} changed'
                  + (f' · {more["files"]} folded into the last row' if more.get("files") else ""))

    # A LEGEND ONLY EXPLAINS MARKS THAT ARE ON THIS CARD. It printed all eight keys on every
    # grind until 31 Aug, so `grind-reading` — a sitting with `files_read == 0` — carried a key
    # for a mark class it does not draw. A legend entry is a sentence about the drawing, and a
    # sentence about a mark that is not there is the same defect as a number the source denies.
    _more = run.get("more") or {}
    _rows = run["rows"]
    _has_read = run["files_read"] > 0
    _has_edit = run["files_edited"] > 0
    _has_flag = any(r.get("shipped") for r in _rows) or run["commits"] > 0
    _has_late = st_["later"] > 0
    _has_dead = st_["never"] > 0
    legend = "".join(x for x in [
        '<span><i class="st"></i>a prompt you typed</span>' if run["typed_stamps"] else "",
        '<span><i class="sp"></i>the path the work took between files</span>' if len(_rows) > 1 else "",
        '<span><i class="se"></i>edited</span>' if _has_edit else "",
        '<span><i class="sr"></i>read</span>' if _has_read else "",
        ('<span><i class="sf"></i>commit — on the row of every file git says it contains</span>'
         if _has_flag else ""),
        '<span><i class="sl"></i>committed after the grind closed</span>' if _has_late else "",
        '<span><i class="sd"></i>edited, nothing has committed it since</span>' if _has_dead else "",
        ('<span><i class="sg"></i>the longest span nobody typed through</span>'
         if (m["band"] and not m["band"]["full"]) else ""),
    ] if x)

    tally = "".join(
        f'<li><b>{cats[c]:,}</b> {lab}</li>' for c, lab in (
            ("tool_result", "tool results — a tool's output returning to the agent that called it"),
            ("injected", "injected context — skill bodies, pasted-image notices"),
            ("orchestrator", "prompts a parent session wrote to a subagent"),
            ("harness", "harness envelopes — slash-command expansions, notifications, interrupts"),
        ) if cats[c])

    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(who.display)} · {h_title} — {BRAND}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  {CARD_THEME}

  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--ink);padding:26px 14px;display:flex;
    justify-content:center;font:15px/1.55 "IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
  .card{{width:100%;max-width:1040px;background:var(--card);border:1px solid var(--line);
    border-radius:2px;overflow:hidden;box-shadow:none}}
  .top{{display:flex;align-items:center;gap:12px;padding:18px 22px 8px}}
  .av{{width:38px;height:38px;border-radius:50%;background:var(--accent);color:#fff;font-weight:800;
    display:grid;place-items:center;font-size:17px;object-fit:cover;flex:0 0 auto}}
  .av.none{{background:var(--line)}}
  .who b{{font-weight:700}}
  .who small{{display:block;color:var(--faint);font-size:11.5px;white-space:nowrap;
    font-family:"IBM Plex Sans",system-ui,sans-serif}}
  .brand{{margin-left:auto;font-weight:800;letter-spacing:.13em;color:var(--faint);font-size:11px}}
  h1{{margin:6px 22px 2px;font-size:27px;line-height:1.16;letter-spacing:-.018em;font-weight:800}}
  .pb{{display:inline-block;vertical-align:middle;margin-left:11px;font-size:11px;font-weight:700;
    color:var(--accent);border:1px solid var(--accent);border-radius:999px;padding:3px 10px;
    font-family:"IBM Plex Sans",system-ui,sans-serif;letter-spacing:.02em;white-space:nowrap}}
  .prog{{padding:8px 22px 0;font-size:12.5px;color:var(--muted)}}
  .prog b{{color:var(--ink);font-family:"IBM Plex Sans",system-ui,sans-serif}}
  .prog .q{{color:var(--faint)}}
  .prog .mono{{font-family:"IBM Plex Sans",system-ui,sans-serif}}
  .sub{{padding:0 22px 4px;color:var(--muted);font-size:13px}}
  .sub .q{{color:var(--faint);font-style:italic}}
  .callout{{margin:14px 22px 0;padding:12px 15px;border-left:3px solid var(--accent);
    background:var(--bg);font-size:13.5px;line-height:1.62;color:var(--muted)}}
  .callout b{{color:var(--ink);font-family:"IBM Plex Sans",system-ui,sans-serif;font-weight:700}}
  .hl{{display:flex;align-items:baseline;gap:14px;padding:14px 22px 10px;cursor:help}}
  .hl .n{{font:800 46px/1 "IBM Plex Sans",system-ui,sans-serif;letter-spacing:-.04em;color:var(--accent)}}
  .hl .lbl{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.12em}}
  .hl .f{{display:block;font-size:12px;color:var(--faint);text-transform:none;letter-spacing:0;
    font-family:"IBM Plex Sans",system-ui,sans-serif}}
{GRID_CSS}
  .five{{background:var(--card);padding:10px 8px 9px;text-align:center;cursor:help}}
  .five .v{{font:700 15px/1.2 "IBM Plex Sans",system-ui,sans-serif;letter-spacing:-.01em;white-space:nowrap}}
  .five .k{{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;
    margin-top:3px;line-height:1.25}}
  .five[data-missing] .v{{color:var(--muted);font-weight:400}}
  .five.cost .v{{color:var(--muted)}}
  .costtag{{font-style:normal;display:inline-block;margin-left:4px;padding:0 4px;border-radius:4px;
    background:var(--line);color:var(--muted);font-size:9px;letter-spacing:.04em}}
  .grp{{padding:12px 22px 0;font-size:10.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.14em}}
  .unmeasured{{margin:0;padding:10px 22px;color:var(--faint);font-size:12px;line-height:1.5}}
  .unmeasured span{{border-bottom:1px dotted var(--line);cursor:help}}
  .verdict{{padding:10px 22px 4px;font-size:13.5px;line-height:1.55}}
  .verdict .who{{font-size:10.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.14em;margin-bottom:4px}}
  .verdict .who b{{color:var(--ink);font-family:"IBM Plex Sans",system-ui,sans-serif;text-transform:none;letter-spacing:0}}
  .verdict ul{{margin:6px 0 0;padding-left:18px}} .verdict li{{margin:2px 0}}
  .verdict .prog{{margin:8px 0 0;padding:8px 10px;border-left:3px solid var(--accent);background:var(--card);
    color:var(--muted);font-size:12.5px}} .verdict .prog b{{color:var(--ink)}}
  .verdict .pred{{color:var(--faint);font-style:italic}}
  .stats{{margin-top:8px}}
  .stat{{background:var(--card);padding:14px 18px}}
  .stat .v{{font:700 25px/1.1 "IBM Plex Sans",system-ui,sans-serif;letter-spacing:-.02em}}
  .stat .k{{font-size:10.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-top:4px}}
  .stat .src{{font-size:10.5px;color:var(--faint);margin-top:5px;
    font-family:"IBM Plex Sans",system-ui,sans-serif}}
  .maphead{{display:flex;align-items:baseline;gap:14px;padding:18px 22px 0;flex-wrap:wrap}}
  .maphead h2{{margin:0;font-size:11px;text-transform:uppercase;letter-spacing:.14em;color:var(--muted)}}
  .maphead .note{{font-size:11.5px;color:var(--faint);
    font-family:"IBM Plex Sans",system-ui,sans-serif}}
  .mapwrap{{padding:6px 22px 4px;overflow-x:auto}}
  .mapwrap.phonewrap{{display:none;overflow:visible}}
  svg.routemap{{display:block;width:100%;min-width:620px;height:auto}}
  svg.routemap.phone{{min-width:0}}
  .grid{{stroke:var(--grid);stroke-width:1}}
  .stretch{{fill:var(--accent);opacity:.065}}
  .slabel{{fill:var(--accent);font:700 10.5px "IBM Plex Sans",system-ui,sans-serif;letter-spacing:.04em}}
  .trunk{{stroke:var(--ink);stroke-width:1.5}}
  .tick{{stroke:var(--ink);stroke-width:2;opacity:.85}}
  .tlabel{{fill:var(--ink);font:700 13px "IBM Plex Sans",system-ui,sans-serif}}
  .hair{{stroke:var(--line);stroke-width:1}}
  .path{{fill:none;stroke:var(--accent);stroke-width:1.05;opacity:.3;stroke-linejoin:round}}
  .hair.faint{{opacity:.6}}
  .mark{{stroke-linecap:round}}
  .mark.edit{{stroke:var(--accent);stroke-width:5.5;opacity:.95}}
  .mark.read{{stroke:var(--muted);stroke-width:2.2;opacity:.55}}
  .mark.faint{{opacity:.3}}
  .cap.ship{{fill:var(--ship)}}
  .cap.spur{{fill:var(--card);stroke:var(--accent);stroke-width:1.5;opacity:.9}}
  .cap.late{{fill:var(--card);stroke:var(--ship);stroke-width:1.5;opacity:.8}}
  .flag{{stroke:var(--ship);stroke-width:1.6}}
  .pennant{{fill:var(--ship)}}
  .rtag{{fill:var(--ink);font:700 11.5px "IBM Plex Sans",system-ui,sans-serif}}
  .rtag.faint{{fill:var(--faint);font-weight:400}}
  .rnote{{fill:var(--faint);font-weight:400}}
  .gl{{fill:var(--faint);font:10px "IBM Plex Sans",system-ui,sans-serif}}
  .profill{{fill:var(--accent);opacity:.13}}
  .profline{{fill:none;stroke:var(--accent);stroke-width:1.6;stroke-linejoin:round}}
  .base{{stroke:var(--line);stroke-width:1}}
  .plabel{{fill:var(--muted);font:11px "IBM Plex Sans",system-ui,sans-serif}}
  .pmax{{fill:var(--faint);font:10px "IBM Plex Sans",system-ui,sans-serif}}
  .legend{{display:flex;flex-wrap:wrap;gap:15px;padding:2px 22px 16px;font-size:11.5px;
    color:var(--muted);font-family:"IBM Plex Sans",system-ui,sans-serif}}
  .legend i{{display:inline-block;vertical-align:middle;margin-right:6px;font-style:normal}}
  .se{{width:22px;height:0;border-top:5px solid var(--accent);display:inline-block;vertical-align:middle}}
  .sp{{width:22px;height:0;border-top:1.5px solid var(--accent);opacity:.4;display:inline-block;vertical-align:middle}}
  .sr{{width:22px;height:0;border-top:2px solid var(--muted);opacity:.6;display:inline-block;vertical-align:middle}}
  .st{{width:2px;height:13px;background:var(--ink);display:inline-block;vertical-align:middle}}
  .sf{{width:0;height:0;border-left:8px solid var(--ship);border-top:4px solid transparent;
    border-bottom:4px solid transparent;display:inline-block;vertical-align:middle}}
  .sd{{width:8px;height:8px;border:1.5px solid var(--accent);border-radius:50%;
    display:inline-block;vertical-align:middle;background:var(--card)}}
  .sl{{width:8px;height:8px;border:1.5px solid var(--ship);border-radius:50%;
    display:inline-block;vertical-align:middle;background:var(--card)}}
  .sg{{width:16px;height:11px;background:var(--accent);opacity:.14;display:inline-block;vertical-align:middle}}
  .dead{{margin:0 22px 16px;padding:11px 14px;border-left:3px solid var(--accent);background:var(--bg);
    font-size:12.5px;color:var(--muted);line-height:1.6}}
  .dead.ok{{border-left-color:var(--ship)}}
  .dead b{{color:var(--ink);font-family:"IBM Plex Sans",system-ui,sans-serif}}
  .dead .mono{{font-family:"IBM Plex Sans",system-ui,sans-serif}}
  .dead code{{font-family:"IBM Plex Sans",system-ui,sans-serif;font-size:11.5px;color:var(--ink)}}
  .dead .q{{color:var(--faint)}}
  .honest{{background:var(--bg);border-top:1px solid var(--line);padding:15px 22px;
    font-size:12px;color:var(--muted);line-height:1.65}}
  .honest b{{color:var(--ink);font-family:"IBM Plex Sans",system-ui,sans-serif;font-weight:700}}
  .honest .mono{{font-family:"IBM Plex Sans",system-ui,sans-serif}}
  ul.tally{{margin:8px 0;padding-left:0;list-style:none}}
  ul.tally li{{padding:2px 0 2px 14px;border-left:2px solid var(--line);margin-bottom:3px}}
  .repro{{display:block;margin-top:9px;color:var(--faint);font-size:11px;
    font-family:"IBM Plex Sans",system-ui,sans-serif;word-break:break-all}}
  .foot{{display:flex;align-items:center;gap:8px;padding:13px 22px;border-top:1px solid var(--line);
    color:var(--muted);font-size:12.5px}}
  .foot .tag{{margin-left:auto;font-family:"IBM Plex Sans",system-ui,sans-serif;color:var(--faint)}}
  /* Below 760 the desktop trace is retired outright and the phone layout takes over. It was
     kept, scaled and scrolled, until 31 Aug: measured in a real 390px iframe, that put 14 of
     grind-deep's file-path labels outside the scroller at the card's own opening scroll. */
  /* THE RUN PHOTO: declared by the author, never measured. The headline sits on it. */
  .photo{{position:relative;margin:4px 0 0;line-height:0}}
  .photo img{{display:block;width:100%;max-height:560px;object-fit:cover}}
  .photo h1{{position:absolute;left:0;right:0;bottom:0;margin:0;padding:64px 22px 16px;color:#fff;
    line-height:1.15;background:linear-gradient(to top,rgba(0,0,0,.62),rgba(0,0,0,0))}}
  .decl{{padding:7px 22px 0;line-height:1.4;font-size:11px;color:var(--faint);
    font-family:"IBM Plex Sans",system-ui,sans-serif}}
  @media (max-width:760px){{
    #mapwrap{{display:none}}
    .mapwrap.phonewrap{{display:block}}
    svg.routemap.phone .rtag{{font-size:10px}}
    svg.routemap.phone .rnote{{font-size:9px}}
    svg.routemap.phone .tlabel{{font-size:11px}}
    svg.routemap.phone .gl{{font-size:9px}}
    svg.routemap.phone .plabel{{font-size:9.5px}}
    svg.routemap.phone .pmax{{font-size:9px}}
    svg.routemap.phone .slabel{{font-size:9.5px}}
    svg.routemap.phone .mark.edit{{stroke-width:4.2}}
    svg.routemap.phone .mark.read{{stroke-width:1.8}}
  }}
  @media (max-width:640px){{
    body{{padding:12px 8px}}
    .av{{flex:0 0 auto;width:34px;height:34px;font-size:15px}}
    .who{{min-width:0}} .who small{{font-size:10px}}
    .brand{{flex:0 0 auto;font-size:9.5px;letter-spacing:.1em}}
    .top{{gap:9px}}
    .hl{{padding-left:14px;padding-right:14px}} .hl .n{{font-size:36px}} .grp{{padding-left:14px}}
    h1{{font-size:20px}} .stat .v{{font-size:21px}}
    .top,.sub,h1,.mapwrap,.maphead,.legend,.honest,.foot,.callout,.dead,.decl{{padding-left:14px;padding-right:14px}}
    .callout,.dead{{margin-left:14px;margin-right:14px;padding-left:12px;padding-right:12px}}
  }}
{runviz.CSS}
</style></head>
<body>
  <div class="card">
    <div class="top">
      {_avatar(run)}
      <div class="who"><b>{_esc(who.display)}</b><small>{date_line}{_esc(note)}</small></div>
      <div class="brand">{BRAND}</div>
    </div>
    {_photo_hero(photo_src, h_title, pill)}
    <div class="sub">{run["harness"]} · {_esc(run["project"])} ·
      sitting {sit["index"]} of {sit["of"]} in this transcript
      {f'<span class="q">— “{prompt}”</span>' if prompt else ''}</div>
    {f'<div class="callout">{callout}</div>' if callout else ''}
    {prog}
    {chosen_visual}{components}

    <div class="hl" title="{_esc(tip)} · {_esc(hl.formula)}">
      <div class="n">{hl.text}</div>
      <div class="lbl">{_esc(hl.label)}<span class="f">{_esc(hl.formula)}</span></div>
    </div>
    {five}
    {_unmeasured_note(hl.five)}
    {_verdict_block(run)}
    {_practice_block(run)}

    <div class="grp">Cost — what the grind spent</div>
    {cost}

    <div class="maphead"><h2>The grind trace</h2>
      <span class="note">{trace_note} · peak {m["peak_per_min"]:.0f} tool calls/min</span></div>
    <div class="mapwrap" id="mapwrap" data-focus="{m["focus"] / 1000.0:.4f}">{svg}</div>
    <div class="mapwrap phonewrap">{psvg}</div>
    <div class="legend">{legend}</div>
    {dead_line}

    <div class="honest">
      <b>Authorship.</b> This sitting holds <b>{naive:,}</b> records of
      <b>type:&#8203;user</b>. <b>{cats["human"]}</b> of them ({pct:.1f}%) were typed by a person —
      the gate is <span class="mono">promptSource</span> <b>typed</b> or <b>queued</b>, dropping
      injected and sidechain records, which is Transcripto's measured signal, not a rule invented
      here. The rest were sorted by what the record actually contains:
      <ul class="tally">{tally}</ul>
      Disjoint, and they add up — the only way you can check them:
      <b>{" + ".join(f"{cats[c]:,}" for c in CATEGORIES if cats[c])} = {naive:,}</b>.
      A counter that trusted <b>type:&#8203;user</b> would print <b>{naive:,} prompts</b>
      where this card prints <b>{cats["human"]}</b>.
      <span class="repro">{COMMAND.replace("authorship --since &lt;ISO&gt;", "authorship")}</span>
    </div>

    <div class="foot"><span>Grind in public. Ship with proof.</span>
      <span class="tag">{run["tool_calls"]:,} tool calls · {per_prompt:.0f} per prompt · {run["bash"]} shell</span></div>
  </div>
<script>
  // A trace wider than the screen opens on its own left edge, which on most grinds is the
  // minutes before anything happened. Open it where the work is instead.
  (function () {{
    var w = document.getElementById("mapwrap");
    if (!w) return;
    var f = parseFloat(w.getAttribute("data-focus"));
    if (!(f > 0)) return;
    var over = w.scrollWidth - w.clientWidth;
    if (over > 8) w.scrollLeft = Math.max(0, f * w.scrollWidth - w.clientWidth * 0.30);
  }})();
</script>
</body></html>'''


# ---------------------------------------------------------------------------------------------
# THE CONTROL, ON THE WAY OUT
#
# Every card this module produces is scanned before it is returned. Not the source it was built
# from -- the finished HTML, which is the artefact a person opens and a screenshot is taken of.
# A leak that survives the renderer therefore cannot reach a file: the call raises.
#
# This wrapper exists because the previous privacy pass fixed the wrong object. It did not change
# the renderer at all; it CHOSE six sessions whose row labels happened to be repo-relative
# (scratchpad/clean.py filters 625 sittings down to the 169 that were already safe) and re-shot
# those. The product was unchanged, and any user grinding on a seventh session got the old
# behaviour. A control that runs on the output cannot be satisfied by picking nicer input.
# ---------------------------------------------------------------------------------------------

_render_unchecked = render_solo_card


def render_solo_card(*a, photo_src: str | None = None, **kw) -> str:
    # The privacy control reads every character of the card. A base64 image is bytes, not text a
    # reader sees, and random base64 can spell a pattern by chance, so the control runs on the card
    # with a placeholder where the image goes, and the image is put in after it passes. The photo
    # itself was cleaned in photo.load_photo, which is where its own private data lives.
    token = "agentgrinder-photo-placeholder" if photo_src else None
    html = _render_unchecked(*a, photo_src=token, **kw)
    privacy.assert_clean(html, where="render_solo_card")
    return html.replace(token, photo_src) if token else html
