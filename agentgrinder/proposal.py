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
class ProposedVisual:
    kind: str
    label: str
    values: tuple[int, ...]
    basis: str
    window: str
    limitation: str


@dataclass(frozen=True)
class ProposedInsight:
    text: str
    basis: str


@dataclass(frozen=True)
class RunShape:
    label: str
    reason: str
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
    visual: ProposedVisual | None = None
    shape: RunShape | None = None
    change: str = ""
    change_basis: str = ""
    effort: str = ""
    effort_basis: str = ""
    insights: tuple[ProposedInsight, ...] = field(default_factory=tuple)
    next_action: str = ""
    next_basis: str = ""
    omitted: tuple[str, ...] = field(default_factory=tuple)
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


def _list_count(run: dict, key: str) -> int | None:
    value = run.get(key)
    return len(value) if isinstance(value, list) else None


def _repos(run: dict) -> int | None:
    count, _ = _first_count(run, "repositories_touched", "repos_touched", "projects_touched")
    if count is not None:
        return count
    projects = run.get("projects")
    if isinstance(projects, list):
        return len({value for value in projects if isinstance(value, str) and value})
    return 1 if _safe_text(run.get("project")) else None


def _files(run: dict) -> int | None:
    return _first_count(run, "files_changed", "files_touched", "files_edited")[0]


def _active_seconds(run: dict) -> float | None:
    for key in ("active_time_s", "active_s"):
        value = run.get(key)
        if type(value) in (int, float) and value >= 0:
            return value
    return None


def _elapsed_seconds(run: dict) -> float | None:
    for key in ("wall_time_s", "wall_s"):
        value = run.get(key)
        if type(value) in (int, float) and value >= 0:
            return value
    return None


def _matching_checks(run: dict) -> int:
    before = run.get("failed_check_ids_before")
    after = run.get("passed_check_ids_after")
    if not isinstance(before, list) or not isinstance(after, list):
        return 0
    failed = {_safe_text(value) for value in before} - {""}
    passed = {_safe_text(value) for value in after} - {""}
    return len(failed & passed)


def _has_outcome(run: dict) -> bool:
    try:
        return bool(public_outcome(run).get("shipped")) or outcome_of(run).shipped
    except ValueError:
        return outcome_of(run).shipped


def _shape(run: dict) -> RunShape | None:
    """Name an observed run shape. A shape describes evidence; it never grades quality."""
    auth, auth_key = _first_count(run, "auth_stops", "human_input_stops")
    if (auth or 0) > 0 and not _has_outcome(run):
        return RunShape(
            "Blocked climb",
            f"The run ended with {auth:,} recorded authorization or human-input stop{'s' if auth != 1 else ''} and no recorded outcome.",
            f"run.{auth_key} plus the absence of a measured or declared outcome",
        )
    matched = _matching_checks(run)
    retries, retry_key = _first_count(run, "retries", "failed_attempts")
    if matched or (retries or 0) > 0:
        reason = (f"{matched:,} checks failed before and passed after."
                  if matched else f"The run recorded {retries:,} retr{'ies' if retries != 1 else 'y'}.")
        basis = ("intersection of run.failed_check_ids_before and run.passed_check_ids_after"
                 if matched else f"run.{retry_key}")
        return RunShape("Rescue mission", reason, basis)
    repos = _repos(run)
    lanes, lane_key = _first_count(run, "lane_count", "lanes_returned")
    if (repos or 0) >= 3 or (lanes or 0) >= 3:
        facts = []
        if (repos or 0) >= 3:
            facts.append(f"{repos:,} repositories or projects")
        if (lanes or 0) >= 3:
            facts.append(f"{lanes:,} lanes")
        return RunShape(
            "Fleet sprint", " and ".join(facts) + " were recorded in one run.",
            "run.projects/repositories_touched and " + (f"run.{lane_key}" if lane_key else "captured project count"),
        )
    reads = sum((_count(run.get(key)) or 0) for key in
                ("web_searches", "context_reads", "index_reads", "memory_reads"))
    edits = (_files(run) or 0) + (_count(run.get("commits")) or 0)
    if reads > 0 and reads > edits:
        return RunShape(
            "Research lap", f"{reads:,} recorded searches or reads outweighed {edits:,} files-plus-commits events.",
            "sum of run.web_searches/context_reads/index_reads/memory_reads compared with files and commits",
        )
    receipts = _list_count(run, "receipts") or 0
    prs, _ = _first_count(run, "pull_requests", "prs_opened", "prs_merged")
    deploys, _ = _first_count(run, "deployments", "deployments_verified")
    if receipts or (prs or 0) > 0 or (deploys or 0) > 0:
        facts = []
        if receipts:
            facts.append(f"{receipts:,} receipt{'s' if receipts != 1 else ''}")
        if prs:
            facts.append(f"{prs:,} pull request{'s' if prs != 1 else ''}")
        if deploys:
            facts.append(f"{deploys:,} deployment{'s' if deploys != 1 else ''}")
        return RunShape("Shipping run", " and ".join(facts) + " recorded.",
                        "run.receipts/pull_requests/deployments")
    duration = _active_seconds(run)
    duration_key = "active_time_s"
    if duration is None:
        duration = run.get("duration_s") if type(run.get("duration_s")) in (int, float) else None
        duration_key = "duration_s"
    files = _files(run)
    if duration is not None and duration >= 3600 and (files or 0) >= 5 and (repos or 1) <= 1:
        return RunShape(
            "Deep dive", f"One codebase held the run for {round(duration / 60):,} recorded minutes across {files:,} files.",
            f"run.{duration_key}, files_changed/files_touched, and captured project count",
        )
    return None


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


def _change(run: dict) -> tuple[str, str]:
    matched = _matching_checks(run)
    if matched:
        return (
            f"{matched:,} check{'s' if matched != 1 else ''} moved from failing to passing.",
            "intersection of run.failed_check_ids_before and run.passed_check_ids_after",
        )
    added, _ = _first_count(run, "lines_added")
    deleted, _ = _first_count(run, "lines_deleted")
    files = _files(run)
    if added is not None or deleted is not None:
        parts = [f"+{added or 0:,}", f"-{deleted or 0:,} lines"]
        if files is not None:
            parts.append(f"across {files:,} file{'s' if files != 1 else ''}")
        return " ".join(parts) + ".", "run.lines_added, run.lines_deleted, and changed-file count"
    commits = _count(run.get("commits"))
    if commits is not None and files is not None:
        return (
            f"{commits:,} commit{'s' if commits != 1 else ''} touched {files:,} file{'s' if files != 1 else ''}.",
            "run.commits and files_changed/files_touched in the same capture window",
        )
    if commits is not None:
        return f"{commits:,} commit{'s' if commits != 1 else ''} landed.", "run.commits"
    return "", ""


def _tool_breakdown(run: dict) -> tuple[dict[str, int], int] | None:
    raw = run.get("tool_calls_by_category")
    if not isinstance(raw, dict) or not raw:
        return None
    clean = {}
    for key, value in raw.items():
        label = _safe_text(key)
        count = _count(value)
        if label and count is not None:
            clean[label.lower()] = count
    total = sum(clean.values())
    declared = _count(run.get("tool_calls"))
    if not clean or total <= 0 or (declared is not None and declared != total):
        return None
    return clean, total


def _effort(run: dict) -> tuple[str, str]:
    breakdown = _tool_breakdown(run)
    if breakdown:
        values, total = breakdown
        label, count = max(values.items(), key=lambda item: (item[1], item[0]))
        share = round(count * 100 / total)
        return (
            f"{label.title()} was the largest tool category: {count:,} of {total:,} calls ({share}%).",
            "run.tool_calls_by_category; categories must sum to run.tool_calls when that total exists",
        )
    active, elapsed = _active_seconds(run), _elapsed_seconds(run)
    if active is not None and elapsed is not None and elapsed > 0 and active <= elapsed:
        return (
            f"{round(active / 60):,}m active inside {round(elapsed / 60):,}m elapsed ({round(active * 100 / elapsed)}%).",
            "run.active_time_s divided by run.wall_time_s/wall_s",
        )
    tools = _count(run.get("tool_calls"))
    turns = _count(run.get("turns_typed"))
    if tools is not None and turns:
        return (
            f"{tools:,} tool calls followed {turns:,} typed turns.",
            "run.tool_calls and run.turns_typed in the same capture window",
        )
    return "", ""


def _insights(run: dict) -> tuple[ProposedInsight, ...]:
    """Relational observations only. Volume alone never becomes a quality judgement."""
    insights: list[ProposedInsight] = []
    breakdown = _tool_breakdown(run)
    if breakdown:
        values, total = breakdown
        label, count = max(values.items(), key=lambda item: (item[1], item[0]))
        insights.append(ProposedInsight(
            f"Tool mix: {label} accounted for {round(count * 100 / total)}% of recorded calls ({count:,}/{total:,}).",
            "run.tool_calls_by_category divided by its source-bound total",
        ))
    tools = _count(run.get("tool_calls"))
    turns = _count(run.get("turns_typed"))
    if tools is not None and turns:
        insights.append(ProposedInsight(
            f"Tool amplification: each typed turn led to about {tools / turns:.1f} tool calls ({tools:,}/{turns:,}).",
            "run.tool_calls divided by run.turns_typed",
        ))
    commits = _count(run.get("commits"))
    files = _files(run)
    if commits and files is not None:
        insights.append(ProposedInsight(
            f"Edit breadth: {files / commits:.1f} files were touched per commit ({files:,}/{commits:,}).",
            "files_changed/files_touched divided by run.commits",
        ))
    claims = _count(run.get("claims"))
    verified = _count(run.get("claims_verified"))
    if claims and verified is not None and verified <= claims:
        unverified = claims - verified
        insights.append(ProposedInsight(
            (f"Verification gap: {verified:,} of {claims:,} recorded claims had verification; "
             f"{unverified:,} did not."),
            "run.claims_verified compared with run.claims",
        ))
    matched = _matching_checks(run)
    if matched:
        insights.append(ProposedInsight(
            f"Recovery: all {matched:,} checks found in both snapshots changed from failing to passing.",
            "intersection of run.failed_check_ids_before and run.passed_check_ids_after",
        ))
    found = _count(run.get("bugs_found"))
    fixed = _count(run.get("bugs_fixed"))
    if found and fixed is not None and fixed <= found:
        insights.append(ProposedInsight(
            f"Bug closure: {fixed:,} of {found:,} recorded bugs were fixed; {found - fixed:,} remained in the run record.",
            "run.bugs_fixed compared with run.bugs_found",
        ))
    active, elapsed = _active_seconds(run), _elapsed_seconds(run)
    if active is not None and elapsed is not None and elapsed > 0 and active <= elapsed:
        unobserved = elapsed - active
        insights.append(ProposedInsight(
            f"Time shape: the capture observed {round(active * 100 / elapsed)}% active time; {round(unobserved / 60):,} elapsed minutes were not active capture.",
            "run.active_time_s compared with run.wall_time_s/wall_s",
        ))
    outcomes = _list_count(run, "shipped")
    receipts = _list_count(run, "receipts")
    if outcomes and receipts is not None:
        insights.append(ProposedInsight(
            f"Proof density: {outcomes:,} declared outcomes are backed by {receipts:,} attached receipt{'s' if receipts != 1 else ''}.",
            "count of run.shipped compared with count of run.receipts",
        ))
    repos = _repos(run)
    repos_with_commits = _count(run.get("repositories_with_commits"))
    if repos and repos_with_commits is not None and repos_with_commits <= repos:
        insights.append(ProposedInsight(
            f"Fleet spread: {repos:,} repositories were touched, but {repos_with_commits:,} produced a recorded commit.",
            "repository count compared with run.repositories_with_commits",
        ))
    if tools is not None and tools > 0 and not _has_outcome(run):
        insights.append(ProposedInsight(
            f"Unclosed activity: {tools:,} tool calls were recorded, but no shipped outcome was recorded.",
            "run.tool_calls compared with outcome_of(run)",
        ))
    # An absent timed capture is a useful comparison for receipt-driven shipping runs; it stops
    # commit volume from masquerading as effort distribution.
    if receipts and _elapsed_seconds(run) is None and _active_seconds(run) is None and run.get("duration_s") is None:
        insights.append(ProposedInsight(
            "Timing blind spot: the receipts show shipping evidence, but this record cannot say where time went.",
            "run.receipts exists; active_time_s, wall_time_s, wall_s, and duration_s are absent",
        ))
    return tuple(insights[:3])


def _next_action(run: dict, outcome, proof_url: str) -> tuple[str, str]:
    failed = _count(run.get("tests_failed"))
    if failed:
        return (f"Resolve the {failed:,} remaining failed test{'s' if failed != 1 else ''}.",
                "run.tests_failed")
    auth, auth_key = _first_count(run, "auth_stops", "human_input_stops")
    if auth:
        return (f"Clear the {auth:,} recorded authorization or human-input stop{'s' if auth != 1 else ''}.",
                f"run.{auth_key}")
    if not outcome.shipped:
        return ("Attach one result or receipt before sharing this as a completed run.",
                "outcome_of(run) found no measured or declared shipped result")
    if not run.get("outside_use_verified"):
        return ("Verify that one person outside the run can reach and use the result.",
                "run.outside_use_verified is absent or false")
    if proof_url:
        return "Open the attached proof and choose what to share.", "the run has a proof URL and outside use is verified"
    return "Attach inspectable proof before sharing.", "a shipped result exists without an attached proof URL"


def _omitted(run: dict) -> tuple[str, ...]:
    groups = (
        ("active time", ("active_time_s", "active_s")),
        ("elapsed time", ("wall_time_s", "wall_s")),
        ("tool categories", ("tool_calls_by_category",)),
        ("line changes", ("lines_added", "lines_deleted")),
        ("test totals", ("tests_run", "tests_passed", "tests_failed", "checks_passed")),
        ("bug totals", ("bugs_found", "bugs_fixed")),
        ("web searches", ("web_searches",)),
        ("remote sessions", ("remote_sessions", "vm_logins")),
        ("authorization stops", ("auth_stops", "human_input_stops")),
        ("models used", ("models_used", "models_used_count")),
        ("context and memory reads", ("context_reads", "index_reads", "memory_reads")),
        ("pull request and deployment outcomes", ("pull_requests", "prs_opened", "prs_merged", "deployments", "deployments_verified")),
    )
    return tuple(label for label, keys in groups if not any(key in run for key in keys))


def _sample(values: list[int], limit: int = 48) -> list[int]:
    if len(values) <= limit:
        return values
    return [values[index * (len(values) - 1) // (limit - 1)] for index in range(limit)]


def _normalize(values: list[int]) -> tuple[int, ...]:
    peak = max(values, default=0)
    if peak == 0:
        return tuple(0 for _ in values)
    return tuple(round(value * 100 / peak) for value in values)


def _visual(run: dict) -> ProposedVisual | None:
    """Compile safe numeric geometry only; never carry labels or capture prose."""
    route = run.get("route")
    if (isinstance(route, list) and 1 <= len(route) <= 10000
            and all(type(value) is int and value >= 0 for value in route)):
        collapsed = [route[0]]
        for value in route[1:]:
            if value != collapsed[-1]:
                collapsed.append(value)
        lanes = {value: index for index, value in enumerate(sorted(set(collapsed)))}
        ordinal = [lanes[value] for value in collapsed]
        if len(ordinal) == 1:
            ordinal.append(ordinal[0])
        sampled = _sample(ordinal)
        return ProposedVisual(
            kind="route",
            label="Activity route",
            values=_normalize(sampled),
            basis=("run.route · categorical numeric station lanes · consecutive repeats "
                   "collapsed; up to 48 evenly sampled points"),
            window="captured session window; exact event timing is not represented",
            limitation=("Activity shape only. Vertical station position is not a rank. "
                        "This does not measure quality, progress, success, or code authorship."),
        )

    ridge = run.get("ridge")
    if (isinstance(ridge, list) and 40 <= len(ridge) <= 60
            and all(type(value) is int and value >= 0 for value in ridge)):
        methods = {
            "wall-time": "equal wall-time bins",
            "call-index": "capture call-order bins",
            "turn-order": "capture turn-order bins",
        }
        method = methods.get(run.get("ridge_basis"))
        if method:
            return ProposedVisual(
                kind="rhythm",
                label="Activity rhythm",
                values=_normalize(ridge),
                basis=f"run.ridge · {method} · each bin normalized to the run peak (0-100)",
                window="the capture window represented by the supplied ridge bins",
                limitation=("Relative activity only. It does not measure quality, progress, "
                            "success, output, or code authorship."),
            )
    return None


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
    change, change_basis = _change(run)
    effort, effort_basis = _effort(run)
    next_action, next_basis = _next_action(run, outcome, proof_url)
    return ResultCardProposal(
        archetype=archetype,
        outcome=outcome.text,
        outcome_basis=outcome.basis,
        turning_point=_turning_point(run),
        metrics=metrics_for(run, archetype),
        proof_url=proof_url,
        proof_label=proof_label,
        visual=_visual(run),
        shape=_shape(run),
        change=change,
        change_basis=change_basis,
        effort=effort,
        effort_basis=effort_basis,
        insights=_insights(run),
        next_action=next_action,
        next_basis=next_basis,
        omitted=_omitted(run),
        limit=_limit(run, outcome.measured, outcome.shipped, proof_url, outcome.basis),
    )
