import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {runtimeConfig} from '../server/runtime-config.mjs';

const read = path => readFile(new URL('../' + path, import.meta.url), 'utf8');
const [index, publicRun, health, agentApi, a2a, publicConfigText] = await Promise.all([
  read('site/index.html'),
  read('server/public-run.mjs'),
  read('api/health.js'),
  read('agentgrinder/agent_api.py'),
  read('agentgrinder/a2a_client.py'),
  read('server/public-config.json'),
]);
const publicConfig = JSON.parse(publicConfigText);

function requireText(source, text, location, purpose) {
  assert.ok(
    source.includes(text),
    `${location} is missing ${purpose}: ${JSON.stringify(text)}`,
  );
}

assert.equal(publicConfig.SB_SCHEMA, 'strava', 'server/public-config.json must pin SB_SCHEMA to strava');
requireText(index, 'const SB_SCHEMA="strava";', 'site/index.html', 'the browser schema pin');
requireText(index, 'db:{schema:SB_SCHEMA}', 'site/index.html', 'the browser schema selection');
requireText(index, 'storageKey:"agentic-strava-auth"', 'site/index.html', 'the Strava-only auth storage key');
requireText(publicRun, '"Accept-Profile":config.SB_SCHEMA', 'server/public-run.mjs', 'the public read schema header');
requireText(health, "'Accept-Profile':'strava'", 'api/health.js', 'the health read schema header');
requireText(agentApi, "'Content-Profile':DEFAULT_SCHEMA", 'agentgrinder/agent_api.py', 'the agent write schema header');
requireText(a2a, '"Accept-Profile": DEFAULT_SCHEMA', 'agentgrinder/a2a_client.py', 'the CLI read schema header');

const anonKey = 'e30.' + Buffer.from(JSON.stringify({role: 'anon'})).toString('base64url') + '.signature';
const config = runtimeConfig({
  VERCEL: '1',
  AGENTGRINDER_SUPABASE_URL: 'https://project-ref.supabase.co',
  AGENTGRINDER_SUPABASE_ANON_KEY: anonKey,
  STRAVA_ORIGIN: 'https://strava.example',
});
assert.equal(config.SB_SCHEMA, 'strava');
assert.equal(config.ORIGIN, 'https://strava.example');

console.log('PASS: hosted dry run pins browser, server, CLI and agent traffic to the strava schema.');
console.log('No network request or production write was made.');
