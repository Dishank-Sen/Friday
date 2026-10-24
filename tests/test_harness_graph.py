from __future__ import annotations

from dataclasses import replace

import pytest
from langgraph.errors import GraphRecursionError

from friday.harness.graph import build_graph
from friday.harness.nodes import Node, Nodes, default_nodes
from friday.harness.state import AgentState, initial_state


def _node(name: str, calls: list[str], update: dict | None = None) -> Node:
    def run(state: AgentState) -> dict:
        calls.append(name)
        return update or {}

    return run


def _nodes(calls: list[str], decide: Node, guard: Node | None = None) -> Nodes:
    return Nodes(
        observe=_node("observe", calls),
        decide=decide,
        guard=guard or _node("guard", calls),
        executor=_node("executor", calls),
        settle=_node("settle", calls),
        verify=_node("verify", calls),
        build_context=_node("build_context", calls),
        finish=_node("finish", calls),
    )


def test_default_stubs_finish_when_decision_is_missing() -> None:
    result = build_graph().invoke(initial_state("goal", 1))

    assert result["decision"] is None


@pytest.mark.parametrize("decision", ["done", "fail"])
def test_terminal_decisions_go_directly_to_finish(decision: str) -> None:
    calls: list[str] = []
    graph = build_graph(_nodes(calls, _node("decide", calls, {"decision": decision})))

    graph.invoke(initial_state("goal", 1))

    assert calls == ["observe", "decide", "finish"]


def test_allowed_action_runs_full_cycle_then_decides_again() -> None:
    calls: list[str] = []
    decisions = iter(["action", "done"])

    def decide(state: AgentState) -> dict:
        calls.append("decide")
        return {"decision": next(decisions)}

    graph = build_graph(_nodes(calls, decide, _node("guard", calls, {"guard_verdict": "allow"})))

    graph.invoke(initial_state("goal", 1))

    assert calls == [
        "observe",
        "decide",
        "guard",
        "executor",
        "settle",
        "verify",
        "build_context",
        "decide",
        "finish",
    ]


def test_rejected_guard_rebuilds_context_then_decides() -> None:
    calls: list[str] = []
    decisions = iter(["action", "done"])

    def decide(state: AgentState) -> dict:
        calls.append("decide")
        return {"decision": next(decisions)}

    graph = build_graph(_nodes(calls, decide, _node("guard", calls, {"guard_verdict": "reject"})))

    graph.invoke(initial_state("goal", 1))

    assert calls == ["observe", "decide", "guard", "build_context", "decide", "finish"]


def test_stopped_guard_finishes() -> None:
    calls: list[str] = []
    graph = build_graph(
        _nodes(
            calls,
            _node("decide", calls, {"decision": "action"}),
            _node("guard", calls, {"guard_verdict": "stop"}),
        )
    )

    graph.invoke(initial_state("goal", 1))

    assert calls == ["observe", "decide", "guard", "finish"]


def test_retry_rebuilds_context_then_decides() -> None:
    calls: list[str] = []
    decisions = iter(["retry", "done"])

    def decide(state: AgentState) -> dict:
        calls.append("decide")
        return {"decision": next(decisions)}

    build_graph(_nodes(calls, decide)).invoke(initial_state("goal", 1))

    assert calls == ["observe", "decide", "build_context", "decide", "finish"]


@pytest.mark.parametrize(("field", "value"), [("decision", "bad"), ("guard_verdict", "bad")])
def test_unknown_route_values_raise(field: str, value: str) -> None:
    calls: list[str] = []
    update = {field: value}
    nodes = _nodes(calls, _node("decide", calls, update))
    if field == "guard_verdict":
        nodes = _nodes(
            calls,
            _node("decide", calls, {"decision": "action"}),
            _node("guard", calls, update),
        )

    with pytest.raises(ValueError, match="bad"):
        build_graph(nodes).invoke(initial_state("goal", 1))


def test_recursion_limit_stops_never_finishing_graph() -> None:
    calls: list[str] = []
    graph = build_graph(_nodes(calls, _node("decide", calls, {"decision": "retry"})))

    with pytest.raises(GraphRecursionError):
        graph.invoke(initial_state("goal", 1), {"recursion_limit": 4})


def test_topology_matches_expected_nodes_and_edges() -> None:
    graph = build_graph().get_graph()
    names = set(graph.nodes)
    edges = {(edge.source, edge.target) for edge in graph.edges}

    assert names == {
        "__start__",
        "__end__",
        "observe",
        "decide",
        "guard",
        "executor",
        "settle",
        "verify",
        "build_context",
        "finish",
    }
    assert edges == {
        ("__start__", "observe"),
        ("observe", "decide"),
        ("decide", "guard"),
        ("decide", "finish"),
        ("decide", "build_context"),
        ("guard", "executor"),
        ("guard", "finish"),
        ("guard", "build_context"),
        ("executor", "settle"),
        ("settle", "verify"),
        ("verify", "build_context"),
        ("build_context", "decide"),
        ("finish", "__end__"),
    }


def test_replacing_one_node_keeps_default_nodes() -> None:
    calls: list[str] = []
    replacement = _node("replacement_decide", calls)
    nodes = replace(default_nodes(), decide=replacement)

    build_graph(nodes).invoke(initial_state("goal", 1))

    assert calls == ["replacement_decide"]
