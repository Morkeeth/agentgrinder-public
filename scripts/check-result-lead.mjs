import assert from 'node:assert/strict';
import {writeFile,readFile} from 'node:fs/promises';
import ResultLead from '../site/result-lead.js';
import {ImageResponse} from '@vercel/og';

const productionOrigin='https://agentic-strava.vercel.app';
process.env.STRAVA_ORIGIN=productionOrigin;
const {html,card}=await import('../server/public-run.mjs');

// Exact authorized public row, read from the production strava schema on 27 September.
// It is a pre-run plan, not a result. Null stays null: this check must never promote the
// caption to a result account or produce a launch card from it.
const current={
 id:'df6525c7-cdb0-4d6f-a7d3-c9650cb1915a',
 created_at:'2026-09-26T13:14:59.174882+00:00',
 title:'SUNDAY COMING IN HOT · the 2 hour studio sprint',
 caption:'Two hours. Four lanes. One finish line.\n\nFree Lunch × STRIVE: one connected journey.\nHelicon: one clean install.\nFAVOUR: company → accepted work → payment path.\nSTORY: one sourced article + video pack.\n\n16:00: 4 returns, 3 proofs, 1 night plan. Sunday coming in hot.',
 note:null,coach_verdict:null,duration_s:7200,commits:null,is_ship:false,route:null,
 visibility:'public',profiles:{handle:'morkeeth',display_name:'Oscar Morkeeth',github_handle:'Morkeeth'}
};
const currentLead=ResultLead.guard(ResultLead.present(current,'view'),current);
assert.equal(currentLead.label,'Outcome not recorded');
assert.equal(currentLead.outcome,null);
assert.equal(currentLead.outcomeSource,null);
assert.equal(currentLead.sourceLine,'Evidence source: none stored for this view');
assert.equal(currentLead.duration,'2h 0m');
const currentPage=html(current);
assert.ok(currentPage.includes('<link rel="canonical" href="'+productionOrigin+'/r/'+current.id+'">'));
assert.ok(currentPage.includes('<meta property="og:title" content="'+current.title+'">'));
assert.equal(currentPage.includes('localhost'),false);
assert.equal(currentPage.includes('Builder’s account'),false);
assert.equal(currentPage.includes('Observed outcome'),false);

// A clearly labelled fixture proves the result path without pretending the current run has one.
const fixture={
 id:'28d5d0b7-eda2-4d94-a83c-580d2e3b75b2',visibility:'public',
 title:'TEST FIXTURE · result-first contract',
 note:'TEST FIXTURE: the builder reports that the import opens on the run it created.',
 duration_s:8400,commits:3,is_ship:true,route:[0,1,2,1,3],harness:'Cursor',
 created_at:'2026-08-30T11:33:00Z',profiles:{github_handle:'fixture-builder'}
};
const lead=ResultLead.guard(ResultLead.present(fixture,'view'),fixture);
assert.equal(lead.label,'Builder’s account');
assert.equal(lead.outcome,fixture.note);
assert.equal(lead.outcomeSource,'runs.note');
assert.equal(lead.sourceLine,'Evidence source: runs.note');
assert.equal(lead.duration,'2h 20m');
assert.ok(lead.limit.startsWith('Builder-authored account.'));
assert.notEqual(lead.label,'Observed outcome');

const fake={...lead,outcome:'Deep focus'};
assert.throws(()=>ResultLead.guard(fake,fixture),/result source guard/);
const saved=ResultLead.guard;
ResultLead.guard=value=>value;
assert.equal(ResultLead.guard(fake,fixture).outcome,'Deep focus');
ResultLead.guard=saved;
assert.throws(()=>ResultLead.guard(fake,fixture),/result source guard/);

const fixturePage=html(fixture),body=fixturePage.slice(fixturePage.indexOf('<body>'));
const accountAt=body.indexOf('Builder’s account'),sourceAt=body.indexOf('Evidence source: runs.note'),limitAt=body.indexOf('<strong>Limit:</strong>'),durationAt=body.indexOf('>2h 20m<');
assert.ok(accountAt>0&&sourceAt>accountAt&&limitAt>sourceAt&&durationAt>limitAt);
assert.ok(fixturePage.includes('<meta property="og:title" content="'+fixture.note+'">'));
assert.equal(fixturePage.includes('localhost'),false);
const image=new ImageResponse(card(fixture),{width:1200,height:630});
const bytes=Buffer.from(await image.arrayBuffer());
assert.equal(bytes.subarray(1,4).toString(),'PNG');
assert.equal(bytes.readUInt32BE(16),1200);assert.equal(bytes.readUInt32BE(20),630);

// QA only. This exact-current-row page shows the honest missing-result state at 390 px. It is
// not a launch asset, and no image is generated for the result-less current run.
const design=await readFile(new URL('../site/design.css',import.meta.url),'utf8');
const feed=await readFile(new URL('../site/feed.css',import.meta.url),'utf8');
await writeFile('/tmp/strive-current-resultless-qa.html',currentPage.replace('</head>','<style>'+design+'\n'+feed+'</style></head>'));
console.log('Result lead passed: exact public run has no stored result account; production canonical is clean; fixture guard went red, was restored, and fixture OG rendered in memory only.');
