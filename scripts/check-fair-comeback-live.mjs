/**
 * Real local cross-product walk: Free Lunch PR14 issues the challenge and day-two capability;
 * the shipped STRIVE page reads a real session file, creates a real PGlite-backed card, and its
 * production confirmation module returns the proof. Only the clocks and public STRIVE host are
 * substituted: the browser maps Free Lunch's public target to this local checkout.
 *
 *   FAIR_REPO=~/CODE/.worktrees/sun-0927-fl \
 *   FAIR_COMEBACK_OUT=/tmp/strive-fair-comeback node scripts/check-fair-comeback-live.mjs
 */
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {serve as startStrive} from './dropin-dev-server.mjs';

const ROOT=fileURLToPath(new URL('..',import.meta.url));
const FAIR_REPO=resolve(process.env.FAIR_REPO||'');
if(!FAIR_REPO) throw new Error('Set FAIR_REPO to the completed Free Lunch PR14 checkout.');
const out=resolve(process.env.FAIR_COMEBACK_OUT||join(tmpdir(),'strive-fair-comeback'));
mkdirSync(out,{recursive:true});
execFileSync(process.execPath,[join(ROOT,'scripts/build-site.mjs')],{cwd:ROOT,stdio:'inherit'});

const [{startFairServer},{RETURN_GAP_MS},{chromium}]=await Promise.all([
 import(pathToFileURL(join(FAIR_REPO,'server/start.mjs')).href),
 import(pathToFileURL(join(FAIR_REPO,'proof/rules.mjs')).href),
 import(pathToFileURL(join(FAIR_REPO,'node_modules/@playwright/test/index.mjs')).href),
]);
const SECRET='b'.repeat(64);
let now=Date.parse('2026-09-26T12:00:00.000Z');
const fair=await startFairServer({
 env:{FAIR_DB_PATH:join(mkdtempSync(join(tmpdir(),'fair-strive-comeback-')),'proof.sqlite'),FAIR_PORT:'0',FAIR_HOST:'127.0.0.1',FAIR_SIGNALS:'0',FAIR_PRODUCT_SECRET_STRIVE:SECRET},
 clock:()=>now,
});
const strive=await startStrive({listen:0,fairEnv:{FAIR_URL:fair.url,FAIR_PRODUCT_SECRET_STRIVE:SECRET}});
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:2});
const fairPage=await context.newPage();
const strivePage=await context.newPage();
const rows=[];

const fairCookie=async()=> (await context.cookies(fair.url)).map(c=>`${c.name}=${c.value}`).join('; ');

async function goTarget(){
 await fairPage.goto(`${fair.url}/try?id=strive`,{waitUntil:'domcontentloaded'});
 const response=await fetch(`${fair.url}/go?id=strive`,{redirect:'manual',headers:{cookie:await fairCookie()}});
 assert.equal(response.status,302);
 return new URL(response.headers.get('location'));
}

async function card(kind){
 const target=await goTarget();
 const challengeId=target.searchParams.get('fair_challenge');
 const returnToken=target.searchParams.get('fair_return_token');
 assert.ok(challengeId,`${kind}: no challenge`);
 if(kind==='fair-witnessed') assert.equal(returnToken,null,'day one carried a return token');
 else assert.match(returnToken,/^[a-f0-9]{64}$/,`${kind}: no day-two capability`);

 const local=new URL(strive.origin+'/?post');
 for(const [key,value] of target.searchParams) local.searchParams.append(key,value);
 let sent=null;
 await strivePage.route('**/api/fair/confirm',async route=>{
  const body=route.request().postDataJSON();
  sent=body;
  // PGlite uses its wall clock. Move only this just-created test row onto the same controlled
  // clock as Free Lunch before STRIVE's production action-window check reads it.
  await strive.db.query('update strava.dropin_links set created_at=$1 where id=$2',[new Date(now).toISOString(),body.id]);
  await route.continue();
 });
 const confirmResponse=strivePage.waitForResponse(r=>r.url().endsWith('/api/fair/confirm')&&r.request().method()==='POST');
 await strivePage.goto(local.href,{waitUntil:'domcontentloaded'});
 await strivePage.locator('#drop-zone').waitFor({state:'visible'});
 const cleaned=new URL(strivePage.url());
 assert.equal(cleaned.searchParams.has('fair_challenge'),false,'challenge remained in the visible URL');
 assert.equal(cleaned.searchParams.has('fair_return_token'),false,'return capability remained in the visible URL');
 await strivePage.setInputFiles('#drop-file',join(ROOT,'samples/dropin/claude-edge.jsonl'));
 await strivePage.locator('.drop-result .fc').waitFor({state:'visible'});
 await strivePage.fill('#drop-title',kind==='fair-return'?'Returned to STRIVE on day two':'Made a STRIVE card on day one');
 await strivePage.click('#drop-next');
 await strivePage.locator('.post-pane[data-pane="2"]:not([hidden])').waitFor();
 await strivePage.click('label.aud-opt:has(input[value="unlisted"])');
 await strivePage.click('#drop-continue');
 await strivePage.locator('#drop-url').waitFor({state:'visible'});
 const response=await confirmResponse;
 const confirmed=await response.json();
 assert.equal(response.status(),200,JSON.stringify(confirmed));
 assert.equal(confirmed.kind,kind,JSON.stringify(confirmed));
 assert.equal(sent.challengeId,challengeId);
 if(kind==='fair-return') assert.equal(sent.returnToken,returnToken,'STRIVE changed the day-two capability');
 else assert.equal('returnToken' in sent,false,'STRIVE invented a day-one return capability');
 const viewport=await strivePage.evaluate(()=>({innerWidth,scrollWidth:document.documentElement.scrollWidth,stored:StriveFair.pending()}));
 assert.ok(viewport.scrollWidth<=viewport.innerWidth,`390 px overflow: ${JSON.stringify(viewport)}`);
 assert.equal(viewport.stored,null,'the completed confirmation remained pending');
 const shot=join(out,`${kind}-strive-390.png`);
 await strivePage.screenshot({path:shot,fullPage:true});
 rows.push({kind,challengeId,returnToken:returnToken?'present':'absent',sentReturnToken:Boolean(sent.returnToken),status:response.status(),viewport,shot});
 await strivePage.unroute('**/api/fair/confirm');
}

try{
 await card('fair-witnessed');
 now+=RETURN_GAP_MS;
 await card('fair-return');
 const state=await (await fetch(`${fair.url}/api/state?project=strive`,{headers:{cookie:await fairCookie()}})).json();
 const checkpoint=await (await fetch(`${fair.url}/api/proof/checkpoint`)).json();
 assert.equal(state.snapshot.witnessedUses,1);
 assert.equal(state.snapshot.returns,1);
 assert.equal(checkpoint.types['proof.redeemed'],2);
 assert.equal(checkpoint.verified,true);
 const result={observedAt:new Date().toISOString(),freeLunchHead:execFileSync('git',['rev-parse','HEAD'],{cwd:FAIR_REPO,encoding:'utf8'}).trim(),striveHead:execFileSync('git',['rev-parse','HEAD'],{cwd:ROOT,encoding:'utf8'}).trim(),controlledClock:new Date(now).toISOString(),rows,counts:{witnessedUses:state.snapshot.witnessedUses,returns:state.snapshot.returns,returningTeams:state.snapshot.returningTeams},checkpointVerified:checkpoint.verified};
 writeFileSync(join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
 process.stdout.write(JSON.stringify(result,null,2)+'\n');
}finally{
 await context.close();await browser.close();
 await new Promise(r=>strive.server.close(r));await strive.db.close();
 await fair.close();
}
