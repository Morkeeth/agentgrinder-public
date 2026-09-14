"""Browser acceptance for Find people → follow → Following → profile → run → Responses.

Uses disposable PGlite actors labelled TEST DATA. Injects people lane hooks without
editing site/index.html (root owns that integration).
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
ARTIFACTS = Path(os.environ.get("GRINDER_PEOPLE_ARTIFACTS", "/tmp/agentic-strava-people"))
ARTIFACTS.mkdir(parents=True, exist_ok=True)

INJECT_HEAD = """
<link rel="stylesheet" href="/people.css">
<script src="/people.js"></script>
"""

HOOK_AFTER_SOCIAL = (
    "const social=GrinderSocial({client:sb,me:()=>ME,app:()=>$('app'),frame,status,\n"
    "  renderRuns:async runs=>{noteTraces(runs);const ad=await ackData(runs);setTimeout(()=>{wireKudos();countUp()},0);return runs.map(r=>runCard(r,ad.mine.has(r.id),ad.counts[r.id])).join('')}});"
)
HOOK_PEOPLE = (
    HOOK_AFTER_SOCIAL
    + "\nconst people=GrinderPeople({client:sb,me:()=>ME,app:()=>$('app'),frame,status,social,drawAvatar:avatar,"
    + "renderRuns:async runs=>{noteTraces(runs);const ad=await ackData(runs);setTimeout(()=>{wireKudos();countUp()},0);return runs.map(r=>runCard(r,ad.mine.has(r.id),ad.counts[r.id])).join('')}});"
)

HOOK_ROUTE = "if(q.has('following')){setPrimarySection('feed');return social.following();}"
HOOK_ROUTE_WITH_PEOPLE = "if(q.has('people')){setPrimarySection('feed');return people.discover(q.get('q')||'');}\n  if(q.has('following')){setPrimarySection('feed');return social.following();}"

HOOK_RETURN = "if(pending&&/^\\?(post|mine|following|inbox|run|u|example)(=|$)/.test(pending))"
HOOK_RETURN_WITH = "if(pending&&/^\\?(post|mine|following|inbox|run|u|example|people)(=|$)/.test(pending))"

HOOK_TABS = 'return `<nav class="feed-tabs" aria-label="Feed filters"><a href="/?explore" class="${active===\'discover\'?\'on\':\'\'}" ${active===\'discover\'?\'aria-current="page"\':\'\'}>Discover</a><a href="/?following" class="${active===\'following\'?\'on\':\'\'}" ${active===\'following\'?\'aria-current="page"\':\'\'}>Following</a></nav>`;'
HOOK_TABS_WITH = 'return `<nav class="feed-tabs" aria-label="Feed filters"><a href="/?explore" class="${active===\'discover\'?\'on\':\'\'}" ${active===\'discover\'?\'aria-current="page"\':\'\'}>Discover</a><a href="/?people" class="${active===\'people\'?\'on\':\'\'}" ${active===\'people\'?\'aria-current="page"\':\'\'}>Find people</a><a href="/?following" class="${active===\'following\'?\'on\':\'\'}" ${active===\'following\'?\'aria-current="page"\':\'\'}>Following</a></nav>`;'


class SiteHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "site"), **kwargs)

    def log_message(self, _format, *_args):
        pass

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            body = (ROOT / "site" / "index.html").read_text()
            body = body.replace(
                'const SB_URL="http://127.0.0.1:54321";',
                f'const SB_URL="https://{HOST}";',
            )
            if "people.js" not in body:
                body = body.replace("</head>", INJECT_HEAD + "</head>")
            if "GrinderPeople({" not in body:
                if HOOK_AFTER_SOCIAL not in body:
                    raise RuntimeError("social bootstrap hook missing from index.html")
                body = body.replace(HOOK_AFTER_SOCIAL, HOOK_PEOPLE, 1)
            if "q.has('people')" not in body:
                body = body.replace(HOOK_ROUTE, HOOK_ROUTE_WITH_PEOPLE, 1)
            if "people)(=|$)" not in body:
                body = body.replace(HOOK_RETURN, HOOK_RETURN_WITH, 1)
            if 'href="/?people"' not in body:
                if HOOK_TABS not in body:
                    raise RuntimeError("feedTabs hook missing from index.html")
                body = body.replace(HOOK_TABS, HOOK_TABS_WITH, 1)
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
                    if key.lower()
                    not in ("transfer-encoding", "content-encoding", "content-length")
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
    environment["PATH"] = "/Users/morkeeth/.nvm/versions/node/v22.22.3/bin:" + environment.get(
        "PATH", ""
    )
    process = Popen(
        [
            "/Users/morkeeth/.nvm/versions/node/v22.22.3/bin/node",
            str(ROOT / "scripts" / "disposable-supabase.mjs"),
            "--serve",
        ],
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
            chrome = os.environ.get("CHROME_BIN")
            launch = {"headless": True, "args": ["--no-sandbox"]}
            if chrome:
                launch["executable_path"] = chrome
            elif Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome").exists():
                launch["executable_path"] = (
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                )
            browser = playwright.chromium.launch(**launch)

            def context_for(sub=None, handle=None, width=1280, height=900):
                context = browser.new_context(viewport={"width": width, "height": height})
                context.route(f"https://{HOST}/**", lambda route: proxy(route, disposable))
                if sub:
                    context.add_init_script(session_script(mint(sub, handle)))
                return context

            # Riley: empty Following, find Casey by handle, follow before extra posts.
            riley_context = context_for(info["riley"], "test-riley", 390, 844)
            riley = riley_context.new_page()
            riley.on("pageerror", lambda error: errors.append("riley: " + str(error)))
            riley.goto(base + "/?following", wait_until="networkidle")
            riley.get_by_text("You are not following anyone yet", exact=False).wait_for()
            riley.screenshot(path=str(ARTIFACTS / "following-empty-mobile.png"), full_page=True)

            riley.goto(base + "/?people", wait_until="networkidle")
            riley.get_by_role("heading", name="Find people").wait_for()
            riley.screenshot(path=str(ARTIFACTS / "people-discover-mobile.png"), full_page=True)
            riley.get_by_label("Handle or name").fill("casey")
            riley.get_by_role("button", name="Search").click()
            riley.get_by_role("heading", name="Matches").wait_for()
            riley.get_by_role("button", name="Follow", exact=True).first.click()
            riley.get_by_role("button", name="Following · unfollow", exact=True).first.wait_for()
            riley.screenshot(path=str(ARTIFACTS / "people-search-follow-mobile.png"), full_page=True)

            # Casey posts a public run (desktop).
            casey_context = context_for(info["casey"], "test-casey")
            casey = casey_context.new_page()
            casey.on("pageerror", lambda error: errors.append("casey: " + str(error)))
            casey.goto(base + "/?post", wait_until="networkidle")
            casey.get_by_text("Post a run without a Cursor export").click()
            casey.get_by_label("What did you build?").fill("TEST DATA people lane")
            casey.get_by_label("Project").fill("agentic-strava-people TEST DATA")
            casey.get_by_label("Short caption").fill(
                "TEST DATA: friend lookup and follow before the run existed."
            )
            casey.get_by_label("Who can see this run?").select_option("public")
            casey.get_by_role("button", name="Save run").click()
            casey.wait_for_url("**/?run=*", timeout=20_000)
            run_id = casey.url.split("run=", 1)[1].split("&", 1)[0]
            casey.goto(base + "/?people", wait_until="networkidle")
            casey.get_by_text("Your shareable profile").wait_for()
            casey.screenshot(path=str(ARTIFACTS / "people-share-desktop.png"), full_page=True)

            # Riley: Following shows the run; open profile → run → reply.
            riley.goto(base + "/?following", wait_until="networkidle")
            riley.get_by_text("TEST DATA people lane", exact=True).wait_for()
            riley.screenshot(path=str(ARTIFACTS / "following-feed-mobile.png"), full_page=True)
            riley.goto(base + "/?u=test-casey", wait_until="networkidle")
            riley.get_by_role("button", name="Following · unfollow", exact=True).wait_for()
            riley.get_by_text("TEST DATA people lane", exact=True).click()
            riley.wait_for_url("**/?run=*", timeout=20_000)
            riley.get_by_label("Your reply").fill(
                "TEST DATA reply from Following → profile → run."
            )
            riley.get_by_role("button", name="Post reply", exact=True).click()
            riley.get_by_text("TEST DATA reply from Following → profile → run.").wait_for()
            riley.screenshot(path=str(ARTIFACTS / "profile-run-response-mobile.png"), full_page=True)

            casey.goto(base + "/?inbox", wait_until="networkidle")
            casey.get_by_role("heading", name="Responses").wait_for()
            assert "replied to your run" in casey.locator("#social-body").inner_text()
            casey.get_by_role("link", name="Open profile").first.wait_for()
            casey.screenshot(path=str(ARTIFACTS / "responses-return-desktop.png"), full_page=True)

            # Signed-out profile URL still resolves; no inventing ownership.
            anon_context = context_for(width=390, height=844)
            anon = anon_context.new_page()
            anon.on("pageerror", lambda error: errors.append("anon: " + str(error)))
            anon.goto(base + "/?u=test-casey", wait_until="networkidle")
            anon.get_by_text("TEST DATA people lane", exact=True).wait_for()
            anon.goto(base + "/?u=not-a-real-handle-xyz", wait_until="networkidle")
            anon.get_by_text("Profile not found.", exact=True).wait_for()
            anon.screenshot(path=str(ARTIFACTS / "signed-out-missing-profile-mobile.png"), full_page=True)

            # Keyboard: search field reachable and Escape clears on people page.
            riley.goto(base + "/?people", wait_until="networkidle")
            riley.get_by_label("Handle or name").focus()
            riley.keyboard.type("riley")
            riley.keyboard.press("Escape")
            assert riley.get_by_label("Handle or name").input_value() == ""

            assert not errors, errors
            for page in (riley, casey, anon):
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
            browser.close()
            print(
                json.dumps(
                    {
                        "fixture": "TEST DATA · disposable PGlite · people lane",
                        "run_id": run_id,
                        "find_people": True,
                        "follow_before_post": True,
                        "following_empty": True,
                        "following_feed": True,
                        "profile_run_response": True,
                        "responses_return": True,
                        "signed_out_profile": True,
                        "keyboard_escape_clear": True,
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
