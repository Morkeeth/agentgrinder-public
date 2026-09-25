// The /l/ page as a reader on X meets it: the ask lands on the drop zone, and the unfurl title is
// the card's own title. No ghost sentence (removed 25 Sep 2026).
import assert from 'node:assert/strict';
import * as L from '../server/dropin-link.mjs';

const origin = 'https://strive.test';
const row = { id: '93979dfd-bace-43a8-8f34-0e5574afc934', harness: 'Claude Code', turns_typed: 2, tool_calls: 400, files_touched: 3, commits: 1, duration_s: 47100, started_hour: 23, rhythm: [1, 2], route: null, created_at: '2026-09-25T10:00:00Z' };
const page = (r) => L.linkHtml(r, { origin });
const og = (html) => html.match(/<meta property="og:title" content="([^"]*)">/)[1];
const tw = (html) => html.match(/<meta name="twitter:title" content="([^"]*)">/)[1];

// The ask: one tap from the maker's number to the drop zone.
const typed = page({ ...row, title: 'Shipped the parser' });
assert.match(typed, /<a class="open" href="\/#drop-zone">They logged 1 commit\. Drop yours\.<\/a>/);
assert.ok(!typed.includes('<a class="open" href="/">'), 'the ask must not land on the top of the page');
assert.match(L.missingHtml(), /href="\/#drop-zone"/);

// A typed title always wins.
assert.equal(og(typed), 'Shipped the parser');
// No typed title: the card's own default title unfurls, never a ghost sentence.
const untyped = page({ ...row, title: 'Claude Code session, 25 Sep' });
assert.equal(og(untyped), 'Claude Code session, 25 Sep');
assert.equal(tw(untyped), 'Claude Code session, 25 Sep');
assert.ok(!/ghost|while you slept|alone/i.test(untyped), 'no ghost framing on the link page');
assert.equal(L.typedTitle({ harness: 'Codex', title: 'Codex session, 3 Oct' }), '');
assert.equal(L.typedTitle({ harness: 'Codex', title: 'Codex session notes' }), 'Codex session notes');
console.log('Link page: the ask lands on the drop zone; the unfurl is the card title.');
