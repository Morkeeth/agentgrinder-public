// POST /api/connect/device and POST /api/connect/token: RFC 8628 device pairing for STRIVE.
// Connect once on the device, approve once on a phone, then sync forever.
//
// Like server/agent-upload.mjs this server holds no extra power. It forwards to the strava
// schema with the public anon key; the database mints the codes, enforces the 900 second window
// and the poll interval, and hands the credential over exactly once. Nothing here is logged: a
// device code is a secret and a user code is about to become one.
const HARNESSES = new Set(["cursor", "codex", "claude", "grokbot", "other"]);
const SCOPES = new Set(["draft", "publish"]);
export const MAX_BYTES = 2048;
export const DEVICE_GRANT = "urn:ietf:params:oauth:grant-type:device_code";
// RFC 8628 section 3.5, plus invalid_grant for a code we are not holding an answer for.
export const POLL_ERRORS = {
  authorization_pending: "Approve this device in STRIVE, then poll again.",
  slow_down: "Poll no faster than the interval you were given.",
  access_denied: "The request was denied in STRIVE.",
  expired_token: "That code expired. Start the connection again on the device.",
  invalid_grant: "That device code is not waiting for a credential.",
};

function refusal(message) {
  if (/Too many connection requests/.test(message)) return { status: 429, error: "slow_down" };
  return { status: 400, error: "invalid_request" };
}

function guard({ method, headers, body }) {
  if (method !== "POST") return { status: 405, headers: { Allow: "POST" }, body: { error: "invalid_request", error_description: "Use POST." } };
  if (Number(headers?.["content-length"] || 0) > MAX_BYTES || (body && Buffer.byteLength(JSON.stringify(body), "utf8") > MAX_BYTES))
    return { status: 413, body: { error: "invalid_request", error_description: "Send a short JSON or form body." } };
  if (!body || typeof body !== "object" || Array.isArray(body))
    return { status: 400, body: { error: "invalid_request", error_description: "Send one JSON object." } };
  return null;
}

async function rpc(name, args, { SB_URL, SB_KEY }, fetchImpl) {
  let response;
  try {
    response = await fetchImpl(SB_URL + "/rest/v1/rpc/" + name, {
      method: "POST",
      headers: { "Content-Type": "application/json", apikey: SB_KEY, "Content-Profile": "strava" },
      body: JSON.stringify(args),
      signal: AbortSignal.timeout(15000),
      cache: "no-store",
    });
  } catch {
    return { failed: { status: 503, body: { error: "temporarily_unavailable", error_description: "STRIVE is unavailable. Try again." } } };
  }
  let result = null;
  try {
    result = await response.json();
  } catch {}
  if (!response.ok) {
    const message = typeof result?.message === "string" ? result.message.slice(0, 300) : "The request was refused.";
    const mapped = refusal(message);
    return { failed: { status: response.status >= 500 ? 502 : mapped.status, body: { error: mapped.error, error_description: message } } };
  }
  return { result };
}

// Step one. The device asks for a pair of codes and is told where a human should go.
export async function deviceStart({ method, headers, body }, config, fetchImpl = fetch) {
  const stop = guard({ method, headers, body });
  if (stop) return stop;
  const harness = String(body.harness || "").trim().toLowerCase();
  if (!HARNESSES.has(harness))
    return { status: 400, body: { error: "invalid_request", error_description: "Name the harness: cursor, codex, claude, grokbot or other." } };
  const device_name = String(body.device_name || "").trim();
  if (!device_name || device_name.length > 40)
    return { status: 400, body: { error: "invalid_request", error_description: "Send a device_name of 1 to 40 characters." } };
  const asked = Array.isArray(body.scopes) ? body.scopes : String(body.scope || "draft publish").split(/\s+/);
  const scopes = asked.map((scope) => String(scope).trim()).filter(Boolean);
  if (!scopes.length || !scopes.every((scope) => SCOPES.has(scope)))
    return { status: 400, body: { error: "invalid_scope", error_description: "Device pairing grants draft and publish only." } };
  const { result, failed } = await rpc(
    "connect_device_start",
    { p_harness: harness, p_device_name: device_name, p_scopes: scopes },
    config,
    fetchImpl,
  );
  if (failed) return failed;
  if (!result || typeof result.device_code !== "string" || typeof result.user_code !== "string")
    return { status: 502, body: { error: "temporarily_unavailable", error_description: "STRIVE returned an unexpected response." } };
  const verification_uri = config.ORIGIN + "/?pair";
  return {
    status: 200,
    body: {
      device_code: result.device_code,
      user_code: result.user_code,
      verification_uri,
      verification_uri_complete: verification_uri + "=" + encodeURIComponent(result.user_code),
      expires_in: result.expires_in,
      interval: result.interval,
    },
  };
}

// Step two. The device polls. Every answer but the credential is an RFC 8628 error code.
export async function devicePoll({ method, headers, body }, config, fetchImpl = fetch) {
  const stop = guard({ method, headers, body });
  if (stop) return stop;
  if (body.grant_type !== undefined && body.grant_type !== DEVICE_GRANT)
    return { status: 400, body: { error: "unsupported_grant_type", error_description: "Use grant_type " + DEVICE_GRANT + "." } };
  const device_code = String(body.device_code || "");
  if (!/^dc_[0-9a-f-]{10,80}$/.test(device_code))
    return { status: 400, body: { error: "invalid_request", error_description: "Send the device_code from /api/connect/device." } };
  const { result, failed } = await rpc("connect_device_poll", { p_device_code: device_code }, config, fetchImpl);
  if (failed) return failed;
  if (result && typeof result.error === "string") {
    const known = POLL_ERRORS[result.error] ? result.error : "invalid_grant";
    const out = { error: known, error_description: POLL_ERRORS[known] };
    if (result.interval) out.interval = result.interval;
    return { status: 400, body: out };
  }
  if (!result || typeof result.access_token !== "string")
    return { status: 502, body: { error: "temporarily_unavailable", error_description: "STRIVE returned an unexpected response." } };
  return {
    status: 200,
    body: {
      access_token: result.access_token,
      token_type: "bearer",
      expires_in: result.expires_in,
      scope: result.scope,
    },
  };
}
