"""Pure routing functions for the agent harness."""

from __future__ import annotations

import logging

from .state import AgentState

LOGGER = logging.getLogger(__name__)

_AFTER_DECIDE = {"action": "guard", "done": "finish", "fail": "finish", "retry": "build_context"}
_AFTER_GUARD = {"allow": "executor", "reject": "build_context", "stop": "finish"}


def route_after_decide(state: AgentState) -> str:
    """Route from decide using its declared decision only."""
    return _route(state["decision"], _AFTER_DECIDE, "decision")


def route_after_guard(state: AgentState) -> str:
    """Route from guard using its declared verdict only."""
    return _route(state["guard_verdict"], _AFTER_GUARD, "guard_verdict")


def _route(value: str | None, routes: dict[str, str], field: str) -> str:
    if value is None:
        LOGGER.warning("harness route missing %s; finishing", field)
        return "finish"
    try:
        return routes[value]
    except KeyError as error:
        raise ValueError(f"unknown {field}: {value}") from error
