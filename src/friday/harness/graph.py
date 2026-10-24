"""Topology for Friday's future agent decision loop."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from .config import DEFAULT_RECURSION_LIMIT
from .nodes import Nodes, default_nodes
from .routes import route_after_decide, route_after_guard
from .state import AgentState


def build_graph(nodes: Nodes | None = None, checkpointer: Any = None) -> Any:
    """Compile a reusable harness graph with injectable node implementations."""
    selected = nodes or default_nodes()
    graph = StateGraph(AgentState)
    graph.add_node("observe", selected.observe)
    graph.add_node("decide", selected.decide)
    graph.add_node("guard", selected.guard)
    graph.add_node("executor", selected.executor)
    graph.add_node("settle", selected.settle)
    graph.add_node("verify", selected.verify)
    graph.add_node("build_context", selected.build_context)
    graph.add_node("finish", selected.finish)
    graph.add_edge(START, "observe")
    graph.add_edge("observe", "build_context")
    graph.add_conditional_edges(
        "decide",
        route_after_decide,
        {"guard": "guard", "finish": "finish", "build_context": "build_context"},
    )
    graph.add_conditional_edges(
        "guard",
        route_after_guard,
        {"executor": "executor", "finish": "finish", "build_context": "build_context"},
    )
    graph.add_edge("executor", "settle")
    graph.add_edge("settle", "verify")
    graph.add_edge("verify", "build_context")
    graph.add_edge("build_context", "decide")
    graph.add_edge("finish", END)
    return graph.compile(checkpointer=checkpointer).with_config(
        {"recursion_limit": DEFAULT_RECURSION_LIMIT}
    )
