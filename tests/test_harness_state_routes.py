import logging

import pytest

from friday.harness.routes import route_after_decide, route_after_guard
from friday.harness.state import initial_state


def test_initial_state_has_neutral_defaults() -> None:
    state = initial_state("open terminal", 7)

    assert state == {
        "goal": "open terminal",
        "status": "running",
        "step": 0,
        "max_steps": 7,
        "started_at": 0.0,
        "screenshot_path": None,
        "prev_screenshot_path": None,
        "decision": None,
        "pending_action": None,
        "guard_verdict": None,
        "last_result": None,
        "history": [],
        "hint": None,
        "retries": 0,
        "stuck_count": 0,
        "final_report": None,
    }


@pytest.mark.parametrize(
    ("decision", "expected"),
    [("action", "guard"), ("done", "finish"), ("fail", "finish"), ("retry", "build_context")],
)
def test_route_after_decide(decision: str, expected: str) -> None:
    state = initial_state("goal", 1)
    state["decision"] = decision  # type: ignore[typeddict-item]
    assert route_after_decide(state) == expected


@pytest.mark.parametrize(
    ("verdict", "expected"),
    [("allow", "executor"), ("reject", "build_context"), ("stop", "finish")],
)
def test_route_after_guard(verdict: str, expected: str) -> None:
    state = initial_state("goal", 1)
    state["guard_verdict"] = verdict  # type: ignore[typeddict-item]
    assert route_after_guard(state) == expected


@pytest.mark.parametrize(
    ("route", "field"), [(route_after_decide, "decision"), (route_after_guard, "guard_verdict")]
)
def test_missing_route_value_finishes_with_warning(
    caplog: pytest.LogCaptureFixture, route: object, field: str
) -> None:
    state = initial_state("goal", 1)
    with caplog.at_level(logging.WARNING):
        assert route(state) == "finish"  # type: ignore[operator]
    assert field in caplog.text


@pytest.mark.parametrize(
    ("route", "field"), [(route_after_decide, "decision"), (route_after_guard, "guard_verdict")]
)
def test_unknown_route_value_raises(route: object, field: str) -> None:
    state = initial_state("goal", 1)
    state[field] = "unknown"  # type: ignore[literal-required]
    with pytest.raises(ValueError, match="unknown"):
        route(state)  # type: ignore[operator]
