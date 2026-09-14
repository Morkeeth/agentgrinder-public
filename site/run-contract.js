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
  const api = { validate, message, trace, sittingsComparable, headlineMetric, rejectPaths };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.GrinderContract = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
