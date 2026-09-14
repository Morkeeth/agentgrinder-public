import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';
import {readPublic,html,card} from '../server/public-run.mjs';
import {ImageResponse} from '@vercel/og';
const id='28d5d0b7-eda2-4d94-a83c-580d2e3b75b2';let fetches=0;
assert.equal(await readPublic('bad',()=>{fetches++}),null);assert.equal(fetches,0);
const fixture={id,title:'Fixture: repaired the import',harness:'Codex',prompts:8,artifacts_produced:2,commits:null,rhythm:[1,3,2,5,1,2],profiles:{github_handle:'fixture-builder'}};
assert.deepEqual(await readPublic(id,async(url,options)=>{assert.equal(new URL(url).searchParams.get('visibility'),'eq.public');assert(!new URL(url).searchParams.get('select').includes('note'));assert(new URL(url).searchParams.get('select').includes('github_handle,handle,display_name'));assert.equal(options.cache,'no-store');assert.equal(options.headers['Accept-Profile'],'strava');return{ok:true,json:async()=>[fixture]}}),fixture);
assert.equal(await readPublic(id,async()=>({ok:true,json:async()=>[]})),null);
assert(!html({...fixture,title:'<script>"bad"</script>'}).includes('<script>'));
const chosen={...fixture,profiles:{handle:'chosen-builder',github_handle:null,display_name:'Chosen Builder'}};
assert(JSON.stringify(card(chosen)).includes('@chosen-builder'),'chosen-only identity appears on the share card');
assert(JSON.stringify(card(fixture)).includes('@fixture-builder'),'legacy identity fallback survives');
const renamed=JSON.stringify(card({...chosen,profiles:{...chosen.profiles,github_handle:'old-alias'}}));
assert(renamed.includes('@chosen-builder')&&!renamed.includes('@old-alias'),'chosen identity takes precedence');
const image=new ImageResponse(card(chosen),{width:1200,height:630});const bytes=Buffer.from(await image.arrayBuffer());assert.equal(bytes.subarray(1,4).toString(),'PNG');assert.equal(bytes.readUInt32BE(16),1200);assert.equal(bytes.readUInt32BE(20),630);await writeFile('/tmp/grinder-public-preview.png',bytes);
if(process.argv.includes('--live')) {const live=await readPublic(id);assert(live?.id===id);assert(html(live).includes('og:image'));}
console.log('Preview: actual PNG rendered; escaped title; public-only query; private/missing refusal passed (live read requires --live)');
