"""Finish node: set the terminal status and final report for a run."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def finish(state: AgentState) -> dict:
    """Set terminal status and write the final report; this stub performs neither."""
    LOGGER.info("harness finish stub ran")
    return {}


def make_finish() -> object:
    """Create a finish node that resolves the run's terminal status/report.

    A run reaches finish either already failed (observe capture or verify stuck),
    stopped by the guard, done (the model said so), or failed (the model said so).
    The node reads the terminal markers and writes a coherent ``status`` and
    ``final_report`` so the runner can report how the loop ended. It is pure and
    needs no injected dependencies.
    """

    def run(state: AgentState) -> dict:
        status = state.get("status")
        final = state.get("final_report")
        decision = state.get("decision")
        verdict = state.get("guard_verdict")

        update: dict = {}
        if status == "failed":
            update["status"] = "failed"
            update["final_report"] = final or "task failed"
        elif verdict == "stop":
            update["status"] = "stopped"
            update["final_report"] = final or state.get("hint") or "stopped"
        elif decision == "done":
            update["status"] = "done"
            update["final_report"] = final or "task complete"
        elif decision == "fail":
            update["status"] = "failed"
            update["final_report"] = final or state.get("hint") or "task failed"
        else:
            update["status"] = "stopped"
            update["final_report"] = final or "no decision reached"
        return update

    return run