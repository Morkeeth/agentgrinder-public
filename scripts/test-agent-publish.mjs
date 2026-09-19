// Agent publish path for STRIVE, exercised in disposable PostgreSQL (PGlite). TEST DATA only.
// Never pointed at production. Loads the production function bodies first to prove the new
// checks fail on them, then applies supabase/strava/006_agent_publish_ridge.sql.
//
// Root acceptance list covered here: field allowlist, token hash, expiry, revocation, default
// private, explicit scopes, request size limit, per-token abuse limit, security definer with a
// fixed search path, execute grants, audience escalation, and per-owner idempotency that never
// overwrites another record or widens an audience on retry.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";

const { PGlite } = await import("@electric-sql/pglite");
const db = new PGlite();
const OWNER_A = "a1000000-0000-0000-0000-000000000001";
const OWNER_B = "b1000000-0000-0000-0000-000000000002";
const sha = (s) => createHash("sha256").update(s, "utf8").digest("hex");

await db.exec(`
create role anon; create role authenticated;
create schema strava;
create table strava.profiles(id uuid primary key, auth_uid uuid);
create table strava.grinder_agents(id uuid primary key default gen_random_uuid(), owner_id uuid references strava.profiles(id),
  name text, rig_revision uuid, visibility text not null default 'private', created_at timestamptz not null default now());
create table strava.grinder_agent_tokens(id uuid primary key default gen_random_uuid(), agent_id uuid references strava.grinder_agents(id),
  token_hash text unique, scopes text[], audiences text[], expires_at timestamptz, revoked boolean default false,
  window_started timestamptz default now(), window_actions integer default 0, created_at timestamptz default now());
create table strava.grinder_agent_requests(token_id uuid not null, request_id uuid not null, fingerprint text not null,
  response jsonb not null, created_at timestamptz not null default now(), primary key(token_id, request_id));
create table strava.grinder_agent_drafts(id uuid primary key default gen_random_uuid(), owner_id uuid, agent_id uuid, payload jsonb, created_at timestamptz default now());
create table strava.grinder_replies(id uuid primary key default gen_random_uuid(), run_id uuid, author_id uuid, parent_id uuid, body text,
  evidence_ref text, created_at timestamptz default now(), edited_at timestamptz, source_actor_id uuid, agent_name text, question_id uuid);
create table strava.acks(id uuid primary key default gen_random_uuid(), from_profile uuid, to_profile uuid, run_id uuid, reason text, same_owner boolean);
-- runs: the production column set and constraints this path touches, read 2026-09-19.
create table strava.runs(id uuid primary key default gen_random_uuid(), profile_id uuid not null, title text not null, project text,
  harness text, started_at timestamptz, duration_s double precision, prompts integer, tool_calls integer, files_touched integer,
  commits integer, rhythm jsonb, is_ship boolean not null default false, visibility text not null default 'private',
  created_at timestamptz not null default now(), note text, route jsonb, claims integer, claims_verified integer,
  artifacts_produced integer, schema_version integer, measurement_revision text, baseline_revision text, trace_basis text,
  source_actor_id uuid, agent_name text, caption text, model text, wall_time_s integer, ridge jsonb, worker_bins jsonb,
  commit_bins jsonb, ridge_basis text, ridge_wall_seconds double precision, ridge_tool_calls integer, shell_calls integer,
  constraint runs_visibility_check check (visibility = any(array['private','close_friends','link','public','crew','anonymous'])),
  constraint runs_ridge_basis_check check (ridge_basis is null or ridge_basis = any(array['wall-time','call-index','turn-order'])),
  constraint runs_ridge_shape_check check (ridge is null or (jsonb_typeof(ridge)='array' and jsonb_array_length(ridge) between 40 and 60
    and worker_bins is not null and jsonb_typeof(worker_bins)='array' and jsonb_array_length(worker_bins)=jsonb_array_length(ridge)
    and (commit_bins is null or jsonb_typeof(commit_bins)='array'))));
create unique index runs_profile_measurement_revision_unique on strava.runs(profile_id, measurement_revision) where measurement_revision is not null;
insert into strava.profiles(id, auth_uid) values('${OWNER_A}','${OWNER_A}'),('${OWNER_B}','${OWNER_B}');
`);

async function agent(owner, { visibility = "private" } = {}) {
  const r = await db.query("insert into strava.grinder_agents(owner_id,name,visibility) values($1,$2,$3) returning id", [owner, "Grok Bot", visibility]);
  return r.rows[0].id;
}
async function token(agentId, { scopes = ["publish"], audiences = ["private"], expires = "now() + interval '30 days'", revoked = false } = {}) {
  // Same construction as production grinder_issue_agent_token: ag_ plus two random UUIDs.
  const secret = "ag_" + randomUUID() + randomUUID();
  await db.query(
    `insert into strava.grinder_agent_tokens(agent_id,token_hash,scopes,audiences,expires_at,revoked) values($1,$2,$3,$4,${expires},$5)`,
    [agentId, sha(secret), scopes, audiences, revoked],
  );
  return secret;
}
const act = async (secret, action, payload, requestId = randomUUID()) =>
  (await db.query("select strava.grinder_agent_action($1,$2,$3,$4) as v", [secret, action, payload, requestId])).rows[0].v;
async function refused(promise, pattern) {
  await assert.rejects(promise, (e) => pattern.test(e.message), `expected refusal matching ${pattern}`);
}

const BINS = 50;
const RIDGE = Array.from({ length: BINS }, (_, i) => [1, 2, 5, 13, 0, 7][Math.floor(i / 9) % 6]);
const WORKERS = Array.from({ length: BINS }, () => 1);
const REV = (n) => sha("measurement-" + n);
const strivePayload = (rev, extra = {}) => ({
  title: "Sunday build", harness: "Grok Bot", turns_typed: 6, tool_calls: 28, schema_version: 1,
  measurement_revision: rev, ridge: RIDGE, worker_bins: WORKERS, ridge_basis: "turn-order", ridge_tool_calls: 28, ...extra,
});

// ---------- RED: production functions refuse the STRIVE shape ----------
await db.exec(await readFile(new URL("../tests/fixtures/agent-action-prod-2026-09-19.sql", import.meta.url), "utf8"));
{
  const secret = await token(await agent(OWNER_A));
  await refused(act(secret, "publish", strivePayload(REV("red"))), /Unsupported public field: (ridge|worker_bins|ridge_basis|ridge_tool_calls)/);
  // Retry of the same measurement with a fresh request ID hits the unique index raw.
  await act(secret, "publish", { title: "old shape", measurement_revision: REV("dup") });
  await refused(act(secret, "publish", { title: "old shape", measurement_revision: REV("dup") }), /duplicate key|unique/i);
  console.log("RED on production functions: ridge refused, retry collides raw");
}

// ---------- apply 006 ----------
await db.exec(await readFile(new URL("../supabase/strava/006_agent_publish_ridge.sql", import.meta.url), "utf8"));

// Grants and definer settings.
{
  const g = (role, fn) => db.query(`select has_function_privilege($1, $2, 'execute') as ok`, [role, fn]).then((r) => r.rows[0].ok);
  const ACTION = "strava.grinder_agent_action(text,text,jsonb,uuid)";
  const CHECK = "strava.grinder_check_agent_payload(jsonb)";
  assert.equal(await g("anon", ACTION), true);
  assert.equal(await g("authenticated", ACTION), true);
  assert.equal(await g("anon", CHECK), false, "payload check must not be callable directly");
  const meta = (await db.query(
    "select prosecdef, proconfig from pg_proc where oid = $1::regprocedure", [ACTION])).rows[0];
  assert.equal(meta.prosecdef, true);
  assert.ok(meta.proconfig.some((c) => c.startsWith("search_path=") && c.includes("strava")), "fixed search_path");
  console.log("grants and security definer settings hold");
}

const agentA = await agent(OWNER_A, { visibility: "public" });
const pubA = await token(agentA, { scopes: ["publish", "reply"], audiences: ["private", "public"] });

// GREEN: the STRIVE shape persists, default audience private.
{
  const out = await act(pubA, "publish", strivePayload(REV(1)));
  const run = (await db.query("select * from strava.runs where id=$1", [out.id])).rows[0];
  assert.equal(run.visibility, "private", "default audience is private");
  assert.equal(run.ridge_basis, "turn-order");
  assert.deepEqual(run.ridge, RIDGE);
  assert.equal(run.ridge_tool_calls, 28);
  assert.equal(run.profile_id, OWNER_A);
  assert.equal(out.existing, undefined);
  console.log("publish persists ridge, turn-order basis and counts, private by default");
}

// Idempotency: same request ID returns the stored response, a different payload is refused.
{
  const rid = randomUUID();
  const a = await act(pubA, "publish", strivePayload(REV(2)), rid);
  const b = await act(pubA, "publish", strivePayload(REV(2)), rid);
  assert.deepEqual(a, b);
  await refused(act(pubA, "publish", strivePayload(REV(2), { title: "changed" }), rid), /cannot be reused/);
  console.log("request ID idempotency holds and cannot be reused for a different payload");
}

// Per-owner measurement idempotency: no duplicate, no overwrite, no audience widening.
{
  const first = await act(pubA, "publish", strivePayload(REV(3), { title: "original" }));
  const retry = await act(pubA, "publish", strivePayload(REV(3), { title: "overwrite attempt", visibility: "public" }));
  assert.equal(retry.id, first.id);
  assert.equal(retry.existing, true);
  assert.equal(retry.visibility, "private", "a retry must not widen the audience");
  const rows = (await db.query("select title, visibility from strava.runs where profile_id=$1 and measurement_revision=$2", [OWNER_A, REV(3)])).rows;
  assert.equal(rows.length, 1);
  assert.deepEqual(rows[0], { title: "original", visibility: "private" });
  console.log("same measurement returns the existing run untouched, audience not widened");
}

// Never matches another owner's record.
{
  const agentB = await agent(OWNER_B);
  const tokB = await token(agentB);
  const outB = await act(tokB, "publish", strivePayload(REV(3)));
  const aRow = (await db.query("select id from strava.runs where profile_id=$1 and measurement_revision=$2", [OWNER_A, REV(3)])).rows[0];
  assert.notEqual(outB.id, aRow.id);
  assert.equal(outB.existing, undefined);
  console.log("another owner with the same measurement gets their own run");
}

// Audience escalation, expiry, revocation, scopes.
{
  const privOnly = await token(agentA, { audiences: ["private"] });
  await refused(act(privOnly, "publish", strivePayload(REV(4), { visibility: "public" })), /audience is outside/);
  const agentPrivate = await agent(OWNER_B, { visibility: "private" });
  const wantsPublic = await token(agentPrivate, { audiences: ["private", "public"] });
  await refused(act(wantsPublic, "publish", strivePayload(REV(5), { visibility: "public" })), /agent profile public/);
  const expired = await token(agentA, { expires: "now() - interval '1 minute'" });
  await refused(act(expired, "publish", strivePayload(REV(6))), /Agent access is unavailable/);
  const revoked = await token(agentA, { revoked: true });
  await refused(act(revoked, "publish", strivePayload(REV(7))), /Agent access is unavailable/);
  await refused(act("ag_not-a-real-token", "publish", strivePayload(REV(8))), /Agent access is unavailable/);
  const publishOnly = await token(agentA, { scopes: ["publish"] });
  await refused(act(publishOnly, "reply", { run_id: randomUUID(), body: "hi" }), /outside the granted scope/);
  console.log("escalation, expired, revoked, unknown token and missing scope all refused");
}

// Allowlist and validation.
{
  await refused(act(pubA, "publish", { title: "x", transcript: "raw text" }), /Unsupported public field: transcript/);
  await refused(act(pubA, "publish", strivePayload(REV(9), { ridge: RIDGE.slice(0, 30), worker_bins: WORKERS.slice(0, 30) })), /40 to 60 bins/);
  await refused(act(pubA, "publish", strivePayload(REV(10), { worker_bins: WORKERS.slice(0, 10) })), /same length as the ridge/);
  await refused(act(pubA, "publish", strivePayload(REV(11), { ridge_basis: "vibes" })), /ridge_basis must be/);
  await refused(act(pubA, "publish", strivePayload(REV(12), { shell_calls: -1 })), /non-negative whole numbers/);
  await refused(act(pubA, "publish", { title: "x", note: "y".repeat(70000) }), /under 64 KiB/);
  // worker_bins and commit_bins content, not only their type.
  await refused(act(pubA, "publish", strivePayload(REV(14), { worker_bins: WORKERS.map((w, i) => (i === 3 ? -2 : w)) })), /worker_bins must be non-negative/);
  await refused(act(pubA, "publish", strivePayload(REV(15), { worker_bins: WORKERS.map((w, i) => (i === 3 ? 1.5 : w)) })), /worker_bins must be non-negative/);
  await refused(act(pubA, "publish", strivePayload(REV(16), { commit_bins: [3, 50] })), /ridge bin indexes from 0 to 49/);
  await refused(act(pubA, "publish", strivePayload(REV(17), { commit_bins: [-1] })), /ridge bin indexes/);
  await refused(act(pubA, "publish", strivePayload(REV(18), { commit_bins: [2.5] })), /ridge bin indexes/);
  await refused(act(pubA, "publish", { title: "x", commit_bins: [1] }), /need a ridge/);
  // Regression rows from the independent review of 006 (backend-review/results.txt, 2026-09-19).
  // Each of these was accepted by the database while the browser renderer dropped or mislabelled it.
  await refused(act(pubA, "publish", strivePayload(REV(20), { ridge: RIDGE.map((v, i) => (i === 0 ? 0.5 : v)) })), /Ridge bins must be non-negative whole/);
  await refused(act(pubA, "publish", strivePayload(REV(21), { worker_bins: WORKERS.map((w, i) => (i === 0 ? 1e20 : w)) })), /worker_bins must be non-negative whole/);
  await refused(act(pubA, "publish", strivePayload(REV(22), { ridge_basis: null })), /ridge_basis must be/);
  const noBasis = strivePayload(REV(23)); delete noBasis.ridge_basis;
  await refused(act(pubA, "publish", noBasis), /ridge_basis must be/);
  await refused(act(pubA, "publish", strivePayload(REV(24), { caption: { transcript: "raw source text" } })), /caption must be text/);
  await refused(act(pubA, "publish", strivePayload(REV(25), { model: { secret: "nested raw" } })), /model must be text/);
  await refused(act(pubA, "publish", strivePayload(REV(26), { title: ["raw"] })), /title must be text/);
  await refused(act(pubA, "publish", { title: "x", ridge_basis: "turn-order" }), /need a ridge/);
  // The largest safe integer is still accepted, so the bound is exact.
  const edge = await act(pubA, "publish", strivePayload(REV(27), { ridge: RIDGE.map((v, i) => (i === 0 ? 9007199254740991 : v)) }));
  assert.ok(edge.id);
  const ok = await act(pubA, "publish", strivePayload(REV(19), { commit_bins: [3, 17, 42] }));
  assert.deepEqual((await db.query("select commit_bins from strava.runs where id=$1", [ok.id])).rows[0].commit_bins, [3, 17, 42]);
  console.log("allowlist, ridge shape, worker and commit bin contents, basis, counts and 64 KiB limit enforced");
}

// Per-token abuse limit.
{
  const limited = await token(agentA);
  await db.query("update strava.grinder_agent_tokens set window_actions=60, window_started=now() where token_hash=$1", [sha(limited)]);
  await refused(act(limited, "publish", strivePayload(REV(13))), /Hourly action limit/);
  console.log("per-token hourly limit enforced");
}

console.log("\nAGENT PUBLISH: all checks passed");
