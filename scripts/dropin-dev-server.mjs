// A local STRIVE for the drop-in flow, with a real database and no network writes.
// Serves the built site (dist/, run `npm run build` first) and answers /api/link and /l/<id> with
// the production handlers (server/dropin-link.mjs). Their PostgREST calls are answered by PGlite
// running the real strava schema and supabase/strava/011_dropin_links.sql, as the anon role.
//
//   node scripts/dropin-dev-server.mjs [port]      then open http://localhost:<port>/
import http from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { PGlite } from '@electric-sql/pglite';
import * as L from '../server/dropin-link.mjs';
import { confirm as fairConfirm } from '../server/fair-confirm.mjs';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const DIST = path.join(ROOT, 'dist');
const port = Number(process.argv[2] || 8765);
const ORIGIN = `http://localhost:${port}`;

export async function database() {
  const db = new PGlite();
  const build = p => execFileSync('python3', [path.join(ROOT, 'scripts', p)], { encoding: 'utf8' });
  await db.exec(`create role anon; create role authenticated;
  alter default privileges grant all on tables to anon,authenticated;
  alter default privileges grant execute on functions to anon,authenticated;
  create schema auth;
  create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
  grant usage on schema auth to anon,authenticated;`);
  await db.exec(readFileSync(path.join(ROOT, 'tests/fixtures/hosted-base.sql'), 'utf8'));
  await db.exec(build('prepare-migration.py'));
  await db.exec(build('prepare-strava-database.py'));
  return db;
}

// PostgREST's rpc endpoint, for the three drop-in functions only, called as anon.
export function postgrest(db) {
  const SIG = { dropin_create: ['payload::jsonb', 'bucket'], dropin_read: ['link_id::uuid'], dropin_delete: ['link_id::uuid', 'token'] };
  return async (url, init) => {
    const name = String(url).split('/rest/v1/rpc/')[1];
    if (!SIG[name]) return new Response(JSON.stringify({ message: 'not found' }), { status: 404 });
    const args = JSON.parse(init.body);
    const names = SIG[name].map(s => s.split('::')[0]);
    const params = names.map(n => (n === 'payload' ? JSON.stringify(args[n]) : args[n]));
    const call = SIG[name].map((s, i) => `${s.split('::')[0]}=>$${i + 1}${s.includes('::') ? '::' + s.split('::')[1] : ''}`).join(',');
    try {
      await db.exec('set role anon');
      const r = (await db.query(`select strava.${name}(${call}) as r`, params)).rows[0].r;
      return new Response(JSON.stringify(r), { status: 200, headers: { 'Content-Type': 'application/json' } });
    } catch (e) {
      return new Response(JSON.stringify({ message: e.message }), { status: 400, headers: { 'Content-Type': 'application/json' } });
    } finally { await db.exec('reset role'); }
  };
}

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.txt': 'text/plain' };

export async function serve({ db, listen = port, fairEnv = process.env } = {}) {
  db = db || await database();
  const dbFetch = postgrest(db);
  const fetchImpl = (url, init) => String(url).startsWith('http://postgrest.local/') ? dbFetch(url, init) : fetch(url, init);
  const config = { SB_URL: 'http://postgrest.local', SB_KEY: 'local-development-only', ORIGIN: `http://localhost:${listen}` };
  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url, config.ORIGIN);
    const send = (status, body, type = 'application/json') => { res.writeHead(status, { 'Content-Type': type, 'Cache-Control': 'no-store' }); res.end(typeof body === 'string' || Buffer.isBuffer(body) ? body : JSON.stringify(body)); };
    try {
      if (url.pathname === '/api/link' && req.method === 'POST') {
        let raw = ''; for await (const c of req) raw += c;
        let body; try { body = JSON.parse(raw); } catch { body = undefined; }
        const headers = { ...req.headers, 'x-forwarded-for': req.headers['x-forwarded-for'] || req.socket.remoteAddress };
        const out = url.searchParams.get('action') === 'delete'
          ? await L.deleteLink({ method: 'POST', body }, config, fetchImpl)
          : await L.createLink({ method: 'POST', headers, body }, config, fetchImpl, fairEnv);
        return send(out.status, out.body);
      }
      if (url.pathname === '/api/fair/confirm' && req.method === 'POST') {
        let raw = ''; for await (const c of req) raw += c;
        let body; try { body = JSON.parse(raw); } catch { body = undefined; }
        const out = await fairConfirm({ method: 'POST', headers: req.headers, body }, config, fairEnv, fetchImpl);
        return send(out.status, out.body);
      }
      const m = /^\/l\/([^/]+)(\/delete)?$/.exec(url.pathname);
      if (m) {
        if (m[2]) return send(200, L.deleteHtml(m[1]), TYPES['.html']);
        const link = await L.readLink(m[1], config, fetchImpl);
        return link ? send(200, L.linkHtml(link, { origin: config.ORIGIN }), TYPES['.html']) : send(404, L.missingHtml(), TYPES['.html']);
      }
      let file = path.join(DIST, decodeURIComponent(url.pathname));
      if (!file.startsWith(DIST)) return send(403, 'no', 'text/plain');
      let found = await stat(file).then(s => s.isFile()).catch(() => false);
      if (!found && await stat(file + '.html').then(s => s.isFile()).catch(() => false)) { file += '.html'; found = true; }
      if (!found) file = path.join(DIST, 'index.html');
      send(200, await readFile(file), TYPES[path.extname(file)] || 'application/octet-stream');
    } catch (e) { send(500, { error: String(e.message || e) }); }
  });
  await new Promise(r => server.listen(listen, '127.0.0.1', r));
  const address = server.address();
  config.ORIGIN = `http://127.0.0.1:${address.port}`;
  return { server, db, origin: config.ORIGIN };
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  const { origin } = await serve();
  console.log(`Drop-in dev server on ${origin} (dist/ + PGlite strava schema, anon role).`);
}
