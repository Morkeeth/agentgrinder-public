/* Free Lunch visits. Free Lunch sends a visitor here with ?fair_challenge=<id>. On the same
   person's day-two visit, it also sends ?fair_return_token=<capability>. The pair is kept for this
   tab only and taken out of the address at once, so a copied or shared link never carries either.
   When the visitor finishes a real action (a saved run, or an "Anyone with the link" card), the
   page asks STRIVE's server to confirm it (api/fair/confirm.js). The server checks the action and
   signs; the page never holds a secret. No stored id means no call at all. */
(function (root) {
  "use strict";
  const KEY = "strive_fair_visit";
  const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  const RETURN_TOKEN = /^[a-f0-9]{64}$/;

  function capture() {
    try {
      const url = new URL(root.location.href);
      const id = url.searchParams.get("fair_challenge");
      const token = url.searchParams.get("fair_return_token");
      if (id === null && token === null) return;
      // Remove only these capabilities and keep the rest as typed (URLSearchParams would turn
      // ?post into ?post=). A token is accepted only as part of the challenge it came beside.
      const rest = url.search.slice(1).split("&").filter((part) => part && !/^fair_challenge(=|$)/.test(part) && !/^fair_return_token(=|$)/.test(part)).join("&");
      root.history.replaceState(root.history.state, "", url.pathname + (rest ? "?" + rest : "") + url.hash);
      if (UUID.test(id) && (token === null || RETURN_TOKEN.test(token))) {
        root.sessionStorage.setItem(KEY, JSON.stringify({ challengeId: id, ...(token ? { returnToken: token } : {}) }));
      } else root.sessionStorage.removeItem(KEY);
    } catch (_) {}
  }
  function pendingVisit() {
    try {
      const visit = JSON.parse(root.sessionStorage.getItem(KEY) || "null");
      if (!visit || !UUID.test(visit.challengeId)) return null;
      if (visit.returnToken !== undefined && !RETURN_TOKEN.test(visit.returnToken)) return null;
      return visit;
    } catch (_) { return null; }
  }
  function pending() {
    return pendingVisit()?.challengeId || null;
  }

  // kind is "run" or "link". A run needs the visitor's accessToken (it must be theirs); a link needs
  // the ticket STRIVE returned when this visitor made it.
  async function confirm(kind, id, accessToken, ticket) {
    const visit = pendingVisit();
    if (!visit) return null;
    try {
      const res = await fetch("/api/fair/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(accessToken ? { Authorization: "Bearer " + accessToken } : {}) },
        body: JSON.stringify({ challengeId: visit.challengeId, kind, id, ...(ticket ? { ticket } : {}), ...(visit.returnToken ? { returnToken: visit.returnToken } : {}) }),
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
