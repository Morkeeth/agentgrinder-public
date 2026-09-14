"""Browser acceptance for the focused social loop against disposable PGlite.

All actors and activity are labelled TEST DATA and remain in an in-memory database.
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
ARTIFACTS = Path(os.environ.get("GRINDER_SOCIAL_ARTIFACTS", "/tmp/agentic-strava-social"))
ARTIFACTS.mkdir(parents=True, exist_ok=True)


class SiteHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "site"), **kwargs)

    def log_message(self, _format, *_args):
        pass

    def do_GET(self):
        if self.path.split("?", 1)[0] in ("/", "/index.html"):
            body = (ROOT / "site" / "index.html").read_text().replace(
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
    headers = {key: value for key, value in request.headers.items() if key.lower() != "host"}
    data = request.post_data.encode() if request.post_data is not None else None
    outgoing = urllib.request.Request(target, data=data, method=request.method, headers=headers)
    try:
        with urllib.request.urlopen(outgoing, timeout=30) as response:
            route.fulfill(
                status=response.status,
                headers={
                    key: value
                    for key, value in response.headers.items()
                    if key.lower() not in ("transfer-encoding", "content-encoding", "content-length")
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
    header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').decode().rstrip("=")
    payload = base64.urlsafe_b64encode(
        json.dumps(
            {
                "sub": sub,
                "email": handle + "@example.test",
                "role": "authenticated",
                "aud": "authenticated",
                "exp": 2_000_000_000,
            }
        ).encode()
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
        },
    }


def session_script(session):
    return (
        "localStorage.setItem('sb-kqxasvolwtrczusjhlli-auth-token',"
        + json.dumps(json.dumps(session))
        + ");"
    )


def main():
    environment = os.environ.copy()
    environment["GRINDER_DISPOSABLE_TEST"] = "1"
    process = Popen(
        ["node", str(ROOT / "scripts" / "disposable-supabase.mjs"), "--serve"],
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
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=os.environ.get("CHROME_BIN", "/usr/local/bin/google-chrome"),
                args=["--no-sandbox"],
            )

            def context_for(sub=None, handle=None, width=1280, height=900):
                context = browser.new_context(viewport={"width": width, "height": height})
                context.route(f"https://{HOST}/**", lambda route: proxy(route, disposable))
                if sub:
                    context.add_init_script(session_script(mint(sub, handle)))
                return context

            casey_context = context_for(info["casey"], "test-casey")
            casey = casey_context.new_page()
            casey.on("pageerror", lambda error: errors.append("casey: " + str(error)))
            casey.goto(base + "/?post", wait_until="networkidle")
            casey.get_by_role("heading", name="Post a run").wait_for()
            assert casey.get_by_role("link", name="Post a run", exact=True).first.get_attribute(
                "aria-current"
            ) == "page"
            casey.get_by_text("Post a run without a Cursor export").click()
            casey.get_by_label("What did you build?").fill("TEST DATA social loop")
            casey.get_by_label("Project").fill("agentgrinder-public TEST DATA")
            casey.get_by_label("Short caption").fill(
                "TEST DATA: connected a focused run-card posting flow."
            )
            casey.get_by_label("Link to what was built (optional)").fill(
                "https://example.test/test-output"
            )
            casey.get_by_label("Who can see this run?").select_option("public")
            casey.screenshot(path=str(ARTIFACTS / "post-preview-desktop.png"), full_page=True)
            casey.get_by_role("button", name="Save run").click()
            casey.wait_for_url("**/?run=*", timeout=20_000)
            run_id = casey.url.split("run=", 1)[1].split("&", 1)[0]
            casey.get_by_text("TEST DATA: connected a focused run-card posting flow.").wait_for()
            casey.get_by_role("link", name="Open what was built").wait_for()
            casey.screenshot(path=str(ARTIFACTS / "posted-run-desktop.png"), full_page=True)
            assert info["caseyRun"] != run_id

            anonymous_context = context_for(width=390, height=844)
            anonymous = anonymous_context.new_page()
            anonymous.on("pageerror", lambda error: errors.append("anonymous: " + str(error)))
            anonymous.goto(base + "/?explore", wait_until="networkidle")
            anonymous.get_by_text("TEST DATA social loop", exact=True).wait_for()
            assert anonymous.get_by_text("TEST DATA Casey coach sitting", exact=True).count() == 0
            anonymous.screenshot(path=str(ARTIFACTS / "feed-mobile.png"), full_page=True)

            riley_context = context_for(info["riley"], "test-riley", 390, 844)
            riley = riley_context.new_page()
            riley.on("pageerror", lambda error: errors.append("riley: " + str(error)))
            riley.goto(base + "/?u=test-casey", wait_until="networkidle")
            riley.get_by_role("button", name="Follow", exact=True).click()
            riley.get_by_role("button", name="Following · unfollow", exact=True).wait_for()
            riley.goto(base + "/?run=" + run_id, wait_until="networkidle")
            riley.get_by_role("button", name="ACK", exact=True).click()
            riley.get_by_role("button", name="Send ACK", exact=True).click()
            riley.get_by_label("Your reply").fill("TEST DATA reply: the audience choice is clear.")
            riley.get_by_role("button", name="Post reply", exact=True).click()
            riley.get_by_text("TEST DATA reply: the audience choice is clear.").wait_for()
            riley.screenshot(path=str(ARTIFACTS / "response-mobile.png"), full_page=True)
            riley.goto(base + "/?run=" + info["caseyRun"], wait_until="networkidle")
            riley.get_by_text("This run is private or does not exist.").wait_for()

            casey.goto(base + "/?inbox", wait_until="networkidle")
            casey.get_by_role("heading", name="Responses").wait_for()
            assert "ACKed your work" in casey.locator("#social-body").inner_text()
            assert "replied to your run" in casey.locator("#social-body").inner_text()
            casey.screenshot(path=str(ARTIFACTS / "responses-desktop.png"), full_page=True)

            # Existing runs without a caption must remain withdrawable.
            casey.goto(base + "/?run=" + run_id, wait_until="networkidle")
            casey.get_by_label("Short caption").fill("")
            casey.get_by_label("Who can read this run").select_option("private")
            with casey.expect_response(lambda response: response.request.method == "PATCH" and "/rest/v1/runs" in response.url) as saved:
                casey.get_by_role("button", name="Save changes", exact=True).click()
            assert saved.value.ok
            anonymous.goto(base + "/?run=" + run_id, wait_until="networkidle")
            anonymous.get_by_text("This run is private or does not exist.").wait_for()

            assert not errors, errors
            for page in (casey, anonymous, riley):
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
            browser.close()
            print(
                json.dumps(
                    {
                        "fixture": "TEST DATA · disposable PGlite · no public writes",
                        "run_id": run_id,
                        "public_feed": True,
                        "private_run_hidden": True,
                        "follow": True,
                        "ack": True,
                        "reply": True,
                        "responses": True,
                        "mobile": True,
                        "desktop": True,
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
