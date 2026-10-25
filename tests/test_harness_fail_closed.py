"""Fail-closed proof: an unwired (stub) guard cannot allow executor to run.

The guard is the enforcement boundary: if it is still the default no-op stub it
never writes ``guard_verdict`` (stays ``None``), so a decision to act must not
reach the executor. The router in ``routes.py`` maps a missing ``guard_verdict``
to ``finish``; these tests prove that end to end on the real compiled graph with
default stubs everywhere except a fake decide that proposes an action and fake
probe nodes we control.
"""

from __future__ import annotations

from dataclasses import replace

from friday.harness.graph import build_graph
from friday.harness.nodes import Node, Nodes, default_nodes
from friday.harness.state import AgentState, initial_state


def _probe(name: str, calls: list[str], update: dict | None = None) -> Node:
    def run(state: AgentState) -> dict:
        calls.append(name)
        return update or {}

    return run


def _nodes_with_stub_guard(calls: list[str]) -> Nodes:
    """Default stubs everywhere except a decide that proposes to act."""
    return replace(
        default_nodes(),
        observe=_probe("observe", calls),
        build_context=_probe("build_context", calls),
        decide=_probe("decide", calls, {"decision": "action"}),
        executor=_probe("executor", calls),
        settle=_probe("settle", calls),
        verify=_probe("verify", calls),
        finish=_probe("finish", calls),
        # guard is deliberately left as the default stub
    )


def test_unwired_guard_routes_action_to_finish_never_executor() -> None:
    calls: list[str] = []
    graph = build_graph(_nodes_with_stub_guard(calls))

    result = graph.invoke(initial_state("goal", 5))

    # the guard never produced a verdict: guard_verdict stayed unset
    assert result["guard_verdict"] is None
    # the action decision could not reach the executor: an unwired guard lets
    # the router drop to finish instead of executing anything
    assert "executor" not in calls
    assert "settle" not in calls
    assert "verify" not in calls
    assert calls[0] == "observe"
    assert calls[-1] == "finish"
    assert "executor" not in calls