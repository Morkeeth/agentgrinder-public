// Public share page and OG card must use the same Code Route data.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
process.env.AGENTGRINDER_SUPABASE_URL ||= 'http://localhost:54321';
process.env.AGENTGRINDER_SUPABASE_ANON_KEY ||= 'local-development-only';
const {html, card} = await import('../../server/public-run.mjs');
const manifest = JSON.parse(readFileSync(new URL('./code_route_multi_project_manifest.json', import.meta.url), 'utf8'));
// Build via Python validation path to keep the fixture identical to export bytes.
import {execFileSync} from 'node:child_process';
const code_route = JSON.parse(execFileSync('python3', ['-c',
  'import json,sys; from agentgrinder.code_route import from_manifest; print(json.dumps(from_manifest(json.load(sys.stdin))))'],
  {input: JSON.stringify(manifest), encoding: 'utf8'}));

const run = {
  id: '11111111-1111-1111-1111-111111111111',
  title: 'Multi-project night',
  visibility: 'public',
  profiles: {handle: 'oscar'},
  harness: 'Cursor + Claude CLI + Codex',
  commits: 1,
  files_touched: 10,
  code_route,
};

const page = html(run);
assert.ok(page.includes('Code Route'), 'page missing Code Route');
assert.ok(page.includes('zup') && page.includes('agentgrinder-public') && page.includes('mountain-of-helicon'));
assert.ok(page.includes('measured') && page.includes('declared'));
assert.ok(page.includes('cursor') && page.includes('claude-cli') && page.includes('codex'));
assert.ok(page.includes('absent') && page.includes('grok-bot'));
assert.ok(page.includes('projects touched') || page.includes('Projects touched') || page.includes('3 projects touched'));

const og = card(run);
assert.equal(og.type, 'div');
const dump = JSON.stringify(og);
assert.ok(dump.includes('Code Route') || dump.includes('projects touched'), 'OG card missing Code Route label');
assert.ok(page.includes('code-route-projects'), 'page missing project list');
assert.ok(!page.includes('agentgrinder-…') && !page.includes('mountain-of-h…'), 'page still ellipsizes lanes');
assert.ok(dump.includes('zup') && dump.includes('agentgrinder-public') && dump.includes('mountain-of-helicon'), 'OG card missing full project names');
assert.ok(dump.includes('1 · zup') || dump.includes('1 ·'), 'OG card missing numbered lanes');
console.log('PASS public Code Route page and share image use the same route data');
