"""Map a coding-agent session to an athletic 'run'. Every metric traces to the session log.

A 'run' JSON (see samples/) carries only counts read from a real session:
  athlete, title, harness, project, started (ISO), duration_s,
  turns_typed, tool_calls, files_touched, commits,
  rhythm  -> typed turns per time bucket (the 'route')
and, optionally, the five numbers of a run (METRICS-AGENTIC-ENGINEERING-2026-09-02, an internal spec not in this repo):
  claims, claims_verified        -> verified-claims share (the calibrated claim rule in
                                    claims.py; the evidence side is still unmeasured)
  corrections                    -> correction rate (not measured yet: nothing labels a turn as
                                    undoing the one before it)
  artifacts_produced, artifacts_promised -> produced ÷ promised (produced is measured; promised is
                                    not measured yet: nothing records what a run promised)
  reach                          -> true/false/None: did the output cross to a person who is not
                                    the author (reach.py, from git)

THE HEADLINE is verified-per-turn = (claims_verified + artifacts_produced) ÷ turns_typed.
Typed turns are a COST (the denominator), never the achievement. A card that headlines
"47 prompts" celebrates the person who talked the most (METR 2025: developers believed
they were 20% faster and measured 19% slower). Distance = verified output; prompts = cost.

We never invent a number. If a field is missing, the derived stat is None and the card
shows a dash, not a guess (Constitution rule 3). A dash carries a tooltip that says, in plain
words, WHICH FACT is missing and whether the person reading it can supply that fact today
(SOURCES below). It never names a tool a stranger cannot install.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


def _fmt_dur(s: int | None) -> str:
    if not s:
        return "—"
    h, rem = divmod(int(s), 3600)
    m, sec = divmod(rem, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m {sec:02d}s"


def _fmt_pace(sec_per: float | None) -> str:
    if not sec_per:
        return "—"
    m, s = divmod(int(round(sec_per)), 60)
    return f"{m}:{s:02d} /prompt"


# What each of the five numbers is, in words a stranger can act on. A cell that cannot be
# computed says NOT MEASURED YET and names the fact that is missing, plus whether the person
# reading it can supply that fact today. It never names a tool they cannot install.
SOURCES = {
    "typed_turns": "the turns you typed or queued, read from the transcript (authorship.py): "
                   "tool results and injected context are not turns",
    "verified_share": "claims that had matching evidence inside their own turn. The rule that "
                      "decides what a claim is reads precision 0.63 and recall 0.66 on a "
                      "held-out hand-labelled set (archive/hackathon-2026-09/docs/CLAIM-RULE-CALIBRATION-2026-09-03.md); "
                      "whether a claim was matched to the right evidence is not measured yet",
    "correction_rate": "not measured yet: it needs every turn labelled as undoing the one before "
                       "it, and no harness records that, so nothing on your machine can supply it "
                       "today",
    "produced_over_promised": "produced is measured here: files this run wrote that exist on disk. "
                              "Promised is not measured yet: nothing records what a run said it "
                              "would deliver, so you cannot supply it today",
    "reach": "did the output cross to a person who is not the author: read from the commits in "
             "this window, your remotes and their push refs (reach.py). A dash whenever the "
             "machine cannot tell, and it says which fact was missing",
}


def verified_per_turn(verified_claims: int | None, artifacts_produced: int | None,
                      turns_typed: int | None) -> float | None:
    """(verified claims + artifacts produced) ÷ typed turns.

    None if ANY input is missing or there are no typed turns: a missing numerator defaulted to
    0 would fabricate a low score, which is a fabrication like any other.
    """
    if verified_claims is None or artifacts_produced is None or not turns_typed:
        return None
    return (verified_claims + artifacts_produced) / turns_typed


def _ratio(num: int | None, den: int | None) -> float | None:
    if num is None or not den:
        return None
    return num / den


HEADLINE_TIP = ("verified per turn = (verified claims + artifacts produced) ÷ typed turns. "
                "Local: the calibrated claims.py rule (precision 0.63, recall 0.66 held out) plus "
                "Edit/Write paths on disk. A rate, not a count: a count of claims moves with how "
                "much the agent talks, see /methodology")

ARTIFACTS_PER_TURN_TIP = ("artifacts per turn = artifacts produced ÷ typed turns. Used only when "
                          "claim evidence cannot be measured on this harness. It is not verified "
                          "per turn; do not compare it to a verified-per-turn reading as the same metric.")

METRIC_VERIFIED_PER_TURN = "verified_per_turn"
METRIC_ARTIFACTS_PER_TURN = "artifacts_per_turn"


@dataclass
class Cell:
    """One of the five run numbers: the printed value, and where it comes from."""
    label: str
    value: str            # "—" when not computable here
    source: str           # tooltip: the tool that owns this number
    cost: bool = False    # typed turns is the denominator — labelled as cost on the card


@dataclass
class Activity:
    athlete: str
    title: str
    harness: str
    project: str
    date_str: str
    # headline stats (the three big numbers, Strava-style)
    distance: str          # prompts you typed
    moving_time: str       # session duration
    pace: str              # time per typed prompt
    # secondary
    effort: str            # tool calls (the grind / 'elevation')
    segments: str          # files touched
    commits: str
    prompts_per_hour: str
    focus_pb: bool         # a light 'personal best' flag when cadence is high
    rhythm: list[int]      # the route profile
    # THE HEADLINE — verified per turn — and the five numbers of a run
    trace: list = field(default_factory=list)
    trace_basis: str = ""
    coach_verdict: str = ""
    coach_plan: str = ""
    coach_mode: str = ""
    headline: str = "—"                        # e.g. "0.21"
    headline_val: float | None = None
    headline_formula: str = ""                 # "(6 verified + 4 artifacts) ÷ 47 typed turns"
    headline_label: str = "verified per turn"
    headline_metric_id: str = METRIC_VERIFIED_PER_TURN
    five: list = field(default_factory=list)   # five Cell rows, in the metric spec's order


@dataclass
class Headline:
    """The card's one big number, and the five cells that sit under it. ONE definition,
    used by every surface (demo card, grind card, profile, terminal), so they cannot disagree."""
    text: str                  # "0.21" or "—"
    value: float | None
    formula: str               # "(6 verified + 4 artifacts) ÷ 47 typed turns" / "needs …"
    five: list                 # five Cell rows, in the metric spec's order
    metric_id: str = METRIC_VERIFIED_PER_TURN
    label: str = "verified per turn"


def five_cells(run: dict) -> list[Cell]:
    turns = run.get("turns_typed")
    claims = run.get("claims")
    verified = run.get("claims_verified")
    corrections = run.get("corrections")
    produced = run.get("artifacts_produced")
    promised = run.get("artifacts_promised")
    reach = run.get("reach")
    share = _ratio(verified, claims)   # None when no claims were made
    corr = _ratio(corrections, turns)
    caps = run.get("capabilities") or {}

    def _n(v):
        return "—" if v is None else str(v)

    if share is not None:
        verified_cell = f"{verified}/{claims} · {share:.0%}"
        verified_src = SOURCES["verified_share"]
    elif verified is not None and claims is not None:
        verified_cell = f"{verified}/{claims}"
        verified_src = SOURCES["verified_share"]
    elif claims is not None and caps.get("claim_evidence") is False:
        # Claims counted from assistant prose; same-turn tool stdout is not in this harness's
        # transcript, so the evidence half stays unmeasured (baseline), never a fabricated 0.
        verified_cell = f"—/{claims}"
        verified_src = ("claims counted from assistant text; same-turn tool stdout is not in this "
                        "harness transcript, so verified share cannot be measured here today")
    else:
        verified_cell = "—"
        verified_src = SOURCES["verified_share"]

    return [
        Cell("typed turns", _n(turns), SOURCES["typed_turns"], cost=True),
        Cell("verified claims", verified_cell, verified_src),
        Cell("correction rate", f"{corr:.0%}" if corr is not None else "—", SOURCES["correction_rate"]),
        Cell("produced ÷ promised", f"{_n(produced)} ÷ {_n(promised)}", SOURCES["produced_over_promised"]),
        # the reach dash carries the sentence the probe wrote for THIS run ("no commit landed
        # inside this window…"), and falls back to the definition when a run predates the probe.
        Cell("reach", ("yes" if reach else "no") if reach is not None else "—",
             run.get("reach_reason") or SOURCES["reach"]),
    ]


def headline_of(run: dict) -> Headline:
    """Headline number for a run: verified-per-turn when both inputs exist.

    When claim evidence cannot be measured (`capabilities.claim_evidence` is False and
    `claims_verified` is None), the headline is **artifacts per turn** — a different metric
    identity. Never label that number "verified per turn".
    """
    turns = run.get("turns_typed")
    verified = run.get("claims_verified")
    produced = run.get("artifacts_produced")
    vpt = verified_per_turn(verified, produced, turns)
    if vpt is not None:
        return Headline(
            text=f"{vpt:.2f}", value=vpt,
            formula=f"({verified} verified + {produced} artifacts) ÷ {turns} typed turns",
            five=five_cells(run),
            metric_id=METRIC_VERIFIED_PER_TURN, label="verified per turn")
    caps = run.get("capabilities") or {}
    if (caps.get("claim_evidence") is False and produced is not None and turns
            and verified is None):
        apt = produced / turns
        return Headline(
            text=f"{apt:.2f}", value=apt,
            formula=f"{produced} artifacts ÷ {turns} typed turns",
            five=five_cells(run),
            metric_id=METRIC_ARTIFACTS_PER_TURN, label="artifacts per turn")
    missing = [k for k, v in (("verified claims", verified), ("artifacts produced", produced),
                              ("typed turns", turns)) if v is None]
    return Headline(
        text="—", value=None,
        formula="needs " + ", ".join(missing) if missing else "no typed turns",
        five=five_cells(run),
        metric_id=METRIC_VERIFIED_PER_TURN, label="verified per turn")

def _public_coach_text(value: str) -> str:
    """HTML cards are an export destination. Paths stay off them; local CLI text is separate."""
    from .coach.experiment import public_text
    return public_text(value) or ""


def build_activity(run: dict) -> Activity:
    turns = run.get("turns_typed")
    tools = run.get("tool_calls")
    files = run.get("files_touched")
    commits = run.get("commits")
    rhythm = run.get("rhythm") or []
    caps = run.get("capabilities") or {}
    # Refuse elapsed/rate displays when the harness says the trace is not a timed clock.
    timed = caps.get("timed_trace", True) is not False and run.get("duration_s") is not None
    dur = run.get("duration_s") if timed else None

    pace_sec = (dur / turns) if (dur and turns) else None
    pph = (turns / (dur / 3600)) if (dur and turns) else None
    # 'personal best': a genuinely high, sustained cadence — traced, not decorative.
    focus_pb = bool(pph and pph >= 25 and turns and turns >= 30)

    started = run.get("started")
    try:
        date_str = datetime.fromisoformat(started).strftime("%a %d %b %Y · %H:%M") if started else "—"
    except ValueError:
        date_str = started or "—"

    hl = headline_of(run)
    moving = _fmt_dur(dur) if timed else "—"
    pace = _fmt_pace(pace_sec) if timed else "—"
    cadence = f"{pph:.1f}/h" if pph else ("—" if not timed else "—")
    if not timed:
        # Tooltip-facing copy lives on the card cost group via dash + trace_basis.
        moving = "—"
        pace = "—"
        cadence = "—"

    return Activity(
        athlete=run.get("athlete", "athlete"),
        title=run.get("title", "Untitled session"),
        harness=run.get("harness", "coding agent"),
        project=run.get("project", "—"),
        date_str=date_str,
        distance=f"{turns} prompts" if turns is not None else "—",
        moving_time=moving,
        pace=pace,
        effort=f"{tools} tool calls" if tools is not None else "—",
        segments=f"{files} files" if files is not None else "—",
        commits=str(commits) if commits is not None else "—",
        prompts_per_hour=cadence,
        focus_pb=focus_pb,
        rhythm=[int(x) for x in rhythm],
        coach_verdict=_public_coach_text(run.get("coach_verdict") or ""),
        coach_plan=_public_coach_text("\n".join(x for x in [run.get("coach_plan"), run.get("private_coach_plan")] if x)),
        coach_mode=run.get("coach_mode") or "",
        trace=run.get("trace") or [],
        trace_basis=run.get("trace_basis") or "",
        headline=hl.text,
        headline_val=hl.value,
        headline_formula=hl.formula,
        headline_label=hl.label,
        headline_metric_id=hl.metric_id,
        five=hl.five,
    )
