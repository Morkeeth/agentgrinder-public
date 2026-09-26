// Browser contract for the Free Lunch -> STRIVE -> Free Lunch comeback pair.
// Run the shipped IIFE in a small browser-shaped VM: this tests the address, tab storage and the
// exact request body without giving the test a second implementation of the capture logic.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('../site/fair.js',import.meta.url),'utf8');
const CH='11111111-2222-4333-8444-555555555555';
const TOKEN='a'.repeat(64);

function page(href){
 const values=new Map(),requests=[];
 const root={
  location:{href},
  history:{state:{kept:true},replaceState(state,_title,next){root.history.state=state;root.location.href=new URL(next,root.location.href).href;}},
  sessionStorage:{setItem:(k,v)=>values.set(k,String(v)),getItem:k=>values.get(k)??null,removeItem:k=>values.delete(k)},
 };
 const fetch=async(url,opts)=>{requests.push({url,body:JSON.parse(opts.body)});return {status:200,json:async()=>({confirmed:true,kind:'fair-return'})};};
 vm.runInNewContext(source,{window:root,globalThis:root,URL,fetch});
 return {root,values,requests};
}

// Day one keeps the challenge through the save flow, strips capabilities from the visible URL,
// and confirms without a token.
{
 const x=page(`https://strive.test/?via=the-fair&fair_challenge=${CH}&keep=yes#drop-zone`);
 assert.equal(x.root.location.href,'https://strive.test/?via=the-fair&keep=yes#drop-zone');
 assert.equal(x.root.StriveFair.pending(),CH);
 await x.root.StriveFair.confirm('link','aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee',null,'b'.repeat(64));
 assert.equal(x.requests.length,1);
 assert.equal(x.requests[0].body.challengeId,CH);
 assert.equal('returnToken' in x.requests[0].body,false);
 assert.equal('token' in x.requests[0].body,false);
}

// Day two stores challenge + capability as one tab-scoped visit and echoes the capability once.
{
 const x=page(`https://strive.test/?fair_return_token=${TOKEN}&via=the-fair&fair_challenge=${CH}&keep=yes`);
 assert.equal(x.root.location.href,'https://strive.test/?via=the-fair&keep=yes');
 assert.equal(x.root.StriveFair.pending(),CH);
 await x.root.StriveFair.confirm('link','aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee',null,'b'.repeat(64));
 assert.equal(x.requests.length,1);
 assert.equal(x.requests[0].body.challengeId,CH);
 assert.equal(x.requests[0].body.returnToken,TOKEN);
 assert.equal('fair_return_token' in x.requests[0].body,false);
 assert.equal(x.root.StriveFair.pending(),null,'a completed pair cannot confirm a second action');
 await x.root.StriveFair.confirm('link','bbbbbbbb-cccc-4ddd-8eee-ffffffffffff',null,'c'.repeat(64));
 assert.equal(x.requests.length,1,'the return capability is echoed on one intended confirmation only');
}

// A capability without its challenge is not paired with a stale visit and causes no request.
{
 const x=page(`https://strive.test/?fair_return_token=${TOKEN}&keep=yes`);
 assert.equal(x.root.location.href,'https://strive.test/?keep=yes');
 assert.equal(x.root.StriveFair.pending(),null);
 await x.root.StriveFair.confirm('link','aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee',null,'b'.repeat(64));
  assert.equal(x.requests.length,0);
}

// A malformed capability beside a valid challenge fails closed rather than being downgraded to
// an ordinary day-one confirmation.
{
 const x=page(`https://strive.test/?fair_challenge=${CH}&fair_return_token=broken`);
 assert.equal(x.root.StriveFair.pending(),null);
 await x.root.StriveFair.confirm('link','aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee',null,'b'.repeat(64));
 assert.equal(x.requests.length,0);
}

console.log('Free Lunch return browser checks passed.');
