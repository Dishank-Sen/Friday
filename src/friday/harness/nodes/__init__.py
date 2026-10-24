"""Injectable node collection for the harness graph."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from friday.harness.state import AgentState

from .build_context import build_context
from .decide import decide
from .executor import executor
from .finish import finish
from .guard import guard
from .observe import observe
from .settle import settle
from .verify import verify

Node = Callable[[AgentState], dict]


@dataclass(frozen=True, slots=True)
class Nodes:
    observe: Node
    decide: Node
    guard: Node
    executor: Node
    settle: Node
    verify: Node
    build_context: Node
    finish: Node


def default_nodes() -> Nodes:
    """Return the no-I/O default node stubs."""
    return Nodes(observe, decide, guard, executor, settle, verify, build_context, finish)
