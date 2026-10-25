"""Composition root for a live harness graph.

A live run must never silently run with an unwired stub in a required slot.
This module is the one place that assembles the ``Nodes`` the runner actually
uses: it replaces the default stubs with the real factories for the nodes that
exist today, and — unless ``allow_stubs`` is passed — refuses to build a graph
where a required node is still the default no-op stub. The stub files themselves
need no changes: a stub is detected by object identity with the matching entry
of ``default_nodes()``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Protocol

from friday.harness.facts import FactLimits
from friday.harness.graph import build_graph
from friday.harness.nodes import Node, default_nodes
from friday.harness.nodes.build_context import make_build_context
from friday.harness.nodes.decide import make_decide
from friday.harness.nodes.executor import ExecutorDeps, make_executor_node
from friday.harness.nodes.guard import make_guard
from friday.harness.nodes.observe import make_observe
from friday.llm.base import VisionLLM

# Nodes that must be real (not the default stub) for a live run. When a node
# becomes implemented, add its name here: a one-line change. Keeping this as the
# single source lets ``build_production_graph`` fail closed on any unwired slot.
REQUIRED_REAL: frozenset[str] = frozenset({"observe", "build_context", "decide", "guard"})

# Pairs that must be real *together*: if the first member is real, the second
# must be real too, else the produced graph is unsound. Adding a pair is one
# line. ``allow_stubs`` bypasses both checks.
REQUIRED_TOGETHER: frozenset[tuple[str, str]] = frozenset(
    {("executor", "settle"), ("executor", "verify")}
)


class ConfigurationError(ValueError):
    """A live graph cannot be assembled as requested."""


class PolicyProvider(Protocol):
    """Resolves the current approval / user-control status for one step."""

    def policy(self, state): ...  # noqa: ANN001


@dataclass(frozen=True, slots=True)
class ProductionDeps:
    """Injected dependencies for the real harness factories.

    A node is built from its factory only when the dependencies it needs are
    present; otherwise that slot stays the default stub, which the
    ``REQUIRED_REAL`` check then rejects (unless ``allow_stubs``).
    """

    client: object | None = None
    trace_writer: object | None = None
    focus_table: Callable[[str | None], str] | None = None
    llm: VisionLLM | None = None
    policy: PolicyProvider | None = None
    limits: FactLimits | None = None
    executor: ExecutorDeps | None = None
    settle: Node | None = None
    verify: Node | None = None


def build_production_graph(
    deps: ProductionDeps,
    *,
    checkpointer: object | None = None,
    allow_stubs: bool = False,
) -> object:
    """Assemble the live graph from the real factories and required deps.

    A required node is promoted real only when the dependencies it needs are
    present; otherwise its slot stays the default stub. ``observe`` needs
    ``client`` and ``trace_writer``; ``decide`` needs ``llm``; ``build_context``
    and ``guard`` need ``policy`` (they must share one policy source so
    selection and enforcement agree). Any required node left as a stub — with
    ``allow_stubs=False`` (the default) — raises ``ConfigurationError`` naming
    it, so a live run cannot be assembled with an unwired required slot.
    """
    base = default_nodes()

    real: dict[str, Node] = {}
    if deps.client is not None and deps.trace_writer is not None:
        focus = deps.focus_table or (lambda _class: "other")
        real["observe"] = make_observe(deps.client, deps.trace_writer, focus)
    if deps.llm is not None:
        real["decide"] = make_decide(llm=deps.llm)
    if deps.policy is not None:
        real["build_context"] = make_build_context(policy=deps.policy, limits=deps.limits)
        real["guard"] = make_guard(policy=deps.policy)
    if deps.executor is not None:
        real["executor"] = make_executor_node(deps.executor)
    if deps.settle is not None:
        real["settle"] = deps.settle
    if deps.verify is not None:
        real["verify"] = deps.verify

    nodes = replace(base, **real)

    if not allow_stubs:
        for name in REQUIRED_REAL:
            if getattr(nodes, name) is getattr(base, name):
                raise ConfigurationError(
                    f"{name} is still the default stub; provide the dependencies "
                    f"required to make it real before running live"
                )
        for first, second in REQUIRED_TOGETHER:
            first_real = getattr(nodes, first) is not getattr(base, first)
            second_is_stub = getattr(nodes, second) is getattr(base, second)
            if first_real and second_is_stub:
                raise ConfigurationError(
                    f"a real {first} requires a real {second}; a {first} with a "
                    f"stub {second} would act on stale state"
                )
    return build_graph(nodes, checkpointer=checkpointer)