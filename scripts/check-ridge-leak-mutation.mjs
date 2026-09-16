// Red-light audit for the excluded-reader half of scripts/test-ridge-persistence.mjs.
// It re-runs those assertions against a deliberately widened database. If the assertions still
// pass here, they are a check nobody has seen fail. Nothing is applied to any live database.
// Run it by hand. It exits 0 only when the assertions DID fail on the widened database.
import assert from "node:assert/strict";
import {
  bootDisposable,
  startDisposableServer,
  mintJwt,
  seedJourneyActors,
  CASEY,
  RILEY,
} from "./disposable-supabase.mjs";
import { runtimeConfig } from "../server/runtime-config.mjs";
import { readPublic } from "../server/public-run.mjs";

const STRANGER = "11000000-0000-0000-0000-000000000003";
const BINS = 50;
const RIDGE = Array.from({ length: BINS }, (_, i) => (i % 7 === 0 ? 4 : i % 3));
const WORKER_BINS = Array.from({ length: BINS }, () => 1);

const config = runtimeConfig();
const { db } = await bootDisposable();
await seedJourneyActors(db);
await db.exec("reset role");
await db.query(
  "insert into strava.profiles(id,auth_uid,handle,display_name,name) values($1,$1,'test-stranger','TEST DATA Stranger','TEST DATA Stranger')",
  [STRANGER],
);
const { server, url: restUrl } = await startDisposableServer(db);

const closeRun = (
  await db.query(
    `insert into strava.runs(profile_id,title,caption,visibility,ridge,worker_bins,commit_bins,ridge_basis,ridge_wall_seconds)
     values($1,'TEST DATA leak probe run','TEST DATA leak caption','close_friends',$2,$3,'[1]'::jsonb,'wall-time',12.5) returning id`,
    [CASEY, JSON.stringify(RIDGE), JSON.stringify(WORKER_BINS)],
  )
).rows[0].id;

// THE MUTATION. This is the leak the slice must not introduce: the restrictive audience policy
// from 002_close_friends.sql is dropped and every reader is allowed every row.
await db.exec(`drop policy if exists grinder_close_friends_audience on strava.runs;
create policy ridge_leak_mutation on strava.runs for select to anon, authenticated using (true);`);

const read = async (sub) => {
  const headers = { apikey: "local-development-only", "Accept-Profile": "strava" };
  if (sub) headers.Authorization = "Bearer " + mintJwt(sub, "test@example.test");
  const response = await fetch(restUrl + "/rest/v1/runs?select=*&id=eq." + closeRun, { headers });
  return await response.json();
};

const failures = [];
const expectRed = async (name, check) => {
  try {
    await check();
    console.log("STILL GREEN on a leaking database: " + name);
  } catch (error) {
    failures.push(name);
    console.log("RED as required: " + name + " :: " + error.message.split("\n")[0]);
  }
};

console.log("MUTATION A: the audience policy leaks. The readPublic visibility filter is intact.");
await expectRed("an excluded reader gets no row and therefore no ridge", async () =>
  assert.deepEqual(await read(STRANGER), []));
await expectRed("an anonymous visitor gets no row and therefore no ridge", async () =>
  assert.deepEqual(await read(null), []));
const anonFetch = (target, options) =>
  fetch(String(target).replace(config.SB_URL, restUrl), options);
await expectRed("the image reader gets no close friends row, policy leak only", async () =>
  assert.equal(await readPublic(closeRun, anonFetch), null));

// MUTATION B. The image path has two independent defences: the row policy and the
// visibility=eq.public filter in readPublic. Mutation A trips only the first, so the image
// assertion needs the second defence removed as well before it can go red. This fetcher
// simulates that second mutation without editing the file.
console.log("MUTATION B: the audience policy leaks AND readPublic drops its visibility filter.");
const leakyFetch = (target, options) => {
  const rewritten = new URL(String(target).replace(config.SB_URL, restUrl));
  rewritten.searchParams.delete("visibility");
  return fetch(rewritten, options);
};
await expectRed("the image reader gets no close friends row, both defences removed", async () =>
  assert.equal(await readPublic(closeRun, leakyFetch), null));

server.close();
await db.close();
const required = 3;
if (failures.length < required) {
  console.error("Only " + failures.length + " assertions went red. The check is too weak.");
  process.exit(1);
}
console.log(
  "PASS: every excluded-reader assertion can go red. The database assertions go red on a leaking policy. " +
    "The image assertion needs both the policy and the visibility filter removed, which is two defences, not one.",
);
