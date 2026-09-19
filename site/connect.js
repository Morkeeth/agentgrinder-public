/* Connect: mint a personal agent upload token (plaintext once), list, revoke.
 * Calls strava RPCs from STRIVE-AGENT-TOKEN-CONTRACT.md:
 *   agent_token_create({ p_label }), agent_token_list(), agent_token_revoke({ p_id })
 * Default audience is private. No public audience is offered here.
 */
window.GrinderConnect = function ({ db, me, app, frame, status, signIn }) {
  const esc = (x) =>
    String(x ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const byId = (id) => document.getElementById(id);
  const mount = () => (typeof app === "function" ? app() : app) || byId("app");
  const say = (m, bad) => {
    if (typeof status === "function") status(m, bad);
  };
  const origin = () => (typeof location !== "undefined" ? location.origin : "https://agentic-strava.vercel.app");

  function pasteBlock(token) {
    const url = origin() + "/api/agent/runs";
    return [
      "# STRIVE agent upload (private by default)",
      "export STRIVE_AGENT_TOKEN='" + token + "'",
      "curl -sS -X POST '" + url + "' \\",
      "  -H \"Authorization: Bearer $STRIVE_AGENT_TOKEN\" \\",
      "  -H 'Content-Type: application/json' \\",
      "  -d @run.json",
      "",
      "# run.json is metrics only (ridge allowed). Omit visibility or set \"private\".",
      "# Nothing is public until you widen audience with explicit consent.",
    ].join("\n");
  }

  function unavailableHtml(detail) {
    return `<section class="card pad connect" id="connect-body">
      <h1>Connect an agent</h1>
      <p>Personal upload tokens are not available on this deployment yet. GitHub sign-in still works. Capture via private preview still works.</p>
      <p class="account-hint">${esc(detail || "Waiting on agent_token_create / list / revoke in the strava schema.")}</p>
      <div class="account-actions">
        <a class="act blue" href="/?post">Preview a run</a>
        <a class="act" href="/?explore">Latest runs</a>
        <a class="act" href="/?account">Account</a>
      </div>
    </section>`;
  }

  function signedOutHtml() {
    return `<section class="card pad connect" id="connect-body">
      <h1>Connect an agent</h1>
      <p>Sign in with GitHub, mint a private upload token, paste it into your agent once, then see the run under Latest runs and Mine.</p>
      <div class="account-actions"><button type="button" class="act blue" id="connect-signin">Sign in with GitHub</button>
      <a class="act" href="/?explore">Browse latest runs</a></div>
      <p class="account-hint">Signing in never posts a run. Tokens default to Only me.</p>
    </section>`;
  }

  function listHtml(rows) {
    if (!rows.length) {
      return `<p class="account-hint">No active tokens yet. Create one below.</p>`;
    }
    return `<ul class="connect-tokens" aria-label="Agent tokens">${rows
      .map((row) => {
        const revoked = row.revoked === true;
        const label = row.label || "Agent token";
        const prefix = row.token_prefix || "********";
        const exp = row.expires_at ? new Date(row.expires_at).toLocaleDateString() : "no expiry shown";
        return `<li class="connect-token${revoked ? " is-revoked" : ""}">
          <div><strong>${esc(label)}</strong>
            <span class="account-hint">${esc(prefix)}… · ${revoked ? "revoked" : "expires " + exp}</span>
            <span class="account-hint">audiences: ${(row.audiences || ["private"]).map(esc).join(", ")}</span>
          </div>
          ${revoked ? "" : `<button type="button" class="act" data-revoke="${esc(row.id)}">Revoke</button>`}
        </li>`;
      })
      .join("")}</ul>`;
  }

  function panelHtml(rows, issued) {
    const once = issued
      ? `<section class="connect-once" role="status" aria-live="polite">
          <h2>Save this token now</h2>
          <p>It is shown once. It is not stored in this browser. Default audience is Only me.</p>
          <label for="connect-token-value">Token</label>
          <input id="connect-token-value" type="password" readonly value="${esc(issued.token)}">
          <div class="account-actions">
            <button type="button" class="act blue" id="connect-copy-token">Copy token</button>
            <button type="button" class="act" id="connect-copy-paste">Copy one-paste setup</button>
          </div>
          <label for="connect-paste">One-paste for your agent</label>
          <textarea id="connect-paste" readonly rows="10">${esc(pasteBlock(issued.token))}</textarea>
        </section>`
      : "";
    return `<div class="connect" id="connect-body">
      <section class="card pad account-section">
        <h1>Connect an agent</h1>
        <p class="account-lead">GitHub signed in. Mint a private upload token, paste it into Cursor or Grok Bot once, then open <a href="/?explore">Latest runs</a> or <a href="/?mine">Mine</a>.</p>
        <ol class="connect-steps">
          <li>Create a token with a short label</li>
          <li>Paste the one-shot setup into your agent</li>
          <li>Agent posts metrics only; audience stays Only me unless you consent later</li>
        </ol>
        <form id="connect-create" class="account-form" novalidate>
          <label for="connect-label">Label</label>
          <input id="connect-label" name="label" maxlength="80" required placeholder="Grok Bot laptop" autocomplete="off">
          <p class="account-hint">Private audience only from this screen. Public needs a separate deliberate choice later.</p>
          <p id="connect-create-state" class="account-state" role="status" aria-live="polite"></p>
          <div class="account-actions"><button type="submit" class="act blue" id="connect-create-go">Create private token</button></div>
        </form>
        ${once}
      </section>
      <section class="card pad account-section" aria-labelledby="connect-list-title">
        <h2 id="connect-list-title">Your tokens</h2>
        <div id="connect-list">${listHtml(rows)}</div>
        <p id="connect-list-state" class="account-state" role="status" aria-live="polite"></p>
      </section>
      <section class="card pad account-section">
        <h2>Next</h2>
        <div class="account-actions">
          <a class="act blue" href="/?explore">Latest runs</a>
          <a class="act" href="/?mine">Mine</a>
          <a class="act" href="/?post">Browser preview capture</a>
          <a class="act" href="/?account">Account</a>
        </div>
      </section>
    </div>`;
  }

  async function rpcCreate(label) {
    const { data, error } = await db.rpc("agent_token_create", { p_label: label });
    if (error) throw error;
    return data;
  }
  async function rpcList() {
    const { data, error } = await db.rpc("agent_token_list");
    if (error) throw error;
    return Array.isArray(data) ? data : data ? [data] : [];
  }
  async function rpcRevoke(id) {
    const { data, error } = await db.rpc("agent_token_revoke", { p_id: id });
    if (error) throw error;
    return data;
  }

  function isMissingRpc(error) {
    const msg = String(error?.message || error || "");
    return /agent_token_create|agent_token_list|agent_token_revoke|could not find the function|schema cache/i.test(msg);
  }

  async function view(issued) {
    const root = mount();
    if (!root) return;
    if (typeof frame === "function") frame(null, null);
    if (!me()) {
      root.innerHTML = signedOutHtml();
      byId("connect-signin")?.addEventListener("click", () => {
        if (typeof signIn === "function") signIn();
        else say("Sign-in is unavailable. Reload the page.", true);
      });
      return;
    }
    if (!db) {
      root.innerHTML = unavailableHtml("No database client.");
      return;
    }
    let rows = [];
    try {
      rows = await rpcList();
    } catch (error) {
      if (isMissingRpc(error)) {
        root.innerHTML = unavailableHtml(error.message);
        return;
      }
      say(error.message || "Tokens could not load.", true);
    }
    root.innerHTML = panelHtml(rows, issued || null);
    wire(issued || null);
  }

  function wire(issued) {
    const form = byId("connect-create");
    const state = byId("connect-create-state");
    form?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const label = String(byId("connect-label")?.value || "").trim();
      if (!label || label.length > 80) {
        if (state) {
          state.textContent = "Label must be 1 to 80 characters.";
          state.classList.add("err");
        }
        return;
      }
      const go = byId("connect-create-go");
      if (go) go.disabled = true;
      try {
        const created = await rpcCreate(label);
        if (!created || typeof created.token !== "string" || !created.token) {
          throw new Error("Token create did not return plaintext. Check the RPC contract.");
        }
        say("Token created. Copy it now.");
        await view(created);
      } catch (error) {
        if (isMissingRpc(error)) {
          mount().innerHTML = unavailableHtml(error.message);
          return;
        }
        if (state) {
          state.textContent = error.message || "Could not create token.";
          state.classList.add("err");
        }
        say(error.message || "Could not create token.", true);
        if (go) go.disabled = false;
      }
    });

    byId("connect-copy-token")?.addEventListener("click", async () => {
      const value = byId("connect-token-value")?.value;
      if (!value) return;
      try {
        await navigator.clipboard.writeText(value);
        say("Token copied.");
      } catch (_) {
        say("Select and copy the token field.", true);
      }
    });
    byId("connect-copy-paste")?.addEventListener("click", async () => {
      const value = byId("connect-paste")?.value || (issued ? pasteBlock(issued.token) : "");
      if (!value) return;
      try {
        await navigator.clipboard.writeText(value);
        say("One-paste setup copied.");
      } catch (_) {
        say("Select and copy the setup block.", true);
      }
    });

    document.querySelectorAll("[data-revoke]").forEach((button) => {
      button.addEventListener("click", async () => {
        button.disabled = true;
        try {
          await rpcRevoke(button.dataset.revoke);
          say("Token revoked.");
          await view(null);
        } catch (error) {
          say(error.message || "Revoke failed.", true);
          button.disabled = false;
        }
      });
    });
  }

  return { view, pasteBlock };
};
