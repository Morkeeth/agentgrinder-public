/* Strava identity: provider-neutral sign-in, onboarding, identity linking, profile presentation
 * and local sign-out. Uses the page's existing Supabase client (db.schema = strava, its own
 * auth storage key). Never creates a client and never holds a key.
 *
 * Contract for other lanes (see RETURN.md):
 *   GrinderAuth.present(profileRow) -> {id, handle, display_name, avatar_url, legacy}
 *   profile.id is the stable identity; handle/display_name fall back to github_handle/name.
 *
 * A handle is a label chosen by the owner. It never proves ownership of a GitHub or X account:
 * github_handle is written only from a real GitHub identity on the signed-in Auth user.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.GrinderAuth = factory();
})(typeof window !== "undefined" ? window : globalThis, function () {
  // Providers this app can offer. Cursor is deliberately absent: cursor.com documents Cursor
  // only as a consumer of identity (SSO, CLI login), never as an identity provider for other
  // sites, so there is no honest "Sign in with Cursor" button. Repository connection is a
  // separate planned feature, not a login.
  const PROVIDERS = Object.freeze([
    { id: "github", label: "GitHub", kind: "oauth" },
    { id: "x", label: "X", kind: "oauth" },
    { id: "email", label: "Email link", kind: "otp" },
  ]);
  const OAUTH = new Set(["github", "x"]);
  const HANDLE_RE = /^[a-z0-9]([a-z0-9_-]{0,38}[a-z0-9])?$/;
  const HANDLE_KEYS = ["user_name", "preferred_username", "screen_name", "username", "login"];
  const NAME_KEYS = ["full_name", "name", "display_name"];
  const AVATAR_KEYS = ["avatar_url", "picture", "profile_image_url"];

  const str = (v) => (typeof v === "string" ? v.trim() : "");
  const pick = (obj, keys) => {
    for (const k of keys) if (str(obj?.[k])) return str(obj[k]);
    return "";
  };

  /* ---------- pure helpers (no client) ---------- */

  function normalizeHandle(input, fallbackSeed) {
    let h = str(input)
      .toLowerCase()
      .replace(/^@+/, "")
      .replace(/[^a-z0-9_-]+/g, "-")
      .replace(/-{2,}/g, "-")
      .replace(/^[-_]+|[-_]+$/g, "")
      .slice(0, 40)
      .replace(/[-_]+$/g, "");
    if (!h && fallbackSeed) h = "builder-" + String(fallbackSeed).replace(/[^a-z0-9]/gi, "").slice(0, 8).toLowerCase();
    return HANDLE_RE.test(h) ? h : "";
  }
  function normalizeDisplayName(input, fallback) {
    let n = str(input).replace(/\s+/g, " ").slice(0, 60).trim();
    if (!n || n.includes("@")) n = str(fallback).slice(0, 60);
    return n || "";
  }
  function normalizeAvatarUrl(input) {
    const u = str(input);
    if (!u || u.length > 2048 || /\s/.test(u)) return null;
    return /^https:\/\/\S+$/.test(u) ? u : null;
  }
  function validateHandle(input) {
    const h = str(input).toLowerCase().replace(/^@+/, "");
    if (!h) return { ok: false, code: "handle_required", message: "Choose a handle." };
    if (h.length > 40) return { ok: false, code: "handle_too_long", message: "Handles are at most 40 characters." };
    if (!HANDLE_RE.test(h)) return { ok: false, code: "handle_format", message: "Use letters, numbers, - or _, starting and ending with a letter or number." };
    return { ok: true, handle: h };
  }

  // Identities on the Auth user, with provider data normalised. identity_data key names for X
  // are not confirmed by Supabase docs; several candidates are read, none is required.
  function identitiesOf(user) {
    const list = Array.isArray(user?.identities) ? user.identities : [];
    return list.map((i) => {
      const d = i.identity_data || {};
      return {
        id: i.identity_id || i.id || null,
        provider: i.provider || "",
        handle: pick(d, HANDLE_KEYS),
        name: pick(d, NAME_KEYS),
        avatar_url: normalizeAvatarUrl(pick(d, AVATAR_KEYS)),
        email: str(d.email) || null,
      };
    });
  }
  // The github_handle column is written only from a GitHub identity, never from a chosen handle.
  function githubHandleOf(user) {
    const gh = identitiesOf(user).find((i) => i.provider === "github");
    const h = gh ? gh.handle : "";
    return /^[a-z0-9_-]{1,60}$/i.test(h) ? h : null;
  }
  // Suggested onboarding values. The owner confirms or edits them; nothing is saved here.
  function suggest(user) {
    const ids = identitiesOf(user);
    const meta = user?.user_metadata || {};
    const first = ids.find((i) => i.handle) || ids.find((i) => i.name) || ids[0] || {};
    const seed = user?.id || "";
    const handle = normalizeHandle(first.handle || pick(meta, HANDLE_KEYS) || pick(meta, NAME_KEYS), seed);
    const display_name = normalizeDisplayName(first.name || pick(meta, NAME_KEYS), handle);
    const avatar_url = first.avatar_url || normalizeAvatarUrl(pick(meta, AVATAR_KEYS));
    return { handle, display_name, avatar_url, providers: ids.map((i) => i.provider), github_handle: githubHandleOf(user) };
  }

  // Presentation contract. profile.id is stable; handle/display_name fall back to legacy columns.
  function present(p) {
    if (!p) return null;
    const handle = str(p.handle) || str(p.github_handle) || "";
    const display_name = str(p.display_name) || str(p.name) || (handle ? "@" + handle : "A builder");
    return {
      id: p.id,
      handle,
      display_name,
      avatar_url: normalizeAvatarUrl(p.avatar_url),
      legacy: !str(p.handle),
      url: handle ? "/?u=" + encodeURIComponent(handle) : "/",
    };
  }

  // Provider and database errors as codes the UI can branch on. Message text is ours.
  function explain(error) {
    if (!error) return null;
    const code = String(error.code || "");
    const msg = String(error.message || error.error_description || "");
    const m = (c, message, retry) => ({ code: c, message, retry: !!retry, raw: msg });
    if (code === "23505" || /handle_taken/.test(msg)) {
      if (/auth_uid/.test(msg)) return m("profile_exists", "You already have a profile.", true);
      return m("handle_taken", "That handle is taken. Choose another.");
    }
    if (code === "23514" || /violates check constraint/.test(msg)) {
      if (/avatar/.test(msg)) return m("avatar_invalid", "Avatar must be an https link.");
      if (/display_name/.test(msg)) return m("display_name_invalid", "Display name must be 1 to 60 characters.");
      return m("handle_format", "Use letters, numbers, - or _, starting and ending with a letter or number.");
    }
    if (code === "42501" || /row-level security|permission denied/.test(msg)) return m("forbidden", "You can only edit your own profile.");
    if (code === "manual_linking_disabled" || /manual linking/i.test(msg)) return m("linking_disabled", "Account linking is not enabled on this service yet.");
    if (code === "identity_already_exists" || /identity is already linked|already linked/i.test(msg)) return m("identity_taken", "That account is already linked to another profile. Sign in with it instead.");
    if (code === "single_identity_not_deletable" || /at least 2 linked|single identity|last identity/i.test(msg)) return m("last_identity", "Keep at least one way to sign in. Link another account before removing this one.");
    if (code === "identity_not_found") return m("identity_missing", "That linked account was not found.");
    if (code === "validation_failed" || code === "invalid_request" || /provider is not enabled|unsupported provider/i.test(msg)) return m("provider_unavailable", "That sign-in provider is not available here yet.");
    if (code === "over_email_send_rate_limit" || code === "over_request_rate_limit") return m("rate_limited", "Too many attempts. Wait a minute and try again.", true);
    if (/fetch|network|Failed to fetch|Load failed/i.test(msg)) return m("offline", "Could not connect. Check your connection and try again.", true);
    return m("unknown", "Something went wrong. Try again.", true);
  }

  /* ---------- client-bound API ---------- */

  function create({ client, redirectTo, storage } = {}) {
    if (!client || !client.auth || typeof client.from !== "function") throw new Error("GrinderAuth needs the Supabase client");
    const where = () => redirectTo || (typeof location !== "undefined" ? location.origin + "/" : undefined);
    const fail = (error) => Object.assign(new Error(explain(error).message), { detail: explain(error), cause: error });
    const memo = () => {
      try { return storage || (typeof sessionStorage !== "undefined" ? sessionStorage : null); } catch (_) { return null; }
    };
    const RETURN_KEY = "ag_auth_return";
    const remember = (v) => { const s = memo(); if (s && v != null) try { s.setItem(RETURN_KEY, String(v)); } catch (_) {} };

    async function session() {
      const { data, error } = await client.auth.getSession();
      if (error) throw fail(error);
      return data?.session || null;
    }
    async function user() {
      const s = await session();
      return s ? s.user : null;
    }

    // Start sign-in. OAuth providers redirect; email sends a link. Returns the provider used.
    async function signIn(provider, opts = {}) {
      if (OAUTH.has(provider)) {
        if (opts.returnTo) remember(opts.returnTo);
        const { error } = await client.auth.signInWithOAuth({ provider, options: { redirectTo: where(), ...(opts.options || {}) } });
        if (error) throw fail(error);
        return { provider, started: true };
      }
      if (provider === "email") {
        if (opts.returnTo) remember(opts.returnTo);
        const email = str(opts.email);
        if (!email) throw fail({ code: "validation_failed", message: "email required" });
        const { error } = await client.auth.signInWithOtp({ email, options: { emailRedirectTo: where() } });
        if (error) throw fail(error);
        return { provider, started: true, sent: true };
      }
      throw fail({ code: "validation_failed", message: "unsupported provider " + provider });
    }

    // Profile for the signed-in Auth user, or null. Never creates: onboarding is explicit.
    async function profile() {
      const u = await user();
      if (!u) return null;
      const { data, error } = await client.from("profiles").select("*").eq("auth_uid", u.id).maybeSingle();
      if (error) throw fail(error);
      return data || null;
    }
    async function current() {
      const u = await user();
      if (!u) return { user: null, profile: null, needsOnboarding: false, suggestion: null };
      const p = await profile();
      return { user: u, profile: p, needsOnboarding: !p, suggestion: p ? null : suggest(u), identities: identitiesOf(u) };
    }

    // Insert-if-missing keyed on auth_uid. profile.id never changes after this.
    async function onboard(choice = {}) {
      const u = await user();
      if (!u) throw fail({ code: "42501", message: "not signed in" });
      const existing = await profile();
      if (existing) return { profile: existing, created: false };
      const s = suggest(u);
      const v = validateHandle(choice.handle || s.handle);
      if (!v.ok) throw fail({ code: "23514", message: "check constraint " + v.code });
      const row = {
        auth_uid: u.id,
        handle: v.handle,
        display_name: normalizeDisplayName(choice.display_name, s.display_name || v.handle) || null,
        avatar_url: choice.avatar_url === undefined ? s.avatar_url : normalizeAvatarUrl(choice.avatar_url),
        github_handle: s.github_handle,
        name: normalizeDisplayName(choice.display_name, s.display_name || v.handle) || null,
      };
      const created = await client.from("profiles").insert(row).select("*").single();
      if (!created.error) return { profile: created.data, created: true };
      if (created.error.code === "23505" && /auth_uid/.test(String(created.error.message))) {
        const again = await profile();
        if (again) return { profile: again, created: false };
      }
      throw fail(created.error);
    }

    // Owner-only edit; server policies enforce it, this only scopes the statement.
    async function updateProfile(patch = {}) {
      const u = await user();
      const p = await profile();
      if (!u || !p) throw fail({ code: "42501", message: "not signed in" });
      const row = {};
      if (patch.handle !== undefined) {
        const v = validateHandle(patch.handle);
        if (!v.ok) throw fail({ code: "23514", message: "check constraint " + v.code });
        row.handle = v.handle;
      }
      if (patch.display_name !== undefined) {
        row.display_name = normalizeDisplayName(patch.display_name, "") || null;
        row.name = row.display_name;
      }
      if (patch.avatar_url !== undefined) {
        const a = normalizeAvatarUrl(patch.avatar_url);
        if (str(patch.avatar_url) && !a) throw fail({ code: "23514", message: "check constraint avatar" });
        row.avatar_url = a;
      }
      if (!Object.keys(row).length) return p;
      const { data, error } = await client.from("profiles").update(row).eq("id", p.id).eq("auth_uid", u.id).select("*").single();
      if (error) throw fail(error);
      return data;
    }

    // Public lookup for /?u=<handle>: chosen handle first, legacy github_handle second.
    async function byHandle(lookup) {
      const h = str(lookup).replace(/^@+/, "");
      if (!h) return null;
      const { data, error } = await client.rpc("strava_profile_by_handle", { lookup: h }).maybeSingle();
      if (error) throw fail(error);
      return data || null;
    }

    // Identity linking on the shared Auth user. Requires manual linking enabled on the project.
    async function identities() {
      const { data, error } = await client.auth.getUserIdentities();
      if (error) throw fail(error);
      return identitiesOf({ identities: data?.identities || [] });
    }
    async function link(provider, opts = {}) {
      if (!OAUTH.has(provider)) throw fail({ code: "validation_failed", message: "unsupported provider " + provider });
      if (opts.returnTo) remember(opts.returnTo);
      const { data, error } = await client.auth.linkIdentity({ provider, options: { redirectTo: where(), ...(opts.options || {}) } });
      if (error) throw fail(error);
      return { provider, url: data?.url || null, started: true };
    }
    async function unlink(identityId) {
      const { data, error } = await client.auth.getUserIdentities();
      if (error) throw fail(error);
      const list = data?.identities || [];
      const target = list.find((i) => (i.identity_id || i.id) === identityId);
      if (!target) throw fail({ code: "identity_not_found", message: "identity not found" });
      if (list.length < 2) throw fail({ code: "single_identity_not_deletable", message: "at least 2 linked identities" });
      const r = await client.auth.unlinkIdentity(target);
      if (r.error) throw fail(r.error);
      return { removed: identityId };
    }
    // After a GitHub link, the legacy column may be filled; it is never set from a chosen handle.
    async function syncGithubHandle() {
      const u = await user();
      const p = await profile();
      if (!u || !p) return p;
      const gh = githubHandleOf(u);
      if (!gh || p.github_handle) return p;
      const { data, error } = await client.from("profiles").update({ github_handle: gh }).eq("id", p.id).eq("auth_uid", u.id).select("*").single();
      if (error) {
        if (explain(error).code === "handle_taken") return p; // someone else's label; leave legacy column empty
        throw fail(error);
      }
      return data;
    }

    // Local sign-out only: other devices and the shared Grinder session stay signed in.
    async function signOutLocal() {
      const { error } = await client.auth.signOut({ scope: "local" });
      if (error) throw fail(error);
      const s = memo();
      if (s) try { s.removeItem(RETURN_KEY); } catch (_) {}
      return true;
    }
    // Deletes the Strava profile and owned rows (server cascade). The Auth account remains.
    async function deleteProfile() {
      const u = await user();
      const p = await profile();
      if (!u || !p) throw fail({ code: "42501", message: "not signed in" });
      const { error } = await client.from("profiles").delete().eq("id", p.id).eq("auth_uid", u.id);
      if (error) throw fail(error);
      await signOutLocal();
      return { deleted: p.id };
    }
    function returnTo() {
      const s = memo();
      if (!s) return null;
      try { const v = s.getItem(RETURN_KEY); s.removeItem(RETURN_KEY); return v; } catch (_) { return null; }
    }
    function onChange(handler) {
      const { data } = client.auth.onAuthStateChange((event, s) => handler(event, s));
      return () => data?.subscription?.unsubscribe?.();
    }

    return { providers: PROVIDERS, session, user, signIn, profile, current, onboard, updateProfile, byHandle,
      identities, link, unlink, syncGithubHandle, signOutLocal, deleteProfile, returnTo, onChange,
      present, explain, suggest, normalizeHandle, normalizeDisplayName, normalizeAvatarUrl, validateHandle };
  }

  return { create, providers: PROVIDERS, present, explain, suggest, identitiesOf, githubHandleOf,
    normalizeHandle, normalizeDisplayName, normalizeAvatarUrl, validateHandle };
});
