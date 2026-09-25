"""A run can belong to a project; a project page shows its runs (25 Sep 2026)."""
from pathlib import Path

INDEX = (Path(__file__).resolve().parents[1] / "site/index.html").read_text()


def test_preview_and_composer_take_a_repository_link():
    assert 'id="i_repo"' in INDEX and 'id="f_repo"' in INDEX
    assert "'i_repo'" in INDEX.split("const editFields=")[1].split("]")[0]
    assert "'f_repo'" in INDEX.split("const fields=['f_title'")[1].split("]")[0]
    assert "repo_url:safeRepoUrl($('i_repo')?.value)||null" in INDEX
    # The saved row: the typed field wins over the capture, and a non-link clears it.
    assert "if(repo) coach.repo_url=repo; else delete coach.repo_url;" in INDEX
    assert "repo_url:safeRepoUrl($('f_repo')?.value)" in INDEX
    # https only, or nothing: a repository link is clicked, never printed as text.
    assert "function safeRepoUrl(value)" in INDEX and "/^https:/.test(url)" in INDEX


def test_project_page_and_list_are_routed_and_public_only():
    assert "if(q.has('projects'))return viewProjects();" in INDEX
    assert "if(q.has('project'))return viewProject(q.get('project'));" in INDEX
    page = INDEX[INDEX.index("async function viewProject(name)") : INDEX.index("async function viewProjects()")]
    assert ".eq('project',name).eq('visibility','public')" in page
    assert ".eq('project',name).eq('profile_id',ME.id)" in page  # the owner sees their own too
    lst = INDEX[INDEX.index("async function viewProjects()") : INDEX.index("async function viewProfile(handle)")]
    assert ".eq('visibility','public').not('project','is',null)" in lst
    assert "['/?projects','Projects']" in INDEX


def test_cards_and_profile_link_to_the_project():
    assert "function projectLinkHtml(r)" in INDEX
    assert "opts.preview?esc(project):projectLinkHtml(r)" in INDEX
    assert "Projects: ${[...seen].map" in INDEX
