"""The executor-boundary run_steps: success, failure, batching, error mapping."""

from __future__ import annotations

import pytest

from friday.actions.models import ActionResult, parse_action
from friday.desktop.errors import (
    DesktopConnectionError,
    DesktopRequestError,
    DesktopTimeoutError,
)
from friday.harness.steps import (
    ConfigurationError,
    ExecutorSettings,
    StepSpec,
    run_steps,
)


class _FakeExecutor:
    def __init__(self, result: ActionResult | Exception, *, calls: list | None = None) -> None:
        self._result = result
        self.calls = calls if calls is not None else []

    def execute(self, action: object) -> ActionResult:
        self.calls.append(action)
        if isinstance(self._result, BaseException):
            raise self._result
        return self._result


def _step(payload: str, expected_result: str | None = None) -> StepSpec:
    return StepSpec(action=parse_action(payload), expected_result=expected_result)


def _ok(detail: str | None = None, point=None, image: bytes | None = None) -> ActionResult:
    return ActionResult(ok=True, detail=detail, point=point, image_png=image)


def _clock(now: float = 0.0):
    def tick() -> float:
        return now

    return tick


# --- success -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("payload", "operation"),
    [
        ('{"action":"left_click","x":1,"y":2}', "left_click"),
        ('{"action":"type","text":"hi"}', "type"),
        ('{"action":"key","key":"ctrl+a"}', "key"),
        ('{"action":"shortcut","name":"copy"}', "shortcut"),
        ('{"action":"scroll","amount":2}', "scroll"),
        ('{"action":"wait","seconds":0.1}', "wait"),
        ('{"action":"screenshot"}', "screenshot"),
    ],
)
def test_success_for_each_operation_family(payload: str, operation: str) -> None:
    executor = _FakeExecutor(_ok())
    outcomes = run_steps(executor, [_step(payload)])

    assert len(outcomes) == 1
    assert outcomes[0].ok is True
    assert outcomes[0].operation == operation
    assert outcomes[0].error is None


def test_one_step_runs_and_records_duration() -> None:
    executor = _FakeExecutor(_ok())
    outcomes = run_steps(executor, [_step('{"action":"left_click","x":1,"y":2}')])

    assert len(outcomes) == 1
    assert outcomes[0].duration_ms == 0


@pytest.mark.parametrize("limit", [1, 2])
def test_sequence_length_must_not_exceed_max_steps_per_call(limit: int) -> None:
    executor = _FakeExecutor(_ok())
    steps = [_step('{"action":"left_click","x":1,"y":2}')] * (limit + 1)

    with pytest.raises(ConfigurationError, match="batching is not enabled"):
        run_steps(executor, steps, settings=ExecutorSettings(max_steps_per_call=limit))


def test_two_steps_run_when_max_steps_per_call_is_two() -> None:
    executor = _FakeExecutor(_ok())
    steps = [
        _step('{"action":"left_click","x":1,"y":2}'),
        _step('{"action":"key","key":"ctrl+a"}'),
    ]

    outcomes = run_steps(executor, steps, settings=ExecutorSettings(max_steps_per_call=2))

    assert len(outcomes) == 2
    assert all(outcome.ok for outcome in outcomes)


# --- failure and stop-at-first-failure ---------------------------------------


def test_stops_at_first_failure_and_returns_outcomes_so_far() -> None:
    calls: list[object] = []

    def execute(action):  # noqa: ANN001, ANN202
        calls.append(action)
        if len(calls) == 1:
            return ActionResult(ok=True)
        return ActionResult(ok=False, detail="boom")

    class _FailingAfterFirst:
        def execute(self, action: object):  # noqa: ANN002
            return execute(action)

    executor = _FailingAfterFirst()
    steps = [
        _step('{"action":"left_click","x":1,"y":2}'),
        _step('{"action":"key","key":"ctrl+a"}'),
    ]

    outcomes = run_steps(executor, steps, settings=ExecutorSettings(max_steps_per_call=2))

    assert [outcome.ok for outcome in outcomes] == [True, False]
    assert len(calls) == 2  # the third would stop; here exactly two run


def test_failure_records_outcome_without_raising() -> None:
    executor = _FakeExecutor(ActionResult(ok=False, detail="rejected by server"))

    outcomes = run_steps(executor, [_step('{"action":"scroll","amount":2}')])

    assert len(outcomes) == 1
    assert outcomes[0].ok is False


# --- typed error mapping -----------------------------------------------------


def test_timeout_maps_to_timeout_with_outcome_unknown_note() -> None:
    executor = _FakeExecutor(DesktopTimeoutError("timeout"))
    outcomes = run_steps(executor, [_step('{"action":"key","key":"a"}')])

    assert outcomes[0].error == {
        "type": "timeout",
        "message": "outcome unknown: the action may have run; check the screen before repeating",
    }


def test_connection_error_maps_to_connection() -> None:
    executor = _FakeExecutor(DesktopConnectionError("down"))
    outcomes = run_steps(executor, [_step('{"action":"key","key":"a"}')])

    assert outcomes[0].error == {
        "type": "connection",
        "message": "outcome unknown: the control server could not be reached",
    }


def test_client_rejection_maps_to_rejected_by_server() -> None:
    executor = _FakeExecutor(DesktopRequestError(422, "bad request"))
    outcomes = run_steps(executor, [_step('{"action":"key","key":"a"}')])

    assert outcomes[0].error["type"] == "rejected_by_server"


def test_server_command_failure_maps_to_command_failed() -> None:
    executor = _FakeExecutor(DesktopRequestError(502, "command failed"))
    outcomes = run_steps(executor, [_step('{"action":"key","key":"a"}')])

    assert outcomes[0].error["type"] == "command_failed"


def test_unknown_exception_maps_to_unknown_without_traceback() -> None:
    executor = _FakeExecutor(RuntimeError("boom raw detail"))
    outcomes = run_steps(executor, [_step('{"action":"key","key":"a"}')])

    assert outcomes[0].error["type"] == "unknown"
    assert "Traceback" not in outcomes[0].error["message"]


def test_keyboard_interrupt_propagates() -> None:
    executor = _FakeExecutor(KeyboardInterrupt())

    with pytest.raises(KeyboardInterrupt):
        run_steps(executor, [_step('{"action":"key","key":"a"}')])


# --- result shape ------------------------------------------------------------


def test_last_result_is_json_serializable_and_bounded() -> None:
    import json

    executor = _FakeExecutor(_ok(detail="x" * 1000))
    outcome = run_steps(executor, [_step('{"action":"screenshot"}')])[0]

    dumped = json.dumps(outcome.model_dump(mode="json"))
    assert dumped  # serializes
    assert len(outcome.detail) <= 400
    assert outcome.detail.endswith("…")  # truncation visibly marked


def test_image_bytes_are_transient_and_never_serialized() -> None:
    executor = _FakeExecutor(_ok(image=b"\x89PNG\r\n\x1a\n"))
    outcome = run_steps(executor, [_step('{"action":"screenshot"}')])[0]

    assert outcome.image_png == b"\x89PNG\r\n\x1a\n"
    serialized = outcome.model_dump(mode="json")
    assert "image_png" not in serialized or serialized.get("image_png") is None


def test_point_and_expected_result_are_recorded() -> None:
    executor = _FakeExecutor(_ok(point=(3, 4)))
    outcome = run_steps(executor, [_step('{"action":"left_click","x":3,"y":4}', "click at 3,4")])[0]

    assert outcome.point == [3, 4]
    assert outcome.expected_result == "click at 3,4"


def test_sensitive_operation_detail_is_not_surfaced() -> None:
    executor = _FakeExecutor(_ok(detail="SHOULD-NOT-LEAK"))
    outcome = run_steps(executor, [_step('{"action":"type","text":"SCKRET"}')])[0]

    assert outcome.detail is None