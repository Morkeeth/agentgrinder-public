/* Shared browser boundary: a successful parse is not permission to store arbitrary fields. */
(function (root) {
  "use strict";
  const counts = [
    "turns_typed",
    "tool_calls",
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
  const api = { validate, message, trace, sittingsComparable, headlineMetric, rejectPaths, tree };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.GrinderContract = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
