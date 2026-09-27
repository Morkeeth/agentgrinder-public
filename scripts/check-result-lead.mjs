import assert from 'node:assert/strict';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import ResultLead from '../site/result-lead.js';
import {html,card} from '../server/public-run.mjs';
import {ImageResponse} from '@vercel/og';

const out=new URL('../artifacts/result-first/',import.meta.url);
await mkdir(out,{recursive:true});
const run={
 id:'a6f0fc15-ebf9-4c33-9c18-91b4a6b2623f',visibility:'public',title:'Sunday build run',
 note:'Shipped the CLI coach, the route map, and the ACK loop. One region ate the whole afternoon.',
 duration_s:8400,commits:3,is_ship:true,route:[0,0,1,0,2,2,1,0,3,3,2,0,0,1,4,0],
 harness:'Cursor',created_at:'2026-09-27T11:33:00Z',profiles:{github_handle:'morkeeth'}
};
const lead=ResultLead.guard(ResultLead.present(run,'view'),run);
assert.equal(lead.label,'Builder’s account');
assert.equal(lead.outcome,run.note);
assert.equal(lead.outcomeSource,'runs.note');
assert.equal(lead.sourceLine,'Evidence source: runs.note');
assert.equal(lead.duration,'2h 20m');
assert.ok(lead.limit.startsWith('Builder-authored account.'));
assert.notEqual(lead.label,'Observed outcome');

const fake={...lead,outcome:'Deep focus'};
assert.throws(()=>ResultLead.guard(fake,run),/result source guard/);
const saved=ResultLead.guard;
ResultLead.guard=value=>value;
assert.equal(ResultLead.guard(fake,run).outcome,'Deep focus');
ResultLead.guard=saved;
assert.throws(()=>ResultLead.guard(fake,run),/result source guard/);

const page=html(run),body=page.slice(page.indexOf('<body>'));
const accountAt=body.indexOf('Builder’s account'),sourceAt=body.indexOf('Evidence source: runs.note'),limitAt=body.indexOf('<strong>Limit:</strong>'),durationAt=body.indexOf('>2h 20m<');
assert.ok(accountAt>0&&sourceAt>accountAt&&limitAt>sourceAt&&durationAt>limitAt);
assert.ok(page.includes('<meta property="og:title" content="'+run.note+'">'));
assert.equal(page.includes('agentgrinder.vercel.app'),false);

const image=new ImageResponse(card(run),{width:1200,height:630});
const bytes=Buffer.from(await image.arrayBuffer());
assert.equal(bytes.subarray(1,4).toString(),'PNG');
assert.equal(bytes.readUInt32BE(16),1200);assert.equal(bytes.readUInt32BE(20),630);
await writeFile(new URL('strive-result-first-og.png',out),bytes);
const design=await readFile(new URL('../site/design.css',import.meta.url),'utf8');
const feed=await readFile(new URL('../site/feed.css',import.meta.url),'utf8');
const appSource=await readFile(new URL('../site/index.html',import.meta.url),'utf8');
const appStyles=(appSource.match(/<style>([\s\S]*?)<\/style>/)||[])[1]||'';
const styled=page.replace('</head>','<style>'+design+'\n'+feed+'</style></head>');
await writeFile(new URL('strive-result-first-run.html',out),styled);
const resultSource=(await readFile(new URL('../site/result-lead.js',import.meta.url),'utf8')).replaceAll('</script>','<\\/script>');
const sharing=(await readFile(new URL('../site/sharing.js',import.meta.url),'utf8')).replaceAll('__BRAND__','STRIVE').replaceAll('</script>','<\\/script>');
const share=`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>${design}\n${feed}\n${appStyles}body{padding:16px}.share-studio{display:block}.post-preview canvas{width:100%;height:auto}</style><main id="slot"></main><div id="status"></div><script>${resultSource}</script><script>${sharing}</script><script>GrinderSharing.mount({run:${JSON.stringify(run)},slot:document.getElementById('slot'),status:m=>document.getElementById('status').textContent=m});</script>`;
await writeFile(new URL('strive-result-first-share.html',out),share);
console.log('Result lead passed: Builder’s account → runs.note → limit → 2h 20m; guard went red, was restored, and OG rendered.');
