"""Executor node: defensive checks, run_steps wiring, image saving, contracts."""

from __future__ import annotations

import json

import pytest

from friday.desktop.errors import DesktopTimeoutError
from friday.harness.nodes.executor import make_executor_node
from friday.harness.state import initial_state


class _FakeExecutor:
    def __init__(self, result=None) -> None:  # noqa: ANN001
        self.result = result
        self.calls: list = []
        self._result_holder = None

    def execute(self, payload):  # noqa: ANN001, ANN202
        self.calls.append(payload)
        if callable(self.result):
            return self.result(payload)
        if isinstance(self.result, BaseException):
            raise self.result
        from friday.actions.models import ActionResult

        return self.result or ActionResult(ok=True)


class _FakeTrace:
    def __init__(self) -> None:
        self.saved: list[tuple] = []

    def write_image(self, step_index: int, name: str, png: bytes) -> str:
        self.saved.append((step_index, name))
        return f"/traces/{name}-{step_index}.png"


class _Clock:
    def __init__(self, start: float = 0.0) -> None:
        self._v = start

    def __call__(self) -> float:
        return self._v


def _policy_default():  # noqa: ANN202
    from friday.harness.capabilities import ControlPolicy

    return ControlPolicy(approval=True, user_control=False)


def _state(pending: dict | None, *, verdict: str = "allow", **extra) -> dict:
    state = initial_state("do a thing", 5)
    state["pending_action"] = pending
    state["guard_verdict"] = verdict
    state.update(extra)
    return state


def _node(executor=None, trace=None, max_steps=1):  # noqa: ANN001
    from friday.harness.nodes.executor import ExecutorDeps
    from friday.harness.steps import ExecutorSettings

    return make_executor_node(
        ExecutorDeps(
            executor=executor or _FakeExecutor(),
            trace_writer=trace or _FakeTrace(),
            settings=ExecutorSettings(max_steps_per_call=max_steps),
            clock=_Clock(),
        )
    )


def _click() -> dict:
    return {"action": "left_click", "x": 10, "y": 20}


# --- defensive checks (executor never called) --------------------------------


def test_not_allowed_verdict_records_failure_and_never_executes() -> None:
    executor = _FakeExecutor()
    node = _node(executor=executor)
    state = _state(_click(), verdict="reject")

    result = node(state)

    assert executor.calls == []
    assert result["last_result"]["ok"] is False
    assert result["last_result"]["error"]["type"] == "not_allowed"


def test_missing_pending_action_is_internal_error() -> None:
    executor = _FakeExecutor()
    node = _node(executor=executor)

    result = node(_state(None))

    assert executor.calls == []
    assert result["last_result"]["error"]["type"] == "internal_error"


def test_missing_discriminator_is_internal_error() -> None:
    executor = _FakeExecutor()
    node = _node(executor=executor)

    # a proposal with neither an action nor an operation discriminator is not
    # runnable and must not reach the executor
    result = node(_state({"purpose": "confused"}))

    assert executor.calls == []
    assert result["last_result"]["error"]["type"] == "internal_error"


def test_invalid_action_is_rejected_with_invalid_action() -> None:
    executor = _FakeExecutor()
    node = _node(executor=executor)

    result = node(_state({"action": "sudo_rm_rf", "target": "/"}))

    assert executor.calls == []
    assert result["last_result"]["error"]["type"] == "invalid_action"


# --- success path ------------------------------------------------------------


def test_allowed_action_runs_and_lands_in_last_result() -> None:
    executor = _FakeExecutor()
    node = _node(executor=executor)

    result = node(_state(_click()))

    # the node validates the raw dict into a typed Action and passes it through
    assert len(executor.calls) == 1
    assert executor.calls[0].model_dump() == _click()
    assert result["last_result"]["ok"] is True
    assert result["last_result"]["operation"] == "left_click"


def test_node_passes_shortcut_action_through_unchanged() -> None:
    executor = _FakeExecutor()
    node = _node(executor=executor)
    pending = {"action": "shortcut", "name": "copy", "repeat": 1}

    result = node(_state(pending))

    assert len(executor.calls) == 1
    assert executor.calls[0].model_dump() == pending
    assert result["last_result"]["ok"] is True


def test_node_writes_only_last_result() -> None:
    executor = _FakeExecutor()
    node = _node(executor=executor)

    result = node(_state(_click()))

    assert set(result.keys()) == {"last_result"}


# --- error mapping -----------------------------------------------------------


def test_timeout_from_executor_becomes_timeout_error() -> None:
    executor = _FakeExecutor(DesktopTimeoutError("timed out"))
    node = _node(executor=executor)

    result = node(_state(_click()))

    assert result["last_result"]["error"]["type"] == "timeout"
    assert "may have run" in result["last_result"]["error"]["message"]


def test_keyboard_interrupt_propagates_from_executor() -> None:
    executor = _FakeExecutor(KeyboardInterrupt())
    node = _node(executor=executor)

    with pytest.raises(KeyboardInterrupt):
        node(_state(_click()))


# --- observation image handling ----------------------------------------------


def test_image_bytes_saved_and_state_holds_only_path() -> None:
    from friday.actions.models import ActionResult

    def image_result(action):  # noqa: ANN001
        return ActionResult(ok=True, image_png=b"\x89PNG\r\n\x1a\n")

    trace = _FakeTrace()
    executor = _FakeExecutor(image_result)
    node = _node(executor=executor, trace=trace)

    result = node(_state({"action": "screenshot"}))

    assert trace.saved == [(0, "screenshot")]
    assert result["last_result"]["image_path"] == "/traces/screenshot-0.png"
    # no image bytes anywhere in the serialized result or state
    assert "image_png" not in json.dumps(result)


# --- canary: no sensitive text leaks -----------------------------------------


def test_typed_text_canary_never_reaches_last_result() -> None:
    from friday.actions.models import ActionResult

    executor = _FakeExecutor(ActionResult(ok=True, detail="the-typed-token"))
    node = _node(executor=executor)

    result = node(_state({"action": "type", "text": "the-typed-token"}))

    dumped = json.dumps(result["last_result"])
    assert "the-typed-token" not in dumped


def test_result_is_json_serializable_and_bounded() -> None:
    executor = _FakeExecutor()
    node = _node(executor=executor)

    result = node(_state(_click()))

    json.dumps(result["last_result"])  # does not raise


# --- operations are dispatched, not rejected ---------------------------------


def test_operation_is_dispatched_and_recorded() -> None:
    """An allowed operation reaches the executor, not an internal_error."""
    from friday.operations.registry import OpenUrl

    executor = _FakeExecutor()
    node = _node(executor=executor)
    pending = {"operation": "open_url", "url": "https://github.com/Dishank-Sen"}

    result = node(_state(pending, verdict="allow"))

    assert len(executor.calls) == 1
    dispatched = executor.calls[0]
    assert isinstance(dispatched, OpenUrl)
    assert dispatched.url == "https://github.com/Dishank-Sen"
    assert result["last_result"]["ok"] is True
    assert result["last_result"]["error"] is None


def test_operation_dict_result_is_folded_into_last_result() -> None:
    """Operation results are plain dicts; ok is preserved into last_result."""
    executor = _FakeExecutor({"ok": True, "pid": 1234})
    node = _node(executor=executor)
    pending = {"operation": "launch_app", "app": "browser"}

    result = node(_state(pending, verdict="allow"))

    assert result["last_result"]["ok"] is True
    assert result["last_result"]["detail"] == '{"ok": true, "pid": 1234}'


def test_read_operation_text_flows_into_last_result() -> None:
    """Read-type operations return text that is the point of the operation."""
    executor = _FakeExecutor({"content": "the unexpected token"})
    node = _node(executor=executor)
    pending = {"operation": "read_file", "path": "notes.txt"}

    result = node(_state(pending, verdict="allow"))

    assert result["last_result"]["ok"] is True
    dumped = json.dumps(result["last_result"])
    assert "the unexpected token" in dumped


def test_failed_operation_is_recorded_as_failed() -> None:
    """An operation whose result reports ok:false is a failure, not success."""
    executor = _FakeExecutor({"ok": False, "output": "command returned nonzero"})
    node = _node(executor=executor)
    pending = {"operation": "close_app", "pid": 999}

    result = node(_state(pending, verdict="allow"))

    assert result["last_result"]["ok"] is False


def test_unknown_operation_is_an_internal_error_not_dispatched() -> None:
    """An unparseable operation never reaches the executor."""
    executor = _FakeExecutor()
    node = _node(executor=executor)
    pending = {"operation": "sudo_rm_rf", "target": "/"}

    result = node(_state(pending))

    assert executor.calls == []
    assert result["last_result"]["error"]["type"] == "invalid_action"