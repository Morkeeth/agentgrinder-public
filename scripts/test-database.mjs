// Runs the actual migration and RLS in PostgreSQL/WASM. Authentication is a test GUC;
// profile/run seed rows are explicit fixtures, not claimed live users.
import { readFile } from "node:fs/promises";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
process.on("uncaughtException", (error) => {
  console.error(error.name === "AssertionError" ? error.stack : error.message);
  process.exit(1);
});
if (Number(process.versions.node.split(".")[0]) < 20) {
  console.error("Database checks require Node 20 or newer.");
  process.exit(1);
}
const { PGlite } = await import("@electric-sql/pglite");
const db = new PGlite();
const userA = "10000000-0000-0000-0000-000000000001",
  userB = "10000000-0000-0000-0000-000000000002",
  userC = "10000000-0000-0000-0000-000000000003";
const runA = "20000000-0000-0000-0000-000000000001";
await db.exec(`create role anon; create role authenticated;
alter default privileges grant all on tables to anon,authenticated;
alter default privileges grant execute on functions to anon,authenticated;
create schema auth;
create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
grant usage on schema auth to anon,authenticated;
`);
await db.exec(await readFile(new URL('../tests/fixtures/hosted-base.sql',import.meta.url),'utf8'));
await db.exec(`grant select,insert,update,delete on profiles,runs,acks to anon,authenticated;
insert into profiles(id,auth_uid) values('${userA}','${userA}'),('${userB}','${userB}'),('${userC}','${userC}');
insert into runs(title,id,profile_id,visibility) values('Fixture run','${runA}','${userA}','public');`);
// Exercise the deploy transaction on the base schema before individual retries can mask ordering defects.
await db.exec(execFileSync("python3", [new URL("./prepare-migration.py", import.meta.url).pathname], {encoding:"utf8"}));
// Check fresh creation BEFORE replaying the blanket permission migration: replay can
// hide direct grants inherited from Supabase's default function privileges.
const authenticatedRpcs = [
  'grinder_practice_from_moment(uuid,text,text)',
  'grinder_adopt_moment(uuid,uuid,text,text)',
  'grinder_review_attempt(uuid,uuid,boolean,text,text)',
  'grinder_review_cycle(uuid,uuid,text,text)',
];
async function checkNewRpcPrivileges() {
  for (const signature of authenticatedRpcs) {
    const result = (await db.query("select has_function_privilege('anon',$1,'EXECUTE') anonymous, has_function_privilege('authenticated',$1,'EXECUTE') signed_in", [signature])).rows[0];
    assert.equal(result.anonymous,false,`${signature}: anon must not inherit execution`);
    assert.equal(result.signed_in,true,`${signature}: authenticated API must remain available`);
  }
  for (const role of ['anon','authenticated']) {
    assert.equal((await db.query("select has_function_privilege($1,'grinder_sittings_comparable(jsonb,jsonb)','EXECUTE') allowed", [role])).rows[0].allowed,false,`${role}: internal comparison helper is not a client API`);
  }
}
await checkNewRpcPrivileges();
for (const file of (
  await readFile(new URL("./migration-order.txt", import.meta.url), "utf8")
)
  .trim()
  .split("\n")) {
  const sql = await readFile(
    new URL("../supabase/migrations/" + file, import.meta.url),
    "utf8",
  );
  await db.exec(sql);
  await db.exec(sql); // migrations must tolerate retries
}
await db.exec(execFileSync("python3", [new URL("./prepare-migration.py", import.meta.url).pathname], {encoding:"utf8"}));
await checkNewRpcPrivileges();
async function as(id) {
  await db.exec("reset role");
  await db.query("select set_config('request.jwt.claim.sub',$1,false)", [id]);
  await db.exec("set role authenticated");
}
async function anonymous() {
 await db.exec("reset role");
 await db.query("select set_config('request.jwt.claim.sub','',false)");
 await db.exec("set role anon");
}
async function denied(sql, params = []) {
  let caught = false;
  try {
    await db.query(sql, params);
  } catch (error) {
    assert(["P0001", "42501", "23514", "23505"].includes(error.code), "Unexpected error instead of a policy denial: " + error.code + " " + error.message);
    caught = true;
  }
  assert(caught, "Expected server denial: " + sql);
}
await denied(`select grinder_check_agent_payload('{"claims_verified":1}')`);
await denied(`select grinder_check_agent_payload('{"claims_verified":0,"claims":null}')`);
await db.query(`select grinder_check_agent_payload('{"claims_verified":0,"claims":0}')`);

await as(userA);
await denied("update runs set claims_verified=1,claims=null where id=$1",[runA]);
await db.query(
  "update runs set caption=$2,output_url=$3 where id=$1",
  [runA, "TEST DATA: added the public run-card fields.", "https://example.test/test-output"],
);
await denied("update runs set caption=$2 where id=$1", [runA, ""]);
await denied("update runs set output_url=$2 where id=$1", [runA, "javascript:alert(1)"]);
const crew = (await db.query("select grinder_create_crew('Test crew') id"))
  .rows[0].id;
assert.equal(
  (await db.query("select * from grinder_memberships")).rows.length,
  1,
);
const token = (await db.query("select grinder_invite($1) token", [crew]))
  .rows[0].token;
await as(userB);
assert.equal(
  (await db.query("update runs set caption='TEST DATA: not mine' where id=$1 returning id", [runA]))
    .rows.length,
  0,
);
assert.equal((await db.query("select * from grinder_crews")).rows.length, 0);
await denied("select grinder_invite($1)", [crew]);
await db.query("select grinder_join_crew($1)", [token]);
await as(userA);
await denied("delete from profiles where id=$1",[userA]);
await as(userB);
assert.equal((await db.query("select * from grinder_crews")).rows.length, 1);
await db.query(
  "insert into grinder_follows(follower_id,followed_id) values($1,$2)",
  [userB, userA],
);
await denied(
  "insert into grinder_follows(follower_id,followed_id) values($1,$2)",
  [userA, userC],
);
await denied(
  "insert into grinder_follows(follower_id,followed_id) values($1,$1)",
  [userB],
);
const reply = (
  await db.query(
    "insert into grinder_replies(run_id,author_id,body) values($1,$2,$3) returning id",
    [runA, userB, "What check did you run?"],
  )
).rows[0].id;
await as(userA);
assert.equal(
  (await db.query("select * from grinder_notifications")).rows.length,
  2,
);
assert.equal(
  (
    await db.query(
      "update grinder_replies set body='changed' where id=$1 returning id",
      [reply],
    )
  ).rows.length,
  0,
);
await as(userC);
await denied("select grinder_join_crew($1)", [token]);
assert.equal(
  (await db.query("select * from grinder_notifications")).rows.length,
  0,
);
await db.exec("reset role");
await db.query("update runs set visibility='private' where id=$1", [runA]);
await as(userB);
assert.equal((await db.query("select * from grinder_replies")).rows.length, 0);
await denied(
  "insert into grinder_replies(run_id,author_id,body) values($1,$2,$3)",
  [runA, userB, "Private leak"],
);
await as(userA);
await db.query("select grinder_share_with_crew($1,$2)", [runA, crew]);
await as(userB);
assert.equal((await db.query("select * from runs")).rows.length, 1);
await as(userC);
assert.equal((await db.query("select * from runs")).rows.length, 0);
await as(userA);
await db.query("select grinder_remove_member($1,$2)", [crew, userB]);
await as(userB);
assert.equal((await db.query("select * from grinder_crews")).rows.length, 0);
assert.equal((await db.query("select * from runs")).rows.length, 0);
await as(userA);
const actor = (
  await db.query(
    "insert into grinder_agents(owner_id,name) values($1,'Test agent') returning id",
    [userA],
  )
).rows[0].id;
const issued = (
  await db.query(
    "select grinder_issue_agent_token($1,array['draft','publish'],array['private'],now()+interval '1 day') as value",
    [actor],
  )
).rows[0].value;
await as(userB);
await denied(
  "select grinder_issue_agent_token($1,array['draft'],array['private'],now()+interval '1 day')",
  [actor],
);
const req = "30000000-0000-0000-0000-000000000001";
await anonymous();
const drafted = (
  await db.query("select grinder_agent_action($1,'draft',$2,$3) value", [
    issued.token,
    { turns_typed: 2, title: "Fixture draft" },
    req,
  ])
).rows[0].value;
const repeated = (
  await db.query("select grinder_agent_action($1,'draft',$2,$3) value", [
    issued.token,
    { turns_typed: 2, title: "Fixture draft" },
    req,
  ])
).rows[0].value;
assert.equal(drafted.id, repeated.id);
await denied("select grinder_agent_action($1,'draft',$2,$3)", [
  issued.token,
  { turns_typed: 3 },
  req,
]);
await denied("select grinder_agent_action($1,'publish',$2,$3)", [
  issued.token,
  { visibility: "public" },
  "30000000-0000-0000-0000-000000000002",
]);
await denied("select grinder_agent_action($1,'draft',$2,$3)", [
  issued.token,
  { turns_typed: -1 },
  "30000000-0000-0000-0000-000000000003",
]);
await denied("select grinder_agent_action($1,'reply',$2,$3)", [
  issued.token,
  { run_id: runA, body: "Not permitted" },
  "30000000-0000-0000-0000-000000000004",
]);
await as(userA);
assert.equal(
  (await db.query("select * from grinder_agent_drafts")).rows.length,
  1,
);
await denied("select token_hash from grinder_agent_tokens");
await db.query("update grinder_agent_tokens set revoked=true where id=$1", [
  issued.id,
]);
await denied("update grinder_agent_tokens set revoked=false where id=$1", [
  issued.id,
]);
await denied(
  "insert into grinder_rig_revisions(owner_id,label,manifest) values($1,'Unsafe',$2)",
  [userA, { api_key: "fixture" }],
);
await anonymous();
await denied("select grinder_agent_action($1,'draft',$2,$3)", [
  issued.token,
  { turns_typed: 2, title: "Fixture draft" },
  req,
]);
await as(userA);
const rigA = (
  await db.query(
    "insert into grinder_rig_revisions(owner_id,label,manifest,visibility) values($1,'Fixture rig',$2,'public') returning id",
    [userA, { harnesses: ["fixture"] }],
  )
).rows[0].id;
await as(userC);
const hostCrew=(await db.query("select grinder_create_crew('Host fixture crew') id")).rows[0].id;
const challenge = (
  await db.query(
    "select grinder_create_challenge($1,'Fixture OCTACON',$2,now()+interval '1 day','octacon',8) id",
    [
      hostCrew,
      { task: "Complete the fixture task", checks: ["Run the declared check"] },
    ],
  )
).rows[0].id;
await denied("select grinder_enter_challenge($1,$2,$3)",[challenge,hostCrew,rigA]);
await as(userA);
const entryA = (
  await db.query("select grinder_enter_challenge($1,$2,$3) id", [
    challenge,
    crew,
    rigA,
  ])
).rows[0].id;
const duplicateCrew=(await db.query("select grinder_create_crew('Duplicate fixture crew') id")).rows[0].id;
await denied("select grinder_enter_challenge($1,$2,$3)",[challenge,duplicateCrew,rigA]);
await denied("update grinder_challenges set contract='{}' where id=$1", [
  challenge,
]);
await as(userB);
const crewB = (
  await db.query("select grinder_create_crew('Second fixture crew') id")
).rows[0].id;
const rigB = (
  await db.query(
    "insert into grinder_rig_revisions(owner_id,label,manifest,visibility) values($1,'Second fixture rig',$2,'public') returning id",
    [userB, { harnesses: ["fixture"] }],
  )
).rows[0].id;
await db.query("select grinder_enter_challenge($1,$2,$3)", [
  challenge,
  crewB,
  rigB,
]);
await denied("select grinder_submit_challenge($1,$2)", [entryA, runA]);
await db.exec("reset role");
await db.query(
  "update runs set visibility='public',measurement_revision=$2,claims=10,claims_verified=1,started_at=now(),rig_revision=$3 where id=$1",
  [runA, "a".repeat(64), rigA],
);
await as(userA);
const submission = (
  await db.query("select grinder_submit_challenge($1,$2) id", [entryA, runA])
).rows[0].id;
await denied("select grinder_review_submission($1,'accepted','Self review')",[submission]);
await as(userC);
await denied("delete from profiles where id=$1",[userC]);
const rejected = (
  await db.query(
    "select grinder_review_submission($1,'rejected','Declared check was missing') id",
    [submission],
  )
).rows[0].id;
await denied("select grinder_appeal_review($1,'Not the entrant')",[rejected]);
await as(userA);
await db.query(
  "select grinder_appeal_review($1,'The check result is attached to the submitted revision')",
  [rejected],
);
await as(userC);
await db.query(
  "select grinder_review_submission($1,'accepted','Reviewed the submitted result',$2)",
  [submission, rejected],
);
assert.equal(
  (await db.query("select * from grinder_challenge_reviews")).rows.length,
  2,
);
await db.exec("reset role");
await db.query("update runs set claims_verified=9 where id=$1", [runA]);
assert.equal(
  (
    await db.query(
      "select snapshot from grinder_challenge_submissions where id=$1",
      [submission],
    )
  ).rows[0].snapshot.claims_verified,
  1,
);
await db.query(
  "update grinder_challenges set closes_at=now()-interval '1 minute' where id=$1",
  [challenge],
);
await as(userA);
await denied("select grinder_submit_challenge($1,$2)", [entryA, runA]);
await as(userA);
await denied(
  "select grinder_create_challenge($1,'Invalid',$2,now()+interval '1 day')",
  [crew, { task: "Missing checks" }],
);
await denied(
  "select grinder_review_submission($1,'accepted','Duplicate without supersedes')",
  [submission],
);
const practice = (
  await db.query(
    "insert into grinder_practice_versions(owner_id,title,task_context,instruction,expected,visibility) values($1,'Check before claiming','Small fixes','Run the named check','Evidence for the changed behavior','public') returning id",
    [userA],
  )
).rows[0].id;
await as(userB);
await denied("select grinder_start_attempt($1,$2,true)", [practice, runA]);
await db.exec("reset role");
const runB = "20000000-0000-0000-0000-000000000002";
await db.query(
  "insert into runs(title,id,profile_id,visibility,harness,measurement_revision,started_at) values('Fixture run',$1,$2,'private','fixture',$3,now()-interval '1 day')",
  [runB, userB, "b".repeat(64)],
);
await as(userB);
const attempt = (
  await db.query("select grinder_start_attempt($1,$2,true) id", [
    practice,
    runB,
  ])
).rows[0].id;
await denied(
  "select grinder_review_attempt($1,null,false,'keep','Not tried')",
  [attempt],
);
await db.query(
  "select grinder_review_attempt($1,null,false,'incomparable','Not tried')",
  [attempt],
);
await denied(
  "select grinder_review_attempt($1,null,false,'incomparable','Rewrite')",
  [attempt],
);
await as(userA);
assert.equal(
  (await db.query("select * from grinder_practice_attempts")).rows[0].decision,
  "incomparable",
);
await db.query(
  "insert into grinder_blocks(blocker_id,blocked_id) values($1,$2)",
  [userA, userB],
);
await as(userC);
assert.equal((await db.query("select grinder_blocked($1,$2) blocked",[userA,userB])).rows[0].blocked,false);
await denied("select grinder_blocked_pair($1,$2)",[userA,userB]);
await anonymous();
await denied("select grinder_blocked($1,$2)",[userA,userB]);
await as(userB);
assert.equal(
  (await db.query("select id from runs where id=$1", [runA])).rows.length,
  0,
);
assert.equal((await db.query("select grinder_can_read_practice($1) allowed",[practice])).rows[0].allowed,false);
await denied("select grinder_start_attempt($1,$2)",[practice,runB]);
await denied(
  "insert into grinder_follows(follower_id,followed_id) values($1,$2)",
  [userB, userA],
);
await denied(
  "insert into grinder_replies(run_id,author_id,body) values($1,$2,$3)",
  [runA, userB, "Blocked reply"],
);
await as(userA);
await db.query(
  "delete from grinder_blocks where blocker_id=$1 and blocked_id=$2",
  [userA, userB],
);
await as(userB);
assert.equal(
  (await db.query("select id from runs where id=$1", [runA])).rows.length,
  1,
);
await as(userA);
await db.query("update grinder_agents set visibility='public' where id=$1", [
  actor,
]);
const answering = (
  await db.query(
    "select grinder_issue_agent_token($1,array['publish','reply'],array['public'],now()+interval '1 day') value",
    [actor],
  )
).rows[0].value;
await anonymous();
const agentRun = (
  await db.query(
    "select grinder_agent_action($1,'publish',$2,gen_random_uuid()) value",
    [
      answering.token,
      {
        title: "Public fixture grind",
        visibility: "public",
        turns_typed: 2,
        measurement_revision: "c".repeat(64),
      },
    ],
  )
).rows[0].value.id;
await as(userB);
const question = (
  await db.query("select grinder_ask_agent($1,$2,'Which check passed?') id", [
    actor,
    agentRun,
  ])
).rows[0].id;
await anonymous();
const queue = (
  await db.query("select grinder_agent_questions($1) value", [answering.token])
).rows[0].value;
assert.equal(queue[0].question_id, question);
assert.equal(queue[0].evidence.turns_typed, 2);
assert(!JSON.stringify(queue).includes("token"));
await db.query("select grinder_agent_action($1,'reply',$2,gen_random_uuid())", [
  answering.token,
  {
    run_id: agentRun,
    question_id: question,
    body: "Only the reported counts are available. No named test output is included.",
  },
]);
assert.deepEqual(
  (
    await db.query("select grinder_agent_questions($1) value", [
      answering.token,
    ])
  ).rows[0].value,
  [],
);
await denied("select grinder_agent_action($1,'reply',$2,gen_random_uuid())", [
  answering.token,
  { run_id: agentRun, question_id: question, body: "Duplicate response" },
]);
await as(userA);
const experiment = (
  await db.query(
    "select grinder_create_experiment($1,$2,'Fixture experiment','Observe the next two cycles') id",
    [crew, practice],
  )
).rows[0].id;
const cycle = (
  await db.query("select grinder_start_cycle($1,$2) id", [experiment, runA])
).rows[0].id;
await db.query(
  "select grinder_review_cycle($1,null,'incomparable','No outcome yet')",
  [cycle],
);
const nextCycle = (
  await db.query("select grinder_start_cycle($1,$2) id", [experiment, runA])
).rows[0].id;
assert.notEqual(cycle, nextCycle);
await denied("select grinder_review_cycle($1,null,'adopt','No outcome')", [
  nextCycle,
]);
await as(userC);
assert.equal(
  (await db.query("select * from grinder_experiments")).rows.length,
  0,
);
await denied("select grinder_start_cycle($1,$2)", [experiment, runA]);
await db.exec("reset role");
const deleting = "10000000-0000-0000-0000-000000000004";
await db.query("insert into profiles(id,auth_uid) values($1,$1)", [deleting]);
await as(deleting);
const deletingCrew = (
  await db.query("select grinder_create_crew('Delete fixture') id")
).rows[0].id;
await db.query(
  "insert into grinder_rig_revisions(owner_id,label,manifest) values($1,'Delete rig','{}')",
  [deleting],
);
await db.exec("reset role");
await db.query("insert into runs(title,profile_id,visibility) values('Fixture run',$1,'private')", [
  deleting,
]);
await as(deleting);
await db.query("insert into acks(from_profile,to_profile,run_id,reason) values($1,$2,$3,'shipped')",[deleting,userA,runA]);
await db.query("delete from profiles where id=$1", [deleting]);
await db.exec("reset role");
assert.equal(
  (await db.query("select * from grinder_crews where id=$1", [deletingCrew]))
    .rows.length,
  0,
);
assert.equal(
  (await db.query("select * from runs where profile_id=$1", [deleting])).rows
    .length,
  0,
);
await as(userA);
await db.query("select grinder_feature_run($1)", [runA]);
assert.equal(
  (await db.query("select featured_run_id from profiles where id=$1", [userA]))
    .rows[0].featured_run_id,
  runA,
);
await as(userB);
await denied("select grinder_feature_run($1)", [runA]);
await as(userB);
await denied("insert into runs(title,profile_id,visibility) values('Fixture run',$1,$2)",[userA,'public']);
assert.equal((await db.query('delete from runs where id=$1 returning id',[runA])).rows.length,0);
await denied('insert into acks(from_profile,to_profile,run_id,reason) values($1,$2,$3,$4)',[userC,userA,runA,'shipped']);
await db.query('insert into acks(from_profile,to_profile,run_id,reason) values($1,$2,$3,$4)',[userB,userA,runA,'shipped']);
await as(userA);
assert.equal((await db.query("select * from grinder_notifications where kind='ack' and run_id=$1",[runA])).rows.length,1);
// Deleting a source must preserve another person's question and frozen results.
await db.query("delete from grinder_replies where question_id=$1",[question]);
await as(userB);
assert.equal((await db.query("select reply_id from grinder_agent_questions where id=$1",[question])).rows[0].reply_id,null);
await as(userA);
await db.query("delete from runs where id=$1",[runA]);
assert.equal((await db.query("select run_id from grinder_challenge_submissions where id=$1",[submission])).rows[0].run_id,null);
assert.equal((await db.query("select * from grinder_challenge_reviews where submission_id=$1",[submission])).rows.length,2);
await as(userB);
assert.equal((await db.query("select decision from grinder_practice_attempts where id=$1",[attempt])).rows[0].decision,"incomparable");
// Ghost rows cannot expose profile identity through direct table access.
await as(userA);
const ghost=(await db.query("insert into runs(profile_id,title,visibility) values($1,'Legacy ghost fixture','anonymous') returning id",[userA])).rows[0].id;
assert.equal((await db.query('select id from runs where id=$1',[ghost])).rows.length,1);
await anonymous();
assert.equal((await db.query('select id from runs where id=$1',[ghost])).rows.length,0);
await as(userB);
assert.equal((await db.query('select id from runs where id=$1',[ghost])).rows.length,0);
// Link collections and ACKs cannot reveal private activity IDs.
await as(userA);
const secretLink=(await db.query("insert into runs(profile_id,title,visibility) values($1,'Link fixture','link') returning id",[userA])).rows[0].id;
await anonymous();
assert.equal((await db.query("select id from runs where visibility='link'")).rows.length,0);
assert.equal((await db.query('select grinder_can_read_run($1) yes',[secretLink])).rows[0].yes,false);
await db.query("select set_config('request.headers',$1,false)",[JSON.stringify({'x-grinder-run-id':secretLink})]);
assert.equal((await db.query('select id from runs where id=$1',[secretLink])).rows.length,1);
assert.equal((await db.query('select grinder_can_read_run($1) yes',[secretLink])).rows[0].yes,true);
await db.query("select set_config('request.headers','{}',false)");
await db.exec('reset role');
const privateAckRun=(await db.query("insert into runs(profile_id,title,visibility) values($1,'Private ACK fixture','public') returning id",[userC])).rows[0].id;
const privateAck=(await db.query("insert into acks(run_id,from_profile,to_profile,reason) values($1,$2,$3,'shipped') returning id",[privateAckRun,userA,userC])).rows[0].id;
await db.query("update runs set visibility='private' where id=$1",[privateAckRun]);
await anonymous();
assert.equal((await db.query("select id from acks where id=$1",[privateAck])).rows.length,0);
await as(userC);
assert.equal((await db.query("select id from acks where id=$1",[privateAck])).rows.length,1);
// The per-owner limit survives issuing another token. Replays still work at the limit.
await as(userA);
const secondAccess=(await db.query("select grinder_issue_agent_token($1,array['publish'],array['public'],now()+interval '1 day') value",[actor])).rows[0].value;
for(let i=0;i<3;i++) await db.query("select grinder_issue_agent_token($1,array['publish'],array['public'],now()+interval '1 day')",[actor]);
await denied("select grinder_issue_agent_token($1,array['publish'],array['public'],now()+interval '1 day')",[actor]);
await db.exec('reset role');
const priorActions=Number((await db.query("select count(*) n from grinder_agent_requests r join grinder_agent_tokens t on t.id=r.token_id join grinder_agents a on a.id=t.agent_id where a.owner_id=$1 and r.created_at>now()-interval '1 hour'",[userA])).rows[0].n);
await anonymous();
let lastId;
const limitedPayload={title:'Rate-limit fixture',visibility:'public',turns_typed:1};
for(let i=priorActions;i<60;i++) {lastId=(await db.query('select gen_random_uuid() id')).rows[0].id;await db.query("select grinder_agent_action($1,'publish',$2,$3)",[answering.token,limitedPayload,lastId]);}
await denied("select grinder_agent_action($1,'publish',$2,gen_random_uuid())",[secondAccess.token,limitedPayload]);
await db.query("select grinder_agent_action($1,'publish',$2,$3)",[answering.token,limitedPayload,lastId]);
await denied('truncate grinder_challenges cascade');
await denied('truncate runs cascade');
await as(userA);
await denied("update grinder_agent_tokens set scopes=array['ack'] where id=$1",[secondAccess.id]);
await db.exec('reset role');
await db.exec('begin');
await db.exec(await readFile(new URL('./friend-preflight.sql',import.meta.url),'utf8'));
await db.exec('rollback');
// Returning-user product: compare frozen runs, choose a practice, then review a later session.
await db.exec('reset role');
const progressOwner='10000000-0000-0000-0000-000000000004';
const progressOther='10000000-0000-0000-0000-000000000005';
await db.query('insert into profiles(id,auth_uid) values($1,$1),($2,$2)',[progressOwner,progressOther]);
await as(progressOwner);
const earlierProgress=(await db.query("insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts,note) values($1,'Earlier fixture','private','Codex',1,$2,'elapsed',now()-interval '2 days',3,'PRIVATE NOTE EXCLUDED') returning id",[progressOwner,'e'.repeat(64)])).rows[0].id;
const laterProgress=(await db.query("insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts) values($1,'Later fixture','private','Codex',1,$2,'elapsed',now()-interval '1 day',4) returning id",[progressOwner,'f'.repeat(64)])).rows[0].id;
const progressRequest='80000000-0000-0000-0000-000000000001';
const savedProgress=(await db.query("select grinder_save_comparison($1,$2,'Same fixture task',true,$3) id",[earlierProgress,laterProgress,progressRequest])).rows[0].id;
const frozenProgress=(await db.query('select * from grinder_comparisons where id=$1',[savedProgress])).rows[0];
assert.deepEqual(frozenProgress.limitations,[]);
assert.equal(frozenProgress.before_run.turns_typed,3);
assert.equal(frozenProgress.after_run.turns_typed,4);
assert(!JSON.stringify(frozenProgress).includes('PRIVATE NOTE EXCLUDED'));
assert.equal((await db.query("select grinder_save_comparison($1,$2,'Same fixture task',true,$3) id",[earlierProgress,laterProgress,progressRequest])).rows[0].id,savedProgress);
await denied("select grinder_save_comparison($1,$2,'Changed retry',true,$3)",[earlierProgress,laterProgress,progressRequest]);
await denied("select grinder_save_comparison($1,$1,'Same run',true,gen_random_uuid())",[earlierProgress]);
await denied("update grinder_comparisons set task_context='rewrite' where id=$1",[savedProgress]);
await db.query('update runs set prompts=99 where id=$1',[laterProgress]);
const nextPractice=(await db.query("select grinder_practice_from_comparison($1,'Run the named check','A test result in the completion turn') value",[savedProgress])).rows[0].value;
const nextAttempt=(await db.query('select * from grinder_practice_attempts where id=$1',[nextPractice.attempt_id])).rows[0];
assert.equal(nextAttempt.baseline.turns_typed,4,'The next practice must keep the frozen comparison, not reread the edited run');
assert.equal(nextAttempt.visibility,'private');
assert.equal((await db.query("select grinder_practice_from_comparison($1,'Run the named check','A test result in the completion turn') value",[savedProgress])).rows[0].value.attempt_id,nextPractice.attempt_id);
await denied("select grinder_practice_from_comparison($1,'Different action','Different expectation')",[savedProgress]);
const unknownProgress=(await db.query("select grinder_save_comparison($1,$2,'Different tasks',false,gen_random_uuid()) id",[laterProgress,earlierProgress])).rows[0].id;
const limitations=(await db.query('select limitations from grinder_comparisons where id=$1',[unknownProgress])).rows[0].limitations;
assert(limitations.some(x=>x.includes('context'))&&limitations.some(x=>x.includes('later session')));
await as(progressOther);
assert.equal((await db.query('select id from grinder_comparisons where id=$1',[savedProgress])).rows.length,0);
await denied("select grinder_save_comparison($1,$2,'Not my runs',true,gen_random_uuid())",[earlierProgress,laterProgress]);
await denied("select grinder_practice_from_comparison($1,'Other user action','No')",[savedProgress]);
await anonymous();
await denied('select * from grinder_comparisons');
await denied("select grinder_save_comparison($1,$2,'Anonymous',true,gen_random_uuid())",[earlierProgress,laterProgress]);
await as(progressOwner);
const practiceOutcome=(await db.query("insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts) values($1,'Practice outcome fixture','private','Codex',1,$2,'elapsed',now(),2) returning id",[progressOwner,'1'.repeat(64)])).rows[0].id;
await db.query("select grinder_review_attempt($1,$2,true,'incomparable','Controlled fixture: named check was tried')",[nextPractice.attempt_id,practiceOutcome]);
assert.equal((await db.query('select decision from grinder_practice_attempts where id=$1',[nextPractice.attempt_id])).rows[0].decision,'incomparable');
await db.query('delete from runs where id in ($1,$2)',[earlierProgress,laterProgress]);
const retainedProgress=(await db.query('select * from grinder_comparisons where id=$1',[savedProgress])).rows[0];
assert.equal(retainedProgress.earlier_run,null);
assert.equal(retainedProgress.before_run.turns_typed,3);
assert.equal(retainedProgress.after_run.turns_typed,4);
// These legacy fixtures omit headline evidence, so reviews above remain incomparable.
// Authored moment -> exact visible evidence -> frozen private practice -> later review.
await as(progressOwner);
const momentRun=(await db.query("insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts) values($1,'TEST DATA moment grind','private','Codex',1,$2,'elapsed',now()-interval '2 days',3) returning id",[progressOwner,'a'.repeat(64)])).rows[0].id;
const momentFields=[momentRun,progressOwner,'a'.repeat(64),'TEST DATA failure then repair','A local import check passed','TEST DATA receipt/check-import','TEST DATA: 1 check passed','One local check; no deployment or adoption','Run the check before editing'];
const insertMoment='insert into grinder_run_moments(run_id,owner_id,measurement_revision,title,claim,evidence_ref,excerpt,limitation,next_action) values($1,$2,$3,$4,$5,$6,$7,$8,$9) returning id';
const moment=(await db.query(insertMoment,momentFields)).rows[0].id;
await denied('update grinder_run_moments set claim=$2 where id=$1',[moment,'rewritten']);
await denied(insertMoment,[momentRun,progressOwner,'b'.repeat(64),...momentFields.slice(3)]);
await anonymous();assert.equal((await db.query('select * from grinder_run_moments where id=$1',[moment])).rows.length,0);
await as(userB);assert.equal((await db.query('select * from grinder_run_moments where id=$1',[moment])).rows.length,0);
await denied("select grinder_practice_from_moment($1,'TEST DATA action','TEST DATA expectation')",[moment]);
await denied(insertMoment,[momentRun,userB,...momentFields.slice(2)]);
await as(progressOwner);await db.query("update runs set visibility='public' where id=$1",[momentRun]);
await anonymous();assert.equal((await db.query('select excerpt from grinder_run_moments where id=$1',[moment])).rows[0].excerpt,momentFields[6]);
await as(progressOwner);await db.query("update runs set visibility='private' where id=$1",[momentRun]);
await anonymous();assert.equal((await db.query('select * from grinder_run_moments where id=$1',[moment])).rows.length,0);
await as(progressOwner);
const momentPractice=(await db.query("select grinder_practice_from_moment($1,'TEST DATA run the check first','TEST DATA check precedes edit') result",[moment])).rows[0].result;
const retryMoment=(await db.query("select grinder_practice_from_moment($1,'TEST DATA run the check first','TEST DATA check precedes edit') result",[moment])).rows[0].result;
assert.deepEqual(retryMoment,momentPractice);
await denied("select grinder_practice_from_moment($1,'TEST DATA another action','TEST DATA check precedes edit')",[moment]);
assert.equal((await db.query('select baseline from grinder_practice_attempts where id=$1',[momentPractice.attempt_id])).rows[0].baseline.measurement_revision,'a'.repeat(64));
assert.equal((await db.query('select visibility from grinder_practice_versions where id=$1',[momentPractice.practice_id])).rows[0].visibility,'private');
const staleMoment=(await db.query(insertMoment,momentFields)).rows[0].id;
await db.query('update runs set measurement_revision=$2 where id=$1',[momentRun,'b'.repeat(64)]);
await denied("select grinder_practice_from_moment($1,'TEST DATA action','TEST DATA expectation')",[staleMoment]);
const momentLater=(await db.query("insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts) values($1,'TEST DATA later grind','private','Codex',1,$2,'elapsed',now(),2) returning id",[progressOwner,'c'.repeat(64)])).rows[0].id;
await db.query("select grinder_review_attempt($1,$2,true,'incomparable','TEST DATA local check was used; no causal inference')",[momentPractice.attempt_id,momentLater]);
assert.equal((await db.query('select decision from grinder_practice_attempts where id=$1',[momentPractice.attempt_id])).rows[0].decision,'incomparable');
await db.query('delete from grinder_run_moments where id=$1',[moment]);
assert.equal((await db.query('select * from runs where id=$1',[momentRun])).rows.length,1);
assert.equal((await db.query('select * from grinder_practice_attempts where id=$1',[momentPractice.attempt_id])).rows.length,1);
console.log('Moment checks passed: ownership, audience revocation, immutable excerpt, changed revision refusal, idempotent practice, frozen baseline, later review, no grind deletion.');

// A stranger who was not there: read a moment, keep its next practice, bring their OWN baseline.
await as(progressOwner);
const sharedRun=(await db.query("insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts) values($1,'TEST DATA published grind','private','Codex',1,$2,'elapsed',now()-interval '5 days',9) returning id",[progressOwner,'4'.repeat(64)])).rows[0].id;
const sharedFields=[sharedRun,progressOwner,'4'.repeat(64),'TEST DATA the check that changed the plan','A local import check passed','TEST DATA receipt/check-import','TEST DATA: 1 check passed','One local check; not deployment or adoption','Run the failing check before editing'];
const sharedMoment=(await db.query(insertMoment,sharedFields)).rows[0].id;
const secondMoment=(await db.query(insertMoment,sharedFields)).rows[0].id;
const thirdMoment=(await db.query(insertMoment,sharedFields)).rows[0].id;
const keepTitle='TEST DATA run the failing check before editing',keepExpected='TEST DATA the check runs before the first edit';
await as(userB);
const strangerBaseline=(await db.query("insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts) values($1,'TEST DATA stranger earlier grind','private','Codex',1,$2,'elapsed',now()-interval '3 days',5) returning id",[userB,'5'.repeat(64)])).rows[0].id;
// A private grind is not a shared technique: the stranger cannot read it and cannot keep it.
await denied('select grinder_adopt_moment($1,$2,$3,$4)',[sharedMoment,strangerBaseline,keepTitle,keepExpected]);
await as(progressOwner);await db.query("update runs set visibility='public' where id=$1",[sharedRun]);
await anonymous();await denied('select grinder_adopt_moment($1,$2,$3,$4)',[sharedMoment,strangerBaseline,keepTitle,keepExpected]);
await as(userB);
const kept=(await db.query('select grinder_adopt_moment($1,$2,$3,$4) result',[sharedMoment,strangerBaseline,keepTitle,keepExpected])).rows[0].result;
const keptPractice=(await db.query('select * from grinder_practice_versions where id=$1',[kept.practice_id])).rows[0];
assert.equal(keptPractice.owner_id,userB);
assert.equal(keptPractice.visibility,'private');
// the kept practice points at the STRANGER's own grind, never at the author's.
assert.equal(keptPractice.source_run,strangerBaseline);
assert.notEqual(keptPractice.source_run,sharedRun);
const keptAttempt=(await db.query('select * from grinder_practice_attempts where id=$1',[kept.attempt_id])).rows[0];
assert.equal(keptAttempt.owner_id,userB);
assert.equal(keptAttempt.baseline.measurement_revision,'5'.repeat(64));
assert.equal(keptAttempt.baseline.turns_typed,5);
const provenance=(await db.query('select * from grinder_adopted_moments where practice_id=$1',[kept.practice_id])).rows[0];
assert.equal(provenance.source_run,sharedRun);
assert.equal(provenance.source_measurement_revision,'4'.repeat(64));
assert.equal(provenance.source_measurement_stale,false);
// keeping is idempotent, and the same moment cannot quietly become a different practice.
assert.deepEqual((await db.query('select grinder_adopt_moment($1,$2,$3,$4) result',[sharedMoment,strangerBaseline,keepTitle,keepExpected])).rows[0].result,kept);
await denied('select grinder_adopt_moment($1,$2,$3,$4)',[sharedMoment,strangerBaseline,'TEST DATA a different action',keepExpected]);
// A retry with a different baseline must not report success for the original attempt.
const changedBaseline=(await db.query("insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts) values($1,'TEST DATA other chosen baseline','private','Codex',1,$2,'elapsed',now()-interval '4 days',6) returning id",[userB,'9'.repeat(64)])).rows[0].id;
await denied('select grinder_adopt_moment($1,$2,$3,$4)',[sharedMoment,changedBaseline,keepTitle,keepExpected]);
await denied('select grinder_adopt_moment($1,$2,$3,$4)',[sharedMoment,sharedRun,keepTitle,keepExpected]);
// the baseline must be the stranger's own measured grind, not the author's.
await denied('select grinder_adopt_moment($1,$2,$3,$4)',[secondMoment,sharedRun,keepTitle,keepExpected]);
// nothing was written to the author's grind.
assert.equal((await db.query('select count(*) n from grinder_run_moments where run_id=$1',[sharedRun])).rows[0].n,3);
await denied("insert into grinder_adopted_moments(practice_id,adopter_id,attempt_id,moment_id,source_run,source_measurement_revision,source_measurement_stale) values($1,$2,$3,$4,$5,$6,false)",[kept.practice_id,userB,kept.attempt_id,secondMoment,sharedRun,'4'.repeat(64)]);
// provenance is the adopter's own row: nobody else reads who kept what.
await as(userC);assert.equal((await db.query('select * from grinder_adopted_moments where practice_id=$1',[kept.practice_id])).rows.length,0);
await as(progressOwner);assert.equal((await db.query('select * from grinder_adopted_moments where practice_id=$1',[kept.practice_id])).rows.length,0);
// an older source measurement is recorded, not refused: the technique is still readable.
await db.query('update runs set measurement_revision=$2 where id=$1',[sharedRun,'6'.repeat(64)]);
await as(userC);
const otherBaseline=(await db.query("insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts) values($1,'TEST DATA third builder grind','private','Codex',1,$2,'elapsed',now()-interval '2 days',4) returning id",[userC,'7'.repeat(64)])).rows[0].id;
const keptStale=(await db.query('select grinder_adopt_moment($1,$2,$3,$4) result',[thirdMoment,otherBaseline,keepTitle,keepExpected])).rows[0].result;
assert.equal((await db.query('select source_measurement_stale from grinder_adopted_moments where practice_id=$1',[keptStale.practice_id])).rows[0].source_measurement_stale,true);
// the stranger returns with a later session of their own. Their own two runs, no cross-account numbers.
await as(userB);
const strangerLater=(await db.query("insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts) values($1,'TEST DATA stranger later grind','private','Codex',1,$2,'elapsed',now(),3) returning id",[userB,'8'.repeat(64)])).rows[0].id;
await db.query("select grinder_review_attempt($1,$2,true,'incomparable','TEST DATA tried the check first; one observation, no causal claim')",[kept.attempt_id,strangerLater]);
const reviewed=(await db.query('select * from grinder_practice_attempts where id=$1',[kept.attempt_id])).rows[0];
assert.equal(reviewed.decision,'incomparable');
assert.equal(reviewed.outcome.measurement_revision,'8'.repeat(64));
// the author narrows the audience afterwards: the source stops resolving, the stranger's own work survives.
await as(progressOwner);await db.query("update runs set visibility='private' where id=$1",[sharedRun]);
await as(userB);
assert.equal((await db.query('select * from grinder_run_moments where id=$1',[sharedMoment])).rows.length,0);
assert.equal((await db.query('select * from grinder_practice_versions where id=$1',[kept.practice_id])).rows.length,1);
assert.equal((await db.query('select * from grinder_practice_attempts where id=$1',[kept.attempt_id])).rows.length,1);
console.log('Stranger checks passed: private source refused, anonymous refused, own baseline enforced, author grind untouched, provenance private, stale source recorded, idempotent keep, later review, audience revocation survivable.');

await as(userA);
const coachRun = (
  await db.query(
    "insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts) values($1,'TEST DATA coach mode grind','private','Codex',1,$2,'elapsed',now(),2) returning id",
    [userA, "d".repeat(64)],
  )
).rows[0].id;
await db.query("update runs set coach_mode='local scripted Strands loop' where id=$1", [
  coachRun,
]);
assert.equal(
  (await db.query("select coach_mode from runs where id=$1", [coachRun])).rows[0]
    .coach_mode,
  "local scripted Strands loop",
);
await db.query("update runs set coach_mode=null where id=$1", [coachRun]);
assert.equal(
  (await db.query("select coach_mode from runs where id=$1", [coachRun])).rows[0]
    .coach_mode,
  null,
);
console.log("Coach mode column is nullable and writable by the owner.");

await as(userA);
const cmpBase = (
  await db.query(
    "insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts,claims,claims_verified) values($1,'TEST DATA comparable baseline','private','Codex',1,$2,'elapsed',now()-interval '2 days',4,4,2) returning id",
    [userA, "2".repeat(64)],
  )
).rows[0].id;
const cmpPractice = (
  await db.query(
    "insert into grinder_practice_versions(owner_id,title,task_context,instruction,expected,visibility,source_run,harness) values($1,'TEST DATA run the named check','Coach experiment on this grind','Run test_draft_renders in the same turn','check_claim returns verified','private',$2,'Codex') returning id",
    [userA, cmpBase],
  )
).rows[0].id;
const cmpAttempt = (
  await db.query("select grinder_start_attempt($1,$2,false) id", [cmpPractice, cmpBase])
).rows[0].id;
const cursorLater = (
  await db.query(
    "insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts,claims,claims_verified) values($1,'TEST DATA cursor later','private','Cursor',1,$2,'elapsed',now(),3,4,3) returning id",
    [userA, "3".repeat(64)],
  )
).rows[0].id;
await denied(
  "select grinder_review_attempt($1,$2,true,'keep','TEST DATA different harness')",
  [cmpAttempt, cursorLater],
);
const basisLater = (
  await db.query(
    "insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts,claims,claims_verified) values($1,'TEST DATA basis later','private','Codex',1,$2,'typed-turn order',now(),3,4,3) returning id",
    [userA, "e".repeat(64)],
  )
).rows[0].id;
await denied(
  "select grinder_review_attempt($1,$2,true,'keep','TEST DATA different time basis')",
  [cmpAttempt, basisLater],
);
await db.query(
  "select grinder_review_attempt($1,$2,true,'incomparable','TEST DATA harness differed; not a keep')",
  [cmpAttempt, cursorLater],
);
assert.equal(
  (await db.query("select decision from grinder_practice_attempts where id=$1", [cmpAttempt]))
    .rows[0].decision,
  "incomparable",
);
const cmpAttempt2 = (
  await db.query("select grinder_start_attempt($1,$2,false) id", [cmpPractice, cmpBase])
).rows[0].id;
const sameLater = (
  await db.query(
    "insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts,claims,claims_verified) values($1,'TEST DATA same harness later','private','Codex',1,$2,'elapsed',now(),3,4,3) returning id",
    [userA, "f".repeat(64)],
  )
).rows[0].id;
await db.query(
  "select grinder_review_attempt($1,$2,true,'keep','TEST DATA same measurements; one observation')",
  [cmpAttempt2, sameLater],
);
assert.equal(
  (await db.query("select decision from grinder_practice_attempts where id=$1", [cmpAttempt2]))
    .rows[0].decision,
  "keep",
);
console.log(
  "Comparable sittings: keep denied across harness and trace_basis even with claim counts; same measurements still keep.",
);

// A matching harness and clock alone cannot turn absent measurements into evidence.
const metricAttempt = (await db.query("select grinder_start_attempt($1,$2,false) id", [cmpPractice, cmpBase])).rows[0].id;
const unknownLater = (await db.query(
  "insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts,claims,claims_verified,artifacts_produced) values($1,'TEST DATA unknown later','private','Codex',1,$2,'elapsed',now(),3,null,null,null) returning id",
  [userA, "9".repeat(64)],
)).rows[0].id;
await denied("select grinder_review_attempt($1,$2,true,'keep','Unknown is not comparable')", [metricAttempt, unknownLater]);
await db.query("select grinder_review_attempt($1,$2,true,'incomparable','Unknown stays unknown')", [metricAttempt, unknownLater]);
await db.exec('reset role'); // Exercise the internal pure helper as migration owner.
const measured = {harness:'Codex',trace_basis:'elapsed',turns_typed:4,claims_verified:0};
for (const missing of [{...measured,claims_verified:null}, {...measured,turns_typed:0}, {...measured,turns_typed:null}]) {
  assert.equal((await db.query('select grinder_sittings_comparable($1::jsonb,$2::jsonb) ok', [JSON.stringify(missing),JSON.stringify(missing)])).rows[0].ok,false);
}
for (const valid of [measured,{...measured,claims_verified:null,artifacts_produced:0}]) {
  assert.equal((await db.query('select grinder_sittings_comparable($1::jsonb,$2::jsonb) ok', [JSON.stringify(valid),JSON.stringify(valid)])).rows[0].ok,true);
}
console.log('Missing headline evidence denied; measured zero and artifact fallback accepted.');

await db.close();
console.log(
  "Database checks passed: social permissions; agent capabilities; two-crew Challenge; locked Contract; frozen submission; rejection, appeal and revised review; late-submission denial.",
);
