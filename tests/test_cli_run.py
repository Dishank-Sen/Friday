"""The CLI `run` path assembles the live graph through the composition root."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from friday import __main__


class _Args:
    goal = "open the terminal"
    trace_dir = ".friday-traces"


class _Graph:
    def invoke(self, state, config=None):
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


def test_run_task_wires_a_real_executor_dependency() -> None:
    seen: dict = {}

    def fake_build(deps, *, checkpointer=None, allow_stubs=False):
        seen["executor"] = deps.executor is not None
        return _Graph()

    _run(fake_build)

    assert seen["executor"] is True


def test_run_task_stamps_started_at_before_the_graph_runs() -> None:
    # The guard relies on started_at for its wall-clock time budget, so a live
    # run must set it (using the injected wall clock) before the graph invokes.
    invoked_with: dict = {}

    def fake_initial(goal, max_steps):  # noqa: ANN001
        return {"goal": goal, "started_at": 0.0}

    class _G:
        @staticmethod
        def invoke(state, config=None):  # noqa: ANN001
            invoked_with["started_at"] = state["started_at"]
            return {"decision": "done"}

    def fake_build(deps, *, checkpointer=None, allow_stubs=False):
        return _G()

    with patch("friday.__main__.build_production_graph", side_effect=fake_build), patch(
        "friday.__main__.DesktopClient"
    ), patch("friday.__main__.create_llm"), patch(
        "friday.__main__._load_sandbox", return_value=_Sandbox()
    ), patch("friday.__main__.initial_state", side_effect=fake_initial), patch(
        "friday.__main__.time.time", return_value=1234.0
    ):
        __main__._run_task(_Args())

    # started_at (0.0 from initial_state) must be replaced by the runner's wall
    # clock stamp before the first node runs
    assert invoked_with["started_at"] == 1234.0


def test_run_task_prints_loop_diagnostic_on_recursion() -> None:
    captured: list[str] = []

    class _RaisingGraph:
        def invoke(self, state, config=None):  # noqa: ANN001
            raise RuntimeError("recursion limit reached")

    def fake_build(deps, *, checkpointer=None, allow_stubs=False):
        return _RaisingGraph()

    with patch("friday.__main__.build_production_graph", side_effect=fake_build), patch(
        "friday.__main__.DesktopClient"
    ), patch("friday.__main__.create_llm"), patch(
        "friday.__main__._load_sandbox", return_value=_Sandbox()
    ), patch("friday.__main__.print", side_effect=captured.append):
        with pytest.raises(RuntimeError):
            __main__._run_task(_Args())

    joined = " ".join(captured)
    assert "[loop]" in joined
    assert "kept deciding" in joined
    assert "advances step" in joined