// Exercise site/fair.js as two browser tabs sharing one origin. This proves the CLI-opened tab can
// inherit the pending Free Lunch visit, while the 15-minute expiry and URL stripping stay explicit.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';

const source=await readFile(new URL('../site/fair.js',import.meta.url),'utf8');
const CH='11111111-2222-4333-8444-555555555555';
const TOKEN='return.token_1234567890+/=';
const ACTION='aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee';
const shared=new Map();
const storage={
 getItem:key=>shared.has(key)?shared.get(key):null,
 setItem:(key,value)=>shared.set(key,String(value)),
 removeItem:key=>shared.delete(key),
};
let now=1_800_000_000_000;
const Clock=class extends Date { static now(){return now;} };

function tab(href,response={status:200,body:{confirmed:true,kind:'fair-return'}}){
 let replaced=null,request=null;
 const root={
  location:{href},localStorage:storage,
  history:{state:null,replaceState(_state,_title,url){replaced=url;}},
 };
 const fetch=async(_url,options)=>{
  request=JSON.parse(options.body);
  return {status:response.status,json:async()=>response.body};
 };
 vm.runInNewContext(source,{window:root,globalThis:root,URL,Date:Clock,fetch,JSON,Number});
 return {root,replaced,get request(){return request;}};
}

// Capture strips both capabilities but keeps unrelated query text and the hash.
const first=tab(`https://strive.test/connect?via=the-fair&fair_challenge=${CH}&fair_return_token=${encodeURIComponent(TOKEN)}#capture`);
assert.equal(first.replaced,'/connect?via=the-fair#capture');
assert.equal(first.root.StriveFair.pending(),CH);
assert.ok(!first.replaced.includes('fair_return_token'));

// The CLI opens a new tab. Its separate JS context sees the same origin-wide pending visit and
// sends the opaque return token unchanged.
const opened=tab('https://strive.test/?post');
assert.equal(opened.root.StriveFair.pending(),CH);
assert.deepEqual(await opened.root.StriveFair.confirm('link',ACTION,null,'a'.repeat(64)),{confirmed:true,kind:'fair-return'});
assert.equal(opened.request.challengeId,CH);
assert.equal(opened.request.returnToken,TOKEN);
assert.equal(shared.size,0,'a confirmed visit clears challenge and return token');

// An early return is exposed as Free Lunch's code and closes a 409 visit without leaking its text.
const early=tab(`https://strive.test/connect?fair_challenge=${CH}&fair_return_token=${encodeURIComponent(TOKEN)}`,{status:409,body:{confirmed:false,code:'TOO_EARLY'}});
assert.deepEqual(await early.root.StriveFair.confirm('link',ACTION,null,'a'.repeat(64)),{confirmed:false,code:'TOO_EARLY'});
assert.equal(early.request.returnToken,TOKEN);
assert.equal(shared.size,0);

// Expired and malformed state is removed, including its paired capability.
const expiring=tab(`https://strive.test/connect?fair_challenge=${CH}&fair_return_token=${encodeURIComponent(TOKEN)}`);
now+=900001;
assert.equal(expiring.root.StriveFair.pending(),null);
assert.equal(shared.size,0);
shared.set('strive_fair_challenge','not-json');
shared.set('strive_fair_return_token',JSON.stringify({token:TOKEN,until:now+1000}));
assert.equal(expiring.root.StriveFair.pending(),null);
assert.equal(shared.size,0);

console.log('Free Lunch browser referral checks passed.');
