"""Capture > preview > deliberate post, with the failures a new builder actually hits.

Drives site/index.html and site/social.js as committed against the disposable PGlite shim
(scripts/disposable-supabase.mjs). Proves, on a phone viewport:

  1. offline save: the draft survives, nothing is posted, recovery is on screen, no retry fires
     by itself; Try again is the person's click and makes exactly one run.
  2. lost response: the insert lands but the browser never hears back; Try again finds the run
     the first attempt made instead of posting a second one.
  3. same capture saved again on purpose: opens the existing run, says the caption was not applied.
  4. a chopped import link says so, instead of falling through to the landing page.
  5. an exact-reply link ranked past the 12-page load (331 replies; page one plus 12 more pages is 325) is rendered directly, not
     called removed; a reply that does not exist is called removed or not visible.

Disposable TEST DATA identities only. No hosted OAuth, no consenting person, no public write.
"""
from __future__ import annotations

import importlib.util
import json
import os
import threading
import uuid
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

ARTIFACTS = Path(os.environ.get("GRINDER_POST_RECOVERY_ARTIFACTS", "/tmp/agentic-strava-post-recovery"))
ARTIFACTS.mkdir(parents=True, exist_ok=True)
HOST = round2.HOST


def capture(revision, started: str):
    payload = {
        "schema_version": 1,
        "harness": "Cursor",
        "project": "agentgrinder-public TEST DATA",
        "turns_typed": 3,
        "duration_s": 600,
        "tool_calls": 9,
        "started": started,
        "rig_mcps": 2,
        "rig_skills": 1,
        "rig_notes": "TEST DATA stack notes",
    }
    if revision:
        payload["measurement_revision"] = revision
    return "#import=" + quote(base64.b64encode(json.dumps(payload).encode()).decode(), safe="")


def main():
    environment = os.environ.copy()
    environment["GRINDER_DISPOSABLE_TEST"] = "1"
    environment["DISPOSABLE_GRINDER"] = "1"
    process = Popen([round2.NODE, str(ROOT / "scripts" / "disposable-supabase.mjs"), "--serve"], cwd=ROOT, env=environment, stdout=PIPE, stderr=PIPE, text=True)
    line = process.stdout.readline()
    try:
        info = json.loads(line)
    except Exception as exc:  # noqa: BLE001
        process.kill()
        raise RuntimeError("disposable supabase failed to start: " + line + (process.stderr.read() or "")) from exc
    disposable = info["url"]
    casey, riley = info["casey"], info["riley"]
    before = round2.snapshot(disposable)
    site = ThreadingHTTPServer(("127.0.0.1", 0), round2.SiteHandler)
    threading.Thread(target=site.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{site.server_address[1]}"
    errors, observed, js_errors = [], [], []

    def check(condition, message):
        (observed if condition else errors).append(message)

    def ids_for(sub):
        return [{"identity_id": i["id"], "id": i["id"], "user_id": sub, "provider": i["provider"], "identity_data": {}} for i in before["identities"] if i["user_id"] == sub]

    def shot(page, name):
        page.screenshot(path=str(ARTIFACTS / name), full_page=True)

    try:
        with sync_playwright() as playwright:
            launch = {"headless": True, "args": ["--no-sandbox"]}
            if Path(round2.CHROME).exists():
                launch["executable_path"] = round2.CHROME
            browser = playwright.chromium.launch(**launch)

            def context_for(sub=None, handle=None, width=390, height=844):
                context = browser.new_context(viewport={"width": width, "height": height})
                context.route(f"https://{HOST}/**", lambda route: round2.proxy(route, disposable))
                if sub:
                    context.add_init_script(round2.session_script(round2.mint(sub, handle, ids_for(sub))))
                page = context.new_page()
                page.on("pageerror", lambda error: js_errors.append((handle or "signed-out") + ": " + str(error)))
                return context, page

            def settle(page, handle):
                page.wait_for_function("document.getElementById('me').textContent.trim()==='@" + handle + "'")
                page.wait_for_timeout(600)

            def all_runs(page):
                return page.evaluate("async () => { const {data,error}=await sb.from('runs').select('id,caption,measurement_revision').order('created_at'); return error?{error:error.message}:data; }")

            seeded = {"ids": None}

            def my_runs(page):
                # The disposable fixture seeds one TEST DATA run for Casey; only rows this walk makes count.
                rows = all_runs(page)
                if seeded["ids"] is None:
                    seeded["ids"] = {r["id"] for r in rows}
                    return []
                return [r for r in rows if r["id"] not in seeded["ids"]]

            first = capture("c" * 64, "2026-09-14T20:00:00+00:00")
            casey_context, cp = context_for(casey, "test-casey")
            posts = {"count": 0}

            def gate(route):
                # Every POST to runs while the gate is closed is a failed connection: the browser
                # sees nothing, the server sees nothing. Counted so a silent auto-retry shows up.
                if route.request.method == "POST" and "/rest/v1/runs" in route.request.url:
                    posts["count"] += 1
                    if gate.mode == "offline":
                        route.abort("connectionfailed")
                        return
                    if gate.mode == "lost":
                        # The insert reaches the server; the response never reaches the browser.
                        import urllib.request
                        request = route.request
                        target = request.url.replace("https://" + HOST, disposable)
                        headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
                        outgoing = urllib.request.Request(target, data=request.post_data.encode(), method="POST", headers=headers)
                        with round2.OPENER.open(outgoing, timeout=30) as response:
                            response.read()
                        route.abort("connectionfailed")
                        return
                round2.proxy(route, disposable)

            gate.mode = "open"
            casey_context.unroute(f"https://{HOST}/**")
            casey_context.route(f"https://{HOST}/**", gate)

            # 1. Offline at the moment of the deliberate post.
            cp.goto(base + "/" + first)
            settle(cp, "test-casey")
            my_runs(cp)
            cp.get_by_role("heading", name="Preview your run").wait_for()
            contents = cp.inner_text(".export-contents")
            check("project folder name" in contents and "route as numbers" in contents and "never carries prompts, code or file paths" in contents and "how many MCPs and skills" in contents and "the stack notes you wrote" in contents, "preview: says in words what the export carries and what it never carries: " + contents[:80])
            cp.fill("#i_title", "TEST DATA recovery session")
            cp.fill("#i_caption", "TEST DATA: caption typed before the connection dropped.")
            cp.select_option("#i_vis", "public")
            gate.mode = "offline"
            cp.click("#i_pub")
            cp.locator("#i_recover:not([hidden])").wait_for(timeout=15000)
            recover_text = cp.inner_text("#i_recover")
            check("Not saved" in recover_text and "could not be reached" in recover_text, "offline: recovery names the failure and that nothing was posted: " + recover_text[:90])
            check("Try again" in recover_text and "already saved" in recover_text, "offline: recovery offers Try again and says it checks for an existing run first")
            check(cp.get_by_role("link", name="Your runs").count() == 1, "offline: recovery links to Your runs")
            check(cp.input_value("#i_caption") == "TEST DATA: caption typed before the connection dropped." and cp.input_value("#i_vis") == "public", "offline: caption and audience survive on the page")
            check("import=" in cp.url, "offline: the capture stays on the URL, nothing navigated away")
            cp.wait_for_timeout(2500)
            check(posts["count"] == 1, "offline: no automatic retry fired (POST count " + str(posts["count"]) + ")")
            check(my_runs(cp) == [], "offline: no run from this walk exists on the server")
            shot(cp, "01-offline-save-recovery-mobile.png")

            # Connection back, the person presses Try again: exactly one run.
            gate.mode = "open"
            cp.click("#i_retry")
            cp.wait_for_url("**/?run=*", timeout=20000)
            run_id = cp.url.split("run=", 1)[1].split("&", 1)[0]
            cp.get_by_text("TEST DATA: caption typed before the connection dropped.").wait_for()
            rows = my_runs(cp)
            check(len(rows) == 1 and rows[0]["id"] == run_id and rows[0]["measurement_revision"] == "c" * 64, "try again: exactly one run, opened at /?run=, with the capture's measurement reference")
            check("Run published" in cp.inner_text("#status"), "try again: status says the run was published")
            shot(cp, "02-try-again-posted-mobile.png")

            # 2. Same capture saved again on purpose: the existing run opens, no second row.
            cp.goto(base + "/" + first)
            settle(cp, "test-casey")
            cp.get_by_role("heading", name="Preview your run").wait_for()
            cp.fill("#i_title", "TEST DATA recovery session again")
            cp.fill("#i_caption", "TEST DATA: a second caption that must not create a second run.")
            cp.select_option("#i_vis", "public")
            cp.click("#i_pub")
            cp.wait_for_url(f"**/?run={run_id}*", timeout=20000)
            cp.wait_for_function("document.getElementById('status').textContent.includes('already saved')")
            again = cp.inner_text("#status")
            check("already saved" in again and "not applied" in again, "re-save: opens the existing run and says the new caption was not applied: " + again[:100])
            rows = my_runs(cp)
            check(len(rows) == 1 and rows[0]["caption"] == "TEST DATA: caption typed before the connection dropped.", "re-save: still one run with the first caption")
            cp.get_by_text("No replies yet").wait_for()
            shot(cp, "03-resave-opens-existing-mobile.png")

            # 3. Lost response: the insert lands, the browser never hears back.
            # Stable measurement revision allows lost-response recovery without conflating distinct captures.
            second = capture("review-lost-response-unique", "2026-09-14T21:00:00+00:00")
            cp.goto(base + "/" + second)
            settle(cp, "test-casey")
            cp.get_by_role("heading", name="Preview your run").wait_for()
            cp.fill("#i_title", "TEST DATA lost response session")
            cp.fill("#i_caption", "TEST DATA: the server saved this; the browser never heard.")
            cp.select_option("#i_vis", "private")
            gate.mode = "lost"
            cp.click("#i_pub")
            cp.locator("#i_recover:not([hidden])").wait_for(timeout=15000)
            rows = my_runs(cp)
            check(len(rows) == 2, "lost response: the server holds the run the browser thinks failed (rows " + str(len(rows)) + ")")
            check("Not saved" in cp.inner_text("#i_recover"), "lost response: the page says not saved, because it cannot know better yet")
            shot(cp, "04-lost-response-recovery-mobile.png")
            gate.mode = "open"
            cp.click("#i_retry")
            cp.wait_for_url("**/?run=*", timeout=20000)
            cp.wait_for_function("document.getElementById('status').textContent.includes('already saved')")
            rows = my_runs(cp)
            lost_id = cp.url.split("run=", 1)[1].split("&", 1)[0]
            check(len(rows) == 2 and any(r["id"] == lost_id and r["measurement_revision"] == "review-lost-response-unique" for r in rows), "lost response: Try again found the saved run by measurement revision instead of posting a duplicate (rows " + str(len(rows)) + ")")
            check("Only me" in cp.inner_text("#status"), "lost response: the status names the audience the run was saved with")
            shot(cp, "05-lost-response-found-mobile.png")

            # 4. A chopped import link.
            cp.goto(base + "/" + first[:-40])
            cp.get_by_role("heading", name="This import link is incomplete").wait_for(timeout=10000)
            check("Nothing was posted" in cp.inner_text("#app"), "chopped link: says the link is incomplete and nothing was posted")
            shot(cp, "06-chopped-link-mobile.png")

            # 5. Exact reply beyond the paging cap, then a reply that does not exist.
            riley_context, rp = context_for(riley, "test-riley")
            rp.goto(base + "/?run=" + run_id)
            settle(rp, "test-riley")
            oldest = rp.evaluate("""async (args) => { const {data,error}=await sb.from('grinder_replies').insert([{run_id:args.run, author_id:args.me, body:'TEST DATA the reply a friend actually meant'}]).select('id'); return error?error.message:data[0].id; }""", {"run": run_id, "me": riley})
            check(len(str(oldest)) == 36, "cap: the target reply exists (" + str(oldest)[:36] + ")")
            filler = rp.evaluate("""async (args) => { const rows=[...Array(330)].map((_,i)=>({run_id:args.run, author_id:args.me, body:'TEST DATA filler reply '+(i+1)})); const {data,error}=await sb.from('grinder_replies').insert(rows).select('id'); return error?error.message:data.length; }""", {"run": run_id, "me": riley})
            check(filler == 330, "cap: 330 newer TEST DATA replies inserted (got " + str(filler) + ")")
            cp.evaluate("sessionStorage.setItem('ag_response_return','?inbox')")
            cp.goto(base + f"/?run={run_id}&reply={oldest}#reply-{oldest}")
            settle(cp, "test-casey")
            try:
                cp.locator(f".reply-direct #reply-{oldest}.reply-target, .reply-missing").first.wait_for(timeout=120000)
            except Exception:  # noqa: BLE001
                shot(cp, "debug-cap-timeout.png")
                print("DEBUG js_errors", js_errors)
                print("DEBUG replies loaded", cp.locator(".thread-items .reply").count(), "older button", cp.locator(".older-replies").count())
                print("DEBUG app text", cp.inner_text("#app")[:600])
                raise
            check(cp.locator(f".reply-direct #reply-{oldest}.reply-target").count() == 1, "cap: the exact reply past the 12-page load is rendered directly")
            check(cp.locator(".reply-missing").count() == 0, "cap: no removed claim for a reply that exists")
            check("shown here on its own" in cp.inner_text(".reply-direct") and "the reply a friend actually meant" in cp.inner_text(".reply-direct"), "cap: the direct card explains itself and carries the reply body")
            check(cp.evaluate("() => document.activeElement && document.activeElement.id === 'reply-" + str(oldest) + "'"), "cap: focus lands on the exact reply")
            check(cp.locator(".reply-direct").get_by_role("link", name="Back to Responses").count() == 1, "cap: Back to Responses is offered on the direct card")
            cp.screenshot(path=str(ARTIFACTS / "07-exact-reply-beyond-cap-mobile.png"), full_page=False)
            ghost = str(uuid.uuid4())
            cp.goto(base + f"/?run={run_id}&reply={ghost}#reply-{ghost}")
            settle(cp, "test-casey")
            cp.locator(".reply-missing").wait_for(timeout=120000)
            check("removed or is not visible to you" in cp.inner_text(".reply-missing"), "missing reply: named as removed or not visible, not as an error")
            check(cp.locator(".reply-direct").count() == 0, "missing reply: nothing rendered directly for an id that does not exist")
            cp.screenshot(path=str(ARTIFACTS / "08-missing-reply-mobile.png"), full_page=False)

            for page in (cp, rp):
                check(not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1"), "phone: no horizontal overflow")
            check(not js_errors, "no JavaScript page errors: " + json.dumps(js_errors))
            browser.close()
    finally:
        site.shutdown()
        process.terminate()
        process.wait(timeout=10)

    for message in observed:
        print("ok  " + message)
    for message in errors:
        print("FAIL " + message)
    print(json.dumps({
        "fixture": "TEST DATA · disposable PGlite · committed shell",
        "checks_passed": len(observed),
        "checks_failed": len(errors),
        "javascript_errors": js_errors,
        "artifacts": str(ARTIFACTS),
        "hosted_oauth": "not run",
        "consenting_users": "none",
    }))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
