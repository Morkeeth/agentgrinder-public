/* Shared browser boundary: a successful parse is not permission to store arbitrary fields. */
(function (root) {
  "use strict";
  const counts = [
    "turns_typed",
    "tool_calls",
    "shell_calls",
    "files_touched",
    "commits",
    "claims",
    "claims_verified",
    "artifacts_produced",
  ];
  function validate(run) {
    if (!run || typeof run !== "object" || Array.isArray(run))
      throw new Error("A grind must be a JSON object.");
    const version = run.schema_version ?? 0;
    if (!Number.isInteger(version) || ![0, 1].includes(version))
      throw new Error(
        "This grind uses an unsupported format. Update Agent Grinder to read it.",
      );
    for (const field of counts) {
      if (
        run[field] != null &&
        (!Number.isSafeInteger(run[field]) || run[field] < 0)
      )
        throw new Error(
          field + " must be a non-negative whole number or unknown.",
        );
    }
    if (
      run.duration_s != null &&
      (typeof run.duration_s !== "number" ||
        !Number.isFinite(run.duration_s) ||
        run.duration_s < 0)
    )
      throw new Error("Invalid grind duration.");
    if (run.claims_verified != null && run.claims == null)
      throw new Error("Verified claims require a counted-claims total.");
    if (
      run.claims != null &&
      run.claims_verified != null &&
      run.claims_verified > run.claims
    )
      throw new Error("Verified claims cannot exceed the claims counted.");
    if (run.ridge != null) {
      if (
        !Array.isArray(run.ridge) ||
        run.ridge.length < 40 ||
        run.ridge.length > 60 ||
        run.ridge.some((v) => !Number.isSafeInteger(v) || v < 0)
      )
        throw new Error(
          "ridge must contain 40 to 60 non-negative whole-number bins.",
        );
      if (
        !Array.isArray(run.worker_bins) ||
        run.worker_bins.length !== run.ridge.length ||
        run.worker_bins.some((v) => !Number.isSafeInteger(v) || v < 0)
      )
        run.worker_bins = Array(run.ridge.length).fill(0);
      if (
        !Array.isArray(run.commit_bins || []) ||
        (run.commit_bins || []).some(
          (v) =>
            !Number.isSafeInteger(v) || v < 0 || v >= run.ridge.length,
        )
      )
        throw new Error("commit_bins must contain valid ridge indexes.");
      if (!["wall-time", "call-index", "turn-order"].includes(run.ridge_basis))
        throw new Error("ridge_basis must be wall-time, call-index, or turn-order.");
      if (
        run.ridge_wall_seconds != null &&
        (typeof run.ridge_wall_seconds !== "number" ||
          !Number.isFinite(run.ridge_wall_seconds) ||
          run.ridge_wall_seconds < 0)
      )
        throw new Error("Invalid ridge wall time.");
    }
    // Declared outcome receipts. Same rules the database enforces in migration 008. These are the
    // uploader's claims, never measurements, so they are validated for safety and shown apart.
    for (const field of ["repo_url", "artifact_url", "image_url"]) {
      if (run[field] == null) continue;
      if (typeof run[field] !== "string" || !safeUrl(run[field]))
        throw new Error(field + " must be one https link under 300 characters.");
    }
    if (run.repo_url != null && !/^https:\/\/(github\.com|gitlab\.com|codeberg\.org)\/[A-Za-z0-9._-]+\/[A-Za-z0-9._-]+/i.test(run.repo_url))
      throw new Error("repo_url must be a repository on github.com, gitlab.com or codeberg.org.");
    if (run.image_url != null && !/\.(png|jpe?g|webp)([?#].*)?$/i.test(run.image_url))
      throw new Error("image_url must end in .png, .jpg, .jpeg or .webp.");
    if (run.shipped != null) {
      if (!Array.isArray(run.shipped) || run.shipped.length > 5)
        throw new Error("shipped holds at most 5 lines.");
      if (run.shipped.some((line) => typeof line !== "string" || line.trim().length < 1 || line.trim().length > 120))
        throw new Error("each shipped line is text, 1 to 120 characters.");
    }
    if (run.receipts != null) {
      if (!Array.isArray(run.receipts) || run.receipts.length > 5)
        throw new Error("receipts holds at most 5 links.");
      if (run.receipts.some((r) => !r || typeof r !== "object" || Array.isArray(r)
        || Object.keys(r).some((k) => k !== "label" && k !== "url")
        || typeof r.label !== "string" || r.label.trim().length < 1 || r.label.trim().length > 60
        || typeof r.url !== "string" || !safeUrl(r.url)))
        throw new Error("each receipt is {label, url}: a label of 1 to 60 characters and one https link.");
    }
    for (const field of ["measurement_revision", "baseline_revision"]) {
      if (
        run[field] != null &&
        (typeof run[field] !== "string" || !/^[a-f0-9]{64}$/.test(run[field]))
      )
        throw new Error("Invalid measurement revision reference.");
    }
    return run;
  }
  function safeUrl(value) {
    if (typeof value !== "string" || value.length < 12 || value.length > 300) return false;
    if (/[\s<>"'\\]/.test(value) || /javascript:/i.test(value)) return false;
    try { return new URL(value).protocol === "https:"; } catch (_) { return false; }
  }
  function esc(text) {
    return String(text).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
  function outcome(run) {
    // Declared by the uploader. Kept in its own block, with its own heading, so it can never read as
    // a measurement. Every link is re-checked here, because a stored row is still untrusted input.
    if (!run) return "";
    const link = (href, text) => safeUrl(href)
      ? `<a href="${esc(href)}" rel="noopener noreferrer nofollow" target="_blank">${esc(text)}</a>` : "";
    const parts = [];
    const repo = safeUrl(run.repo_url) ? link(run.repo_url, String(run.repo_url).replace(/^https:\/\//, "")) : "";
    if (repo) parts.push(`<p class="run-outcome-repo">${repo}</p>`);
    const shipped = Array.isArray(run.shipped) ? run.shipped.filter((l) => typeof l === "string" && l.trim()).slice(0, 5) : [];
    if (shipped.length) parts.push(`<ul class="run-outcome-shipped">${shipped.map((l) => `<li>${esc(l.trim().slice(0, 120))}</li>`).join("")}</ul>`);
    const receipts = (Array.isArray(run.receipts) ? run.receipts : []).filter((r) => r && safeUrl(r.url) && typeof r.label === "string").slice(0, 5);
    const extra = [];
    receipts.forEach((r) => extra.push(link(r.url, r.label.trim().slice(0, 60))));
    if (safeUrl(run.artifact_url)) extra.push(link(run.artifact_url, "Open the demo"));
    if (extra.length) parts.push(`<p class="run-outcome-links">${extra.join(" · ")}</p>`);
    if (safeUrl(run.image_url) && /\.(png|jpe?g|webp)([?#].*)?$/i.test(run.image_url))
      parts.push(`<p class="run-outcome-image"><img src="${esc(run.image_url)}" alt="Screenshot the uploader attached" loading="lazy" referrerpolicy="no-referrer"></p>`);
    if (!parts.length) return "";
    return `<section class="run-outcome"><div class="run-story-label">Said by the uploader, not measured</div>${parts.join("")}</section>`;
  }
  function message(error) {
    const text =
      error?.message || "This action could not be completed. Try again.";
    return /schema cache|could not find the table|relation .*does not exist|column .*does not exist/i.test(
      text,
    )
      ? "This part of Grinder is not available on this deployment yet."
      : text;
  }
  function trace(snapshot) {
    const values = snapshot?.rhythm;
    if (
      !Array.isArray(values) ||
      !values.length ||
      values.length > 10000 ||
      values.some((v) => !Number.isFinite(v) || v < 0)
    )
      return "<small>Trace unavailable</small>";
    const max = Math.max(1, ...values),
      points = values
        .map(
          (v, i) =>
            `${4 + (i * 232) / Math.max(1, values.length - 1)},${64 - (v * 54) / max}`,
        )
        .join(" ");
    return (
      '<svg viewBox="0 0 240 72" role="img" aria-label="Recorded session rhythm" style="display:block;width:100%;color:var(--blue)"><polyline points="' +
      points +
      '" stroke="currentColor" fill="none" stroke-width="2"/></svg>'
    );
  }
  function ridge(snapshot) {
    const values = snapshot?.ridge;
    const workers = snapshot?.worker_bins;
    if (
      !Array.isArray(values) ||
      values.length < 40 ||
      values.length > 60 ||
      values.some((v) => !Number.isSafeInteger(v) || v < 0) ||
      !Array.isArray(workers) ||
      workers.length !== values.length ||
      workers.some((v) => !Number.isSafeInteger(v) || v < 0)
    )
      return "";
    const w = 800, h = 150, base = 132, top = 16;
    const x = (i) => (i * w) / Math.max(1, values.length - 1);
    const max = Math.max(1, ...values);
    const y = (v) => base - (v / max) * (base - top);
    const line = values
      .map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`)
      .join(" ");
    const area = `0,${base} ${line} ${w},${base}`;
    const workerMax = Math.max(0, ...workers);
    let backs = "";
    for (let level = Math.min(3, workerMax); level >= 1; level--) {
      const points = workers
        .map((v, i) => {
          const active = Math.min(v, level) / level;
          const value = active ? Math.max(values[i], max * (0.2 + level * 0.08)) : 0;
          return `${x(i).toFixed(1)},${y(value).toFixed(1)}`;
        })
        .join(" ");
      backs += `<polygon class="ridge-worker ridge-worker-${level}" points="0,${base} ${points} ${w},${base}"/>`;
    }
    const ticks = (snapshot.commit_bins || [])
      .filter((v) => Number.isSafeInteger(v) && v >= 0 && v < values.length)
      .map((v) => `<line class="ridge-commit" x1="${x(v).toFixed(1)}" y1="${base}" x2="${x(v).toFixed(1)}" y2="${base - 10}"/>`)
      .join("");
    // Output chips stay off the plot unless a measured bin places them. output_url alone is not a timed landmark.
    const basisLabel =
      snapshot.ridge_basis === "wall-time"
        ? "wall time"
        : snapshot.ridge_basis === "turn-order"
          ? "turn order"
          : "call order";
    const peak = Math.max(0, ...values);
    const peakIndex = peak > 0 ? values.indexOf(peak) : -1;
    const commits = (snapshot.commit_bins || []).filter(
      (v) => Number.isSafeInteger(v) && v >= 0 && v < values.length,
    );
    const hits = values
      .map((v, i) => {
        const x0 = Math.max(0, i === 0 ? 0 : x(i) - w / values.length / 2);
        const x1 = Math.min(w, i === values.length - 1 ? w : x(i) + w / values.length / 2);
        return `<rect class="run-map-hit" data-bin="${i}" x="${x0.toFixed(1)}" y="0" width="${(x1 - x0).toFixed(1)}" height="${h}" fill="transparent"/>`;
      })
      .join("");
    const payload = escText(
      JSON.stringify({
        values,
        workers,
        commits,
        peak,
        peakIndex,
        basis: snapshot.ridge_basis || "",
        basisLabel,
      }),
    );
    const startBin = peakIndex >= 0 ? peakIndex : 0;
    const help =
      "Each activity slice is one measured step along " +
      basisLabel +
      ". Commit marks sit only on measured commit_bins. Linked output is not placed on the map without a timed bin.";
    return `<div class="ridge-wrap run-map" data-ridge-basis="${escText(snapshot.ridge_basis || "")}" data-run-map="${payload}"><div class="run-map-head"><span class="run-story-label">Run map</span><span class="meta">Activity along ${escText(basisLabel)}</span></div><div class="run-map-plot"><svg class="ridge" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">${backs}<polygon class="ridge-fill" points="${area}"/><line class="ridge-base" x1="0" y1="${base}" x2="${w}" y2="${base}"/>${ticks}<polyline class="ridge-line" points="${line}"/><circle class="ridge-start" cx="0" cy="${y(values[0]).toFixed(1)}" r="5"/><circle class="ridge-end" cx="${w}" cy="${y(values[values.length - 1]).toFixed(1)}" r="5"/><line class="run-map-scrub" x1="${x(startBin).toFixed(1)}" y1="${top}" x2="${x(startBin).toFixed(1)}" y2="${base}" /><circle class="run-map-focus" cx="${x(startBin).toFixed(1)}" cy="${y(values[startBin]).toFixed(1)}" r="6"/>${hits}</svg></div><label class="run-map-slider-label"><span class="visually-hidden">Activity slice</span><input class="run-map-slider" type="range" min="0" max="${values.length - 1}" value="${startBin}" step="1" aria-valuemin="0" aria-valuemax="${values.length - 1}" aria-valuenow="${startBin}" /></label><div class="run-map-readout" aria-live="polite"></div><details class="run-map-help"><summary>How to read this map</summary><p>${escText(help)}</p></details></div>`;
  }
  function mountRunMaps(root) {
    const scope = root && root.querySelectorAll ? root : typeof document !== "undefined" ? document : null;
    if (!scope) return;
    scope.querySelectorAll(".run-map[data-run-map]").forEach((wrap) => {
      if (wrap.dataset.wired === "1") return;
      wrap.dataset.wired = "1";
      let data;
      try {
        data = JSON.parse(wrap.getAttribute("data-run-map") || "{}");
      } catch (_) {
        return;
      }
      const values = data.values || [];
      if (!values.length) return;
      const plot = wrap.querySelector(".run-map-plot");
      const svg = wrap.querySelector("svg.ridge");
      const scrub = wrap.querySelector(".run-map-scrub");
      const focus = wrap.querySelector(".run-map-focus");
      const readout = wrap.querySelector(".run-map-readout");
      const slider = wrap.querySelector(".run-map-slider");
      if (!plot || !svg) return;
      const w = 800,
        base = 132,
        top = 16;
      const x = (i) => (i * w) / Math.max(1, values.length - 1);
      const max = Math.max(1, ...values);
      const y = (v) => base - (v / max) * (base - top);
      const describe = (i) => {
        const tools = values[i] || 0;
        const workers = (data.workers && data.workers[i]) || 0;
        const isPeak = i === data.peakIndex && data.peak > 0;
        const commitHere = (data.commits || []).includes(i);
        const bits = [];
        bits.push(`Activity slice ${i + 1} of ${values.length}`);
        bits.push(`${tools} tool call${tools === 1 ? "" : "s"}`);
        if (workers) bits.push(`${workers} worker${workers === 1 ? "" : "s"}`);
        if (isPeak) bits.push(`peak activity ${data.peak}`);
        if (commitHere) bits.push("commit landmark");
        return bits.join(" · ");
      };
      const paint = (i) => {
        const idx = Math.max(0, Math.min(values.length - 1, i | 0));
        if (scrub) {
          scrub.setAttribute("x1", x(idx).toFixed(1));
          scrub.setAttribute("x2", x(idx).toFixed(1));
        }
        if (focus) {
          focus.setAttribute("cx", x(idx).toFixed(1));
          focus.setAttribute("cy", y(values[idx]).toFixed(1));
        }
        if (readout) readout.textContent = describe(idx);
        wrap.dataset.activeBin = String(idx);
        if (slider) {
          slider.value = String(idx);
          slider.setAttribute("aria-valuenow", String(idx));
          slider.setAttribute("aria-valuetext", describe(idx));
        }
      };
      paint(data.peakIndex >= 0 ? data.peakIndex : 0);
      const binFromClientX = (clientX) => {
        if (!svg) return null;
        const rect = svg.getBoundingClientRect();
        if (!Number.isFinite(clientX) || !rect.width) return null;
        const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
        return Math.round(ratio * (values.length - 1));
      };
      const fromPointer = (event) => {
        const hit = event.target.closest && event.target.closest(".run-map-hit");
        if (hit && hit.dataset.bin != null) return Number(hit.dataset.bin);
        const clientX = event.clientX;
        return binFromClientX(clientX);
      };
      plot.addEventListener("pointerdown", (event) => {
        const i = fromPointer(event);
        if (i == null) return;
        paint(i);
      });
      plot.addEventListener("pointermove", (event) => {
        if (event.buttons === 0 && event.pointerType !== "mouse") return;
        if (event.pointerType === "mouse" && event.buttons === 0) {
          const i = fromPointer(event);
          if (i != null) paint(i);
          return;
        }
        if (event.buttons > 0) {
          const i = fromPointer(event);
          if (i != null) paint(i);
        }
      });
      let touchOrigin = null;
      plot.addEventListener(
        "touchstart",
        (event) => {
          const t = event.touches && event.touches[0];
          if (!t) return;
          touchOrigin = { x: t.clientX, y: t.clientY, scrubbing: false };
        },
        { passive: true },
      );
      plot.addEventListener(
        "touchmove",
        (event) => {
          const t = event.touches && event.touches[0];
          if (!t || !touchOrigin) return;
          const dx = t.clientX - touchOrigin.x;
          const dy = t.clientY - touchOrigin.y;
          if (!touchOrigin.scrubbing) {
            if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
            if (Math.abs(dy) >= Math.abs(dx)) {
              touchOrigin = null;
              return;
            }
            touchOrigin.scrubbing = true;
          }
          if (event.cancelable) event.preventDefault();
          const i = binFromClientX(t.clientX);
          if (i != null) paint(i);
        },
        { passive: false },
      );
      plot.addEventListener(
        "touchend",
        () => {
          touchOrigin = null;
        },
        { passive: true },
      );
      if (slider) {
        slider.addEventListener("input", () => paint(Number(slider.value)));
        slider.addEventListener("keydown", (event) => {
          let next = null;
          if (event.key === "Home") next = 0;
          else if (event.key === "End") next = values.length - 1;
          else if (event.key === "ArrowLeft" || event.key === "ArrowDown") next = Number(slider.value) - 1;
          else if (event.key === "ArrowRight" || event.key === "ArrowUp") next = Number(slider.value) + 1;
          else if (event.key === "PageDown") next = Number(slider.value) - 5;
          else if (event.key === "PageUp") next = Number(slider.value) + 5;
          if (next == null) return;
          event.preventDefault();
          paint(next);
        });
      }
    });
  }
  function headlineMetric(snapshot) {
    if (snapshot && snapshot.headline_metric_id) return snapshot.headline_metric_id;
    if (snapshot && snapshot.claims_verified == null && snapshot.artifacts_produced != null)
      return "artifacts_per_turn";
    return "verified_per_turn";
  }
  function sittingsComparable(before, after, review = {}) {
    if (review.decision === "incomparable" || review.tried === false)
      return { ok: false, why: "The participant marked this outcome incomparable or did not try the practice." };
    if (!before || !after)
      return { ok: false, why: "No later measurement is bound yet." };
    if (!before.harness || !after.harness || before.harness !== after.harness)
      return {
        ok: false,
        why:
          "Harness differs or is unknown. Different harnesses are not the same measurement, even when claim counts are present.",
      };
    if (!before.trace_basis || !after.trace_basis || before.trace_basis !== after.trace_basis)
      return {
        ok: false,
        why: "Time basis differs or is unknown. Do not read the traces as one claim.",
      };
    const beforeMetric = headlineMetric(before);
    const afterMetric = headlineMetric(after);
    if (beforeMetric !== afterMetric)
      return {
        ok: false,
        why:
          "Headline metrics differ (" +
          beforeMetric +
          " vs " +
          afterMetric +
          "); do not read a number change as the same claim.",
      };
    if ((before.claims_verified != null) !== (after.claims_verified != null))
      return {
        ok: false,
        why: "Verified-claim evidence is present on only one sitting.",
      };
    const numerator = beforeMetric === "verified_per_turn" ? "claims_verified"
      : beforeMetric === "artifacts_per_turn" ? "artifacts_produced" : null;
    if (!numerator || [before, after].some((s) =>
      !Number.isFinite(s[numerator]) || s[numerator] < 0 ||
      !Number.isFinite(s.turns_typed) || s.turns_typed <= 0))
      return { ok: false, why: "The headline numerator or typed-turn count is missing or invalid. Two missing measurements do not make a comparison." };
    return {
      ok: true,
      why: "Same harness, time basis and metric identity. This is an observation, not proof the practice caused the difference. Different task difficulty is not productivity proof.",
    };
  }
  function rejectPaths(value) {
    if (value == null) return value;
    if (typeof value === "object") {
      if (Array.isArray(value)) return value.map(rejectPaths);
      const out = {};
      for (const k of Object.keys(value)) out[k] = rejectPaths(value[k]);
      return out;
    }
    if (typeof value !== "string") return value;
    return value
      .split(/\n/)
      .map((line) =>
        line
          .split(/\s+/)
          .map((raw) => {
            if (!raw) return raw;
            const tok = raw.replace(/^[,.;:()[\]{}'"`]+|[,.;:()[\]{}'"`]+$/g, "");
            if (
              tok.startsWith("/") ||
              tok.startsWith("~") ||
              tok.includes("\\") ||
              tok.includes("/") ||
              /^[A-Za-z]:/.test(tok)
            )
              return "[file]";
            return raw;
          })
          .join(" "),
      )
      .join("\n");
  }
  /* Orchestration tree: one orchestrator on top, workers as rows. Reads only the fields the
     tree builder allows (ids, model, timestamps, counts). A tree with no children still renders
     the orchestrator line so a reader sees that delegation was recorded but the workers were not. */
  const escText = (s) =>
    String(s ?? "").replace(/[<>&"']/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&#39;" })[c]);
  function wall(seconds) {
    if (!Number.isFinite(seconds) || seconds < 0) return "unknown";
    const total = Math.round(seconds), h = Math.floor(total / 3600), m = Math.floor((total % 3600) / 60), s = total % 60;
    if (h) return h + "h " + String(m).padStart(2, "0") + "m";
    if (m) return m + "m " + String(s).padStart(2, "0") + "s";
    return s + "s";
  }
  function offset(start, base) {
    const a = Date.parse(start), b = Date.parse(base);
    if (!Number.isFinite(a) || !Number.isFinite(b) || a < b) return "";
    return "+" + wall((a - b) / 1000);
  }
  function treeNode(node) {
    if (!node || typeof node !== "object" || Array.isArray(node)) return null;
    const num = (v) => (Number.isSafeInteger(v) && v >= 0 ? v : null);
    return {
      model: typeof node.model === "string" ? node.model.slice(0, 60) : null,
      subagent_type: typeof node.subagent_type === "string" ? node.subagent_type.slice(0, 24) : null,
      status: typeof node.status === "string" ? node.status.slice(0, 24) : null,
      started_at: typeof node.started_at === "string" && Number.isFinite(Date.parse(node.started_at)) ? node.started_at : null,
      wall_seconds: Number.isFinite(node.wall_seconds) && node.wall_seconds >= 0 ? node.wall_seconds : null,
      bubbles: num(node.bubbles),
      tool_calls: num(node.tool_calls),
      tool_errors: num(node.tool_errors),
      children: Array.isArray(node.children) ? node.children.map(treeNode).filter(Boolean).slice(0, 200) : [],
    };
  }
  function tree(raw) {
    const root = treeNode(raw);
    if (!root) return "";
    const workers = root.children;
    const longest = Math.max(1, ...workers.map((w) => w.wall_seconds || 0));
    const chip = (m) => '<span class="tree-chip" title="' + escText(m || "model unknown") + '">' + escText(m || "model unknown") + "</span>";
    const counts = (n) =>
      '<span class="tree-counts">' +
      (n.bubbles == null ? "?" : n.bubbles) + " turns · " +
      (n.tool_calls == null ? "?" : n.tool_calls) + " tools" +
      (n.tool_errors ? " · " + n.tool_errors + " err" : "") +
      "</span>";
    const rows = workers
      .map((w, i) => {
        const width = w.wall_seconds == null ? 0 : Math.max(1, Math.round((w.wall_seconds / longest) * 100));
        const label = "worker " + (i + 1) + (w.subagent_type && w.subagent_type !== "generalPurpose" ? " · " + w.subagent_type : "");
        const flag = w.status && w.status !== "completed" ? ' <span class="tree-flag">' + escText(w.status) + "</span>" : "";
        return (
          '<li class="tree-worker"><div class="tree-line"><span class="tree-name">' + escText(label) + flag + "</span>" + chip(w.model) +
          '<span class="tree-wall">' + escText(wall(w.wall_seconds)) + "</span></div>" +
          '<div class="tree-bar" role="img" aria-label="' + escText(wall(w.wall_seconds)) + ' of the longest worker"><span style="width:' + width + '%"></span></div>' +
          '<div class="tree-line small">' + counts(w) + '<span class="tree-start">' + escText(offset(w.started_at, root.started_at)) + "</span></div></li>"
        );
      })
      .join("");
    const sum = workers.reduce((a, w) => a + (w.wall_seconds || 0), 0);
    return (
      '<section class="tree" aria-label="Orchestration tree">' +
      '<div class="tree-root"><div class="tree-line"><span class="tree-name">orchestrator</span>' + chip(root.model) +
      '<span class="tree-wall">' + escText(wall(root.wall_seconds)) + " span</span></div>" +
      '<div class="tree-line small">' + counts(root) + '<span class="tree-start">' + workers.length + " worker" + (workers.length === 1 ? "" : "s") +
      (workers.length ? " · " + escText(wall(sum)) + " worker time" : "") + "</span></div></div>" +
      (workers.length ? '<ol class="tree-workers">' + rows + "</ol>" : '<p class="tree-empty">Delegation recorded, no worker rows found.</p>') +
      '<p class="tree-foot">Bars compare worker wall time to the longest worker. Model names are what Cursor recorded. Tokens are not on disk and are not shown.</p>' +
      "</section>"
    );
  }
  const api = { validate, message, trace, ridge, outcome, mountRunMaps, sittingsComparable, headlineMetric, rejectPaths, tree };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.GrinderContract = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
