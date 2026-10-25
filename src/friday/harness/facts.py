"""Fact collection and summarization for the build_context node.

This layer turns the raw ``AgentState`` snapshot into a compact, bounded,
model-ready representation of desktop facts and action history. It performs no
desktop automation, HTTP, LLM, file, or Docker operations: it only reads the
already-collected state and normalizes it.

Design rules (see docs/harness.md):
- Prefer facts already in state over duplicate system queries.
- Bound histories, results, and error text so a prompt stays bounded.
- Label an action's outcome honestly: an operation that was merely proposed is
  *unverified*, never "succeeded".
- Missing desktop metadata stays missing; it is not fabricated into a fact.
- Capability *selection* (capabilities.py) and prompt *rendering* (the future
  renderer) are separate layers; this module does neither.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from friday.harness.capabilities import ControlPolicy
from friday.harness.state import AgentState

Outcome = Literal["succeeded", "failed", "rejected", "unverified", "none"]

_DEFAULT = 10
_LONG = 400
_ELLIPSIS = "…"


@dataclass(frozen=True, slots=True)
class FactLimits:
    """Bounds applied while normalizing facts, so a prompt stays bounded."""

    max_history: int = _DEFAULT
    max_string: int = _LONG
    max_windows: int = 20


@dataclass(frozen=True, slots=True)
class NormalizedFacts:
    """The bounded, model-facing facts for one decision step.

    Mirror of ``PromptFacts`` plus an explicit ``outcome`` label and the
    approval / user-control status for the step. ``screen_size`` is carried for
    the decide node's coordinate checks but must never be rendered into a prompt.
    """

    goal: str | None
    screenshot: str | None
    screen_size: tuple[int, int] | None
    focused_app: str | None
    windows: tuple[dict, ...]
    history: tuple[dict, ...]
    last_result: dict | None
    outcome: Outcome
    hint: str | None
    step: int
    max_steps: int
    steps_remaining: int
    retries: int
    approval: bool
    user_control: bool


def _bound_value(value: object, limit: int) -> object:
    """Return a bounded, safe copy of a scalar, list, or shallow dict.

    String values over ``limit`` are truncated; lists are capped to ``limit``
    items and their string items bounded; dicts are normalized shallowly one
    level deep (dict values are bounded only if they are strings or lists).
    Anything else (bools, ints, None) passes through untouched.
    """
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + _ELLIPSIS
    if isinstance(value, list):
        bounded = [_bound_string_item(item, limit) for item in value[:limit]]
        return bounded
    if isinstance(value, dict):
        return _bound_dict(value, limit)
    return value


def _bound_string_item(item: object, limit: int) -> object:
    if isinstance(item, str):
        return item if len(item) <= limit else item[:limit] + _ELLIPSIS
    return item


def _bound_dict(value: dict, limit: int) -> dict:
    """Normalize one shallow dict: bound its direct string/list values."""
    bounded: dict = {}
    for key, item in value.items():
        if isinstance(item, str):
            bounded[key] = item if len(item) <= limit else item[:limit] + _ELLIPSIS
        elif isinstance(item, list):
            bounded[key] = [_bound_string_item(entry, limit) for entry in item[:limit]]
        else:
            bounded[key] = item
    return bounded


def _window(w: dict, limit: int) -> dict:
    """Keep a window entry compact: id, title (bounded), and active state."""
    window_id = w.get("id")
    title = w.get("title")
    active = w.get("active")
    return {
        "id": window_id if isinstance(window_id, str) else None,
        "title": _bound_value(title, limit) if isinstance(title, str) else None,
        "active": active if isinstance(active, bool) else None,
    }


def _history_entry(entry: dict, limit: int) -> dict:
    """Normalize one history entry: keep decision + a bounded action summary."""
    action = entry.get("action")
    return {
        "decision": entry.get("decision"),
        "outcome": entry.get("outcome"),
        "action": _bound_value(action, limit) if action is not None else None,
    }


def _last_result(result: dict, limit: int) -> dict | None:
    """Bound a last_result without ever dropping its success indicator."""
    bounded = _bound_dict(result, limit)
    bounded["ok"] = bool(result.get("ok"))
    return bounded


def _outcome(state: AgentState) -> Outcome:
    """Label the most recent attempt honestly.

    An executed operation is ``succeeded`` only when its result says so; an
    expected failure is ``failed``; a rejected action is ``rejected``; a
    proposed-but-unexecuted action is ``unverified`` (never claimed to have
    succeeded); with no attempt yet the label is ``none``.
    """
    # A guard rejection concerns the current proposal and must win even when a
    # stale last_result from an earlier step lingers.
    if state.get("guard_verdict") == "reject":
        return "rejected"
    result = state.get("last_result")
    if result is not None:
        return "succeeded" if result.get("ok") else "failed"
    if state.get("pending_action") is not None:
        return "unverified"
    return "none"


def summarize_facts(
    state: AgentState,
    *,
    limits: FactLimits | None = None,
    policy: ControlPolicy | None = None,
) -> NormalizedFacts:
    """Normalize and bound a state snapshot into model-ready facts.

    No side effects: this reads state only. ``limits`` bounds histories, results,
    error text, and windows. ``policy`` supplies approval / user-control status
    for the step; when omitted, approval is not assumed granted (an honest
    default, since nothing in state records it).
    """
    limits = limits or FactLimits()
    policy = policy or ControlPolicy(approval=False, user_control=False)

    raw_windows = state.get("windows") or []
    windows = tuple(_window(w, limits.max_string) for w in raw_windows[: limits.max_windows])

    raw_history = state.get("history") or []
    history = tuple(
        _history_entry(entry, limits.max_string) for entry in raw_history[-limits.max_history :]
    )

    raw_result = state.get("last_result")
    last_result = _last_result(raw_result, limits.max_string) if raw_result else None

    goal = state.get("goal")
    hint = state.get("hint")

    step = state.get("step", 0)
    max_steps = state.get("max_steps", 0)

    return NormalizedFacts(
        goal=_bound_value(goal, limits.max_string) if isinstance(goal, str) else goal,
        screenshot=state.get("screenshot_path"),
        screen_size=state.get("screen_size"),
        focused_app=state.get("focused_app"),
        windows=windows,
        history=history,
        last_result=last_result,
        outcome=_outcome(state),
        hint=_bound_value(hint, limits.max_string) if isinstance(hint, str) else hint,
        step=step,
        max_steps=max_steps,
        steps_remaining=max(0, max_steps - step),
        retries=state.get("retries", 0),
        approval=policy.approval,
        user_control=policy.user_control,
    )