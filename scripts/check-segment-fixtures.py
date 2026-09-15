"""Render the public segment leaderboard with labelled local fixture data."""
from pathlib import Path
import os

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)

SEGMENT = {
    "id": "segment-01",
    "name": "Add a --json flag to a small CLI",
    "description": "TEST DATA leaderboard for the bundled CLI task.",
    "task_url": "https://example.test/task",
    "repo_url": "https://example.test/repo",
}
RUNS = [
    {"id": "test-a", "title": "TEST DATA run A", "project": "TEST DATA alpha",
     "model": "TEST DATA Model A", "duration_s": 90, "tool_calls": 4,
     "rhythm": [0, 2, 1], "segment_id": "segment-01", "visibility": "public"},
    {"id": "test-b", "title": "TEST DATA run B", "project": "TEST DATA beta",
     "model": "TEST DATA Model B", "duration_s": 90, "tool_calls": 4,
     "rhythm": [0, 1, 2], "segment_id": "segment-01", "visibility": "public"},
    {"id": "test-c", "title": "TEST DATA run C", "project": "TEST DATA gamma",
     "model": "TEST DATA Model C", "duration_s": 130, "tool_calls": 3,
     "rhythm": [1, 0, 1], "segment_id": "segment-01", "visibility": "public"},
]

with sync_playwright() as playwright:
    launch = {"headless": True, "args": ["--no-sandbox"]}
    binary = os.environ.get("BRAVE_BINARY") or os.environ.get("CHROME_BIN")
    if binary:
        launch["executable_path"] = binary
    browser = playwright.chromium.launch(**launch)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(
        "<style>" + (ROOT / "site/design.css").read_text() + "</style>"
        '<div id="status"></div><main id="app" class="main"></main>'
    )
    page.add_script_tag(content=(ROOT / "site/run-contract.js").read_text())
    page.add_script_tag(content=(ROOT / "site/segments.js").read_text())
    page.evaluate(
        """([segment, runs]) => {
          const filters = [];
          const client = {from(name) {
            const source = name === "segments" ? [segment] : runs;
            const local = [];
            const query = {
              select() { return query; },
              eq(key, value) { local.push([key, value]); filters.push([name, key, value]); return query; },
              maybeSingle() {
                const data = source.filter(row => local.every(([key, value]) => row[key] === value));
                return Promise.resolve({data: data[0] || null, error: null});
              },
              then(resolve, reject) {
                const data = source.filter(row => local.every(([key, value]) => row[key] === value));
                return Promise.resolve({data, error: null}).then(resolve, reject);
              }
            };
            return query;
          }};
          window.fixtureFilters = filters;
          return GrinderSegments.mount({
            client,
            id: "segment-01",
            slot: document.getElementById("app"),
            frame: () => {},
            status: text => { document.getElementById("status").textContent = text; }
          });
        }""",
        [SEGMENT, RUNS],
    )
    page.locator(".segment-row").first.wait_for()
    assert page.locator(".segment-row").count() == 3
    assert page.get_by_text("TEST DATA", exact=False).count() >= 3
    assert page.locator(".segment-place").all_text_contents() == ["1", "1", "3"]
    assert ["runs", "visibility", "public"] in page.evaluate("fixtureFilters")
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
    assert not errors, errors
    page.screenshot(path=ARTIFACTS / "segment-390.png", full_page=True)
    page.set_viewport_size({"width": 1280, "height": 900})
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
    page.screenshot(path=ARTIFACTS / "segment-1280.png", full_page=True)
    browser.close()
