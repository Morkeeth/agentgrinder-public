// Distinct authenticated contexts against real moments/practices/adoption RPCs.
// Isolated PGlite. TEST DATA users, not claimed live builders.
import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
import {
  bootDisposable,
  seedJourneyActors,
  seedCoachRun,
  CASEY,
  RILEY,
} from "./disposable-supabase.mjs";

const { db, as, anonymous, denied } = await bootDisposable();
await seedJourneyActors(db);

await as(CASEY);
const caseyRun = await seedCoachRun(
  db,
  CASEY,
  "TEST DATA Casey coach sitting",
  "a".repeat(64),
  "now()-interval '2 days'",
);
await as(CASEY);
const practice = (
  await db.query(
    "insert into grinder_practice_versions(owner_id,title,task_context,instruction,expected,visibility,source_run,harness) values($1,$2,'Coach experiment on this grind',$3,$4,'private',$5,'Codex') returning id",
    [
      CASEY,
      "Run test_draft_renders in the same turn as the claim",
      "In the same human turn as the completion claim, run test_draft_renders and keep its result in that turn before saying it passed.",
      "check_claim on the named target returns verified, with test_draft_renders in the evidence snippet.",
      caseyRun,
    ],
  )
).rows[0].id;
const attempt = (await db.query("select grinder_start_attempt($1,$2,false) id", [practice, caseyRun]))
  .rows[0].id;
const frozen = (await db.query("select * from grinder_practice_attempts where id=$1", [attempt])).rows[0];
assert.equal(frozen.baseline.measurement_revision, "a".repeat(64));
assert.equal(frozen.baseline.harness, "Codex");
assert.equal(frozen.owner_id, CASEY);
assert.equal(frozen.visibility, "private");

const caseyLater = (
  await db.query(
    "insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts,claims,claims_verified,artifacts_produced,rhythm) values($1,'TEST DATA Casey later sitting','private','Codex',1,$2,'elapsed',now(),3,2,2,1,'[1,1,1]'::jsonb) returning id",
    [CASEY, "b".repeat(64)],
  )
).rows[0].id;
await db.query(
  "select grinder_review_attempt($1,$2,true,'keep','TEST DATA named check now has same-turn evidence. One observation, not proof of cause.')",
  [attempt, caseyLater],
);
const reviewed = (await db.query("select * from grinder_practice_attempts where id=$1", [attempt])).rows[0];
assert.equal(reviewed.decision, "keep");
assert.equal(reviewed.outcome.measurement_revision, "b".repeat(64));
assert.equal(reviewed.outcome.harness, "Codex");

const moment = (
  await db.query(
    "insert into grinder_run_moments(run_id,owner_id,measurement_revision,title,claim,evidence_ref,excerpt,limitation,next_action) values($1,$2,$3,$4,$5,$6,$7,$8,$9) returning id",
    [
      caseyRun,
      CASEY,
      "a".repeat(64),
      "TEST DATA the named check that was missing",
      "TEST DATA check_claim found no evidence in that turn",
      "TEST DATA receipt/test_draft_renders",
      "TEST DATA: test_draft_renders had no matching snippet",
      "One local fixture sitting, not adoption or a real-user result",
      "Run test_draft_renders in the same turn as the claim",
    ],
  )
).rows[0].id;
await as(RILEY);
assert.equal((await db.query("select * from grinder_run_moments where id=$1", [moment])).rows.length, 0);
await as(CASEY);
await db.query("update runs set visibility='public' where id=$1", [caseyRun]);

await as(RILEY);
const rileyBase = await seedCoachRun(
  db,
  RILEY,
  "TEST DATA Riley own baseline",
  "c".repeat(64),
  "now()-interval '3 days'",
);
await as(RILEY);
await denied("select grinder_adopt_moment($1,$2,$3,$4)", [
  moment,
  caseyRun,
  "Run test_draft_renders in the same turn as the claim",
  "check_claim returns verified",
]);
const kept = (
  await db.query("select grinder_adopt_moment($1,$2,$3,$4) result", [
    moment,
    rileyBase,
    "Run test_draft_renders in the same turn as the claim",
    "check_claim returns verified on my own later sitting",
  ])
).rows[0].result;
assert.equal(kept.practice_id != null, true);
const keptPractice = (
  await db.query("select * from grinder_practice_versions where id=$1", [kept.practice_id])
).rows[0];
assert.equal(keptPractice.owner_id, RILEY);
assert.equal(keptPractice.source_run, rileyBase);
assert.notEqual(keptPractice.source_run, caseyRun);
assert.equal(keptPractice.visibility, "private");
const keptAttempt = (
  await db.query("select * from grinder_practice_attempts where id=$1", [kept.attempt_id])
).rows[0];
assert.equal(keptAttempt.baseline.measurement_revision, "c".repeat(64));
assert.equal(keptAttempt.owner_id, RILEY);

const rileyLater = (
  await db.query(
    "insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts,claims,claims_verified,rhythm) values($1,'TEST DATA Riley later sitting','private','Codex',1,$2,'elapsed',now(),4,2,2,'[1,2,1]'::jsonb) returning id",
    [RILEY, "d".repeat(64)],
  )
).rows[0].id;
await db.query(
  "select grinder_review_attempt($1,$2,true,'keep','TEST DATA I ran the named check on my own baseline. Not the author counts.')",
  [kept.attempt_id, rileyLater],
);
const rileyReview = (
  await db.query("select * from grinder_practice_attempts where id=$1", [kept.attempt_id])
).rows[0];
assert.equal(rileyReview.decision, "keep");
assert.equal(rileyReview.outcome.measurement_revision, "d".repeat(64));
assert.notEqual(rileyReview.outcome.measurement_revision, reviewed.outcome.measurement_revision);

await as(CASEY);
await db.query("update runs set visibility='private' where id=$1", [caseyRun]);
await as(RILEY);
assert.equal((await db.query("select * from grinder_run_moments where id=$1", [moment])).rows.length, 0);
assert.equal(
  (await db.query("select * from grinder_practice_versions where id=$1", [kept.practice_id])).rows.length,
  1,
);
assert.equal(
  (await db.query("select * from grinder_practice_attempts where id=$1", [kept.attempt_id])).rows.length,
  1,
);
const provenance = (
  await db.query("select * from grinder_adopted_moments where practice_id=$1", [kept.practice_id])
).rows[0];
assert.equal(provenance.source_run, caseyRun);
await as(CASEY);
assert.equal(
  (await db.query("select * from grinder_adopted_moments where practice_id=$1", [kept.practice_id]))
    .rows.length,
  0,
);
await anonymous();
assert.equal((await db.query("select * from grinder_run_moments where id=$1", [moment])).rows.length, 0);

const receipt = {
  fixture: true,
  label: "TEST DATA · disposable PGlite · not live users",
  casey_practice: practice,
  casey_attempt: attempt,
  casey_decision: reviewed.decision,
  riley_practice: kept.practice_id,
  riley_attempt: kept.attempt_id,
  riley_decision: rileyReview.decision,
  riley_baseline: "c".repeat(64),
  source_revoked: true,
  riley_owned_work_survived: true,
};
await writeFile("/tmp/grinder-persisted-journey.json", JSON.stringify(receipt, null, 2));
await db.close();
console.log("Persisted two-builder journey passed:", JSON.stringify(receipt));
