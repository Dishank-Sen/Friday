"""Verify node: reconcile the last result and advance the loop.

This is the designated owner of the loop's progression fields that nothing
else writes today: it advances ``step``, appends a decision+outcome record to
``history``, and tracks ``stuck_count`` (how many consecutive actions failed).
Advancing ``step`` is what lets the guard's step budget fire, so a real
``verify`` is what makes a live loop terminate instead of recursing.
"""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)

# Input actions whose payload carries user-supplied text. Their carried values
# are never written into history so typed text and clipboard contents cannot
# leak into a later prompt or log.
_SENSITIVE_OPERATIONS: frozenset[str] = frozenset({"type", "key", "hold_key"})


def verify(state: AgentState) -> dict:
    """Compare pre/post screenshots; this wired pass-through stub performs no comparison."""
    LOGGER.info("harness verify stub ran")
    return {}


def _sanitize_action(pending: dict) -> dict:
    """Return the action without any sensitive carried value.

    For a ``type``/``key``/``hold_key`` action only the action-kind marker is
    kept, so the recorded history entry carries the shape of what happened, not
    the text that was typed. Other actions pass through unchanged.
    """
    name = pending.get("action")
    if name in _SENSITIVE_OPERATIONS:
        return {"action": name}
    return dict(pending)


def make_verify(*, stuck_limit: int = 3) -> object:
    """Create a verify node that reconciles the last result and advances the loop.

    ``stuck_limit`` is how many consecutive failures mark the run failed
    (default 3). The node writes only its contract fields: ``step`` (always a
    production step, bumped exactly once per call), ``history`` (an immutable
    append of the just-completed decision), and ``stuck_count`` / ``status`` /
    ``final_report`` when the failure budget trips.
    """

    def run(state: AgentState) -> dict:
        LOGGER.info("harness verify ran")
        step = state.get("step", 0)
        decision = state.get("decision")
        pending = state.get("pending_action")

        outcome = "failed"
        if decision == "action" and pending:
            last = state.get("last_result") or {}
            outcome = "succeeded" if last.get("ok") else "failed"

        entry: dict = {"decision": decision, "outcome": outcome}
        if decision == "action" and pending:
            entry["action"] = _sanitize_action(pending)

        history = list(state.get("history") or [])
        history.append(entry)

        update: dict = {"step": step + 1, "history": history}

        if outcome == "failed":
            stuck = (state.get("stuck_count") or 0) + 1
            update["stuck_count"] = stuck
            if stuck >= stuck_limit:
                update["status"] = "failed"
                update["final_report"] = f"stuck after {stuck} failed actions"
        else:
            update["stuck_count"] = 0

        return update

    return run