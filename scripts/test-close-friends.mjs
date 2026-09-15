// Actual PostgreSQL RLS through the repository's disposable PGlite fixture.
// Synthetic actors only. No network, migration application, or hosted writes.
import assert from "node:assert/strict";
import {
  bootDisposable,
  CASEY,
  RILEY,
  seedJourneyActors,
} from "./disposable-supabase.mjs";

const STRANGER = "11000000-0000-0000-0000-000000000003";
const { db, as, anonymous, denied } = await bootDisposable();
await seedJourneyActors(db);
await db.exec("reset role");
await db.query(
  "insert into strava.profiles(id,auth_uid,handle,display_name,name) values($1,$1,'test-stranger','TEST DATA Stranger','TEST DATA Stranger')",
  [STRANGER],
);

await as(CASEY);
await db.query(
  "insert into strava.close_friends(owner_profile_id,friend_profile_id) values($1,$2)",
  [CASEY, RILEY],
);
const closeRun = (
  await db.query(
    "insert into strava.runs(profile_id,title,visibility) values($1,'TEST DATA close friends run','close_friends') returning id",
    [CASEY],
  )
).rows[0].id;
assert.equal(
  (
    await db.query(
      "select friend_profile_id from strava.close_friends where owner_profile_id=$1",
      [CASEY],
    )
  ).rows.length,
  1,
);

await as(RILEY);
assert.equal(
  (await db.query("select id from strava.runs where id=$1", [closeRun])).rows
    .length,
  1,
  "a listed close friend can read the run",
);
await db.query(
  "insert into strava.acks(from_profile,to_profile,run_id,reason) values($1,$2,$3,'shipped')",
  [RILEY, CASEY, closeRun],
);
assert.equal(
  (await db.query("select * from strava.close_friends")).rows.length,
  0,
  "a friend cannot read the owner's private list",
);
await denied(
  "insert into strava.close_friends(owner_profile_id,friend_profile_id) values($1,$2)",
  [CASEY, STRANGER],
);

await as(STRANGER);
assert.equal(
  (await db.query("select id from strava.runs where id=$1", [closeRun])).rows
    .length,
  0,
  "a non-friend cannot read the run",
);

await anonymous();
assert.equal(
  (await db.query("select id from strava.runs where id=$1", [closeRun])).rows
    .length,
  0,
  "an anonymous visitor cannot read the run",
);

await as(CASEY);
assert.equal(
  (
    await db.query("select id from strava.acks where run_id=$1", [closeRun])
  ).rows.length,
  1,
  "a close friend can ACK a readable run",
);
await db.query(
  "delete from strava.close_friends where owner_profile_id=$1 and friend_profile_id=$2",
  [CASEY, RILEY],
);
await as(RILEY);
assert.equal(
  (await db.query("select id from strava.runs where id=$1", [closeRun])).rows
    .length,
  0,
  "removal revokes run access",
);

await db.close();
console.log(
  "PASS: owner-only list, friend read and ACK, non-friend denial, anonymous denial, and removal revocation",
);
