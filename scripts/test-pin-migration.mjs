// Pin runs to a profile (supabase/strava/015_pin.sql) in real PostgreSQL/WASM.
// Proves: the owner pins up to 3 of their own runs; a 4th is refused; unpinning frees a slot;
// nobody else can pin or unpin them; anon writes nothing.
import { PGlite } from '@electric-sql/pglite';
import { readFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import assert from 'node:assert/strict';

assert.ok(existsSync(new URL('../supabase/strava/015_pin.sql', import.meta.url)), '015_pin.sql is missing');
const db = new PGlite();
const read = p => readFileSync(new URL('../' + p, import.meta.url), 'utf8');
const build = p => execFileSync('python3', [new URL('./' + p, import.meta.url).pathname], { encoding: 'utf8' });
await db.exec(`create role anon; create role authenticated;
alter default privileges grant all on tables to anon,authenticated;
alter default privileges grant execute on functions to anon,authenticated;
create schema auth;
create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
grant usage on schema auth to anon,authenticated;`);
await db.exec(read('tests/fixtures/hosted-base.sql'));
await db.exec(build('prepare-migration.py'));
const full = build('prepare-strava-database.py');
assert.ok(full.includes('-- strava/015_pin.sql'), '015 must be part of the strava bootstrap');
await db.exec(full);
await db.exec(read('supabase/strava/015_pin.sql')); // re-applying is safe

const A = '40000000-0000-0000-0000-00000000000a', B = '40000000-0000-0000-0000-00000000000b';
await db.exec(`insert into strava.profiles(id,auth_uid,handle,display_name) values ('${A}','${A}','alice','Alice'),('${B}','${B}','bob','Bob')`);
const runs = [1, 2, 3, 4].map(i => `50000000-0000-0000-0000-00000000000${i}`);
for (const id of runs) await db.exec(`insert into strava.runs(id,profile_id,title,visibility) values ('${id}','${A}','Run','private')`);
await db.exec('set search_path=strava,pg_temp');
const as = async (id) => { await db.exec('reset role'); await db.query("select set_config('request.jwt.claim.sub',$1,false)", [id || '']); await db.exec(`set role ${id ? 'authenticated' : 'anon'}`); };
const pinned = async () => { await db.exec('reset role'); const n = (await db.query(`select count(*)::int n from strava.runs where profile_id=$1 and pinned_at is not null`, [A])).rows[0].n; return n; };

// The owner pins three.
await as(A);
for (const id of runs.slice(0, 3)) await db.query(`update strava.runs set pinned_at=now() where id=$1`, [id]);
assert.equal(await pinned(), 3);
// A fourth is refused.
await as(A);
await assert.rejects(db.query(`update strava.runs set pinned_at=now() where id=$1`, [runs[3]]), /Pin up to 3 runs/);
assert.equal(await pinned(), 3);
// Unpinning frees a slot.
await as(A);
await db.query(`update strava.runs set pinned_at=null where id=$1`, [runs[0]]);
await db.query(`update strava.runs set pinned_at=now() where id=$1`, [runs[3]]);
assert.equal(await pinned(), 3);
// Someone else cannot pin or unpin them (RLS filters the row).
await as(B);
await db.query(`update strava.runs set pinned_at=null where id=$1`, [runs[1]]);
await db.query(`update strava.runs set pinned_at=now() where id=$1`, [runs[0]]);
assert.equal(await pinned(), 3);
await db.exec('reset role');
assert.equal((await db.query(`select pinned_at from strava.runs where id=$1`, [runs[0]])).rows[0].pinned_at, null, 'B pinned A\'s run');
// Anon writes nothing.
await as(null);
await db.query(`update strava.runs set pinned_at=null where id=$1`, [runs[1]]).catch(() => {});
assert.equal(await pinned(), 3);
console.log('015: the owner pins up to 3 runs; a 4th is refused; nobody else pins or unpins; anon writes nothing.');
