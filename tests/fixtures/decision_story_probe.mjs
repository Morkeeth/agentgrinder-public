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
 'Challenge the fleet handoff',
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
assert.ok(continuation.searchParams.get('body').includes('carry the measured route'));
assert.ok(continuation.searchParams.get('body').includes('State renderer repaired'));

const neutral=neutralDecisionHtml(run.id,{origin});
assert.ok(neutral.includes('not public'));
for(const privateText of [run.title,'agentgrinder-public','fleet-ops','State renderer repaired']){
 assert.ok(!neutral.includes(privateText),`neutral page leaked ${privateText}`);
}

console.log('PASS decision story uses the supplied route and preserves context in its one continuation');
