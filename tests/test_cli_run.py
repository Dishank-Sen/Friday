"""The CLI `run` path assembles the live graph through the composition root."""

from __future__ import annotations

from unittest.mock import patch

from friday import __main__


class _Args:
    goal = "open the terminal"
    trace_dir = ".friday-traces"


class _Graph:
    def invoke(self, state):
        return {"decision": "done"}


class _Sandbox:
    config = type("Config", (), {"request_timeout": 5.0})()


class _DepsRecorder:
    def __init__(self, deps) -> None:
        self.deps = deps


def _run(fake_build):
    with patch("friday.__main__.build_production_graph", side_effect=fake_build), patch(
        "friday.__main__.DesktopClient"
    ), patch("friday.__main__.create_llm"), patch(
        "friday.__main__._load_sandbox", return_value=_Sandbox()
    ):
        return __main__._run_task(_Args())


def test_run_task_builds_the_production_graph() -> None:
    built: list[bool] = []

    def fake_build(deps, *, checkpointer=None, allow_stubs=False):
        built.append(True)
        return _Graph()

    rc = _run(fake_build)

    assert rc == 0
    assert built == [True]


def test_run_task_passes_desktop_client_and_policy_into_composition_root() -> None:
    seen: dict = {}

    def fake_build(deps, *, checkpointer=None, allow_stubs=False):
        seen["client"] = deps.client
        seen["policy"] = type(deps.policy).__name__
        seen["llm"] = deps.llm is not None
        return _Graph()

    _run(fake_build)

    assert seen["client"] is not None
    assert seen["policy"] == "_CliPolicy"
    assert seen["llm"] is True


def test_run_task_feeds_goal_into_initial_state() -> None:
    states: list[dict] = []

    def fake_build(deps, *, checkpointer=None, allow_stubs=False):
        return _Graph()

    with patch("friday.__main__.build_production_graph", side_effect=fake_build), patch(
        "friday.__main__.DesktopClient"
    ), patch("friday.__main__.create_llm"), patch(
        "friday.__main__._load_sandbox", return_value=_Sandbox()
    ), patch(
        "friday.__main__.initial_state", side_effect=lambda goal, max_steps: {"goal": goal}
    ) as initial:
        __main__._run_task(_Args())

    assert initial.call_args.args[0] == "open the terminal"