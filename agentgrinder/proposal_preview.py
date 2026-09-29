"""Render a compiled result-card proposal as a private, offline HTML page.

The renderer accepts a ``ResultCardProposal`` rather than the captured run. That boundary is
deliberate: transcripts, local paths and any unsupported run fields never enter the template.
"""
from __future__ import annotations

from html import escape

from . import privacy
from .proposal import ResultCardProposal


def _section(label: str, body: str, class_name: str = "") -> str:
    extra = f" {class_name}" if class_name else ""
    return f'<section class="block{extra}"><h2>{label}</h2>{body}</section>'


def _visual(card: ResultCardProposal) -> str:
    visual = card.visual
    if visual is None or len(visual.values) < 2:
        return ""
    width, height, top, bottom = 520, 116, 10, 104
    span = max(1, len(visual.values) - 1)
    points = " ".join(
        f"{index * width / span:.1f},{bottom - value * (bottom - top) / 100:.1f}"
        for index, value in enumerate(visual.values)
    )
    graphic = (
        f'<svg class="activity-visual" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="activity-title activity-desc" preserveAspectRatio="none">'
        f'<title id="activity-title">{escape(visual.label)}</title>'
        f'<desc id="activity-desc">{escape(visual.limitation)}</desc>'
        f'<line class="activity-base" x1="0" y1="{bottom}" x2="{width}" y2="{bottom}"/>'
        f'<polyline class="activity-line" points="{points}"/></svg>'
    )
    details = (
        '<details class="visual-basis"><summary>Visual basis</summary><dl>'
        f'<dt>Field and method</dt><dd>{escape(visual.basis)}</dd>'
        f'<dt>Window</dt><dd>{escape(visual.window)}</dd>'
        f'<dt>Limit</dt><dd>{escape(visual.limitation)}</dd>'
        '</dl></details>'
    )
    return _section(visual.label, graphic + details, "visual-block")


def render_proposal(card: ResultCardProposal) -> str:
    """Return deterministic, network-free HTML for one compiled proposal."""
    result = _section("Result", f'<p class="result">{escape(card.outcome)}</p>', "result-block")

    shape = ""
    shape_class = "shape-none"
    if card.shape:
        shape_class = "shape-" + card.shape.label.lower().replace(" ", "-")
        shape = (
            '<section class="run-shape">'
            f'<span>Observed run shape</span><strong>{escape(card.shape.label)}</strong>'
            f'<p>{escape(card.shape.reason)}</p>'
            '</section>'
        )

    proof = ""
    if card.proof_url:
        proof = _section(
            "Proof",
            f'<a class="proof" href="{escape(card.proof_url, quote=True)}" '
            f'rel="noreferrer">{escape(card.proof_label or "Open proof")}</a>',
        )

    turn = ""
    if card.turning_point:
        turn = _section("Turn", f'<p class="turn">{escape(card.turning_point)}</p>')

    visual = _visual(card)

    change = (_section("What changed", f'<p class="change">{escape(card.change)}</p>')
              if card.change else "")
    effort = (_section("Where effort went", f'<p class="effort">{escape(card.effort)}</p>')
              if card.effort else "")

    insights = ""
    if card.insights:
        rows = "".join(
            f'<li><span>{index}</span><p>{escape(insight.text)}</p></li>'
            for index, insight in enumerate(card.insights, 1)
        )
        insights = _section("Run read", f'<ol class="insights">{rows}</ol>', "insight-block")

    next_step = ""
    if card.next_action:
        next_step = _section("Next stride", f'<p class="next">{escape(card.next_action)}</p>', "next-block")

    metrics = ""
    basis = ""
    if card.metrics:
        cells = "".join(
            '<div class="metric">'
            f'<strong>{escape(metric.value)}</strong>'
            f'<span>{escape(metric.label)}</span>'
            '</div>'
            for metric in card.metrics[:4]
        )
        metrics = _section("Measured", f'<div class="metrics">{cells}</div>')
        items = "".join(
            f'<li><strong>{escape(metric.label)}</strong><span>{escape(metric.basis)}</span></li>'
            for metric in card.metrics[:4]
        )
        basis = (
            '<details class="basis"><summary>Measurement basis</summary>'
            f'<ul>{items}</ul></details>'
        )

    limit = _section("Limit", f'<p class="limit">{escape(card.limit)}</p>') if card.limit else ""
    evidence_rows = []
    if card.shape:
        evidence_rows.append(("Run shape", card.shape.basis))
    if card.change_basis:
        evidence_rows.append(("Change", card.change_basis))
    if card.effort_basis:
        evidence_rows.append(("Effort", card.effort_basis))
    evidence_rows.extend((f"Insight {index}", insight.basis)
                         for index, insight in enumerate(card.insights, 1))
    if card.next_basis:
        evidence_rows.append(("Next stride", card.next_basis))
    evidence = ""
    if evidence_rows or card.omitted:
        rows = "".join(
            f'<dt>{escape(label)}</dt><dd>{escape(value)}</dd>' for label, value in evidence_rows
        )
        missing = ""
        if card.omitted:
            missing = ('<dt>Not recorded</dt><dd>' + escape(", ".join(card.omitted)) + '</dd>')
        evidence = (
            '<details class="evidence"><summary>Evidence and missing data</summary>'
            f'<dl>{rows}{missing}</dl></details>'
        )
    is_shipping = card.shape and card.shape.label == "Shipping run"
    if is_shipping:
        body = f"{shape}{result}{proof}{change}{metrics}{insights}{effort}{visual}{turn}{next_step}{basis}{evidence}{limit}"
    else:
        body = f"{shape}{result}{change}{visual}{effort}{metrics}{insights}{turn}{proof}{next_step}{basis}{evidence}{limit}"
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>Private result proposal · STRIVE</title>
<style>
:root{{--paper:#f7f7f5;--box:#fff;--ink:#0a0a0a;--soft:#6f6f6b;--rule:#e3e3df;
  --rule-2:#efefec;--blue:#0047ff;--blue-soft:#c4d2ff;--blue-wash:#f2f5ff}}
*{{box-sizing:border-box}}html,body{{margin:0;max-width:100%;overflow-x:hidden}}
body{{background:var(--paper);color:var(--ink);font:15px/1.5 "IBM Plex Sans",system-ui,-apple-system,sans-serif;
  -webkit-font-smoothing:antialiased;padding:0 14px 40px}}
main{{width:100%;max-width:560px;margin:0 auto}}
.brand{{min-height:48px;display:flex;align-items:center;color:var(--blue);font-weight:700;letter-spacing:.08em}}
.private{{margin:0 0 10px;color:var(--soft);font-size:13px}}
.card{{background:var(--box);border:1px solid var(--rule);overflow:hidden}}
.run-shape{{padding:12px 16px;background:var(--blue);color:white;display:grid;grid-template-columns:1fr auto;gap:2px 12px}}
.run-shape span{{font-size:10px;line-height:1.2;text-transform:uppercase;letter-spacing:.09em;opacity:.8}}
.run-shape strong{{font-size:13px;line-height:1.2}}.run-shape p{{grid-column:1/-1;margin:4px 0 0;font-size:13px;opacity:.92}}
.block{{padding:16px;border-bottom:1px solid var(--rule-2);overflow-wrap:anywhere}}
.block:last-child{{border-bottom:0}}
h1{{font-size:13px;line-height:1.35;font-weight:500;color:var(--soft);margin:0 0 4px}}
h2{{font-size:10px;line-height:1.2;text-transform:uppercase;letter-spacing:.09em;color:var(--blue);margin:0 0 7px}}
p{{margin:0}}.result{{font-size:26px;line-height:1.14;font-weight:600;letter-spacing:-.02em}}
.change,.effort{{font-size:17px;line-height:1.35;font-weight:560}}
.turn{{font-size:17px;line-height:1.35;font-weight:600;border-left:3px solid var(--blue);padding-left:10px}}
.proof{{color:var(--blue);font-weight:600;text-underline-offset:3px;overflow-wrap:anywhere}}
.visual-block{{padding-left:0;padding-right:0}}.visual-block>h2{{padding:0 16px}}
.activity-visual{{display:block;width:100%;height:auto;max-width:100%;min-width:0;background:var(--box)}}
.activity-base{{stroke:var(--rule);stroke-width:1}}.activity-line{{fill:none;stroke:var(--blue);stroke-width:3;
  stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}}
.visual-basis{{color:var(--soft);border-top:1px solid var(--rule-2)}}
.visual-basis summary{{min-height:44px;display:flex;align-items:center;padding:0 16px;cursor:pointer;font-size:13px}}
.visual-basis dl{{margin:0;padding:10px 16px 14px;border-top:1px solid var(--rule-2);font-size:12px}}
.visual-basis dt{{color:var(--ink);font-weight:600;margin-top:7px}}.visual-basis dt:first-child{{margin-top:0}}
.visual-basis dd{{margin:1px 0 0;overflow-wrap:anywhere}}
.metrics{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;background:var(--rule-2)}}
.metric{{min-width:0;background:var(--box);padding:9px 10px 9px 0;display:flex;flex-direction:column}}
.metric:only-child{{grid-column:1/-1}}
.metric strong{{font-size:28px;line-height:1;font-weight:600;font-variant-numeric:tabular-nums}}
.metric span{{margin-top:5px;color:var(--soft);font-size:12px}}
.insights{{list-style:none;padding:0;margin:0}}.insights li{{display:grid;grid-template-columns:24px 1fr;gap:8px;padding:10px 0;border-top:1px solid var(--rule-2)}}
.insights li:first-child{{border-top:0;padding-top:0}}.insights li:last-child{{padding-bottom:0}}
.insights li>span{{color:var(--blue);font-size:12px;font-weight:700;padding-top:2px}}.insights p{{font-size:15px;line-height:1.4}}
.next-block{{background:var(--blue-wash)}}.next{{font-size:19px;line-height:1.3;font-weight:650}}
.basis{{background:var(--box);border-bottom:1px solid var(--rule-2);color:var(--soft)}}
.basis summary{{min-height:48px;display:flex;align-items:center;padding:0 16px;cursor:pointer;font-size:13px}}
.basis ul{{list-style:none;padding:0 16px 14px;margin:0;border-top:1px solid var(--rule-2)}}
.basis li{{display:flex;flex-direction:column;padding:9px 0;border-bottom:1px solid var(--rule-2);font-size:12px}}
.basis li:last-child{{border-bottom:0}}.basis strong{{color:var(--ink);font-weight:600}}.basis span{{margin-top:2px}}
.evidence{{background:var(--box);border-bottom:1px solid var(--rule-2);color:var(--soft)}}
.evidence summary{{min-height:48px;display:flex;align-items:center;padding:0 16px;cursor:pointer;font-size:13px}}
.evidence dl{{margin:0;padding:10px 16px 16px;border-top:1px solid var(--rule-2);font-size:12px}}
.evidence dt{{color:var(--ink);font-weight:650;margin-top:8px}}.evidence dt:first-child{{margin-top:0}}.evidence dd{{margin:1px 0 0;overflow-wrap:anywhere}}
.shape-shipping-run .result-block{{background:var(--blue-wash)}}
.limit{{color:var(--soft);font-size:13px}}
a:focus-visible,summary:focus-visible{{outline:2px solid var(--blue);outline-offset:3px}}
@media(max-width:420px){{body{{padding-left:10px;padding-right:10px}}.result{{font-size:23px}}}}
</style></head><body><main>
<div class="brand">STRIVE</div>
<p class="private">Private proposal · local only · not published</p>
<article class="card {shape_class}" aria-labelledby="proposal-title">
<h1 class="block" id="proposal-title">Post-run result card proposal</h1>
{body}
</article>
</main></body></html>"""
    privacy.assert_clean(html, "result proposal")
    return html
