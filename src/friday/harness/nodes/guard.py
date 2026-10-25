"""Guard node: independently enforces authoritative policy on the proposed action.

The guard is the enforcement boundary for a decision step. It reads the proposed
action/operation the decide node produced, validates it *independently* against
the authoritative registries and schema, checks budgets, repeats, approval, and
user-control / cancellation, and returns a verdict. It never relies on the
capability manifest: the model may invent names or be exposed extra capabilities,
but this node decides from the authoritative registries only.

A context-construction error leaves no pending action, so the guard cannot allow
anything: absent a proposal it rejects rather than executing.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any, Protocol

from friday.actions.models import ShortcutAction, parse_action
from friday.harness.capabilities import ControlPolicy, requires_approval
from friday.harness.config import (
    APPROVAL_REQUIRED_CATEGORIES,
    DEFAULT_MAX_SECONDS,
    DEFAULT_MAX_STUCK,
    WORKSPACE_ROOT,
)
from friday.harness.state import AgentState
from friday.operations.registry import parse_operation
from friday.shortcuts.registry import ShortcutNotAvailable, resolve_shortcut

LOGGER = logging.getLogger(__name__)


class PolicyProvider(Protocol):
    """Resolves the current approval / user-control status for one step."""

    def policy(self, state: AgentState) -> ControlPolicy: ...


class GuardConfig(Protocol):
    workspace_root: str
    approval_required_categories: frozenset[str]
    max_seconds: float | None
    max_stuck: int


class _GuardConfig:
    def __init__(
        self,
        workspace_root: str,
        approval_required_categories: frozenset[str],
        max_seconds: float | None = DEFAULT_MAX_SECONDS,
        max_stuck: int = DEFAULT_MAX_STUCK,
    ) -> None:
        self.workspace_root = workspace_root
        self.approval_required_categories = approval_required_categories
        self.max_seconds = max_seconds
        self.max_stuck = max_stuck


def _default_config() -> GuardConfig:
    return _GuardConfig(WORKSPACE_ROOT, APPROVAL_REQUIRED_CATEGORIES)


def guard(state: AgentState) -> dict:
    """Safe default with no dependencies; injected guards perform the real check."""
    LOGGER.info("harness guard stub ran")
    return {}


def make_guard(
    *,
    parse: Callable[[dict], Any] | None = None,
    policy: PolicyProvider | None = None,
    config: GuardConfig | None = None,
    clock: Callable[[], float] | None = None,
) -> Callable[[AgentState], dict]:
    """Create a guard node with injectable dependencies.

    ``parse`` independently validates a proposed action against the authoritative
    registries (operation or input action). ``policy`` supplies approval /
    user-control status for this step; it should be wired to the same source as
    the build_context node so manual control blocks input here independently of
    what the model was offered. ``config`` supplies the workspace root, the
    approval-required categories, and the optional wall-clock time budget
    (``max_seconds``). ``clock`` is the injected wall clock; use ``time.time``
    rather than a monotonic clock so the budget survives checkpointing a long run
    to another process.

    Returns a partial state update with ``guard_verdict`` and, when not allowed,
    a recovery ``hint``. Any failure to validate the proposal is a rejection.
    """
    do_parse = parse or _authoritative_parse
    step_policy = policy.policy if policy is not None else _default_policy()
    cfg = config or _default_config()
    now = clock or time.time

    def run(state: AgentState) -> dict:
        LOGGER.info("harness guard ran")
        pending = state.get("pending_action")

        # No proposal, or an unclear one, never authorizes execution.
        if pending is None or not isinstance(pending, dict):
            return {"guard_verdict": "reject", "hint": "no pending action to validate"}

        # Stopped / failed tasks cannot act further (the kill switch uses the
        # existing ``stopped`` status; there is no ``cancelled`` status).
        if state.get("status") in {"stopped", "failed"}:
            return {"guard_verdict": "stop", "hint": "task is no longer running"}
        control = step_policy(state)
        if control.user_control:
            return {"guard_verdict": "reject", "hint": "user currently controls the desktop"}

        # Budgets.
        if state.get("step", 0) >= state.get("max_steps", 0):
            return {"guard_verdict": "stop", "hint": "step budget exhausted"}
        if (state.get("stuck_count") or 0) >= cfg.max_stuck:
            return {"guard_verdict": "stop", "hint": "stuck: screen did not change"}
        if state.get("retries", 0) <= 0:
            return {"guard_verdict": "reject", "hint": "retry budget exhausted"}
        if cfg.max_seconds is not None:
            started = state.get("started_at", 0.0)
            if started > 0 and now() - started >= cfg.max_seconds:
                return {"guard_verdict": "stop", "hint": "time budget exhausted"}
            if started <= 0:
                LOGGER.warning("harness guard time budget configured but started_at is unset")

        # Independent schema/registry validation of the proposed action.
        try:
            parsed = do_parse(dict(pending))
        except (ValueError, TypeError) as error:
            return {"guard_verdict": "reject", "hint": f"invalid action: {error}"}

        # Coordinate bounds, when screen dimensions are known.
        screen = state.get("screen_size")
        if screen is not None:
            reason = _coordinate_rejection(parsed, screen)
            if reason:
                return {"guard_verdict": "reject", "hint": reason}

        # A shortcut must be resolvable for the currently focused app. The same
        # ``resolve_shortcut`` resolver is used by capability selection and the
        # executor's fresh-focus read, so selection, enforcement, and execution
        # all share one availability rule. focus ``None`` means "other".
        if isinstance(parsed, ShortcutAction):
            reason = _shortcut_rejection(parsed, state.get("focused_app"))
            if reason:
                return {"guard_verdict": "reject", "hint": reason}

        # Do not repeat a recently failed/rejected action without a recovery reason.
        reason = _repeat_rejection(state, parsed)
        if reason:
            return {"guard_verdict": "reject", "hint": reason}

        # Approval for destructive/sensitive categories.
        name = _proposed_name(parsed)
        if name is not None and requires_approval(name, cfg.approval_required_categories):
            if not control.approval:
                return {"guard_verdict": "reject", "hint": f"approval required for {name}"}

        return {"guard_verdict": "allow", "hint": "action allowed"}

    return run


def _default_policy() -> Callable[[AgentState], ControlPolicy]:
    def policy(state: AgentState) -> ControlPolicy:
        return ControlPolicy(approval=False, user_control=False)

    return policy


def _authoritative_parse(payload: dict) -> Any:
    """Validate a proposal against the authoritative registries only.

    The capability manifest is never consulted. An operation carries an
    ``operation`` discriminator; an input action (including shortcuts, which are
    a typed action) carries ``action``.
    """
    if "operation" in payload:
        return parse_operation(payload, WORKSPACE_ROOT)
    if "action" in payload:
        return parse_action(payload)
    raise ValueError("unknown action kind")


def _proposed_name(parsed: Any) -> str | None:
    op = getattr(parsed, "operation", None)
    if op is not None:
        return str(op)
    act = getattr(parsed, "action", None)
    if act is not None:
        return str(act)
    return None


def _shortcut_rejection(parsed: ShortcutAction, focused_app: str | None) -> str | None:
    """Reject a shortcut that has no binding for the focused application.

    ``resolve_shortcut`` raises ``ShortcutNotAvailable`` when the focused app
    has no binding (an unknown focus is treated as ``"other"``), which also
    covers keyboard-capturing and unnecessary-focus cases. This is the same
    resolver the executor's fresh-focus read uses, keeping enforcement and
    execution on one availability rule.
    """
    try:
        resolve_shortcut(parsed.name, focused_app or "other")
    except ShortcutNotAvailable as error:
        return f"shortcut not available for focus: {error}"
    except ValueError as error:
        return f"unknown shortcut: {error}"
    return None


def _coordinate_rejection(parsed: Any, screen: tuple[int, int]) -> str | None:
    width, height = screen
    for x, y in _coordinates(parsed):
        if x < 0 or y < 0 or x >= width or y >= height:
            return f"coordinates ({x}, {y}) out of bounds for screen {width}x{height}"
    return None


def _coordinates(parsed: Any):
    x = getattr(parsed, "x", None)
    y = getattr(parsed, "y", None)
    if x is not None and y is not None:
        yield x, y
    for prefix in ("start", "end"):
        sx = getattr(parsed, f"{prefix}_x", None)
        sy = getattr(parsed, f"{prefix}_y", None)
        if sx is not None and sy is not None:
            yield sx, sy


def _repeat_rejection(state: AgentState, parsed: Any) -> str | None:
    proposed = _proposed_name(parsed)
    if proposed is None:
        return None
    history = state.get("history") or []
    for entry in history[-8:]:
        if not isinstance(entry, dict):
            continue
        action = entry.get("action")
        prior_op = action.get("operation") if isinstance(action, dict) else action
        if prior_op != proposed:
            continue
        if entry.get("outcome") in {"failed", "rejected"}:
            if state.get("hint"):
                continue
            return (
                f"refusing to repeat a recently {entry.get('outcome')} action "
                f"({proposed}) without a recovery reason"
            )
    return None