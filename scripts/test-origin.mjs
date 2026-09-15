// Origin repository connection states. Synthetic connector only: no Origin app, OAuth call,
// repository token or production data is used.
import { createRequire } from "node:module";
import assert from "node:assert/strict";

const Origin = createRequire(import.meta.url)("../site/origin.js");

assert.equal(Origin.state({ signedIn: false, configured: true }).kind, "hidden");
assert.equal(Origin.html(Origin.state({ signedIn: false, configured: true })), "", "Origin is absent before Pacecard sign-in");

const unconfigured = Origin.state({ signedIn: true, configured: false });
assert.equal(unconfigured.kind, "hidden", "no connector means no Origin panel");
assert.equal(Origin.html(unconfigured), "", "Origin panel is absent until a connector exists");
assert.equal(Origin.create().html(), "", "shipped controller without a connector renders nothing");
let markup;

assert.equal(Origin.state({ signedIn: true, configured: true }).kind, "connect");
assert.match(Origin.html(Origin.state({ signedIn: true, configured: true })), /data-origin-connect/);
assert.match(Origin.html(Origin.state({ signedIn: true, configured: true, outcome: "cancelled" })), /cancelled.*Nothing changed/s);
assert.match(Origin.html(Origin.state({ signedIn: true, configured: true, error: new Error("Receipt rejected") })), /could not connect.*Receipt rejected/s);
assert.match(Origin.html(Origin.state({ signedIn: true, configured: true, outcome: "disconnected" })), /disconnected/);

const calls = [];
const connected = Origin.create({ connector: {
  async connect() {
    calls.push(["connect"]);
    return { id: "installation-1", repository: "owner/repository" };
  },
  async disconnect(id) {
    calls.push(["disconnect", id]);
  },
} });
let state = await connected.connect();
assert.equal(state.kind, "connected");
assert.deepEqual(state.connections.map((c) => c.repository), ["owner/repository"]);
markup = connected.html();
assert.match(markup, /owner\/repository/);
assert.match(markup, /data-origin-disconnect/);
state = await connected.disconnect("installation-1");
assert.equal(state.kind, "disconnected");
assert.deepEqual(state.connections, []);
assert.deepEqual(calls, [["connect"], ["disconnect", "installation-1"]]);

const cancelled = Origin.create({ connector: { async connect() { return { cancelled: true }; } } });
assert.equal((await cancelled.connect()).kind, "cancelled");
const failed = Origin.create({ connector: { async connect() { throw new Error("Invalid installation receipt"); } } });
state = await failed.connect();
assert.equal(state.kind, "error");
assert.match(state.message, /Invalid installation receipt/);

console.log("PASS Origin: hidden without sign-in or connector, connect, cancel, error, connected and disconnect states");
