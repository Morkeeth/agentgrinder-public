// The human half of Connect: the /?pair approve page, the QR it draws, and the Connections list.
// DOM proof in jsdom against a mocked client. The QR is compared module for module with the
// reference `qrcode` package, which is a dev dependency and ships with nothing.
//
//   node --test scripts/test-connect-pair.mjs
import { JSDOM } from "jsdom";
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import { test } from "node:test";

const require = createRequire(import.meta.url);
const read = (path) => readFileSync(new URL("../" + path, import.meta.url), "utf8");
const CSS = read("site/account.css");
const INDEX = read("site/index.html");
const CONNECT_JS = read("site/connect.js");
const ORIGIN = "https://agentic-strava.vercel.app";

function page(search = "/?pair=BCDFGHJK") {
  const dom = new JSDOM('<!doctype html><html><body><div id="app"></div></body></html>', {
    url: ORIGIN + search,
    pretendToBeVisual: true,
  });
  const { window } = dom;
  globalThis.window = window;
  globalThis.document = window.document;
  globalThis.location = window.location;
  globalThis.history = window.history;
  globalThis.sessionStorage = window.sessionStorage;
  window.eval(read("site/qr.js"));
  window.eval(read("site/connect-status.js"));
  window.eval(read("site/connect.js"));
  window.eval(read("site/pair.js"));
  return window;
}

// One pending pairing, and a record of what the page asked the database to do.
function client(view, { fail = null } = {}) {
  const calls = [];
  return {
    calls,
    rpc(name, args) {
      calls.push({ name, args });
      if (name === "connect_pairing_view") return Promise.resolve({ data: view, error: null });
      if (name === "connect_pairing_decide") {
        if (fail) return Promise.resolve({ data: null, error: new Error(fail) });
        return Promise.resolve({ data: { status: args.p_approve ? "approved" : "denied" }, error: null });
      }
      throw new Error("unexpected rpc " + name);
    },
  };
}
const PENDING = {
  harness: "cursor",
  device_name: "Studio laptop",
  scopes: ["draft", "publish"],
  audiences: ["private"],
  status: "pending",
  expires_in: 840,
};
function mount(window, { me = { id: "profile-1" }, view = PENDING, fail = null } = {}) {
  const db = client(view, { fail });
  const said = [];
  const pair = window.GrinderPair({
    db,
    me: () => me,
    app: () => window.document.getElementById("app"),
    frame: () => {},
    status: (message, bad) => said.push({ message, bad }),
    signInGitHub: () => said.push({ message: "signin" }),
    qr: window.GrinderQR,
  });
  return { pair, db, said, app: window.document.getElementById("app") };
}

test("the approve page shows the device, the harness and the scopes it is granting", async () => {
  const window = page();
  const { pair, db, app } = mount(window);
  await pair.view("BCDFGHJK");
  assert.deepEqual(db.calls[0], { name: "connect_pairing_view", args: { p_user_code: "BCDFGHJK" } });
  const text = app.textContent;
  assert.match(text, /Connect this device\?/);
  assert.match(text, /Studio laptop/);
  assert.match(text, /Cursor/);
  assert.match(text, /save a private draft/);
  assert.match(text, /upload a run as Only me/);
  assert.match(text, /cannot make a run public/);
  assert.match(text, /counts and allowlisted fields only/);
  assert.match(text, /about 14 minutes/);
  assert.ok(app.querySelector("#pair-approve"), "Approve is on the page");
  assert.ok(app.querySelector("#pair-deny"), "Deny is on the page");
  // Nothing about the machine that asked: no path, no address, no project.
  assert.ok(!/\/Users\/|\/home\/|http/.test(text.replace(ORIGIN, "")), text);
});

test("Approve records the decision once and reports it", async () => {
  const window = page();
  const { pair, db, said, app } = mount(window);
  await pair.view("BCDFGHJK");
  app.querySelector("#pair-approve").click();
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.deepEqual(db.calls[1], { name: "connect_pairing_decide", args: { p_user_code: "BCDFGHJK", p_approve: true } });
  assert.match(app.textContent, /Approved/);
  assert.match(app.textContent, /collecting its credential/);
  assert.match(said.at(-1).message, /Approved/);
  assert.equal(app.querySelector("#pair-approve"), null, "the decision is not offered twice");
});

test("Deny records a denial and offers no credential", async () => {
  const window = page();
  const { pair, db, app } = mount(window);
  await pair.view("BCDFGHJK");
  app.querySelector("#pair-deny").click();
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.deepEqual(db.calls[1], { name: "connect_pairing_decide", args: { p_user_code: "BCDFGHJK", p_approve: false } });
  assert.match(app.textContent, /Denied/);
  assert.match(app.textContent, /No credential was issued/);
});

test("a refused decision is shown on the page and can be retried", async () => {
  const window = page();
  const { pair, app } = mount(window, { fail: "That code has already been used" });
  await pair.view("BCDFGHJK");
  app.querySelector("#pair-approve").click();
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.match(app.querySelector("#pair-state").textContent, /already been used/);
  assert.equal(app.querySelector("#pair-approve").disabled, false, "the buttons come back");
});

test("a settled or expired code explains itself instead of offering Approve", async () => {
  for (const [status, expected] of [
    ["approved", /Approved/],
    ["claimed", /Connected/],
    ["denied", /Denied/],
    ["expired", /expired/],
  ]) {
    const window = page();
    const { pair, app } = mount(window, { view: { ...PENDING, status } });
    await pair.view("BCDFGHJK");
    assert.match(app.textContent, expected);
    assert.equal(app.querySelector("#pair-approve"), null, status);
  }
});

test("a typed code is cleaned up, and a wrong one is named as wrong", async () => {
  const window = page("/?pair");
  assert.equal(window.GrinderPair.normalize("bcdf-ghjk"), "BCDFGHJK");
  assert.equal(window.GrinderPair.normalize(" bcdf ghjk "), "BCDFGHJK");
  const { pair, db, app } = mount(window);
  await pair.view("");
  assert.ok(app.querySelector("#pair-code-form"), "the page asks for the code");
  assert.equal(db.calls.length, 0, "nothing is looked up until there is a code");
  app.querySelector("#pair-code").value = "aeiou123";
  app.querySelector("#pair-code-form").dispatchEvent(new window.Event("submit"));
  assert.match(app.querySelector("#pair-code-state").textContent, /eight letters, no vowels and no digits/);
  assert.equal(db.calls.length, 0);
  await pair.view("AEIOU123");
  assert.match(app.querySelector("#pair-code-state").textContent, /eight letters/);
});

test("signed out, the page asks for sign-in and never reads the pairing", async () => {
  const window = page();
  const { pair, db, app } = mount(window, { me: null });
  await pair.view("BCDFGHJK");
  assert.equal(db.calls.length, 0);
  assert.match(app.textContent, /Sign in as the owner/);
  assert.ok(app.querySelector(".qr"), "the phone handoff QR is still offered");
});

test("the page draws a scannable QR of its own pairing link", async () => {
  const window = page();
  const { pair, app } = mount(window);
  await pair.view("BCDFGHJK");
  const svg = app.querySelector(".qr");
  assert.ok(svg, "a QR is drawn");
  assert.match(svg.getAttribute("aria-label"), /phone/i);
  const reference = require("qrcode").create([{ data: ORIGIN + "/?pair=BCDFGHJK", mode: "byte" }], {
    errorCorrectionLevel: "M",
  });
  const drawn = window.GrinderQR.matrix(ORIGIN + "/?pair=BCDFGHJK");
  assert.equal(drawn.modules.length, reference.modules.size);
  assert.equal(drawn.mask, reference.maskPattern, "the mask is chosen by the same penalty rules");
  for (let y = 0; y < reference.modules.size; y += 1) {
    for (let x = 0; x < reference.modules.size; x += 1) {
      assert.equal(drawn.modules[y][x], reference.modules.data[y * reference.modules.size + x] ? 1 : 0, `${x},${y}`);
    }
  }
  // A quiet zone is part of the symbol; without it a phone will not see the finders.
  const [, , width] = svg.getAttribute("viewBox").split(" ").map(Number);
  assert.equal(width, reference.modules.size + 8);
});

test("the QR encoder matches the reference for every mask, version and a non-ASCII payload", () => {
  const window = page();
  const QR = require("qrcode");
  const payloads = [
    ORIGIN + "/?pair=BCDFGHJK",
    "http://localhost:8000/?pair=ZXWVTSRQ",
    "A",
    "STRIVE pairing ünïcode ✓",
    "x".repeat(200),
  ];
  for (const payload of payloads) {
    for (let mask = 0; mask < 8; mask += 1) {
      const reference = QR.create([{ data: payload, mode: "byte" }], { errorCorrectionLevel: "M", maskPattern: mask });
      const drawn = window.GrinderQR.matrix(payload, mask);
      const size = reference.modules.size;
      assert.equal(drawn.modules.length, size, `${payload.length} bytes, mask ${mask}`);
      for (let y = 0; y < size; y += 1) {
        for (let x = 0; x < size; x += 1) {
          assert.equal(drawn.modules[y][x], reference.modules.data[y * size + x] ? 1 : 0, `${payload.length}/${mask} at ${x},${y}`);
        }
      }
    }
  }
  assert.throws(() => window.GrinderQR.matrix("y".repeat(300)), /too long/);
});

test("the approve page is phone first: 44px targets and a 390px layout", () => {
  assert.match(CSS, /\.pair-decide button\{[^}]*min-height:44px/);
  assert.match(CSS, /\.pair \.account-actions button,\.pair \.account-actions \.act\{min-height:44px\}/);
  assert.match(CSS, /\.pair\{max-width:26rem\}/);
  const phone = CSS.slice(CSS.indexOf("@media(max-width:390px){", CSS.indexOf(".pair-qr")));
  assert.match(phone, /\.pair-decide button\{flex:1 1 100%\}/);
  assert.match(CSS, /\.pair-qr \.qr\{width:min\(200px,60vw\)/);
});

test("the route, the scripts and the sign-in return all carry ?pair", () => {
  assert.match(INDEX, /if\(q\.has\('pair'\)\)\{if\(pair\)return pair\.view\(q\.get\('pair'\)\)/);
  assert.match(INDEX, /<script src="\/pair\.js"><\/script>/);
  assert.match(INDEX, /<script src="\/qr\.js"><\/script>/);
  assert.match(INDEX, /<script src="\/connect-status\.js"><\/script>/);
  assert.match(INDEX, /people\|account\|connect\|pair\)/);
  assert.match(read("site/social.js"), /people\|account\|connect\|pair\)/);
});

test("Connections says when each device last synced and marks a week of silence", () => {
  const window = page("/?connect");
  const status = window.GrinderConnectStatus;
  const now = Date.parse("2026-09-23T12:00:00Z");
  const live = {
    id: "token-1",
    device_name: "Studio laptop",
    token_prefix: "ag_1234",
    revoked: false,
    created_at: "2026-09-01T12:00:00Z",
    last_seen_at: "2026-09-23T09:30:00Z",
    expires_at: "2026-12-22T09:30:00Z",
  };
  const quiet = { ...live, id: "token-2", device_name: "Kitchen mini", last_seen_at: "2026-09-15T09:30:00Z" };
  const fresh = { ...live, id: "token-3", device_name: "New box", last_seen_at: null, created_at: "2026-09-22T09:30:00Z" };
  const waiting = { ...fresh, id: "token-4", created_at: "2026-09-10T09:30:00Z" };
  const revoked = { ...quiet, id: "token-5", revoked: true };
  assert.equal(status.lastSynced(live, now), "Last synced 2 hours ago");
  assert.equal(status.lastSynced(quiet, now), "Last synced 8 days ago");
  assert.equal(status.lastSynced(fresh, now), "No run yet");
  assert.equal(status.lastSynced(revoked, now), "Revoked");
  assert.equal(status.isStale(live, now), false);
  assert.equal(status.isStale(quiet, now), true);
  assert.equal(status.isStale(fresh, now), false, "a new device is waiting, not stale");
  assert.equal(status.isStale(waiting, now), true, "a device that never synced in its first week is stale");
  assert.equal(status.isStale(revoked, now), false, "a revoked device is finished, not stale");
  assert.equal(status.STALE_DAYS, 7);
});

test("the Connections list renders last synced, the amber mark and Revoke", () => {
  // listHtml is internal to the page module, so render the real list through the real view.
  const window = page("/?connect");
  const rows = [
    {
      id: "token-1",
      device_name: "Studio laptop",
      token_prefix: "ag_1234",
      revoked: false,
      created_at: "2020-01-01T00:00:00Z",
      last_seen_at: new Date(Date.now() - 8 * 86400000).toISOString(),
      expires_at: new Date(Date.now() + 80 * 86400000).toISOString(),
    },
  ];
  const connect = window.GrinderConnect({
    db: {
      rpc: (name) => Promise.resolve({ data: name === "agent_token_list" ? rows : null, error: null }),
      from: () => ({ select: () => ({ eq: () => ({ eq: () => ({ order: () => ({ limit: () => Promise.resolve({ data: [], error: null }) }) }) }) }) }),
    },
    me: () => ({ id: "profile-1" }),
    app: () => window.document.getElementById("app"),
    frame: () => {},
    status: () => {},
  });
  return connect.view().then(() => {
    const item = window.document.querySelector(".connect-token");
    assert.ok(item, "the device is listed");
    assert.ok(item.classList.contains("is-stale"), "a week of silence is marked");
    assert.match(item.textContent, /Last synced 8 days ago/);
    assert.match(item.textContent, /no run for over a week/);
    assert.match(item.textContent, /renews for 90 days on each run/);
    assert.equal(item.querySelector("[data-revoke]").textContent, "Revoke");
    assert.match(window.document.querySelector("#connect-device-title").textContent, /pair the device itself/);
    assert.match(CONNECT_JS, /api\/connect\/device/);
  });
});
