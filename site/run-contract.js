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
        throw new Error("worker_bins must match ridge.");
      if (
        !Array.isArray(run.commit_bins || []) ||
        (run.commit_bins || []).some(
          (v) =>
            !Number.isSafeInteger(v) || v < 0 || v >= run.ridge.length,
        )
      )
        throw new Error("commit_bins must contain valid ridge indexes.");
      if (!["wall-time", "call-index"].includes(run.ridge_basis))
        throw new Error("ridge_basis must be wall-time or call-index.");
      if (
        run.ridge_wall_seconds != null &&
        (typeof run.ridge_wall_seconds !== "number" ||
          !Number.isFinite(run.ridge_wall_seconds) ||
          run.ridge_wall_seconds < 0)
      )
        throw new Error("Invalid ridge wall time.");
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
    const output = (() => {
      let label = "";
      const url = String(snapshot.output_url || "");
      if (/github\.com\/[^/]+\/[^/]+\/pull\/\d+/i.test(url)) label = "PR";
      else if (/\.(png|jpe?g|webp)(?:[?#]|$)/i.test(url)) label = "Screenshot";
      else if (url) label = "Output";
      else if (Number.isSafeInteger(snapshot.commits) && snapshot.commits > 0)
        label = snapshot.commits + " commit" + (snapshot.commits === 1 ? "" : "s");
      if (!label) return "";
      const width = Math.min(118, 24 + label.length * 7);
      const chipY = Math.max(2, y(values[values.length - 1]) - 30);
      return `<g class="ridge-chip" transform="translate(${w - width - 2},${chipY.toFixed(1)})"><rect width="${width}" height="23" rx="2"/><text x="${width / 2}" y="15">${escText(label)}</text></g>`;
    })();
    return `<div class="ridge-wrap"><svg class="ridge" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" role="img" aria-label="Tool calls across ${escText(snapshot.ridge_basis === "wall-time" ? "wall time" : "call order")}">${backs}<polygon class="ridge-fill" points="${area}"/><line class="ridge-base" x1="0" y1="${base}" x2="${w}" y2="${base}"/>${ticks}<polyline class="ridge-line" points="${line}"/><circle class="ridge-start" cx="0" cy="${y(values[0]).toFixed(1)}" r="5"/><circle class="ridge-end" cx="${w}" cy="${y(values[values.length - 1]).toFixed(1)}" r="5"/>${output}</svg><span class="meta">${snapshot.ridge_basis === "wall-time" ? "Tool calls over wall time" : "Tool calls over call order"}</span></div>`;
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
  const api = { validate, message, trace, ridge, sittingsComparable, headlineMetric, rejectPaths, tree };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.GrinderContract = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
