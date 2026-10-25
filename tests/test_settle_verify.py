"""Settle and verify nodes: post-execution reconciliation that lets the loop advance."""

from __future__ import annotations

import pytest

from friday.harness.nodes.settle import make_settle
from friday.harness.nodes.verify import make_verify
from friday.harness.state import initial_state


class _Observation:
    def __init__(self) -> None:
        from friday.desktop.observation import WindowInfo

        self.screenshot_png = b"\x89PNG\r\n\x1a\n"
        self.screen_size = (1280, 720)
        self.windows = [WindowInfo(id="1", title="Chromium", class_name="Chromium", active=True)]
        self.active_window_class = "Chromium"
        self.focused_app = "browser"


class _Client:
    def __init__(self, observation=None) -> None:  # noqa: ANN001
        self._observation = observation or _Observation()
        self.calls = 0

    def observation(self):
        self.calls += 1
        return self._observation


class _FailingClient:
    def observation(self):
        raise RuntimeError("desktop unavailable")


class _Trace:
    def __init__(self) -> None:
        self.writes = 0

    def write(self, observation, error=None):  # noqa: ANN001
        self.writes += 1
        return f"/traces/screenshot-{self.writes}.png"


def _focus(table_class):  # noqa: ANN001, ANN202
    return "browser"


def _settle(client=None, trace=None, focus=None):  # noqa: ANN001
    return make_settle(
        client or _Client(), trace or _Trace(), focus or _focus
    )


def _base(**overrides) -> dict:
    state = initial_state("open a web page", 10)
    state["step"] = 1
    state["retries"] = 2
    state["history"] = []
    state["screenshot_path"] = "/traces/screenshot-0.png"
    state["stuck_count"] = 0
    state.update(overrides)
    return state


# --- settle: post-execution refresh -----------------------------------------


def test_settle_rotates_prev_and_refreshes_capture_with_fresh_observation() -> None:
    client = _Client()
    trace = _Trace()
    node = _settle(client=client, trace=trace)
    state = _base(screenshot_path="/traces/previous.png")

    result = node(state)

    assert result["prev_screenshot_path"] == "/traces/previous.png"
    assert result["screenshot_path"].startswith("/traces/")
    assert client.calls == 1
    assert trace.writes == 1
    assert result["screen_size"] == (1280, 720)
    assert result["windows"] == [
        {"id": "1", "title": "Chromium", "class_name": "Chromium", "active": True}
    ]
    assert result["focused_app"] == "browser"


def test_settle_writes_only_its_contract_fields() -> None:
    result = _settle()(_base())

    assert set(result.keys()) == {
        "prev_screenshot_path",
        "screenshot_path",
        "screen_size",
        "windows",
        "focused_app",
    }


def test_settle_survives_observation_failure_without_losing_prior_path() -> None:
    node = _settle(client=_FailingClient())
    state = _base(screenshot_path="/traces/previous.png")

    result = node(state)

    # the prior capture is unchanged on failure; no fields are invented
    assert result.get("prev_screenshot_path") == "/traces/previous.png"
    assert "screenshot_path" not in result


# --- verify: step advance, history, stuck tracking ---------------------------


def _verify(**kwargs):  # noqa: ANN202
    return make_verify(**kwargs)


def _history_of(update: dict) -> list:
    return update["history"]


def test_verify_advances_step_on_success() -> None:
    node = _verify()
    state = _base(
        step=2,
        decision="action",
        pending_action={"action": "left_click", "x": 1, "y": 2},
        last_result={"ok": True, "operation": "left_click"},
    )

    result = node(state)

    assert result["step"] == 3


def test_verify_records_success_in_history() -> None:
    node = _verify()
    pending = {"action": "wait", "seconds": 1}
    state = _base(decision="action", pending_action=pending, last_result={"ok": True})

    result = node(state)
    entry = _history_of(result)[-1]

    assert entry["action"] == pending
    assert entry["decision"] == "action"
    assert entry["outcome"] == "succeeded"


def test_verify_records_failure_in_history() -> None:
    node = _verify()
    pending = {"action": "shortcut", "name": "copy"}
    state = _base(
        decision="action",
        pending_action=pending,
        last_result={"ok": False, "operation": "shortcut"},
    )

    result = node(state)
    entry = _history_of(result)[-1]

    assert entry["outcome"] == "failed"
    assert entry["action"] == pending


def test_verify_appends_to_existing_history() -> None:
    node = _verify()
    prior = [{"decision": "action", "outcome": "succeeded", "action": {"action": "wait"}}]
    state = _base(
        decision="action",
        pending_action={"action": "key", "key": "a"},
        last_result={"ok": True},
        history=list(prior),
    )

    result = node(state)

    assert len(result["history"]) == 2
    assert result["history"][0] == prior[0]


def test_verify_does_not_mutate_the_input_state_history() -> None:
    node = _verify()
    prior = [{"decision": "action", "outcome": "succeeded", "action": {"action": "wait"}}]
    state = _base(
        decision="action",
        pending_action={"action": "key", "key": "a"},
        last_result={"ok": True},
        history=list(prior),
    )

    node(state)

    assert state["history"] == prior


def test_failed_result_increments_stuck_count_with_hint() -> None:
    node = _verify()
    state = _base(
        decision="action",
        pending_action={"action": "left_click", "x": 1, "y": 2},
        last_result={"ok": False, "operation": "left_click"},
        stuck_count=1,
    )

    result = node(state)

    assert result["stuck_count"] == 2


def test_success_resets_stuck_count() -> None:
    node = _verify()
    state = _base(
        decision="action",
        pending_action={"action": "left_click", "x": 1, "y": 2},
        last_result={"ok": True},
        stuck_count=2,
    )

    result = node(state)

    assert result["stuck_count"] == 0


def test_reaching_stuck_limit_marks_run_failed() -> None:
    node = _verify()
    state = _base(
        decision="action",
        pending_action={"action": "left_click", "x": 1, "y": 2},
        last_result={"ok": False, "operation": "left_click"},
        stuck_count=2,
    )

    result = node(state)

    assert result["status"] == "failed"
    assert "final_report" in result


def test_below_stuck_limit_leaves_status_running() -> None:
    node = _verify()
    state = _base(
        decision="action",
        pending_action={"action": "left_click", "x": 1, "y": 2},
        last_result={"ok": False, "operation": "left_click"},
        stuck_count=0,
    )

    result = node(state)

    assert result.get("status", "running") == "running"


def test_verify_writes_only_its_contract_fields() -> None:
    state = _base(
        decision="action",
        pending_action={"action": "left_click", "x": 1, "y": 2},
        last_result={"ok": True},
        stuck_count=0,
    )

    result = _verify()(state)

    assert set(result.keys()) <= {
        "step",
        "history",
        "stuck_count",
        "final_report",
        "status",
        "hint",
    }


@pytest.mark.parametrize(
    "last_result,expected",
    [
        ({"ok": True}, "succeeded"),
        ({"ok": False, "operation": "key"}, "failed"),
    ],
)
def test_verify_sensitive_history_outcome_is_classified_not_payload(
    last_result, expected
) -> None:
    """A failed sensitive action's history entry classifies the outcome only."""
    node = _verify()
    state = _base(
        decision="action",
        pending_action={"action": "key", "key": "secret"},
        last_result=last_result,
    )

    result = node(state)
    entry = _history_of(result)[-1]

    assert entry["outcome"] == expected
    dumped = str(entry)
    assert "secret" not in dumped