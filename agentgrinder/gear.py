"""THE GEAR CHIP AND THE TROPHY MARKS — both counted from captured runs, or both absent.

Strava puts your shoes under the run and a trophy on the ones that were your best. The equivalent
here is the agent, the harness and the model the work was done with, and the small number of
badges a local machine can actually prove. Both are built from ONE population: the private capture
drafts in `~/.agentgrinder/capture` (capture.py). Nothing here reaches a network, and nothing here
counts a run this machine did not capture, so the chip says which population it counted.

TWO OF THE FOUR BADGES ARE USUALLY ABSENT, ON PURPOSE. The vocabulary has four (contract.
TROPHY_IDS): biggest pull request, first merge, merge streak, longest run. A local capture can
measure the size of a change and the length of a run. It cannot see a merge: nothing on this disk
knows whether a pull request was accepted, and a badge that guessed would be the first fabricated
mark on a card whose whole argument is that its marks are real. So `first-merge` and
`merge-streak` stay unbuilt until something measures them, and the card simply has fewer badges.
"""
from __future__ import annotations

import json

BASIS = "Counted from the runs captured on this machine"
MAX_RUNS = 5000


def _runs(directory=None) -> list:
    """Every captured draft, newest last. An unreadable or absent capture database is no runs.

    It is opened only when it already exists. `capture.connect` creates the private database on
    the way in, and a chip that counts nothing is not worth making a file on the disk of someone
    who has never run a capture.
    """
    from pathlib import Path

    root = Path(directory) if directory else Path.home() / ".agentgrinder" / "capture"
    if not (root / "capture.db").is_file():
        return []
    try:
        from .capture import connect

        db = connect(root)
    except Exception:                                    # a capture database is optional
        return []
    try:
        rows = db.execute("select payload from drafts order by started").fetchall()
    except Exception:
        return []
    finally:
        db.close()
    out = []
    for row in rows[:MAX_RUNS]:
        try:
            value = json.loads(row[0])
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            out.append(value)
    return out


def _lines(run: dict) -> int:
    work = run.get("file_work")
    if isinstance(work, dict) and isinstance(work.get("totals"), dict):
        value = work["totals"].get("lines_changed")
        if type(value) is int and value > 0:
            return value
    return 0


def _pull_request(run: dict) -> bool:
    """Does this run carry a link to a pull request the author declared?"""
    for receipt in run.get("receipts") or []:
        url = receipt.get("url") if isinstance(receipt, dict) else None
        if isinstance(url, str) and "/pull/" in url:
            return True
    url = run.get("repo_url")
    return isinstance(url, str) and "/pull/" in url


def _clock(seconds) -> str:
    if type(seconds) not in (int, float) or seconds <= 0:
        return ""
    minutes = int(seconds) // 60
    hours, rest = divmod(minutes, 60)
    return f"{hours}h {rest:02d}m" if hours else f"{rest}m"


def chip(run: dict, history: list) -> dict | None:
    """Agent, harness and model from THIS run; the totals from every captured run."""
    out = {}
    for field, key in (("agent", "agent_name"), ("harness", "harness"), ("model", "model")):
        value = run.get(key)
        if isinstance(value, str) and value.strip():
            out[field] = value.strip()[:48]
    if history:
        out["runs"] = len(history)
        commits = sum(r["commits"] for r in history
                      if type(r.get("commits")) is int and r["commits"] > 0)
        if commits:
            out["commits"] = commits
        lines = sum(_lines(r) for r in history)
        if lines:
            out["lines_changed"] = lines
        out["basis"] = BASIS
    if not out or set(out) == {"basis"}:
        return None
    return out


def badges(history: list) -> list:
    """The trophies this machine can prove. Two of the four; the others need a merge it cannot see."""
    out = []
    sized = [(r, _lines(r)) for r in history if _lines(r)]
    with_pr = [(r, lines) for r, lines in sized if _pull_request(r)]
    if with_pr:
        best = max(with_pr, key=lambda pair: pair[1])
        out.append({
            "id": "biggest-pr",
            "label": "Biggest pull request",
            "value": f"{best[1]:,}",
            "basis": "Most lines changed in a captured run carrying a pull request link",
        })
    timed = [r for r in history
             if type(r.get("duration_s")) in (int, float) and r["duration_s"] > 0]
    if timed:
        longest = max(timed, key=lambda r: r["duration_s"])
        clock = _clock(longest["duration_s"])
        if clock:
            out.append({
                "id": "longest-run",
                "label": "Longest run",
                "value": clock,
                "basis": "Longest moving time across the captured runs",
            })
    return out


def attach(run: dict, directory=None) -> dict:
    """Put a measured gear chip and measured trophies on a run. Absent stays absent.

    A run that already carries either is left alone: the author may have set them deliberately,
    and a capture pass is not allowed to overwrite a person's own card.
    """
    if not isinstance(run, dict):
        return run
    history = _runs(directory)
    if run.get("gear") is None:
        made = chip(run, history)
        if made:
            run["gear"] = made
    if run.get("trophies") is None:
        made = badges(history)
        if made:
            run["trophies"] = made
    return run
