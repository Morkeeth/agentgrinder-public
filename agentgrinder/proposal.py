"""Compile captured evidence into a private, editable STRIVE result-card proposal.

This module does not publish, call a model, or read prose from a transcript. It uses only
structured fields the capture already produced. Missing evidence stays missing.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import privacy
from .contract import public_outcome
from .outcome import NOTHING_SHIPPED, outcome_of


@dataclass(frozen=True)
class ProposedMetric:
    value: str
    label: str
    basis: str


@dataclass(frozen=True)
class ResultCardProposal:
    archetype: str
    outcome: str
    outcome_basis: str
    turning_point: str = ""
    metrics: tuple[ProposedMetric, ...] = field(default_factory=tuple)
    proof_url: str = ""
    proof_label: str = ""
    limit: str = ""


def _count(value) -> int | None:
    return value if type(value) is int and value >= 0 else None


def _safe_text(value) -> str:
    if not isinstance(value, str):
        return ""
    text = privacy.strip_home_names(" ".join(value.split()))
    if not text or privacy.scan(text):
        return ""
    return text[:160].rstrip()


def _first_count(run: dict, *keys: str) -> tuple[int | None, str]:
    for key in keys:
        value = _count(run.get(key))
        if value is not None:
            return value, key
    return None, ""


def classify(run: dict) -> str:
    """Select evidence policy quietly. This is not a user identity or scored label."""
    projects = run.get("projects")
    lanes, _ = _first_count(run, "lane_count", "lanes_returned")
    if (isinstance(projects, list) and len(projects) > 1) or (lanes or 0) > 1:
        return "fleet"
    if any((_count(run.get(k)) or 0) > 0 for k in
           ("sources_count", "citations_count", "web_searches", "experiments_run")):
        return "research"
    if any((_count(run.get(k)) or 0) > 0 for k in
           ("bugs_found", "bugs_fixed", "regressions_found", "tests_failed_before")):
        return "debugger"
    if any(run.get(k) for k in
           ("skills_used", "models_used", "routines_changed", "indexes_changed")):
        return "architect"
    if any((_count(run.get(k)) or 0) > 0 for k in
           ("assets_created", "articles_created", "videos_created", "audio_created")):
        return "creator"
    return "shipper"


def _metric(value: int | None, label: str, basis: str) -> ProposedMetric | None:
    if value is None:
        return None
    return ProposedMetric(f"{value:,}", label, basis)


def _duration(run: dict) -> ProposedMetric | None:
    key = next((name for name in ("wall_time_s", "wall_s", "duration_s")
                if type(run.get(name)) in (int, float) and run[name] >= 0), "")
    if not key:
        return None
    wall = run[key]
    minutes = max(1, round(wall / 60)) if wall else 0
    if key == "wall_time_s":
        return ProposedMetric(f"{minutes}m", "wall time", "wall time measured by the capture")
    if key == "wall_s":
        return ProposedMetric(f"{minutes}m", "elapsed", "first-to-last event timestamps")
    # solo.py computes duration_s with a capped-gap moving estimate. Other readers attach
    # different timing bases to the same field, so it must never be presented as exact elapsed
    # or exact active time.
    return ProposedMetric(
        f"{minutes}m", "activity estimate",
        "capture-derived activity estimate; not exact active time",
    )


def metrics_for(run: dict, archetype: str) -> tuple[ProposedMetric, ...]:
    policies = {
        "fleet": (("lane_count", "lanes", "captured lane count"),
                  ("lanes_returned", "returns", "lanes with a recorded return"),
                  ("projects_touched", "projects", "distinct projects recorded by capture"),
                  ("handoffs", "handoffs", "recorded cross-lane handoffs")),
        "research": (("sources_count", "sources", "distinct recorded sources"),
                     ("citations_count", "citations", "citations stored on the run"),
                     ("web_searches", "web searches", "search calls recorded by capture"),
                     ("experiments_run", "experiments", "recorded experiment executions")),
        "debugger": (("bugs_found", "bugs found", "bugs recorded by the run"),
                     ("bugs_fixed", "bugs fixed", "fixes recorded by the run"),
                     ("checks_passed", "checks passing", "passing checks recorded by the run"),
                     ("regressions_found", "regressions", "regressions recorded by the run")),
        "architect": (("skills_used_count", "skills used", "skills recorded as loaded"),
                      ("routines_changed_count", "routines changed", "routine changes recorded by the run"),
                      ("indexes_changed_count", "indexes changed", "index changes recorded by the run"),
                      ("models_used_count", "models used", "models recorded by the run")),
        "creator": (("assets_created", "assets", "created assets recorded by the run"),
                    ("articles_created", "articles", "created articles recorded by the run"),
                    ("videos_created", "videos", "created videos recorded by the run"),
                    ("audio_created", "audio pieces", "created audio recorded by the run")),
        "shipper": (("features_shipped", "features", "features recorded as shipped"),
                    ("commits", "commits", "git commits measured in the run window"),
                    ("files_changed", "files changed", "files changed in the run window"),
                    ("checks_passed", "checks passing", "passing checks recorded by the run")),
    }
    selected = []
    for key, label, basis in policies[archetype]:
        item = _metric(_count(run.get(key)), label, basis)
        if item is not None:
            selected.append(item)
        if len(selected) == 3:
            break
    duration = _duration(run)
    if duration is not None and len(selected) < 4:
        selected.append(duration)
    return tuple(selected[:4])


def _turning_point(run: dict) -> str:
    before = run.get("failed_check_ids_before")
    after = run.get("passed_check_ids_after")
    if isinstance(before, list) and isinstance(after, list):
        failed_ids = {_safe_text(value) for value in before}
        passed_ids = {_safe_text(value) for value in after}
        matched = (failed_ids & passed_ids) - {""}
        if matched:
            count = len(matched)
            return (f"{count:,} matching check{'s' if count != 1 else ''} failed before "
                    "and passed after.")
    bugs = _count(run.get("bugs_fixed"))
    if bugs:
        return f"The run recorded {bugs:,} bug fix{'es' if bugs != 1 else ''}."
    # An explicit structured field is allowed only when it carries its own receipt.
    point = _safe_text(run.get("turning_point"))
    receipt = run.get("turning_point_receipt")
    if point and isinstance(receipt, str) and receipt.startswith(("https://", "http://")):
        return point
    return ""


def _proof(run: dict) -> tuple[str, str]:
    try:
        declared = public_outcome(run)
    except ValueError:
        return "", ""
    for receipt in declared.get("receipts") or []:
        if not isinstance(receipt, dict):
            continue
        url = receipt.get("url")
        if isinstance(url, str) and url.startswith(("https://", "http://")):
            return url, _safe_text(receipt.get("label")) or "Open proof"
    return "", ""


def _limit(run: dict, measured: bool, shipped: bool, proof_url: str, basis: str) -> str:
    if not shipped:
        return basis
    if measured:
        return "Measured from local evidence. Deployment and outside use were not verified."
    if proof_url:
        return "The proof link was supplied by the author; STRIVE did not verify its destination."
    return "Author reported. No inspectable proof was attached."


def propose(run: dict) -> ResultCardProposal:
    """Return a private proposal. The caller must ask the author before saving or publishing."""
    if not isinstance(run, dict):
        run = {}
    archetype = classify(run)
    outcome = outcome_of(run)
    proof_url, proof_label = _proof(run)
    return ResultCardProposal(
        archetype=archetype,
        outcome=outcome.text,
        outcome_basis=outcome.basis,
        turning_point=_turning_point(run),
        metrics=metrics_for(run, archetype),
        proof_url=proof_url,
        proof_label=proof_label,
        limit=_limit(run, outcome.measured, outcome.shipped, proof_url, outcome.basis),
    )
