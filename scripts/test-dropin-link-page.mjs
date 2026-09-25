// The /l/ page as a reader on X meets it: the ask lands on the drop zone, and the unfurl title is
// the typed title, or, for a ghost run with none, the ghost's own sentence.
import assert from 'node:assert/strict';
import * as L from '../server/dropin-link.mjs';

const origin = 'https://strive.test';
const ghost = { id: '93979dfd-bace-43a8-8f34-0e5574afc934', harness: 'Claude Code', turns_typed: 2, tool_calls: 400, files_touched: 3, commits: 1, duration_s: 47100, started_hour: 23, rhythm: [1, 2], route: null, created_at: '2026-09-25T10:00:00Z' };
const page = (row) => L.linkHtml(row, { origin });
const og = (html) => html.match(/<meta property="og:title" content="([^"]*)">/)[1];
const tw = (html) => html.match(/<meta name="twitter:title" content="([^"]*)">/)[1];

// The ask: one tap from the maker's number to the drop zone.
const typed = page({ ...ghost, title: 'Shipped the parser' });
assert.match(typed, /<a class="open" href="\/#drop-zone">Their agent ran 13h 5m alone\. Drop yours\.<\/a>/);
assert.ok(!typed.includes('<a class="open" href="/">'), 'the ask must not land on the top of the page');
assert.match(L.missingHtml(), /href="\/#drop-zone"/);

// A typed title always wins.
assert.equal(og(typed), 'Shipped the parser');
// No typed title: the drop-in's default, or nothing, unfurls as the ghost sentence.
for (const title of ['Claude Code session, 25 Sep', 'Claude Code session', '']) {
  const html = page({ ...ghost, title });
  assert.equal(og(html), '13h 5m while you slept', `untyped ${JSON.stringify(title)}`);
  assert.equal(tw(html), '13h 5m while you slept');
  assert.match(html, /<h1 class="fc-title">Claude Code session[^<]*<\/h1>/, 'the card keeps its own title');
}
// Not a ghost: the default title stays.
assert.equal(og(page({ ...ghost, duration_s: 600, title: 'Claude Code session, 25 Sep' })), 'Claude Code session, 25 Sep');
assert.equal(L.typedTitle({ harness: 'Codex', title: 'Codex session, 3 Oct' }), '');
assert.equal(L.typedTitle({ harness: 'Codex', title: 'Codex session notes' }), 'Codex session notes');
console.log('Link page: the ask lands on the drop zone; a ghost with no typed title unfurls as its sentence.');
