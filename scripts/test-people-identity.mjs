// Actual PostgreSQL/RLS through PGlite. Synthetic actors; no network or hosted writes.
import { PGlite } from '@electric-sql/pglite';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import assert from 'node:assert/strict';
const db=new PGlite();
const a='31000000-0000-0000-0000-000000000001',b='31000000-0000-0000-0000-000000000002',c='31000000-0000-0000-0000-000000000003';
await db.exec(`create role anon; create role authenticated;
alter default privileges grant all on tables to anon,authenticated;
alter default privileges grant execute on functions to anon,authenticated;
create schema auth;
create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
grant usage on schema auth to anon,authenticated;
create table auth.identities(user_id uuid,provider text,identity_data jsonb);
insert into auth.identities values('${c}','github','{"user_name":"LegacyBuilder"}');
create table public.profiles(id uuid,name text);
insert into public.profiles values('${a}','Grinder sentinel');
create function public.grinder_find_people(q text,lim integer default 20) returns jsonb language sql as $$select '[]'::jsonb$$;
create function public.grinder_recent_builders(lim integer default 12) returns jsonb language sql as $$select '[]'::jsonb$$;`);
async function untouched(){return (await db.query(`select jsonb_build_object(
 'tables',(select jsonb_agg(row_to_json(c) order by c.oid) from pg_class c where relnamespace in ('public'::regnamespace,'auth'::regnamespace)),
 'functions',(select jsonb_agg(row_to_json(p) order by p.oid) from pg_proc p where pronamespace in ('public'::regnamespace,'auth'::regnamespace)),
 'profiles',(select jsonb_agg(row_to_json(p)) from public.profiles p),
 'identities',(select jsonb_agg(row_to_json(i)) from auth.identities i)) v`)).rows[0].v;}
const before=await untouched();
const sql=execFileSync('python3',[new URL('./prepare-strava-database.py',import.meta.url).pathname],{encoding:'utf8'});
assert(sql.indexOf('-- strava/identity.sql')<sql.indexOf('-- strava/people_identity.sql'),'identity columns must exist before RPC overrides');
await db.exec(sql);
const migration=readFileSync(new URL('../supabase/strava/people_identity.sql',import.meta.url),'utf8');
await db.exec(migration);await db.exec(migration);
assert.deepEqual(await untouched(),before);
await db.exec('set search_path=strava,pg_temp');
async function as(id){await db.exec('reset role');await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id||'']);await db.exec(id?'set role authenticated':'set role anon');}
const find=async q=>(await db.query('select strava.grinder_find_people($1,20) v',[q])).rows[0].v;
const recent=async ()=>(await db.query('select strava.grinder_recent_builders(12) v')).rows[0].v;
await as(a);
await db.query("insert into profiles(id,auth_uid,handle,display_name) values($1,$1,'email-builder','Email Builder')",[a]);
await as(b);
await db.query("insert into profiles(id,auth_uid,handle,display_name,avatar_url) values($1,$1,'x-builder','X Builder','https://example.test/avatar.png')",[b]);
await as(c);
await db.query("insert into profiles(id,auth_uid,github_handle,name) values($1,$1,'LegacyBuilder','Legacy Name')",[c]);
await as(a);
const x=(await find('x-builder'))[0];
assert.equal(x.id,b);assert.equal(x.github_handle,null);assert.equal(x.handle,'x-builder');
assert.equal(x.display_name,'X Builder');assert.equal(x.avatar_url,'https://example.test/avatar.png');
assert.equal((await find('X Builder'))[0].id,b);
assert.equal((await find('Legacy Name'))[0].handle,'LegacyBuilder');
assert.equal((await find('LegacyBuilder'))[0].display_name,'Legacy Name');
assert.deepEqual(await recent(),[],'recent builders still requires a public run');
assert.equal((await db.query('select count(*)::int n from runs')).rows[0].n,0);
await db.query('insert into grinder_follows(follower_id,followed_id) values($1,$2)',[a,b]);
assert.equal((await db.query('select followed_id from grinder_follows where follower_id=$1',[a])).rows[0].followed_id,b,'follow before first post');
await as(b);
await db.query("insert into runs(profile_id,title,caption,visibility) values($1,'TEST DATA public','TEST DATA','public'),($1,'TEST DATA private','TEST DATA','private')",[b]);
await as(a);
assert.equal((await recent())[0].handle,'x-builder');assert.equal(Number((await recent())[0].public_runs),1);
// Pair blocking applies in both directions to search and public-run suggestions.
await db.query('insert into grinder_blocks(blocker_id,blocked_id) values($1,$2)',[a,b]);
assert.deepEqual(await find('x-builder'),[]);assert.deepEqual(await recent(),[]);
await as(b);assert.deepEqual(await find('email-builder'),[]);
await as(a);await db.query('delete from grinder_blocks where blocker_id=$1',[a]);
assert.equal((await find('x-builder'))[0].id,b);
await as(b);assert.deepEqual(await recent(),[],'exclude self from recent suggestions');
await as(null);
assert.equal((await find('EMAIL-BUILDER'))[0].id,a);
assert.equal((await recent())[0].id,b);
for(const q of ['%','_','\\','']) assert.deepEqual(await find(q),[],'literal wildcard or empty search');
for(const row of await find('builder')) assert(!('auth_uid' in row)&&!('rig' in row),'only public identity fields returned');
await db.exec('reset role');
assert.deepEqual(await untouched(),before,'migration and Strava actions leave Grinder/Auth unchanged');
console.log('PASS: chosen-handle search, display/avatar, legacy fallback, follow before post, public-only recent builders, pair blocking, literal search, Grinder/Auth isolation');
await db.close();
