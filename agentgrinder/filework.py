"""WHAT THE RUN DID TO THE FILES, asked of git — never of the transcript.

`gitwork` answers "which commits happened in this window, and which files were in them". That is
enough to say a file shipped. It is not enough to DRAW the run: a size map needs the line count of
every file at the end, a folder line needs the order the work visited folders in, and an elevation
profile needs a clock with a number attached to each tick. All four of those facts are in git and
in none of the harness transcripts, so this module asks git for them and nothing else asks.

Three measurements, one window, one total
-----------------------------------------
  lines changed   `git log --numstat` over the run's own commits, added + deleted per file.
                  CHURN, not the net diff: a file written twice in one run was worked on twice,
                  and a range diff that cancels the two would draw a file the run never touched.
  lines at the end  `git grep -I -c -e ''` at the last commit, which is `wc -l` per TEXT file,
                  measured on this repository against `git show | wc -l` and equal on every file.
                  It skips binary blobs, and a blob with no line to count is not a box on a map.
  visit order     the folders of each commit, in commit order, run-length encoded. A folder the
                  work came back to after leaving has a RETURN; one long stay does not.

Every view built on this payload therefore adds up to the same number, because they are all the
same sum sliced differently: total = every surviving file's churn + every deleted file's churn.
A deleted file has no box on a size map (it has no size), so the map prints the deleted total as a
sentence instead of dropping it, and the two together are the folder line's total and the
elevation's last point.

WHAT DOES NOT TRAVEL: a file name. The payload carries folder names, counts and line numbers. The
per-file rows are anonymous triples, because the size of a file is a fact about the work and the
name of a file is a fact about the person — repo C's filenames named two employers (privacy.py).
A folder name is checked like any other public label before it is allowed out.
"""
from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone

SCHEMA = 1
# A size map with more boxes than a phone has pixels is not a drawing. Past this, the per-file
# rows are dropped and the map is simply not offered; the folder totals still are.
MAX_FILES = 2000
MAX_FOLDERS = 40
MAX_MARKS = 400
MAX_LINES = 20_000_000
ROOT_FOLDER = "root"
SOURCE = "git numstat over the run's commits, and line counts at the end commit"
_FOLDER = re.compile(r"^[A-Za-z0-9._][A-Za-z0-9._-]{0,39}$")
_HASHES = re.compile(r"^[0-9a-f]{7,40}\.\.[0-9a-f]{7,40}$")
# The elevation is only honest about a clock it measured. Five points over ten minutes is the
# smallest shape that is a profile rather than two dots and a guess.
MIN_MARKS = 5
MIN_SPAN_S = 600


def _bad(message: str) -> None:
    raise ValueError(message)


def _git(root: str, args: list[str], timeout: int = 40) -> str | None:
    try:
        out = subprocess.run(["git", "-C", root] + args, capture_output=True, text=True,
                             timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout if out.returncode == 0 else None


def _z(when: datetime) -> str:
    return when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def folder_of(path: str) -> str:
    """The top-level folder a repository-relative path sits in. A root file is in `root`."""
    head = path.split("/", 1)
    if len(head) == 1:
        return ROOT_FOLDER
    name = head[0]
    return name if _FOLDER.match(name) else "other"


def end_state(root: str, commit: str) -> tuple[dict[str, int], set]:
    """({text path: lines}, every path) at `commit`.

    `git grep -c` on an empty pattern is `wc -l` per file: measured against `git show | wc -l` on
    this repository, equal on every file. `-I` drops binary blobs, which have no line to count and
    therefore no box on a size map, so both lists are returned and the difference is reported.
    """
    names = _git(root, ["ls-tree", "-r", "-z", "--name-only", commit])
    if names is None:
        return {}, set()
    every = {p for p in names.split("\0") if p}
    counted = _git(root, ["grep", "-I", "-z", "-c", "-e", "", commit, "--"])
    lines: dict[str, int] = {}
    prefix = commit + ":"
    for row in (counted or "").split("\n"):
        if not row.startswith(prefix) or "\0" not in row:
            continue
        path, _, count = row[len(prefix):].partition("\0")
        if count.isdigit() and path in every:
            lines[path] = int(count)
    return lines, every


def _numstat(root: str, args: list[str]) -> list[dict]:
    """[{hash, at, files, binary}] in commit order. A binary row has no line count to give."""
    raw = _git(root, ["log", "--numstat", "--no-renames",
                      "--pretty=format:%x01%H%x1f%cI"] + args)
    if raw is None:
        return []
    commits, seen = [], set()
    for chunk in raw.split("\x01"):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        head, _, rest = chunk.partition("\n")
        parts = head.split("\x1f")
        if len(parts) < 2 or len(parts[0]) < 7:
            continue
        if parts[0] in seen:
            continue
        seen.add(parts[0])
        files, binary = [], []
        for line in rest.split("\n"):
            cells = line.split("\t")
            if len(cells) != 3 or not cells[2]:
                continue
            if not cells[0].isdigit() or not cells[1].isdigit():
                binary.append(cells[2])      # a binary row is "-\t-\tpath": no lines to count
                continue
            files.append((int(cells[0]), int(cells[1]), cells[2]))
        from .gitwork import parse_iso

        commits.append({"hash": parts[0], "at": parse_iso(parts[1]), "files": files,
                        "binary": binary})
    commits.sort(key=lambda c: c["at"])
    return commits


def _build(root: str, commits: list[dict], head: str, label: str | None) -> dict | None:
    if not commits:
        return None
    churn: dict[str, int] = {}
    binary_paths: set = set()
    order: list[str] = []
    returns: dict[str, int] = {}
    marks: list[list[int]] = []
    first = commits[0]["at"]
    for commit in commits:
        folders = []
        for added, deleted, path in commit["files"]:
            churn[path] = churn.get(path, 0) + added + deleted
            folder = folder_of(path)
            if folder not in folders:
                folders.append(folder)
        binary_paths.update(commit.get("binary") or ())
        for folder in sorted(folders):
            # A RETURN is coming back after leaving. Two commits in a row in one folder is one
            # stay, so the sequence is run-length encoded before the arrivals are counted.
            if order and order[-1] == folder:
                continue
            if folder in order:
                returns[folder] = returns.get(folder, 0) + 1
            order.append(folder)
    churn = {path: moved for path, moved in churn.items() if moved}
    if not churn:
        return None

    lines_end, every = end_state(root, head)
    # A path git counted lines for and the end tree still holds is a box on the map. A path the
    # end tree does not hold at all was deleted. A path the tree holds but has no line count for
    # turned binary during the run: it is reported as binary, never as deleted, and its lines are
    # not in any total, because nothing measured them.
    alive = sorted(path for path in churn if path in lines_end)
    deleted_paths = sorted(path for path in churn if path not in every)
    turned = [path for path in churn if path in every and path not in lines_end]
    for path in turned:
        binary_paths.add(path)
        churn.pop(path, None)
    binary_end = max(0, len(every) - len(lines_end))
    binary_touched = len(binary_paths)
    deleted_lines = sum(churn[path] for path in deleted_paths)

    # The elevation is drawn from the same rows the totals are summed from, so it is built after
    # the excluded paths are known. A profile that climbed past its own total would be a fourth
    # number for one run.
    for commit in commits:
        moved = sum(added + deleted for added, deleted, path in commit["files"] if path in churn)
        if moved:
            marks.append([int(max(0, (commit["at"] - first).total_seconds())), moved])

    visited: list[str] = []
    for folder in order:
        if folder not in visited:
            visited.append(folder)
    resting = sorted({folder_of(path) for path in lines_end} - set(visited))
    names = visited + resting
    if len(names) > MAX_FOLDERS:
        return None
    index = {name: i for i, name in enumerate(names)}

    folders = [{"name": name, "files_end": 0, "lines_end": 0, "touched_files": 0,
                "lines_changed": 0, "deleted_files": 0, "deleted_lines": 0,
                "returns": returns.get(name, 0)} for name in names]
    rows: list[list[int]] = []
    for path, size in sorted(lines_end.items()):
        slot = index[folder_of(path)]
        moved = churn.get(path, 0)
        rows.append([slot, size, moved])
        folder = folders[slot]
        folder["files_end"] += 1
        folder["lines_end"] += size
        folder["lines_changed"] += moved
        folder["touched_files"] += 1 if moved else 0
    for path in deleted_paths:
        folder = folders[index[folder_of(path)]]
        folder["lines_changed"] += churn[path]
        folder["deleted_files"] += 1
        folder["deleted_lines"] += churn[path]

    payload = {
        "v": SCHEMA,
        "source": SOURCE,
        "folders": folders,
        "files": rows if len(rows) <= MAX_FILES else [],
        "files_capped": 0 if len(rows) <= MAX_FILES else len(rows),
        "binary_end": binary_end,
        "binary_touched": binary_touched,
        "deleted": {"files": len(deleted_paths), "lines": deleted_lines},
        "totals": {
            "files_end": len(rows),
            "files_touched": len(alive) + len(deleted_paths),
            "lines_end": sum(row[1] for row in rows),
            "lines_changed": sum(churn.values()),
        },
        "marks": marks[:MAX_MARKS],
        # The span of the POINTS, not of the window: the gate on the elevation asks whether this
        # run drew over ten real minutes, and a commit with nothing to count draws nothing.
        "span_s": marks[-1][0] if marks else 0,
        "commits": len(commits),
    }
    if label:
        payload["range"] = label
    return validate_file_work(payload)


def measure_range(root: str, base: str, head: str) -> dict | None:
    """The file work of one commit range, e.g. a pull request's `ccef745..eadbc3e`."""
    commits = _numstat(root, [f"{base}..{head}"])
    if not commits:
        return None
    short = _git(root, ["rev-parse", "--short", base]), _git(root, ["rev-parse", "--short", head])
    label = None
    if short[0] and short[1]:
        label = f"{short[0].strip()}..{short[1].strip()}"
    return _build(root, commits, commits[-1]["hash"], label if label and _HASHES.match(label) else None)


def measure_window(root: str, since: datetime, until: datetime) -> dict | None:
    """The file work of a run's own window. `--all` because the work is often off HEAD.

    The window is the run's, not a branch's, so the commits are collected by time on every ref and
    the end state is read at the LAST of them. Reading it at HEAD instead would measure a tree the
    run never produced whenever the author has since moved on.
    """
    commits = _numstat(root, ["--all", "--since", _z(since), "--until", _z(until)])
    if not commits:
        return None
    return _build(root, commits, commits[-1]["hash"], None)


def attach(run: dict, root: str | None, since: datetime | None, until: datetime | None) -> dict:
    """Put a measured `file_work` on a run that has a repository and a window. Never invent one.

    Opt out with AGENTGRINDER_NO_FILEWORK=1: this shells out to git several times, and a capture
    that runs in a loop over hundreds of transcripts should be able to say no.
    """
    if not isinstance(run, dict) or run.get("file_work") is not None:
        return run
    if not root or since is None or until is None or os.environ.get("AGENTGRINDER_NO_FILEWORK"):
        return run
    try:
        measured = measure_window(root, since, until)
    except (OSError, ValueError):
        return run
    if measured:
        run["file_work"] = measured
    return run


# ---------------------------------------------------------------------------------------------
# THE CONTRACT. Same shape as code_route.validate_code_route: a loud local error, never a card
# that quietly shows a weaker number. The totals are re-derived here rather than trusted, because
# a payload whose parts do not add up is the one defect a reader cannot see and cannot check.
# ---------------------------------------------------------------------------------------------
_ALLOWED_TOP = frozenset({"v", "source", "range", "folders", "files", "files_capped", "binary_end",
                          "binary_touched", "deleted", "totals", "marks", "span_s", "commits"})
_ALLOWED_FOLDER = frozenset({"name", "files_end", "lines_end", "touched_files", "lines_changed",
                             "deleted_files", "deleted_lines", "returns"})
_ALLOWED_TOTALS = frozenset({"files_end", "files_touched", "lines_end", "lines_changed"})


def _count(value, field: str, limit: int = MAX_LINES) -> int:
    if type(value) is not int or value < 0 or value > limit:
        _bad(f"{field} must be a non-negative whole number.")
    return value


def _keys(obj: dict, allowed: frozenset, name: str) -> None:
    unknown = set(obj) - allowed
    if unknown:
        _bad(f"Unknown {name} key: {sorted(unknown)[0]}")


def validate_file_work(value) -> dict:
    """Validate and return a normalised public file_work object."""
    if not isinstance(value, dict):
        _bad("file_work must be an object.")
    _keys(value, _ALLOWED_TOP, "file_work")
    if value.get("v") != SCHEMA:
        _bad("file_work.v must be 1.")
    source = value.get("source")
    if not isinstance(source, str) or not 8 <= len(source) <= 160:
        _bad("file_work.source must say how the numbers were measured.")
    label = value.get("range")
    if label is not None and (not isinstance(label, str) or not _HASHES.match(label)):
        _bad("file_work.range must be two short commit hashes, base..head.")

    folders = value.get("folders")
    if not isinstance(folders, list) or not 1 <= len(folders) <= MAX_FOLDERS:
        _bad(f"file_work.folders holds 1 to {MAX_FOLDERS} folders.")
    from . import privacy

    names, clean_folders = [], []
    for folder in folders:
        if not isinstance(folder, dict):
            _bad("each folder is an object.")
        _keys(folder, _ALLOWED_FOLDER, "folder")
        name = folder.get("name")
        # A folder name is the only word from the filesystem that travels, so it is checked twice:
        # for the shape of a path, and for a home directory flattened into a single segment
        # (`Users-someone-code`), which is how an account name reached a public card before.
        if (not isinstance(name, str) or not _FOLDER.match(name) or privacy.scan(name)
                or privacy.strip_home_names(name) != name):
            _bad("a folder name must be one short safe segment, never a path.")
        if name in names:
            _bad("folder names must be unique.")
        names.append(name)
        row = {"name": name}
        for field in ("files_end", "lines_end", "touched_files", "lines_changed",
                      "deleted_files", "deleted_lines", "returns"):
            row[field] = _count(folder.get(field), f"folder.{field}")
        if row["touched_files"] > row["files_end"]:
            _bad("a folder cannot change more files than it holds at the end.")
        clean_folders.append(row)

    files = value.get("files") or []
    if not isinstance(files, list) or len(files) > MAX_FILES:
        _bad(f"file_work.files holds at most {MAX_FILES} rows.")
    clean_files = []
    for row in files:
        if not isinstance(row, list) or len(row) != 3:
            _bad("each file row is [folder, lines_end, lines_changed].")
        slot = _count(row[0], "file.folder", len(clean_folders) - 1)
        clean_files.append([slot, _count(row[1], "file.lines_end"),
                            _count(row[2], "file.lines_changed")])

    deleted = value.get("deleted") or {}
    if not isinstance(deleted, dict) or set(deleted) - {"files", "lines"}:
        _bad("file_work.deleted is {files, lines}.")
    clean_deleted = {"files": _count(deleted.get("files", 0), "deleted.files"),
                     "lines": _count(deleted.get("lines", 0), "deleted.lines")}

    totals = value.get("totals")
    if not isinstance(totals, dict):
        _bad("file_work.totals is required.")
    _keys(totals, _ALLOWED_TOTALS, "totals")
    clean_totals = {field: _count(totals.get(field), f"totals.{field}") for field in
                    sorted(_ALLOWED_TOTALS)}

    marks = value.get("marks") or []
    if not isinstance(marks, list) or len(marks) > MAX_MARKS:
        _bad(f"file_work.marks holds at most {MAX_MARKS} points.")
    clean_marks, last = [], -1
    for mark in marks:
        if not isinstance(mark, list) or len(mark) != 2:
            _bad("each mark is [seconds from the first commit, lines changed].")
        at = _count(mark[0], "mark.at", 60 * 60 * 24 * 90)
        if at < last:
            _bad("marks must be in time order.")
        last = at
        clean_marks.append([at, _count(mark[1], "mark.lines")])

    out = {
        "v": SCHEMA,
        "source": source,
        "folders": clean_folders,
        "files": clean_files,
        "files_capped": _count(value.get("files_capped", 0), "files_capped"),
        "binary_end": _count(value.get("binary_end", 0), "binary_end"),
        "binary_touched": _count(value.get("binary_touched", 0), "binary_touched"),
        "deleted": clean_deleted,
        "totals": clean_totals,
        "marks": clean_marks,
        "span_s": _count(value.get("span_s", 0), "span_s", 60 * 60 * 24 * 90),
        "commits": _count(value.get("commits", 0), "commits", 100000),
    }
    if label:
        out["range"] = label
    _agree(out)
    return out


def _agree(work: dict) -> None:
    """ONE RUN, ONE TOTAL. Every view is a slice of this sum, so the sum is checked here once.

    A size map draws surviving files, a folder line draws folders and an elevation draws
    commits. If those three disagree the card is three claims about one run, and a reader has no
    way to tell which is the true one. So a payload whose parts do not add up is refused at the
    boundary rather than rendered.
    """
    folders, totals = work["folders"], work["totals"]
    changed = sum(folder["lines_changed"] for folder in folders)
    if changed != totals["lines_changed"]:
        _bad("folder line totals must add up to totals.lines_changed.")
    if sum(folder["deleted_lines"] for folder in folders) != work["deleted"]["lines"]:
        _bad("folder deleted lines must add up to deleted.lines.")
    if sum(folder["deleted_files"] for folder in folders) != work["deleted"]["files"]:
        _bad("folder deleted files must add up to deleted.files.")
    if sum(folder["touched_files"] for folder in folders) + work["deleted"]["files"] \
            != totals["files_touched"]:
        _bad("touched files must add up to totals.files_touched.")
    marks = sum(mark[1] for mark in work["marks"])
    if marks and marks != totals["lines_changed"]:
        _bad("the elevation marks must add up to totals.lines_changed.")
    if not work["files"]:
        return
    if len(work["files"]) != totals["files_end"]:
        _bad("the file rows must number totals.files_end.")
    if sum(row[1] for row in work["files"]) != totals["lines_end"]:
        _bad("the file rows must add up to totals.lines_end.")
    if sum(row[2] for row in work["files"]) + work["deleted"]["lines"] != totals["lines_changed"]:
        _bad("the drawn files plus the deleted files must add up to totals.lines_changed.")
    if sum(folder["files_end"] for folder in folders) != totals["files_end"]:
        _bad("folder file counts must add up to totals.files_end.")
    if sum(folder["lines_end"] for folder in folders) != totals["lines_end"]:
        _bad("folder line counts must add up to totals.lines_end.")


def has_size_map(work) -> bool:
    return bool(isinstance(work, dict) and work.get("files") and work["totals"]["lines_end"])


def has_folder_line(work) -> bool:
    return bool(isinstance(work, dict)
                and [f for f in work.get("folders") or [] if f["lines_changed"]])


def has_elevation(work) -> bool:
    """A profile needs a clock it measured: five points over ten minutes, or it is not offered."""
    if not isinstance(work, dict):
        return False
    marks = work.get("marks") or []
    return len(marks) >= MIN_MARKS and work.get("span_s", 0) >= MIN_SPAN_S
