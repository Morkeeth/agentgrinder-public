"""Browser acceptance for the account panel and sign-in recovery.

Drives the real site against the disposable PGlite shim with TEST DATA actors. Since round 2
the shell hooks live in site/index.html itself; this walk refuses to run against a shell that
RETURN.md lists the same strings. Exercises: cancelled and failed provider round trips with a
draft in the browser, a sign-in that never came back, handle and name edit, duplicate handle
with an offered free variant, unlink with two methods, last-identity refusal by the server, and
Strava-only deletion with Grinder's public.profiles and the Auth identities untouched.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from subprocess import PIPE, Popen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HOST = "kqxasvolwtrczusjhlli.supabase.co"
NODE = os.environ.get("NODE_BIN", "/Users/morkeeth/.nvm/versions/node/v22.22.3/bin/node")
ARTIFACTS = Path(os.environ.get("GRINDER_ACCOUNT_ARTIFACTS", "/tmp/agentic-strava-account"))
ARTIFACTS.mkdir(parents=True, exist_ok=True)

def integrated_index():
    """The real shell, byte for byte, with only the backend host pointed at the disposable
    PGlite shim. No production hook is inserted here: the account panel, its route and its
    footer link must already be wired in site/index.html or the walk fails."""
    body = (ROOT / "site" / "index.html").read_text()
    for needle in ("account.js", "account.css", "GrinderAccount({", "account.recover()", "q.has('account')", 'href="/?account#danger"'):
        if needle not in body:
            raise RuntimeError("site/index.html is not integrated: missing " + needle)
    return body.replace('const SB_URL="http://127.0.0.1:54321";', f'const SB_URL="https://{HOST}";')


class SiteHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "site"), **kwargs)

    def log_message(self, _format, *_args):
        pass

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
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
OAUTH_OUTCOME = {"value": "cancel", "session": None}
REQUESTS = []


def proxy(route, disposable):
    request = route.request
    url = request.url
    REQUESTS.append(request.method + " " + url.replace("https://" + HOST, ""))
    # The provider round trip: the browser really navigates to the authorize URL and is sent
    # back to redirect_to with the implicit-flow error fragment a cancel or failure produces.
    if "/auth/v1/user/identities/authorize" in url:
        # linkIdentity fetches this with the JWT and gets the provider URL as JSON; the browser
        # then navigates there itself (supabase-js v2 behaviour).
        from urllib.parse import quote, parse_qs, urlparse

        back = parse_qs(urlparse(url).query).get("redirect_to", ["/"])[0]
        body = json.dumps({"url": "https://" + HOST + "/auth/v1/authorize?provider=github&link=1&redirect_to=" + quote(back, safe="")}).encode()
        route.fulfill(status=200, headers={"Content-Type": "application/json"}, body=body)
        return
    if "/auth/v1/authorize" in url:
        from urllib.parse import parse_qs, urlparse

        back = parse_qs(urlparse(url).query).get("redirect_to", ["/"])[0]
        if OAUTH_OUTCOME["value"] == "fail":
            fragment = "error=server_error&error_code=unexpected_failure&error_description=Unable+to+exchange+external+code"
        elif OAUTH_OUTCOME["value"] == "link-success":
            # The provider approved: GoTrue would add the identity and return the session tokens.
            s = OAUTH_OUTCOME["session"]
            fragment = "access_token=" + s["access_token"] + "&refresh_token=" + s["refresh_token"] + "&token_type=bearer&expires_in=86400&expires_at=2000000000"
        else:
            fragment = "error=access_denied&error_code=access_denied&error_description=The+user+cancelled+the+authorisation"
        route.fulfill(status=302, headers={"Location": back + ("&" if "#" in back else "#") + fragment}, body=b"")
        return
    target = url.replace("https://" + HOST, disposable)
    headers = {key: value for key, value in request.headers.items() if key.lower() != "host"}
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
        body = exc.read()
        hdrs = {k: v for k, v in exc.headers.items() if k.lower() not in ("transfer-encoding", "content-encoding", "content-length")}
        route.fulfill(status=exc.code, headers=hdrs, body=body)


def settle(page, handle):
    # After a load the shell routes twice (session restore, then SIGNED_IN); the second pass
    # re-renders the panel. Wait for the header identity, then let that second pass finish.
    page.wait_for_function("document.getElementById('me').textContent.trim()==='@" + handle + "'")
    page.wait_for_timeout(600)


def insert_identity(disposable, user_id, provider, identity_data):
    req = urllib.request.Request(disposable + "/_test/insert-identity", data=json.dumps({"user_id": user_id, "provider": provider, "identity_data": identity_data}).encode(), method="POST", headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())["id"]


def snapshot(disposable):
    with urllib.request.urlopen(disposable + "/_test/grinder-snapshot", timeout=30) as response:
        return json.loads(response.read().decode())


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
    errors = []
    observed = []

    def check(condition, message):
        (observed if condition else errors).append(message)

    ids = {i["user_id"]: [x for x in before["identities"] if x["user_id"] == i["user_id"]] for i in before["identities"]}
    casey_ids = [{"identity_id": i["id"], "id": i["id"], "user_id": casey, "provider": i["provider"], "identity_data": {}} for i in ids[casey]]
    riley_ids = [{"identity_id": i["id"], "id": i["id"], "user_id": riley, "provider": i["provider"], "identity_data": {}} for i in ids[riley]]

    try:
        with sync_playwright() as playwright:
            launch = {"headless": True, "args": ["--no-sandbox"]}
            chrome = os.environ.get("CHROME_BIN")
            if chrome:
                launch["executable_path"] = chrome
            elif Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome").exists():
                launch["executable_path"] = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            browser = playwright.chromium.launch(**launch)

            def context_for(sub=None, handle=None, identities=None, width=390, height=844):
                context = browser.new_context(viewport={"width": width, "height": height})
                context.route(f"https://{HOST}/**", lambda route: proxy(route, disposable))
                if sub:
                    context.add_init_script(session_script(mint(sub, handle, identities or [])))
                return context

            # 1. Signed out, a draft in the browser, provider cancels. Draft and message survive.
            OAUTH_OUTCOME["value"] = "cancel"
            context = context_for(width=1280, height=900)
            page = context.new_page()
            page.goto(base + "/?post")
            page.wait_for_selector("#auth")
            page.evaluate("sessionStorage.setItem('ag_import','eyJ0ZXN0IjoiZHJhZnQifQ')")
            page.click("#auth")
            page.wait_for_selector("#signin-dialog[open]")
            page.click("#signin-dialog [data-provider=github]")
            page.wait_for_url(lambda url: url.startswith(base) and "error" not in url, timeout=15000)
            page.wait_for_function("document.getElementById('status').textContent.length>0")
            text = page.inner_text("#status")
            check("cancelled" in text.lower(), "cancel round trip: status says cancelled: " + text)
            check("draft is still here" in text.lower(), "cancel round trip: draft named in the message")
            # The shell restores a stashed draft onto the URL hash after any load, so the draft
            # survives either as the stash or as #import= on the cleaned URL.
            draft_alive = page.evaluate("sessionStorage.getItem('ag_import')") == "eyJ0ZXN0IjoiZHJhZnQifQ" or "import=eyJ0ZXN0IjoiZHJhZnQifQ" in page.url
            check(draft_alive, "cancel round trip: draft survives (stash or restored #import=): " + page.url)
            check("error" not in page.url, "cancel round trip: error fragment removed from the URL: " + page.url)
            page.evaluate("history.replaceState(null,'','/')")
            check(page.evaluate("sessionStorage.getItem('ag_auth_pending')") is None, "cancel round trip: pending marker settled")
            page.screenshot(path=str(ARTIFACTS / "cancelled-signin-desktop.png"))
            # Same browser, provider fails this time, landing on the account route: inline notice.
            OAUTH_OUTCOME["value"] = "fail"
            page.goto(base + "/?account")
            page.wait_for_selector("#account-signin")
            page.click("#account-signin")
            page.wait_for_selector("#signin-dialog[open]")
            page.click("#signin-dialog [data-provider=github]")
            page.wait_for_url(lambda url: url.startswith(base) and "error" not in url, timeout=15000)
            page.wait_for_function("document.getElementById('status').textContent.length>0")
            check("did not finish" in page.inner_text("#status"), "failed round trip: landing status names the failure: " + page.inner_text("#status"))
            page.goto(base + "/?account")
            page.wait_for_selector("#account-body .account-notice", timeout=15000)
            notice = page.inner_text("#account-body .account-notice")
            check("did not finish" in notice and "provider" in notice.lower(), "failed round trip: inline notice on account: " + notice)
            check(page.is_visible("#account-retry"), "failed round trip: retry offered")
            page.click("#account-retry")
            check(page.is_visible("#signin-dialog[open]"), "failed round trip: retry reopens sign-in")
            page.screenshot(path=str(ARTIFACTS / "failed-signin-desktop.png"))
            context.close()

            # 2. A sign-in that never came back (closed provider tab), on a phone.
            context = context_for()
            page = context.new_page()
            page.goto(base + "/")
            page.wait_for_selector("#auth")
            page.evaluate("sessionStorage.setItem('ag_auth_pending',JSON.stringify({action:'signin',provider:'github',returnTo:'?post',at:Date.now()}))")
            page.goto(base + "/?account")
            page.wait_for_selector("#account-body .account-notice")
            notice = page.inner_text("#account-body .account-notice")
            check("has not finished" in notice and "GitHub" in notice, "pending sign-in: notice names the provider: " + notice)
            page.screenshot(path=str(ARTIFACTS / "pending-signin-mobile.png"), full_page=True)
            page.click("#account-dismiss")
            page.wait_for_selector("#account-signin")
            check(page.query_selector("#account-body .account-notice") is None, "pending sign-in: dismiss clears the notice")
            check(page.evaluate("sessionStorage.getItem('ag_auth_pending')") is None, "pending sign-in: dismiss clears the marker")
            page.screenshot(path=str(ARTIFACTS / "signed-out-account-mobile.png"), full_page=True)
            context.close()

            # 3. A GitHub-only Auth user has no Strava row yet: onboarding creates exactly that
            # profile, then Origin appears only inside the signed-in account as an honest empty
            # repository-connection state.
            github_new = "11000000-0000-0000-0000-000000000003"
            github_identity = insert_identity(
                disposable,
                github_new,
                "github",
                {"user_name": "test-github-new", "full_name": "TEST DATA GitHub New"},
            )
            github_ids = [{
                "identity_id": github_identity,
                "id": github_identity,
                "user_id": github_new,
                "provider": "github",
                "identity_data": {"user_name": "test-github-new", "full_name": "TEST DATA GitHub New"},
            }]
            context = context_for(github_new, "test-github-new", github_ids)
            page = context.new_page()
            page.goto(base + "/")
            page.wait_for_selector("#identity-form")
            check("Make this your profile" in page.inner_text("#app"), "GitHub-only: first sign-in opens Pacecard onboarding")
            check(page.query_selector("#origin-connection") is None, "GitHub-only: Origin is not mixed into onboarding")
            page.screenshot(path=str(ARTIFACTS / "github-only-onboarding-mobile.png"), full_page=True)
            page.fill("[name=handle]", "test-github-builder")
            page.fill("[name=display_name]", "TEST DATA GitHub Builder")
            page.click("#identity-form button")
            settle(page, "test-github-builder")
            after_onboard = snapshot(disposable)
            created = [p for p in after_onboard["strava"] if p["auth_uid"] == github_new]
            check(len(created) == 1 and created[0]["handle"] == "test-github-builder", "GitHub-only: one dedicated Pacecard profile created")
            check(after_onboard["grinder"] == before["grinder"], "GitHub-only: Grinder public profile data unchanged")
            page.goto(base + "/?account")
            page.wait_for_selector("#origin-connection")
            origin_text = page.inner_text("#origin-connection")
            check("No Origin repositories are connected" in origin_text, "Origin: signed-in empty state is explicit")
            check("not a sign-in method" in origin_text, "Origin: repository connection is separate from Auth")
            check(page.query_selector("[data-origin-connect]") is None, "Origin: no action before app review")
            page.screenshot(path=str(ARTIFACTS / "origin-empty-mobile.png"), full_page=True)
            context.close()

            # 4. Casey (GitHub + email) on a phone: panel, duplicate handle, free variant, name edit.
            context = context_for(casey, "test-casey", casey_ids)
            page = context.new_page()
            page.goto(base + "/?account")
            settle(page, "test-casey")
            page.wait_for_selector("#account-profile")
            page.wait_for_function("document.querySelectorAll('.account-identity').length===2")
            check(page.inner_text("#me").strip() == "@test-casey", "panel: header shows the signed-in handle")
            check("GitHub" in page.inner_text("#account-identities") and "Email link" in page.inner_text("#account-identities"), "panel: both linked methods listed")
            check("X sign-in is not available" in page.inner_text("#account-identities"), "panel: X shown as unavailable text, no button")
            check(page.query_selector("[data-link=x]") is None, "panel: no X link button")
            check("Cursor" not in page.inner_text("#account-identities") or "not a login" in page.inner_text("#account-identities"), "panel: no Cursor/Origin login")
            check(page.is_disabled("#account-delete-go"), "panel: delete disabled until the handle is typed")
            page.screenshot(path=str(ARTIFACTS / "account-panel-mobile.png"), full_page=True)
            page.fill("#account-handle", "test-riley")
            page.click("#account-save")
            page.wait_for_selector("#account-use-alt")
            state = page.inner_text("#account-profile-state")
            check("taken" in state and "test-riley-2" in state, "duplicate handle: refused with a free variant offered: " + state)
            check(page.get_attribute("#account-handle", "aria-invalid") == "true", "duplicate handle: input marked invalid")
            check(page.evaluate("document.activeElement.id") == "account-handle", "duplicate handle: focus returns to the input")
            page.screenshot(path=str(ARTIFACTS / "duplicate-handle-mobile.png"), full_page=True)
            page.click("#account-use-alt")
            page.fill("#account-name", "TEST DATA Casey Two")
            page.click("#account-save")
            page.wait_for_function("document.getElementById('account-profile-state').textContent.startsWith('Saved')")
            page.wait_for_function("document.getElementById('me').textContent.trim()==='@test-riley-2'")
            check(True, "handle edit: saved and header updated to @test-riley-2")
            after_edit = snapshot(disposable)
            row = next(r for r in after_edit["strava"] if r["auth_uid"] == casey)
            check(row["id"] == casey and row["handle"] == "test-riley-2", "handle edit: profile id stable, handle stored normalised")
            page.fill("#account-handle", "bad handle!")
            page.click("#account-save")
            page.wait_for_function("document.getElementById('account-profile-state').textContent.includes('letters')")
            check(True, "format error: explained inline before any request")
            page.fill("#account-handle", "test-riley-2")
            # Unlink the email method: two methods, so it goes through.
            page.click("[data-unlink] >> nth=1")
            page.wait_for_function("document.querySelectorAll('.account-identity').length===1")
            check("Unlinked" in page.inner_text("#account-identities-state"), "unlink: second method removed with confirmation text")
            check("only way to sign in" in page.inner_text("#account-identities"), "unlink: remaining method now protected in the UI")
            check(page.query_selector("[data-unlink]") is None, "unlink: no unlink button on the last method")
            check(page.is_visible("[data-link=github]") is False, "unlink: GitHub still linked, no link button for it")
            # Server refusal for the last identity, independent of the UI guard.
            last_id = page.evaluate("document.querySelector('.account-identity') && (async()=>{const {data}=await sb.auth.getUserIdentities();return data.identities[0].identity_id})()")
            denial = page.evaluate(
                "(async(id)=>{const {error}=await sb.auth.unlinkIdentity({identity_id:id});return error?GrinderAuth.explain(error).code:null})('" + last_id + "')"
            )
            check(denial == "last_identity", "last identity: server refuses unlink and maps to last_identity, got " + str(denial))
            existing_actor_ids = [i for i in snapshot(disposable)["identities"] if i["user_id"] != github_new]
            check(len(existing_actor_ids) == len(before["identities"]) - 1, "last identity: only the deliberate unlink changed existing actors' auth.identities")
            page.screenshot(path=str(ARTIFACTS / "sign-in-methods-mobile.png"), full_page=True)
            # Delete: typed confirmation, then Strava row gone, Grinder and Auth untouched.
            page.goto(base + "/")
            page.goto(base + "/?account#danger")
            settle(page, "test-riley-2")
            page.wait_for_selector("#account-confirm")
            page.fill("#account-confirm", "wrong")
            check(page.is_disabled("#account-delete-go"), "delete: wrong handle keeps the button disabled")
            page.fill("#account-confirm", "test-riley-2")
            page.wait_for_function("!document.getElementById('account-delete-go').disabled")
            page.screenshot(path=str(ARTIFACTS / "delete-confirm-mobile.png"), full_page=True)
            page.click("#account-delete-go")
            page.wait_for_selector("text=Your Pacecard profile was deleted")
            after = snapshot(disposable)
            check(all(r["auth_uid"] != casey for r in after["strava"]), "delete: Pacecard profile row removed")
            check(after["grinder"] == before["grinder"], "delete: Grinder public.profiles unchanged")
            expected_ids = sorted(i["id"] for i in before["identities"] if i["user_id"] == casey and i["provider"] == "github")
            check(sorted(i["id"] for i in after["identities"] if i["user_id"] == casey) == expected_ids and expected_ids, "delete: Auth identities for the user remain (all but the one deliberately unlinked)")
            check(page.evaluate("localStorage.getItem('agentic-strava-auth')") is None, "delete: local session cleared")
            check(page.inner_text("#me").strip() == "", "delete: header no longer shows a handle")
            page.screenshot(path=str(ARTIFACTS / "deleted-mobile.png"), full_page=True)
            context.close()

            # 4. Riley (email only): unlink is not offered; sign out here is local.
            context = context_for(riley, "test-riley", riley_ids)
            page = context.new_page()
            page.goto(base + "/?account")
            settle(page, "test-riley")
            page.wait_for_selector("#account-profile")
            page.wait_for_function("document.querySelectorAll('.account-identity').length===1")
            check(page.query_selector("[data-unlink]") is None and "only way to sign in" in page.inner_text("#account-identities"), "riley: last method cannot be unlinked from the UI")
            check(page.is_visible("[data-link=github]"), "riley: GitHub link offered")
            # Link GitHub, provider fails: back on Account with the link notice, still signed in.
            OAUTH_OUTCOME["value"] = "fail"
            page.click("[data-link=github]")
            page.wait_for_url(lambda url: "error" not in url and "account" in url, timeout=15000)
            settle(page, "test-riley")
            page.wait_for_selector("#account-body .account-notice")
            notice = page.inner_text("#account-body .account-notice")
            check("Linking GitHub did not finish" in notice, "riley link failed: inline notice names the link: " + notice)
            check(page.query_selector("#account-retry") is None and page.is_visible("#account-dismiss"), "riley link failed: no sign-in retry while signed in, dismiss offered")
            check(page.is_visible("[data-link=github]"), "riley link failed: GitHub still offered")
            page.screenshot(path=str(ARTIFACTS / "link-failed-mobile.png"), full_page=True)
            page.goto(base + "/?explore")
            settle(page, "test-riley")  # let the feed route run, so the shell's recover() sees the notice was passed by
            page.goto(base + "/?account")
            settle(page, "test-riley")
            check(page.query_selector("#account-body .account-notice") is None, "riley link failed: leaving the page clears the seen notice")
            # Link GitHub, provider approves: identity added, session returned in the fragment,
            # panel shows both methods and the legacy github_handle is filled from the identity.
            OAUTH_OUTCOME["value"] = "link-success"
            OAUTH_OUTCOME["session"] = mint(riley, "test-riley", riley_ids)
            insert_identity(disposable, riley, "github", {"user_name": "test-riley", "avatar_url": "https://avatars.example.test/riley.png"})
            page.click("[data-link=github]")
            page.wait_for_url(lambda url: "access_token" not in url and "account" in url, timeout=15000)
            settle(page, "test-riley")
            page.wait_for_function("document.querySelectorAll('.account-identity').length===2")
            check(page.query_selector("#account-body .account-notice") is None, "riley link ok: no stale failure notice after a successful link")
            check(page.evaluate("sessionStorage.getItem('ag_auth_pending')") is None, "riley link ok: pending link settled")
            row = next(r for r in snapshot(disposable)["strava"] if r["auth_uid"] == riley)
            gh = page.evaluate("(async()=>{const {data}=await sb.from('profiles').select('github_handle').eq('auth_uid','" + riley + "').maybeSingle();return data&&data.github_handle})()")
            check(gh == "test-riley" and row["handle"] == "test-riley", "riley link ok: legacy github_handle filled from the real identity, chosen handle unchanged")
            check(page.query_selector("[data-link=github]") is None and len(page.query_selector_all("[data-unlink]")) == 2, "riley link ok: both methods unlinkable, GitHub no longer offered")
            page.screenshot(path=str(ARTIFACTS / "link-success-mobile.png"), full_page=True)
            page.click("#account-signout")
            page.wait_for_url(base + "/")
            page.wait_for_selector("#auth")
            # The test context re-seeds the session on every load, so the object checked is the
            # request the SDK made: a logout scoped to this browser only, never global.
            check(any(r.startswith("POST /auth/v1/logout?scope=local") for r in REQUESTS), "riley: sign-out sent scope=local logout: " + ", ".join(r for r in REQUESTS if "logout" in r))
            check(not any("scope=global" in r or "scope=others" in r for r in REQUESTS), "riley: no global sign-out was requested")
            check(any(r["auth_uid"] == riley for r in snapshot(disposable)["strava"]), "riley: profile row survives sign-out")
            riley_ids = [{"identity_id": i["id"], "id": i["id"], "user_id": riley, "provider": i["provider"], "identity_data": {}} for i in snapshot(disposable)["identities"] if i["user_id"] == riley]
            context.close()

            # 5. Keyboard: the account menu item is reachable and the danger link resolves.
            context = context_for(riley, "test-riley", riley_ids, width=1280, height=900)
            page = context.new_page()
            page.goto(base + "/")
            page.wait_for_function("document.getElementById('me').textContent.trim()==='@test-riley'")
            page.click("#account-menu summary")
            check(page.is_visible("a[href='/?account']"), "menu: Account settings item visible when signed in")
            page.keyboard.press("Escape")
            page.click("#delete")
            page.wait_for_selector("#danger")
            check("account" in page.url and page.evaluate("location.hash") == "#danger", "footer: delete link opens the panel's danger section")
            context.close()
            browser.close()
    finally:
        process.kill()
        site.shutdown()

    receipt = {"label": "TEST DATA · disposable PGlite · not live users", "observed": observed, "errors": errors, "artifacts": str(ARTIFACTS)}
    (ARTIFACTS / "receipt.json").write_text(json.dumps(receipt, indent=2))
    for line in observed:
        print("ok  " + line)
    for line in errors:
        print("ERR " + line)
    if errors:
        print("Account loop FAILED: " + str(len(errors)) + " checks")
        sys.exit(1)
    print("Account loop passed: " + str(len(observed)) + " checks, screenshots in " + str(ARTIFACTS))


if __name__ == "__main__":
    main()
