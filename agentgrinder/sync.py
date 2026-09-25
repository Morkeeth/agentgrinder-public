"""Automatic fetch: new agent sessions become private STRIVE drafts, with no file picking.

Oscar, 25 Sep 2026: "the uploads is awful ... automatic fetch". Connect once in the browser (it
issues a private upload token), run `agentgrinder sync --install --token <token>` once, and from
then on every finished Claude Code, Cursor and Codex session on this computer is uploaded as a
private run. Only the counts leave the machine: the payload is agent_api.run_payload, the same
allowlist as `agentgrinder agent draft`, with no title, no prompt text and no paths. Nothing is
public until the person publishes it on the site.

A session is "finished" when its file has not changed for IDLE_SECONDS. Each finished file is
sent once: the Idempotency-Key is derived from the file identity, so a retry or a second
machine run of the same file returns the existing run instead of a duplicate, and the local
state file remembers what was sent.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from . import ingest

DEFAULT_SITE = os.environ.get("STRIVE_URL", "https://agentic-strava.vercel.app")
STATE_DIR = Path(os.environ.get("STRIVE_HOME", str(Path.home() / ".strive")))
IDLE_SECONDS = 10 * 60
SINCE_DAYS = 7
INTERVAL = 15 * 60
MAX_PER_SYNC = 20   # the database rate-limits uploads; the rest go on the next sync
LABEL = "app.strive.sync"
NAMESPACE = uuid.UUID("7d3f0a52-6d3c-4b7e-9a4f-2f0c6a1e5b11")
UVX_SOURCE = "git+https://github.com/Morkeeth/agentgrinder-public"


def _paths():
    return {"token": STATE_DIR / "token", "state": STATE_DIR / "synced.json", "log": STATE_DIR / "sync.log"}


def discover(now: float | None = None, since_days: int = SINCE_DAYS, idle: int = IDLE_SECONDS) -> list[tuple[str, str]]:
    """(harness, path) for every finished session changed in the last since_days, oldest first."""
    now = time.time() if now is None else now
    found: dict[str, tuple[str, float]] = {}
    sources = [("claude", glob.glob(os.path.expanduser(ingest.CLAUDE_GLOB))),
               ("cursor", glob.glob(os.path.expanduser(ingest.CURSOR_GLOB))),
               ("codex", ingest.codex_session_files())]
    for harness, files in sources:
        for path in files:
            try:
                mtime = os.path.getmtime(path)
            except OSError:
                continue
            if now - mtime < idle or now - mtime > since_days * 86400:
                continue
            found.setdefault(path, (harness, mtime))
    return [(h, p) for p, (h, _) in sorted(found.items(), key=lambda kv: kv[1][1])]


def file_key(harness: str, path: str) -> str:
    st = os.stat(path)
    return f"{harness}|{os.path.realpath(path)}|{st.st_size}|{st.st_mtime_ns}"


def idempotency_key(key: str) -> str:
    return str(uuid.uuid5(NAMESPACE, key))


def parse(harness: str, path: str) -> dict:
    if harness == "cursor":
        return ingest.parse_cursor_session(path)
    if harness == "codex":
        return ingest.parse_codex_session(path)
    return ingest.parse_session(path)


def payload_for(harness: str, path: str) -> dict:
    from .agent_api import run_payload
    run = parse(harness, path)
    run.pop("title", None)
    return run_payload(run, "private")


def read_token(explicit: str | None = None) -> str | None:
    if explicit:
        return explicit.strip()
    env = os.environ.get("STRIVE_AGENT_TOKEN")
    if env:
        return env.strip()
    try:
        return _paths()["token"].read_text().strip() or None
    except OSError:
        return None


def save_token(token: str) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(STATE_DIR, 0o700)
    path = _paths()["token"]
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(token.strip() + "\n")
    os.chmod(path, 0o600)
    return path


def load_state() -> dict:
    try:
        data = json.loads(_paths()["state"].read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _paths()["state"].with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True))
    tmp.replace(_paths()["state"])


def upload(payload: dict, token: str, key: str, site: str = DEFAULT_SITE, opener=urllib.request.urlopen) -> dict:
    body = json.dumps(payload).encode()
    request = urllib.request.Request(site.rstrip("/") + "/api/agent/runs", data=body, method="POST", headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + token, "Idempotency-Key": key})
    try:
        with opener(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            message = json.load(error).get("error") or ""
        except (ValueError, AttributeError):
            message = ""
        raise RuntimeError(f"HTTP {error.code}: {message}".strip()) from None
    except urllib.error.URLError:
        raise RuntimeError("STRIVE is unreachable. The next sync retries.") from None


def sync_once(token: str, site: str = DEFAULT_SITE, dry_run: bool = False, since_days: int = SINCE_DAYS,
              now: float | None = None, opener=urllib.request.urlopen, out=print) -> dict:
    state = load_state()
    counts = {"sent": 0, "skipped": 0, "failed": 0, "already": 0}
    for harness, path in discover(now=now, since_days=since_days):
        if counts["sent"] >= MAX_PER_SYNC:
            break
        try:
            key = file_key(harness, path)
        except OSError:
            continue
        digest = hashlib.sha256(key.encode()).hexdigest()   # the state file holds no paths
        if digest in state:
            counts["already"] += 1
            continue
        try:
            payload = payload_for(harness, path)
        except (ValueError, KeyError, TypeError, OSError):
            # No typed turn, an unreadable file or a session still being written: not a run.
            state[digest] = {"status": "skipped", "at": int(time.time())}
            counts["skipped"] += 1
            continue
        if dry_run:
            out(f"  would send a private {payload.get('harness') or harness} run: "
                f"{payload.get('tool_calls') or 0} tool calls, {payload.get('turns_typed') or 0} turns")
            counts["sent"] += 1
            continue
        try:
            result = upload(payload, token, idempotency_key(key), site, opener)
        except RuntimeError as error:
            out(f"  not sent ({harness}): {error}")
            counts["failed"] += 1
            if "HTTP 401" in str(error) or "HTTP 403" in str(error):
                break   # a revoked or expired token fails every file; stop and say so once
            continue
        state[digest] = {"status": "sent", "id": result.get("id"), "at": int(time.time())}
        counts["sent"] += 1
    if not dry_run:
        save_state(state)
    return counts


def _command() -> list[str]:
    uvx = shutil.which("uvx")
    if uvx:
        return [uvx, "--from", UVX_SOURCE, "agentgrinder", "sync"]
    return [sys.executable, "-m", "agentgrinder", "sync"]


def install(interval: int = INTERVAL) -> str:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    log = str(_paths()["log"])
    if sys.platform == "darwin":
        import plistlib
        agents = Path.home() / "Library" / "LaunchAgents"
        agents.mkdir(parents=True, exist_ok=True)
        plist = agents / f"{LABEL}.plist"
        plist.write_bytes(plistlib.dumps({"Label": LABEL, "ProgramArguments": _command(), "StartInterval": interval,
                                          "RunAtLoad": True, "StandardOutPath": log, "StandardErrorPath": log}))
        subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
        subprocess.run(["launchctl", "load", str(plist)], check=True)
        return f"Installed: every {interval // 60} minutes (launchd {LABEL}). Log: {log}"
    marker = "# strive-sync"
    line = f"*/{max(1, interval // 60)} * * * * {' '.join(_command())} >> {log} 2>&1 {marker}"
    current = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    kept = [row for row in current.splitlines() if marker not in row]
    subprocess.run(["crontab", "-"], input="\n".join(kept + [line]) + "\n", text=True, check=True)
    return f"Installed: every {interval // 60} minutes (cron). Log: {log}"


def uninstall() -> str:
    if sys.platform == "darwin":
        plist = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
        if plist.exists():
            subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
            plist.unlink()
    else:
        current = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
        kept = [row for row in current.splitlines() if "# strive-sync" not in row]
        subprocess.run(["crontab", "-"], input="\n".join(kept) + "\n", text=True, check=False)
    return "Automatic sync is off. The token file stays in ~/.strive until you delete it."


def add_parser(sub) -> None:
    p = sub.add_parser("sync", help="upload new agent sessions automatically as private STRIVE runs")
    p.add_argument("--token", help="the private upload token from the Connect page (saved to ~/.strive/token)")
    p.add_argument("--install", action="store_true", help="run sync every 15 minutes in the background")
    p.add_argument("--uninstall", action="store_true", help="stop automatic sync")
    p.add_argument("--dry-run", action="store_true", help="show what would be sent; send nothing")
    p.add_argument("--since-days", type=int, default=SINCE_DAYS, help="look back this many days (default 7)")
    p.add_argument("--site", default=DEFAULT_SITE, help=argparse_help_site())


def argparse_help_site() -> str:
    return "STRIVE address (default https://agentic-strava.vercel.app)"


def run_cli(args) -> int:
    if args.uninstall:
        print(uninstall())
        return 0
    token = read_token(args.token)
    if args.token:
        print(f"Token saved to {save_token(args.token)} (only you can read it).")
    if not token and not args.dry_run:
        print("No token yet. Sign in on STRIVE, open Connect, press Turn on automatic sync, and run the line it shows.")
        return 1
    counts = sync_once(token or "", site=args.site, dry_run=args.dry_run, since_days=args.since_days)
    verb = "would send" if args.dry_run else "sent"
    print(f"STRIVE sync: {verb} {counts['sent']} private run(s), {counts['already']} already sent, "
          f"{counts['skipped']} skipped, {counts['failed']} not sent. Private until you publish them.")
    if args.install:
        print(install())
    return 0 if not counts["failed"] else 2
