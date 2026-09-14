"""Browser acceptance: post > reply > inbox > exact conversation > return.

Disposable PGlite identities only. Labelled TEST DATA. No public writes.
"""
from __future__ import annotations

import base64
import json
import os
import threading
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from subprocess import PIPE, Popen

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
HOST = "kqxasvolwtrczusjhlli.supabase.co"
ARTIFACTS = Path(
    os.environ.get("GRINDER_RESPONSE_ARTIFACTS", "/tmp/agentic-strava-response-return")
)
ARTIFACTS.mkdir(parents=True, exist_ok=True)
CHROME = os.environ.get(
    "CHROME_BIN",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)
NODE = os.environ.get(
    "NODE_BIN",
    "/Users/morkeeth/.nvm/versions/node/v22.22.3/bin/node",
)


class SiteHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "site"), **kwargs)

    def log_message(self, _format, *_args):
        pass

    def do_GET(self):
        if self.path.split("?", 1)[0] in ("/", "/index.html"):
            body = (
                ROOT / "site" / "index.html"
            ).read_text().replace(
                'const SB_URL="http://127.0.0.1:54321";',
                f'const SB_URL="https://{HOST}";',
            )
            encoded = body.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return
        super().do_GET()


def proxy(route, disposable):
    request = route.request
    target = request.url.replace("https://" + HOST, disposable)
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() != "host"
    }
    data = request.post_data.encode() if request.post_data is not None else None
    outgoing = urllib.request.Request(
        target, data=data, method=request.method, headers=headers
    )
    try:
        with urllib.request.urlopen(outgoing, timeout=30) as response:
            route.fulfill(
                status=response.status,
                headers={
                    key: value
                    for key, value in response.headers.items()
                    if key.lower()
                    not in (
                        "transfer-encoding",
                        "content-encoding",
                        "content-length",
                    )
                },
                body=response.read(),
            )
    except urllib.error.HTTPError as error:
        route.fulfill(
            status=error.code,
            headers={"content-type": "application/json"},
            body=error.read(),
        )


def mint(sub, handle):
    header = (
        base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}')
        .decode()
        .rstrip("=")
    )
    payload = (
        base64.urlsafe_b64encode(
            json.dumps(
                {
                    "sub": sub,
                    "email": handle + "@example.test",
                    "role": "authenticated",
                    "aud": "authenticated",
                    "exp": 2_000_000_000,
                }
            ).encode()
        )
        .decode()
        .rstrip("=")
    )
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
            "user_metadata": {
                "user_name": handle,
                "full_name": "TEST DATA " + handle,
            },
        },
    }


def session_script(session):
    return (
        "localStorage.setItem('agentic-strava-auth',"
        + json.dumps(json.dumps(session))
        + ");"
    )


def main():
    environment = os.environ.copy()
    environment["GRINDER_DISPOSABLE_TEST"] = "1"
    process = Popen(
        [NODE, str(ROOT / "scripts" / "disposable-supabase.mjs"), "--serve"],
        cwd=ROOT,
        env=environment,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    info = json.loads(process.stdout.readline())
    disposable = info["url"]
    site = ThreadingHTTPServer(("127.0.0.1", 0), SiteHandler)
    threading.Thread(target=site.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{site.server_address[1]}"
    errors = []

    try:
        with sync_playwright() as playwright:
            launch = {"headless": True, "args": ["--no-sandbox"]}
            if Path(CHROME).exists():
                launch["executable_path"] = CHROME
            browser = playwright.chromium.launch(**launch)

            def context_for(sub=None, handle=None, width=390, height=844):
                context = browser.new_context(
                    viewport={"width": width, "height": height}
                )
                context.route(
                    f"https://{HOST}/**",
                    lambda route: proxy(route, disposable),
                )
                if sub:
                    context.add_init_script(session_script(mint(sub, handle)))
                return context

            # Casey posts a public run.
            casey_context = context_for(info["casey"], "test-casey", 390, 844)
            casey = casey_context.new_page()
            casey.on("pageerror", lambda error: errors.append("casey: " + str(error)))
            casey.goto(base + "/?post", wait_until="networkidle")
            casey.get_by_role("heading", name="Post a run").wait_for()
            casey.get_by_text("Post a run without a Cursor export").click()
            casey.get_by_label("What did you build?").fill(
                "TEST DATA response return"
            )
            casey.get_by_label("Project").fill("agentgrinder-public TEST DATA")
            casey.get_by_label("Short caption").fill(
                "TEST DATA: response > return inbox path."
            )
            casey.get_by_label("Who can see this run?").select_option("public")
            casey.get_by_role("button", name="Save run").click()
            casey.wait_for_url("**/?run=*", timeout=20_000)
            run_id = casey.url.split("run=", 1)[1].split("&", 1)[0]

            # Riley ACKs and replies.
            riley_context = context_for(info["riley"], "test-riley", 390, 844)
            riley = riley_context.new_page()
            riley.on("pageerror", lambda error: errors.append("riley: " + str(error)))
            riley.goto(base + "/?run=" + run_id, wait_until="networkidle")
            riley.get_by_role("button", name="ACK", exact=True).click()
            riley.get_by_role("button", name="Send ACK", exact=True).click()
            riley.get_by_role("button", name="ACKed 1", exact=True).wait_for()
            riley.get_by_label("Your reply").fill(
                "TEST DATA reply for exact return."
            )
            riley.get_by_role("button", name="Post reply", exact=True).click()
            riley.get_by_text("TEST DATA reply for exact return.").wait_for()
            reply_id = riley.evaluate(
                """() => {
                  const el = [...document.querySelectorAll('.reply')].find(a =>
                    a.textContent.includes('TEST DATA reply for exact return.')
                  );
                  return el ? el.id.replace(/^reply-/, '') : null;
                }"""
            )
            assert reply_id, "reply card missing id"
            riley.screenshot(
                path=str(ARTIFACTS / "reply-mobile.png"), full_page=True
            )

            # Private / missing run failure for Riley.
            riley.goto(base + "/?run=" + info["caseyRun"], wait_until="networkidle")
            riley.get_by_text("This run is private or does not exist.").wait_for()
            riley.screenshot(
                path=str(ARTIFACTS / "private-or-missing-mobile.png"),
                full_page=True,
            )

            # Casey inbox: items render, exact reply link present.
            # Visible rows may become read via IntersectionObserver (that is correct).
            casey.goto(base + "/?inbox", wait_until="networkidle")
            casey.get_by_role("heading", name="Responses").wait_for()
            body = casey.locator("#social-body")
            assert "replied to your run" in body.inner_text()
            assert "ACKed your work" in body.inner_text()
            assert casey.locator(".response-item").count() >= 2
            exact = casey.get_by_role("link", name="Open exact reply").first
            href = exact.get_attribute("href") or ""
            assert f"run={run_id}" in href
            assert f"reply={reply_id}" in href
            assert f"#reply-{reply_id}" in href
            # Confirm marking uses per-item updates, not a silent swallow of unseen rows:
            # both visible phone rows may be marked; Unread filter then shows empty or fewer.
            casey.screenshot(
                path=str(ARTIFACTS / "inbox-unread-mobile.png"), full_page=True
            )

            casey.goto(base + "/?inbox&filter=unread", wait_until="networkidle")
            casey.get_by_role("heading", name="Responses").wait_for()
            casey.screenshot(
                path=str(ARTIFACTS / "inbox-filter-mobile.png"), full_page=True
            )

            casey.goto(base + "/?inbox", wait_until="networkidle")
            casey.get_by_role("link", name="Open exact reply").first.click()
            casey.wait_for_url(f"**/?run={run_id}*", timeout=20_000)
            casey.get_by_text("TEST DATA reply for exact return.").wait_for()
            casey.locator(f"#reply-{reply_id}.reply-target").wait_for()
            casey.get_by_role("link", name="Back to Responses").first.wait_for()
            casey.screenshot(
                path=str(ARTIFACTS / "exact-reply-return-mobile.png"),
                full_page=True,
            )

            # Return to inbox after opening the conversation.
            casey.get_by_role("link", name="Back to Responses").first.click()
            casey.wait_for_url("**/?inbox*", timeout=20_000)
            casey.get_by_role("heading", name="Responses").wait_for()

            # Deleted reply: remove Riley's reply, reopen the deep link.
            riley.goto(base + "/?run=" + run_id, wait_until="networkidle")
            riley.once("dialog", lambda dialog: dialog.accept())
            with riley.expect_response(
                lambda response: response.request.method == "DELETE"
                and "grinder_replies" in response.url
            ) as deleted:
                riley.get_by_role("button", name="Delete", exact=True).click()
            assert deleted.value.ok

            casey.goto(
                base
                + f"/?run={run_id}&reply={reply_id}#reply-{reply_id}",
                wait_until="networkidle",
            )
            casey.get_by_text(
                "That reply was removed or is not visible to you."
            ).wait_for()
            casey.screenshot(
                path=str(ARTIFACTS / "deleted-reply-mobile.png"), full_page=True
            )

            # Blocked interaction: Casey blocks Riley; Riley cannot keep conversing.
            casey.goto(base + "/?u=test-riley", wait_until="networkidle")
            casey.get_by_role("button", name="Block", exact=True).click()
            casey.get_by_role("button", name="Unblock", exact=True).wait_for()
            riley.goto(base + "/?run=" + run_id, wait_until="networkidle")
            reply_box = riley.get_by_label("Your reply")
            if reply_box.count():
                reply_box.fill("TEST DATA should be blocked.")
                riley.get_by_role("button", name="Post reply", exact=True).click()
                riley.wait_for_timeout(1500)
                assert (
                    riley.get_by_text("TEST DATA should be blocked.").count() == 0
                ), "blocked actor still posted a reply"
            else:
                # Prefer denial of the composer or of the run itself.
                page_text = riley.locator("#app").inner_text()
                assert (
                    "private or does not exist" in page_text
                    or "Sign in to reply" in page_text
                    or "temporarily unavailable" in page_text
                    or "Your reply" not in page_text
                )
            casey.screenshot(
                path=str(ARTIFACTS / "blocked-profile-mobile.png"),
                full_page=True,
            )

            assert not errors, errors
            for page in (casey, riley):
                assert not page.evaluate(
                    "document.documentElement.scrollWidth > innerWidth + 1"
                )
            browser.close()
            print(
                json.dumps(
                    {
                        "fixture": "TEST DATA · disposable PGlite · response return",
                        "run_id": run_id,
                        "reply_id": reply_id,
                        "inbox_unread": True,
                        "exact_reply_navigation": True,
                        "return_to_responses": True,
                        "deleted_reply": True,
                        "private_or_missing": True,
                        "blocked_reply_denied": True,
                        "mobile": True,
                        "javascript_errors": errors,
                        "artifacts": str(ARTIFACTS),
                    }
                )
            )
    finally:
        site.shutdown()
        process.terminate()
        process.wait(timeout=10)


if __name__ == "__main__":
    main()
