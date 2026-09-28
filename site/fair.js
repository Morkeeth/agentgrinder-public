/* Free Lunch visits. Free Lunch sends a visitor here with ?fair_challenge=<id>. The id is kept for
   fifteen minutes and taken out of the address at once, so a copied or shared link never carries it.
   When the visitor finishes a real action (a saved run, or an "Anyone with the link" card), the
   page asks STRIVE's server to confirm it (api/fair/confirm.js). The server checks the action and
   signs; the page never holds STRIVE's signing key. No stored id means no call at all. */
(function (root) {
  "use strict";
  const KEY = "strive_fair_challenge";
  const RETURN_KEY = "strive_fair_return_token";
  const TTL_MS = 900000;
  const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  // Free Lunch's day-two capability. STRIVE copies it back unchanged and never interprets it.
  const TOKEN = /^[A-Za-z0-9._~+/=-]{16,400}$/;

  function clear() {
    try {
      root.localStorage.removeItem(KEY);
      root.localStorage.removeItem(RETURN_KEY);
    } catch (_) {}
  }

  function readHeld(key, field, pattern) {
    try {
      const raw = root.localStorage.getItem(key);
      if (!raw) return null;
      const held = JSON.parse(raw);
      if (!held || !pattern.test(held[field]) || !Number.isFinite(held.until) || Date.now() > held.until) {
        root.localStorage.removeItem(key);
        return null;
      }
      return held[field];
    } catch (_) {
      try { root.localStorage.removeItem(key); } catch (_) {}
      return null;
    }
  }

  function capture() {
    try {
      const url = new URL(root.location.href);
      const id = url.searchParams.get("fair_challenge");
      const token = url.searchParams.get("fair_return_token");
      if (id === null && token === null) return;
      // Remove only these parameters and keep the rest as typed (URLSearchParams would turn ?post into ?post=).
      const rest = url.search.slice(1).split("&")
        .filter((part) => part && !/^fair_challenge(=|$)/.test(part) && !/^fair_return_token(=|$)/.test(part))
        .join("&");
      root.history.replaceState(root.history.state, "", url.pathname + (rest ? "?" + rest : "") + url.hash);
      if (!UUID.test(id || "")) { clear(); return; }
      const until = Date.now() + TTL_MS;
      // `agentgrinder grind --push` opens a new tab. localStorage keeps the visit across that tab
      // boundary, while the matching expiry stops it outliving Free Lunch's challenge.
      root.localStorage.setItem(KEY, JSON.stringify({ id, until }));
      if (token !== null && TOKEN.test(token)) root.localStorage.setItem(RETURN_KEY, JSON.stringify({ token, until }));
      else root.localStorage.removeItem(RETURN_KEY);
    } catch (_) {}
  }
  function pending() {
    const id = readHeld(KEY, "id", UUID);
    if (!id) {
      try { root.localStorage.removeItem(RETURN_KEY); } catch (_) {}
    }
    return id;
  }

  // kind is "run" or "link". A run needs the visitor's accessToken (it must be theirs); a link needs
  // the ticket STRIVE returned when this visitor made it.
  async function confirm(kind, id, accessToken, ticket) {
    const challengeId = pending();
    if (!challengeId) return null;
    const returnToken = readHeld(RETURN_KEY, "token", TOKEN);
    try {
      const res = await fetch("/api/fair/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(accessToken ? { Authorization: "Bearer " + accessToken } : {}) },
        body: JSON.stringify({ challengeId, kind, id, ...(ticket ? { ticket } : {}), ...(returnToken ? { returnToken } : {}) }),
      });
      const body = await res.json().catch(() => ({}));
      // One challenge, one confirmation: done, closed or refused, it is not tried again.
      if (body.confirmed || res.status === 409) clear();
      return body;
    } catch (_) { return null; }
  }

  capture();
  root.StriveFair = { capture, pending, confirm };
})(typeof window !== "undefined" ? window : globalThis);
