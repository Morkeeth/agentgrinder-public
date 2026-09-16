// Ridge persistence through a real PostgreSQL round trip, plus the excluded-reader contract.
// Isolated PGlite and the repository's PostgREST shim. TEST DATA actors only.
// No network, no hosted writes, no migration applied to any live database.
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { ImageResponse } from "@vercel/og";
import {
  bootDisposable,
  startDisposableServer,
  mintJwt,
  seedJourneyActors,
  CASEY,
  RILEY,
} from "./disposable-supabase.mjs";
import { runtimeConfig } from "../server/runtime-config.mjs";
import { readPublic, card, privateCard } from "../server/public-run.mjs";

const STRANGER = "11000000-0000-0000-0000-000000000003";
const BINS = 50;
// One deterministic ridge. The shape does not matter, the survival of every bin does.
const RIDGE = Array.from({ length: BINS }, (_, i) => (i % 7 === 0 ? 4 : i % 3));
const WORKER_BINS = Array.from({ length: BINS }, (_, i) => (i > 10 && i < 30 ? 2 : 0));
const COMMIT_BINS = [3, 17, 42];
const RIDGE_BASIS = "wall-time";
const RIDGE_WALL_SECONDS = 1234.5;
// The store's own count, deliberately different from the transcript's. The two vocabularies
// never match on real data, so the fixture must disagree or it proves nothing.
const RIDGE_TOOL_CALLS = 255;
const TRANSCRIPT_TOOL_CALLS = 226;

const config = runtimeConfig();
const { db } = await bootDisposable();
await seedJourneyActors(db);
await db.exec("reset role");
await db.query(
  "insert into strava.profiles(id,auth_uid,handle,display_name,name) values($1,$1,'test-stranger','TEST DATA Stranger','TEST DATA Stranger')",
  [STRANGER],
);
const { server, url: restUrl } = await startDisposableServer(db);

function headers(sub, write) {
  const h = { apikey: "local-development-only" };
  h[write ? "Content-Profile" : "Accept-Profile"] = "strava";
  if (write) h["Content-Type"] = "application/json";
  if (sub) h.Authorization = "Bearer " + mintJwt(sub, "test-" + sub.slice(0, 8) + "@example.test");
  return h;
}

// The browser Save path: POST /rest/v1/runs with the ridge fields in the body.
async function saveRun(sub, row) {
  const response = await fetch(restUrl + "/rest/v1/runs?select=id", {
    method: "POST",
    headers: headers(sub, true),
    body: JSON.stringify(row),
  });
  const payload = await response.json();
  assert.equal(response.status, 200, "Save must succeed: " + JSON.stringify(payload));
  return payload[0].id;
}

// The browser reload path: the run view and the feed both select every column.
async function readRun(sub, id) {
  const response = await fetch(restUrl + "/rest/v1/runs?select=*&id=eq." + id, {
    headers: headers(sub, false),
  });
  assert.equal(response.status, 200);
  return await response.json();
}

function ridgeFields(row) {
  return {
    ridge: row.ridge,
    worker_bins: row.worker_bins,
    commit_bins: row.commit_bins,
    ridge_basis: row.ridge_basis,
    ridge_wall_seconds: row.ridge_wall_seconds,
    ridge_tool_calls: row.ridge_tool_calls,
  };
}

const SENT = {
  ridge: RIDGE,
  worker_bins: WORKER_BINS,
  commit_bins: COMMIT_BINS,
  ridge_basis: RIDGE_BASIS,
  ridge_wall_seconds: RIDGE_WALL_SECONDS,
  ridge_tool_calls: RIDGE_TOOL_CALLS,
};

// TEST 1: a run saved with a ridge keeps its ridge across a reload.
const publicRun = await saveRun(CASEY, {
  profile_id: CASEY,
  title: "TEST DATA ridge survives a reload",
  caption: "TEST DATA caption",
  project: "TEST DATA project",
  visibility: "public",
  harness: "Codex",
  prompts: 12,
  commits: 3,
  tool_calls: TRANSCRIPT_TOOL_CALLS,
  wall_time_s: 1234,
  rhythm: [1, 2, 1],
  ...SENT,
});
const reloaded = (await readRun(CASEY, publicRun))[0];
assert.ok(reloaded, "the owner can reload the run");
assert.deepEqual(ridgeFields(reloaded), SENT, "every ridge field survives the round trip");
assert.equal(reloaded.ridge.length, BINS, "the reloaded ridge has the same bin count");

await db.exec("reset role");
const stored = (
  await db.query(
    "select ridge, worker_bins, commit_bins, ridge_basis, ridge_wall_seconds from strava.runs where id=$1",
    [publicRun],
  )
).rows[0];
assert.notEqual(stored.ridge, null, "SQL on strava.runs shows ridge not null");
assert.equal(stored.ridge.length, BINS, "SQL shows the same bin count");
assert.equal(stored.ridge_basis, RIDGE_BASIS);
assert.equal(Number(stored.ridge_wall_seconds), RIDGE_WALL_SECONDS);
// The disagreement between the two tool counts is recorded, not resolved. The delta is
// derived from the tool_calls column that already exists.
assert.equal(reloaded.ridge_tool_calls - reloaded.tool_calls, 29, "the count delta is readable");

// TEST 2: an excluded reader gets neither the ridge nor a ridge image.
await db.exec("reset role");
await db.query("select set_config('request.jwt.claim.sub',$1,false)", [CASEY]);
await db.exec("set role authenticated");
await db.query(
  "insert into strava.close_friends(owner_profile_id,friend_profile_id) values($1,$2)",
  [CASEY, RILEY],
);
await db.exec("reset role");

const closeRun = await saveRun(CASEY, {
  profile_id: CASEY,
  title: "TEST DATA close friends ridge",
  caption: "TEST DATA private caption",
  project: "TEST DATA project",
  visibility: "close_friends",
  harness: "Codex",
  prompts: 9,
  rhythm: [2, 1, 2],
  ...SENT,
});

// Positive control. Without this the excluded-reader assertion could pass on a query that
// returns nothing to anybody.
const friendRows = await readRun(RILEY, closeRun);
assert.equal(friendRows.length, 1, "a listed close friend still reads the run");
assert.deepEqual(ridgeFields(friendRows[0]), SENT, "a listed close friend still reads the ridge");

const strangerRows = await readRun(STRANGER, closeRun);
assert.deepEqual(strangerRows, [], "an excluded reader gets no row and therefore no ridge");
const anonRows = await readRun(null, closeRun);
assert.deepEqual(anonRows, [], "an anonymous visitor gets no row and therefore no ridge");
assert.ok(
  !JSON.stringify(strangerRows).includes("ridge"),
  "no ridge field name reaches an excluded reader",
);

// The share image path an excluded reader hits: /api/run?id=X&image=1 reads with the anon key.
const anonFetch = (target, options) =>
  fetch(String(target).replace(config.SB_URL, restUrl), options);
assert.equal(
  await readPublic(closeRun, anonFetch),
  null,
  "the image reader gets no close friends row",
);
const excludedTree = privateCard();
const excludedJson = JSON.stringify(excludedTree);
for (const forbidden of ["ridge", "TEST DATA close friends ridge", "TEST DATA private caption", "test-casey"]) {
  assert.ok(!excludedJson.includes(forbidden), "the neutral card omits " + forbidden);
}

const png = async (tree) => {
  const image = new ImageResponse(tree, { width: 1200, height: 630 });
  const bytes = Buffer.from(await image.arrayBuffer());
  assert.equal(bytes.subarray(1, 4).toString(), "PNG", "the renderer produced a PNG");
  assert.equal(bytes.readUInt32BE(16), 1200);
  assert.equal(bytes.readUInt32BE(20), 630);
  return createHash("sha256").update(bytes).digest("hex");
};
const excludedHash = await png(excludedTree);
const neutralHash = await png(privateCard());
assert.equal(excludedHash, neutralHash, "the excluded reader's image is the neutral card, byte for byte");

// TEST 3: the public share image uses the persisted ridge, and a run without bins does not.
const publicRow = await readPublic(publicRun, anonFetch);
assert.ok(publicRow, "a public run is readable by the image path");
assert.deepEqual(ridgeFields(publicRow), SENT, "the public preview select carries the ridge");
const withRidge = JSON.stringify(card(publicRow));
assert.ok(withRidge.includes('"type":"polygon"'), "a persisted ridge draws a filled polygon");
assert.ok(withRidge.includes("Agent ridge"), "the ridge image is labelled Agent ridge");

const legacyRun = await saveRun(CASEY, {
  profile_id: CASEY,
  title: "TEST DATA legacy run without bins",
  caption: "TEST DATA legacy caption",
  visibility: "public",
  harness: "Codex",
  rhythm: [1, 4, 2, 5, 3],
});
const legacyRow = await readPublic(legacyRun, anonFetch);
assert.equal(legacyRow.ridge, null, "a run saved without a ridge stays null, no backfill");
const withoutRidge = JSON.stringify(card(legacyRow));
assert.ok(!withoutRidge.includes('"type":"polygon"'), "no bins means no filled ridge");
assert.ok(withoutRidge.includes("Session trace"), "a run with no bins keeps the rhythm polyline label");
assert.ok(!withoutRidge.includes("Agent ridge"), "a run with no bins is not labelled as a ridge");

// Rasterize both. A tree that satori refuses would make /api/run?image=1 return 503 for every
// public run that has bins, which is worse than the defect this slice fixes.
const ridgeHash = await png(card(publicRow));
const legacyHash = await png(card(legacyRow));
assert.notEqual(ridgeHash, legacyHash, "the persisted ridge changes the rendered pixels");
assert.notEqual(ridgeHash, neutralHash, "the public ridge image is not the neutral card");

server.close();
await db.close();
console.log(
  "PASS: ridge survives save and reload in SQL and over REST, an excluded reader gets no ridge and the neutral image, and the share card draws the ridge only when bins exist",
);
