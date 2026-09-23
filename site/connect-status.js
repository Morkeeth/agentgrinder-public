/* When a connected device last synced, and when that becomes a problem.
 *
 * One rule in one place, because the Connections list and the database both state it: a device
 * token slides 90 days forward every time it uploads, and a device with no run for seven days is
 * shown in amber. strava.agent_token_list() returns the same `stale` flag from SQL; the parity is
 * checked in scripts/test-connect-device.mjs.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.GrinderConnectStatus = factory();
})(typeof window !== "undefined" ? window : globalThis, function () {
  const STALE_DAYS = 7;
  const DAY = 86400000;
  const time = (value) => {
    const at = value ? Date.parse(value) : NaN;
    return Number.isFinite(at) ? at : null;
  };

  // A revoked or expired credential is not stale, it is finished. A device that has never
  // uploaded is waiting for its first run until its own first week passes.
  function isStale(row, now = Date.now()) {
    if (!row || row.revoked === true) return false;
    const expires = time(row.expires_at);
    if (expires !== null && expires <= now) return false;
    const since = time(row.last_seen_at) ?? time(row.created_at);
    if (since === null) return false;
    return now - since > STALE_DAYS * DAY;
  }

  function lastSynced(row, now = Date.now()) {
    if (!row) return "";
    if (row.revoked === true) return "Revoked";
    const since = time(row.last_seen_at);
    if (since === null) return "No run yet";
    const minutes = Math.floor((now - since) / 60000);
    if (minutes < 1) return "Last synced just now";
    if (minutes < 60) return `Last synced ${minutes} minute${minutes === 1 ? "" : "s"} ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `Last synced ${hours} hour${hours === 1 ? "" : "s"} ago`;
    const days = Math.floor(hours / 24);
    return `Last synced ${days} day${days === 1 ? "" : "s"} ago`;
  }

  return { isStale, lastSynced, STALE_DAYS };
});
