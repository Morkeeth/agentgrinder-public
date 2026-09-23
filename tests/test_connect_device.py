"""STRIVE Connect: the pairing contract, the reversible migration, and what an upload carries.

The behaviour of the pairing itself is proved against real SQL in scripts/test-connect-device.mjs
(`node --test`), because RFC 8628 lives in the database. What belongs here is the promise the
Python capture path makes: a transcript full of secrets becomes counts and allowlisted fields, so
there is nothing for a device credential to leak in the first place.
"""
import json
import re
import subprocess
from pathlib import Path

from agentgrinder.agent_api import RUN_FIELDS, run_payload
from agentgrinder.capture import read_run

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase/strava/011_connect_device.sql").read_text()
DOWN = (ROOT / "supabase/strava/down/011_connect_device.sql").read_text()
SERVER = (ROOT / "server/connect-device.mjs").read_text()
DEVICE_ROUTE = (ROOT / "api/connect/device.js").read_text()
TOKEN_ROUTE = (ROOT / "api/connect/token.js").read_text()
TRANSCRIPT = ROOT / "tests/fixtures/connect_canary_session.jsonl"
CANARY = "CANARY-NEVER-UPLOAD-8f21c7"
FAKE_HOME = "/Users/canary-person"
POLL_STATES = ("authorization_pending", "slow_down", "access_denied", "expired_token")


def test_the_device_authorization_response_follows_rfc_8628():
    assert "window_seconds constant integer := 900" in MIGRATION
    assert "poll_interval constant integer := 5" in MIGRATION
    # RFC 8628 section 6.1: twenty characters, no vowels and no digits, eight of them.
    assert "'BCDFGHJKLMNPQRSTVWXZ'" in MIGRATION
    assert "while length(code) < 8 loop" in MIGRATION
    assert "AEIOU" not in MIGRATION
    for state in POLL_STATES + ("invalid_grant",):
        assert state in MIGRATION, state
        assert state in SERVER, state
    assert "urn:ietf:params:oauth:grant-type:device_code" in SERVER
    assert "verification_uri_complete" in SERVER


def test_every_poll_state_carries_a_sentence_a_person_can_act_on():
    for state in POLL_STATES + ("invalid_grant",):
        described = re.search(rf"{state}: \"([^\"]+)\"", SERVER)
        assert described, state
        assert described.group(1).endswith("."), state


def test_the_funnel_records_steps_and_has_nowhere_to_put_content():
    block = MIGRATION[MIGRATION.index("create table if not exists strava.connect_funnel_events") :]
    block = block[: block.index(");")]
    columns = [name for name in re.findall(r"^\s{2}(\w+)", block, re.M) if name != "unique"]
    assert columns == ["id", "pairing_id", "event", "created_at"]
    for step in ("connect_started", "code_issued", "code_approved", "token_claimed", "first_run_received"):
        assert step in block, step
    # A pairing that never reaches Approve still records one terminal step, so an abandoned
    # pairing is three rows and is never confused with one that is still waiting.
    assert "code_denied" in block and "code_expired" in block
    assert "unique (pairing_id, event)" in block


def test_a_device_token_slides_ninety_days_instead_of_expiring_at_thirty():
    assert "interval '30 days'" not in MIGRATION
    assert "now() + interval '90 days'" in MIGRATION
    assert "greatest(expires_at, now() + interval '90 days')" in MIGRATION
    assert "last_seen_at" in MIGRATION
    assert "after insert on strava.grinder_agent_requests" in MIGRATION
    # Only a Connect device slides. An Advanced Agents grant keeps the expiry its owner chose.
    assert "case when label is not null" in MIGRATION
    # And the reverse restores the fixed thirty days exactly.
    assert "now()+interval '30 days'" in DOWN


def test_the_migration_is_reversible_object_for_object():
    restored = ("agent_token_create", "agent_token_list")
    created = re.findall(r"create table if not exists strava\.(\w+)", MIGRATION)
    assert set(created) == {"connect_pairings", "connect_funnel_events"}
    for table in created:
        assert f"drop table if exists strava.{table};" in DOWN, table
    for function in re.findall(r"create or replace function strava\.(\w+)\(", MIGRATION):
        if function in restored:
            assert f"create or replace function strava.{function}(" in DOWN, function
        else:
            assert f"drop function if exists strava.{function}(" in DOWN, function
    assert "drop trigger if exists connect_token_touch" in DOWN
    assert "drop column if exists last_seen_at" in DOWN
    # Both directions are one transaction, so a failed apply or revert leaves nothing behind.
    for script in (MIGRATION, DOWN):
        assert "\nbegin;\n" in script and script.rstrip().endswith("commit;")
        assert script.index("\nbegin;\n") < script.index("\ncreate ") if "\ncreate " in script else True


def test_the_bootstrap_ships_011_and_never_a_down_migration():
    built = subprocess.check_output(["python3", str(ROOT / "scripts/prepare-strava-database.py")], text=True)
    assert "-- strava/011_connect_device.sql" in built
    assert "create table if not exists strava.connect_pairings" in built
    assert "strava.connect_device_poll" in built
    assert "drop table if exists strava.connect_pairings" not in built
    assert built.count("create trigger connect_token_touch") == 1


def test_the_pairing_endpoints_forward_and_hold_no_extra_power():
    for route, handler in ((DEVICE_ROUTE, "deviceStart"), (TOKEN_ROUTE, "devicePoll")):
        assert f"server/connect-device.mjs" in route
        assert handler in route
        assert "runtimeConfig()" in route
        assert "Cache-Control','no-store'" in route
        assert "SERVICE_ROLE" not in route and "service_role" not in route
    assert "apikey: SB_KEY" in SERVER
    assert "'Content-Profile': 'strava'".replace("'", '"') in SERVER or '"Content-Profile": "strava"' in SERVER
    assert "service_role" not in SERVER


def test_a_transcript_full_of_secrets_uploads_counts_and_allowlisted_fields_only():
    source = TRANSCRIPT.read_text()
    assert CANARY in source and FAKE_HOME in source, "the fixture must carry both"
    payload = run_payload(read_run("codex", str(TRANSCRIPT)))
    uploaded = json.dumps(payload)
    assert CANARY not in uploaded
    assert FAKE_HOME not in uploaded and "/Users/" not in uploaded and "/home/" not in uploaded
    assert set(payload) <= RUN_FIELDS
    # The measurements still travel; this is not a test that passes by uploading nothing.
    assert payload["tool_calls"] == 3
    assert payload["turns_typed"] == 1
    assert payload["duration_s"] == 30
    assert payload["visibility"] == "private"
    # The title is the work, not a path, and the typed prompt is not a caption.
    assert "title" not in payload and "note" not in payload


def test_a_device_name_is_a_name_so_a_home_path_cannot_reach_the_approve_page():
    assert "A device name carries no file path" in MIGRATION
    assert r"clean_name ~ '[/\\]'" in MIGRATION
    assert "length(device_name) between 1 and 40" in MIGRATION
