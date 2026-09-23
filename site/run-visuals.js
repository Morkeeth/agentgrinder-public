/* THE RUN-CARD COMPONENTS IN THE BROWSER — the same four heroes agentgrinder/runviz.py draws.
 *
 * Two surfaces draw these: the local card the capture writes, and this app. They are two
 * implementations of one drawing, so they are kept identical on purpose and a test compares the
 * strings they produce (tests/test_run_visuals.py). Rounding is the trap: `format(x, '.1f')`
 * rounds half to even and `Number.toFixed(1)` rounds half away from zero, so both sides floor the
 * half in `one()` instead and a coordinate cannot drift by a tenth of a pixel between them.
 *
 * Oscar's ruling, 23 September, with the two corrections of the same day: light mode, IBM Plex
 * Sans, sentence case, every mark tied to real captured data — the components are drawn in the
 * app's own STRIVE blue, with Strava orange spent on three small accents (the biggest-change
 * tile's outline, the elevation peak, the trophy marks), and NO HELPER COPY on the card. The
 * source sentence, the ramp's thresholds and what a station's number counts are provenance, and
 * provenance lives under Explore this run (`provenanceHtml`), not under the picture.
 *
 * NO FILE NAME IS DRAWN AND NONE IS CARRIED. The per-file rows are anonymous triples of
 * [folder, lines at the end, lines changed]; only folder names, counts and totals are words on
 * the card. A treemap tile carries no text at all, which is both the privacy rule and the only
 * way the map is readable at 390px.
 */
(function (root) {
  "use strict";
  const HEROES = ["size-map", "folder-line", "elevation", "screenshot", "ridge"];
  const DEFAULT_HERO = "size-map";
  const LABELS = {
    "size-map": "Size map",
    "folder-line": "Folder line",
    elevation: "Elevation",
    screenshot: "Screenshot",
    ridge: "Activity ridge",
  };
  const WHY = {
    "size-map": "Every file at the end of the run, sized by its line count.",
    "folder-line": "The folders the run visited, in order, with returns.",
    elevation: "Lines changed against the clock.",
    screenshot: "Your own image, added by you.",
    ridge: "Tool calls across the run, the card's original visual.",
  };
  const MAP_W = 390, MAP_H = 220, LINE_W = 390, LINE_H = 122, LIFT_W = 390, LIFT_H = 150;
  const MAX_STATIONS = 6, MIN_TILE = 1.2, MAX_FILES = 2000, MAX_FOLDERS = 40, MAX_MARKS = 400;
  const MIN_MARKS = 5, MIN_SPAN_S = 600;
  const RAMP = [[50, "pc-t1", "Under 50"], [200, "pc-t2", "50 to 199"],
                [null, "pc-t3", "200 or more"]];
  const UNTOUCHED = ["pc-t0", "Untouched"];
  const FOLDER_NAME = /^[A-Za-z0-9._][A-Za-z0-9._-]{0,39}$/;

  function esc(text) {
    return String(text == null ? "" : text)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#x27;");
  }
  function one(value) {
    return (Math.floor(value * 10 + 0.5) / 10).toFixed(1);
  }
  function count(value) {
    return String(Math.trunc(value)).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }
  function plural(n, word) {
    return n + " " + word + (n === 1 ? "" : "s");
  }
  function span(seconds) {
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60), rest = minutes % 60;
    return hours ? hours + "h " + String(rest).padStart(2, "0") + "m" : rest + "m";
  }

  /* ---- the contract, the same rules as agentgrinder/filework.validate_file_work -------------- */
  function whole(value, field, limit) {
    if (!Number.isSafeInteger(value) || value < 0 || value > (limit == null ? 20000000 : limit))
      throw new Error(field + " must be a non-negative whole number.");
    return value;
  }
  function validateFileWork(value) {
    if (!value || typeof value !== "object" || Array.isArray(value))
      throw new Error("file_work must be an object.");
    if (value.v !== 1) throw new Error("file_work.v must be 1.");
    if (typeof value.source !== "string" || value.source.length < 8 || value.source.length > 160)
      throw new Error("file_work.source must say how the numbers were measured.");
    if (value.range != null && !/^[0-9a-f]{7,40}\.\.[0-9a-f]{7,40}$/.test(value.range))
      throw new Error("file_work.range must be two short commit hashes, base..head.");
    const folders = value.folders;
    if (!Array.isArray(folders) || !folders.length || folders.length > MAX_FOLDERS)
      throw new Error("file_work.folders holds 1 to " + MAX_FOLDERS + " folders.");
    const names = new Set();
    for (const folder of folders) {
      if (!folder || typeof folder !== "object") throw new Error("each folder is an object.");
      if (typeof folder.name !== "string" || !FOLDER_NAME.test(folder.name))
        throw new Error("a folder name must be one short safe segment, never a path.");
      if (names.has(folder.name)) throw new Error("folder names must be unique.");
      names.add(folder.name);
      for (const field of ["files_end", "lines_end", "touched_files", "lines_changed",
                           "deleted_files", "deleted_lines", "returns"])
        whole(folder[field], "folder." + field);
      if (folder.touched_files > folder.files_end)
        throw new Error("a folder cannot change more files than it holds at the end.");
    }
    const files = value.files || [];
    if (!Array.isArray(files) || files.length > MAX_FILES)
      throw new Error("file_work.files holds at most " + MAX_FILES + " rows.");
    for (const row of files) {
      if (!Array.isArray(row) || row.length !== 3)
        throw new Error("each file row is [folder, lines_end, lines_changed].");
      whole(row[0], "file.folder", folders.length - 1);
      whole(row[1], "file.lines_end");
      whole(row[2], "file.lines_changed");
    }
    const deleted = value.deleted || {};
    for (const field of ["files", "lines"]) whole(deleted[field] || 0, "deleted." + field);
    const totals = value.totals;
    if (!totals || typeof totals !== "object") throw new Error("file_work.totals is required.");
    for (const field of ["files_end", "files_touched", "lines_end", "lines_changed"])
      whole(totals[field], "totals." + field);
    const marks = value.marks || [];
    if (!Array.isArray(marks) || marks.length > MAX_MARKS)
      throw new Error("file_work.marks holds at most " + MAX_MARKS + " points.");
    let last = -1;
    for (const mark of marks) {
      if (!Array.isArray(mark) || mark.length !== 2)
        throw new Error("each mark is [seconds from the first commit, lines changed].");
      whole(mark[0], "mark.at", 60 * 60 * 24 * 90);
      whole(mark[1], "mark.lines");
      if (mark[0] < last) throw new Error("marks must be in time order.");
      last = mark[0];
    }
    agree(value);
    return value;
  }
  /* ONE RUN, ONE TOTAL. Three views of one measurement that disagree are three claims, and a
   * reader cannot tell which is true — so a payload whose parts do not add up is refused here
   * exactly as filework._agree refuses it before the card is written. */
  function agree(work) {
    const folders = work.folders, totals = work.totals, deleted = work.deleted || {files: 0, lines: 0};
    const sum = (list, read) => list.reduce((acc, item) => acc + read(item), 0);
    if (sum(folders, (f) => f.lines_changed) !== totals.lines_changed)
      throw new Error("folder line totals must add up to totals.lines_changed.");
    if (sum(folders, (f) => f.deleted_lines) !== (deleted.lines || 0))
      throw new Error("folder deleted lines must add up to deleted.lines.");
    if (sum(folders, (f) => f.deleted_files) !== (deleted.files || 0))
      throw new Error("folder deleted files must add up to deleted.files.");
    if (sum(folders, (f) => f.touched_files) + (deleted.files || 0) !== totals.files_touched)
      throw new Error("touched files must add up to totals.files_touched.");
    const marks = sum(work.marks || [], (m) => m[1]);
    if (marks && marks !== totals.lines_changed)
      throw new Error("the elevation marks must add up to totals.lines_changed.");
    const files = work.files || [];
    if (!files.length) return;
    if (files.length !== totals.files_end)
      throw new Error("the file rows must number totals.files_end.");
    if (sum(files, (row) => row[1]) !== totals.lines_end)
      throw new Error("the file rows must add up to totals.lines_end.");
    if (sum(files, (row) => row[2]) + (deleted.lines || 0) !== totals.lines_changed)
      throw new Error("the drawn files plus the deleted files must add up to totals.lines_changed.");
    if (sum(folders, (f) => f.files_end) !== totals.files_end)
      throw new Error("folder file counts must add up to totals.files_end.");
    if (sum(folders, (f) => f.lines_end) !== totals.lines_end)
      throw new Error("folder line counts must add up to totals.lines_end.");
  }

  /* ---- what this run can draw ---------------------------------------------------------------- */
  function hasSizeMap(work) {
    return !!(work && (work.files || []).length && work.totals && work.totals.lines_end);
  }
  function hasFolderLine(work) {
    return !!(work && (work.folders || []).some((f) => f.lines_changed));
  }
  function hasElevation(work) {
    const marks = (work && work.marks) || [];
    return marks.length >= MIN_MARKS && (work.span_s || 0) >= MIN_SPAN_S;
  }
  function available(run) {
    const work = (run && run.file_work) || null;
    const out = [];
    if (hasSizeMap(work)) out.push("size-map");
    if (hasFolderLine(work)) out.push("folder-line");
    if (hasElevation(work)) out.push("elevation");
    if (run && run.image_url) out.push("screenshot");
    const ridge = run && run.ridge;
    if (Array.isArray(ridge) && ridge.length >= 40 && ridge.length <= 60) out.push("ridge");
    return out;
  }
  function chosen(run) {
    const offered = available(run);
    if (!offered.length) return "";
    const picked = run && run.hero_visual;
    if (offered.indexOf(picked) !== -1) return picked;
    return offered.indexOf(DEFAULT_HERO) !== -1 ? DEFAULT_HERO : offered[offered.length - 1];
  }

  /* ---- the size map --------------------------------------------------------------------------- */
  function sliceTiles(items, x, y, w, h, out) {
    if (!items.length) return;
    if (items.length === 1) {
      out.push([items[0][0], x, y, w, h]);
      return;
    }
    let total = 0;
    for (const item of items) total += item[1];
    if (!total) total = 1;
    let running = 0, best = null;
    for (let index = 1; index < items.length; index += 1) {
      running += items[index - 1][1];
      const gap = Math.abs(running / total - 0.5);
      if (best === null || gap < best[0]) best = [gap, index, running];
    }
    const cut = best[1], part = best[2] / total;
    if (w >= h) {
      sliceTiles(items.slice(0, cut), x, y, w * part, h, out);
      sliceTiles(items.slice(cut), x + w * part, y, w - w * part, h, out);
    } else {
      sliceTiles(items.slice(0, cut), x, y, w, h * part, out);
      sliceTiles(items.slice(cut), x, y + h * part, w, h - h * part, out);
    }
  }
  function rampClass(changed) {
    if (changed <= 0) return UNTOUCHED[0];
    for (const [edge, name] of RAMP) if (edge === null || changed < edge) return name;
    return RAMP[RAMP.length - 1][1];
  }
  /* One tile is outlined in orange: the file this run changed most. It is the only mark on the
   * map that is not the blue ramp, so it reads as "start here" without a sentence saying so. */
  function sizeMapSvg(work) {
    const files = work.files || [];
    const groups = new Map();
    files.forEach((row, index) => {
      if (!groups.has(row[0])) groups.set(row[0], []);
      groups.get(row[0]).push([index, row]);
    });
    const weight = (slot) => groups.get(slot).reduce((acc, pair) => acc + pair[1][1], 0);
    const order = Array.from(groups.keys()).sort((a, b) => weight(b) - weight(a) || a - b);
    const boxes = [];
    sliceTiles(order.map((slot) => [slot, weight(slot)]), 0, 0, MAP_W, MAP_H, boxes);
    let biggest = -1;
    files.forEach((row, index) => {
      if (row[2] > 0 && (biggest < 0 || row[2] > files[biggest][2])) biggest = index;
    });
    const parts = [];
    let peak = "", drawn = 0, tiny = 0;
    for (let [slot, x, y, w, h] of boxes) {
      if (w > 3 && h > 3) { x += 1; y += 1; w -= 2; h -= 2; }
      const rows = groups.get(slot).slice().sort((a, b) => b[1][1] - a[1][1] || a[0] - b[0]);
      const inner = [];
      sliceTiles(rows.map((pair) => [pair[0], pair[1][1]]), x, y, w, h, inner);
      for (const [index, fx, fy, fw, fh] of inner) {
        if (fw < MIN_TILE || fh < MIN_TILE) { tiny += 1; continue; }
        drawn += 1;
        parts.push('<rect class="' + rampClass(files[index][2]) + '" x="' + one(fx) +
          '" y="' + one(fy) + '" width="' + one(fw) + '" height="' + one(fh) + '"/>');
        if (index === biggest)
          peak = '<rect class="pc-peak" x="' + one(fx) + '" y="' + one(fy) + '" width="' +
            one(fw) + '" height="' + one(fh) + '"/>';
      }
    }
    const label = "Size map: " + count(work.totals.files_end) +
      " files at the end of the run, sized by line count, " +
      count(work.totals.files_touched) + " of them changed";
    const svg = '<svg class="pc-map" viewBox="0 0 ' + MAP_W + " " + MAP_H +
      '" preserveAspectRatio="none" role="img" aria-label="' + esc(label) + '">' +
      parts.join("") + peak + "</svg>";
    return [svg, drawn, tiny];
  }
  function folderRows(work, limit) {
    limit = limit || 8;
    const rows = (work.folders || []).filter((f) => f.lines_changed)
      .slice().sort((a, b) => b.lines_changed - a.lines_changed);
    const out = rows.slice(0, limit).map((folder) =>
      "<li><b>" + esc(folder.name) + "</b> " + count(folder.touched_files) + " of " +
      count(folder.files_end) + " files · " + count(folder.lines_changed) + " lines</li>");
    const rest = rows.slice(limit);
    if (rest.length)
      out.push("<li>" + plural(rest.length, "more folder") + " · " +
        count(rest.reduce((acc, f) => acc + f.lines_changed, 0)) + " lines</li>");
    return out.join("");
  }
  /* The caption: numbers with short labels, and not one word of instruction. Where the numbers
   * came from and what the ramp means are provenance, and provenance is in the detail layer. */
  function totalLine(work, options) {
    const opts = options || {};
    const totals = work.totals;
    const deleted = work.deleted || {files: 0, lines: 0};
    const gone = opts.deleted && deleted.files
      ? ' · <span class="pc-gone">also deleted ' + plural(deleted.files, "file") + ", " +
        count(deleted.lines) + " lines</span>"
      : "";
    const tail = opts.extra ? ' · <span class="pc-when">' + opts.extra + "</span>" : "";
    return '<p class="pc-total">' + count(totals.lines_changed) + " lines changed · " +
      count(totals.files_touched) + " of " + count(totals.files_end) + " files" + gone +
      tail + "</p>";
  }
  function sizeMapHtml(work) {
    if (!hasSizeMap(work)) return "";
    const [svg] = sizeMapSvg(work);
    let keys = RAMP.map(([, name, label]) => '<li><i class="' + name + '"></i>' + label + "</li>").join("");
    keys += '<li><i class="' + UNTOUCHED[0] + '"></i>' + UNTOUCHED[1] + "</li>";
    return '<figure class="pc-visual pc-size" data-visual="size-map">' + svg +
      '<figcaption class="pc-legend">' + totalLine(work, {deleted: true}) +
      '<ul class="pc-keys">' + keys + "</ul>" +
      '<ul class="pc-folders">' + folderRows(work) + "</ul>" +
      "</figcaption></figure>";
  }

  /* ---- the folder line -------------------------------------------------------------------------- */
  function clip(text, room) {
    return text.length <= room ? text : text.slice(0, Math.max(1, room - 1)) + "…";
  }
  function folderLineHtml(work) {
    if (!hasFolderLine(work)) return "";
    const every = work.folders.filter((f) => f.lines_changed);
    const stations = every.slice(0, MAX_STATIONS);
    const n = stations.length;
    const left = 26, right = LINE_W - 26;
    const step = n > 1 ? (right - left) / (n - 1) : 0;
    const axis = 44;
    const top = Math.max.apply(null, stations.map((f) => f.lines_changed)) || 1;
    let room = n > 1 ? Math.floor((right - left) / Math.max(1, n - 1) / 5.4) : 40;
    room = Math.max(7, Math.min(24, room));
    const marks = [], labels = [];
    stations.forEach((folder, index) => {
      const x = n > 1 ? left + step * index : LINE_W / 2;
      const radius = 8 + 9 * Math.sqrt(folder.lines_changed / top);
      marks.push('<circle class="pc-station" cx="' + one(x) + '" cy="' + one(axis) +
        '" r="' + one(radius) + '"/>');
      marks.push('<text class="pc-station-n" x="' + one(x) + '" y="' + one(axis + 3.6) + '">' +
        count(folder.returns) + "</text>");
      let anchor = "middle", tx = x;
      if (index === 0) { anchor = "start"; tx = 2; }
      else if (index === n - 1) { anchor = "end"; tx = LINE_W - 2; }
      labels.push('<text class="pc-label" text-anchor="' + anchor + '" x="' + one(tx) +
        '" y="76">' + esc(clip(folder.name, room)) + "</text>");
      labels.push('<text class="pc-sub" text-anchor="' + anchor + '" x="' + one(tx) +
        '" y="90">' + count(folder.lines_changed) + " lines</text>");
    });
    // One word, once: the compact key for the number inside every station.
    const svg = '<svg class="pc-line" viewBox="0 0 ' + LINE_W + " " + LINE_H +
      '" role="img" aria-label="Folder line: ' + plural(n, "folder") +
      ' in the order the run first reached them, with the number of returns in each">' +
      '<text class="pc-key" x="2" y="20">returns</text>' +
      '<line class="pc-rail pc-draw" x1="' + one(left) + '" y1="' + one(axis) + '" x2="' +
      one(right) + '" y2="' + one(axis) + '"/>' + marks.join("") + labels.join("") + "</svg>";
    return '<figure class="pc-visual pc-folders-visual" data-visual="folder-line">' + svg +
      '<figcaption class="pc-legend">' + totalLine(work) + "</figcaption></figure>";
  }

  /* ---- the elevation ---------------------------------------------------------------------------- */
  function elevationHtml(work) {
    if (!hasElevation(work)) return "";
    const marks = work.marks;
    const seconds = Math.max(1, work.span_s);
    const total = marks.reduce((acc, mark) => acc + mark[1], 0) || 1;
    const left = 38, right = LIFT_W - 8, top = 14, base = LIFT_H - 28;
    const points = [];
    let running = 0;
    for (const [at, lines] of marks) {
      running += lines;
      points.push([left + (right - left) * (at / seconds),
                   base - (base - top) * (running / total)]);
    }
    const line = points.map(([x, y]) => one(x) + "," + one(y)).join(" ");
    const last = points[points.length - 1];
    const area = one(left) + "," + one(base) + " " + line + " " + one(last[0]) + "," + one(base);
    const svg = '<svg class="pc-lift" viewBox="0 0 ' + LIFT_W + " " + LIFT_H +
      '" role="img" aria-label="Elevation: lines changed against the clock, ' + count(total) +
      " over " + span(seconds) + '">' +
      '<line class="pc-axis" x1="' + one(left) + '" y1="' + one(base) + '" x2="' + one(right) +
      '" y2="' + one(base) + '"/>' +
      '<polygon class="pc-fill" points="' + area + '"/>' +
      '<polyline class="pc-stroke pc-draw" points="' + line + '"/>' +
      '<circle class="pc-peak-mark" cx="' + one(last[0]) + '" cy="' + one(last[1]) + '" r="4.5"/>' +
      '<text class="pc-sub" x="2" y="' + one(top + 4) + '">' + count(total) + " lines</text>" +
      '<text class="pc-sub" x="' + one(left) + '" y="' + one(base + 16) + '">0m</text>' +
      '<text class="pc-sub" text-anchor="end" x="' + one(right) + '" y="' + one(base + 16) +
      '">' + span(seconds) + "</text></svg>";
    const when = plural(marks.length, "commit") + " · " + span(seconds);
    return '<figure class="pc-visual pc-elevation" data-visual="elevation">' + svg +
      '<figcaption class="pc-legend">' + totalLine(work, {extra: when}) +
      "</figcaption></figure>";
  }

  /* ---- the screenshot, and the three small components -------------------------------------------- */
  function screenshotHtml(run) {
    const url = run && run.image_url;
    if (!url) return "";
    // Four words, not a sentence: a reader must not take a picture for a measurement.
    return '<figure class="pc-visual pc-shot" data-visual="screenshot">' +
      '<img src="' + esc(url) + '" alt="Image added by the author" loading="lazy" ' +
      'decoding="async" referrerpolicy="no-referrer">' +
      '<figcaption class="pc-legend"><p class="pc-total">Added by the author</p>' +
      "</figcaption></figure>";
  }
  function gearChipHtml(run) {
    const gear = run && run.gear;
    if (!gear || typeof gear !== "object") return "";
    const bits = ["agent", "harness", "model"].filter((f) => gear[f]).map((f) => esc(gear[f]));
    for (const [field, word] of [["runs", "run"], ["commits", "commit"]])
      if (gear[field] != null) bits.push(esc(plural(gear[field], word)));
    if (gear.lines_changed != null) bits.push(count(gear.lines_changed) + " lines changed");
    if (!bits.length) return "";
    const chips = bits.map((bit) => '<span class="pc-gear-bit">' + bit + "</span>").join("");
    return '<p class="pc-gear">' + chips +
      (gear.basis ? "<small>" + esc(gear.basis) + "</small>" : "") + "</p>";
  }
  function quoteHtml(run) {
    const quote = run && run.quote;
    if (!quote || typeof quote !== "object" || !quote.text) return "";
    return '<figure class="pc-quote"><blockquote>' + esc(quote.text) + "</blockquote>" +
      "<figcaption>Chosen by the author from this run.</figcaption></figure>";
  }
  function trophiesHtml(run) {
    const badges = run && run.trophies;
    if (!Array.isArray(badges) || !badges.length) return "";
    const items = badges.filter((b) => b && typeof b === "object").map((badge) =>
      '<li class="pc-trophy" data-trophy="' + esc(badge.id) + '">' +
      '<span class="pc-mark">' + esc(badge.value) + "</span><b>" + esc(badge.label) +
      "</b><small>" + esc(badge.basis) + "</small></li>").join("");
    return items ? '<ul class="pc-trophies">' + items + "</ul>" : "";
  }
  /* THE HOME OF THE COPY THE CARD NO LONGER CARRIES. The app already has one place for "how was
   * this measured": Explore this run. So the source line, the ramp's thresholds, what a station's
   * number counts and every caveat about a file too small to draw live here — one open question
   * away from the card, and never a paragraph under a picture. */
  function provenanceHtml(run) {
    const work = (run && run.file_work) || null;
    if (!work || typeof work !== "object") return "";
    const totals = work.totals;
    const deleted = work.deleted || {files: 0, lines: 0};
    const rows = [count(totals.lines_changed) + " lines changed across " +
      count(totals.files_touched) + " of " + count(totals.files_end) + " files, " +
      esc(work.source)];
    if (work.range)
      rows.push("Range " + esc(work.range) + " · " + plural(work.commits || 0, "commit"));
    if (deleted.files)
      rows.push(plural(deleted.files, "deleted file") + ", " + count(deleted.lines) +
        " lines. A deleted file has no size at the end of the run, so it has no tile on the " +
        "size map and its lines are counted in the total instead.");
    if (hasSizeMap(work)) {
      const tiny = sizeMapSvg(work)[2];
      rows.push("Size map: one tile per file, area is its line count at the end commit, colour " +
        "is how many lines changed — under 50, 50 to 199, 200 or more. The orange outline is " +
        "the file this run changed most.");
      if (tiny)
        rows.push(plural(tiny, "file") + " too small to draw one pixel wide at this size.");
    }
    if (work.binary_end)
      rows.push(plural(work.binary_end, "binary file") + " " +
        (work.binary_end === 1 ? "has" : "have") + " no line count and " +
        (work.binary_end === 1 ? "is" : "are") + " not drawn.");
    const changed = (work.folders || []).filter((f) => f.lines_changed);
    if (changed.length) {
      rows.push("Folder line: the folders in the order the run first reached them, sized by the " +
        "lines changed there. The number inside a station is how many times the run came back " +
        "to that folder after leaving it.");
      const hidden = changed.slice(MAX_STATIONS);
      if (hidden.length)
        rows.push(plural(hidden.length, "further folder") + " changed, " +
          count(hidden.reduce((acc, f) => acc + f.lines_changed, 0)) + " lines, beyond the " +
          MAX_STATIONS + " stations drawn.");
    }
    if (hasElevation(work))
      rows.push("Elevation: one point per commit that changed lines, against the commit clock, " +
        "climbing to the same total. The orange mark is the peak.");
    return '<div class="pc-provenance"><ul>' +
      rows.map((row) => "<li>" + row + "</li>").join("") + "</ul></div>";
  }
  function heroHtml(run) {
    const pick = chosen(run);
    const work = (run && run.file_work) || null;
    if (pick === "size-map") return sizeMapHtml(work);
    if (pick === "folder-line") return folderLineHtml(work);
    if (pick === "elevation") return elevationHtml(work);
    if (pick === "screenshot") return screenshotHtml(run);
    return "";
  }
  function componentsHtml(run) {
    return quoteHtml(run) + gearChipHtml(run) + trophiesHtml(run);
  }

  /* ---- the picker, in the private preview --------------------------------------------------------
   * One hero per run, chosen by the author, and only the visuals this run measured the data for.
   * A run with one option is not a choice, so the picker says so instead of drawing a lone radio
   * button that cannot be unselected. */
  function pickerHtml(run, options) {
    const opts = options || {};
    const name = opts.name || "hero_visual";
    const offered = available(run);
    if (!offered.length)
      return '<p class="hint">This run has no visual yet. A capture with commits in its window ' +
        "draws a size map; an image you add draws a screenshot.</p>";
    const picked = chosen(run);
    const rows = offered.map((key) =>
      '<label class="visual-choice"><input type="radio" name="' + esc(name) + '" value="' +
      esc(key) + '"' + (key === picked ? " checked" : "") + "><span><b>" + esc(LABELS[key]) +
      "</b><small>" + esc(WHY[key]) + "</small></span></label>").join("");
    return '<fieldset class="visual-picker"><legend>Choose the visual for this run</legend>' +
      rows + '<p class="hint">One visual per run. Only the ones this capture measured are ' +
      "offered.</p></fieldset>";
  }

  const api = {
    HEROES, LABELS, WHY, validateFileWork, available, chosen, heroHtml, componentsHtml,
    sizeMapHtml, folderLineHtml, elevationHtml, screenshotHtml, gearChipHtml, quoteHtml,
    trophiesHtml, pickerHtml, provenanceHtml,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.GrinderVisuals = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
