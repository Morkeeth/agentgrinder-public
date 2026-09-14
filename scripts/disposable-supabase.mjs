// Isolated disposable Postgres + a tiny PostgREST/GoTrue shim.
// TEST DATA only. Never pointed at production. Coordinator owns hosted deploy.
import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
export const CASEY = "11000000-0000-0000-0000-000000000001";
export const RILEY = "11000000-0000-0000-0000-000000000002";
const TABLES = new Set([
  "profiles",
  "runs",
  "acks",
  "grinder_follows",
  "grinder_blocks",
  "grinder_replies",
  "grinder_practice_versions",
  "grinder_practice_attempts",
  "grinder_run_moments",
  "grinder_adopted_moments",
  "grinder_notifications",
  "grinder_memberships",
  "grinder_crews",
]);

export function mintJwt(sub, email) {
  const header = Buffer.from(JSON.stringify({ alg: "none", typ: "JWT" })).toString("base64url");
  const payload = Buffer.from(
    JSON.stringify({
      sub,
      email,
      role: "authenticated",
      aud: "authenticated",
      exp: Math.floor(Date.now() / 1000) + 86400,
    }),
  ).toString("base64url");
  return `${header}.${payload}.sig`;
}

export function sessionFor(sub, email, handle) {
  const access_token = mintJwt(sub, email);
  const user = {
    id: sub,
    aud: "authenticated",
    role: "authenticated",
    email,
    user_metadata: { user_name: handle, full_name: handle, preferred_username: handle },
    app_metadata: { provider: "email" },
  };
  return {
    access_token,
    refresh_token: access_token,
    token_type: "bearer",
    expires_in: 86400,
    expires_at: Math.floor(Date.now() / 1000) + 86400,
    user,
  };
}

export async function bootDisposable() {
  const { PGlite } = await import("@electric-sql/pglite");
  const db = new PGlite();
  await db.exec(`create role anon; create role authenticated;
alter default privileges grant all on tables to anon,authenticated;
alter default privileges grant execute on functions to anon,authenticated;
create schema auth;
create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
grant usage on schema auth to anon,authenticated;
`);
  await db.exec(await readFile(join(ROOT, "tests/fixtures/hosted-base.sql"), "utf8"));
  await db.exec(`grant select,insert,update,delete on profiles,runs,acks to anon,authenticated;`);
  await db.exec(
    execFileSync("python3", [join(ROOT, "scripts/prepare-migration.py")], { encoding: "utf8" }),
  );
  for (const file of (await readFile(join(ROOT, "scripts/migration-order.txt"), "utf8"))
    .trim()
    .split("\n")) {
    const sql = await readFile(join(ROOT, "supabase/migrations", file), "utf8");
    await db.exec(sql);
  }
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
      caught = ["P0001", "42501", "23514", "23505"].includes(error.code);
      if (!caught) throw error;
    }
    if (!caught) throw new Error("Expected server denial: " + sql);
  }
  return { db, as, anonymous, denied };
}

export async function seedJourneyActors(db) {
  await db.exec("reset role");
  await db.query(
    "insert into profiles(id,auth_uid,github_handle,name) values($1,$1,'test-casey','TEST DATA Casey'),($2,$2,'test-riley','TEST DATA Riley')",
    [CASEY, RILEY],
  );
}

function decodeSub(req) {
  const auth = req.headers.authorization || "";
  const token = auth.replace(/^Bearer\s+/i, "").trim();
  if (!token) return "";
  const parts = token.split(".");
  if (parts.length >= 2) {
    try {
      const payload = JSON.parse(Buffer.from(parts[1], "base64url").toString());
      return payload.sub || "";
    } catch (_) {
      return "";
    }
  }
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(token) ? token : "";
}

function parseFilters(url) {
  const filters = [];
  for (const [key, raw] of url.searchParams) {
    if (["select", "order", "limit", "offset"].includes(key)) continue;
    const [op, ...rest] = raw.split(".");
    const value = rest.join(".");
    if (op === "eq") filters.push({ key, op: "=", value });
    else if (op === "not" && value === "is.null") filters.push({ key, op: "IS NOT NULL" });
    else if (op === "is" && value === "null") filters.push({ key, op: "IS NULL" });
    else if (op === "in") {
      const inner = value.replace(/^\(|\)$/g, "");
      filters.push({
        key,
        op: "IN",
        value: inner.split(",").map((x) => x.replace(/^"|"$/g, "")),
      });
    }
  }
  return filters;
}

function ident(name) {
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name)) throw new Error("Bad identifier");
  return '"' + name + '"';
}

async function withRole(db, sub, fn) {
  await db.exec("begin");
  try {
    await db.exec("reset role");
    await db.query("select set_config('request.jwt.claim.sub',$1,true)", [sub || ""]);
    await db.exec(sub ? "set role authenticated" : "set role anon");
    const result = await fn();
    await db.exec("commit");
    return result;
  } catch (error) {
    try {
      await db.exec("rollback");
    } catch (_) {}
    throw error;
  } finally {
    try {
      await db.exec("reset role");
    } catch (_) {}
  }
}

function pgError(error) {
  return {
    message: error.message,
    code: error.code || "P0001",
    details: null,
    hint: null,
  };
}

async function readBody(req) {
  const chunks = [];
  for await (const c of req) chunks.push(c);
  if (!chunks.length) return null;
  try {
    return JSON.parse(Buffer.concat(chunks).toString("utf8") || "null");
  } catch (_) {
    return null;
  }
}

function cors(res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Headers", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,PATCH,DELETE,OPTIONS");
  res.setHeader("Access-Control-Expose-Headers", "Content-Range,Content-Profile,Location");
}

export function startDisposableServer(db, { port = 0 } = {}) {
  let chain = Promise.resolve();
  const serialize = (fn) => {
    const next = chain.then(fn, fn);
    chain = next.catch(() => {});
    return next;
  };
  const server = createServer((req, res) => {
    cors(res);
    if (req.method === "OPTIONS") {
      res.statusCode = 204;
      res.end();
      return;
    }
    serialize(() => handle(db, req, res)).catch((error) => {
      if (res.headersSent) return;
      res.statusCode = 400;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(pgError(error)));
    });
  });
  return new Promise((resolve) => {
    server.listen(port, "127.0.0.1", () => {
      const addr = server.address();
      resolve({ server, url: `http://127.0.0.1:${addr.port}` });
    });
  });
}

async function handle(db, req, res) {
  const url = new URL(req.url, "http://127.0.0.1");
  const sub = decodeSub(req);
  if (url.pathname === "/auth/v1/user") {
    if (!sub) {
      res.statusCode = 401;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ message: "Invalid token" }));
      return;
    }
    const row = (
      await db.query("select id,github_handle,name from profiles where auth_uid=$1", [sub])
    ).rows[0];
    const handle = row?.github_handle || "grinder-" + sub.slice(0, 8);
    res.setHeader("Content-Type", "application/json");
    res.end(
      JSON.stringify({
        id: sub,
        aud: "authenticated",
        role: "authenticated",
        email: handle + "@example.test",
        user_metadata: { user_name: handle, full_name: row?.name || handle },
      }),
    );
    return;
  }
  if (url.pathname === "/auth/v1/token") {
    const body = await readBody(req);
    const token = body?.refresh_token || "";
    const fakeReq = { headers: { authorization: "Bearer " + token } };
    const refreshSub = decodeSub(fakeReq);
    const sess = sessionFor(refreshSub, "user@example.test", "grinder-" + (refreshSub || "").slice(0, 8));
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify(sess));
    return;
  }
  if (url.pathname.startsWith("/rest/v1/rpc/")) {
    const fn = url.pathname.slice("/rest/v1/rpc/".length);
    if (!/^[a-z_][a-z0-9_]*$/.test(fn)) throw new Error("Unknown RPC");
    const body = (await readBody(req)) || {};
    const keys = Object.keys(body);
    const result = await withRole(db, sub, async () => {
      if (!keys.length) {
        return (await db.query(`select ${ident(fn)}() as result`)).rows[0].result;
      }
      const args = keys.map((k, i) => ident(k) + " := $" + (i + 1)).join(", ");
      const values = keys.map((k) => body[k]);
      return (await db.query(`select ${ident(fn)}(${args}) as result`, values)).rows[0].result;
    });
    let payload = result;
    if (typeof payload === "string") {
      try {
        payload = JSON.parse(payload);
      } catch (_) {}
    }
    res.statusCode = 200;
    res.setHeader("Content-Type", "application/json");
    res.end(payload === undefined ? "null" : JSON.stringify(payload));
    return;
  }
  if (url.pathname === "/_test/insert-run") {
    if (process.env.GRINDER_DISPOSABLE_TEST !== "1") {
      res.statusCode = 404;
      res.end(JSON.stringify({ message: "Not found" }));
      return;
    }
    const body = (await readBody(req)) || {};
    await db.exec("reset role");
    const id = (
      await db.query(
        `insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts,claims,claims_verified,artifacts_produced,rhythm)
         values($1,$2,'private',$3,1,$4,$5,now(),$6,$7,$8,$9,'[1,2,1]'::jsonb) returning id`,
        [
          body.profile_id,
          body.title || "TEST DATA later sitting",
          body.harness || "Codex",
          body.measurement_revision,
          body.trace_basis || "elapsed",
          body.prompts ?? 3,
          body.claims ?? 2,
          body.claims_verified ?? 2,
          body.artifacts_produced ?? 1,
        ],
      )
    ).rows[0].id;
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify({ id }));
    return;
  }
  if (!url.pathname.startsWith("/rest/v1/")) {
    res.statusCode = 404;
    res.end(JSON.stringify({ message: "Not found" }));
    return;
  }
  const table = url.pathname.slice("/rest/v1/".length).split("/")[0];
  if (!TABLES.has(table)) throw new Error("Unknown table");
  const select = url.searchParams.get("select") || "*";
  const filters = parseFilters(url);
  const prefer = String(req.headers.prefer || "");
  const singular = /vnd\.pgrst\.object/.test(String(req.headers.accept || "")) || /return=representation/.test(prefer) && req.method === "GET" && url.searchParams.has("limit") === false && filters.some((f) => f.key === "id" && f.op === "=");
  const wantObject =
    /vnd\.pgrst\.object/.test(String(req.headers.accept || ""));
  const body = ["POST", "PATCH"].includes(req.method) ? await readBody(req) : null;

  const result = await withRole(db, sub, async () => {
    if (req.method === "GET") return selectRows(db, table, select, filters, url);
    if (req.method === "POST") {
      const rows = Array.isArray(body) ? body : [body];
      const out = [];
      for (const row of rows) out.push(await insertRow(db, table, row, select));
      return out;
    }
    if (req.method === "PATCH") {
      return updateRows(db, table, body || {}, filters, select);
    }
    if (req.method === "DELETE") {
      return deleteRows(db, table, filters);
    }
    throw new Error("Unsupported method");
  });
  res.statusCode = 200;
  res.setHeader("Content-Type", "application/json");
  if (wantObject) {
    const row = Array.isArray(result) ? result[0] : result;
    if (!row) {
      res.statusCode = 406;
      res.end(JSON.stringify({ message: "JSON object requested, multiple (or no) rows returned", code: "PGRST116" }));
      return;
    }
    res.end(JSON.stringify(row));
    return;
  }
  res.end(JSON.stringify(Array.isArray(result) ? result : result == null ? [] : [result]));
}

function embedParts(select) {
  const embeds = [];
  let columns = select;
  columns = columns.replace(/(?:([A-Za-z_]+):)?([A-Za-z_]+)!([A-Za-z0-9_]+)\(([^)]*)\)/g, (_, alias, table, hint, cols) => {
    embeds.push({ alias: alias || table, table, hint, cols });
    return "";
  });
  columns = columns.replace(/([A-Za-z_]+):([A-Za-z0-9_]+)\(([^)]*)\)/g, (_, alias, table, cols) => {
    embeds.push({ alias, table, cols });
    return "";
  });
  columns = columns.replace(/,+/g, ",").replace(/^,|,$/g, "");
  if (!columns.trim()) columns = "*";
  return { columns, embeds };
}

function whereClause(filters, start = 1) {
  const parts = [];
  const params = [];
  let i = start;
  for (const f of filters) {
    if (f.op === "IS NOT NULL") parts.push(`${ident(f.key)} is not null`);
    else if (f.op === "IS NULL") parts.push(`${ident(f.key)} is null`);
    else if (f.op === "IN") {
      const slots = f.value.map(() => "$" + i++);
      params.push(...f.value);
      parts.push(`${ident(f.key)} in (${slots.join(",")})`);
    } else {
      parts.push(`${ident(f.key)} ${f.op} $${i++}`);
      params.push(f.value);
    }
  }
  return { sql: parts.length ? " where " + parts.join(" and ") : "", params };
}

async function selectRows(db, table, select, filters, url) {
  const { columns, embeds } = embedParts(select);
  const { sql, params } = whereClause(filters);
  let q = `select ${columns === "*" ? "*" : columns.split(",").map((c) => ident(c.trim())).join(",")} from ${ident(table)}${sql}`;
  const order = url.searchParams.get("order");
  if (order) {
    const [col, dir] = order.split(".");
    q += ` order by ${ident(col)} ${dir === "desc" ? "desc" : "asc"}`;
  }
  const limit = url.searchParams.get("limit");
  if (limit) q += ` limit ${Number(limit)}`;
  const rows = (await db.query(q, params)).rows;
  for (const row of rows) {
    for (const emb of embeds) {
      if (emb.table === "profiles" && (row.profile_id || row.author_id || row.actor_id)) {
        const p = (
          await db.query("select id,github_handle,name,rig from profiles where id=$1", [emb.alias === "author" ? row.author_id : emb.alias === "actor" ? row.actor_id : row.profile_id])
        ).rows[0];
        row[emb.alias] = p || null;
      } else if (emb.table === "grinder_run_moments" && (row.moment_id || row.id)) {
        const id = row.moment_id;
        const m = id
          ? (await db.query("select id,title from grinder_run_moments where id=$1", [id])).rows[0]
          : null;
        row[emb.alias] = m || null;
      }
    }
  }
  return rows;
}

async function insertRow(db, table, row, select) {
  const keys = Object.keys(row || {}).filter((k) => /^[A-Za-z_][A-Za-z0-9_]*$/.test(k));
  if (!keys.length) throw new Error("Empty insert");
  const values = keys.map((k) => row[k]);
  const returning = select && select !== "*" ? select.split(",").map((c) => ident(c.trim())).join(",") : "*";
  const q = `insert into ${ident(table)} (${keys.map(ident).join(",")}) values (${keys.map((_, i) => "$" + (i + 1)).join(",")}) returning ${returning}`;
  return (await db.query(q, values)).rows[0];
}

async function updateRows(db, table, row, filters, select) {
  const keys = Object.keys(row || {}).filter((k) => /^[A-Za-z_][A-Za-z0-9_]*$/.test(k));
  if (!keys.length) return [];
  const set = keys.map((k, i) => `${ident(k)}=$${i + 1}`).join(",");
  const { sql, params } = whereClause(filters, keys.length + 1);
  const returning = select && select !== "*" ? select.split(",").map((c) => ident(c.trim())).join(",") : "*";
  const q = `update ${ident(table)} set ${set}${sql} returning ${returning}`;
  return (await db.query(q, [...keys.map((k) => row[k]), ...params])).rows;
}

async function deleteRows(db, table, filters) {
  const { sql, params } = whereClause(filters);
  const q = `delete from ${ident(table)}${sql} returning id`;
  return (await db.query(q, params)).rows;
}

const COACH_PLAN = `Friction: Claim 2 named test_draft_renders as done, but check_claim found no matching evidence in that claim's own turn.
Consequence: The card cannot treat that claim as verified. A later sitting that looks shorter or busier is not proof the named check ran.
Experiment: In the same human turn as the completion claim, run test_draft_renders and keep its result in that turn before saying it passed.
Look for: check_claim on the named target returns verified, with test_draft_renders in the evidence snippet. Missing evidence stays unknown, not zero.`;

export async function seedCoachRun(db, owner, title, revision, whenSql) {
  await db.exec("reset role");
  const row = (
    await db.query(
      `insert into runs(profile_id,title,visibility,harness,schema_version,measurement_revision,trace_basis,started_at,prompts,claims,claims_verified,artifacts_produced,rhythm,coach_verdict,coach_plan,coach_mode,coach_tool_calls)
       values($1,$2,'private','Codex',1,$3,'elapsed',${whenSql},3,2,1,1,'[1,2,1]'::jsonb,$4,$5,'deterministic fallback · no agent, no model',6) returning id`,
      [
        owner,
        title,
        revision,
        "1 of 2 claims had evidence in their own turn. TEST DATA fixture sitting.",
        COACH_PLAN,
      ],
    )
  ).rows[0];
  return row.id;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const serve = process.argv.includes("--serve");
  const { db } = await bootDisposable();
  await seedJourneyActors(db);
  const caseyRun = await seedCoachRun(db, CASEY, "TEST DATA Casey coach sitting", "a".repeat(64), "now()-interval '2 days'");
  const rileyRun = await seedCoachRun(db, RILEY, "TEST DATA Riley own baseline", "c".repeat(64), "now()-interval '3 days'");
  const { server, url } = await startDisposableServer(db, { port: Number(process.env.DISPOSABLE_PORT || 0) });
  process.stdout.write(JSON.stringify({ url, casey: CASEY, riley: RILEY, caseyRun, rileyRun, serve }) + "\n");
  if (!serve) {
    server.close();
    await db.close();
  }
}
