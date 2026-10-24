"""Serializable state for the agent harness."""

from __future__ import annotations

from typing import Literal, TypedDict


class AgentState(TypedDict):
    goal: str
    status: Literal["running", "done", "failed", "stopped"]
    step: int
    max_steps: int
    started_at: float
    screenshot_path: str | None
    prev_screenshot_path: str | None
    decision: Literal["action", "done", "fail", "retry"] | None
    pending_action: dict | None
    guard_verdict: Literal["allow", "reject", "stop"] | None
    last_result: dict | None
    history: list[dict]
    hint: str | None
    retries: int
    stuck_count: int
    final_report: str | None


def initial_state(goal: str, max_steps: int) -> AgentState:
    """Create the neutral initial state for one harness run."""
    return {
        "goal": goal,
        "status": "running",
        "step": 0,
        "max_steps": max_steps,
        "started_at": 0.0,
        "screenshot_path": None,
        "prev_screenshot_path": None,
        "decision": None,
        "pending_action": None,
        "guard_verdict": None,
        "last_result": None,
        "history": [],
        "hint": None,
        "retries": 0,
        "stuck_count": 0,
        "final_report": None,
    }
