"""Private post-session capture for Cursor.

Cursor exposes no documented local post-composer hook. Pacecard therefore checks the local
state.vscdb with a user scheduler. It reads completed composer ids and the redacted bubble clock,
stores one private draft per composer, and opens only a loopback preview.
"""
from __future__ import annotations

import glob
import hashlib
import http.server
import json
import os
import plistlib
import shlex
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from . import cursor_tree

DEFAULT_ROOT = Path.home() / ".agentgrinder" / "hook"
DEFAULT_PORT = 8765
LABEL = "app.pacecard.cursor-hook"
CRON_MARKER = "# pacecard-cursor-hook"


def _root(value=None) -> Path:
    root = Path(value or DEFAULT_ROOT).expanduser()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    return root


def _state(root: Path) -> sqlite3.Connection:
    db = sqlite3.connect(root / "state.db")
    db.execute("create table if not exists processed(composer_id text primary key, captured_at text not null default CURRENT_TIMESTAMP)")
    os.chmod(root / "state.db", 0o600)
    return db


def finished_composers(conn: sqlite3.Connection) -> list[str]:
    """Completed top-level composers, oldest first. No composer text is returned."""
    out = []
    for key, raw in conn.execute(
            "select key,value from cursorDiskKV where key like 'composerData:%'"):
        try:
            composer = json.loads(raw)
        except (TypeError, ValueError):
            continue
        if not isinstance(composer, dict) or composer.get("status") != "completed":
            continue
        info = composer.get("subagentInfo")
        if isinstance(info, dict) and info.get("parentComposerId"):
            continue
        composer_id = key.split(":", 1)[1]
        updated = composer.get("lastUpdatedAt") or composer.get("createdAt") or 0
        out.append((updated, composer_id))
    out.sort(key=lambda item: (item[0], item[1]))
    return [composer_id for _, composer_id in out]


def _transcript(composer_id: str) -> Path | None:
    pattern = str(Path.home() / ".cursor/projects/*/agent-transcripts" / composer_id / "*.jsonl")
    files = [Path(path) for path in glob.glob(pattern) if Path(path).is_file()]
    return max(files, key=lambda path: path.stat().st_mtime) if files else None


def _capture(composer_id: str) -> dict | None:
    path = _transcript(composer_id)
    if path is None:
        return None
    from .ingest import parse_cursor_session
    run = parse_cursor_session(str(path))
    # Message excerpts and path-derived region labels have no place in an automatic card.
    run.pop("private_title_prompt", None)
    run.pop("route_legend", None)
    run["composer_id"] = composer_id
    return run


def _store_private(root: Path, composer_id: str, run: dict) -> str:
    from .capture import connect
    db = connect(root / "capture")
    draft_id = hashlib.sha256(("cursor-composer:" + composer_id).encode()).hexdigest()
    source = "cursor-composer:" + composer_id
    try:
        with db:
            db.execute(
                """insert into drafts(id,source,harness,started,digest,payload)
                   values(?,?,?,?,?,?)
                   on conflict(id) do update set payload=excluded.payload,
                     digest=excluded.digest,updated_at=CURRENT_TIMESTAMP""",
                (draft_id, source, "cursor", run.get("started") or "unknown",
                 hashlib.sha256(json.dumps(run, sort_keys=True).encode()).hexdigest(),
                 json.dumps(run)),
            )
    finally:
        db.close()
    cards = root / "cards"
    cards.mkdir(mode=0o700, exist_ok=True)
    from .metrics import build_activity
    from .render import render_card
    card = cards / f"{composer_id}.html"
    card.write_text(render_card(build_activity(run)), encoding="utf-8")
    os.chmod(card, 0o600)
    return card.name


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def _ensure_server(root: Path, port: int) -> None:
    def ready() -> bool:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                return True
        except OSError:
            return False

    pid_file = root / "server.pid"
    try:
        if _pid_alive(int(pid_file.read_text().strip())) and ready():
            return
    except (OSError, ValueError):
        pass
    command = [sys.executable, "-m", "agentgrinder", "hook", "serve",
               "--directory", str(root), "--port", str(port)]
    process = subprocess.Popen(
        command, cwd=Path(__file__).resolve().parents[1],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    pid_file.write_text(str(process.pid))
    for _ in range(20):
        if ready():
            return
        if process.poll() is not None:
            break
        time.sleep(0.05)
    raise OSError(f"Could not start the private preview at 127.0.0.1:{port}.")


def run_once(directory=None, db=None, port: int = DEFAULT_PORT,
             capture_one=None, open_one=None) -> dict:
    root = _root(directory)
    capture_one = capture_one or _capture
    open_one = open_one or (lambda url: webbrowser.open(url))
    source = Path(db).expanduser() if db else cursor_tree.db_path()
    created = []
    with cursor_tree.CopiedDb(source) as cursor_db:
        finished = finished_composers(cursor_db)
    state = _state(root)
    try:
        for composer_id in finished:
            with state:
                claimed = state.execute(
                    "insert or ignore into processed(composer_id) values(?)", (composer_id,))
            if claimed.rowcount == 0:
                continue
            try:
                run = capture_one(composer_id)
                if run is None:
                    with state:
                        state.execute("delete from processed where composer_id=?", (composer_id,))
                    continue
                card_name = _store_private(root, composer_id, run)
            except Exception:
                with state:
                    state.execute("delete from processed where composer_id=?", (composer_id,))
                raise
            created.append((composer_id, card_name))
    finally:
        state.close()
    if created:
        _ensure_server(root, port)
        open_one(f"http://127.0.0.1:{port}/{created[-1][1]}")
    return {"captured": len(created), "composer_ids": [item[0] for item in created]}


def _command(directory: Path, port: int, action: str = "run", db=None) -> list[str]:
    command = [sys.executable, "-m", "agentgrinder", "hook", action, "--harness", "cursor",
               "--directory", str(directory), "--port", str(port)]
    if db is not None and action in ("run", "watch"):
        command.extend(["--db", str(Path(db).expanduser())])
    return command


def _seed(root: Path, db=None) -> int:
    source = Path(db).expanduser() if db else cursor_tree.db_path()
    with cursor_tree.CopiedDb(source) as cursor_db:
        ids = finished_composers(cursor_db)
    state = _state(root)
    try:
        with state:
            state.executemany("insert or ignore into processed(composer_id) values(?)",
                              ((composer_id,) for composer_id in ids))
    finally:
        state.close()
    return len(ids)


def _install_launchd(root: Path, port: int, db=None) -> dict:
    agents = Path.home() / "Library/LaunchAgents"
    agents.mkdir(parents=True, exist_ok=True)
    path = agents / f"{LABEL}.plist"
    payload = {
        "Label": LABEL,
        "ProgramArguments": _command(root, port, db=db),
        "WorkingDirectory": str(Path(__file__).resolve().parents[1]),
        "StartInterval": 30,
        "RunAtLoad": True,
        "StandardOutPath": str(root / "hook.log"),
        "StandardErrorPath": str(root / "hook.log"),
    }
    path.write_bytes(plistlib.dumps(payload))
    subprocess.run(["launchctl", "unload", str(path)], capture_output=True)
    subprocess.run(["launchctl", "load", str(path)], check=True)
    return {"mode": "launchd", "config": str(path)}


def _systemd_available() -> bool:
    if not shutil.which("systemctl"):
        return False
    return subprocess.run(
        ["systemctl", "--user", "show-environment"],
        capture_output=True, timeout=5,
    ).returncode == 0


def _install_systemd(root: Path, port: int, db=None) -> dict:
    folder = Path.home() / ".config/systemd/user"
    folder.mkdir(parents=True, exist_ok=True)
    service = folder / "pacecard-cursor-hook.service"
    timer = folder / "pacecard-cursor-hook.timer"
    command = " ".join(shlex.quote(part) for part in _command(root, port, db=db))
    service.write_text(
        "[Unit]\nDescription=Pacecard private Cursor capture\n\n"
        "[Service]\nType=oneshot\n"
        f"WorkingDirectory={Path(__file__).resolve().parents[1]}\nExecStart={command}\n")
    timer.write_text(
        "[Unit]\nDescription=Check for completed Cursor composers\n\n"
        "[Timer]\nOnBootSec=30\nOnUnitActiveSec=30\nAccuracySec=5\n\n"
        "[Install]\nWantedBy=timers.target\n")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", timer.name], check=True)
    return {"mode": "systemd-user-timer", "config": str(timer), "service": str(service)}


def _install_cron(root: Path, port: int, db=None) -> dict | None:
    if not shutil.which("crontab"):
        return None
    current = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    lines = [] if current.returncode else [
        line for line in current.stdout.splitlines() if CRON_MARKER not in line]
    command = " ".join(shlex.quote(part) for part in _command(root, port, db=db))
    lines.append(f"* * * * * cd {shlex.quote(str(Path(__file__).resolve().parents[1]))} && {command} {CRON_MARKER}")
    subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True, check=True)
    return {"mode": "cron", "config": "user crontab"}


def _install_watcher(root: Path, port: int, db=None) -> dict:
    process = subprocess.Popen(
        _command(root, port, "watch", db), cwd=Path(__file__).resolve().parents[1],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=open(root / "hook.log", "a"), start_new_session=True,
    )
    (root / "watcher.pid").write_text(str(process.pid))
    return {"mode": "polling-watcher", "config": str(root / "watcher.pid")}


def install(directory=None, db=None, port: int = DEFAULT_PORT) -> dict:
    root = _root(directory)
    current = status(root)
    if current.get("installed") and current.get("active"):
        return current
    seeded = _seed(root, db)
    if sys.platform == "darwin":
        record = _install_launchd(root, port, db)
    elif _systemd_available():
        record = _install_systemd(root, port, db)
    else:
        record = _install_watcher(root, port, db)
    record.update({"harness": "cursor", "directory": str(root), "port": port,
                   "existing_composers_ignored": seeded,
                   "reason": "Cursor exposes no documented local completion hook, so Pacecard checks state.vscdb on a local timer."})
    (root / "install.json").write_text(json.dumps(record, indent=2))
    return record


def _active(record: dict, root: Path) -> bool:
    mode = record.get("mode")
    if mode == "launchd":
        return subprocess.run(
            ["launchctl", "print", f"gui/{os.getuid()}/{LABEL}"],
            capture_output=True,
        ).returncode == 0
    if mode == "systemd-user-timer":
        return subprocess.run(
            ["systemctl", "--user", "is-active", "--quiet", "pacecard-cursor-hook.timer"],
            capture_output=True,
        ).returncode == 0
    if mode == "cron":
        current = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        return current.returncode == 0 and CRON_MARKER in current.stdout
    if mode == "polling-watcher":
        try:
            return _pid_alive(int((root / "watcher.pid").read_text().strip()))
        except (OSError, ValueError):
            return False
    return False


def status(directory=None) -> dict:
    root = _root(directory)
    try:
        record = json.loads((root / "install.json").read_text())
    except (OSError, ValueError):
        return {"installed": False, "directory": str(root)}
    state = _state(root)
    try:
        captured = state.execute("select count(*) from processed").fetchone()[0]
    finally:
        state.close()
    return {**record, "installed": True, "active": _active(record, root),
            "processed_composers": captured}


def _kill_pid(path: Path) -> None:
    try:
        pid = int(path.read_text().strip())
        command = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            capture_output=True, text=True,
        ).stdout
        if _pid_alive(pid) and "agentgrinder hook" in command:
            os.kill(pid, signal.SIGTERM)
    except (OSError, ValueError):
        pass
    path.unlink(missing_ok=True)


def uninstall(directory=None) -> dict:
    root = _root(directory)
    prior = status(root)
    mode = prior.get("mode")
    if mode == "launchd":
        path = Path(prior["config"])
        subprocess.run(["launchctl", "unload", str(path)], capture_output=True)
        path.unlink(missing_ok=True)
    elif mode == "systemd-user-timer":
        subprocess.run(["systemctl", "--user", "disable", "--now", "pacecard-cursor-hook.timer"],
                       capture_output=True)
        Path(prior["config"]).unlink(missing_ok=True)
        Path(prior["service"]).unlink(missing_ok=True)
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    elif mode == "cron" and shutil.which("crontab"):
        current = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        lines = [line for line in current.stdout.splitlines() if CRON_MARKER not in line]
        subprocess.run(["crontab", "-"], input="\n".join(lines) + ("\n" if lines else ""),
                       text=True, check=True)
    _kill_pid(root / "watcher.pid")
    _kill_pid(root / "server.pid")
    (root / "install.json").unlink(missing_ok=True)
    return {"installed": False, "private_captures_kept": True, "directory": str(root)}


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        return


def serve(directory=None, port: int = DEFAULT_PORT) -> int:
    root = _root(directory)
    cards = root / "cards"
    cards.mkdir(mode=0o700, exist_ok=True)
    handler = lambda *args, **kwargs: _QuietHandler(*args, directory=str(cards), **kwargs)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    server.serve_forever()
    return 0


def watch(directory=None, db=None, port: int = DEFAULT_PORT) -> int:
    while True:
        try:
            run_once(directory, db, port)
        except (FileNotFoundError, sqlite3.DatabaseError, OSError, ValueError):
            pass
        time.sleep(30)


def add_parser(sub) -> None:
    parser = sub.add_parser("hook", help="capture completed sessions privately on this machine")
    commands = parser.add_subparsers(dest="hook_command", required=True)
    for name in ("install", "status", "uninstall", "run", "watch", "serve"):
        command = commands.add_parser(name)
        command.add_argument("--harness", choices=["cursor"], default="cursor")
        command.add_argument("--directory")
        command.add_argument("--port", type=int, default=DEFAULT_PORT)
        if name in ("install", "run", "watch"):
            command.add_argument("--db")


def run_cli(args) -> int:
    try:
        if args.hook_command == "install":
            output = install(args.directory, args.db, args.port)
        elif args.hook_command == "status":
            output = status(args.directory)
        elif args.hook_command == "uninstall":
            output = uninstall(args.directory)
        elif args.hook_command == "run":
            output = run_once(args.directory, args.db, args.port)
        elif args.hook_command == "watch":
            return watch(args.directory, args.db, args.port)
        else:
            return serve(args.directory, args.port)
        print(json.dumps(output, indent=2))
        return 0
    except (FileNotFoundError, OSError, sqlite3.DatabaseError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1
