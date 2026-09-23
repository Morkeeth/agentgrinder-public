"""THE RUN-CARD COMPONENTS — one hero the author chose, and three small marks beside it.

Oscar's ruling, 23 September: light mode, the app's own IBM Plex Sans, sentence case, and "let
people use what visualisation they want, or add a screenshot". So this module does not decide
what a run looks like. It offers the visuals the run has the data for, draws the one the author
picked, and draws nothing at all for the rest.

TWO CORRECTIONS THE SAME DAY, and both are structural rather than cosmetic:

  THE COMPONENTS ARE BLUE. The app's STRIVE blue carries every drawing, and Strava orange is
  spent on exactly three marks — the outline of the single biggest-change tile, the elevation's
  peak, and the trophy marks. An accent that colours half a treemap is not an accent.

  NO HELPER COPY ON THE CARD. No "Area = ...", no "The number inside = ...", no source sentence
  under a picture. A visual is self-explanatory or it is unfinished: a compact key where one is
  strictly needed (the ramp, and the single word `returns`), numbers with short labels, and
  nothing else. Every line of provenance moved to `provenance_html`, which the card shows in the
  detail layer the app already has for raw metrics.

Four heroes, and each one is a different question about the same run:

  SIZE MAP     where the work landed in a repository you cannot see the shape of otherwise.
               Area is the file's real line count at the end of the run, colour is how much of
               it moved. NO TEXT ON A COLOURED TILE: a treemap label is unreadable at 390px and
               a file name is private, so the folder names and totals are a legend underneath.
  FOLDER LINE  the route between folders, in the order the work first reached them, with the
               number of RETURNS inside each station. Six stations at most: a seventh is a
               diagram of a diagram.
  ELEVATION    cumulative lines changed against the clock. Offered only when the capture has
               five timestamped points over ten real minutes, because four dots and a guess is
               not a profile.
  SCREENSHOT   the author's own image, on the path the card already has for one (image_url).

ONE RUN, ONE TOTAL. Every view prints the same number of lines changed, because they are all
slices of the same sum (filework._agree checks that before anything is drawn) — and the source of
that sum is one open question away, in the detail layer. The size map's tiles cannot show a file
that no longer exists, so the deleted files are counted in the caption rather than left as a
silent difference between two views.

WHAT IS NOT MEASURED IS NOT DRAWN, which here means: not offered. A run with no file work has no
size map option in the picker at all, and its hero falls back to the ridge the card already had.
"""
from __future__ import annotations

import math
from html import escape

from . import filework

HEROES = ("size-map", "folder-line", "elevation", "screenshot", "ridge")
DEFAULT_HERO = "size-map"
MAP_W, MAP_H = 390, 220
LINE_W, LINE_H = 390, 122
LIFT_W, LIFT_H = 390, 150
MAX_STATIONS = 6
MIN_TILE = 1.2
# THE COMPONENTS ARE BLUE. Oscar's correction, 23 September: the app's own STRIVE blue carries
# the drawing, and Strava orange is kept for three tiny accents and nothing else — the single
# biggest-change tile's outline, the elevation's peak marker, and the trophy marks. An accent
# that colours half a treemap is not an accent.
#
# The keyed ramp is three steps of that blue on an untouched grey, so a tile's colour is a number
# a reader can look up rather than a gradient they have to feel.
RAMP = ((50, "pc-t1", "Under 50"), (200, "pc-t2", "50 to 199"), (None, "pc-t3", "200 or more"))
UNTOUCHED = ("pc-t0", "Untouched")


def _n(value: float) -> str:
    """One decimal, rounded the same way in Python and in JavaScript.

    site/run-visuals.js draws these same components in the browser, and tests/test_run_visuals.py
    compares the two strings. `format(x, '.1f')` rounds half to even and `Number.toFixed(1)` rounds
    half away from zero, so a coordinate landing exactly on x.x5 would differ by a tenth of a pixel
    and by one failing test. Both sides floor the half instead.
    """
    return f"{math.floor(value * 10 + 0.5) / 10:.1f}"


def _c(value: int) -> str:
    return f"{int(value):,}"


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" + ("" if count == 1 else "s")


def _span(seconds: int) -> str:
    minutes = int(seconds) // 60
    hours, rest = divmod(minutes, 60)
    return f"{hours}h {rest:02d}m" if hours else f"{rest}m"


def _view(run) -> dict:
    """The fields the components read. A run is a plain dict everywhere this is called from."""
    if not isinstance(run, dict):
        return {}
    return run


def available(run) -> list:
    """The visuals this run has the data for, in picker order. Never a visual with no data."""
    view = _view(run)
    work = view.get("file_work")
    out = []
    if filework.has_size_map(work):
        out.append("size-map")
    if filework.has_folder_line(work):
        out.append("folder-line")
    if filework.has_elevation(work):
        out.append("elevation")
    if view.get("image_url"):
        out.append("screenshot")
    ridge = view.get("ridge")
    if isinstance(ridge, list) and 40 <= len(ridge) <= 60:
        out.append("ridge")
    return out


def chosen(run) -> str:
    """The author's hero if the run can still draw it, else the default: size map, else ridge.

    A choice that outlived its data is not honoured. An author who picked the elevation and then
    re-captured a run with two commits gets the default back, not an empty frame.
    """
    offered = available(run)
    if not offered:
        return ""
    picked = _view(run).get("hero_visual")
    if picked in offered:
        return picked
    return DEFAULT_HERO if DEFAULT_HERO in offered else offered[-1]


# ---------------------------------------------------------------------------------------------
# the size map
# ---------------------------------------------------------------------------------------------

def _slice_tiles(items: list, x: float, y: float, w: float, h: float, out: list) -> None:
    """Split the rectangle at the value nearest half, alternating with the longer side.

    Not a squarified treemap: the cut point is chosen by value rather than by aspect ratio. On
    real repositories (423 files here) it produces tiles a reader can still tell apart, and it is
    thirty lines rather than a hundred, which matters when the same algorithm has to exist twice
    and produce the same pixels in both languages.
    """
    if not items:
        return
    if len(items) == 1:
        out.append((items[0][0], x, y, w, h))
        return
    total = sum(value for _, value in items) or 1
    best = None
    running = 0.0
    for index in range(1, len(items)):
        running += items[index - 1][1]
        gap = abs(running / total - 0.5)
        if best is None or gap < best[0]:
            best = (gap, index, running)
    _, cut, running = best
    part = running / total
    if w >= h:
        _slice_tiles(items[:cut], x, y, w * part, h, out)
        _slice_tiles(items[cut:], x + w * part, y, w - w * part, h, out)
    else:
        _slice_tiles(items[:cut], x, y, w, h * part, out)
        _slice_tiles(items[cut:], x, y + h * part, w, h - h * part, out)


def _ramp_class(changed: int) -> str:
    if changed <= 0:
        return UNTOUCHED[0]
    for edge, name, _label in RAMP:
        if edge is None or changed < edge:
            return name
    return RAMP[-1][1]


def size_map_svg(work: dict) -> tuple:
    """(svg, tiles drawn, tiles too small to draw). No text node: the legend carries the words.

    One tile is outlined in orange: the file this run changed most. It is the only mark on the map
    that is not the blue ramp, so it reads as "start here" without a sentence saying so.
    """
    files = work.get("files") or []
    groups = {}
    for index, row in enumerate(files):
        groups.setdefault(row[0], []).append((index, row))
    order = sorted(groups, key=lambda slot: (-sum(row[1] for _, row in groups[slot]), slot))
    boxes = []
    _slice_tiles([(slot, sum(row[1] for _, row in groups[slot])) for slot in order],
                 0.0, 0.0, float(MAP_W), float(MAP_H), boxes)
    biggest = -1
    for index, row in enumerate(files):
        if row[2] > 0 and (biggest < 0 or row[2] > files[biggest][2]):
            biggest = index
    parts, peak, drawn, tiny = [], "", 0, 0
    for slot, x, y, w, h in boxes:
        if w > 3 and h > 3:                  # a one-pixel inset so a folder reads as one block
            x, y, w, h = x + 1, y + 1, w - 2, h - 2
        inner = []
        rows = sorted(groups[slot], key=lambda pair: (-pair[1][1], pair[0]))
        _slice_tiles([(index, row[1]) for index, row in rows], x, y, w, h, inner)
        for index, fx, fy, fw, fh in inner:
            if fw < MIN_TILE or fh < MIN_TILE:
                tiny += 1
                continue
            drawn += 1
            parts.append(f'<rect class="{_ramp_class(files[index][2])}" x="{_n(fx)}" '
                         f'y="{_n(fy)}" width="{_n(fw)}" height="{_n(fh)}"/>')
            if index == biggest:
                peak = (f'<rect class="pc-peak" x="{_n(fx)}" y="{_n(fy)}" width="{_n(fw)}" '
                        f'height="{_n(fh)}"/>')
    touched = work["totals"]["files_touched"]
    label = (f'Size map: {_c(work["totals"]["files_end"])} files at the end of the run, '
             f'sized by line count, {_c(touched)} of them changed')
    svg = (f'<svg class="pc-map" viewBox="0 0 {MAP_W} {MAP_H}" preserveAspectRatio="none" '
           f'role="img" aria-label="{escape(label)}">' + "".join(parts) + peak + "</svg>")
    return svg, drawn, tiny


def _folder_rows(work: dict, limit: int = 8) -> str:
    rows = [f for f in work.get("folders") or [] if f["lines_changed"]]
    rows.sort(key=lambda f: -f["lines_changed"])
    out = []
    for folder in rows[:limit]:
        out.append(f'<li><b>{escape(folder["name"])}</b> {_c(folder["touched_files"])} of '
                   f'{_c(folder["files_end"])} files · {_c(folder["lines_changed"])} lines</li>')
    rest = rows[limit:]
    if rest:
        out.append(f'<li>{_plural(len(rest), "more folder")} · '
                   f'{_c(sum(f["lines_changed"] for f in rest))} lines</li>')
    return "".join(out)


def _total_line(work: dict, *, deleted: bool = False, extra: str = "") -> str:
    """The caption: numbers with short labels, and not one word of instruction.

    Oscar's correction, 23 September: no helper copy on the card. Where the measurement came from,
    what the ramp means and what a station's number counts are all facts a reader can want — and
    all of them are provenance, so they live in the run's own detail layer (`provenance_html`)
    where the app already keeps the raw metrics. A drawing that needs a paragraph under it to be
    read is a drawing that has not been finished.
    """
    totals = work["totals"]
    gone = ""
    if deleted and work["deleted"]["files"]:
        gone = (f' · <span class="pc-gone">also deleted '
                f'{_plural(work["deleted"]["files"], "file")}, '
                f'{_c(work["deleted"]["lines"])} lines</span>')
    tail = f' · <span class="pc-when">{extra}</span>' if extra else ""
    return (f'<p class="pc-total">{_c(totals["lines_changed"])} lines changed · '
            f'{_c(totals["files_touched"])} of {_c(totals["files_end"])} files{gone}{tail}</p>')


def size_map_html(work: dict) -> str:
    if not filework.has_size_map(work):
        return ""
    svg, _drawn, _tiny = size_map_svg(work)
    keys = "".join(f'<li><i class="{name}"></i>{label}</li>'
                   for _edge, name, label in RAMP)
    keys += f'<li><i class="{UNTOUCHED[0]}"></i>{UNTOUCHED[1]}</li>'
    return (f'<figure class="pc-visual pc-size" data-visual="size-map">{svg}'
            f'<figcaption class="pc-legend">{_total_line(work, deleted=True)}'
            f'<ul class="pc-keys">{keys}</ul>'
            f'<ul class="pc-folders">{_folder_rows(work)}</ul>'
            f'</figcaption></figure>')


# ---------------------------------------------------------------------------------------------
# the folder line
# ---------------------------------------------------------------------------------------------

def _clip(text: str, room: int) -> str:
    """Fit a label to its slot. A clipped label is a lie about a folder name; this one is short."""
    if len(text) <= room:
        return text
    return text[:max(1, room - 1)] + "…"


def folder_line_html(work: dict) -> str:
    if not filework.has_folder_line(work):
        return ""
    stations = [f for f in work["folders"] if f["lines_changed"]][:MAX_STATIONS]
    count = len(stations)
    left, right = 26.0, float(LINE_W - 26)
    step = (right - left) / (count - 1) if count > 1 else 0.0
    axis = 44.0
    top = max(f["lines_changed"] for f in stations) or 1
    room = int((right - left) / max(1, count - 1) / 5.4) if count > 1 else 40
    room = max(7, min(24, room))
    marks, labels = [], []
    for index, folder in enumerate(stations):
        x = left + step * index if count > 1 else LINE_W / 2
        radius = 8.0 + 9.0 * math.sqrt(folder["lines_changed"] / top)
        marks.append(f'<circle class="pc-station" cx="{_n(x)}" cy="{_n(axis)}" '
                     f'r="{_n(radius)}"/>')
        marks.append(f'<text class="pc-station-n" x="{_n(x)}" y="{_n(axis + 3.6)}">'
                     f'{_c(folder["returns"])}</text>')
        # The first and last labels are anchored to the drawing's edge instead of to their own
        # station, which is the only way a six-station line keeps every label inside 390px.
        anchor, tx = "middle", x
        if index == 0:
            anchor, tx = "start", 2.0
        elif index == count - 1:
            anchor, tx = "end", float(LINE_W - 2)
        labels.append(f'<text class="pc-label" text-anchor="{anchor}" x="{_n(tx)}" y="76">'
                      f'{escape(_clip(folder["name"], room))}</text>')
        labels.append(f'<text class="pc-sub" text-anchor="{anchor}" x="{_n(tx)}" y="90">'
                      f'{_c(folder["lines_changed"])} lines</text>')
    # One word, once: the compact key for the number inside every station. A sentence explaining
    # it belongs in the detail layer, and four words on the drawing beat forty under it.
    svg = (f'<svg class="pc-line" viewBox="0 0 {LINE_W} {LINE_H}" role="img" '
           f'aria-label="Folder line: {_plural(count, "folder")} in the order the run first '
           f'reached them, with the number of returns in each">'
           f'<text class="pc-key" x="2" y="20">returns</text>'
           f'<line class="pc-rail pc-draw" x1="{_n(left)}" y1="{_n(axis)}" x2="{_n(right)}" '
           f'y2="{_n(axis)}"/>' + "".join(marks) + "".join(labels) + "</svg>")
    return (f'<figure class="pc-visual pc-folders-visual" data-visual="folder-line">{svg}'
            f'<figcaption class="pc-legend">{_total_line(work)}</figcaption></figure>')


# ---------------------------------------------------------------------------------------------
# the elevation
# ---------------------------------------------------------------------------------------------

def elevation_html(work: dict) -> str:
    if not filework.has_elevation(work):
        return ""
    marks = work["marks"]
    span = max(1, work["span_s"])
    total = sum(mark[1] for mark in marks) or 1
    left, right, top, base = 38.0, float(LIFT_W - 8), 14.0, float(LIFT_H - 28)
    points, running = [], 0
    for at, lines in marks:
        running += lines
        x = left + (right - left) * (at / span)
        y = base - (base - top) * (running / total)
        points.append((x, y))
    line = " ".join(f"{_n(x)},{_n(y)}" for x, y in points)
    area = f"{_n(left)},{_n(base)} {line} {_n(points[-1][0])},{_n(base)}"
    svg = (f'<svg class="pc-lift" viewBox="0 0 {LIFT_W} {LIFT_H}" role="img" '
           f'aria-label="Elevation: lines changed against the clock, '
           f'{_c(total)} over {_span(span)}">'
           f'<line class="pc-axis" x1="{_n(left)}" y1="{_n(base)}" x2="{_n(right)}" '
           f'y2="{_n(base)}"/>'
           f'<polygon class="pc-fill" points="{area}"/>'
           f'<polyline class="pc-stroke pc-draw" points="{line}"/>'
           f'<circle class="pc-peak-mark" cx="{_n(points[-1][0])}" cy="{_n(points[-1][1])}" '
           f'r="4.5"/>'
           f'<text class="pc-sub" x="2" y="{_n(top + 4)}">{_c(total)} lines</text>'
           f'<text class="pc-sub" x="{_n(left)}" y="{_n(base + 16)}">0m</text>'
           f'<text class="pc-sub" text-anchor="end" x="{_n(right)}" y="{_n(base + 16)}">'
           f'{_span(span)}</text></svg>')
    when = _plural(len(marks), "commit") + " · " + _span(span)
    return (f'<figure class="pc-visual pc-elevation" data-visual="elevation">{svg}'
            f'<figcaption class="pc-legend">{_total_line(work, extra=when)}'
            f'</figcaption></figure>')


# ---------------------------------------------------------------------------------------------
# the screenshot, and the three small components
# ---------------------------------------------------------------------------------------------

def screenshot_html(run) -> str:
    """The author's own image. Declared, never measured, and the card says so under it."""
    url = _view(run).get("image_url")
    if not url:
        return ""
    # Four words, not a sentence: a reader must not take a picture for a measurement, and that
    # is a label on the image rather than a paragraph under it.
    return (f'<figure class="pc-visual pc-shot" data-visual="screenshot">'
            f'<img src="{escape(url)}" alt="Image added by the author" loading="lazy" '
            f'decoding="async" referrerpolicy="no-referrer">'
            f'<figcaption class="pc-legend"><p class="pc-total">Added by the author</p>'
            f'</figcaption></figure>')


def gear_chip_html(run) -> str:
    """Agent, harness, model and the lifetime totals — from captured runs, and it says so."""
    gear = _view(run).get("gear")
    if not isinstance(gear, dict) or not gear:
        return ""
    bits = [escape(str(gear[field])) for field in ("agent", "harness", "model") if gear.get(field)]
    for field, word in (("runs", "run"), ("commits", "commit")):
        if gear.get(field) is not None:
            bits.append(escape(_plural(gear[field], word)))
    if gear.get("lines_changed") is not None:
        bits.append(f'{_c(gear["lines_changed"])} lines changed')
    if not bits:
        return ""
    chips = "".join(f'<span class="pc-gear-bit">{bit}</span>' for bit in bits)
    basis = (f'<small>{escape(gear["basis"])}</small>' if gear.get("basis") else "")
    return f'<p class="pc-gear">{chips}{basis}</p>'


def quote_html(run) -> str:
    """One line the author picked. Never read out of a transcript; the contract refuses that."""
    quote = _view(run).get("quote")
    if not isinstance(quote, dict) or not quote.get("text"):
        return ""
    return (f'<figure class="pc-quote"><blockquote>{escape(quote["text"])}</blockquote>'
            f'<figcaption>Chosen by the author from this run.</figcaption></figure>')


def trophies_html(run) -> str:
    """Round orange marks, one per measured badge. A badge with no measurement is not here."""
    badges = _view(run).get("trophies")
    if not isinstance(badges, list) or not badges:
        return ""
    items = "".join(
        f'<li class="pc-trophy" data-trophy="{escape(badge["id"])}">'
        f'<span class="pc-mark">{escape(badge["value"])}</span>'
        f'<b>{escape(badge["label"])}</b><small>{escape(badge["basis"])}</small></li>'
        for badge in badges if isinstance(badge, dict))
    return f'<ul class="pc-trophies">{items}</ul>' if items else ""


def hero_html(run) -> str:
    """The one visual the author chose, or nothing when the run has no data for any of them."""
    view = _view(run)
    pick = chosen(view)
    work = view.get("file_work")
    if pick == "size-map":
        return size_map_html(work)
    if pick == "folder-line":
        return folder_line_html(work)
    if pick == "elevation":
        return elevation_html(work)
    if pick == "screenshot":
        return screenshot_html(view)
    return ""                                # the ridge is drawn by the card that already had one


def provenance_html(run) -> str:
    """Where the numbers came from, and everything the drawing does not say on its face.

    THIS IS THE HOME OF THE COPY THE CARD NO LONGER CARRIES. The app already has one place for
    "how was this measured": the run's own detail layer, under Explore this run. So the source
    line, the ramp's thresholds, what a station's number counts, and every caveat about a file
    too small to draw or a binary blob with no lines to count live here — one open question away
    from the card, and never a paragraph under a picture.
    """
    view = _view(run)
    work = view.get("file_work")
    if not isinstance(work, dict):
        return ""
    totals = work["totals"]
    rows = [f'{_c(totals["lines_changed"])} lines changed across '
            f'{_c(totals["files_touched"])} of {_c(totals["files_end"])} files, '
            f'{escape(work["source"])}']
    if work.get("range"):
        rows.append(f'Range {escape(work["range"])} · {_plural(work.get("commits", 0), "commit")}')
    deleted = work["deleted"]
    if deleted["files"]:
        rows.append(f'{_plural(deleted["files"], "deleted file")}, {_c(deleted["lines"])} lines. '
                    f'A deleted file has no size at the end of the run, so it has no tile on the '
                    f'size map and its lines are counted in the total instead.')
    if filework.has_size_map(work):
        _svg, _drawn, tiny = size_map_svg(work)
        rows.append("Size map: one tile per file, area is its line count at the end commit, "
                    "colour is how many lines changed — under 50, 50 to 199, 200 or more. The "
                    "orange outline is the file this run changed most.")
        if tiny:
            rows.append(f'{_plural(tiny, "file")} too small to draw one pixel wide at this size.')
    if work.get("binary_end"):
        count = work["binary_end"]
        rows.append(f'{_plural(count, "binary file")} {"has" if count == 1 else "have"} no line '
                    f'count and {"is" if count == 1 else "are"} not drawn.')
    changed = [folder for folder in work["folders"] if folder["lines_changed"]]
    if changed:
        rows.append("Folder line: the folders in the order the run first reached them, sized by "
                    "the lines changed there. The number inside a station is how many times the "
                    "run came back to that folder after leaving it.")
        hidden = changed[MAX_STATIONS:]
        if hidden:
            rows.append(f'{_plural(len(hidden), "further folder")} changed, '
                        f'{_c(sum(folder["lines_changed"] for folder in hidden))} lines, beyond '
                        f'the {MAX_STATIONS} stations drawn.')
    if filework.has_elevation(work):
        rows.append(f'Elevation: one point per commit that changed lines, against the commit '
                    f'clock, climbing to the same total. The orange mark is the peak.')
    items = "".join(f"<li>{row}</li>" for row in rows)
    return f'<div class="pc-provenance"><ul>{items}</ul></div>'


def provenance_details_html(run) -> str:
    """The provenance, in its own disclosure, for a card that has no detail layer of its own."""
    inner = provenance_html(run)
    if not inner:
        return ""
    return (f'<details class="pc-more"><summary>Explore this run</summary>{inner}</details>')


def picked_hero_html(run) -> str:
    """The hero ONLY when the author asked for one by name.

    The grind card (solocard.py) already opens on the trace of the session itself. A default that
    put a size map above it would be two heroes on one card, which is the thing the picker exists
    to prevent — so on that surface the components are opt-in and the default changes nothing.
    """
    return hero_html(run) if _view(run).get("hero_visual") else ""


def components_html(run) -> str:
    """The quote, the gear chip and the trophies. Each one absent by default."""
    return quote_html(run) + gear_chip_html(run) + trophies_html(run)


LABELS = {"size-map": "Size map", "folder-line": "Folder line", "elevation": "Elevation",
          "screenshot": "Screenshot", "ridge": "Activity ridge"}

WHY = {
    "size-map": "Every file at the end of the run, sized by its line count.",
    "folder-line": "The folders the run visited, in order, with returns.",
    "elevation": "Lines changed against the clock.",
    "screenshot": "Your own image, added by you.",
    "ridge": "Tool calls across the run, the card's original visual.",
}

# The components' own styles. Light mode, IBM Plex Sans, the app's STRIVE blue carrying the
# drawing and Strava orange on three small accents. The same block exists in site/design.css for
# the browser; tests/test_run_visuals.py checks the two carry the same colours, so a ramp cannot
# drift between the local card and the app.
CSS = """
  .pc-visual{margin:0;padding:12px 20px;border-bottom:1px solid var(--line)}
  .pc-visual svg,.pc-shot img{display:block;width:100%;height:auto}
  .pc-shot img{max-height:360px;object-fit:cover}
  .pc-t0{fill:#EEF0F3} .pc-t1{fill:#C4D2FF} .pc-t2{fill:#6A87FF} .pc-t3{fill:#0047FF}
  .pc-keys i.pc-t0{background:#EEF0F3} .pc-keys i.pc-t1{background:#C4D2FF}
  .pc-keys i.pc-t2{background:#6A87FF} .pc-keys i.pc-t3{background:#0047FF}
  .pc-peak{fill:none;stroke:#FC4C02;stroke-width:2}
  .pc-legend{margin-top:8px;font-size:12px;color:var(--muted);line-height:1.5}
  .pc-total{margin:0 0 6px;color:var(--ink);font-size:12.5px}
  .pc-gone,.pc-when{color:var(--muted)}
  .pc-keys,.pc-folders,.pc-trophies{list-style:none;margin:0;padding:0}
  .pc-keys{display:flex;flex-wrap:wrap;gap:4px 12px;margin-bottom:6px}
  .pc-keys li{display:flex;align-items:center;gap:5px}
  .pc-keys i{width:11px;height:11px;border-radius:2px;display:inline-block}
  .pc-folders li{margin:1px 0} .pc-folders b{color:var(--ink);font-weight:600}
  .pc-rail{stroke:#0047FF;stroke-width:2;stroke-linecap:round}
  .pc-station{fill:#fff;stroke:#0047FF;stroke-width:2}
  .pc-station-n{fill:#0047FF;font:600 11px "IBM Plex Sans",system-ui,sans-serif;
    text-anchor:middle}
  .pc-label{fill:var(--ink);font:600 10px "IBM Plex Sans",system-ui,sans-serif}
  .pc-sub,.pc-key{fill:var(--muted);font:10px "IBM Plex Sans",system-ui,sans-serif}
  .pc-axis{stroke:var(--line);stroke-width:1}
  .pc-fill{fill:#0047FF;opacity:.10}
  .pc-stroke{fill:none;stroke:#0047FF;stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
  .pc-peak-mark{fill:#FC4C02}
  .pc-provenance{padding:0 20px 12px;font-size:12.5px;color:var(--muted);line-height:1.55}
  .pc-provenance ul{margin:0;padding-left:18px} .pc-provenance li{margin:3px 0}
  .pc-more{border-top:1px solid var(--line)}
  .pc-more>summary{padding:12px 20px;cursor:pointer;color:var(--muted);font-size:13px}
  .pc-gear{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:0;padding:10px 20px;
    border-bottom:1px solid var(--line);font-size:12px}
  .pc-gear-bit{border:1px solid var(--line);border-radius:999px;padding:2px 9px;color:var(--ink)}
  .pc-gear small{color:var(--muted)}
  .pc-quote{margin:0;padding:12px 20px;border-bottom:1px solid var(--line);
    border-left:3px solid #0047FF}
  .pc-quote blockquote{margin:0;font-size:16px;font-weight:600;line-height:1.4;color:var(--ink)}
  .pc-quote figcaption{margin-top:4px;font-size:12px;color:var(--muted)}
  .pc-trophies{display:flex;flex-wrap:wrap;gap:14px;padding:12px 20px;
    border-bottom:1px solid var(--line)}
  .pc-trophy{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--muted)}
  .pc-trophy b{display:block;color:var(--ink);font-weight:600}
  .pc-mark{flex:0 0 auto;width:44px;height:44px;border-radius:50%;background:#FC4C02;color:#fff;
    display:grid;place-items:center;font-weight:700;font-size:11px;text-align:center}
  /* A LINE THAT DRAWS ITSELF, and only a line. Nothing moves, nothing fades in, and a reader who
     asked their system for less motion gets a finished drawing immediately. */
  .pc-draw{stroke-dasharray:900;stroke-dashoffset:900;animation:pc-draw .9s ease-out forwards}
  @keyframes pc-draw{to{stroke-dashoffset:0}}
  @media (prefers-reduced-motion:reduce){
    .pc-draw{animation:none;stroke-dashoffset:0}
  }
  @media (max-width:420px){
    .pc-visual,.pc-gear,.pc-quote,.pc-trophies{padding-left:14px;padding-right:14px}
  }
"""
