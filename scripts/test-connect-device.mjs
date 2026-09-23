// STRIVE Connect: connect once, sync forever. The done-when tests for S0 (funnel), S1 (RFC 8628
// device pairing) and S2 (sliding device token), run against real SQL in a disposable in-process
// Postgres. Synthetic actors only; never pointed at a hosted database.
//
//   node --test scripts/test-connect-device.mjs
//   node --test --test-name-pattern "slow_down" scripts/test-connect-device.mjs
import { PGlite } from "@electric-sql/pglite";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { upload } from "../server/agent-upload.mjs";
import { DEVICE_GRANT, deviceStart, devicePoll } from "../server/connect-device.mjs";

const ROOT = new URL("../", import.meta.url);
const CANARY = "CANARY-NEVER-UPLOAD-8f21c7";
const FAKE_HOME = "/Users/canary-person";
const USER_CODE_ALPHABET = "BCDFGHJKLMNPQRSTVWXZ";
const python = (script, args = []) =>
  execFileSync("python3", [new URL(script, ROOT).pathname, ...args], { encoding: "utf8" });
const file = (path) => readFileSync(new URL(path, ROOT), "utf8");

// Roles and the auth shim the hosted project provides, then the whole strava bootstrap.
async function bootPostgres(sql) {
  const db = new PGlite();
  await db.exec(`create role anon; create role authenticated;
alter default privileges grant all on tables to anon,authenticated;
alter default privileges grant execute on functions to anon,authenticated;
create schema auth;
create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
grant usage on schema auth to anon,authenticated;`);
  await db.exec(sql);
  await db.exec("reset role");
  return db;
}

let db;
let actors = 0;

before(async () => {
  db = await bootPostgres(python("scripts/prepare-strava-database.py"));
});
after(async () => {
  await db?.close();
});

const owner = () => db.exec("reset role");
async function as(profile) {
  await db.exec("reset role");
  await db.query("select set_config('request.jwt.claim.sub',$1,false)", [profile]);
  await db.exec("set role authenticated");
}
async function anon() {
  await db.exec("reset role");
  await db.query("select set_config('request.jwt.claim.sub','',false)");
  await db.exec("set role anon");
}
async function rpc(name, args = []) {
  const holes = args.map((_, index) => `$${index + 1}`).join(",");
  const { rows } = await db.query(`select strava.${name}(${holes}) as out`, args);
  return rows[0].out;
}
async function newActor(label) {
  actors += 1;
  const id = `11000000-0000-0000-0000-${String(actors).padStart(12, "0")}`;
  await owner();
  await db.query("insert into strava.profiles(id,auth_uid,name) values($1,$1,$2)", [id, `TEST DATA ${label}`]);
  return id;
}

// One pairing, started by a device that holds no account.
async function startPairing({ harness = "cursor", device = "Studio laptop", scopes = ["draft", "publish"] } = {}) {
  await anon();
  const issued = await rpc("connect_device_start", [harness, device, scopes]);
  await owner();
  const { rows } = await db.query(
    "select id from strava.connect_pairings where device_code_hash=strava.connect_code_hash($1)",
    [issued.device_code],
  );
  return { ...issued, pairing: rows[0].id };
}
async function poll(deviceCode) {
  await anon();
  return rpc("connect_device_poll", [deviceCode]);
}
async function decide(profile, userCode, approve) {
  await as(profile);
  return rpc("connect_pairing_decide", [userCode, approve]);
}
async function funnel(pairing) {
  await owner();
  const { rows } = await db.query("select event from strava.connect_funnel_events where pairing_id=$1 order by id", [pairing]);
  return rows.map((row) => row.event);
}
async function activeTokens(profile) {
  await owner();
  const { rows } = await db.query(
    `select t.id,t.label,t.expires_at,t.last_seen_at,t.revoked from strava.grinder_agent_tokens t
     join strava.grinder_agents a on a.id=t.agent_id where a.owner_id=$1`,
    [profile],
  );
  return rows;
}
// Waiting out the poll interval, without waiting.
const waitInterval = (pairing) =>
  db.query("update strava.connect_pairings set last_polled_at=last_polled_at-interval '30 seconds' where id=$1", [pairing]);
const shiftPairing = (pairing, seconds) =>
  db.query(
    `update strava.connect_pairings set created_at=created_at-make_interval(secs=>$2),
       expires_at=expires_at-make_interval(secs=>$2),
       last_polled_at=last_polled_at-make_interval(secs=>$2) where id=$1`,
    [pairing, seconds],
  );
// A day passing for a credential: its own clock and the request log that rate-limits it.
async function shiftDays(token, days) {
  await owner();
  await db.query(
    `update strava.grinder_agent_tokens set created_at=created_at-make_interval(days=>$2),
       expires_at=expires_at-make_interval(days=>$2), window_started=window_started-make_interval(days=>$2),
       last_seen_at=last_seen_at-make_interval(days=>$2) where id=$1`,
    [token, days],
  );
  await db.query(
    "update strava.grinder_agent_requests set created_at=created_at-make_interval(days=>$2) where token_id=$1",
    [token, days],
  );
}

// The deployed endpoints, with the public anon key replaced by this disposable Postgres. The
// status codes below are the ones a device really receives from /api/connect/* and
// /api/agent/runs.
const CALLS = {
  grinder_agent_action: (sent) => [
    "select strava.grinder_agent_action($1::text,$2::text,$3::jsonb,$4::uuid) as out",
    [sent.token, sent.action, JSON.stringify(sent.payload), sent.request_id],
  ],
  connect_device_start: (sent) => [
    "select strava.connect_device_start($1::text,$2::text,$3::text[]) as out",
    [sent.p_harness, sent.p_device_name, sent.p_scopes],
  ],
  connect_device_poll: (sent) => ["select strava.connect_device_poll($1::text) as out", [sent.p_device_code]],
};
function postgrestFetch() {
  return async (url, init) => {
    const call = CALLS[String(url).split("/rpc/")[1]];
    assert.ok(call, `unexpected endpoint ${url}`);
    const [sql, params] = call(JSON.parse(init.body));
    await anon();
    try {
      const { rows } = await db.query(sql, params);
      return { ok: true, status: 200, json: async () => rows[0].out };
    } catch (error) {
      return { ok: false, status: 400, json: async () => ({ message: error.message }) };
    }
  };
}
const uploadRun = (token, body = { turns_typed: 2, tool_calls: 5, visibility: "private" }) =>
  upload(
    { method: "POST", headers: { authorization: `Bearer ${token}` }, body },
    { SB_URL: "http://127.0.0.1:54321", SB_KEY: "local-development-only" },
    postgrestFetch(),
  );

// A complete pairing: device asks, human approves, device claims one credential.
async function pairDevice(options = {}) {
  const profile = options.profile || (await newActor(options.label || "device owner"));
  const started = await startPairing(options);
  await decide(profile, started.user_code, true);
  const claimed = await poll(started.device_code);
  assert.equal(typeof claimed.access_token, "string", "the approved device receives a credential");
  await owner();
  const { rows } = await db.query("select token_id from strava.connect_pairings where id=$1", [started.pairing]);
  return { ...started, profile, token: claimed.access_token, token_id: rows[0].token_id, claimed };
}

// ---------------------------------------------------------------- S0 funnel events

test("S0: a scripted pairing writes five funnel rows, in order, and no content", async () => {
  const paired = await pairDevice({ label: "funnel five" });
  const response = await uploadRun(paired.token);
  assert.equal(response.status, 200, JSON.stringify(response.body));
  assert.deepEqual(await funnel(paired.pairing), [
    "connect_started",
    "code_issued",
    "code_approved",
    "token_claimed",
    "first_run_received",
  ]);
  // A second run does not re-record the first one.
  await uploadRun(paired.token, { turns_typed: 3, visibility: "private" });
  assert.equal((await funnel(paired.pairing)).length, 5);
  // The funnel cannot carry content because it has nowhere to put any.
  await owner();
  const { rows } = await db.query(
    `select attname from pg_attribute where attrelid='strava.connect_funnel_events'::regclass
       and attnum>0 and not attisdropped order by attnum`,
  );
  assert.deepEqual(
    rows.map((row) => row.attname),
    ["id", "pairing_id", "event", "created_at"],
  );
});

test("S0: a pairing abandoned before Approve writes exactly three rows and issues no token", async () => {
  const profile = await newActor("abandoned");
  const started = await startPairing({ device: "Kitchen table mini" });
  assert.deepEqual(await funnel(started.pairing), ["connect_started", "code_issued"]);
  await owner();
  await shiftPairing(started.pairing, 901);
  await as(profile);
  assert.equal(await rpc("connect_sweep_expired"), 1);
  assert.deepEqual(await funnel(started.pairing), ["connect_started", "code_issued", "code_expired"]);
  assert.deepEqual(await activeTokens(profile), []);
  await owner();
  const { rows } = await db.query("select status,token_id from strava.connect_pairings where id=$1", [started.pairing]);
  assert.equal(rows[0].status, "expired");
  assert.equal(rows[0].token_id, null);
  // Still three rows after the device gives up and polls one last time.
  assert.deepEqual(await poll(started.device_code), { error: "expired_token" });
  assert.equal((await funnel(started.pairing)).length, 3);
});

// ---------------------------------------------------------------- S1 device pairing

test("S1: the device authorization response is RFC 8628 shaped", async () => {
  const started = await startPairing({ harness: "codex", device: "Codex box" });
  assert.equal(started.expires_in, 900);
  assert.equal(started.interval, 5);
  assert.equal(started.user_code.length, 8);
  assert.match(started.user_code, new RegExp(`^[${USER_CODE_ALPHABET}]{8}$`));
  assert.match(started.device_code, /^dc_[0-9a-f-]{72}$/);
  // Neither secret is stored in the clear.
  await owner();
  const { rows } = await db.query("select * from strava.connect_pairings where id=$1", [started.pairing]);
  const stored = JSON.stringify(rows[0]);
  assert.ok(!stored.includes(started.device_code), "the device code is stored as a hash");
  assert.ok(!stored.includes(started.user_code), "the user code is stored as a hash");
  assert.equal(rows[0].device_name, "Codex box");
});

test("S1: poll state authorization_pending while nobody has decided", async () => {
  const started = await startPairing();
  assert.deepEqual(await poll(started.device_code), { error: "authorization_pending" });
});

test("S1: poll state slow_down when the device polls faster than the interval", async () => {
  const started = await startPairing();
  assert.deepEqual(await poll(started.device_code), { error: "authorization_pending" });
  assert.deepEqual(await poll(started.device_code), { error: "slow_down", interval: 5 });
  assert.deepEqual(await poll(started.device_code), { error: "slow_down", interval: 5 });
  // A refused poll never moves the clock, so waiting out the interval still works.
  await owner();
  await waitInterval(started.pairing);
  assert.deepEqual(await poll(started.device_code), { error: "authorization_pending" });
});

test("S1: poll state access_denied, and a denied code never yields a token", async () => {
  const profile = await newActor("denier");
  const started = await startPairing();
  assert.deepEqual(await decide(profile, started.user_code, false), {
    status: "denied",
    device_name: "Studio laptop",
    harness: "cursor",
  });
  assert.deepEqual(await poll(started.device_code), { error: "access_denied" });
  await owner();
  await waitInterval(started.pairing);
  assert.deepEqual(await poll(started.device_code), { error: "access_denied" });
  assert.deepEqual(await activeTokens(profile), []);
  // Denied is final: the same human cannot follow it with an approval.
  await assert.rejects(decide(profile, started.user_code, true), /already been used/);
  assert.deepEqual(await activeTokens(profile), []);
  assert.deepEqual(await funnel(started.pairing), ["connect_started", "code_issued", "code_denied"]);
});

test("S1: poll state expired_token once 900 seconds have passed", async () => {
  const profile = await newActor("late");
  const started = await startPairing();
  await owner();
  await shiftPairing(started.pairing, 899);
  assert.deepEqual(await poll(started.device_code), { error: "authorization_pending" });
  await owner();
  await shiftPairing(started.pairing, 10);
  assert.deepEqual(await poll(started.device_code), { error: "expired_token" });
  await assert.rejects(decide(profile, started.user_code, true), /expired/);
  assert.deepEqual(await activeTokens(profile), []);
});

test("S1: the credential is issued once; a replayed device code is invalid_grant", async () => {
  const paired = await pairDevice({ label: "claim once" });
  await owner();
  await waitInterval(paired.pairing);
  assert.deepEqual(await poll(paired.device_code), { error: "invalid_grant" });
  assert.equal((await activeTokens(paired.profile)).length, 1);
  assert.deepEqual(await poll("dc_not-a-code-we-hold"), { error: "invalid_grant" });
});

test("S1: one code cannot be approved twice", async () => {
  const profile = await newActor("double approver");
  const other = await newActor("second human");
  const started = await startPairing();
  await decide(profile, started.user_code, true);
  await assert.rejects(decide(profile, started.user_code, true), /already been used/);
  await assert.rejects(decide(other, started.user_code, true), /already been used/);
  assert.deepEqual(await funnel(started.pairing), ["connect_started", "code_issued", "code_approved"]);
  const claimed = await poll(started.device_code);
  assert.equal(typeof claimed.access_token, "string");
  // Approved, claimed, and still one credential for one human.
  assert.equal((await activeTokens(profile)).length, 1);
  assert.deepEqual(await activeTokens(other), []);
  await assert.rejects(decide(other, started.user_code, true), /already been used/);
});

test("S1: the approve page reads the harness, the device name and the scopes", async () => {
  const profile = await newActor("approver");
  const started = await startPairing({ harness: "grokbot", device: "Bot runner" });
  await as(profile);
  const view = await rpc("connect_pairing_view", [started.user_code]);
  assert.equal(view.harness, "grokbot");
  assert.equal(view.device_name, "Bot runner");
  assert.deepEqual(view.scopes, ["draft", "publish"]);
  assert.deepEqual(view.audiences, ["private"]);
  assert.equal(view.status, "pending");
  assert.ok(view.expires_in > 0 && view.expires_in <= 900);
  // Lower case from a phone keyboard still finds the pairing; a wrong code is refused.
  assert.equal((await rpc("connect_pairing_view", [started.user_code.toLowerCase()])).status, "pending");
  await assert.rejects(rpc("connect_pairing_view", ["BBBBBBBB"]), /not one of ours/);
  // A device cannot read or decide its own pairing: both are granted to authenticated only.
  await anon();
  await assert.rejects(rpc("connect_pairing_view", [started.user_code]), /permission denied/);
  await assert.rejects(rpc("connect_pairing_decide", [started.user_code, true]), /permission denied/);
  // Signed in with no STRIVE profile yet is asked to sign in, not shown the device.
  await as("11000000-0000-0000-0000-0000000000ff");
  await assert.rejects(rpc("connect_pairing_view", [started.user_code]), /Sign in to approve a device/);
  await assert.rejects(rpc("connect_pairing_decide", [started.user_code, true]), /Sign in to approve a device/);
});

test("S1: a device name is a name, never a file path", async () => {
  await anon();
  await assert.rejects(rpc("connect_device_start", ["cursor", "/Users/someone/laptop", ["draft"]]), /no file path/);
  await assert.rejects(rpc("connect_device_start", ["cursor", "~/laptop", ["draft"]]), /no file path/);
  await assert.rejects(rpc("connect_device_start", ["cursor", "", ["draft"]]), /1 to 40 characters/);
  await assert.rejects(rpc("connect_device_start", ["notepad", "Laptop", ["draft"]]), /harness/);
  await assert.rejects(rpc("connect_device_start", ["cursor", "Laptop", ["reply"]]), /draft and publish only/);
});

// ---------------------------------------------------------------- S2 token lifetime

test("S2: a device token unused for 91 days returns 401", async () => {
  const paired = await pairDevice({ label: "gone quiet" });
  assert.equal((await uploadRun(paired.token)).status, 200);
  await shiftDays(paired.token_id, 91);
  const response = await uploadRun(paired.token);
  assert.equal(response.status, 401);
  assert.match(response.body.error, /Agent access is unavailable/);
});

test("S2: a device token used daily is still valid on day 120", async () => {
  const paired = await pairDevice({ label: "daily driver" });
  for (let day = 1; day <= 120; day += 1) {
    await shiftDays(paired.token_id, 1);
    const response = await uploadRun(paired.token, { turns_typed: day, visibility: "private" });
    assert.equal(response.status, 200, `day ${day}: ${JSON.stringify(response.body)}`);
  }
  await owner();
  const { rows } = await db.query(
    "select expires_at>now() as live, expires_at-now() as remaining from strava.grinder_agent_tokens where id=$1",
    [paired.token_id],
  );
  assert.equal(rows[0].live, true, "daily use keeps the credential alive past its first 90 days");
});

test("S2: revoke makes the next upload 401", async () => {
  const paired = await pairDevice({ label: "revoked" });
  assert.equal((await uploadRun(paired.token)).status, 200);
  await as(paired.profile);
  assert.equal(await rpc("agent_token_revoke", [paired.token_id]), true);
  const response = await uploadRun(paired.token);
  assert.equal(response.status, 401);
  assert.match(response.body.error, /Agent access is unavailable/);
});

test("S2: Connections lists each device with when it last synced, and goes stale after seven days", async () => {
  const paired = await pairDevice({ label: "connections", device: "Studio laptop", harness: "cursor" });
  await as(paired.profile);
  let [listed] = await rpc("agent_token_list");
  assert.equal(listed.device_name, "Studio laptop");
  assert.equal(listed.harness, "cursor");
  assert.equal(listed.paired, true);
  assert.equal(listed.last_seen_at, null, "a device that has never uploaded has not synced");
  assert.equal(listed.stale, false, "a new device is waiting for its first run, not stale");
  assert.equal((await uploadRun(paired.token)).status, 200);
  await as(paired.profile);
  [listed] = await rpc("agent_token_list");
  assert.ok(listed.last_seen_at, "last synced is recorded from the upload itself");
  assert.equal(listed.stale, false);
  await shiftDays(paired.token_id, 8);
  await as(paired.profile);
  [listed] = await rpc("agent_token_list");
  assert.equal(listed.stale, true, "seven days without a run turns the row amber");
  assert.equal(listed.revoked, false);
  // Browser and database agree on the rule, so the amber row is not a client-side opinion.
  const status = createRequire(import.meta.url)("../site/connect-status.js");
  assert.equal(status.isStale(listed), true);
  await as(paired.profile);
  assert.equal(await rpc("agent_token_revoke", [paired.token_id]), true);
  [listed] = await rpc("agent_token_list");
  assert.equal(listed.stale, false, "a revoked device is finished, not stale");
  assert.equal(status.isStale(listed), false);
});

test("S2: an Advanced Agents token keeps the fixed expiry its owner chose", async () => {
  const profile = await newActor("advanced");
  await as(profile);
  const { rows: agent } = await db.query(
    "insert into strava.grinder_agents(owner_id,name,visibility) values($1,'Bench','private') returning id",
    [profile],
  );
  const issued = await rpc("grinder_issue_agent_token", [agent[0].id, ["publish"], ["private"], new Date(Date.now() + 3 * 864e5)]);
  assert.equal((await uploadRun(issued.token)).status, 200);
  await owner();
  const { rows } = await db.query(
    "select expires_at<now()+interval '4 days' as unchanged, last_seen_at is not null as seen from strava.grinder_agent_tokens where id=$1",
    [issued.id],
  );
  assert.equal(rows[0].unchanged, true, "only a labelled Connect device slides");
  assert.equal(rows[0].seen, true, "every credential still records when it was last used");
});

// ---------------------------------------------------------------- the two endpoints, end to end

test("S1: a device pairs through /api/connect/device and /api/connect/token", async () => {
  const profile = await newActor("endpoint");
  const config = { SB_URL: "http://127.0.0.1:54321", SB_KEY: "local-development-only", ORIGIN: "http://localhost:8000" };
  const request = (body) => ({ method: "POST", headers: {}, body });
  const started = await deviceStart(request({ harness: "cursor", device_name: "Studio laptop" }), config, postgrestFetch());
  assert.equal(started.status, 200);
  assert.equal(started.body.verification_uri, "http://localhost:8000/?pair");
  assert.equal(started.body.verification_uri_complete, "http://localhost:8000/?pair=" + started.body.user_code);
  assert.equal(started.body.expires_in, 900);
  assert.equal(started.body.interval, 5);

  const pending = await devicePoll(request({ device_code: started.body.device_code, grant_type: DEVICE_GRANT }), config, postgrestFetch());
  assert.equal(pending.status, 400);
  assert.equal(pending.body.error, "authorization_pending");
  const fast = await devicePoll(request({ device_code: started.body.device_code }), config, postgrestFetch());
  assert.equal(fast.body.error, "slow_down");
  assert.equal(fast.body.interval, 5);

  await decide(profile, started.body.user_code, true);
  await owner();
  const { rows } = await db.query("select id from strava.connect_pairings where device_code_hash=strava.connect_code_hash($1)", [
    started.body.device_code,
  ]);
  await waitInterval(rows[0].id);
  const claimed = await devicePoll(request({ device_code: started.body.device_code }), config, postgrestFetch());
  assert.equal(claimed.status, 200);
  assert.equal(claimed.body.token_type, "bearer");
  assert.equal(claimed.body.scope, "draft publish");
  assert.equal(claimed.body.expires_in, 7776000);
  assert.equal((await uploadRun(claimed.body.access_token)).status, 200);

  // The credential is not handed out twice, and neither endpoint answers a GET.
  await owner();
  await waitInterval(rows[0].id);
  const replay = await devicePoll(request({ device_code: started.body.device_code }), config, postgrestFetch());
  assert.equal(replay.body.error, "invalid_grant");
  assert.equal((await deviceStart({ method: "GET", headers: {}, body: {} }, config, postgrestFetch())).status, 405);
  assert.equal((await devicePoll({ method: "GET", headers: {}, body: {} }, config, postgrestFetch())).status, 405);
});

// ---------------------------------------------------------------- privacy

test("privacy: a canary string and a fake home path in a transcript never reach storage", async () => {
  const transcript = file("tests/fixtures/connect_canary_session.jsonl");
  assert.ok(transcript.includes(CANARY) && transcript.includes(FAKE_HOME), "the fixture must carry both");
  const payload = JSON.parse(python("tests/fixtures/connect_canary_payload.py", ["tests/fixtures/connect_canary_session.jsonl"]));
  assert.ok(payload.tool_calls > 0, "the upload still carries the counts it measured");
  const paired = await pairDevice({ label: "canary" });
  const response = await uploadRun(paired.token, payload);
  assert.equal(response.status, 200, JSON.stringify(response.body));
  await owner();
  const { rows: tables } = await db.query(
    "select relname from pg_class where relnamespace='strava'::regnamespace and relkind='r' order by relname",
  );
  for (const { relname } of tables) {
    const { rows } = await db.query(`select coalesce(jsonb_agg(t),'[]'::jsonb) as stored from strava."${relname}" t`);
    const stored = JSON.stringify(rows[0].stored);
    assert.ok(!stored.includes(CANARY), `${relname} stored the canary`);
    assert.ok(!stored.includes(FAKE_HOME), `${relname} stored the fake home path`);
  }
  // The allowlist is the reason, so prove it refuses transcript-shaped extras outright.
  const leaky = await uploadRun(paired.token, { turns_typed: 1, transcript: CANARY, visibility: "private" });
  assert.equal(leaky.status, 400);
  assert.match(leaky.body.error, /Unsupported public field: transcript/);
});

// ---------------------------------------------------------------- migration

test("migration 011 is reversible", async () => {
  // Build the schema as it stood at 010, then apply 011 and its down script.
  const full = python("scripts/prepare-strava-database.py");
  const marker = "-- strava/011_connect_device.sql";
  assert.ok(full.includes(marker), "the bootstrap must ship 011");
  const before = await bootPostgres(full.slice(0, full.indexOf(marker)) + "\ncommit;\n");
  const shape = async () =>
    (
      await before.query(`select jsonb_build_object(
        'tables',(select jsonb_agg(c.relname order by c.relname) from pg_class c where c.relnamespace='strava'::regnamespace and c.relkind='r'),
        'columns',(select jsonb_agg(c.relname||'.'||a.attname order by c.relname,a.attname) from pg_attribute a join pg_class c on c.oid=a.attrelid where c.relnamespace='strava'::regnamespace and a.attnum>0 and not a.attisdropped),
        'functions',(select jsonb_agg(p.proname||':'||md5(p.prosrc)||':'||coalesce(array_to_string(p.proconfig,','),'') order by p.proname,p.oid) from pg_proc p where p.pronamespace='strava'::regnamespace),
        'triggers',(select jsonb_agg(t.tgname order by t.tgname) from pg_trigger t join pg_class c on c.oid=t.tgrelid where c.relnamespace='strava'::regnamespace and not t.tgisinternal),
        'indexes',(select jsonb_agg(ci.relname order by ci.relname) from pg_index i join pg_class ci on ci.oid=i.indexrelid join pg_class c on c.oid=i.indrelid where c.relnamespace='strava'::regnamespace),
        'policies',(select jsonb_agg(pol.polname order by pol.polname) from pg_policy pol join pg_class c on c.oid=pol.polrelid where c.relnamespace='strava'::regnamespace)) as value`)
    ).rows[0].value;
  const at010 = await shape();
  assert.ok(!JSON.stringify(at010).includes("connect_pairings"));
  await before.exec(file("supabase/strava/011_connect_device.sql"));
  const at011 = await shape();
  assert.ok(JSON.stringify(at011).includes("connect_pairings"));
  assert.ok(JSON.stringify(at011).includes("grinder_agent_tokens.last_seen_at"));
  assert.ok(JSON.stringify(at011).includes("connect_token_touch"));
  await before.exec(file("supabase/strava/down/011_connect_device.sql"));
  assert.deepEqual(await shape(), at010, "the down script must leave the 010 schema exactly");
  await before.close();
});
