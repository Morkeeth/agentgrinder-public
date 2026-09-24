/* THE DROP-IN. The landing page's first step: drop a session file, see its card, get a link.
   No install and no account until the person chooses to post to the feed.

   1. The file is read here with GrinderDropin.parseFile (site/dropin-parse.js). No request is made
      while it is read or while the card is drawn.
   2. The card is the feed's card (site/feed-card.js), revealed once: the line draws in, the number
      counts up, the badge settles. This is a first-time moment, so it gets the delight budget,
      about 800 ms in all; with reduced motion it is a 200 ms fade and the final numbers.
   3. "Get a link" sends GrinderDropin.uploadPayload(run, title) and nothing else. "Post to the
      feed" hands the same counts to the existing import preview, which asks for sign-in. */
(function (root) {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[<>&"']/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&#39;" }[c]));
  const EASE_OUT = "cubic-bezier(0.23, 1, 0.32, 1)";
  const EASE_IN_OUT = "cubic-bezier(0.77, 0, 0.175, 1)";
  const reduced = () => root.matchMedia && root.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let run = null;
  let opts = {};

  function row(title) {
    return {
      id: "dropin", title: title || "", harness: run.harness, prompts: run.turns_typed, turns_typed: run.turns_typed,
      tool_calls: run.tool_calls, files_touched: run.files_touched, commits: run.commits, duration_s: run.duration_s,
      rhythm: run.rhythm, started_hour: GrinderDropin.uploadPayload(run, "").started_hour,
      // created_at is when the card is made, as on the shared page, so both say the same thing.
      started_at: run.started, created_at: new Date().toISOString(), visibility: "anonymous",
    };
  }

  function cardHtml() {
    return GrinderFeed.card(row(($("drop-title") || {}).value || ""), { preview: true, foot: false });
  }

  // The reveal. WAAPI, transform/opacity/clip-path only, so it stays smooth while the page works.
  function reveal(host) {
    const card = host.querySelector(".fc");
    if (!card || !card.animate) return;
    if (reduced()) { card.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 200, easing: "ease" }); return; }
    card.animate([{ opacity: 0, transform: "translateY(8px)" }, { opacity: 1, transform: "none" }], { duration: 320, easing: EASE_OUT });
    const svg = host.querySelector(".fc-spark svg");
    if (svg) svg.animate([{ clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0 0 0)" }], { duration: 700, delay: 80, easing: EASE_IN_OUT, fill: "backwards" });
    const peak = host.querySelector(".fc-peak");
    if (peak) peak.animate([{ opacity: 0, transform: "scale(.6)" }, { opacity: 1, transform: "none" }], { duration: 220, delay: 640, easing: EASE_OUT, fill: "backwards" });
    const badge = host.querySelector(".fc-badge");
    if (badge) badge.animate([{ opacity: 0, transform: "translateY(4px)" }, { opacity: 1, transform: "none" }], { duration: 260, delay: 520, easing: EASE_OUT, fill: "backwards" });
    const n = host.querySelector(".fc-n");
    const target = n && /^[\d,]+$/.test(n.textContent) ? Number(n.textContent.replace(/,/g, "")) : null;
    if (target) {
      const t0 = performance.now(), dur = 700, final = n.textContent;
      const tick = (now) => {
        const p = Math.min(1, (now - t0) / dur);
        const eased = 1 - Math.pow(1 - p, 3);
        n.textContent = p < 1 ? Math.round(target * eased).toLocaleString() : final;
        if (p < 1) requestAnimationFrame(tick);
      };
      // Screen readers get the final number, never a frame of the count.
      n.setAttribute("aria-label", final);
      n.textContent = "0";
      requestAnimationFrame(tick);
    }
  }

  function setError(message) {
    const e = $("drop-error");
    if (e) { e.textContent = message || ""; e.hidden = !message; }
  }

  async function read(file) {
    setError("");
    const zone = $("drop-zone"), progress = $("drop-progress");
    if (!file) return;
    zone.classList.add("reading");
    const started = performance.now();
    try {
      run = await GrinderDropin.parseFile(file, (done, total) => {
        if (progress && total > 2e6) progress.textContent = `Reading ${Math.floor((done / total) * 100)}%`;
      });
    } catch (error) {
      zone.classList.remove("reading");
      if (progress) progress.textContent = "";
      run = null;
      setError(error && error.code ? error.message : "This file could not be read. Pick a .jsonl session file.");
      return;
    }
    zone.classList.remove("reading");
    root.__dropinTimings = { readMs: Math.round(performance.now() - started) };
    showResult();
  }

  function showResult() {
    const stage = $("drop-stage");
    stage.innerHTML = `<div class="drop-result">
      <div id="drop-card">${cardHtml()}</div>
      <label class="drop-name">Title<input id="drop-title" maxlength="80" autocomplete="off" placeholder="What did you get done?"></label>
      <div class="drop-actions"><button type="button" class="act primary" id="drop-link">Get a link</button><button type="button" class="act" id="drop-post">Post to the feed</button></div>
      <p class="hint" id="drop-state" role="status">Only the numbers on this card and your title leave this device.</p>
      <div id="drop-out"></div>
      <button type="button" class="drop-again" id="drop-again">Read another file</button>
    </div>`;
    reveal($("drop-card"));
    const title = $("drop-title");
    title.addEventListener("input", () => {
      const t = $("drop-card").querySelector(".fc-title");
      if (t) t.textContent = GrinderFeed.titleOf(row(title.value));
    });
    $("drop-link").onclick = getLink;
    $("drop-post").onclick = post;
    $("drop-again").onclick = () => { run = null; mount(opts); };
  }

  function titleText() {
    const typed = ($("drop-title").value || "").trim();
    return typed || GrinderFeed.titleOf(row(""));
  }

  async function getLink() {
    const button = $("drop-link"), state = $("drop-state");
    button.disabled = true;
    state.textContent = "Making the link…";
    const payload = GrinderDropin.uploadPayload(run, titleText());
    let res, body;
    try {
      res = await fetch("/api/link", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      body = await res.json().catch(() => ({}));
    } catch (_) {
      button.disabled = false;
      state.textContent = "The link could not be made. Check the connection and try again. Nothing was saved.";
      return;
    }
    if (!res.ok || !body.url) {
      button.disabled = false;
      state.textContent = (body && body.error) || "The link could not be made. Nothing was saved.";
      return;
    }
    button.hidden = true;
    $("drop-title").disabled = true;
    state.textContent = "Link ready. Anyone with it can see this card, and nothing else.";
    $("drop-out").innerHTML = `<div class="drop-link">
      <div class="drop-row"><a id="drop-url" href="${esc(body.url)}" target="_blank" rel="noopener">${esc(body.url.replace(/^https?:\/\//, ""))}</a><button type="button" class="act" data-copy="${esc(body.url)}">Copy</button></div>
      <p class="hint">Unlisted and not in the feed. It expires in 90 days.</p>
      <p class="drop-del-h"><b>Delete link, shown once.</b> Save it: it is the only way to delete this card.</p>
      <div class="drop-row"><code id="drop-delete">${esc(body.delete_url)}</code><button type="button" class="act" data-copy="${esc(body.delete_url)}">Copy</button></div>
    </div>`;
    wireCopy($("drop-out"));
    if (root.__dropinTimings) root.__dropinTimings.linkReady = performance.now();
  }

  // The existing import preview (index.html importRun) takes a base64 run in the URL fragment and
  // already carries it through GitHub sign-in. The typed title and the Public audience go with it.
  function post() {
    const token = encodeURIComponent(btoa(JSON.stringify({
      schema_version: 0, harness: run.harness, turns_typed: run.turns_typed, tool_calls: run.tool_calls,
      files_touched: run.files_touched, commits: run.commits, duration_s: run.duration_s, started: run.started, rhythm: run.rhythm,
    })));
    try { sessionStorage.setItem("ag_import_edits", JSON.stringify({ token, i_title: ($("drop-title").value || "").trim(), i_vis: "public" })); } catch (_) {}
    if (opts.post) opts.post(token); else location.href = "/#import=" + token;
  }

  function wireCopy(scope) {
    scope.querySelectorAll("[data-copy]").forEach((b) => {
      b.onclick = async () => {
        const label = b.textContent;
        try { await navigator.clipboard.writeText(b.dataset.copy); b.textContent = "Copied"; }
        catch (_) { b.textContent = "Select and copy"; }
        setTimeout(() => (b.textContent = label), 1600);
      };
    });
  }

  function mount(options) {
    opts = options || {};
    const stage = $("drop-stage");
    if (!stage) return;
    if (opts.template) stage.innerHTML = opts.template;
    else if (stage.dataset.template) stage.innerHTML = stage.dataset.template;
    if (!stage.dataset.template) stage.dataset.template = stage.innerHTML;
    const input = $("drop-file"), zone = $("drop-zone");
    if (!input || !zone) return;
    input.onchange = () => read(input.files && input.files[0]);
    const stop = (e) => { e.preventDefault(); e.stopPropagation(); };
    zone.addEventListener("dragenter", (e) => { stop(e); zone.classList.add("over"); });
    zone.addEventListener("dragover", (e) => { stop(e); zone.classList.add("over"); });
    zone.addEventListener("dragleave", (e) => { stop(e); if (!zone.contains(e.relatedTarget)) zone.classList.remove("over"); });
    zone.addEventListener("drop", (e) => { stop(e); zone.classList.remove("over"); read(e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]); });
    wireCopy(document.querySelector(".drop-where") || document);
    // A file dropped beside the zone would make the browser open it and leave the page. On the
    // landing page a drop anywhere is read as a drop on the zone.
    if (!root.__dropinGuard) {
      root.__dropinGuard = true;
      root.addEventListener("dragover", (e) => { if ($("drop-zone")) e.preventDefault(); });
      root.addEventListener("drop", (e) => {
        if (!$("drop-zone")) return;
        e.preventDefault();
        const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
        if (f) read(f);
      });
    }
  }

  root.GrinderDropinUI = { mount, read, reveal };
})(typeof window !== "undefined" ? window : globalThis);
