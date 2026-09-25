import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

process.env.AGENTGRINDER_SUPABASE_URL||='http://localhost:54321';
process.env.AGENTGRINDER_SUPABASE_ANON_KEY||='local-development-only';

const {decisionHtml,neutralDecisionHtml,routeFacts}=await import('../../server/decision-story.mjs');
const run=JSON.parse(readFileSync(new URL('./full-night-run-code-route.json',import.meta.url),'utf8'));
const origin='http://127.0.0.1:8002';
const canonical=`${origin}/d/${run.id}`;
const page=decisionHtml(run,{preview:true,origin});
const facts=routeFacts(run.code_route);

assert.equal(facts.stops.length,9);
assert.equal(facts.measured.length,9);
assert.equal(facts.dense.id,'agentgrinder-public');
assert.equal(facts.denseCount,3);
assert.equal(facts.handoffs.length,3);
assert.equal(facts.finish.id,'fleet-merge');
assert.equal(facts.finishProject.id,'fleet-ops');

for(const text of [
 'Human goal',
 'Four repos shipped in one night',
 'Agent decision that changed the route',
 'Carry the work beyond agentgrinder-public to fleet-ops.',
 'agentgrinder-public held 3 of 9 stops',
 '3 handoffs carried it onward',
 '9/9 measured stops',
 'Code Route deployed and used',
 'Legacy ruling crash reproduced',
 'State renderer repaired',
 'Challenge the fleet-ops handoff',
 'GitHub sign-in is required to post',
 canonical,
])assert.ok(page.includes(text),`missing ${text}`);

assert.ok(page.includes('Local preview')&&page.includes('not a public run'));
assert.ok(!page.includes('tool calls'));
assert.ok(!page.includes('grok-bot'));
assert.ok(!page.includes('XUDOS'));

const href=page.match(/<a class="action" href="([^"]+)"/)?.[1].replaceAll('&amp;','&');
assert.ok(href,'continuation URL missing');
const continuation=new URL(href);
assert.equal(continuation.hostname,'github.com');
assert.equal(continuation.pathname,'/Morkeeth/agentgrinder-public/issues/new');
assert.ok(continuation.searchParams.get('body').includes(canonical));
assert.ok(continuation.searchParams.get('body').includes('Decision to challenge: Carry the work beyond agentgrinder-public to fleet-ops.'));
assert.ok(continuation.searchParams.get('body').includes('State renderer repaired'));

const neutral=neutralDecisionHtml(run.id,{origin});
assert.ok(neutral.includes('not public'));
for(const privateText of [run.title,'agentgrinder-public','fleet-ops','State renderer repaired']){
 assert.ok(!neutral.includes(privateText),`neutral page leaked ${privateText}`);
}

console.log('PASS decision story uses the supplied route and preserves context in its one continuation');

// Any run's own route, not one run's names: a two-project route says its own projects.
{
 const {decisionHtml:render,hasDecisionStory}=await import('../../server/decision-story.mjs');
 const other={id:'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee',title:'Other night',code_route:{v:1,
  projects:[{id:'api',label:'api'},{id:'web',label:'web'}],
  stops:[{id:'s1',project:'api',kind:'edit',label:'Schema',basis:'measured',evidence:['migration ran']},{id:'s2',project:'api',kind:'check',label:'Tests',basis:'measured'},{id:'s3',project:'web',kind:'deploy',label:'Shipped',basis:'measured',evidence:['deploy ok']}],
  connectors:[{from:'s2',to:'s3',kind:'handoff'}],finish:{stop:'s3'}}};
 assert.ok(hasDecisionStory(other));
 const html=render(other,{origin:'https://strive.test'});
 // The challenge is filed in STRIVE's own repository; nothing else may name another run's projects.
 const story=html.replaceAll('github.com/Morkeeth/agentgrinder-public/issues/new','');
 for(const leak of ['fleet-ops','agentgrinder-public','strive-live','fleet-fail'])assert.ok(!story.includes(leak),'hard-coded '+leak);
 assert.ok(html.includes('Carry the work beyond api to web.')&&html.includes('Challenge the web handoff'));
 // A public run with no Code Route has no decision story (api/decision.js sends it to /r/<id>).
 assert.equal(hasDecisionStory({id:other.id,title:'x',code_route:null}),false);
 console.log('PASS decision story is derived from any run\'s own route; a run without one goes to /r/');
}

// Edges a stranger must never see as false or empty copy (cold review, 26 Sep).
{
 const {decisionHtml:render,hasDecisionStory}=await import('../../server/decision-story.mjs');
 const text=h=>h.replace(/<[^>]+>/g,' ').replace(/\s+/g,' ');
 const edge={id:'cccccccc-dddd-4eee-8fff-000000000000',title:'Edge night',code_route:{v:1,
  projects:[{id:'a',label:'alpha'},{id:'b',label:'beta'}],
  stops:[{id:'x',project:'a',kind:'edit',label:'X',basis:'measured',evidence:['ran']},{id:'y',project:'b',kind:'edit',label:'Y',basis:'declared'}],
  connectors:[]}};
 assert.ok(hasDecisionStory(edge));
 const page=text(render(edge,{origin:'https://strive.test'}));
 // 3: no unique busiest project, no handoffs, mixed basis: no bare "." insight line.
 const html=render(edge,{origin:'https://strive.test'});
 assert.ok(!/<p class="because">\s*\.?\s*<\/p>/.test(html),'bare or empty insight line');
 assert.ok(!/\s\.\s*"/.test(html.match(/name="description" content="[^"]*"/)?.[0]||''),'description ends in a bare "."');
 // 4: no finish stop: no "Recorded finish" and no finish line.
 assert.ok(!page.includes('Recorded finish')&&!page.includes('Finish ·'),'finish printed without a finish stop');
 assert.ok(!/recorded finish/i.test(page),'decision names a finish that does not exist');
 // 5: "measured" only when a stop was measured; a route with no measured stop tells no decision story.
 assert.ok(!/every stop was measured|measured route/.test(page),'claims measured beyond what was measured');
 const declared={...edge,code_route:{...edge.code_route,stops:edge.code_route.stops.map(s=>({...s,basis:'declared'}))}};
 assert.equal(hasDecisionStory(declared),false,'a route with no measured stop is not a decision story');
 console.log('PASS edges: no bare insight, no invented finish, no unearned "measured"');
}

// Second cold pass (Grok, 26 Sep): five more places a sentence could claim what the route does not carry.
{
 const {decisionHtml:render}=await import('../../server/decision-story.mjs');
 const id='dddddddd-eeee-4fff-8000-111111111111';
 const R=(route)=>render({id,title:'T',code_route:{v:1,...route}},{origin:'https://strive.test'});
 const text=h=>h.replace(/<[^>]+>/g,' ').replace(/\s+/g,' ');
 const draft=h=>decodeURIComponent((h.match(/issues\/new\?[^"]*body=([^"&]*)/)||[])[1]||'').replace(/\+/g,' ');
 // 1. An empty lane is not a project the route crossed.
 let h=R({projects:[{id:'a',label:'alpha'},{id:'g',label:'gamma'}],stops:[{id:'1',project:'a',kind:'edit',label:'One',basis:'measured'},{id:'2',project:'a',kind:'edit',label:'Two',basis:'measured'}],connectors:[]});
 assert.ok(!/across 2 projects/.test(text(h)),'counted an empty lane as a project');
 // 2. A stop without a label never prints "undefined" or an empty finish name.
 h=R({projects:[{id:'a',label:'alpha'}],stops:[{id:'1',project:'a',kind:'edit',label:'One',basis:'measured'},{id:'2',project:'a',kind:'edit',basis:'measured'}],connectors:[],finish:{stop:'2'}});
 assert.ok(!text(h).includes('undefined')&&!/Finish · \s*(<|$)/.test(h.replace(/<strong>\s*<\/strong>/,'<strong></strong>'))&&!h.includes('Finish · <strong></strong>'),'undefined or empty finish label');
 // 3. "beyond A to B" only when B comes after A's stretch.
 h=R({projects:[{id:'a',label:'alpha'},{id:'b',label:'beta'}],stops:[{id:'f',project:'b',kind:'edit',label:'Fin',basis:'measured'},{id:'1',project:'a',kind:'edit',label:'One',basis:'measured'},{id:'2',project:'a',kind:'edit',label:'Two',basis:'measured'}],connectors:[],finish:{stop:'f'}});
 assert.ok(!text(h).includes('beyond alpha to beta'),'decision reverses the route order');
 // 4. "Last measured stop" only for a finish that is measured and is the last measured stop.
 h=R({projects:[{id:'a',label:'alpha'},{id:'b',label:'beta'}],stops:[{id:'1',project:'a',kind:'edit',label:'One',basis:'measured'},{id:'2',project:'a',kind:'edit',label:'Two',basis:'measured'},{id:'f',project:'b',kind:'edit',label:'Fin',basis:'declared'}],connectors:[],finish:{stop:'f'}});
 assert.ok(!draft(h).includes('Last measured stop: Fin'),'declared finish called the last measured stop');
 // 5. "Challenge the X handoff" only when a handoff reaches that project.
 assert.ok(!text(h).includes('Challenge the beta handoff'),'handoff named without a handoff connector');
 console.log('PASS second edges: lanes, labels, order, last measured stop, handoff');
}
