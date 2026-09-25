/**
 * DOM proof: Follow signed-out click stores ag_social_return and calls signInGitHub;
 * applyStoredSocialReturn restores inbox filters and clears storage.
 */
import { createRequire } from "node:module";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { JSDOM } from "jsdom";

const require = createRequire(import.meta.url);
const root = new URL("../..", import.meta.url);
const socialPath = new URL("../../site/social.js", import.meta.url);

const dom = new JSDOM('<!doctype html><html><body><div id="app"></div><button id="auth">Sign in</button></body></html>', {
  url: "https://agentic-strava.vercel.app/?u=friend",
  pretendToBeVisual: true,
});
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
globalThis.location = window.location;
globalThis.history = window.history;
globalThis.sessionStorage = window.sessionStorage;
globalThis.HTMLElement = window.HTMLElement;

// Minimal stubs social.js may touch
window.GrinderContract = { message: (e) => String(e?.message || e) };
window.GrinderPeople = {
  present: (p) => ({
    id: p?.id || null,
    handle: p?.handle || p?.github_handle || null,
    display_name: p?.display_name || p?.name || null,
    label: p?.display_name || p?.name || (p?.handle ? "@" + p.handle : "A builder"),
    href: p?.handle ? "/?u=" + encodeURIComponent(p.handle) : null,
  }),
};

const socialSrc = readFileSync(socialPath, "utf8");
window.eval(socialSrc);
assert.equal(typeof window.GrinderSocial, "function");

let signInCalls = 0;
const social = window.GrinderSocial({
  client: {
    from() {
      throw new Error("db should not run for signed-out follow");
    },
  },
  me: () => null,
  app: () => window.document.getElementById("app"),
  frame: () => {},
  status: () => {},
  renderRuns: async () => "",
  signInGitHub: () => {
    signInCalls += 1;
  },
});

const slot = window.document.createElement("div");
slot.id = "social-follow";
window.document.body.append(slot);
window.sessionStorage.clear();

await social.followControl(
  { id: "profile-friend", handle: "friend", name: "Friend" },
  slot,
);

const button = slot.querySelector("#follow-signin");
assert.ok(button, "follow sign-in button mounted");
assert.equal(button.textContent, "Sign in with GitHub");
button.click();
assert.equal(signInCalls, 1, "Follow click invokes signInGitHub");
assert.equal(
  window.sessionStorage.getItem("ag_social_return"),
  "?u=friend",
  "Follow click stores current profile search for return",
);

// Auth return callback with ME present
const signedIn = window.GrinderSocial({
  client: { from() { throw new Error("unused"); } },
  me: () => ({ id: "me" }),
  app: () => window.document.getElementById("app"),
  frame: () => {},
  status: () => {},
  renderRuns: async () => "",
  signInGitHub: () => {},
});

window.sessionStorage.setItem("ag_social_return", "?inbox&filter=unread");
const applied = signedIn.applyStoredSocialReturn();
assert.equal(applied, "?inbox&filter=unread");
assert.equal(window.location.search, "?inbox&filter=unread");
assert.equal(window.sessionStorage.getItem("ag_social_return"), null, "return key cleared");

// A retired section is not a return target. Discover is, since the home became the feed.
window.sessionStorage.setItem("ag_social_return", "?forum");
assert.equal(signedIn.applyStoredSocialReturn(), null, "disallowed forum not applied");
assert.equal(window.sessionStorage.getItem("ag_social_return"), "?forum");

window.sessionStorage.setItem("ag_social_return", "?u=friend");
assert.equal(signedIn.applyStoredSocialReturn(), "?u=friend");
assert.equal(window.location.search, "?u=friend");

assert.equal(signedIn.isSocialReturn("?inbox&filter=unread"), true);
assert.equal(signedIn.isSocialReturn("?forum"), false);
assert.equal(signedIn.isSocialReturn("?explore"), true);

console.log(
  JSON.stringify({
    ok: true,
    followClick: true,
    signInCalls,
    inboxFilterReturn: true,
    profileReturn: true,
    forumRejected: true,
  }),
);
