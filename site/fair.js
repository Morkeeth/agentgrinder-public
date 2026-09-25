/* Free Lunch visits. Free Lunch sends a visitor here with ?fair_challenge=<id>. The id is kept for
   this tab only and taken out of the address at once, so a copied or shared link never carries it.
   When the visitor finishes a real action (a saved run, or an "Anyone with the link" card), the
   page asks STRIVE's server to confirm it (api/fair/confirm.js). The server checks the action and
   signs; the page never holds a secret. No stored id means no call at all. */
(function (root) {
  "use strict";
  const KEY = "strive_fair_challenge";
  const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

  function capture() {
    try {
      const url = new URL(root.location.href);
      const id = url.searchParams.get("fair_challenge");
      if (id === null) return;
      // Remove only this parameter and keep the rest as typed (URLSearchParams would turn ?post into ?post=).
      const rest = url.search.slice(1).split("&").filter((part) => part && !/^fair_challenge(=|$)/.test(part)).join("&");
      root.history.replaceState(root.history.state, "", url.pathname + (rest ? "?" + rest : "") + url.hash);
      if (UUID.test(id)) root.sessionStorage.setItem(KEY, id);
    } catch (_) {}
  }
  function pending() {
    try { const id = root.sessionStorage.getItem(KEY); return id && UUID.test(id) ? id : null; } catch (_) { return null; }
  }

  // kind is "run" or "link". A run needs the visitor's accessToken (it must be theirs); a link needs
  // the ticket STRIVE returned when this visitor made it.
  async function confirm(kind, id, accessToken, ticket) {
    const challengeId = pending();
    if (!challengeId) return null;
    try {
      const res = await fetch("/api/fair/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(accessToken ? { Authorization: "Bearer " + accessToken } : {}) },
        body: JSON.stringify({ challengeId, kind, id, ...(ticket ? { ticket } : {}) }),
      });
      const body = await res.json().catch(() => ({}));
      // One challenge, one confirmation: done, closed or refused, it is not tried again.
      if (body.confirmed || res.status === 409) root.sessionStorage.removeItem(KEY);
      return body;
    } catch (_) { return null; }
  }

  capture();
  root.StriveFair = { capture, pending, confirm };
})(typeof window !== "undefined" ? window : globalThis);
