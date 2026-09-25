// site/home.js: the week strip, builders, popular runs and rows, from real-shaped data only.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const H=createRequire(import.meta.url)('../site/home.js');
const DAY=86400000, now=new Date(2026,8,25,12).getTime();
const at=(d,h=10)=>new Date(new Date(2026,8,25+d,h).getTime()).toISOString();
// Week: 14 days, runs only behind (and today), events only ahead (and today).
const runs=[{id:'a',profile_id:'p1',visibility:'public',created_at:at(0)},{id:'b',profile_id:'p1',visibility:'public',created_at:at(-3)},{id:'c',profile_id:'p2',visibility:'public',created_at:at(-3)},{id:'old',profile_id:'p3',visibility:'public',created_at:at(-20)}];
const events=[{id:'e1',title:'Sunday <b>builders</b>',starts_at:at(2,15),place:'Paris',club:{name:'Club & co'},going:3},{id:'past',title:'x',starts_at:at(-2)}];
const w=H.week(runs,events,now);
assert.equal(w.days.length,14);
assert.equal(w.days.find(d=>d.t===w.today).runs,1);
assert.equal(w.days.reduce((a,d)=>a+d.runs,0),3,'the 20-day-old run is off the strip');
assert.equal(w.days.reduce((a,d)=>a+d.events.length,0),1,'a past event is not shown ahead');
const html=H.weekHtml(runs,events,now);
assert.match(html,/3 public runs in the last 7 days · 1 event in the next 7/);
assert.ok(!html.includes('<b>builders</b>'),'event titles are escaped');
assert.match(H.weekHtml([],[],now),/No public runs in the last 7 days · no events in the next 7/);
// Rows escape everything they print.
const row=H.eventRow(events[0]);
assert.ok(row.includes('Sunday &lt;b&gt;builders&lt;/b&gt;')&&row.includes('Club &amp; co')&&row.includes('3 going'));
assert.ok(H.clubRow({id:'c"1',name:'<x>',members:1}).includes('&lt;x&gt;')&&H.clubRow({id:'c',name:'A',members:1}).includes('1 member<'));
// Builders: public only, most runs first, one row each.
const b=H.builders([...runs,{id:'priv',profile_id:'p9',visibility:'private',created_at:at(0)}]);
assert.deepEqual(b.map(x=>x.run.profile_id),['p1','p2','p3']);
assert.equal(b[0].n,2);
// Popular: most XUDOS first, then newest.
assert.deepEqual(H.popular(runs,{c:2,b:2}).map(r=>r.id),['b','c','a','old']);
assert.deepEqual(H.popular(runs,{old:5}).map(r=>r.id)[0],'old');
console.log('Home checks passed.');
