// STRIVE's Free Lunch confirm against a REAL local Free Lunch server, with a test secret.
// Not run in CI: it needs a the-fair checkout. Usage:
//   FAIR_REPO=~/CODE/the-fair node scripts/check-fair-confirm-live.mjs   (run from the-fair's node_modules context is not needed)
import {mkdtempSync} from 'node:fs'; import {tmpdir} from 'node:os'; import {join} from 'node:path';
const FAIR_REPO=process.env.FAIR_REPO;if(!FAIR_REPO){console.error('Set FAIR_REPO to a the-fair checkout.');process.exit(2);}
const {startFairServer}=await import(FAIR_REPO+'/server/start.mjs');
const {confirm,linkTicket}=await import(new URL('../server/fair-confirm.mjs',import.meta.url).href);
const SECRET='t'.repeat(64);
const fair=await startFairServer({env:{FAIR_DB_PATH:join(mkdtempSync(join(tmpdir(),'w3a-')),'p.sqlite'),FAIR_PORT:'0',FAIR_HOST:'127.0.0.1',FAIR_SIGNALS:'0',FAIR_PRODUCT_SECRET_STRIVE:SECRET}});
let cookie=null;
const visitor=async(path,body)=>{const r=await fetch(fair.url+path,{method:body?'POST':'GET',headers:{...(body?{'content-type':'application/json'}:{}),...(cookie?{cookie}:{})},body:body?JSON.stringify(body):undefined});const s=r.headers.getSetCookie?.()[0];if(s)cookie=s.split(';')[0];return r.json()};
const LINK='aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee';
// STRIVE's database is a stub that says the link was just made; every Free Lunch call is real.
const fairCalls=[];
const fetchImpl=async(url,opts)=>{
 if(url.startsWith(fair.url)){fairCalls.push(url.replace(fair.url,''));return fetch(url,opts);}
 if(url.endsWith('/rpc/dropin_read')) return {ok:true,status:200,json:async()=>({id:LINK,created_at:new Date().toISOString()})};
 throw new Error('unexpected '+url);
};
const SB={SB_URL:'https://db.test',SB_KEY:'sb_publishable_x'};
const envOn={FAIR_URL:fair.url,FAIR_PRODUCT_SECRET_STRIVE:SECRET};
const req=(challengeId,ticket)=>({method:'POST',headers:{},body:{challengeId,kind:'link',id:LINK,ticket}});
try{
 const t0=Date.now();
 const visit=await visitor('/api/visit',{project:'strive'});
 console.log('visit challengeId:',visit.challengeId);
 // 1. Secret unset: off, zero requests to Free Lunch.
 const off=await confirm(req(visit.challengeId,linkTicket(LINK,envOn)),SB,{FAIR_URL:fair.url},fetchImpl);
 console.log((off.body.off&&fairCalls.length===0?'PASS':'FAIL'),'secret unset: off, Free Lunch requests =',fairCalls.length);
 // 2. Wrong secret: refused, no receipt.
 const envWrong={FAIR_URL:fair.url,FAIR_PRODUCT_SECRET_STRIVE:'w'.repeat(64)};
 const wrong=await confirm(req(visit.challengeId,linkTicket(LINK,envWrong)),SB,envWrong,fetchImpl);
 console.log((wrong.body.confirmed===false?'PASS':'FAIL'),'wrong secret refused:',JSON.stringify(wrong.body));
 // 2b. A stranger who knows the public link id but has no ticket: refused, nothing sent to Free Lunch.
 const before=fairCalls.length;
 const stranger=await confirm(req(visit.challengeId,null),SB,envOn,fetchImpl);
 console.log((stranger.status===404&&fairCalls.length===before?'PASS':'FAIL'),'link id without the ticket refused, Free Lunch requests added =',fairCalls.length-before);
 // 3. Genuine: fair-witnessed.
 const good=await confirm(req(visit.challengeId,linkTicket(LINK,envOn)),SB,envOn,fetchImpl);
 console.log((good.body.kind==='fair-witnessed'?'PASS':'FAIL'),'genuine confirm:',JSON.stringify(good.body),'after',Date.now()-t0,'ms');
 // 4. Replay: no second receipt.
 const again=await confirm(req(visit.challengeId,linkTicket(LINK,envOn)),SB,envOn,fetchImpl);
 const cp=await (await fetch(fair.url+'/api/proof/checkpoint')).json();
 console.log(((cp.types['proof.redeemed']??0)===1&&!again.body.confirmed?'PASS':'FAIL'),'replay: redeemed =',cp.types['proof.redeemed'],'second answer',JSON.stringify(again.body),'| chain verified:',cp.verified);
 const state=await visitor('/api/state?project=strive');
 console.log(((state.snapshot?.witnessedUses??state.witnessedUses)===1?'PASS':'FAIL'),'visitor sees witnessedUses =',state.snapshot?.witnessedUses??state.witnessedUses);
}finally{await fair.close();}
