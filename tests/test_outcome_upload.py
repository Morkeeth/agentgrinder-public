"""Declared outcome receipts survive client preparation, and only in their validated shape.

The real call shape is `run_payload(json.loads(file))`, the path `agent_api publish` and the MCP tool
take. The fixture is the night-run JSON prepared for the first signed-in trial, byte for byte.
"""
import base64
import gzip
import json
import subprocess
from pathlib import Path
from urllib.parse import unquote

import pytest

from agentgrinder.agent_api import RUN_FIELDS, run_payload
from agentgrinder.push import export_run, import_url

FIXTURE = Path(__file__).parent / "fixtures" / "night_run_outcome.json"
OUTCOME = ("repo_url", "receipts", "shipped", "artifact_url", "image_url")


def night_run():
    return json.loads(FIXTURE.read_text())


def five_field_run():
    run = night_run()
    run["image_url"] = "https://example.com/strive/card.png?v=2"
    return run


def decode_import(url):
    encoded = url.split("#import=", 1)[1]
    if encoded.startswith("gz."):
        body = encoded.removeprefix("gz.")
        return json.loads(gzip.decompress(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))))
    return json.loads(base64.b64decode(unquote(encoded)))


def test_outcome_fields_are_all_declared_upload_fields():
    assert set(OUTCOME) <= RUN_FIELDS


def test_night_run_keeps_every_declared_outcome_it_carries_through_run_payload():
    run = night_run()
    payload = run_payload(run)
    carried = [field for field in OUTCOME if field in run]
    assert carried == ["repo_url", "receipts", "shipped", "artifact_url"]
    for field in carried:
        assert payload[field] == run[field], field


def test_all_five_outcome_fields_survive_export_run_run_payload_and_the_import_url():
    run = five_field_run()
    for prepared in (export_run(run), run_payload(run), decode_import(import_url(run, "https://strive.example"))):
        for field in OUTCOME:
            assert prepared[field] == run[field], field


def test_outcome_survives_the_gzip_import_encoding():
    run = five_field_run()
    run["ridge"] = [index % 6 for index in range(50)]
    run["ridge_basis"] = "wall-time"
    run["route"] = [index % 8 for index in range(3000)]
    url = import_url(run, "https://strive.example")
    assert url.split("#import=", 1)[1].startswith("gz.")
    decoded = decode_import(url)
    for field in OUTCOME:
        assert decoded[field] == run[field], field


def test_title_and_note_stay_the_uploaders_separate_choice():
    # A parser title can be the first typed prompt, so a title or note inside the run JSON never
    # travels. Only the explicit arguments do. This is the contract, not an omission.
    run = night_run()
    assert "title" in run and "note" in run
    payload = run_payload(run)
    assert "title" not in payload and "note" not in payload
    assert "title" not in export_run(run) and "note" not in export_run(run)
    chosen = run_payload(run, title="Chosen title", note="Chosen note")
    assert (chosen["title"], chosen["note"]) == ("Chosen title", "Chosen note")


def test_the_outcome_path_does_not_widen_what_leaves_the_machine():
    run = five_field_run()
    run.update({"source_path": "/Users/someone/.claude/projects/x.jsonl", "coach_verdict": "PRIVATE_TEXT",
                "cwd": "/Users/someone/work", "prompt": "PRIVATE_PROMPT", "output_url": "https://example.com/a"})
    payload = run_payload(run)
    text = json.dumps(payload)
    assert "PRIVATE" not in text and "/Users/" not in text
    assert set(payload) <= RUN_FIELDS
    assert "output_url" not in payload and "cwd" not in payload


def test_the_receipt_objects_are_copies_holding_only_label_and_url():
    run = five_field_run()
    payload = run_payload(run)
    assert payload["receipts"] is not run["receipts"]
    assert all(set(receipt) == {"label", "url"} for receipt in payload["receipts"])


def test_absent_outcome_fields_stay_absent_not_null():
    payload = run_payload({"turns_typed": 2})
    assert not set(OUTCOME) & set(payload)


LINK = "https://github.com/Morkeeth/agentgrinder-public"
RECEIPT = {"label": "PR", "url": LINK + "/pull/1"}


BAD_OUTCOMES = [
    {"repo_url": "http://github.com/a/b"},
    {"repo_url": "https://example.com/a/b"},
    {"repo_url": "javascript:alert(1)"},
    {"repo_url": 7},
    {"artifact_url": "https://example.com/a b"},
    {"artifact_url": "https://example.com/" + "a" * 300},
    {"artifact_url": "https://example.com/a\"onload=1"},
    {"image_url": "https://example.com/card.svg"},
    {"image_url": "http://example.com/card.png"},
    {"shipped": "one line"},
    {"shipped": ["x"] * 6},
    {"shipped": [""]},
    {"shipped": ["   "]},
    {"shipped": ["x" * 121]},
    {"shipped": [3]},
    {"receipts": {"label": "x", "url": LINK}},
    {"receipts": [RECEIPT] * 6},
    {"receipts": [{"label": "ok", "url": LINK, "extra": "/Users/someone/secret"}]},
    {"receipts": [{"url": LINK}]},
    {"receipts": [{"label": "", "url": LINK}]},
    {"receipts": [{"label": "x" * 61, "url": LINK}]},
    {"receipts": [{"label": "ok", "url": "http://example.com/a"}]},
    {"receipts": ["https://example.com/a"]},
]


@pytest.mark.parametrize("bad", BAD_OUTCOMES)
def test_unsafe_or_malformed_outcomes_fail_loudly_instead_of_being_dropped(bad):
    with pytest.raises(ValueError):
        run_payload({"turns_typed": 2, **bad})
    with pytest.raises(ValueError):
        export_run({"turns_typed": 2, **bad})


def test_null_outcome_fields_mean_unknown():
    payload = run_payload({"turns_typed": 2, **{field: None for field in OUTCOME}})
    assert not set(OUTCOME) & set(payload)


def test_python_and_browser_contracts_accept_and_refuse_the_same_outcomes():
    # The browser preview and the database enforce the same rules. A payload Python lets out that
    # the browser then refuses would be the same silent gap in reverse.
    good = [five_field_run(), night_run(), {"turns_typed": 2}]
    runs = [{"turns_typed": 2, **bad} for bad in BAD_OUTCOMES] + good
    probe = Path(__file__).parent / "fixtures" / "outcome_parity_probe.mjs"
    result = subprocess.run(["node", str(probe)], input=json.dumps(runs), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    browser = json.loads(result.stdout)
    for run, browser_accepts in zip(runs, browser):
        try:
            export_run(run)
            python_accepts = True
        except ValueError:
            python_accepts = False
        assert python_accepts == browser_accepts, run
