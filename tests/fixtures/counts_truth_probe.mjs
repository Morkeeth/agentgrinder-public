// One fixture, three surfaces: /r/ HTML, SPA heroStats + Explore, share caption facts.
// Peak slice counts and run totals must not be confused; null Code Route must not be promised.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { html } from '../../server/public-run.mjs';

const require = createRequire(import.meta.url);
const GrinderContract = require('../../site/run-contract.js');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

const ridge = Array.from({ length: 50 }, (_, i) => (i === 24 ? 10 : i % 3 === 0 ? 2 : 1));
const ridgeSum = ridge.reduce((a, b) => a + b, 0);
assert.equal(Math.max(...ridge), 10);
assert.ok(ridgeSum > 10);

const fixture = {
  id: '3afa89e7-aff5-488d-bec3-da36196b8c5e',
  title: 'Cursor night review ridge',
  caption: 'First wall-time ridge on STRIVE.',
  visibility: 'public',
  prompts: 1,
  tool_calls: 0,
  ridge_tool_calls: ridgeSum,
  ridge,
  worker_bins: Array(50).fill(0),
  ridge_basis: 'wall-time',
  ridge_wall_seconds: 1080,
  project: 'CODE-worktrees-strava-night-review-20260915',
  harness: 'Cursor',
  code_route: null,
  profiles: { handle: 'morkeeth' },
};

const page = html(fixture);
assert.match(page, new RegExp(`<dt>Tool calls</dt><dd>${ridgeSum}</dd>`));
assert.doesNotMatch(page, /Code Route/);
assert.doesNotMatch(page, new RegExp(`<dt>Tool calls</dt><dd>0</dd>`));
assert.doesNotMatch(page, new RegExp(`<dt>Tool calls</dt><dd>10</dd>`));

const strip = GrinderContract.heroStats(fixture);
const toolCell = strip.find(([label]) => label === 'Tool calls');
assert.ok(toolCell, 'SPA metric strip must show Tool calls');
assert.equal(toolCell[1], String(ridgeSum));
assert.equal(GrinderContract.toolCallCount(fixture), ridgeSum);

const cardHtml = (() => {
  const source = fs.readFileSync(root + '/site/index.html', 'utf8');
  const fn = source.slice(
    source.indexOf('function connectWrapperName('),
    source.indexOf('function wireKudos('),
  );
  const context = {
    GrinderContract,
    ME: null,
    esc: (s) =>
      String(s ?? '').replace(
        /[<>&"']/g,
        (c) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&#39;' }[c]),
      ),
    fmtDur: (m) => (!m ? '-' : m >= 60 ? `${Math.floor(m / 60)}h ${m % 60}m` : `${m}m`),
    runAttribution: () => ({ handle: 'morkeeth', name: 'morkeeth', link: null, ghost: false }),
    avatar: () => '',
    safeOutputUrl: () => null,
    ackPickerHtml: () => '',
    suggestAckReasons: () => [],
    fiveRow: () => '',
    coachBlock: () => '',
  };
  vm.createContext(context);
  vm.runInContext(fn, context);
  return vm.runInContext('runCard(' + JSON.stringify(fixture) + ',false,0)', context);
})();
assert.match(cardHtml, new RegExp(`<strong class="num">${ridgeSum}</strong> Tool calls`));
assert.doesNotMatch(cardHtml, /<strong class="num">0<\/strong> Tool calls/);
assert.doesNotMatch(cardHtml, /Code Route/);

const shareCtx = { window: { GrinderContract }, URL };
vm.runInNewContext(fs.readFileSync(root + '/site/sharing.js', 'utf8'), shareCtx);
const facts = shareCtx.window.GrinderSharing.storyFacts(fixture);
assert.equal(facts.code, `${ridgeSum} tool calls`);
const shareStrip = shareCtx.window.GrinderSharing.metricStrip(fixture);
assert.deepEqual(
  shareStrip.find(([label]) => label === 'Tool calls'),
  ['Tool calls', String(ridgeSum)],
);

const mapHtml = GrinderContract.ridge(fixture);
assert.ok(mapHtml.includes('data-run-map'));
const payload = JSON.parse(
  mapHtml
    .match(/data-run-map="([^"]*)"/)[1]
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&'),
);
assert.equal(payload.peak, 10);
assert.equal(payload.values[payload.peakIndex], 10);

function el(tag, attrs = {}, kids = []) {
  const node = {
    tagName: String(tag).toUpperCase(),
    attrs: { ...attrs },
    children: [],
    parentNode: null,
    dataset: {},
    listeners: {},
    textContent: '',
    value: attrs.value != null ? String(attrs.value) : '',
    className: attrs.class || '',
    getAttribute(name) {
      return this.attrs[name] != null ? String(this.attrs[name]) : null;
    },
    setAttribute(name, value) {
      this.attrs[name] = String(value);
    },
    appendChild(child) {
      child.parentNode = this;
      this.children.push(child);
      return child;
    },
    querySelector(sel) {
      return queryAll(this, sel)[0] || null;
    },
    querySelectorAll(sel) {
      return queryAll(this, sel);
    },
    addEventListener(type, fn, opts) {
      (this.listeners[type] ||= []).push({ fn, opts });
    },
    closest(sel) {
      for (let n = this; n; n = n.parentNode) if (matches(n, sel)) return n;
      return null;
    },
    getBoundingClientRect() {
      return { left: 0, width: 800, top: 0, height: 150 };
    },
  };
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') node.className = v;
    else if (k === 'dataset') Object.assign(node.dataset, v);
    else if (k.startsWith('data-')) {
      const camel = k.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      node.dataset[camel] = v;
    }
    node.attrs[k] = v;
  }
  for (const kid of kids) node.appendChild(kid);
  return node;
}
function matches(node, sel) {
  if (!node || !node.tagName) return false;
  const classes = String(node.className || '').split(/\s+/).filter(Boolean);
  let rest = sel;
  const tag = rest.match(/^[a-zA-Z]+/);
  if (tag) {
    if (node.tagName !== tag[0].toUpperCase()) return false;
    rest = rest.slice(tag[0].length);
  }
  while (rest.length) {
    if (rest[0] === '.') {
      const m = rest.match(/^\.([\w-]+)/);
      if (!m || !classes.includes(m[1])) return false;
      rest = rest.slice(m[0].length);
      continue;
    }
    if (rest[0] === '[') {
      const m = rest.match(/^\[([^\=\]]+)(?:=\"([^\"]*)\")?\]/);
      if (!m) return false;
      const val = node.getAttribute(m[1]);
      if (val == null) return false;
      if (m[2] != null && val !== m[2]) return false;
      rest = rest.slice(m[0].length);
      continue;
    }
    return false;
  }
  return true;
}
function queryAll(rootNode, sel) {
  const out = [];
  const walk = (n) => {
    if (!n || !n.tagName) return;
    if (matches(n, sel)) out.push(n);
    for (const c of n.children || []) walk(c);
  };
  walk(rootNode);
  return out;
}

const encoded = mapHtml.match(/data-run-map="([^"]*)"/)[1];
const decoded = encoded
  .replace(/&quot;/g, '"')
  .replace(/&#39;/g, "'")
  .replace(/&lt;/g, '<')
  .replace(/&gt;/g, '>')
  .replace(/&amp;/g, '&');
const wrap = el('div', {
  class: 'ridge-wrap run-map',
  'data-run-map': decoded,
  dataset: { runMap: decoded },
});
const plot = el('div', { class: 'run-map-plot' });
const svg = el('svg', { class: 'ridge' });
payload.values.forEach((_, i) => {
  svg.appendChild(el('rect', { class: 'run-map-hit', 'data-bin': String(i), dataset: { bin: String(i) } }));
});
svg.appendChild(el('line', { class: 'run-map-scrub' }));
svg.appendChild(el('circle', { class: 'run-map-focus' }));
plot.appendChild(svg);
wrap.appendChild(plot);
const slider = el('input', {
  class: 'run-map-slider',
  type: 'range',
  min: '0',
  max: String(payload.values.length - 1),
  value: '0',
});
wrap.appendChild(el('label', { class: 'run-map-slider-label' }, [slider]));
const readout = el('div', { class: 'run-map-readout' });
wrap.appendChild(readout);
GrinderContract.mountRunMaps(el('div', {}, [wrap]));
assert.match(readout.textContent, /10 tool calls in this slice/);
assert.match(readout.textContent, /peak activity 10/);
assert.doesNotMatch(readout.textContent, new RegExp(`${ridgeSum} tool calls in this slice`));

const withRoute = {
  ...fixture,
  code_route: {
    v: 1,
    projects: [
      { id: 'a', label: 'strive' },
      { id: 'b', label: 'zup' },
    ],
    stops: [
      { id: 's1', kind: 'edit', label: 'Edit', basis: 'measured', project: 'a' },
      { id: 's2', kind: 'check', label: 'Check', basis: 'measured', project: 'b' },
    ],
    connectors: [],
    finish: { stop: 's2', kind: 'artifact', label: 'Ship' },
    stats: { projects_touched: 2 },
  },
};
assert.match(html(withRoute), /Code Route/);
assert.match(GrinderContract.codeRoute(withRoute), /Code Route/);

console.log(
  JSON.stringify({
    ok: true,
    toolCalls: ridgeSum,
    peakSlice: 10,
    surfaces: ['/r/', 'heroStats', 'Explore', 'share', 'slice readout'],
  }),
);
