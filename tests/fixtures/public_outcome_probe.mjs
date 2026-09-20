// The public share page must carry declared receipts safely for a signed-out reader.
// A stored row is untrusted: it was written through the agent upload endpoint.
import assert from 'node:assert/strict';
process.env.AGENTGRINDER_SUPABASE_URL ||= 'http://localhost:54321';
process.env.AGENTGRINDER_SUPABASE_ANON_KEY ||= 'local-development-only';
const {html, readPublic} = await import('../../server/public-run.mjs');
const base = {id:'11111111-1111-1111-1111-111111111111', title:'Night run', visibility:'public',
  profiles:{handle:'oscar'}, harness:'Claude Code', commits:2};

const good = html({...base, repo_url:'https://github.com/Morkeeth/agentgrinder-public',
  shipped:['My runs keeps the primary rail'],
  receipts:[{label:'PR 58', url:'https://github.com/Morkeeth/agentgrinder-public/pull/58'}],
  artifact_url:'https://agentic-strava.vercel.app/', image_url:'https://agentic-strava.vercel.app/c.png'});
assert.ok(good.includes('Said by the uploader, not measured'), 'declared block missing');
assert.ok(good.includes('github.com/Morkeeth/agentgrinder-public/pull/58'), 'receipt link missing');
assert.ok(good.includes('My runs keeps the primary rail'), 'shipped line missing');
assert.ok(good.includes('Open the demo') && good.includes('Open the screenshot'), 'links missing');
assert.ok(!/<img[^>]+https:\/\/agentic-strava[^>]*>/.test(good), 'a remote image must never be embedded');
assert.ok(!good.includes('og:image" content="https://agentic-strava.vercel.app/c.png'), 'og:image must stay the generated card');

const hostile = html({...base,
  title:'</title><script>alert(1)</script>',
  repo_url:'https://github.com/a/b" onmouseover="alert(1)',
  shipped:['<img src=x onerror=alert(1)>', 'x'.repeat(400)],
  receipts:[{label:'<script>bad</script>', url:'javascript:alert(1)'},
            {label:'ok', url:'https://ok.example.com/a'},
            {label:'ok2', url:'http://insecure.example.com/a'}],
  artifact_url:'https://x.com/a b', image_url:'https://x.com/a.svg'});
assert.ok(!hostile.includes('<script>'), 'script tag rendered');
assert.ok(!hostile.includes('onerror=alert(1)>'), 'raw markup rendered');
assert.ok(!hostile.includes('onmouseover'), 'attribute broke out of href');
assert.ok(!hostile.includes('javascript:'), 'javascript link rendered');
assert.ok(!hostile.includes('insecure.example.com'), 'http link rendered');
assert.ok(!hostile.includes('a.svg'), 'svg rendered');
assert.ok(hostile.includes('https://ok.example.com/a'), 'a valid receipt beside bad ones was dropped');
assert.ok(!/<li>x{200,}/.test(hostile), 'shipped line not truncated');

// A private row must still render nothing, even with receipts on it.
const rows = [{...base, visibility:'private', repo_url:'https://github.com/a/b'}];
const fake = async () => ({ok:true, json: async () => rows});
assert.equal(await readPublic(base.id, fake), null, 'a non-public row must never reach the page');
console.log('PASS public share page: declared receipts render, hostile stored values are neutralised, no remote image, private rows stay hidden');
