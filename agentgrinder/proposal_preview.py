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


def render_proposal(card: ResultCardProposal) -> str:
    """Return deterministic, network-free HTML for one compiled proposal."""
    result = _section("Result", f'<p class="result">{escape(card.outcome)}</p>')

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
.block{{padding:16px;border-bottom:1px solid var(--rule-2);overflow-wrap:anywhere}}
.block:last-child{{border-bottom:0}}
h1{{font-size:13px;line-height:1.35;font-weight:500;color:var(--soft);margin:0 0 4px}}
h2{{font-size:10px;line-height:1.2;text-transform:uppercase;letter-spacing:.09em;color:var(--blue);margin:0 0 7px}}
p{{margin:0}}.result{{font-size:26px;line-height:1.14;font-weight:600;letter-spacing:-.02em}}
.turn{{font-size:17px;line-height:1.35;font-weight:600;border-left:3px solid var(--blue);padding-left:10px}}
.proof{{color:var(--blue);font-weight:600;text-underline-offset:3px;overflow-wrap:anywhere}}
.metrics{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;background:var(--rule-2)}}
.metric{{min-width:0;background:var(--box);padding:9px 10px 9px 0;display:flex;flex-direction:column}}
.metric strong{{font-size:28px;line-height:1;font-weight:600;font-variant-numeric:tabular-nums}}
.metric span{{margin-top:5px;color:var(--soft);font-size:12px}}
.basis{{background:var(--box);border-bottom:1px solid var(--rule-2);color:var(--soft)}}
.basis summary{{min-height:48px;display:flex;align-items:center;padding:0 16px;cursor:pointer;font-size:13px}}
.basis ul{{list-style:none;padding:0 16px 14px;margin:0;border-top:1px solid var(--rule-2)}}
.basis li{{display:flex;flex-direction:column;padding:9px 0;border-bottom:1px solid var(--rule-2);font-size:12px}}
.basis li:last-child{{border-bottom:0}}.basis strong{{color:var(--ink);font-weight:600}}.basis span{{margin-top:2px}}
.limit{{color:var(--soft);font-size:13px}}
a:focus-visible,summary:focus-visible{{outline:2px solid var(--blue);outline-offset:3px}}
@media(max-width:420px){{body{{padding-left:10px;padding-right:10px}}.result{{font-size:23px}}}}
</style></head><body><main>
<div class="brand">STRIVE</div>
<p class="private">Private proposal · local only · not published</p>
<article class="card" aria-labelledby="proposal-title">
<h1 class="block" id="proposal-title">Post-run result card proposal</h1>
{result}{proof}{turn}{metrics}{basis}{limit}
</article>
</main></body></html>"""
    privacy.assert_clean(html, "result proposal")
    return html
