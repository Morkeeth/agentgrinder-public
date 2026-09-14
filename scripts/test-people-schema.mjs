// Strava-only people lookup: search, blocks, self-follow, recent builders.
import { bootDisposable, CASEY, RILEY, seedJourneyActors } from "./disposable-supabase.mjs";
import assert from "node:assert/strict";

const { db, as, denied } = await bootDisposable();
await seedJourneyActors(db);

await as(CASEY);
await denied(
  "insert into grinder_follows(follower_id,followed_id) values($1,$1)",
  [CASEY],
);

await as(RILEY);
const byHandle = (
  await db.query("select grinder_find_people($1,20) as rows", ["casey"])
).rows[0].rows;
assert.equal(byHandle[0]?.github_handle, "test-casey");
const byName = (
  await db.query("select grinder_find_people($1,20) as rows", ["TEST DATA Casey"])
).rows[0].rows;
assert.equal(byName[0]?.github_handle, "test-casey");

await db.query(
  "insert into grinder_follows(follower_id,followed_id) values($1,$2)",
  [RILEY, CASEY],
);
await db.query(
  "insert into grinder_blocks(blocker_id,blocked_id) values($1,$2)",
  [RILEY, CASEY],
);
assert.equal(
  (await db.query("select grinder_find_people($1,20) as rows", ["casey"])).rows[0]
    .rows.length,
  0,
);

await as(CASEY);
const rev = "a".repeat(64);
await db.query(
  `insert into runs(profile_id,title,visibility,schema_version,measurement_revision,trace_basis)
   values($1,'TEST DATA public people','public',1,$2,'elapsed')`,
  [CASEY, rev],
);

await as(RILEY);
assert.equal(
  (
    await db.query("select grinder_recent_builders(12) as rows")
  ).rows[0].rows.filter((r) => r.github_handle === "test-casey").length,
  0,
);
await db.query(
  "delete from grinder_blocks where blocker_id=$1 and blocked_id=$2",
  [RILEY, CASEY],
);
assert.equal(
  Number(
    (
      await db.query("select grinder_recent_builders(12) as rows")
    ).rows[0].rows.find((r) => r.github_handle === "test-casey").public_runs,
  ),
  1,
);

assert.equal(
  (await db.query("select grinder_find_people($1,20) as rows", ["%"])).rows[0]
    .rows.length,
  0,
);

const fns = (
  await db.query(
    "select proname from pg_proc where pronamespace='strava'::regnamespace and proname in ('grinder_find_people','grinder_recent_builders')",
  )
).rows.map((r) => r.proname);
assert.deepEqual(fns.sort(), ["grinder_find_people", "grinder_recent_builders"]);

console.log(
  "PASS: people search, name match, block hide, self-follow refuse, recent builders, wildcard escape",
);
await db.close();
