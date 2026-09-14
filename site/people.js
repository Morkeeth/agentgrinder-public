/* Friends / people lane. Presentation only — never invents ownership from a typed handle. */
window.GrinderPeople = function ({
  client: db,
  me,
  app,
  frame,
  status,
  social,
  renderRuns,
  drawAvatar,
}) {
  const esc = (x) =>
    String(x ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const byId = (id) => document.getElementById(id);
  const draw =
    drawAvatar ||
    (typeof window.avatar === "function" && window.avatar) ||
    (typeof globalThis.avatar === "function" && globalThis.avatar) ||
    null;

  /** Stable presentation over current github_handle/name and future handle/display_name/avatar_url. */
  function present(profile) {
    if (!profile || typeof profile !== "object") {
      return {
        id: null,
        handle: null,
        display_name: null,
        avatar_url: null,
        label: "A builder",
        href: null,
      };
    }
    const handle =
      (typeof profile.handle === "string" && profile.handle.trim()) ||
      (typeof profile.github_handle === "string" && profile.github_handle.trim()) ||
      null;
    const display_name =
      (typeof profile.display_name === "string" && profile.display_name.trim()) ||
      (typeof profile.name === "string" && profile.name.trim()) ||
      null;
    const avatar_url =
      typeof profile.avatar_url === "string" && /^https?:\/\//i.test(profile.avatar_url)
        ? profile.avatar_url
        : null;
    return {
      id: profile.id || null,
      handle,
      display_name,
      avatar_url,
      label: display_name || (handle ? "@" + handle : "A builder"),
      href: handle ? "/?u=" + encodeURIComponent(handle) : null,
    };
  }

  function profileLink(profile) {
    const p = present(profile);
    if (!p.href) return esc(p.label);
    return `<a href="${p.href}">${esc(p.label)}</a>`;
  }

  function shareUrl(profile) {
    const p = present(profile);
    if (!p.href || typeof location === "undefined") return null;
    return location.origin + p.href;
  }

  async function result(query) {
    const r = await query;
    if (r.error) throw new Error(r.error.message);
    return r.data;
  }

  function fail(error) {
    status(
      typeof GrinderContract !== "undefined" && GrinderContract.message
        ? GrinderContract.message(error)
        : String(error?.message || error),
      true,
    );
  }

  function emptyCard(title, body, actionsHtml) {
    return `<article class="card people-empty"><h3>${esc(title)}</h3><p>${esc(body)}</p>${actionsHtml || ""}</article>`;
  }

  function personCard(row, opts) {
    const p = present(row);
    const meta = [];
    if (opts?.public_runs != null) {
      meta.push(
        opts.public_runs
          ? opts.public_runs +
              (opts.public_runs === 1 ? " public run" : " public runs")
          : "No public runs yet",
      );
    }
    if (opts?.following) meta.push("Following");
    const tile = draw && p.handle
      ? draw(p.handle, { size: 36 })
      : p.avatar_url
        ? `<img class="people-avatar" src="${esc(p.avatar_url)}" alt="" width="36" height="36">`
        : `<span class="people-avatar people-avatar-fallback" aria-hidden="true"></span>`;
    const followSlot = opts?.followSlot
      ? `<div class="people-follow" data-profile-id="${esc(p.id || "")}"></div>`
      : "";
    return `<article class="card people-card" data-profile-id="${esc(p.id || "")}">
      <div class="people-card-main">
        ${tile}
        <div class="people-card-copy">
          <h3>${p.href ? `<a href="${p.href}">${esc(p.display_name || p.handle || "Builder")}</a>` : esc(p.label)}</h3>
          <p class="people-handle">${p.handle ? "@" + esc(p.handle) : "Handle not set"}</p>
          ${meta.length ? `<p class="meta">${esc(meta.join(" · "))}</p>` : ""}
        </div>
      </div>
      ${followSlot}
      ${p.href ? `<div class="people-card-actions"><a class="act" href="${p.href}">Open profile</a></div>` : ""}
    </article>`;
  }

  function peopleTabs(active) {
    if (typeof feedTabs === "function") {
      return feedTabs(active);
    }
    return `<nav class="feed-tabs people-tabs" aria-label="Feed filters">
      <a href="/?people" class="${active === "people" ? "on" : ""}" ${active === "people" ? 'aria-current="page"' : ""}>Find people</a>
      <a href="/?explore" class="${active === "discover" ? "on" : ""}">Discover runs</a>
      <a href="/?following" class="${active === "following" ? "on" : ""}">Following</a>
    </nav>`;
  }

  async function wireFollowSlots(root) {
    if (!social?.followControl || !me?.()) return;
    const slots = root.querySelectorAll(".people-follow[data-profile-id]");
    for (const slot of slots) {
      const id = slot.getAttribute("data-profile-id");
      if (!id) continue;
      try {
        const rows = await result(
          db.from("profiles").select("*").eq("id", id).limit(1),
        );
        const person = Array.isArray(rows) ? rows[0] : rows;
        if (person) await social.followControl(person, slot);
      } catch (e) {
        slot.textContent = "Follow unavailable";
      }
    }
  }

  async function discover(initialQuery) {
    frame(null, null);
    if (typeof setPrimarySection === "function") setPrimarySection("feed");
    const q0 =
      typeof initialQuery === "string"
        ? initialQuery
        : new URLSearchParams(location.search).get("q") || "";
    app().innerHTML =
      peopleTabs("people") +
      `<div class="head"><h2>Find people</h2></div>
      <p class="people-lead">Look up a builder by handle or name. You can follow them before they post a run.</p>
      <form id="people-search" class="people-search" role="search">
        <label for="people-query">Handle or name</label>
        <div class="people-search-row">
          <input id="people-query" name="q" type="search" maxlength="80" autocomplete="off" spellcheck="false" placeholder="e.g. casey or Ada" value="${esc(q0)}">
          <button type="submit">Search</button>
        </div>
      </form>
      <div id="people-body" class="people-body" aria-live="polite">Loading…</div>`;
    const form = byId("people-search");
    const input = byId("people-query");
    const body = byId("people-body");
    form.onsubmit = (e) => {
      e.preventDefault();
      const q = input.value.trim();
      const next = q ? "/?people&q=" + encodeURIComponent(q) : "/?people";
      history.replaceState(null, "", next);
      load(q).catch(fail);
    };
    input.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        input.value = "";
        history.replaceState(null, "", "/?people");
        load("").catch(fail);
      }
    });
    await load(q0.trim());
  }

  async function load(query) {
    const body = byId("people-body");
    if (!body) return;
    body.innerHTML = "<p>Loading…</p>";
    try {
      if (query) {
        const rows = await result(
          db.rpc("grinder_find_people", { q: query, lim: 20 }),
        );
        const list = Array.isArray(rows) ? rows : [];
        if (!list.length) {
          body.innerHTML = emptyCard(
            "No matching builder",
            "Handles are only matched against signed-up profiles. Typing a name does not create or claim an account.",
            `<div class="cta"><a class="act" href="/?explore">Browse public runs</a><a class="act ghost" href="/?people">Clear search</a></div>`,
          );
          return;
        }
        body.innerHTML =
          `<div class="head"><h2>Matches</h2><span class="meta">${list.length}</span></div>` +
          list.map((row) => personCard(row, { followSlot: true })).join("");
        await wireFollowSlots(body);
        return;
      }

      const self = me?.();
      const following = self
        ? await result(
            db
              .from("grinder_follows")
              .select(
                "followed_id,followed:profiles!grinder_follows_followed_id_fkey(id,github_handle,name)",
              )
              .eq("follower_id", self.id)
              .order("created_at", { ascending: false })
              .limit(24),
          ).catch(() =>
            result(
              db
                .from("grinder_follows")
                .select("followed_id")
                .eq("follower_id", self.id)
                .limit(24),
            ).then(async (ids) => {
              if (!ids.length) return [];
              const profiles = await result(
                db
                  .from("profiles")
                  .select("*")
                  .in(
                    "id",
                    ids.map((f) => f.followed_id),
                  ),
              );
              return profiles.map((p) => ({ followed_id: p.id, followed: p }));
            }),
          )
        : [];

      let recent = [];
      try {
        recent = await result(db.rpc("grinder_recent_builders", { lim: 12 }));
      } catch (_) {
        recent = [];
      }
      recent = Array.isArray(recent) ? recent : [];

      const parts = [];
      if (self) {
        const p = present(self);
        parts.push(
          `<section class="people-section"><div class="head"><h2>Your shareable profile</h2></div>
          <article class="card people-share">
            <p>Friends open this link even before you post.</p>
            <p class="people-share-url"><a href="${p.href || "/"}">${esc(shareUrl(self) || location.origin + "/?u=")}</a></p>
            <div class="cta">
              <button type="button" id="people-copy-link" class="act blue">Copy profile link</button>
              <a class="act" href="${p.href || "/"}">Open your profile</a>
            </div>
          </article></section>`,
        );
      } else {
        parts.push(
          emptyCard(
            "Sign in to follow builders",
            "You can still search public profiles. Sign in to follow someone and fill your Following feed.",
            `<div class="cta"><button type="button" id="people-signin" class="act blue">Sign in</button><a class="act" href="/?explore">Browse public runs</a></div>`,
          ),
        );
      }

      const followed = (following || [])
        .map((f) => f.followed || f)
        .filter((p) => p && p.id);
      if (self && !followed.length) {
        parts.push(
          emptyCard(
            "You are not following anyone yet",
            "Search a friend’s handle above, or open a profile from a public run and tap Follow. Following works before they post.",
            `<div class="cta"><a class="act" href="/?following">Open Following</a><a class="act" href="/?explore">Discover runs</a></div>`,
          ),
        );
      } else if (followed.length) {
        parts.push(
          `<section class="people-section"><div class="head"><h2>People you follow</h2><span class="meta">${followed.length}</span></div>` +
            followed
              .map((p) => personCard(p, { following: true, followSlot: true }))
              .join("") +
            `</section>`,
        );
      }

      if (recent.length) {
        parts.push(
          `<section class="people-section"><div class="head"><h2>Builders with public runs</h2><span class="meta">${recent.length}</span></div>` +
            recent
              .map((p) =>
                personCard(p, {
                  public_runs: Number(p.public_runs) || 0,
                  followSlot: !!self,
                }),
              )
              .join("") +
            `</section>`,
        );
      } else {
        parts.push(
          emptyCard(
            "Discover is quiet",
            "No public runs yet. Share your profile link so a friend can follow you, then post when you have a real session.",
            `<div class="cta"><a class="act blue" href="/?post">Post a run</a><a class="act" href="/?explore">Check the run feed</a></div>`,
          ),
        );
      }

      body.innerHTML = parts.join("");
      const copy = byId("people-copy-link");
      if (copy && self) {
        copy.onclick = async () => {
          const url = shareUrl(self);
          try {
            await navigator.clipboard.writeText(url);
            status("Profile link copied.");
          } catch (_) {
            status(url || "Could not copy.", !url);
          }
        };
      }
      const signin = byId("people-signin");
      if (signin) {
        signin.onclick = () => {
          try {
            sessionStorage.setItem("ag_social_return", "?people");
          } catch (_) {}
          byId("auth")?.click();
        };
      }
      await wireFollowSlots(body);
    } catch (e) {
      body.innerHTML = emptyCard(
        "People could not load",
        "Your follows were not changed. Try again in a moment.",
        `<div class="cta"><button type="button" id="people-retry" class="act">Try again</button></div>`,
      );
      byId("people-retry")?.addEventListener("click", () => load(query).catch(fail));
      fail(e);
    }
  }

  /**
   * Shareable profile surface for root integration. Resolves by stored handle only —
   * never creates a profile from the URL.
   */
  async function profile(handleOrId) {
    frame(null, null);
    if (typeof setPrimarySection === "function") setPrimarySection("feed");
    app().innerHTML = '<div class="card"><p>Loading profile…</p></div>';
    const key = String(handleOrId || "").trim();
    if (!key) {
      app().innerHTML = emptyCard(
        "Profile not found",
        "This link has no handle.",
        `<div class="cta"><a class="act" href="/?people">Find people</a></div>`,
      );
      return null;
    }
    try {
      let person = null;
      const uuid = /^[0-9a-f-]{36}$/i.test(key);
      if (uuid) {
        const rows = await result(
          db.from("profiles").select("*").eq("id", key).limit(1),
        );
        person = Array.isArray(rows) ? rows[0] : rows;
      } else {
        // Prefer future handle column when Claude lands identity migration; fall back.
        let rows = await result(
          db.from("profiles").select("*").eq("github_handle", key).limit(1),
        );
        person = Array.isArray(rows) ? rows[0] : rows;
        if (!person) {
          try {
            rows = await result(
              db.from("profiles").select("*").eq("handle", key).limit(1),
            );
            person = Array.isArray(rows) ? rows[0] : rows;
          } catch (_) {
            person = null;
          }
        }
      }
      if (!person) {
        app().innerHTML = emptyCard(
          "No such builder",
          "This handle is not a signed-up profile. Searching or opening a URL does not create an account.",
          `<div class="cta"><a class="act" href="/?people">Find people</a><a class="act" href="/?explore">Browse runs</a></div>`,
        );
        return null;
      }
      const p = present(person);
      const mine = me?.() && me().id === person.id;
      const { data: runs, error } = await db
        .from("runs")
        .select("*, profiles!runs_profile_id_fkey(github_handle,name,rig)")
        .eq("profile_id", person.id)
        [mine ? "in" : "eq"](
          "visibility",
          mine ? ["public", "link", "private", "anonymous"] : "public",
        )
        .order("created_at", { ascending: false })
        .limit(50);
      if (error) throw error;
      const R = runs || [];
      const avatarHtml = (() => {
        if (draw && p.handle) return draw(p.handle, { size: 40 });
        if (p.avatar_url)
          return `<img class="people-avatar" src="${esc(p.avatar_url)}" alt="" width="40" height="40">`;
        return "";
      })();
      app().innerHTML = `${peopleTabs("people")}
        <div class="phero people-hero">
          ${avatarHtml}
          <div>
            <h1>${esc(p.display_name || p.handle || "Builder")}</h1>
            <div class="h">${p.handle ? "@" + esc(p.handle) : "Handle not set"}</div>
          </div>
        </div>
        <div id="social-follow" class="social-follow"></div>
        <div class="cta people-profile-cta">
          <button type="button" id="people-share" class="act">Copy profile link</button>
          <a class="act" href="/?people">Find people</a>
          ${mine ? "" : `<a class="act" href="/?following">Following</a>`}
        </div>
        <div class="head"><h2>${mine ? "Your runs" : "Public runs"}</h2><span class="meta">${R.length || "none yet"}</span></div>
        <div id="people-runs">${R.length ? "Loading runs…" : ""}</div>`;
      if (!R.length) {
        byId("people-runs").innerHTML = emptyCard(
          mine ? "No runs yet" : "No public runs yet",
          mine
            ? "Share your profile so friends can follow you now. Post when you have a real session."
            : "You can still follow this builder. Their public runs will appear here and in Following when they post.",
          mine
            ? `<div class="cta"><a class="act blue" href="/?post">Post a run</a></div>`
            : `<div class="cta"><a class="act" href="/?following">Open Following</a></div>`,
        );
      } else if (typeof renderRuns === "function") {
        byId("people-runs").innerHTML = await renderRuns(R);
      } else {
        byId("people-runs").innerHTML = R.map((r) => {
          const title = esc(r.title || "Run");
          return `<article class="card"><h3><a href="/?run=${encodeURIComponent(r.id)}">${title}</a></h3><p class="meta"><a href="/?run=${encodeURIComponent(r.id)}#grind-thread">Respond</a></p></article>`;
        }).join("");
      }
      if (social?.followControl) {
        await social.followControl(person, byId("social-follow"));
      }
      byId("people-share").onclick = async () => {
        const url = shareUrl(person);
        try {
          await navigator.clipboard.writeText(url);
          status("Profile link copied.");
        } catch (_) {
          status(url || "Could not copy.", !url);
        }
      };
      return person;
    } catch (e) {
      app().innerHTML = emptyCard(
        "Profile could not load",
        "Try again, or find people by handle.",
        `<div class="cta"><a class="act" href="/?people">Find people</a></div>`,
      );
      fail(e);
      return null;
    }
  }

  return {
    present,
    profileLink,
    shareUrl,
    discover,
    profile,
    personCard,
  };
};

window.GrinderPeople.present = function (profile) {
  return window.GrinderPeople({
    client: null,
    me: () => null,
    app: () => null,
    frame: () => {},
    status: () => {},
  }).present(profile);
};
