"""Bundled example journey: labelled fixture, no signup, demo ≠ live, one experiment."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site/index.html").read_text()
EXAMPLE_JS = (ROOT / "site/example.js").read_text()
EXAMPLE_JSON = json.loads((ROOT / "site/bundled-example.json").read_text())
ORDER = (ROOT / "scripts/migration-order.txt").read_text().split()


def test_bundled_example_is_labelled_fixture_and_public_safe():
    assert EXAMPLE_JSON["fixture"] is True
    assert "BUNDLED EXAMPLE" in EXAMPLE_JSON["label"]
    blob = json.dumps(EXAMPLE_JSON)
    assert "/Users/" not in blob and "/home/" not in blob and "AKIA" not in blob
    assert "[fixture]" not in blob
    assert EXAMPLE_JSON["mode_kind"] == "demo"
    assert "not autonomous" in EXAMPLE_JSON["not"].lower() or "Not autonomous" in EXAMPLE_JSON["not"]


def test_example_names_one_named_friction_and_one_experiment():
    exp = EXAMPLE_JSON["run"]["coach_experiment"]
    assert exp["kind"] == "unverified-named-claim"
    assert "test_draft_renders" in exp["title"]
    assert exp["plan"][0].startswith("Friction:")
    assert any(p.startswith("Experiment:") for p in exp["plan"])
    assert "Claims [" not in exp["instruction"]


def test_later_fixture_preserves_original_measurements_and_does_not_claim_cause():
    later = EXAMPLE_JSON["later"]
    assert later["commits"] == EXAMPLE_JSON["run"]["commits"] == 0
    assert "not proof" in later["observed"].lower()
    assert EXAMPLE_JSON["run"]["measurement_revision"] != later["measurement_revision"]


def test_second_builder_uses_their_own_baseline():
    assert EXAMPLE_JSON["reader"]["id"] != EXAMPLE_JSON["run"]["id"]
    assert EXAMPLE_JSON["reader"]["measurement_revision"] != EXAMPLE_JSON["run"]["measurement_revision"]
    assert "author's counts are not shown" in EXAMPLE_JS


def test_router_still_serves_the_example_without_signup():
    # 25 Sep 2026: index.html links a real public run instead (REAL_RUN). /?example still resolves.
    assert "/?example" not in INDEX and "const REAL_RUN=" in INDEX
    assert "q.has('example')" in INDEX
    assert 'src="/example.js"' in INDEX
    assert "GrinderExample.view" in INDEX


def test_demo_and_live_modes_are_visibly_distinguished():
    assert "function coachModeKind" in INDEX
    assert "not autonomous reasoning" in INDEX
    assert "Live model" in INDEX
    assert "coach --live-status" in EXAMPLE_JSON["live"]["command"]
    assert EXAMPLE_JSON["live"]["needs"]


def test_coach_mode_migration_is_registered_and_additive():
    assert "2026-09-13-coach-mode.sql" in ORDER
    sql = (ROOT / "supabase/migrations/2026-09-13-coach-mode.sql").read_text().lower()
    assert "add column if not exists coach_mode" in sql
    assert "drop " not in sql
