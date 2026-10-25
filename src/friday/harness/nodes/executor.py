"""Executor node: run the guard-allowed action and record the outcome.

This node is the execution boundary in the graph. It reads the action the guard
allowed, validates it, runs it exactly once through the injected ``Executor``
(via ``run_steps``, the single execution path), saves any observation image
through the trace writer, and records the result in ``last_result``. It never
waits for the screen, retries, judges success, or takes a screenshot of its own;
``settle`` and ``verify`` own those.

Defensive checks are fail-closed: anything that is not a guard-allowed, valid
action records a failed ``last_result`` and the executor is never called.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from friday.actions.models import parse_action
from friday.harness.state import AgentState
from friday.harness.steps import ExecutorSettings, StepSpec, run_steps

LOGGER = logging.getLogger(__name__)


def executor(state: AgentState) -> dict:
    """Run pending action and record expected failures in last_result; this stub is a no-op."""
    LOGGER.info("harness executor stub ran")
    return {}


@dataclass(frozen=True, slots=True)
class ExecutorDeps:
    """Injected dependencies for the executor node."""

    executor: object
    trace_writer: object
    settings: ExecutorSettings = ExecutorSettings()
    clock: Callable[[], float] | None = None


def make_executor_node(deps: ExecutorDeps) -> Callable[[AgentState], dict]:
    """Create an executor node with injectable dependencies.

    ``deps.executor`` is the ``Executor`` protocol (or a fake); ``deps.trace_writer``
    saves observation images; ``deps.settings`` bounds one call (batching off by
    default); ``deps.clock`` is an injectable monotonic clock for durations.
    Returns a partial state update writing only ``last_result``.
    """

    def run(state: AgentState) -> dict:
        result = _execute_once(state, deps)
        return {"last_result": result}

    return run


def _execute_once(state: AgentState, deps: ExecutorDeps) -> dict:
    if state.get("guard_verdict") != "allow":
        return _defensive("not_allowed", "guard did not allow this action")

    pending = state.get("pending_action")
    if not isinstance(pending, dict) or pending.get("action") is None:
        return _defensive("internal_error", "no action to execute")

    try:
        action = parse_action(dict(pending))
    except (ValueError, TypeError):
        return _defensive("invalid_action", "pending action failed validation")

    step = StepSpec(action=action, expected_result=pending.get("expected_result"))
    outcomes = run_steps(deps.executor, [step], settings=deps.settings, clock=deps.clock)
    outcome = outcomes[-1]

    record = outcome.model_dump(mode="json")
    return _finalize(record, outcome, deps)


def _finalize(record: dict, outcome, deps: ExecutorDeps) -> dict:
    if outcome.image_png:
        try:
            record["image_path"] = deps.trace_writer.write_image(
                step_index=0, name=str(outcome.operation), png=outcome.image_png
            )
        except OSError as error:
            LOGGER.warning("could not save observation image: %s", error)
    record.pop("image_png", None)
    return record


def _defensive(error_type: str, message: str) -> dict:
    return {
        "ok": False,
        "operation": "",
        "error": {"type": error_type, "message": message},
        "duration_ms": 0,
    }