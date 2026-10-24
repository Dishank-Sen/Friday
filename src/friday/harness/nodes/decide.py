"""Decide node stub."""

from __future__ import annotations

import logging

from friday.harness.state import AgentState

LOGGER = logging.getLogger(__name__)


def decide(state: AgentState) -> dict:
    """Read prompt/screenshot, call/validate model, and set decision/action/retry; no-op here."""
    LOGGER.info("harness decide stub ran")
    return {}
