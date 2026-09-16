"""Commit ticks and the ridge under them must come from one clock.

The defect this pins: the timed branch took a call index counted in the TRANSCRIPT and looked it up
in the STORE's tool order. The two sequences have different lengths and different orderings, so a
tick landed in the wrong bin or fell off the end.

The fixture below is deliberately built from TWO lists, not one. A fixture generated from a single
list cannot fail this test, which is exactly how the defect shipped past the earlier suite.
"""
from agentgrinder.cursor_tree import ridge_from_calls


def stamp(second: int) -> str:
    """One stamp per second inside a 1000 second window starting at a fixed instant."""
    minutes, seconds = divmod(second, 60)
    hours, minutes = divmod(minutes, 60)
    return "2026-09-16T%02d:%02d:%02d.000Z" % (hours, minutes, seconds)


# The store saw 100 tool calls, one every ten seconds, so its window is [0, 990].
STORE_CALLS = [stamp(i * 10) for i in range(100)]
# One commit, at second 900. In a 50 bin ridge over [0, 990] that is bin 45.
COMMIT = stamp(900)
# The transcript counted its own 80 calls. Its index for the same commit is 70. The store's 71st
# call by time is at second 700, which is bin 35. The two answers are 10 bins apart on a 50 bin
# ridge, a fifth of the card's width.
TRANSCRIPT_COMMIT_INDEX = 70


def test_a_timed_ridge_places_the_tick_by_the_clock_not_by_a_transcript_index():
    timed = ridge_from_calls(STORE_CALLS, STORE_CALLS, None,
                             commit_call_indices=[TRANSCRIPT_COMMIT_INDEX],
                             commit_stamps=[COMMIT])
    assert timed["ridge_basis"] == "wall-time"
    assert timed["commit_basis"] == "wall-time"
    assert timed["commit_bins"] == [45]


def test_the_old_index_rule_puts_the_same_tick_somewhere_else():
    """The control. Without stamps the timed branch falls back, and the answer moves."""
    without = ridge_from_calls(STORE_CALLS, STORE_CALLS, None,
                               commit_call_indices=[TRANSCRIPT_COMMIT_INDEX],
                               commit_stamps=None)
    assert without["commit_basis"] == "call-index"
    assert without["commit_bins"] == [35]


def test_an_untimed_ridge_still_uses_the_call_index_and_says_so():
    untimed = ridge_from_calls([None] * 80, commit_call_indices=[TRANSCRIPT_COMMIT_INDEX])
    assert untimed["ridge_basis"] == "call-index"
    assert untimed["commit_basis"] == "call-index"
    assert untimed["commit_bins"] == [43]


def test_every_tick_stays_inside_the_ridge_even_when_a_commit_sits_on_the_edge():
    edge = ridge_from_calls(STORE_CALLS, STORE_CALLS, None,
                            commit_stamps=[stamp(0), stamp(990)])
    assert all(0 <= b < len(edge["ridge"]) for b in edge["commit_bins"])
    assert edge["commit_bins"] == [0, 49]


def test_a_measured_zero_is_a_measured_zero_not_a_fall_back_to_the_index():
    """An empty stamp list means the clock saw no commit. It must not reopen the index rule."""
    none = ridge_from_calls(STORE_CALLS, STORE_CALLS, None,
                            commit_call_indices=[TRANSCRIPT_COMMIT_INDEX], commit_stamps=[])
    assert none["commit_bins"] == []
    assert none["commit_basis"] == "wall-time"
