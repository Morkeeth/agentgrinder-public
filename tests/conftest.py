"""No test reads the developer's own Cursor history unless it asks to.

`agentgrinder.cursor_chats` reads `~/.cursor/chats` and `~/.cursor/projects` by default. Without
this fixture a hook test that seeds a synthetic store would also pick up every real session on the
machine running the suite, so the same test would pass on a fresh checkout and fail on the author's
Mac. Measured on this Mac on 16 Sep 2026: 308 real sessions leaked into two hook tests before this
file existed.

A test that wants the real folders sets the two variables itself.
"""
import pytest

from agentgrinder import cursor_chats


@pytest.fixture(autouse=True)
def isolated_cursor_history(tmp_path_factory, monkeypatch):
    empty = tmp_path_factory.mktemp("cursor-history-none")
    monkeypatch.setenv(cursor_chats.ENV_CHATS, str(empty / "chats"))
    monkeypatch.setenv(cursor_chats.ENV_PROJECTS, str(empty / "projects"))
