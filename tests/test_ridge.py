"""Ridge binning keeps counts exact and falls back when Cursor's clock is incomplete."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from agentgrinder.cursor_tree import ridge_from_calls


def stamps(count):
    start = datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc)
    return [(start + timedelta(seconds=index)).isoformat() for index in range(count)]


def test_empty_run_has_fixed_call_index_bins():
    result = ridge_from_calls([])
    assert len(result["ridge"]) == 50
    assert sum(result["ridge"]) == 0
    assert result["ridge_basis"] == "call-index"


def test_one_timed_call_is_not_duplicated():
    one = stamps(1)
    result = ridge_from_calls(one, one)
    assert len(result["ridge"]) == 50
    assert sum(result["ridge"]) == 1
    assert result["ridge_basis"] == "wall-time"


def test_large_run_preserves_all_3221_calls():
    calls = stamps(3221)
    result = ridge_from_calls(calls, calls)
    assert len(result["ridge"]) == 50
    assert sum(result["ridge"]) == 3221
    assert max(result["ridge"]) - min(result["ridge"]) <= 1


def test_any_missing_tool_timestamp_uses_call_index():
    calls = stamps(4)
    calls[2] = None
    result = ridge_from_calls(calls, stamps(4))
    assert result["ridge_basis"] == "call-index"
    assert sum(result["ridge"]) == 4


def test_bin_count_is_bounded():
    with pytest.raises(ValueError):
        ridge_from_calls([], bins=39)
    with pytest.raises(ValueError):
        ridge_from_calls([], bins=61)


def test_sample_ridge_matches_recorded_tool_and_commit_counts():
    sample = json.loads(
        (Path(__file__).resolve().parents[1] / "samples/sample_run.json").read_text())
    assert len(sample["ridge"]) == len(sample["worker_bins"]) == 50
    assert sum(sample["ridge"]) == sample["tool_calls"]
    assert len(sample["commit_bins"]) == sample["commits"]
