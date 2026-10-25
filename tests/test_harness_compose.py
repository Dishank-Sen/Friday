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