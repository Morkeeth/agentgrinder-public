// The home page's share image, rendered the way the endpoint renders it. api/og.js is four
// lines of plumbing around this tree, so the tree is what is worth checking: it must come out
// as a 1200x630 PNG and carry the brand and the tagline, because those are what a reader sees
// in a post before they see anything else.
import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';
import {homeCard} from '../server/public-run.mjs';
import {BRAND,TAGLINE} from '../server/brand.mjs';
import {ImageResponse} from '@vercel/og';

const tree=JSON.stringify(homeCard());
assert(tree.includes(BRAND),'the home share image carries the brand');
assert(tree.includes(TAGLINE),'the home share image carries the tagline');
for(const tool of ['Cursor','Claude Code','Codex','Grok Bot'])
 assert(tree.includes(tool),`the home share image names ${tool}`);
assert(!tree.includes('Users-'),'no home directory slug in the share image');

const image=new ImageResponse(homeCard(),{width:1200,height:630});
const bytes=Buffer.from(await image.arrayBuffer());
assert.equal(bytes.subarray(1,4).toString(),'PNG');
assert.equal(bytes.readUInt32BE(16),1200);
assert.equal(bytes.readUInt32BE(20),630);
await writeFile('/tmp/strive-home-og.png',bytes);
console.log(`Home unfurl: ${bytes.length} byte PNG at 1200x630 carrying ${BRAND} · ${TAGLINE}`);
