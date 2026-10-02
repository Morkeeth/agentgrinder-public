import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {PGlite} from '@electric-sql/pglite';
import {githubFriends} from '../server/github-friends.mjs';
const config={SB_URL:'https://database.test',SB_KEY:'public-key'};
const calls=[];
const response=(data,status=200)=>({ok:status<400,status,json:async()=>data});
const fetcher=async(url,opts)=>{
 calls.push({url,opts});
 if(url.endsWith('/auth/v1/user'))return response({identities:[{provider:'github',identity_data:{sub:'123',user_name:'real-user'}}]});
 if(url==='https://api.github.com/users/real-user')return response({id:123});
 if(url.includes('/following?'))return response([{id:456}]);
 if(url.endsWith('/strava_github_matches'))return response([{id:'public-profile',handle:'friend'}]);
 throw Error('Unexpected URL');
};
const args={authorization:'Bearer private-session',config,fetcher};
assert.deepEqual(await githubFriends(args),{people:[{id:'public-profile',handle:'friend'}],scanned:1,truncated:false,scope:'public_github_following'});
assert(calls.filter(c=>c.url.startsWith('https://api.github.com')).every(c=>!c.opts.headers.Authorization),'Supabase token never goes to GitHub');
assert(!calls.some(c=>c.opts.method&&c.opts.method!=='POST'),'no follow mutation');
await assert.rejects(githubFriends({...args,query:{username:'victim'}}),e=>e.code==='unexpected_query');
await assert.rejects(githubFriends({...args,authorization:''}),e=>e.status===401);
await assert.rejects(githubFriends({...args,fetcher:async(url,opts)=>url==='https://api.github.com/users/real-user'?response({id:999}):fetcher(url,opts)}),e=>e.code==='github_identity_changed');
await assert.rejects(githubFriends({...args,fetcher:async(url,opts)=>url.includes('/following?')?response({},429):fetcher(url,opts)}),e=>e.status===429);
await assert.rejects(githubFriends({...args,fetcher:async(url,opts)=>url.endsWith('/strava_github_matches')?response({},503):fetcher(url,opts)}),e=>e.code==='matching_unavailable');
const db=new PGlite();
await db.exec(`create role anon;create role authenticated;create schema auth;create schema strava;
create function auth.uid() returns uuid language sql as $$select nullif(current_setting('test.uid',true),'')::uuid$$;
create table auth.identities(user_id uuid,provider text,identity_data jsonb);
create table strava.profiles(id uuid,auth_uid uuid,handle text,display_name text,avatar_url text,github_handle text);
create table strava.blocks(a uuid,b uuid);
create function strava.grinder_profile_id() returns uuid language sql as $$select id from strava.profiles where auth_uid=auth.uid()$$;
create function strava.grinder_blocked_pair(a uuid,b uuid) returns boolean language sql as $$select exists(select 1 from strava.blocks x where (x.a=$1 and x.b=$2) or (x.a=$2 and x.b=$1))$$;
grant usage on schema strava to anon,authenticated;
insert into strava.profiles values
('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000001','me',null,null,'me'),
('00000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000002','friend','Friend',null,'real-friend'),
('00000000-0000-0000-0000-000000000003','00000000-0000-0000-0000-000000000003','imposter',null,null,'real-friend');
insert into auth.identities values
('00000000-0000-0000-0000-000000000002','github','{"sub":"456"}'),
('00000000-0000-0000-0000-000000000003','email','{"sub":"456"}');`);
await db.exec(readFileSync(new URL('../supabase/strava/019_github_friends.sql',import.meta.url),'utf8'));
await db.exec("set test.uid='00000000-0000-0000-0000-000000000001';set role authenticated");
const match=async()=>(await db.query("select strava.strava_github_matches(array['456']) result")).rows[0].result;
const matches=await match();assert.equal(matches.length,1);assert.equal(matches[0].handle,'friend');assert(!('auth_uid' in matches[0]));
await db.exec('reset role');await db.exec("insert into strava.blocks values('00000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000001');set role authenticated");
assert.deepEqual(await match(),[],'blocked users never suggested');
await db.exec('reset role;set role anon');await assert.rejects(match(),/permission denied/);
await db.close();
console.log('PASS GitHub discovery: linked numeric identity, malicious username rejection, token isolation, error states, provider spoof rejection, blocked accounts, anonymous denial.');
