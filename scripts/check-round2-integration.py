"""Round 2 integrated walk: one continuous two-person path through the real shell.

account > capture/import preview > deliberate test post > follow > reply > Responses >
exact conversation > back, with cancellation, a duplicate handle, and missing, deleted and
blocked targets. Every step drives site/index.html as committed; the only rewrite is the
backend host, pointed at the disposable PGlite shim. Nothing here inserts a production hook.

Disposable TEST DATA identities only. No hosted OAuth, no consenting person, no public write.
"""
from __future__ import annotations

import base64
import json
import os
import threading
import urllib.error
import urllib.request
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from subprocess import PIPE, Popen
from urllib.parse import parse_qs, quote, urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HOST = "kqxasvolwtrczusjhlli.supabase.co"
NODE = os.environ.get("NODE_BIN", "/Users/morkeeth/.nvm/versions/node/v22.22.3/bin/node")
ARTIFACTS = Path(os.environ.get("GRINDER_ROUND2_ARTIFACTS", "/tmp/agentic-strava-round2"))
ARTIFACTS.mkdir(parents=True, exist_ok=True)
CHROME = os.environ.get("CHROME_BIN", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

# The capture payload a deliberate test post starts from. It is what a local capture would
# hand the shell on the URL hash; the measurement revision is a fixed TEST DATA digest.
CAPTURE = {
    "schema_version": 1,
    "harness": "Cursor",
    "project": "agentgrinder-public TEST DATA",
    "turns_typed": 4,
    "duration_s": 900,
    "tool_calls": 12,
    "measurement_revision": "b" * 64,
}


def integrated_index():
    body = (ROOT / "site" / "index.html").read_text()
    for needle in ("account.js", "GrinderAccount({", "account.recover()", "social.refreshUnread()", "responseReturnLink()"):
        if needle not in body:
            raise RuntimeError("site/index.html is not integrated: missing " + needle)
    return body.replace('const SB_URL="http://127.0.0.1:54321";', f'const SB_URL="https://{HOST}";')


class SiteHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "site"), **kwargs)

    def log_message(self, _format, *_args):
        pass

    def do_GET(self):
        if self.path.split("?", 1)[0] in ("/", "/index.html"):
            encoded = integrated_index().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return
        super().do_GET()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


OPENER = urllib.request.build_opener(NoRedirect)
OAUTH_OUTCOME = {"value": "cancel"}


def proxy(route, disposable):
    request = route.request
    url = request.url
    if "/auth/v1/authorize" in url:
        # The provider round trip, gated to test mode: the person cancels at the provider.
        back = parse_qs(urlparse(url).query).get("redirect_to", ["/"])[0]
        fragment = "error=access_denied&error_code=access_denied&error_description=The+user+cancelled+the+authorisation"
        route.fulfill(status=302, headers={"Location": back + ("&" if "#" in back else "#") + fragment}, body=b"")
        return
    target = url.replace("https://" + HOST, disposable)
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
    data = request.post_data.encode() if request.post_data is not None else None
    outgoing = urllib.request.Request(target, data=data, method=request.method, headers=headers)
    try:
        with OPENER.open(outgoing, timeout=30) as response:
            route.fulfill(
                status=response.status,
                headers={k: v for k, v in response.headers.items() if k.lower() not in ("transfer-encoding", "content-encoding", "content-length")},
                body=response.read(),
            )
    except urllib.error.HTTPError as exc:
        route.fulfill(status=exc.code, headers={"content-type": exc.headers.get("content-type", "application/json")}, body=exc.read())


def mint(sub, handle, identities):
    header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').decode().rstrip("=")
    payload = base64.urlsafe_b64encode(
        json.dumps({"sub": sub, "email": handle + "@example.test", "role": "authenticated", "aud": "authenticated", "exp": 2_000_000_000}).encode()
    ).decode().rstrip("=")
    token = f"{header}.{payload}.sig"
    return {
        "access_token": token,
        "refresh_token": token,
        "token_type": "bearer",
        "expires_in": 86400,
        "expires_at": 2_000_000_000,
        "user": {
            "id": sub,
            "aud": "authenticated",
            "role": "authenticated",
            "email": handle + "@example.test",
            "user_metadata": {"user_name": handle, "full_name": "TEST DATA " + handle},
            "identities": identities,
        },
    }


def session_script(session):
    return "localStorage.setItem('agentic-strava-auth'," + json.dumps(json.dumps(session)) + ");"


def snapshot(disposable):
    with urllib.request.urlopen(disposable + "/_test/grinder-snapshot", timeout=30) as response:
        return json.loads(response.read().decode())


def capture_hash():
    return "#import=" + quote(base64.b64encode(json.dumps(CAPTURE).encode()).decode(), safe="")


def main():
    environment = os.environ.copy()
    environment["GRINDER_DISPOSABLE_TEST"] = "1"
    environment["DISPOSABLE_GRINDER"] = "1"
    process = Popen([NODE, str(ROOT / "scripts" / "disposable-supabase.mjs"), "--serve"], cwd=ROOT, env=environment, stdout=PIPE, stderr=PIPE, text=True)
    line = process.stdout.readline()
    try:
        info = json.loads(line)
    except Exception as exc:  # noqa: BLE001
        process.kill()
        raise RuntimeError("disposable supabase failed to start: " + line + (process.stderr.read() or "")) from exc
    disposable = info["url"]
    casey, riley = info["casey"], info["riley"]
    before = snapshot(disposable)
    site = ThreadingHTTPServer(("127.0.0.1", 0), SiteHandler)
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
            if Path(CHROME).exists():
                launch["executable_path"] = CHROME
            browser = playwright.chromium.launch(**launch)

            def context_for(sub=None, handle=None, width=390, height=844):
                context = browser.new_context(viewport={"width": width, "height": height})
                context.route(f"https://{HOST}/**", lambda route: proxy(route, disposable))
                if sub:
                    context.add_init_script(session_script(mint(sub, handle, ids_for(sub))))
                page = context.new_page()
                page.on("pageerror", lambda error: js_errors.append((handle or "signed-out") + ": " + str(error)))
                return context, page

            def settle(page, handle):
                page.wait_for_function("document.getElementById('me').textContent.trim()==='@" + handle + "'")
                page.wait_for_timeout(600)

            def open_account_settings(page):
                # The phone path: the header menu is hidden under 900px, so a person taps their
                # own handle, opens Edit profile and follows the Account settings link there.
                page.click("#me a")
                page.wait_for_selector(".profile-settings summary")
                page.click(".profile-settings summary")
                page.get_by_role("link", name="Account settings").click()

            # 1. Signed out, a capture preview on the phone, sign-in cancelled at the provider.
            context, page = context_for()
            page.goto(base + "/" + capture_hash())
            page.get_by_role("heading", name="Preview your run").wait_for()
            check(page.get_by_role("heading", name="Card preview").count() == 1, "signed out: capture preview shows the card before any sign-in")
            check("Sign in to save" in page.inner_text("#i_pub"), "signed out: the save button asks for sign-in, nothing is posted")
            page.fill("#i_caption", "TEST DATA caption written before sign-in")
            page.select_option("#i_vis", "public")
            page.click("#i_pub")
            page.wait_for_selector("#signin-dialog[open]")
            shot(page, "01-signin-from-preview-mobile.png")
            page.click("#signin-dialog [data-provider=github]")
            page.wait_for_url(lambda url: url.startswith(base) and "error" not in url, timeout=15000)
            page.wait_for_function("document.getElementById('status').textContent.length>0")
            status_text = page.inner_text("#status")
            check("cancelled" in status_text.lower() and "draft is still here" in status_text.lower(), "cancelled sign-in: landing names the cancel and the surviving draft: " + status_text)
            page.wait_for_function("location.hash.includes('import=')")
            check(page.get_by_role("heading", name="Preview your run").count() == 1, "cancelled sign-in: the capture preview is back on screen from the restored draft")
            check(page.evaluate("sessionStorage.getItem('ag_auth_pending')") is None, "cancelled sign-in: pending marker settled")
            shot(page, "02-cancelled-signin-draft-mobile.png")
            context.close()

            # 2. Casey signed in: same capture, deliberate test post from the preview.
            casey_context, cp = context_for(casey, "test-casey")
            cp.goto(base + "/" + capture_hash())
            settle(cp, "test-casey")
            cp.get_by_role("heading", name="Preview your run").wait_for()
            check("Save run" in cp.inner_text("#i_pub"), "casey preview: save offered once signed in")
            check("not posted" in cp.inner_text("#app"), "casey preview: card labelled not posted before the choice")
            cp.fill("#i_title", "TEST DATA round 2 session")
            cp.fill("#i_caption", "TEST DATA: deliberate round 2 test post from a capture preview.")
            cp.select_option("#i_vis", "public")
            shot(cp, "03-capture-preview-mobile.png")
            cp.click("#i_pub")
            cp.wait_for_url("**/?run=*", timeout=20000)
            run_id = cp.url.split("run=", 1)[1].split("&", 1)[0]
            cp.get_by_text("TEST DATA: deliberate round 2 test post").wait_for()
            check(uuid.UUID(run_id) is not None, "casey post: run saved and opened at /?run=")
            shot(cp, "04-posted-run-mobile.png")

            # 3. Account settings by the phone path: duplicate handle refused, new handle saved.
            open_account_settings(cp)
            cp.wait_for_url("**/?account*")
            cp.wait_for_selector("#account-profile")
            cp.fill("#account-handle", "test-riley")
            cp.click("#account-save")
            cp.wait_for_selector("#account-use-alt")
            state = cp.inner_text("#account-profile-state")
            check("taken" in state and "test-riley-2" in state, "duplicate handle: refused inline with a free variant: " + state)
            check(cp.evaluate("document.getElementById('me').textContent.trim()") == "@test-casey", "duplicate handle: nothing changed on refusal")
            shot(cp, "05-duplicate-handle-mobile.png")
            cp.fill("#account-handle", "test-casey-r2")
            cp.click("#account-save")
            cp.wait_for_function("document.getElementById('account-profile-state').textContent.startsWith('Saved')")
            cp.wait_for_function("document.getElementById('me').textContent.trim()==='@test-casey-r2'")
            row = next(r for r in snapshot(disposable)["strava"] if r["auth_uid"] == casey)
            check(row["id"] == casey and row["handle"] == "test-casey-r2", "handle edit: id stable, new handle stored")
            cp.goto(base + "/?run=" + run_id)
            settle(cp, "test-casey-r2")
            check("test-casey-r2" in cp.inner_text("#app"), "handle edit: the posted run card shows the new handle")
            zero_badge = cp.evaluate("[...document.querySelectorAll('.mobile-inbox-badge')].every(b=>getComputedStyle(b).display==='none')")
            check(zero_badge, "no responses yet: the unread badge is not drawn at zero (no false blue dot)")

            # 4. Riley follows Casey under the new handle and sees the run in Following.
            riley_context, rp = context_for(riley, "test-riley")
            rp.goto(base + "/?u=test-casey-r2")
            settle(rp, "test-riley")
            rp.get_by_role("button", name="Follow", exact=True).click()
            rp.get_by_role("button", name="Following · unfollow", exact=True).wait_for()
            shot(rp, "06-follow-mobile.png")
            rp.goto(base + "/?following")
            settle(rp, "test-riley")
            rp.get_by_text("TEST DATA: deliberate round 2 test post").wait_for()
            check(True, "follow: Casey's run appears in Riley's Following")
            shot(rp, "07-following-feed-mobile.png")

            # 5. Riley ACKs and replies on the run.
            rp.goto(base + "/?run=" + run_id)
            settle(rp, "test-riley")
            rp.get_by_role("button", name="ACK", exact=True).click()
            rp.get_by_role("button", name="Send ACK", exact=True).click()
            rp.get_by_role("button", name="ACKed 1", exact=True).wait_for()
            rp.get_by_label("Your reply").fill("TEST DATA round 2 reply.")
            rp.get_by_role("button", name="Post reply", exact=True).click()
            rp.get_by_text("TEST DATA round 2 reply.").wait_for()
            reply_id = rp.evaluate("""() => { const el=[...document.querySelectorAll('.reply')].find(a=>a.textContent.includes('TEST DATA round 2 reply.')); return el?el.id.replace(/^reply-/,''):null; }""")
            check(bool(reply_id), "reply: card carries its id for the exact deep link")
            shot(rp, "08-reply-mobile.png")

            # 6. Casey, cold load on any page: the unread badge is filled by the shell hook.
            cp.goto(base + "/?explore")
            settle(cp, "test-casey-r2")
            cp.wait_for_function("[...document.querySelectorAll('.mobile-inbox-badge')].some(b=>!b.hidden&&b.textContent.trim())", timeout=10000)
            badge = cp.evaluate("[...document.querySelectorAll('.mobile-inbox-badge')].find(b=>!b.hidden).textContent.trim()")
            check(badge == "3", "cold load: unread badge shows follow + ACK + reply = 3 (got " + badge + ")")
            shot(cp, "09-cold-load-badge-mobile.png")

            # 7. Responses: three items, exact reply link, then the exact conversation and back.
            cp.goto(base + "/?inbox")
            settle(cp, "test-casey-r2")
            cp.get_by_role("heading", name="Responses").wait_for()
            body = cp.locator("#social-body")
            text = body.inner_text()
            check("followed you" in text and "ACKed your work" in text and "replied to your run" in text, "responses: follow, ACK and reply all listed")
            check("TEST DATA Riley" in text, "responses: actor shown by display name")
            follow_links = cp.evaluate("""() => { const row=[...document.querySelectorAll('.response-item')].find(r=>r.textContent.includes('followed you')); return row?[...row.querySelectorAll('.response-item-actions a')].map(a=>a.textContent.trim()):null; }""")
            check(follow_links == ["Open profile", "Open Following"], "responses: the follow row offers the profile once, then Following (got " + json.dumps(follow_links) + ")")
            exact = cp.get_by_role("link", name="Open exact reply").first
            href = exact.get_attribute("href") or ""
            check(f"run={run_id}" in href and f"reply={reply_id}" in href and f"#reply-{reply_id}" in href, "responses: exact reply link targets the reply id")
            shot(cp, "10-responses-mobile.png")
            # Bury the replied-to comment under 25 newer replies (R2-01): page one of the thread
            # must not claim it was removed, the shell has to page until the exact reply is found.
            filler = rp.evaluate("""async (args) => { const rows=[...Array(25)].map((_,i)=>({run_id:args.run, author_id:args.me, body:'TEST DATA filler reply '+(i+1)})); const {data,error}=await sb.from('grinder_replies').insert(rows).select('id'); return error?error.message:data.length; }""", {"run": run_id, "me": riley})
            check(filler == 25, "thread: 25 newer TEST DATA replies inserted as Riley (got " + str(filler) + ")")
            exact.click()
            cp.wait_for_url(f"**/?run={run_id}*", timeout=20000)
            cp.locator(f"#reply-{reply_id}.reply-target, .reply-missing").first.wait_for(timeout=20000)
            check(cp.locator(f"#reply-{reply_id}.reply-target").count() == 1 and cp.locator(".reply-missing").count() == 0, "exact conversation: a reply past page one is found, not reported removed")
            check(cp.get_by_role("link", name="Back to Responses").count() >= 1, "exact conversation: Back to Responses offered")
            check("@test-riley ACKed" in cp.inner_text("#app"), "exact conversation: the ACK list names the acker by handle")
            shot(cp, "11-exact-conversation-mobile.png")
            cp.get_by_role("link", name="Back to Responses").first.click()
            cp.wait_for_url("**/?inbox*", timeout=20000)
            cp.get_by_role("heading", name="Responses").wait_for()
            cp.wait_for_timeout(800)
            read_state = cp.evaluate(f"""() => {{ const a=document.querySelector('[data-notification-id][href*="reply={reply_id}"]'); const item=a&&a.closest('.response-item'); return item?item.dataset.read:null; }}""")
            check(read_state == "1", "back: the opened reply is marked read on return (got " + str(read_state) + ")")
            shot(cp, "12-back-to-responses-mobile.png")

            # 8. Missing target while still in the Responses context keeps a way back.
            cp.evaluate("sessionStorage.setItem('ag_response_return','?inbox')")
            cp.goto(base + "/?run=" + str(uuid.uuid4()))
            settle(cp, "test-casey-r2")
            cp.get_by_text("This run is private or does not exist.").wait_for()
            back = cp.get_by_role("link", name="Back to Responses")
            check(back.count() == 1, "missing run: Back to Responses shown on the empty state")
            shot(cp, "13-missing-run-return-mobile.png")
            back.first.click()
            cp.wait_for_url("**/?inbox*", timeout=20000)
            cp.get_by_role("heading", name="Responses").wait_for()
            check(True, "missing run: return lands on Responses")

            # 9. Riley deletes the reply; Casey's inbox and deep link say so.
            rp.goto(base + "/?run=" + run_id)
            settle(rp, "test-riley")
            deleted = rp.evaluate("""async (id) => { const {data,error}=await sb.from('grinder_replies').delete().eq('id', id).select('id'); return error?error.message:data.length; }""", reply_id)
            check(deleted == 1, "deleted reply: Riley's own reply deleted through the client (got " + str(deleted) + ")")
            cp.goto(base + f"/?run={run_id}&reply={reply_id}#reply-{reply_id}")
            settle(cp, "test-casey-r2")
            cp.get_by_text("That reply was removed or is not visible to you.").wait_for()
            shot(cp, "14-deleted-reply-mobile.png")
            cp.goto(base + "/?inbox")
            settle(cp, "test-casey-r2")
            cp.get_by_role("heading", name="Responses").wait_for()
            check("That reply was removed" in cp.locator("#social-body").inner_text(), "deleted reply: inbox row states the removal instead of a dead link")

            # 10. Riley cancels a profile deletion: wrong handle typed, nothing deleted.
            rp.goto(base + "/?account#danger")
            settle(rp, "test-riley")
            rp.wait_for_selector("#account-confirm")
            rp.fill("#account-confirm", "test-casey-r2")
            check(rp.is_disabled("#account-delete-go"), "delete cancel: wrong handle keeps the delete button disabled")
            shot(rp, "15-delete-cancelled-mobile.png")
            rp.goto(base + "/?explore")
            settle(rp, "test-riley")
            check(any(r["auth_uid"] == riley for r in snapshot(disposable)["strava"]), "delete cancel: walking away leaves Riley's profile in place")

            # 11. Casey blocks Riley; Riley can no longer reply.
            cp.goto(base + "/?u=test-riley")
            settle(cp, "test-casey-r2")
            cp.get_by_role("button", name="Block", exact=True).click()
            cp.get_by_role("button", name="Unblock", exact=True).wait_for()
            shot(cp, "16-blocked-profile-mobile.png")
            rp.goto(base + "/?run=" + run_id)
            settle(rp, "test-riley")
            reply_box = rp.get_by_label("Your reply")
            if reply_box.count():
                reply_box.fill("TEST DATA should be blocked.")
                rp.get_by_role("button", name="Post reply", exact=True).click()
                rp.wait_for_timeout(1500)
                check(rp.get_by_text("TEST DATA should be blocked.").count() == 0, "blocked: Riley's reply is refused")
            else:
                check("Your reply" not in rp.locator("#app").inner_text(), "blocked: composer withheld from Riley")
            shot(rp, "17-blocked-reply-mobile.png")

            # 12. Riley deletes the STRIVE profile for real; Casey's targets go missing cleanly.
            rp.goto(base + "/?account#danger")
            settle(rp, "test-riley")
            rp.wait_for_selector("#account-confirm")
            rp.fill("#account-confirm", "test-riley")
            rp.wait_for_function("!document.getElementById('account-delete-go').disabled")
            rp.click("#account-delete-go")
            rp.wait_for_function("!document.querySelector('#me a')", timeout=15000)
            after = snapshot(disposable)
            check(not any(r["auth_uid"] == riley for r in after["strava"]), "deleted profile: Riley's Strava row is gone")
            check(after["grinder"] == before["grinder"], "deleted profile: Grinder public.profiles snapshot unchanged")
            check(len([i for i in after["identities"] if i["user_id"] == riley]) == len(ids_for(riley)), "deleted profile: Auth identities untouched")
            shot(rp, "18-profile-deleted-mobile.png")
            cp.goto(base + "/?u=test-riley")
            settle(cp, "test-casey-r2")
            cp.get_by_text("Profile not found.").wait_for()
            shot(cp, "19-deleted-target-profile-mobile.png")
            cp.goto(base + "/?inbox")
            settle(cp, "test-casey-r2")
            cp.get_by_role("heading", name="Responses").wait_for()
            inbox_text = cp.locator("#social-body").inner_text()
            # grinder_notifications.actor_id cascades on profile delete, so a deleted person's
            # rows vanish rather than degrade; either outcome must leave no dead link.
            check("Post a real run and share it with a friend" in inbox_text or "Someone" in inbox_text or "unavailable" in inbox_text, "deleted target: inbox is empty (cascade) or degrades cleanly, no crash")
            check(cp.locator('#social-body a[href="/?u=test-riley"]').count() == 0, "deleted target: no dead profile link in Responses")
            shot(cp, "20-responses-after-deletion-mobile.png")

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
    summary = {
        "fixture": "TEST DATA · disposable PGlite · round 2 integrated shell",
        "checks_passed": len(observed),
        "checks_failed": len(errors),
        "javascript_errors": js_errors,
        "artifacts": str(ARTIFACTS),
        "hosted_oauth": "not run",
        "consenting_users": "none",
    }
    print(json.dumps(summary))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
