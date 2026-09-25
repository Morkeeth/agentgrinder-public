// Profiles, public Clubs and events (supabase/strava/014_social.sql) in real PostgreSQL/WASM.
// Proves: bio and agents are checked; a public Club can be joined by the signed-in person and a
// private one cannot; only a Club owner posts an event; people join and leave an event for
// themselves; anon writes nothing; a private Club's events stay with its members.
import { PGlite } from '@electric-sql/pglite';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import assert from 'node:assert/strict';

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
assert.ok(full.includes('-- strava/014_social.sql'), '014 must be part of the strava bootstrap');
await db.exec(full);
await db.exec(read('supabase/strava/014_social.sql')); // re-applying is safe

const A = '30000000-0000-0000-0000-00000000000a', B = '30000000-0000-0000-0000-00000000000b', C = '30000000-0000-0000-0000-00000000000c';
await db.exec(`insert into strava.profiles(id,auth_uid,handle,display_name) values
 ('${A}','${A}','alice','Alice'),('${B}','${B}','bob','Bob'),('${C}','${C}','carol','Carol')`);
await db.exec('set search_path=strava,pg_temp');
const as = async (id) => { await db.exec('reset role'); await db.query("select set_config('request.jwt.claim.sub',$1,false)", [id || '']); await db.exec(`set role ${id ? 'authenticated' : 'anon'}`); };
const one = async (sql, args) => (await db.query(sql, args)).rows[0];

// 1. Profile fields
await as(A);
await db.query(`update strava.profiles set bio=$1, agents=$2 where id=$3`, ['Builds with agents at night.', ['claude-code', 'cursor'], A]);
assert.deepEqual((await one(`select bio, agents from strava.profiles where id=$1`, [A])).agents, ['claude-code', 'cursor']);
await assert.rejects(db.query(`update strava.profiles set bio=repeat('x',161) where id=$1`, [A]), /check/);
await assert.rejects(db.query(`update strava.profiles set agents=array['skynet'] where id=$1`, [A]), /check/);
// Another person's profile is not writable (RLS filters the row).
await db.query(`update strava.profiles set bio='hacked' where id=$1`, [B]);
await as(B);
assert.equal((await one(`select bio from strava.profiles where id=$1`, [B])).bio, null);
await as(null);
assert.equal((await one(`select bio from strava.profiles where id=$1`, [A])).bio, 'Builds with agents at night.');

// 2. Clubs
await as(A);
const pub = (await one(`select grinder_create_crew('Night builders','public') id`)).id;
const priv = (await one(`select grinder_create_crew('Two of us','private') id`)).id;
await as(B);
assert.equal((await one(`select grinder_join_public_crew($1) id`, [pub])).id, pub);
await one(`select grinder_join_public_crew($1) id`, [pub]); // twice is fine
await assert.rejects(db.query(`select grinder_join_public_crew($1)`, [priv]), /private or unavailable/);
assert.equal((await one(`select count(*)::int n from grinder_memberships where crew_id=$1`, [pub])).n, 2);
await assert.rejects(db.query(`insert into grinder_memberships(crew_id,profile_id) values($1,$2)`, [priv, B]), /permission denied|row-level security/);
await as(null);
await assert.rejects(db.query(`select grinder_join_public_crew($1)`, [pub]), /permission denied|Sign in/);

// 3. Events
const soon = new Date(Date.now() + 86400000).toISOString();
await as(B);
await assert.rejects(db.query(`select grinder_create_event($1,'x','','',$2)`, [pub, soon]), /Only the Club owner/);
await as(A);
await assert.rejects(db.query(`select grinder_create_event($1,'Past','','',now()-interval '1 hour')`, [pub]), /future/);
const ev = (await one(`select grinder_create_event($1,'Sunday build','Bring a run.','Paris',$2) id`, [pub, soon])).id;
const privEv = (await one(`select grinder_create_event($1,'Just us','','',$2) id`, [priv, soon])).id;
await as(C);
await db.query(`select grinder_join_event($1)`, [ev]);
await db.query(`select grinder_join_event($1)`, [ev]);
assert.equal((await one(`select count(*)::int n from grinder_event_people where event_id=$1`, [ev])).n, 2);
await assert.rejects(db.query(`select grinder_join_event($1)`, [privEv]), /private or unavailable/);
await assert.rejects(db.query(`insert into grinder_events(crew_id,owner_id,title,starts_at) values($1,$2,'fake',now())`, [pub, C]), /permission denied/);
await assert.rejects(db.query(`insert into grinder_event_people(event_id,profile_id) values($1,$2)`, [ev, A]), /permission denied/);
assert.equal((await db.query(`select id from grinder_events where id=$1`, [privEv])).rows.length, 0, 'a private Club event is hidden from non-members');
await db.query(`select grinder_leave_event($1)`, [ev]);
assert.equal((await one(`select count(*)::int n from grinder_event_people where event_id=$1`, [ev])).n, 1);
await assert.rejects(db.query(`select grinder_delete_event($1)`, [ev]), /Only the host/);
await as(null);
assert.equal((await db.query(`select id from grinder_events where id=$1`, [ev])).rows.length, 1, 'a public Club event is readable signed out');
await assert.rejects(db.query(`select grinder_join_event($1)`, [ev]), /permission denied|Sign in/);
await as(A);
await db.query(`select grinder_delete_event($1)`, [ev]);
assert.equal((await db.query(`select id from grinder_events where id=$1`, [ev])).rows.length, 0);
console.log('014: bio and agents checked; public Clubs joinable, private not; events owner-posted, joined and left by the person; anon writes nothing.');
