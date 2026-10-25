"""Tests for the harness composition root (build_production_graph)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from friday.harness.compose import (
    REQUIRED_REAL,
    ConfigurationError,
    ProductionDeps,
    build_production_graph,
)
from friday.harness.graph import build_graph
from friday.harness.nodes import default_nodes
from friday.harness.state import initial_state


class _FakeClient:
    def observation(self):
        from friday.desktop.observation import Observation, WindowInfo

        return Observation(
            screenshot_png=b"\x89PNG\r\n\x1a\n",
            screen_size=(1280, 720),
            windows=[WindowInfo(id="1", title="Chromium", class_name="Chromium", active=True)],
            active_window_id="1",
            active_window_class="Chromium",
            focused_app="browser",
        )


class _FakeTrace:
    def write(self, observation, error=None):  # noqa: ANN001
        return "/tmp/shot.png"


class _FakeLLM:
    def invoke(self, prompt, images):  # noqa: ANN001
        from friday.llm.base import LLMResponse

        return LLMResponse(text='{"decision": "done"}')


class _FakePolicy:
    def __init__(self) -> None:
        from friday.harness.capabilities import ControlPolicy

        self._policy = ControlPolicy(approval=True)

    def policy(self, state):  # noqa: ANN001
        return self._policy


def _deps(**overrides) -> ProductionDeps:
    deps = ProductionDeps(
        client=_FakeClient(),
        trace_writer=_FakeTrace(),
        focus_table=lambda _c: "browser",
        llm=_FakeLLM(),
        policy=_FakePolicy(),
    )
    return replace(deps, **overrides)


def _probe(name, calls, update=None):  # noqa: ANN001
    def run(state):  # noqa: ANN001
        calls.append(name)
        return update or {}

    return run


# --- REQUIRED_REAL contains today's implemented nodes ------------------------


def test_required_real_lists_the_implemented_nodes() -> None:
    assert REQUIRED_REAL == {"observe", "build_context", "decide", "guard"}


# --- ConfigurationError when a required node is a stub -----------------------


def test_full_deps_build_a_production_graph() -> None:
    graph = build_production_graph(_deps())

    assert graph is not None


def test_missing_observe_deps_raise_configuration_error() -> None:
    deps = _deps(client=None, trace_writer=None)

    with pytest.raises(ConfigurationError, match="observe"):
        build_production_graph(deps)


def test_missing_decide_deps_raise_configuration_error() -> None:
    deps = _deps(llm=None)

    with pytest.raises(ConfigurationError, match="decide"):
        build_production_graph(deps)


def test_missing_policy_raises_configuration_error_naming_a_policy_node() -> None:
    # client/trace/llm are provided so observe and decide build real; only the
    # missing policy leaves build_context and guard as stubs
    deps = _deps(policy=None)

    with pytest.raises(ConfigurationError) as exc_info:
        build_production_graph(deps)

    # the check raises on the first required policy slot that is still a stub
    assert str(exc_info.value) in (
        "build_context is still the default stub; provide the dependencies "
        "required to make it real before running live",
        "guard is still the default stub; provide the dependencies "
        "required to make it real before running live",
    )


def test_allow_stubs_true_builds_even_with_missing_deps() -> None:
    graph = build_production_graph(_deps(policy=None, llm=None), allow_stubs=True)

    assert graph is not None


# --- with fakes, the composed graph runs the expected path -------------------


def test_composed_graph_runs_observe_build_context_decide_guard() -> None:
    calls: list[str] = []
    base = default_nodes()
    nodes = replace(
        base,
        observe=_probe("observe", calls),
        build_context=_probe("build_context", calls),
        decide=_probe("decide", calls, {"decision": "action"}),
        guard=_probe("guard", calls, {"guard_verdict": "stop"}),
        finish=_probe("finish", calls),
    )
    graph = build_graph(nodes)

    graph.invoke(initial_state("goal", 5))

    assert calls == ["observe", "build_context", "decide", "guard", "finish"]


def test_unwired_guard_in_composed_graph_fails_closed() -> None:
    calls: list[str] = []

    def decide(state):  # noqa: ANN001
        calls.append("decide")
        return {"decision": "action"}

    base = default_nodes()
    nodes = replace(
        base,
        observe=_probe("observe", calls),
        build_context=_probe("build_context", calls),
        decide=decide,
        executor=_probe("executor", calls),
        finish=_probe("finish", calls),
    )
    # guard left as the default stub

    build_graph(nodes).invoke(initial_state("goal", 5))

    assert "executor" not in calls
    assert calls[-1] == "finish"


# --- composed graph with a real executor runs the guarded path ----------------

def test_guard_allow_reaches_executor_and_writes_last_result() -> None:
    from friday.harness.nodes.executor import ExecutorDeps, make_executor_node
    from friday.harness.steps import ExecutorSettings

    calls: list[str] = []
    seen_last_result: list[dict] = []

    class _CapturingDecide:
        def __init__(self) -> None:
            self.count = 0

        def __call__(self, state):  # noqa: ANN001, ANN202
            calls.append("decide")
            self.count += 1
            if self.count == 1:
                return {
                    "decision": "action",
                    "pending_action": {"action": "left_click", "x": 1, "y": 2},
                }
            seen_last_result.append(state.get("last_result") or {})
            return {"decision": "done"}

    def guard(state):  # noqa: ANN001
        calls.append("guard")
        return {"guard_verdict": "allow"}

    class _Ex:
        def execute(self, action):  # noqa: ANN001, ANN202
            calls.append("executor")
            from friday.actions.models import ActionResult

            return ActionResult(ok=True)

    class _Tr:
        def write_image(self, step_index: int, name: str, png: bytes) -> str:
            return "/tmp/i.png"

    real_exec = make_executor_node(
        ExecutorDeps(executor=_Ex(), trace_writer=_Tr(), settings=ExecutorSettings())
    )

    base = default_nodes()
    nodes = replace(
        base,
        observe=lambda s: calls.append("observe") or {},
        build_context=lambda s: calls.append("build_context") or {"prompt": "x"},
        decide=_CapturingDecide(),
        guard=guard,
        executor=real_exec,
        settle=lambda s: calls.append("settle") or {},
        verify=lambda s: calls.append("verify") or {},
        finish=_probe("finish", calls),
    )

    build_graph(nodes).invoke(initial_state("goal", 5))

    assert calls == [
        "observe",
        "build_context",
        "decide",
        "guard",
        "executor",
        "settle",
        "verify",
        "build_context",
        "decide",
        "finish",
    ]
    assert seen_last_result and seen_last_result[0].get("ok") is True


def test_guard_reject_never_touches_executor() -> None:
    from friday.harness.nodes.executor import ExecutorDeps, make_executor_node
    from friday.harness.steps import ExecutorSettings

    calls: list[str] = []

    class _Ex:
        def execute(self, action):  # noqa: ANN001, ANN202
            calls.append("executor")
            from friday.actions.models import ActionResult

            return ActionResult(ok=True)

    class _Tr:
        def write_image(self, step_index: int, name: str, png: bytes) -> str:
            return "/tmp/i.png"

    real_exec = make_executor_node(
        ExecutorDeps(executor=_Ex(), trace_writer=_Tr(), settings=ExecutorSettings())
    )
    # guard rejects, so executor must never run even though it is real
    guard = lambda s: calls.append("guard") or {"guard_verdict": "reject"}  # noqa: E731

    class _DecideOnceThenDone:
        def __init__(self) -> None:
            self.count = 0

        def __call__(self, state):  # noqa: ANN001, ANN202
            calls.append("decide")
            self.count += 1
            if self.count == 1:
                return {
                    "decision": "action",
                    "pending_action": {"action": "left_click", "x": 1, "y": 2},
                }
            return {"decision": "done"}

    base = default_nodes()
    nodes = replace(
        base,
        observe=lambda s: calls.append("observe") or {},
        build_context=lambda s: calls.append("build_context") or {"prompt": "x"},
        decide=_DecideOnceThenDone(),
        guard=guard,
        executor=real_exec,
        settle=lambda s: calls.append("settle") or {},
        verify=lambda s: calls.append("verify") or {},
        finish=_probe("finish", calls),
    )

    build_graph(nodes).invoke(initial_state("goal", 5))

    assert "executor" not in calls


# --- full loop through the production graph terminates -----------------------


def test_production_graph_full_loop_executes_settles_verifies_terminal_state() -> None:
    """The composed production graph runs executor -> settle -> verify and terminates.

    Uses the real factories (executor via ExecutorDeps over a fake Executor,
    real settle, real verify, real finish) so the loop actually advances ``step``
    and the run reports a terminal status instead of recursing. This is the
    closed-loop proof that wiring the executor makes a live run end.
    """
    from friday.harness.nodes.executor import ExecutorDeps
    from friday.harness.steps import ExecutorSettings

    executed: list[str] = []

    class _Ex:
        def execute(self, action):  # noqa: ANN001, ANN202
            executed.append(str(action.action))
            from friday.actions.models import ActionResult

            return ActionResult(ok=True)

    class _Tr:
        def __init__(self) -> None:
            import tempfile

            self._f = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            self._f.write(b"\x89PNG\r\n\x1a\n")
            self._f.close()
            self._path = self._f.name

        def write(self, observation, error=None):
            return self._path

        def write_image(self, step_index: int, name: str, png: bytes) -> str:
            return f"{self._path}#{name}"

    class _Policy:
        def policy(self, state):  # noqa: ANN001
            from friday.harness.capabilities import ControlPolicy

            return ControlPolicy(approval=True, user_control=False)

    class _ActionThenDone:
        """A fake LLM whose text response is a valid decision payload."""

        def __init__(self) -> None:
            self.count = 0

        def invoke(self, prompt, images):  # noqa: ANN001
            from friday.llm.base import LLMResponse

            self.count += 1
            if self.count == 1:
                return LLMResponse(
                    text='{"decision": "action", "pending_action": '
                    '{"action": "left_click", "x": 1, "y": 2}}'
                )
            return LLMResponse(text='{"decision": "done"}')

    deps = ProductionDeps(
        client=_FakeClient(),
        trace_writer=_Tr(),
        focus_table=lambda _c: "browser",
        llm=_ActionThenDone(),
        policy=_Policy(),
        executor=ExecutorDeps(executor=_Ex(), trace_writer=_Tr(), settings=ExecutorSettings()),
    )
    graph = build_production_graph(deps)
    state = initial_state("open a web page", 5)
    state["retries"] = 2

    result = graph.invoke(state, config={"recursion_limit": 50})

    assert executed == ["left_click"]
    # the loop advanced step (0 -> 1) and wrote a history record passed through verify
    assert result["step"] == 1
    # screenshot paths point at the fake trace, so the diff is unreliable and
    # the outcome is honestly 'unknown' — verify still records the step
    assert result["history"][-1]["outcome"] == "unknown"
    # finish resolved the terminal status to done
    assert result["status"] == "done"


def test_production_graph_full_loop_dispatches_an_operation_and_terminates() -> None:
    """An operation proposal (open_url) must dispatch and finish, not loop.

    This is the regression test for the reported bug: ``friday run "open my
    github"`` proposed the ``open_url`` operation, the guard allowed it, but the
    executor never dispatched it, so the loop ran to the recursion limit.
    """
    from friday.operations.registry import OpenUrl

    executed: list[object] = []

    class _Ex:
        def execute(self, payload):  # noqa: ANN001, ANN202
            executed.append(payload)
            if isinstance(payload, OpenUrl):
                return {"ok": True}
            from friday.actions.models import ActionResult

            return ActionResult(ok=True)

    class _Tr:
        def __init__(self) -> None:
            import tempfile

            self._f = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            self._f.write(b"\x89PNG\r\n\x1a\n")
            self._f.close()
            self._path = self._f.name

        def write(self, observation, error=None):
            return self._path

        def write_image(self, step_index: int, name: str, png: bytes) -> str:
            return f"{self._path}#{name}"

    class _Policy:
        def policy(self, state):  # noqa: ANN001
            from friday.harness.capabilities import ControlPolicy

            return ControlPolicy(approval=True, user_control=False)

    class _OpenThenDone:
        def __init__(self) -> None:
            self.count = 0

        def invoke(self, prompt, images):  # noqa: ANN001
            from friday.llm.base import LLMResponse

            self.count += 1
            if self.count == 1:
                return LLMResponse(
                    text='{"decision": "action", "pending_action": '
                    '{"operation": "open_url", "url": "https://github.com/Dishank-Sen"}}'
                )
            return LLMResponse(text='{"decision": "done"}')

    from friday.harness.nodes.executor import ExecutorDeps
    from friday.harness.steps import ExecutorSettings

    deps = ProductionDeps(
        client=_FakeClient(),
        trace_writer=_Tr(),
        focus_table=lambda _c: "browser",
        llm=_OpenThenDone(),
        policy=_Policy(),
        executor=ExecutorDeps(executor=_Ex(), trace_writer=_Tr(), settings=ExecutorSettings()),
    )
    graph = build_production_graph(deps)
    state = initial_state("open a web page", 5)
    state["retries"] = 2

    result = graph.invoke(state, config={"recursion_limit": 50})

    assert len(executed) == 1
    assert isinstance(executed[0], OpenUrl)
    # the fake trace has no real pre/post screenshots, so the outcome is
    # honestly 'unknown'; verify still recorded the operation and ok
    assert result["history"][-1]["outcome"] == "unknown"
    assert result["history"][-1]["ok"] is True
    assert result["status"] == "done"

def test_production_graph_settle_waits_with_browser_probe() -> None:
    """When a probe is supplied and the focused app is a browser, settle waits.

    The probe is threaded through ProductionDeps into both settle and verify; a
    browser-focused run should call wait_ready once during settle.
    """
    from friday.harness.nodes.executor import ExecutorDeps
    from friday.harness.steps import ExecutorSettings

    waited: list[float] = []

    class _Probe:
        def state(self) -> dict:
            return {"tab_count": 1, "url": "https://github.com", "ready_state": "complete"}

        def wait_ready(self, timeout_s: float) -> dict:
            waited.append(timeout_s)
            return {"state": "ready", "waited_ms": 0}

    class _Ex:
        def execute(self, action):  # noqa: ANN001, ANN202
            from friday.actions.models import ActionResult

            return ActionResult(ok=True)

    class _Tr:
        def __init__(self) -> None:
            import tempfile

            self._f = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            self._f.write(b"\x89PNG\r\n\x1a\n")
            self._f.close()
            self._path = self._f.name

        def write(self, observation, error=None):
            return self._path

        def write_image(self, step_index: int, name: str, png: bytes) -> str:
            return f"{self._path}#{name}"

    class _Policy:
        def policy(self, state):  # noqa: ANN001
            from friday.harness.capabilities import ControlPolicy

            return ControlPolicy(approval=True, user_control=False)

    class _ActionThenDone:
        def __init__(self) -> None:
            self.count = 0

        def invoke(self, prompt, images):  # noqa: ANN001
            from friday.llm.base import LLMResponse

            self.count += 1
            if self.count == 1:
                return LLMResponse(
                    text='{"decision": "action", "pending_action": '
                    '{"action": "left_click", "x": 1, "y": 2}}'
                )
            return LLMResponse(text='{"decision": "done"}')

    deps = ProductionDeps(
        client=_FakeClient(),
        trace_writer=_Tr(),
        focus_table=lambda _c: "browser",
        llm=_ActionThenDone(),
        policy=_Policy(),
        executor=ExecutorDeps(executor=_Ex(), trace_writer=_Tr(), settings=ExecutorSettings()),
        browser_probe=_Probe(),
    )
    graph = build_production_graph(deps)
    state = initial_state("open a web page", 5)
    state["retries"] = 2
    state["focused_app"] = "browser"

    result = graph.invoke(state, config={"recursion_limit": 50})

    assert waited, "settle should have called probe.wait_ready for a browser"
    assert result["history"][-1].get("browser")  # verify also recorded browser facts
