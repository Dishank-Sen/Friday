"""Finish node: resolve the run's terminal status and final report."""

from __future__ import annotations

from friday.harness.nodes.finish import make_finish
from friday.harness.state import initial_state


def _base(**overrides) -> dict:
    state = initial_state("open a web page", 10)
    state["final_report"] = None
    state.update(overrides)
    return state


def _finish(**kwargs):  # noqa: ANN202
    return make_finish(**kwargs)


def test_done_decision_is_finished_with_report() -> None:
    node = _finish()
    state = _base(decision="done", final_report="opened the page")

    result = node(state)

    assert result["status"] == "done"
    assert result["final_report"] == "opened the page"


def test_done_decision_defaults_report() -> None:
    result = _finish()(_base(decision="done"))

    assert result["status"] == "done"
    assert result["final_report"] == "task complete"


def test_fail_decision_is_failed() -> None:
    result = _finish()(_base(decision="fail"))

    assert result["status"] == "failed"
    assert result["final_report"] == "task failed"


def test_guard_stop_is_stopped() -> None:
    result = _finish()(_base(decision="action", guard_verdict="stop", hint="time budget exhausted"))

    assert result["status"] == "stopped"
    assert "budget" in result["final_report"]


def test_existing_failed_status_is_preserved() -> None:
    result = _finish()(_base(status="failed", final_report="stuck after 3 failed actions"))

    assert result["status"] == "failed"
    assert result["final_report"] == "stuck after 3 failed actions"


def test_unknown_terminal_state_stops_with_report() -> None:
    result = _finish()(_base(decision="action", guard_verdict="allow"))

    assert result["status"] == "stopped"
    assert result["final_report"] == "no decision reached"


def test_finish_writes_only_status_and_final_report() -> None:
    result = _finish()(_base(decision="done"))

    assert set(result.keys()) <= {"status", "final_report"}