/* Approve a device: /?pair=<code>, the human half of RFC 8628.
 *
 * The device asked for a code and is polling. This page is where a signed-in person reads what
 * is being asked for - which harness, which device name, which scopes - and presses Approve or
 * Deny. Nothing about the run, the project or the machine is shown, because nothing about them
 * is stored: the pairing holds a hash, a harness and the name the device gave itself.
 *
 * Phone first at 390px. It also carries a QR of its own address so the desktop that started the
 * pairing can hand the approval to the phone in the owner's pocket.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.GrinderPair = factory();
})(typeof window !== "undefined" ? window : globalThis, function () {
  const ALPHABET = "BCDFGHJKLMNPQRSTVWXZ";
  const CODE = new RegExp("^[" + ALPHABET + "]{8}$");
  const HARNESS = {
    cursor: "Cursor",
    codex: "Codex",
    claude: "Claude Code",
    grokbot: "Grok Bot",
    other: "Another harness",
  };
  const SCOPE_WORDS = {
    draft: "save a private draft",
    publish: "upload a run as Only me",
  };

  // Typed on a phone: lower case, spaces and the dash people add in the middle all clean up.
  function normalize(raw) {
    return String(raw ?? "")
      .toUpperCase()
      .replace(/[^A-Z]/g, "");
  }
  function harnessLabel(harness) {
    return HARNESS[harness] || "Another harness";
  }
  function scopeLines(scopes) {
    const list = Array.isArray(scopes) ? scopes : [];
    return list.map((scope) => SCOPE_WORDS[scope] || scope);
  }

  function create({ db, me, app, frame, status, signInGitHub, signIn, qr, origin }) {
    const esc = (value) =>
      String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
    const byId = (id) => document.getElementById(id);
    const mount = () => (typeof app === "function" ? app() : app) || byId("app");
    const say = (message, bad) => {
      if (typeof status === "function") status(message, bad);
    };
    const site = () =>
      origin || (typeof location !== "undefined" && location.origin) || "https://agentic-strava.vercel.app";
    const completeUri = (code) => site() + "/?pair=" + code;

    function qrBlock(code) {
      const encoder = qr || (typeof window !== "undefined" ? window.GrinderQR : null);
      if (!encoder) return "";
      let drawing = "";
      try {
        drawing = encoder.svg(completeUri(code), { label: "Open this approval on your phone" });
      } catch (_) {
        return "";
      }
      return `<section class="pair-qr" aria-labelledby="pair-qr-title">
        <h2 id="pair-qr-title">On a computer? Finish on your phone</h2>
        ${drawing}
        <p class="account-hint">Scan this with the phone you are signed in on. It opens this same approval.</p>
      </section>`;
    }

    function askForCodeHtml(invalid) {
      return `<section class="card pad pair" id="pair-body">
        <h1>Approve a device</h1>
        <p>Your agent showed an eight character code. Type it here to see what it is asking for.</p>
        <form id="pair-code-form" class="account-form" novalidate>
          <label for="pair-code">Device code</label>
          <input id="pair-code" name="code" inputmode="latin" autocapitalize="characters" autocomplete="off"
            spellcheck="false" maxlength="11" required placeholder="BCDF GHJK">
          <p id="pair-code-state" class="account-state" role="status" aria-live="polite">${
            invalid ? "That code is eight letters, no vowels and no digits." : ""
          }</p>
          <div class="account-actions"><button type="submit" class="act blue">See the request</button>
          <a class="act" href="/?connect">Your connections</a></div>
        </form>
      </section>`;
    }

    function signedOutHtml(code) {
      return `<section class="card pad pair" id="pair-body">
        <h1>Approve a device</h1>
        <p>Sign in as the owner of this account to approve <strong>${esc(code)}</strong>. Approving grants a private
        upload credential to one device. It never posts a run.</p>
        <div class="account-actions"><button type="button" class="act blue" id="pair-signin">Sign in with GitHub</button>
        <a class="act" href="/?connect">Your connections</a></div>
        <p class="account-hint">You will come back to this code after signing in.</p>
        ${qrBlock(code)}
      </section>`;
    }

    function unavailableHtml(detail) {
      return `<section class="card pad pair" id="pair-body">
        <h1>Approve a device</h1>
        <p>Device pairing is not available on this deployment yet. Local capture and preview still work.</p>
        <p class="account-hint">${esc(detail || "Waiting on connect_pairing_view / connect_pairing_decide.")}</p>
        <div class="account-actions"><a class="act blue" href="/?connect">Your connections</a>
        <a class="act" href="/?post">Preview a run</a></div>
      </section>`;
    }

    function settledHtml(code, view, decided) {
      const done = {
        approved: {
          title: "Approved",
          line: "The device is collecting its credential now. It stays a private upload credential until you revoke it.",
        },
        claimed: {
          title: "Connected",
          line: "This device has its credential. Its runs arrive as Only me.",
        },
        denied: { title: "Denied", line: "No credential was issued. The device is told the request was denied." },
        expired: { title: "That code expired", line: "A code lasts 15 minutes. Start the connection again on the device." },
      }[view.status] || { title: "Nothing to approve", line: "This code has already been answered." };
      return `<section class="card pad pair" id="pair-body">
        <h1>${esc(done.title)}</h1>
        <p>${esc(done.line)}</p>
        ${decided ? "" : `<p class="account-hint">Code ${esc(code)}.</p>`}
        <div class="account-actions"><a class="act blue" href="/?connect">Your connections</a>
        <a class="act" href="/?mine">My runs</a></div>
      </section>`;
    }

    function requestHtml(code, view) {
      const scopes = scopeLines(view.scopes);
      const minutes = Math.max(1, Math.round((Number(view.expires_in) || 0) / 60));
      return `<section class="card pad pair" id="pair-body">
        <h1>Connect this device?</h1>
        <dl class="pair-facts">
          <dt>Device</dt><dd>${esc(view.device_name)}</dd>
          <dt>Harness</dt><dd>${esc(harnessLabel(view.harness))}</dd>
          <dt>Code</dt><dd class="pair-code-shown">${esc(code)}</dd>
        </dl>
        <h2>It will be able to</h2>
        <ul class="pair-scopes">${scopes.map((line) => `<li>${esc(line)}</li>`).join("")}</ul>
        <p class="account-hint">Nothing else. It cannot make a run public, follow anyone, reply or read your other runs.
        Uploads carry counts and allowlisted fields only. Expires in about ${minutes} minute${minutes === 1 ? "" : "s"}.</p>
        <div class="pair-decide">
          <button type="button" class="act blue" id="pair-approve">Approve</button>
          <button type="button" class="act" id="pair-deny">Deny</button>
        </div>
        <p id="pair-state" class="account-state" role="status" aria-live="polite"></p>
        ${qrBlock(code)}
      </section>`;
    }

    function isMissingRpc(error) {
      const message = String(error?.message || error || "");
      return /connect_pairing_view|connect_pairing_decide|could not find the function|schema cache/i.test(message);
    }

    function startSignIn() {
      if (typeof signInGitHub === "function") signInGitHub();
      else if (typeof signIn === "function") signIn();
      else say("Sign-in is unavailable. Reload the page.", true);
    }

    async function view(raw) {
      const root = mount();
      if (!root) return;
      if (typeof frame === "function") frame(null, null);
      const code = normalize(raw);
      if (!code) {
        root.innerHTML = askForCodeHtml(false);
        wireCodeForm();
        return;
      }
      if (!CODE.test(code)) {
        root.innerHTML = askForCodeHtml(true);
        wireCodeForm();
        return;
      }
      if (!me()) {
        root.innerHTML = signedOutHtml(code);
        byId("pair-signin")?.addEventListener("click", startSignIn);
        return;
      }
      if (!db) {
        root.innerHTML = unavailableHtml("No database client.");
        return;
      }
      let pairing;
      try {
        const { data, error } = await db.rpc("connect_pairing_view", { p_user_code: code });
        if (error) throw error;
        pairing = data;
      } catch (error) {
        if (isMissingRpc(error)) {
          root.innerHTML = unavailableHtml(error.message);
          return;
        }
        root.innerHTML = askForCodeHtml(false);
        wireCodeForm();
        const state = byId("pair-code-state");
        if (state) {
          state.textContent = error.message || "That code could not be read.";
          state.classList.add("err");
        }
        return;
      }
      if (!pairing || pairing.status !== "pending") {
        root.innerHTML = settledHtml(code, pairing || {}, false);
        return;
      }
      root.innerHTML = requestHtml(code, pairing);
      wireDecide(code, pairing);
    }

    function wireCodeForm() {
      byId("pair-code-form")?.addEventListener("submit", (event) => {
        event.preventDefault();
        const code = normalize(byId("pair-code")?.value);
        if (!CODE.test(code)) {
          const state = byId("pair-code-state");
          if (state) {
            state.textContent = "That code is eight letters, no vowels and no digits.";
            state.classList.add("err");
          }
          return;
        }
        history.pushState(null, "", "/?pair=" + code);
        view(code);
      });
    }

    function wireDecide(code, pairing) {
      const decide = async (approve) => {
        const approveButton = byId("pair-approve");
        const denyButton = byId("pair-deny");
        const state = byId("pair-state");
        if (approveButton) approveButton.disabled = true;
        if (denyButton) denyButton.disabled = true;
        try {
          const { data, error } = await db.rpc("connect_pairing_decide", { p_user_code: code, p_approve: approve });
          if (error) throw error;
          say(approve ? "Approved. The device is collecting its credential." : "Denied. No credential was issued.");
          mount().innerHTML = settledHtml(code, { ...pairing, status: data?.status || (approve ? "approved" : "denied") }, true);
        } catch (error) {
          if (state) {
            state.textContent = error.message || "That decision could not be recorded.";
            state.classList.add("err");
          }
          say(error.message || "That decision could not be recorded.", true);
          if (approveButton) approveButton.disabled = false;
          if (denyButton) denyButton.disabled = false;
        }
      };
      byId("pair-approve")?.addEventListener("click", () => decide(true));
      byId("pair-deny")?.addEventListener("click", () => decide(false));
    }

    return { view, normalize, completeUri };
  }

  // The page calls GrinderPair(...); the helpers are exported for tests.
  const api = (options) => create(options);
  api.create = create;
  api.normalize = normalize;
  api.harnessLabel = harnessLabel;
  api.scopeLines = scopeLines;
  api.ALPHABET = ALPHABET;
  return api;
});
