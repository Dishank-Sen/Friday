"""The exec-once CLI runs guard then executor against a live sandbox."""

from __future__ import annotations

from unittest.mock import patch

from friday import __main__


class _Args:
    action = '{"action": "left_click", "x": 10, "y": 20}'
    trace_dir = ".friday-traces"


class _Sandbox:
    config = type("Config", (), {"request_timeout": 5.0})()  # noqa: SLF001


def _state() -> dict:
    return {"goal": "g", "max_steps": 5, "pending_action": None, "guard_verdict": None}


def test_exec_once_uses_observe_guard_and_executor() -> None:
    calls: list[str] = []

    def fake_observe(client, trace, focus):  # noqa: ANN001
        calls.append("observe")
        return lambda s: {"screen_size": (1280, 720), "focused_app": "browser"}

    def fake_guard(**kwargs):  # noqa: ANN001
        calls.append("guard")
        return lambda s: {"guard_verdict": "allow"}

    def fake_executor(deps):  # noqa: ANN001
        calls.append("executor")
        return lambda s: {"last_result": {"ok": True, "operation": "left_click"}}

    with patch("friday.__main__.make_observe", side_effect=fake_observe), patch(
        "friday.__main__.make_guard", side_effect=fake_guard
    ), patch(
        "friday.__main__.make_executor_node",
        side_effect=lambda deps: fake_executor(deps),
    ), patch(
        "friday.__main__._load_sandbox", return_value=_Sandbox()
    ), patch("friday.__main__.DesktopClient"), patch(
        "friday.__main__.initial_state", side_effect=lambda goal, max_steps: _state()
    ), patch("friday.__main__.time.time", return_value=0.0):
        rc = __main__._exec_once(_Args(), print=print)

    assert rc == 0
    assert calls == ["observe", "guard", "executor"]


def test_exec_once_skips_executor_when_guard_rejects() -> None:
    calls: list[str] = []

    def fake_observe(client, trace, focus):  # noqa: ANN001
        calls.append("observe")
        return lambda s: {}

    def fake_guard(**kwargs):  # noqa: ANN001
        calls.append("guard")
        return lambda s: {"guard_verdict": "reject", "hint": "no"}

    seen: list[str] = []

    def fake_executor(deps):  # noqa: ANN001
        calls.append("executor")
        return lambda s: {"last_result": {"ok": True}}

    with patch("friday.__main__.make_observe", side_effect=fake_observe), patch(
        "friday.__main__.make_guard", side_effect=fake_guard
    ), patch(
        "friday.__main__.make_executor_node",
        side_effect=lambda deps: fake_executor(deps),
    ), patch(
        "friday.__main__._load_sandbox", return_value=_Sandbox()
    ), patch("friday.__main__.DesktopClient"), patch(
        "friday.__main__.initial_state", side_effect=lambda goal, max_steps: _state()
    ), patch("friday.__main__.time.time", return_value=0.0):
        __main__._exec_once(_Args(), print=lambda s: seen.append(s))

    assert calls == ["observe", "guard"]
    assert any("reject" in line for line in seen)