"""A local card loads nothing from the network, and the CLI opens no browser unless asked.

Review of 24 Sep 2026 (REVIEW-CURSOR-PRECOMMIT section 2): the local card embedded a GitHub avatar
URL and Google Fonts, and an interactive terminal opened it by default. Opening a card that was
"only on this computer" then told GitHub and Google the viewer's IP, the time and the GitHub handle.
These tests render every local HTML writer with a signed-in identity, so the avatar branches run,
and fail on any http(s) resource URL. A plain <a href> is a click target, not a request, and is
allowed.
"""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agentgrinder import cli, feedcard  # noqa: E402

SESSION = str(ROOT / "samples" / "sample_session.jsonl")
RUN_JSON = str(ROOT / "samples" / "sample_run.json")

REMOTE = [
    re.compile(r"<(?:img|link|script|iframe|source|video|audio|embed|object|input|track)\b[^>]*"
               r"\s(?:src|href|srcset|data|poster)\s*=\s*[\"']?\s*(?:https?:)?//", re.I),
    re.compile(r"url\(\s*[\"']?\s*(?:https?:)?//", re.I),
    re.compile(r"@import\b", re.I),
    re.compile(r"<meta\b[^>]*http-equiv\s*=\s*[\"']?refresh", re.I),
]


def remote_resources(html: str) -> list:
    return [m.group(0)[:120] for rx in REMOTE for m in rx.finditer(html)]


@pytest.fixture
def no_window(monkeypatch):
    opened = []
    monkeypatch.setattr("webbrowser.open", lambda url, *a, **k: opened.append(url) or True)
    # An interactive terminal is not consent: pretend both ends are a tty.
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True, raising=False)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True, raising=False)
    monkeypatch.setenv("AGENTGRINDER_GITHUB_HANDLE", "octocat")
    return opened


CASES = [
    ("grind", ["grind", SESSION, "--athlete", "@octocat", "--no-series", "-o", "{out}"]),
    ("card", ["card", RUN_JSON, "-o", "{out}"]),
    ("share", ["share", RUN_JSON, "--handle", "octocat", "-o", "{out}"]),
    ("heist", ["heist", "@octocat", "--thief", "friend", "-o", "{out}"]),
]


@pytest.mark.parametrize("name,argv", CASES, ids=[c[0] for c in CASES])
def test_local_card_has_no_remote_resources_and_opens_nothing(name, argv, tmp_path, monkeypatch, no_window):
    monkeypatch.chdir(tmp_path)
    out = tmp_path / f"{name}.html"
    rc = cli.main([a.format(out=out) for a in argv])
    assert rc == 0
    html = out.read_text(encoding="utf-8")
    assert html.strip(), name
    assert remote_resources(html) == [], name
    assert no_window == [], f"{name} opened a browser without --open"


def test_rig_card_has_no_remote_resources():
    # `agentgrinder rig` detects the whole local rig first, which is slow on a busy machine, so the
    # renderer is called directly with a rig that carries names.
    from agentgrinder.rigcard import render_rig_card
    html = render_rig_card(handle="octocat", harnesses=["Claude Code"], share_names=True,
                           rig={"mcps": 2, "skills": 3, "mcp_names": ["github", "linear"]})
    assert remote_resources(html) == []


def test_feed_card_page_draws_the_initial_for_a_signed_in_builder():
    row = {"title": "t", "tool_calls": 3,
           "profiles": {"handle": "octocat", "github_handle": "octocat", "display_name": "@octocat",
                        "avatar_url": "https://github.com/octocat.png?size=96"}}
    html = feedcard.page(row, title="t")
    assert remote_resources(html) == []
    assert "<img" not in html
    assert "github.com/octocat.png" not in html
    assert "fonts.googleapis.com" not in html and "fonts.gstatic.com" not in html
    assert "default-src 'none'" in html      # the browser refuses a remote load even if one slips in


def test_the_detector_can_go_red():
    assert remote_resources('<img src="https://github.com/x.png">')
    assert remote_resources('<link href="https://fonts.googleapis.com/css2" rel="stylesheet">')
    assert remote_resources("<style>body{background:url('//evil.test/a.png')}</style>")
    assert remote_resources("<style>@import 'x.css';</style>")
    assert remote_resources(feedcard.card({"title": "t", "profiles": {"github_handle": "x"}}, avatars=True))
    assert not remote_resources('<a href="https://github.com/o/r/pull/9">PR</a>')
    assert not remote_resources('<img src="data:image/png;base64,AAAA">')


def test_open_is_the_only_way_to_a_window(tmp_path, monkeypatch, no_window):
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "card.html"
    assert cli.main(["card", RUN_JSON, "-o", str(out), "--open"]) == 0
    assert no_window == [out.resolve().as_uri()]


def test_login_does_not_claim_a_window_it_did_not_open(capsys, no_window):
    assert cli.main(["login", "--url", "https://example.test"]) == 0
    printed = capsys.readouterr().out
    assert no_window == []
    assert "opened" not in printed
    assert "https://example.test/?onboard" in printed
