"""Render an Activity to a shareable HTML card.

Signature device: THE SESSION ROUTE — the run's rhythm (typed turns per bucket) drawn as an
elevation profile, the way Strava draws a route. It is taken from the work itself, not a component
library: the shape IS the session. Remove it and you lose the argument that this was a real effort.

Headline: VERIFIED PER TURN — what the typed turns bought, never how many there were. The five
numbers of a run sit under it in one row; every Strava-shaped number (prompts, moving time, pace,
effort, cadence) is kept, grouped as COST. A dash carries a tooltip naming the tool that owns it.
"""
from __future__ import annotations
from .brand import CARD_THEME

from html import escape

from .metrics import ARTIFACTS_PER_TURN_TIP, HEADLINE_TIP, Activity, Cell


def _route_svg(rhythm: list[int], w: int = 720, h: int = 150) -> str:
    if not rhythm:
        return f'<svg viewBox="0 0 {w} {h}" class="route" role="img" aria-label="no route"></svg>'
    n = len(rhythm)
    mx = max(rhythm) or 1
    pad = 6
    def x(i): return pad + i * (w - 2 * pad) / max(n - 1, 1)
    def y(v): return h - pad - (v / mx) * (h - 2 * pad)
    pts = [(x(i), y(v)) for i, v in enumerate(rhythm)]
    line = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    area = f"{pad},{h - pad} " + line + f" {w - pad:.1f},{h - pad}"
    # peak marker = the hardest stretch of the session
    pi = rhythm.index(max(rhythm))
    return f'''<svg viewBox="0 0 {w} {h}" class="route" preserveAspectRatio="none" role="img" aria-label="session route">
  <polygon points="{area}" fill="url(#grad)"/>
  <polyline points="{line}" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linejoin="round"/>
  <circle cx="{x(pi):.1f}" cy="{y(rhythm[pi]):.1f}" r="4.5" fill="var(--accent)" stroke="var(--card)" stroke-width="2"/>
  <defs><linearGradient id="grad" x1="0" x2="0" y1="0" y2="1">
    <stop offset="0" stop-color="var(--accent)" stop-opacity="0.28"/>
    <stop offset="1" stop-color="var(--accent)" stop-opacity="0.02"/>
  </linearGradient></defs>
</svg>'''


def _five_row(cells: list[Cell]) -> str:
    out = []
    for c in cells:
        cls = "five cost" if c.cost else "five"
        tag = '<i class="costtag">cost</i>' if c.cost else ""
        dash = ' data-missing="1"' if c.value.startswith("—") or " —" in c.value else ""
        out.append(f'<div class="{cls}" title="{escape(c.source)}"{dash}>'
                   f'<div class="v">{escape(c.value)}</div>'
                   f'<div class="k">{escape(c.label)}{tag}</div></div>')
    return "".join(out)


def render_card(a: Activity) -> str:
    from dataclasses import replace, fields
    a = replace(a, **{f.name: escape(getattr(a, f.name)) for f in fields(a) if isinstance(getattr(a, f.name), str)})
    initial = (a.athlete or "?")[0].upper()
    pb = '<span class="pb" title="high sustained cadence">High cadence</span>' if a.focus_pb else ""
    if a.trace:
        from .native_trace import svg
        route = svg(a.trace, a.trace_basis)
    else:
        route = _route_svg(a.rhythm) + ("<small>" + a.trace_basis + "</small>" if a.trace_basis else "")
    five = _five_row(a.five)
    coach = (f'<section style="padding:20px"><h2>Next session</h2><small>{a.coach_mode}</small><p>{a.coach_verdict}</p><p style="white-space:pre-wrap">{a.coach_plan}</p></section>' if a.coach_verdict else "")
    tip = (ARTIFACTS_PER_TURN_TIP if a.headline_metric_id == "artifacts_per_turn"
           else HEADLINE_TIP)
    hl_title = escape(tip) + " · " + escape(a.headline_formula)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{a.athlete} · {a.title} — AGENTGRINDER</title>
<style>
  {CARD_THEME}

  *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);
    font:15px/1.5 "IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    display:flex;justify-content:center;padding:28px 16px}}
  .card{{width:100%;max-width:560px;background:var(--card);border:1px solid var(--line);
    border-radius:2px;overflow:hidden;box-shadow:none}}
  .top{{display:flex;align-items:center;gap:12px;padding:18px 20px 12px}}
  .avatar{{width:42px;height:42px;border-radius:50%;background:var(--accent);color:#fff;
    display:grid;place-items:center;font-weight:700;font-size:18px}}
  .who b{{font-weight:650}} .who small{{color:var(--muted);display:block;font-size:12.5px}}
  .brand{{margin-left:auto;font-weight:800;letter-spacing:.06em;color:var(--muted);font-size:12px}}
  .title{{padding:0 20px 4px;font-size:19px;font-weight:680;display:flex;align-items:center;gap:10px}}
  .pb{{font-size:11px;font-weight:700;color:var(--accent);border:1px solid var(--accent);
    border-radius:999px;padding:2px 8px}}
  .sub{{padding:0 20px 14px;color:var(--muted);font-size:13px}}
  .hl{{display:flex;align-items:baseline;gap:14px;padding:6px 20px 12px}}
  .hl .n{{font-size:44px;font-weight:800;letter-spacing:-.03em;line-height:1;color:var(--accent)}}
  .hl .lbl{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}}
  .hl .f{{display:block;font-size:12px;color:var(--muted);text-transform:none;letter-spacing:0}}
  .fiverow{{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:var(--line);
    border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}
  .five{{background:var(--card);padding:10px 8px 9px;text-align:center;cursor:help}}
  .five .v{{font-size:15px;font-weight:700;letter-spacing:-.01em;white-space:nowrap}}
  .five .k{{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;
    margin-top:2px;line-height:1.25}}
  .five[data-missing] .v{{color:var(--muted);font-weight:500}}
  .five.cost .v{{color:var(--muted)}}
  .costtag{{font-style:normal;display:inline-block;margin-left:4px;padding:0 4px;border-radius:4px;
    background:var(--line);color:var(--muted);font-size:9px;letter-spacing:.04em}}
  .grp{{padding:10px 20px 4px;font-size:10.5px;color:var(--muted);text-transform:uppercase;
    letter-spacing:.08em}}
  .stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);
    border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}
  @media (max-width:420px){{.fiverow{{grid-template-columns:repeat(2,1fr)}}.five:nth-child(5){{grid-column:span 2}}.hl .n{{font-size:36px}}
    .stat .v{{font-size:17px}}}}
  .stat{{background:var(--card);padding:14px 16px}}
  .stat .v{{font-size:22px;font-weight:720;letter-spacing:-.01em}}
  .stat .k{{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}}
  .route{{display:block;width:100%;height:150px;background:
    linear-gradient(var(--card),var(--card))}}
  .routewrap{{border-bottom:1px solid var(--line)}}
  .sec{{display:flex;flex-wrap:wrap;gap:18px;padding:14px 20px;font-size:13px}}
  .sec div b{{font-weight:650}} .sec div span{{color:var(--muted)}}
  .foot{{display:flex;align-items:center;gap:16px;padding:12px 20px;border-top:1px solid var(--line);
    color:var(--muted);font-size:13px}}
  .kudo{{display:flex;align-items:center;gap:6px}} .kudo b{{color:var(--ink)}}
</style></head>
<body>
  <div class="card">
    <div class="top">
      <div class="avatar">{initial}</div>
      <div class="who"><b>{a.athlete}</b><small>{a.date_str}</small></div>
      <div class="brand">AGENTGRINDER</div>
    </div>
    <div class="title">{a.title} {pb}</div>
    <div class="sub">{a.harness}{" · bot activity" if a.harness == "Grok Bot" else ""} · {a.project}</div>
    <div class="hl" title="{hl_title}">
      <div class="n">{a.headline}</div>
      <div class="lbl">{a.headline_label}<span class="f">{escape(a.headline_formula)}</span></div>
    </div>
    <div class="fiverow">{five}</div>
    <div class="routewrap">{route}</div>
    <div class="grp">Cost — what the run spent</div>
    <div class="stats">
      <div class="stat"><div class="v">{a.distance}</div><div class="k">Typed turns</div></div>
      <div class="stat"><div class="v">{a.moving_time}</div><div class="k">Moving time</div></div>
      <div class="stat"><div class="v">{a.pace}</div><div class="k">Pace</div></div>
    </div>
    {"" if a.moving_time != "—" or not a.trace_basis else '<p class="grp" style="text-transform:none;letter-spacing:0;padding-top:0">Moving time, pace and cadence are unavailable: this harness trace is turn order, not a measured elapsed clock.</p>'}
    <div class="sec">
      <div><span>Effort</span><br><b>{a.effort}</b></div>
      <div><span>Segments</span><br><b>{a.segments}</b></div>
      <div><span>Commits</span><br><b>{a.commits}</b></div>
      <div><span>Cadence</span><br><b>{a.prompts_per_hour}</b></div>
    </div>
    {coach}
    <div class="foot">
      <div class="kudo">🔥 <b>kudos</b></div>
      <div class="kudo">💬 comment</div>
      <div style="margin-left:auto">Push loops. Ship proof.</div>
    </div>
  </div>
</body></html>'''


def render_profile(p: dict) -> str:
    gh = p["gh"]; t = p["totals"]; acts = p["activities"]
    def stat(v): return v if v not in (None, "") else "—"
    cards = "".join(f'''
      <a class="runrow" href="#">
        <div class="rt">{a.title}</div>
        <div class="rm"><span class="hl" title="{escape(ARTIFACTS_PER_TURN_TIP if a.headline_metric_id=='artifacts_per_turn' else HEADLINE_TIP)} · {escape(a.headline_formula)}">{a.headline} {a.headline_label}</span>
          <span class="cost">{a.distance} · cost</span><span>{a.moving_time}</span><span>{a.pace}</span>
          <span>{a.commits} commits</span>{" <span class='pb'>★ PB</span>" if a.focus_pb else ""}</div>
        <div class="rs">{a.harness}{" · bot activity" if a.harness == "Grok Bot" else ""} · {a.project} · {a.date_str}</div>
      </a>''' for a in acts) or '<div class="empty">No runs yet — <code>agentgrinder run</code> to log one.</div>'
    repos = "".join(f"<li>{r}</li>" for r in gh.get("recent_repos", [])) or "<li>—</li>"
    initial = (gh.get("name") or "?")[0].upper()
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{gh.get("name")} — AGENTGRINDER profile</title>
<style>
  {CARD_THEME}

  *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);
    font:15px/1.5 "IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:24px 14px;
    display:flex;justify-content:center}}
  .wrap{{width:100%;max-width:640px}}
  .hero{{display:flex;gap:16px;align-items:center;margin-bottom:18px}}
  .av{{width:64px;height:64px;border-radius:50%;background:var(--accent);color:#fff;font-weight:700;
    font-size:28px;display:grid;place-items:center}}
  .hero h1{{margin:0;font-size:24px}} .hero .bio{{color:var(--muted);font-size:13.5px}}
  .hero .brand{{margin-left:auto;font-weight:800;letter-spacing:.08em;color:var(--muted);font-size:12px}}
  .stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);
    border:1px solid var(--line);border-radius:2px;overflow:hidden;margin-bottom:12px}}
  .s{{background:var(--card);padding:14px}} .s .v{{font-size:22px;font-weight:720}}
  .s .k{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}}
  .s.hl .v{{color:var(--accent)}} .s.hl{{cursor:help}}
  .cost{{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.06em;margin:0 2px 14px}}
  .rm .hl{{color:var(--accent);font-weight:700;cursor:help}} .rm .cost{{color:var(--muted)}}
  .row2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}}
  .panel{{background:var(--card);border:1px solid var(--line);border-radius:2px;padding:14px}}
  .panel h3{{margin:0 0 8px;font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}}
  .panel ul{{margin:0;padding-left:16px;font-size:13.5px}} .panel .chip{{font-size:13px}}
  h2.feed{{font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin:6px 0 10px}}
  .runrow{{display:block;text-decoration:none;color:inherit;background:var(--card);border:1px solid var(--line);
    border-radius:12px;padding:13px 15px;margin-bottom:10px}}
  .runrow:hover{{border-color:var(--accent)}}
  .rt{{font-weight:640;margin-bottom:4px}} .rm{{display:flex;gap:14px;flex-wrap:wrap;font-size:13px}}
  .rm span{{color:var(--ink)}} .rm .pb{{color:var(--accent);font-weight:700}}
  .rs{{color:var(--muted);font-size:12.5px;margin-top:4px}} .empty{{color:var(--muted);padding:20px;text-align:center}}
</style></head><body><div class="wrap">
  <div class="hero"><div class="av">{initial}</div>
    <div><h1>{gh.get("name")}</h1><div class="bio">@{gh.get("login")}{" · " + gh.get("bio") if gh.get("bio") else ""}</div></div>
    <div class="brand">AGENTGRINDER</div></div>
  <div class="stats">
    <div class="s hl" title="{escape(HEADLINE_TIP)} · {escape(t["vpt_formula"])}"><div class="v">{t["verified_per_turn"]}</div><div class="k">Verified per turn</div></div>
    <div class="s"><div class="v">{t["runs"]}</div><div class="k">Runs</div></div>
    <div class="s"><div class="v">{t["session_commits"]}</div><div class="k">Run commits</div></div>
    <div class="s"><div class="v">{stat(gh.get("public_repos"))}</div><div class="k">Repos</div></div>
  </div>
  <div class="cost">Cost — {t["prompts"]} prompts typed across {t["runs"]} runs</div>
  <div class="row2">
    <div class="panel"><h3>Setup</h3><div class="chip">{" · ".join(t["harnesses"])}</div></div>
    <div class="panel"><h3>Recently shipped ({stat(gh.get("recent_commits"))} commits)</h3><ul>{repos}</ul></div>
  </div>
  <h2 class="feed">Runs</h2>
  {cards}
</div></body></html>'''
