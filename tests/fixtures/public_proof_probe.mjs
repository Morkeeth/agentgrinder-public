import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

process.env.AGENTGRINDER_SUPABASE_URL||='http://localhost:54321';
process.env.AGENTGRINDER_SUPABASE_ANON_KEY||='local-development-only';

const {proofHtml,neutralProofHtml,proofFacts}=await import('../../server/public-proof.mjs');
const run=JSON.parse(readFileSync(new URL('./public_proof_run.json',import.meta.url),'utf8'));
const origin='http://127.0.0.1:8002';
const page=proofHtml(run,{origin});
const facts=proofFacts(run.code_route);

assert.equal(facts.projects.length,4);
assert.equal(facts.stops.length,4);
assert.equal(facts.measured.length,4);
for(const text of [
 'Recorded agent run',
 'A measured four-project release run',
 '4 projects',
 '4 recorded checkpoints',
 '4/4 checkpoints are recorded as measured',
 'Route evidence',
 'Author-reported outcomes',
 'Linked receipts',
 'Open the public run',
 '/r/11111111-1111-1111-1111-111111111111',
])assert.ok(page.includes(text),`missing ${text}`);
assert.ok(!page.includes('Agent decision that changed the route'));
assert.ok(!page.includes('Human goal'));

const neutral=neutralProofHtml(run.id,{origin});
for(const privateText of [run.title,'agentgrinder-public','State renderer repair verified']){
 assert.ok(!neutral.includes(privateText),`neutral proof leaked ${privateText}`);
}
assert.ok(neutral.includes('noindex'));
console.log('PASS public proof separates recorded route evidence from author-reported outcomes');
