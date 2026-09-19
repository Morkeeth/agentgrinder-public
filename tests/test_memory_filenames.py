"""Memory privacy checks classify files from disk, not directory labels."""

import pytest

from agentgrinder import privacy


@pytest.mark.parametrize("name", ["archive", "collection"])
def test_directory_label_is_not_a_filename_but_nested_file_is(tmp_path, monkeypatch, name):
    home = tmp_path / "home"
    memory = home / ".claude" / "projects" / "synthetic-project" / "memory"
    folder = memory / name
    folder.mkdir(parents=True)
    nested = "synthetic-private-note.md"
    (folder / nested).write_text("test fixture")
    monkeypatch.setattr(privacy, "_home", lambda: str(home))

    assert privacy._memory_basenames() == {nested}
    assert privacy.scan(f'<a href="{name}/docs">Reference</a>') == []
    assert ("memory-filename", nested) in privacy.scan(nested)
    repo = tmp_path / "public-repo"
    assert privacy.safe_label(str(repo / name / "docs.md"), str(repo)) == (
        f"{name}/docs.md", "in_repo"
    )
    assert privacy.safe_label(str(repo / nested), str(repo)) == (
        privacy.ELSEWHERE, "elsewhere"
    )


@pytest.mark.parametrize("name", ["archive", "collection"])
def test_same_label_as_a_real_memory_file_is_still_protected(tmp_path, monkeypatch, name):
    home = tmp_path / "home"
    memory = home / ".claude" / "projects" / "synthetic-project" / "memory"
    memory.mkdir(parents=True)
    (memory / name).write_text("test fixture")
    monkeypatch.setattr(privacy, "_home", lambda: str(home))

    assert privacy._memory_basenames() == {name}
    assert ("memory-filename", name) in privacy.scan(f'<a href="{name}/docs">Reference</a>')
    repo = tmp_path / "public-repo"
    assert privacy.safe_label(str(repo / name), str(repo)) == (privacy.ELSEWHERE, "elsewhere")
    assert privacy.safe_prompt(name, opt_in=True) is None
