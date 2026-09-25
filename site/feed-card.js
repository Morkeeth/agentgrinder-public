/* THE FEED CARD. What a stranger scrolls past: a face, a name, one big number, the run map, the
   activity line, and a reaction. The full run card (runCard in index.html) stays the detail view
   behind a tap. A ghost run (ghost below) is the same card with the ghost badge and a dashed line.

   Every value here is a column of the run row the page fetched. A number the row does not carry is
   not drawn; nothing is estimated and nothing is invented to fill a gap. Variety between cards comes
   from the runs themselves: the headline is the strongest thing each run measured, so a run with
   commits leads with commits and a run with only a session time leads with time. */
(function (root) {
  "use strict";
  const esc = (s) =>
    String(s ?? "").replace(/[<>&"']/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&#39;" }[c]));
  const whole = (v) => (Number.isFinite(v) && v >= 0 ? Math.round(v) : null);

  function durationLabel(seconds) {
    if (!Number.isFinite(seconds) || seconds <= 0) return null;
    const m = Math.round(seconds / 60);
    if (m < 1) return "<1m";
    return m >= 60 ? `${Math.floor(m / 60)}h ${m % 60}m` : `${m}m`;
  }

  function when(iso) {
    const t = Date.parse(iso);
    if (!Number.isFinite(t)) return "";
    const days = Math.floor((Date.now() - t) / 86400000);
    if (days <= 0) return "Today";
    if (days === 1) return "Yesterday";
    if (days < 7) return `${days} days ago`;
    const d = new Date(t);
    return `${d.getDate()} ${MONTHS[d.getMonth()]}`;
  }

  // The browser loads run-contract.js as a script; the server share page (server/public-run.mjs)
  // requires this file, so it takes the same contract by require and counts tool calls the same way.
  const contract = () =>
    root.GrinderContract ||
    (typeof module !== "undefined" && module.exports && typeof require === "function" ? require("./run-contract.js") : null);

  // THE TITLE. A folder name or a bare "<harness> sitting" is not a title a stranger can read:
  // "Users-morkeeth · Cursor sitting" printed an account name as the headline. Those, and an
  // empty title, become "<harness> session, 24 Sep", read from the run's own start in the
  // reader's time zone, the same day the meta line under the name gives.
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function dayOf(iso) {
    const t = Date.parse(iso);
    if (!Number.isFinite(t)) return "";
    const d = new Date(t);
    return `${d.getDate()} ${MONTHS[d.getMonth()]}`;
  }
  function titleOf(r) {
    const t = String(r.title ?? "").trim();
    const generic =
      !t || /(^|·\s*)-?Users-\S/.test(t) || /(^|·\s*)-?home-[a-z0-9_]+(\s*·|$)/.test(t) ||
      /(^|·\s*)(Cursor|Claude Code|Claude|Codex|Grok Bot|Agent) sitting$/i.test(t) || /^(untitled run|a run|agent run)$/i.test(t);
    if (!generic) return t;
    const day = dayOf(r.started_at || r.started || r.created_at);
    return `${harnessName(r) || "Agent"} session${day ? `, ${day}` : ""}`;
  }

  // A run captured from a Claude Code subagent arrives with harness "claude-agent". On the card
  // it is Claude Code; the row keeps the raw value.
  function harnessName(r) {
    const h = r.harness ? String(r.harness) : "";
    return h === "claude-agent" ? "Claude Code" : h;
  }

  function toolCalls(r) {
    const C = contract();
    return whole(C && C.toolCallCount ? C.toolCallCount(r) : r.tool_calls);
  }

  // The one number, Strava's distance slot. The first measured, non-zero value wins.
  function headline(r) {
    const commits = whole(r.commits);
    const files = whole(r.files_touched);
    const tools = toolCalls(r);
    const time = durationLabel(r.wall_time_s ?? r.duration_s);
    if (commits) return { n: commits.toLocaleString(), unit: commits === 1 ? "commit" : "commits", key: "commits" };
    if (files) return { n: files.toLocaleString(), unit: files === 1 ? "file changed" : "files changed", key: "files" };
    if (tools) return { n: tools.toLocaleString(), unit: "tool calls", key: "tools" };
    if (time) return { n: time, unit: "session", key: "time" };
    return null;
  }

  // Up to three small facts beside the headline, never repeating it.
  function stats(r, lead) {
    const out = [];
    const add = (key, label, value) => {
      if (out.length >= 3 || value == null || value === "" || (lead && lead.key === key)) return;
      out.push([label, value]);
    };
    add("time", "Time", durationLabel(r.wall_time_s ?? r.duration_s));
    const turns = whole(r.prompts ?? r.turns_typed);
    add("turns", "Turns", turns);
    const tools = toolCalls(r);
    add("tools", "Tool calls", tools ? tools.toLocaleString() : null);
    add("commits", "Commits", whole(r.commits) || null);
    add("files", "Files", whole(r.files_touched) || null);
    return out;
  }

  // THE BADGE. One small achievement per run, computed from the run's own numbers and nothing
  // else: no history, no other runs, no guess. The first rule that holds wins, and its detail line
  // prints the number that earned it, so a reader can check the badge against the card. A run that
  // earns none carries none. agentgrinder/feedcard.py achievement() is the same list.
  // Thousands with commas whatever the runtime locale, as agentgrinder/feedcard.py _thousands.
  const thousands = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");

  function hourOf(r) {
    return Number.isInteger(r.started_hour) && r.started_hour >= 0 && r.started_hour <= 23 ? r.started_hour : null;
  }

  // THE GHOST RUN. Strava is for people who ran. STRIVE is for people who didn't: the agent ran
  // for an hour or more and did real work (30 tool calls or more) while the person was not
  // there, which the run's own numbers show: it was typed to at most twice, or it did 40 or
  // more tool calls per typed turn (a run whose typed turns are unknown counts when it started
  // at night, 22:00 to 04:59). The line prints the measured time and, for a night start,
  // "while you slept"; by day, how often the person typed. Nothing on it is a guess and
  // nothing on it is a disclaimer.
  function ghost(r) {
    const secs = whole(r.wall_time_s ?? r.duration_s);
    const turns = whole(r.prompts ?? r.turns_typed);
    const tools = toolCalls(r);
    const hour = hourOf(r);
    if (!(secs >= 3600) || !(tools >= 30)) return null;
    const night = hour != null && (hour >= 22 || hour < 5);
    const alone = turns == null ? night : turns <= 2 || tools / turns >= 40;
    if (!alone) return null;
    const d = durationLabel(secs);
    const typed = turns == null ? "" : turns === 1 ? "once" : turns === 2 ? "twice" : `${thousands(turns)} times`;
    return { key: "ghost", label: "Ghost run", detail: night ? `${d} while you slept` : `${d}, you typed ${typed}` };
  }

  function achievement(r) {
    const g = ghost(r);
    if (g) return g;
    const secs = whole(r.wall_time_s ?? r.duration_s);
    const turns = whole(r.prompts ?? r.turns_typed);
    const tools = toolCalls(r);
    const commits = whole(r.commits);
    const files = whole(r.files_touched);
    const hour = hourOf(r);
    if (secs >= 10800) return { key: "marathon", label: "Marathon", detail: `${durationLabel(secs)} in one session` };
    if (turns === 1 && tools >= 60) return { key: "one-shot", label: "One-shot", detail: `1 prompt, ${tools.toLocaleString()} tool calls` };
    if (hour != null && (hour >= 23 || hour < 5)) return { key: "night-owl", label: "Night owl", detail: hour >= 23 ? "started after 23:00" : "started before 05:00" };
    if (commits >= 5) return { key: "shipper", label: "Shipper", detail: `${commits.toLocaleString()} commits in one run` };
    if (files >= 25) return { key: "wide-net", label: "Wide net", detail: `${files.toLocaleString()} files changed` };
    if (turns >= 2 && tools && tools / turns >= 30) return { key: "delegator", label: "Delegator", detail: `${Math.round(tools / turns).toLocaleString()} tool calls per prompt` };
    if (secs > 0 && secs < 900 && commits >= 1) return { key: "sprint", label: "Sprint", detail: "a commit in under 15 minutes" };
    if (secs >= 3600) return { key: "deep-focus", label: "Deep focus", detail: "over an hour in one session" };
    if (hour != null && hour >= 5 && hour < 7) return { key: "early-bird", label: "Early bird", detail: "started before 07:00" };
    return null;
  }

  const BADGE_ICON =
    '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M5 1.5h6l-1.6 4.2M5 1.5l1.6 4.2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><circle cx="8" cy="10" r="4.2" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>';
  // The ghost: orange, the card's one warm mark beside the peak dot and a sent XUDOS.
  const GHOST_ICON =
    '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M3 14.5V7.5a5 5 0 0 1 10 0v7l-2-1.6-2 1.6-1-1.6-1 1.6-2-1.6Z" fill="currentColor"/><circle cx="6" cy="7.5" r="1.1" fill="#fff"/><circle cx="10" cy="7.5" r="1.1" fill="#fff"/></svg>';
  function badge(r) {
    const a = achievement(r);
    if (!a) return "";
    const g = a.key === "ghost";
    return `<p class="fc-badge${g ? " fc-ghost" : ""}" data-badge="${esc(a.key)}">${g ? GHOST_ICON : BADGE_ICON}<b>${esc(a.label)}</b><span>${esc(a.detail)}</span></p>`;
  }

  function profileOf(r) {
    const p = r.profiles || {};
    const A = root.GrinderAuth;
    const shown = A && A.present ? A.present(p) : null;
    const handle = (shown && shown.handle) || p.handle || p.github_handle || "";
    const name = p.display_name || p.name || handle || "Builder";
    return { handle, name, github: p.github_handle || null, avatar: p.avatar_url || (shown && shown.avatar_url) || null };
  }

  // A face. The profile's own avatar, else the public avatar of the GitHub account the profile
  // signed in with, else an initial. The GitHub fallback is the person's real picture, not a stock
  // one; if it fails to load the initial takes its place.
  function face(r, size) {
    const s = size || 40;
    if (r.visibility === "anonymous")
      return `<span class="fc-face fc-mono" style="--s:${s}px" aria-hidden="true">?</span>`;
    const p = profileOf(r);
    const initial = esc((p.name || "?").trim().charAt(0).toUpperCase() || "?");
    const src = /^https:\/\//i.test(p.avatar || "")
      ? p.avatar
      : p.github && /^[A-Za-z0-9-]{1,39}$/.test(p.github)
        ? `https://github.com/${p.github}.png?size=${s * 2}`
        : null;
    if (!src) return `<span class="fc-face fc-mono" style="--s:${s}px" aria-hidden="true">${initial}</span>`;
    return `<span class="fc-face" style="--s:${s}px" data-initial="${initial}" aria-hidden="true"><img src="${esc(src)}" alt="" width="${s}" height="${s}" loading="lazy" referrerpolicy="no-referrer" onerror="this.parentNode.classList.add('fc-mono');this.parentNode.textContent=this.parentNode.dataset.initial"></span>`;
  }

  // A short sitting spread over 50 bins is a comb of ones and zeros, and a comb is not a shape
  // (agentgrinder/ingest.py says the same of the ridge). When the series holds fewer than two
  // calls per bin on average, neighbouring bins are added together until it does: the total is
  // kept, and an evenly spread sitting draws as the flat line it was.
  function settle(values) {
    const total = values.reduce((a, v) => a + v, 0);
    if (total >= 2 * values.length) return values;
    const n = Math.max(2, Math.min(values.length, Math.floor(total / 2)));
    if (n >= values.length) return values;
    const out = new Array(n).fill(0);
    values.forEach((v, i) => { out[Math.floor((i * n) / values.length)] += v; });
    return out;
  }

  // The drawing: the run's own activity over its length. The ridge when the run carries one, else
  // the rhythm. The tallest moment gets the one orange mark.
  function spark(r) {
    const raw = Array.isArray(r.ridge) && r.ridge.length > 1 ? r.ridge : Array.isArray(r.rhythm) && r.rhythm.length > 1 ? r.rhythm : null;
    if (!raw || raw.some((v) => !Number.isFinite(v) || v < 0)) return "";
    const src = settle(raw);
    const max = Math.max(...src);
    if (!max) return "";
    const w = 300, h = 56, top = 6;
    const x = (i) => (i * w) / (src.length - 1);
    const y = (v) => h - (v / max) * (h - top);
    const line = src.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
    const peak = src.indexOf(max);
    const px = ((peak / (src.length - 1)) * 100).toFixed(2);
    const py = ((y(max) / h) * 100).toFixed(2);
    return `<div class="fc-spark" aria-hidden="true"><svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><polygon points="0,${h} ${line} ${w},${h}" class="fc-area"/><polyline points="${line}" class="fc-line"/></svg><span class="fc-peak" style="left:${px}%;top:${py}%"></span></div>`;
  }

  // THE RUN MAP. The route the run took through the folders it touched (r.route: station
  // indices in first-visit order, one entry per move; agentgrinder/ingest.py folder_route and
  // site/dropin-parse.js folderRoute). Stations sit on a rail in the order the run first reached
  // them, sized by how often it was there; every move is one arc, forward over the rail and back
  // under it, so a run that kept returning to one folder draws a dense knot and a run that
  // walked the tree once draws a clean sweep. No folder is named: the map is the shape of the
  // work. Blue only; orange is spent on the peak, the ghost and a sent XUDOS.
  const MAP_W = 300, MAP_H = 44, RAIL = 30, MAP_X0 = 12, MAP_X1 = 288;
  function routeGeometry(r) {
    const raw = Array.isArray(r.route) ? r.route : null;
    if (!raw || raw.some((v) => !Number.isInteger(v) || v < 0 || v > 15)) return null;
    // A stay is one visit, and stations are numbered by first appearance: rows saved before the
    // readers collapsed repeats, or with a gap in their numbering, draw the same map.
    const order = new Map();
    const seq = [];
    for (const v of raw) {
      if (!order.has(v)) order.set(v, order.size);
      const i = order.get(v);
      if (!seq.length || seq[seq.length - 1] !== i) seq.push(i);
    }
    if (seq.length < 2) return null;
    const n = order.size;
    const visits = new Array(n).fill(0);
    seq.forEach((v) => { visits[v] += 1; });
    const most = Math.max(...visits);
    const x = (i) => (n > 1 ? MAP_X0 + ((MAP_X1 - MAP_X0) * i) / (n - 1) : MAP_W / 2);
    const stations = visits.map((v, i) => [x(i), v ? 2.5 + 4.5 * Math.sqrt(v / most) : 2]);
    const hops = [];
    for (let k = 1; k < seq.length; k += 1) {
      const a = seq[k - 1], b = seq[k];
      if (a === b) continue;
      const xa = x(a), xb = x(b), span = Math.abs(xb - xa) / (MAP_X1 - MAP_X0);
      const cy = b > a ? RAIL - 26 * span : RAIL + 12 * span;
      hops.push(`M${xa.toFixed(1)},${RAIL} Q${((xa + xb) / 2).toFixed(1)},${cy.toFixed(1)} ${xb.toFixed(1)},${RAIL}`);
    }
    const moves = hops.length, returns = seq.length - n;
    const w = (k, one, many) => `${thousands(k)} ${k === 1 ? one : many}`;
    return { n, moves, returns, stations, hops, label: `${w(n, "folder", "folders")} · ${w(moves, "move", "moves")} · ${w(returns, "return", "returns")}` };
  }
  function routeMap(r) {
    const g = routeGeometry(r);
    if (!g) return "";
    const rail = `<line class="fc-rail" x1="${MAP_X0}" y1="${RAIL}" x2="${MAP_X1}" y2="${RAIL}"/>`;
    const hops = g.hops.map((d) => `<path class="fc-hop" d="${d}"/>`).join("");
    const stations = g.stations.map(([cx, cr]) => `<circle class="fc-stn" cx="${cx.toFixed(1)}" cy="${RAIL}" r="${cr.toFixed(1)}"/>`).join("");
    return `<div class="fc-map"><svg viewBox="0 0 ${MAP_W} ${MAP_H}" role="img" aria-label="Route: ${esc(g.label)}">${rail}${hops}${stations}</svg><p class="fc-map-k">${esc(g.label)}</p></div>`;
  }

  // THE STRIDE LINE. Wordle's grid for a run: two lines of plain text a person pastes into a
  // reply, spoiler-free (no prompt, no code, no repo), readable with zero other users. The first
  // line is the card's own figures in the card's own order; the second is the activity line as
  // twelve bars and, when the card has an address, the address.
  const BARS = "▁▂▃▄▅▆▇█";
  function strideBars(r) {
    const raw = Array.isArray(r.ridge) && r.ridge.length > 1 ? r.ridge : Array.isArray(r.rhythm) && r.rhythm.length > 1 ? r.rhythm : null;
    if (!raw || raw.some((v) => !Number.isFinite(v) || v < 0)) return "";
    const src = settle(raw);
    const n = Math.min(12, src.length);
    const bins = new Array(n).fill(0);
    src.forEach((v, i) => { bins[Math.floor((i * n) / src.length)] += v; });
    const max = Math.max(...bins);
    if (!max) return "";
    // Square-root steps: a burst at the start must not flatten the rest of the night to ▁.
    return bins.map((v) => BARS[Math.round(Math.sqrt(v / max) * 7)]).join("");
  }
  function strideText(r, url) {
    const lead = headline(r);
    const a = achievement(r);
    const figures = stats(r, lead).map(([k, v]) =>
      k === "Time" ? String(v) : k === "Turns" ? `${v} ${v === 1 ? "turn" : "turns"}` : `${v} ${k.toLowerCase()}`);
    const first = ["STRIVE", harnessName(r), lead ? `${lead.n} ${lead.unit}` : "", ...figures, a ? `${a.key === "ghost" ? "👻 " : ""}${a.label}` : ""]
      .filter(Boolean).join(" · ");
    const bars = strideBars(r);
    const where = url ? String(url).replace(/^https?:\/\//, "") : "";
    const second = [bars, where].filter(Boolean).join("  ");
    return second ? `${first}\n${second}` : first;
  }
  function stride(r, opts) {
    const text = strideText(r, opts && opts.url);
    const copy = opts && opts.copy ? `<button type="button" class="fc-copy" data-copy="${esc(text)}">Copy</button>` : "";
    return `<div class="fc-stride"><pre>${esc(text)}</pre>${copy}</div>`;
  }
  // Copy, and Share where the device offers a share sheet. Per surface: the local card the
  // command line writes carries no script at all, so it draws no button.
  function wireStride(scope) {
    (scope || document).querySelectorAll(".fc-copy:not([data-wired])").forEach((b) => {
      b.dataset.wired = "true";
      // Read at the click, not at wiring: the drop-in rewrites data-copy once the link exists.
      const text = () => b.dataset.copy || "";
      b.addEventListener("click", async () => {
        const label = b.textContent;
        try { await navigator.clipboard.writeText(text()); b.textContent = "Copied"; }
        catch (_) { b.textContent = "Select and copy"; }
        setTimeout(() => (b.textContent = label), 1600);
      });
      if (typeof navigator !== "undefined" && navigator.share) {
        const share = document.createElement("button");
        share.type = "button"; share.className = "fc-copy fc-share"; share.textContent = "Share";
        share.addEventListener("click", () => navigator.share({ text: text() }).catch(() => {}));
        b.after(share);
      }
    });
  }

  const KUDOS_ICON =
    '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><path d="M10 17.2 3.3 10.6A4.1 4.1 0 0 1 9.1 4.8l.9.9.9-.9a4.1 4.1 0 0 1 5.8 5.8L10 17.2Z" fill="currentColor"/></svg>';
  const TALK_ICON =
    '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><path d="M3.5 4.5h13v9h-8l-3.5 3v-3H3.5z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>';
  const SHARE_ICON =
    '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><path d="M10 3v10M6 7l4-4 4 4M4 11v5.5h12V11" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  // opts.page: the signed-out share page at /r/<id>. It has no script, so the heart is a link into
  // the run (where a signed-in reader can send XUDOS) and the title is the page's one h1.
  // opts.count null means the count could not be read; the heart then carries no number.
  // opts.preview: a run that is not saved anywhere yet (the import preview, and the card the
  // command line writes on this computer, agentgrinder/feedcard.py). Nothing on it links anywhere:
  // there is no saved run to open, react to or share, so the row is drawn but inert.
  function card(r, opts) {
    opts = opts || {};
    const preview = !!opts.preview;
    const page = !!opts.page;
    const p = profileOf(r);
    const anon = r.visibility === "anonymous";
    const lead = headline(r);
    const facts = stats(r, lead);
    const id = esc(r.id);
    const count = preview || (opts.count === null && page) ? null : whole(opts.count) || 0;
    const countHtml = count === null ? "" : `<span class="num">${count}</span>`;
    const mine = !!opts.mine;
    const tag = opts.heading || (page ? "h1" : "h3");
    const who = anon
      ? `<span class="fc-name">Anonymous builder</span>`
      : preview
      ? `<span class="fc-name">${esc(p.name)}</span>`
      : `<a class="fc-name" href="/?u=${encodeURIComponent(p.handle)}">${esc(p.name)}</a>`;
    const meta = [esc(harnessName(r)), esc(when(r.created_at)), opts.metaExtra ? esc(opts.metaExtra) : ""].filter(Boolean).join(" · ");
    const kudos = preview
      ? `<span class="fc-act" aria-label="Send XUDOS">${KUDOS_ICON}</span>`
      : page
      ? `<a class="fc-act" href="/?run=${id}" aria-label="Send XUDOS${count === null ? "" : `, ${count} so far`}">${KUDOS_ICON}${countHtml}</a>`
      : mine
      ? `<span class="fc-act fc-kudos-mine">${KUDOS_ICON}<span class="num">${count}</span></span>`
      : `<button class="fc-act kudo${opts.acked ? " on" : ""}" data-run="${id}" data-to="${esc(r.profile_id)}" aria-label="${opts.acked ? "XUDOS sent" : "Send XUDOS"}, ${count} so far">${KUDOS_ICON}<span class="num">${count}</span></button>`;
    const talk = preview
      ? `<span class="fc-act" aria-label="Discuss">${TALK_ICON}<span>Discuss</span></span><span class="fc-act" aria-label="Share">${SHARE_ICON}<span>Share</span></span>`
      : `<a class="fc-act" href="/?run=${id}#grind-thread" aria-label="Discuss">${TALK_ICON}<span>Discuss</span></a><a class="fc-act" href="/?share=1&amp;run=${id}" aria-label="Share">${SHARE_ICON}<span>Share</span></a>`;
    const shipped = r.output_url && /^https:\/\//i.test(r.output_url) ? `<span class="fc-chip">Shipped</span>` : "";
    const faceHtml = anon || preview ? face(r) : `<a href="/?u=${encodeURIComponent(p.handle)}" tabindex="-1">${face(r)}</a>`;
    const strideHtml = opts.stride === false || !(preview || page || opts.url) ? "" : stride(r, { url: opts.url, copy: !!opts.copy });
    const body = `
    <${tag} class="fc-title">${esc(titleOf(r))}</${tag}>
    ${r.caption || r.note ? `<p class="fc-cap">${esc(r.caption || r.note)}</p>` : ""}
    <div class="fc-numbers">${lead ? `<div class="fc-hero"><span class="fc-n num">${esc(lead.n)}</span><span class="fc-u">${esc(lead.unit)}</span></div>` : ""}${facts.length ? `<dl class="fc-stats">${facts.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd class="num">${esc(v)}</dd></div>`).join("")}</dl>` : ""}</div>
    ${badge(r)}${routeMap(r)}${spark(r)}${strideHtml}
  `;
    return `<article class="card fc${ghost(r) ? " ghost" : ""}"${preview ? "" : ` id="card-${id}" data-run-id="${id}"`}>
  <header class="fc-top">${faceHtml}<div class="fc-who">${who}<small>${meta}</small></div>${shipped}</header>
  ${preview ? `<div class="fc-body">${body}</div>` : `<a class="fc-body" href="/?run=${id}">${body}</a>`}
  ${opts.foot === false ? "" : `<footer class="fc-foot">${kudos}${talk}</footer>`}
</article>`;
  }


  // The empty chair at the end of a short feed. It says what goes here and offers the one action.
  function nextSlot() {
    return `<a class="fc-next" href="/?post"><span class="fc-face fc-mono" style="--s:40px" aria-hidden="true">+</span><span><strong>Your run goes here</strong><small>Post a run</small></span></a>`;
  }

  // A builder row for "who to follow": face, name, their latest run, and a follow slot the social
  // module fills. Built only from profiles that have a public run.
  function builderRow(r) {
    const p = profileOf(r);
    return `<div class="fc-builder">${face(r, 44)}<div class="fc-who"><a class="fc-name" href="/?u=${encodeURIComponent(p.handle)}">${esc(p.name)}</a><small>Latest: <a href="/?run=${esc(r.id)}">${esc(titleOf(r))}</a></small></div><span class="card-follow" data-profile="${esc(r.profile_id)}" data-handle="${esc(p.handle)}" data-label="Follow"></span></div>`;
  }

  const api = { card, face, headline, stats, achievement, ghost, harnessName, badge, spark, settle, routeGeometry, routeMap, strideBars, strideText, stride, wireStride, nextSlot, builderRow, profileOf, durationLabel, when, titleOf };
  root.GrinderFeed = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
