"""Regression probes for capture dedupe, concurrent save, and disclosure honesty.

Independent review cases. Disposable PGlite TEST DATA only.
"""
from __future__ import annotations

import importlib.util
import json
import os
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
from pathlib import Path
from subprocess import PIPE, Popen
from urllib.parse import quote
import base64

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("round2", ROOT / "scripts" / "check-round2-integration.py")
round2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(round2)

ARTIFACTS = Path(os.environ.get("GRINDER_POST_RECOVERY_PROBE", "/tmp/agentic-strava-post-recovery-probe"))
ARTIFACTS.mkdir(parents=True, exist_ok=True)
HOST = round2.HOST


def capture(**fields):
    payload = {
        "schema_version": 1,
        "harness": "Cursor",
        "project": "agentgrinder-public TEST DATA",
        "turns_typed": 3,
        "duration_s": 600,
        "tool_calls": 9,
        "started": "2026-09-14T22:00:00+00:00",
        "measurement_revision": "a" * 64,
        "rig_mcps": 1,
        "rig_skills": 1,
        **fields,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return "#import=" + quote(base64.b64encode(json.dumps(payload).encode()).decode(), safe="")


def main():
    environment = os.environ.copy()
    environment["GRINDER_DISPOSABLE_TEST"] = "1"
    environment["DISPOSABLE_GRINDER"] = "1"
    process = Popen(
        [round2.NODE, str(ROOT / "scripts" / "disposable-supabase.mjs"), "--serve"],
        cwd=ROOT,
        env=environment,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    line = process.stdout.readline()
    try:
        info = json.loads(line)
    except Exception as exc:  # noqa: BLE001
        process.kill()
        raise RuntimeError("disposable supabase failed: " + line + (process.stderr.read() or "")) from exc
    disposable = info["url"]
    casey = info["casey"]
    before = round2.snapshot(disposable)
    site = ThreadingHTTPServer(("127.0.0.1", 0), round2.SiteHandler)
    threading.Thread(target=site.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{site.server_address[1]}"
    errors, observed = [], []

    def check(condition, message):
        (observed if condition else errors).append(message)

    def ids_for(sub):
        return [
            {"identity_id": i["id"], "id": i["id"], "user_id": sub, "provider": i["provider"], "identity_data": {}}
            for i in before["identities"]
            if i["user_id"] == sub
        ]

    try:
        with sync_playwright() as playwright:
            launch = {"headless": True, "args": ["--no-sandbox"]}
            if Path(round2.CHROME).exists():
                launch["executable_path"] = round2.CHROME
            browser = playwright.chromium.launch(**launch)
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.route(f"https://{HOST}/**", lambda route: round2.proxy(route, disposable))
            context.add_init_script(round2.session_script(round2.mint(casey, "test-casey", ids_for(casey))))
            page = context.new_page()

            def settle():
                page.wait_for_function("document.getElementById('me').textContent.trim()==='@test-casey'")
                page.wait_for_timeout(400)

            # 1. Distinct projects sharing started+harness must each save (no weak fallback).
            alpha = capture(
                measurement_revision=None,
                schema_version=0,
                project="alpha-project TEST DATA",
                started="2026-09-14T18:00:00+00:00",
            )
            beta = capture(
                measurement_revision=None,
                schema_version=0,
                project="beta-project TEST DATA",
                started="2026-09-14T18:00:00+00:00",
                turns_typed=7,
            )
            page.goto(base + "/" + alpha)
            settle()
            page.get_by_role("heading", name="Preview your run").wait_for()
            page.fill("#i_title", "TEST DATA alpha")
            page.fill("#i_caption", "TEST DATA alpha caption")
            page.select_option("#i_vis", "private")
            page.click("#i_pub")
            page.wait_for_url("**/?run=*", timeout=20000)
            alpha_id = page.url.split("run=", 1)[1].split("&", 1)[0]
            page.goto(base + "/" + beta)
            settle()
            page.get_by_role("heading", name="Preview your run").wait_for()
            page.fill("#i_title", "TEST DATA beta")
            page.fill("#i_caption", "TEST DATA beta caption must stay its own run")
            page.select_option("#i_vis", "private")
            page.click("#i_pub")
            page.wait_for_url("**/?run=*", timeout=20000)
            beta_id = page.url.split("run=", 1)[1].split("&", 1)[0]
            check(beta_id != alpha_id, "distinct projects with same started+harness stay separate runs")
            check("already saved" not in page.inner_text("#status"), "beta save is a new run, not a conflated open")

            # 2. Concurrent inserts of one measurement_revision → one row (unique index).
            rev = "b" * 64
            token = round2.mint(casey, "test-casey", ids_for(casey))["access_token"]
            profile = page.evaluate(
                "async () => { const {data}=await sb.from('profiles').select('id').eq('auth_uid',(await sb.auth.getUser()).data.user.id).single(); return data.id; }"
            )

            def insert_once(n):
                payload = {
                    "profile_id": profile,
                    "title": f"TEST DATA concurrent {n}",
                    "project": "concurrent TEST DATA",
                    "harness": "Cursor",
                    "prompts": 1,
                    "duration_s": 10,
                    "visibility": "private",
                    "started_at": "2026-09-14T19:00:00+00:00",
                    "schema_version": 1,
                    "measurement_revision": rev,
                    "caption": "TEST DATA concurrent",
                }
                req = urllib.request.Request(
                    disposable.rstrip("/") + "/rest/v1/runs",
                    data=json.dumps(payload).encode(),
                    method="POST",
                    headers={
                        "Authorization": "Bearer " + token,
                        "apikey": "disposable",
                        "Content-Type": "application/json",
                        "Content-Profile": "strava",
                        "Prefer": "return=representation",
                    },
                )
                try:
                    with round2.OPENER.open(req, timeout=30) as response:
                        return response.status, response.read().decode()[:100]
                except Exception as exc:  # noqa: BLE001
                    return "err", str(exc)[:160]

            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(insert_once, range(4)))
            after = page.evaluate(
                "async (rev) => { const {data,error}=await sb.from('runs').select('id').eq('measurement_revision', rev); return error?{error:error.message}:data; }",
                rev,
            )
            ok_inserts = sum(1 for status, _ in results if status == 200)
            conflicted = sum(1 for status, body in results if status == "err" and "23505" in body)
            check(isinstance(after, list) and len(after) == 1, "concurrent same measurement_revision yields one row (got " + str(after) + ")")
            conflicts = sum(1 for status, _ in results if status != 200)
            check(ok_inserts == 1 and conflicts >= 1, "concurrent arbitration: one 200 and conflicts for the rest (results=" + json.dumps(results) + ")")

            # 3. Disclosure names traveling fields present in this export.
            page.goto(base + "/?post")
            settle()
            page.goto(
                base
                + "/"
                + capture(
                    measurement_revision="c" * 64,
                    reach=True,
                    reach_reason="TEST DATA reach reason travels in the export",
                    progress_verdict="faster",
                    progress_delta=1.5,
                )
            )
            settle()
            page.get_by_role("heading", name="Preview your run").wait_for()
            contents = page.inner_text(".export-contents")
            page.locator(".panel details summary").click()
            details = page.locator(".panel details").inner_text()
            check("TEST DATA reach reason" in details, "imported JSON includes reach_reason bytes")
            check("carries only:" not in contents, "disclosure does not claim a false closed list")
            check("reach flag" in contents and "reason" in contents and "progress notes" in contents and "measurement references" in contents, "disclosure names fields present in this export: " + contents)

            # 4. measurement_revision on schema 0 is persisted and blocks a second insert.
            orphan_rev = "d" * 64
            orphan = capture(
                schema_version=0,
                measurement_revision=orphan_rev,
                started="2026-09-14T17:00:00+00:00",
                project="orphan-rev TEST DATA",
            )
            page.goto(base + "/?post")
            settle()
            page.goto(base + "/" + orphan)
            settle()
            page.get_by_role("heading", name="Preview your run").wait_for()
            page.fill("#i_title", "TEST DATA orphan rev 1")
            page.fill("#i_caption", "TEST DATA first save keeps the measurement reference")
            page.select_option("#i_vis", "private")
            page.click("#i_pub")
            page.wait_for_url("**/?run=*", timeout=20000)
            first_id = page.url.split("run=", 1)[1].split("&", 1)[0]
            stored = page.evaluate(
                "async (id) => { const {data,error}=await sb.from('runs').select('id,measurement_revision').eq('id', id).single(); return error?{error:error.message}:data; }",
                first_id,
            )
            check(stored.get("measurement_revision") == orphan_rev, "schema 0 export still persists measurement_revision: " + json.dumps(stored))
            page.goto(base + "/?post")
            settle()
            page.goto(base + "/" + orphan)
            settle()
            page.get_by_role("heading", name="Preview your run").wait_for()
            page.fill("#i_title", "TEST DATA orphan rev 2")
            page.fill("#i_caption", "TEST DATA second save must open the first")
            page.select_option("#i_vis", "private")
            page.click("#i_pub")
            page.wait_for_url("**/?run=*", timeout=20000)
            second_id = page.url.split("run=", 1)[1].split("&", 1)[0]
            status4 = page.inner_text("#status")
            rows = page.evaluate(
                "async (rev) => { const {data}=await sb.from('runs').select('id,title,measurement_revision').eq('measurement_revision', rev); return data; }",
                orphan_rev,
            )
            check(
                second_id == first_id and "already saved" in status4,
                "retry finds the persisted measurement_revision (first="
                + first_id
                + " second="
                + second_id
                + " status="
                + status4[:120]
                + " rows="
                + json.dumps(rows)
                + ")",
            )
            check(isinstance(rows, list) and len(rows) == 1, "only one row for the orphan measurement_revision")

            browser.close()
    finally:
        site.shutdown()
        process.terminate()
        process.wait(timeout=10)

    for message in observed:
        print("ok  " + message)
    for message in errors:
        print("FAIL " + message)
    print(json.dumps({"checks_passed": len(observed), "checks_failed": len(errors), "artifacts": str(ARTIFACTS)}))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
