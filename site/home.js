/* THE SIGNED-OUT HOME (Oscar, 25 Sep 23:1x: "landing page first, some events, clubs, events that
   are going on, wow homey. then find some friends, most popular runs. and then boom login").
   In that order: This week, Clubs, Builders, Popular runs, then the sign-in ask.

   Every row is a real row. A section with nothing in it says so in one line; nothing is seeded,
   sampled or invented. The one device is the week strip: the last seven days of public runs as
   bars and the next seven days of events as marks, so the page shows the club's week, not a pitch.
   Events need migration 014 (supabase/strava/014_social.sql); before it, that read fails and the
   strip shows runs only. */
(function (root) {
  "use strict";
  const esc = (s) => String(s ?? "").replace(/[<>&"']/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&#39;" }[c]));
  const dayKey = (t) => { const d = new Date(t); return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate(); };
  const startOfDay = (t) => { const d = new Date(t); d.setHours(0, 0, 0, 0); return d.getTime(); };
  // Calendar days, not 24-hour steps, so a daylight-saving change never repeats or skips a date.
  const addDays = (t, n) => { const d = new Date(startOfDay(t)); d.setDate(d.getDate() + n); return d.getTime(); };

  // 14 days: the last seven including today (runs), then the next seven (events). Events later
  // today are drawn on today and counted with the next seven.
  function week(runs, events, now) {
    const today = startOfDay(now);
    const days = [];
    for (let i = -6; i <= 7; i++) days.push({ t: addDays(now, i), runs: 0, events: [] });
    const byKey = new Map(days.map((d) => [dayKey(d.t), d]));
    (runs || []).forEach((r) => { const d = byKey.get(dayKey(r.created_at)); if (d && d.t <= today) d.runs++; });
    (events || []).forEach((e) => { const d = byKey.get(dayKey(e.starts_at)); if (d && d.t >= today && Date.parse(e.starts_at) >= now) d.events.push(e); });
    return { days, today };
  }

  function weekHtml(runs, events, now) {
    const { days, today } = week(runs, events, now);
    const max = Math.max(1, ...days.map((d) => d.runs));
    const cols = days.map((d) => {
      const wd = new Date(d.t).toLocaleDateString("en-GB", { weekday: "narrow" });
      const n = new Date(d.t).getDate();
      const past = d.t < today, isToday = d.t === today;
      const bar = d.runs ? `<span class="wk-bar" style="--h:${Math.round((d.runs / max) * 100)}%" title="${d.runs} public run${d.runs === 1 ? "" : "s"}"></span>` : "";
      const mark = d.events.length ? `<a class="wk-ev" href="/?event=${esc(d.events[0].id)}" title="${esc(d.events[0].title)}"><span class="sr">${esc(d.events[0].title)}</span></a>` : "";
      return `<li class="wk-day${past ? " past" : ""}${isToday ? " today" : ""}"><span class="wk-plot">${bar}${mark}</span><span class="wk-d">${esc(wd)}</span><span class="wk-n">${n}</span></li>`;
    }).join("");
    const ran = days.reduce((a, d) => a + d.runs, 0);
    const coming = days.reduce((a, d) => a + d.events.length, 0);
    const line = `${ran ? ran + " public run" + (ran === 1 ? "" : "s") + " in the last 7 days" : "No public runs in the last 7 days"} · ${coming ? coming + " event" + (coming === 1 ? "" : "s") + " in the next 7" : "no events in the next 7"}`;
    return `<ol class="wk" aria-label="This week on __BRAND__">${cols}</ol><p class="wk-line">${esc(line)}</p>`;
  }

  function eventRow(e) {
    const d = new Date(e.starts_at);
    const club = e.club ? `<span>${esc(e.club.name)}</span>` : "";
    const going = Number.isInteger(e.going) ? `<span>${e.going} going</span>` : "";
    return `<a class="ev" href="/?event=${esc(e.id)}"><span class="ev-date"><b>${d.getDate()}</b><small>${esc(d.toLocaleDateString("en-GB", { month: "short" }))}</small></span>
      <span class="ev-body"><span class="ev-t">${esc(e.title)}</span><span class="ev-meta">${esc(d.toLocaleString("en-GB", { weekday: "short", hour: "2-digit", minute: "2-digit" }))}${e.place ? " · " + esc(e.place) : ""}</span><span class="ev-meta">${club}${club && going ? " · " : ""}${going}</span></span></a>`;
  }

  function clubRow(c) {
    return `<a class="club" href="/?crew=${esc(c.id)}"><span class="club-mark" aria-hidden="true">${esc((c.name || "?").trim().charAt(0).toUpperCase())}</span><span class="club-t">${esc(c.name)}</span><span class="club-n">${c.members} member${c.members === 1 ? "" : "s"}</span></a>`;
  }

  // Builders who posted a public run in the window, most runs first, one row each.
  function builders(runs, limit) {
    const seen = new Map();
    (runs || []).forEach((r) => {
      if (!r.profile_id || r.visibility !== "public") return;
      const b = seen.get(r.profile_id);
      if (b) b.n++; else seen.set(r.profile_id, { run: r, n: 1 });
    });
    return [...seen.values()].sort((a, b) => b.n - a.n || String(b.run.created_at).localeCompare(String(a.run.created_at))).slice(0, limit || 6);
  }

  // Most XUDOS first, then newest. A run nobody cheered still counts as recent.
  function popular(runs, counts, limit) {
    return [...(runs || [])].sort((a, b) => ((counts[b.id] || 0) - (counts[a.id] || 0)) || String(b.created_at).localeCompare(String(a.created_at))).slice(0, limit || 5);
  }

  async function read(sb, now) {
    const since = new Date(addDays(now, -30)).toISOString();
    const until = new Date(addDays(now, 8)).toISOString(); // the end of the seventh day ahead
    const runsQ = sb.from("runs").select("*, profiles!runs_profile_id_fkey(github_handle,name,rig,handle,display_name,avatar_url)")
      .eq("visibility", "public").gte("created_at", since).order("created_at", { ascending: false }).limit(100);
    const clubsQ = sb.from("grinder_crews").select("id,name,visibility,created_at,grinder_memberships(count)").eq("visibility", "public").order("created_at", { ascending: false }).limit(12);
    const eventsQ = sb.from("grinder_events").select("id,title,place,starts_at,crew_id,grinder_crews(name),grinder_event_people(count)")
      .gte("starts_at", new Date(now).toISOString()).lt("starts_at", until).order("starts_at", { ascending: true }).limit(20);
    const [runs, clubs, events] = await Promise.all([runsQ, clubsQ, eventsQ].map((q) => q.then((r) => (r.error ? null : r.data), () => null)));
    return {
      runs: runs || [],
      clubs: (clubs || []).map((c) => ({ id: c.id, name: c.name, members: c.grinder_memberships?.[0]?.count ?? 0 })).sort((a, b) => b.members - a.members),
      // null means the events table is not there yet (014 not applied), [] means none planned.
      events: events === null ? null : events.map((e) => ({ id: e.id, title: e.title, place: e.place, starts_at: e.starts_at, club: e.grinder_crews ? { name: e.grinder_crews.name } : null, going: e.grinder_event_people?.[0]?.count ?? 0 })),
      ok: runs !== null,
    };
  }

  const api = { week, weekHtml, eventRow, clubRow, builders, popular, read };
  root.GrinderHome = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
