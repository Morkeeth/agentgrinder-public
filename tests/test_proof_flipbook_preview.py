from pathlib import Path


HTML = (Path(__file__).parents[1] / "site" / "index.html").read_text()


def import_route() -> str:
    start = HTML.index("async function importRun(){")
    end = HTML.index("async function viewShareRun(", start)
    return HTML[start:end]


def test_import_builds_two_private_outputs_from_one_run():
    route = import_route()
    assert "Card · private preview" in route
    assert "Proof Flipbook · private draft" in route
    assert 'id="proof-flipbook-preview"' in route
    assert 'id="proof-flipbook-play"' in route
    assert 'id="proof-flipbook-download"' in route


def test_flipbook_has_four_editable_evidence_bound_frames():
    route = import_route()
    for label in ("What happened", "What changed", "Evidence", "What remains"):
        assert label in route
    assert "Invite one builder to reply · not done yet" in route
    assert "paintProofFlipbook" in route
    assert "shareFacts" in HTML
    assert "shareFacts" in route


def test_flipbook_stays_private_until_the_author_chooses_an_audience():
    route = import_route()
    assert "Private draft. Nothing here is posted." in route
    assert "Download story definition" in route
    assert "publish flipbook" not in route.lower()
